"""Step 3: T0 simulation study. Runs Full, its ablations and baselines B0–B7 over the
config grid and writes one run record (config, provenance, metrics, predictions).

    python scripts/run_sim.py --config configs/sim_t0.yaml [--smoke]
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from edaphnet2 import baselines as B  # noqa: E402
from edaphnet2.inference import InferenceConfig, infer_batch, loglik_none, report_hypotheses  # noqa: E402
from edaphnet2.metrics import detection_metrics  # noqa: E402
from edaphnet2.properties import NAMES  # noqa: E402
from edaphnet2.simulate import Generator, oracle_r2  # noqa: E402
from edaphnet2.tracking import config_hash, new_run_dir, provenance, write_json  # noqa: E402
from edaphnet2.witness import GaussianModel  # noqa: E402

FEATURES = ["B0_range", "B1_rules", "B2_labonly", "B3_marginal", "B4_swaponly", "B7_regression"]


def score_batch(b, M, cfg_full):
    """All method scores for one batch, plus Full's attribution."""
    R, n = b.r, len(b.r)
    MU_w, MU_p = M["wit"].mean(b.w), M["pop"].mean(n=n)
    s = {}

    full = infer_batch(R, MU_w, M["wit"], cfg_full)
    s["Full"] = full["score"]
    pre = full["precomputed"]
    s["Full-noswap"] = infer_batch(R, MU_w, M["wit"], _cfg(cfg_full, use_swaps=False), precomputed=pre)["score"]
    s["Full-uniformprior"] = infer_batch(R, MU_w, M["wit"], _cfg(cfg_full, uniform_swap_prior=True), precomputed=pre)["score"]
    c_nolib = _cfg(cfg_full, groups=("gross",))
    s["Full-nolibrary"] = infer_batch(R, MU_w, M["wit"], c_nolib, hyp_list=report_hypotheses(R, c_nolib))["score"]
    s["Full-nowitness"] = infer_batch(R, MU_p, M["pop"], cfg_full, hyp_list=pre[0])["score"]

    s["B0_range"] = M["range"].score(R)
    s["B1_rules"] = B.rule_score(R)
    s["B2_labonly"] = B.population_score(R, M["pop"])
    s["B3_marginal"] = B.marginal_witness_score(R, MU_w, M["wit"])
    s["B4_swaponly"] = B.hungarian_score(loglik_none(R, MU_w, M["wit"]))
    s["B7_regression"] = M["b7"].score(R, b.w)
    return s, full


def _cfg(base, **kw):
    d = dict(base.__dict__); d.update(kw)
    return InferenceConfig(**d)


def run_setting(C, seed, ordering, lam, cfg_full, smoke):
    rng = np.random.default_rng([seed, int(lam * 1000), 0 if ordering == "random" else 1])
    g = Generator(lam, rng, ordering, C["farm_size"], C["homogeneity"])
    _, Wtr, Ytr = g.samples(C["n_train"])
    M = {
        "wit": GaussianModel().fit(Ytr, Wtr),
        "pop": GaussianModel().fit(Ytr),
        "range": B.RangeCheck().fit(Ytr),
        "b7": B.RegressionVeracity().fit(Ytr, Wtr),
    }
    n, inj = C["batch_size"], C["inject"]
    k = 0.1 if smoke else 1.0
    n_cal, n_dev, n_test = (max(5, int(C[x] * k)) for x in ("n_cal_batches", "n_dev_batches", "n_test_batches"))

    def collect(n_batches, inject):
        rows, scores, fulls, batches = [], [], [], []
        for bi in range(n_batches):
            b = g.batch(n, inj["swap_batch_prob"] if inject else 0.0,
                        inj["value_error_rate"] if inject else 0.0)
            s, full = score_batch(b, M, cfg_full)
            full = {key: full[key] for key in ("kind", "partner", "value_op")}  # drop large intermediates
            scores.append(s); fulls.append(full); batches.append(b)
        return scores, fulls, batches

    # Two calibration modes (doc 11 §2.6 caveat):
    #   clean    - scores of reports in error-free batches
    #   injected - scores of the clean reports inside batches with injected errors, so that
    #              calibration nulls see the same "error neighbourhood" as test nulls
    cal_clean_s, _, _ = collect(n_cal, False)
    cal_inj_s, _, cal_inj_b = collect(n_cal, True)
    dev_s, _, dev_b = collect(n_dev, True)
    test_s, test_f, test_b = collect(n_test, True)

    def stack(slist, key):
        return np.concatenate([s[key] for s in slist])

    inj_null = np.concatenate([~b.is_error for b in cal_inj_b])

    # B5: supervised model on dev batches (sees the injected error mix: an advantage, stated)
    import lightgbm as lgb
    Xdev = np.column_stack([stack(dev_s, f) for f in FEATURES])
    ydev = np.concatenate([b.is_error for b in dev_b])
    b5 = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=15,
                            random_state=seed, verbose=-1).fit(Xdev, ydev)
    for sl in (cal_clean_s, cal_inj_s, test_s):
        for s in sl:
            s["B5_supervised"] = b5.predict_proba(np.column_stack([s[f] for f in FEATURES]))[:, 1]

    methods = list(test_s[0].keys())
    is_error = np.concatenate([b.is_error for b in test_b])
    kinds = np.concatenate([b.kind for b in test_b])
    groups = np.concatenate([[(vi or {}).get("group", "") for vi in b.value_info] for b in test_b])
    pool_ids = np.repeat(np.arange(len(test_b)) // C["bh_pool_batches"], n)

    results, pvals, rejs = [], {}, {}
    for cal_mode in ("clean", "injected"):
        for m in methods:
            cal = stack(cal_clean_s, m) if cal_mode == "clean" else stack(cal_inj_s, m)[inj_null]
            met, p, rej_d = detection_metrics(cal, stack(test_s, m), is_error, pool_ids, C["q"])
            rej = rej_d["bh"]
            for sub, mask in [("swap", kinds == "swap"), ("value", kinds == "value")] + \
                    [(f"value:{gname}", groups == gname) for gname in sorted(set(groups) - {""})]:
                met[f"power[{sub}]"] = float(rej[mask].mean()) if mask.any() else None
                met[f"n[{sub}]"] = int(mask.sum())
            results.append({"method": m, "cal_mode": cal_mode, **met})
            pvals[(cal_mode, m)], rejs[(cal_mode, m)] = p, rej

    attribution = [{"cal_mode": cm, **_attribution(test_f, test_b, rejs[(cm, "Full")],
                                                   M["range"], rejs[(cm, "B0_range")])}
                   for cm in ("clean", "injected")]
    preds = _predictions(test_s, test_f, test_b, {m: pvals[("injected", m)] for m in methods}, methods)
    return results, attribution, preds


def _attribution(fulls, batches, rej, rangec, rej_b0):
    """Among true errors flagged (pooled BH): is the error correctly explained?"""
    idx = 0
    c = {"swap_flagged": 0, "swap_kind_ok": 0, "swap_partner_ok": 0,
         "value_flagged": 0, "value_kind_ok": 0, "value_op_ok": 0,
         "b6_value_flagged": 0, "b6_op_ok": 0}
    for f, b in zip(fulls, batches):
        for j in range(len(b.r)):
            if b.kind[j] == "swap" and rej[idx]:
                c["swap_flagged"] += 1
                c["swap_kind_ok"] += f["kind"][j] == "swap"
                c["swap_partner_ok"] += f["kind"][j] == "swap" and f["partner"][j] == b.pi[j]
            if b.kind[j] == "value":
                truth = b.value_info[j]
                if rej[idx]:
                    c["value_flagged"] += 1
                    ok_kind = f["kind"][j] == "value"
                    c["value_kind_ok"] += ok_kind
                    c["value_op_ok"] += ok_kind and _op_match(f["value_op"][j][1], truth)
                if rej_b0[idx]:
                    c["b6_value_flagged"] += 1
                    c["b6_op_ok"] += _op_match(rangec.attribute(b.r[j]) or "", truth)
            idx += 1
    rate = lambda a, b: c[a] / c[b] if c[b] else None  # noqa: E731
    return {**c,
            "swap_kind_acc": rate("swap_kind_ok", "swap_flagged"),
            "swap_partner_acc": rate("swap_partner_ok", "swap_flagged"),
            "value_kind_acc": rate("value_kind_ok", "value_flagged"),
            "value_op_acc": rate("value_op_ok", "value_flagged"),
            "b6_op_acc": rate("b6_op_ok", "b6_value_flagged")}


def _op_match(pred, truth):
    if truth["group"] == "gross":
        return pred.startswith("G@") and pred.split("@")[1] == truth["op"].split("@")[1]
    if truth["group"] == "column_swap":
        return pred == truth["op"]
    return pred == truth["op"]


def _predictions(test_s, fulls, batches, pvals, methods):
    rows, idx = [], 0
    for bi, (s, f, b) in enumerate(zip(test_s, fulls, batches)):
        for j in range(len(b.r)):
            row = {"batch": bi, "pos": j, "kind": b.kind[j], "swap_class": b.swap_class,
                   "true_partner": int(b.pi[j]),
                   "true_op": (b.value_info[j] or {}).get("op", ""),
                   "full_kind": f["kind"][j], "full_partner": int(f["partner"][j]),
                   "full_op": f["value_op"][j][1]}
            for m in methods:
                row[f"s:{m}"] = float(s[m][j])
                row[f"p:{m}"] = float(pvals[m][idx])
            rows.append(row)
            idx += 1
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--smoke", action="store_true", help="10%% of batches, one seed, two lambdas")
    args = ap.parse_args()
    C = yaml.safe_load(Path(args.config).read_text())
    if args.smoke:
        C = {**C, "seeds": C["seeds"][:1], "lambdas": [0.0, 2.0], "name": C["name"] + "_smoke"}
    cfg_full = InferenceConfig(rho=C["prior"]["rho"], eps=C["prior"]["eps"])

    run = new_run_dir(ROOT / "results" / "runs", C["name"], ROOT)
    prov = provenance(ROOT)
    write_json(run / "config.json", {**C, "config_hash": config_hash(C), "smoke": args.smoke})
    write_json(run / "provenance.json", prov)
    print(f"run dir: {run}  status: {prov['status']}")

    all_res, all_attr, all_pred = [], [], []
    for seed in C["seeds"]:
        for ordering in C["orderings"]:
            for lam in C["lambdas"]:
                t0 = time.time()
                res, attr, preds = run_setting(C, seed, ordering, lam, cfg_full, args.smoke)
                tag = {"seed": seed, "ordering": ordering, "lambda": lam}
                all_res += [{**tag, **r} for r in res]
                all_attr += [{**tag, **a} for a in attr]
                all_pred += [{**tag, **p} for p in preds]
                msg = "  ".join(
                    f"{r['cal_mode']}: power={r['bh_power']:.3f} fdr={r['bh_fdr']:.3f}"
                    for r in res if r["method"] == "Full")
                print(f"seed={seed} {ordering:9s} lam={lam:<4} Full  {msg}  ({time.time() - t0:.0f}s)",
                      flush=True)

    r2 = {str(l): dict(zip(NAMES, np.round(oracle_r2(l), 3))) for l in C["lambdas"]}
    write_json(run / "witness_oracle_r2.json", r2)
    pd.DataFrame(all_res).to_csv(run / "metrics_by_setting.csv", index=False)
    pd.DataFrame(all_attr).to_csv(run / "attribution_by_setting.csv", index=False)
    pd.DataFrame(all_pred).to_csv(run / "predictions.csv.gz", index=False, compression="gzip")
    prov["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    write_json(run / "provenance.json", prov)
    write_json(run / "metrics.json", {"evidence_tag": "MEASURED-SYNTHETIC",
                                      "unit_of_analysis": "report; BH pooled over all test "
                                      "reports of a setting", "files": ["metrics_by_setting.csv",
                                      "attribution_by_setting.csv", "witness_oracle_r2.json"]})
    print("done:", run)


if __name__ == "__main__":
    main()
