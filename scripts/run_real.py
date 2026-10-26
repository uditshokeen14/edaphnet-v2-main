"""Step 5: semi-real go/no-go test (doc 11 §7, reframed by D-010).

Real lab values and real witnesses (ICRAF-ISRIC, witness ladder from step 4b) with injected
swaps and value errors. Full + ablations vs baselines B0–B5, B7 (cleanlab, Zhou et al. 2023).
Calibration: injection-aware (D-010). BH per pool of 50 batches.

Pools (profile-grouped, disjoint): dev batches <- train split (B5 training), calibration
batches <- cal split, test batches <- test split. Witness means for train rows are
out-of-fold, so no pool sees a witness model trained on its own samples.

    python scripts/run_real.py --config configs/real_icraf8.yaml [--smoke]
"""
import argparse
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from edaphnet2 import baselines as B, operators, swaps  # noqa: E402
from edaphnet2.inference import InferenceConfig, infer_batch, loglik_none, report_hypotheses  # noqa: E402
from edaphnet2.metrics import (density_ratio_weights, detection_metrics, fdr_from_pvalues, mondrian_pvalues,  # noqa: E402
                               recall_at_budget, weighted_conformal_pvalues)
from edaphnet2.real_data import LatentTransform  # noqa: E402
from edaphnet2.space import RealSpace  # noqa: E402
from edaphnet2.tracking import config_hash, new_run_dir, provenance, write_json  # noqa: E402
from edaphnet2.witness import FixedGaussianModel  # noqa: E402
from run_sim import _attribution, _cfg, _predictions  # noqa: E402

FEATURES = ["B0_range", "B1_rules", "B2_labonly", "B3_marginal", "B4_swaponly", "B7_cleanlab"]


def load(tag):
    D = dict(np.load(ROOT / "data" / "processed" / f"t1_{tag}.npz", allow_pickle=True))
    Wt = dict(np.load(ROOT / "data" / "processed" / f"witness_{tag}.npz", allow_pickle=True))
    names = [str(n) for n in D["names"]]
    tf = LatentTransform(names)
    tf.mu, tf.sd = Wt["tf_mu"], Wt["tf_sd"]
    space = RealSpace(tf)
    return D, Wt, space


def sample_indices(pool, groups, depth, n, ordering, rng):
    if ordering == "random":
        return rng.choice(pool, n, replace=False)
    # clustered: whole profiles, layers in depth order, consecutive (as a lab tray would be)
    out = []
    for g in rng.permutation(np.unique(groups[pool])):
        members = pool[groups[pool] == g]
        out.extend(members[np.argsort(depth[members])])
        if len(out) >= n:
            break
    return np.array(out[:n])


def make_batch(idx, Y, MU, F, space, rng, inj):
    n = len(idx)
    y = Y[idx]
    pi, swap_class = np.arange(n), "none"
    if inj and rng.random() < inj["swap_batch_prob"]:
        swap_class, pi = swaps.random_swap(n, rng)
    r = y[pi].copy()
    kind = ["swap" if pi[j] != j else "clean" for j in range(n)]
    info: list = [None] * n
    for j in range(n):
        if inj and kind[j] == "clean" and rng.random() < inj["value_error_rate"]:
            if inj.get("value_error_ops") == "mismatch":     # exploratory: errors outside the library
                import mismatch_ops
                rc, inf = mismatch_ops.apply(r, j, rng, space)
            else:
                rc, inf = operators.apply_random_corruption(y[j], rng, space=space)
            r[j] = space.print_values(rc[None, :])[0]
            if np.allclose(r[j], y[j]):
                continue
            kind[j], info[j] = "value", inf
    return SimpleNamespace(idx=idx, y=y, r=r, pi=pi, swap_class=swap_class, kind=kind, value_info=info,
                           is_error=np.array([k != "clean" for k in kind]), mu=MU[idx],
                           w=None if F is None else F[idx])


def score_batch(b, M, cfg):
    R, MU, s = b.r, b.mu, {}
    full = infer_batch(R, MU, M["wit"], cfg)
    s["Full"] = full["score"]
    pre = full["precomputed"]
    s["Full-noswap"] = infer_batch(R, MU, M["wit"], _cfg(cfg, use_swaps=False), precomputed=pre)["score"]
    s["Full-uniformprior"] = infer_batch(R, MU, M["wit"], _cfg(cfg, uniform_swap_prior=True), precomputed=pre)["score"]
    c_nolib = _cfg(cfg, groups=("gross",))
    s["Full-nolibrary"] = infer_batch(R, MU, M["wit"], c_nolib, hyp_list=report_hypotheses(R, c_nolib))["score"]
    s["Full-nowitness"] = infer_batch(R, np.zeros_like(MU), M["pop"], cfg, hyp_list=pre[0])["score"]
    sp = cfg.space
    s["B0_range"] = M["range"].score(R)
    s["B1_rules"] = B.rule_score(R, sp)
    s["B2_labonly"] = B.population_score(R, M["pop"], sp, pop_mean=np.zeros(sp.P))
    s["B3_marginal"] = B.marginal_witness_score(R, MU, M["wit"], sp)
    s["B4_swaponly"] = B.hungarian_score(loglik_none(R, MU, M["wit"], sp))
    return s, full


def run_setting(C, D, Wt, space, rung, ordering, seed, smoke):
    import zlib  # stable across processes (built-in hash() of str is salted per run)
    rng = np.random.default_rng([seed, zlib.crc32(rung.encode()), 0 if ordering == "random" else 1])
    Y = space.print_values(D["X"])
    split, groups, depth = D["split"], D["groups"], D["depth"]
    MU = Wt[f"{rung}__mu"]
    F = Wt.get(f"{rung}__F")
    tr = np.where(split == "train")[0]
    M = {"wit": FixedGaussianModel(Wt[f"{rung}__S"]), "pop": FixedGaussianModel(Wt["W0__S"]),
         "range": B.RangeCheck(space).fit(Y[tr])}
    cfg = InferenceConfig(rho=C["prior"]["rho"], eps=C["prior"]["eps"], space=space)
    b7 = B.CleanlabOutre(space, seed).fit(Y[tr], None if F is None else F[tr])

    n, inj = C["batch_size"], C["inject"]
    k = 0.1 if smoke else 1.0
    counts = {s: max(5, int(C[f"n_{s}_batches"] * k)) for s in ("cal", "dev", "test")}
    pools = {"cal": np.where(split == "cal")[0], "dev": tr, "test": np.where(split == "test")[0]}

    out = {}
    for name in ("cal", "dev", "test"):
        bs, ss, fs = [], [], []
        for _ in range(counts[name]):
            b = make_batch(sample_indices(pools[name], groups, depth, n, ordering, rng), Y, MU, F, space, rng, inj)
            s, f = score_batch(b, M, cfg)
            f = {key: f[key] for key in ("kind", "partner", "value_op")}  # drop large intermediates
            bs.append(b); ss.append(s); fs.append(f)
        R = np.vstack([b.r for b in bs])
        Wf = None if F is None else np.vstack([b.w for b in bs])
        b7s = b7.score_pool(R, Wf)
        for i, s in enumerate(ss):
            s["B7_cleanlab"] = b7s[i * n:(i + 1) * n]
        out[name] = (bs, ss, fs)

    import lightgbm as lgb
    dev_b, dev_s, _ = out["dev"]
    Xdev = np.vstack([np.column_stack([s[f] for f in FEATURES]) for s in dev_s])
    b5 = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=15, random_state=seed,
                            verbose=-1).fit(Xdev, np.concatenate([b.is_error for b in dev_b]))
    for name in ("cal", "test"):
        for s in out[name][1]:
            s["B5_supervised"] = b5.predict_proba(np.column_stack([s[f] for f in FEATURES]))[:, 1]

    cal_b, cal_s, _ = out["cal"]
    test_b, test_s, test_f = out["test"]
    stack = lambda sl, key: np.concatenate([s[key] for s in sl])  # noqa: E731
    null = np.concatenate([~b.is_error for b in cal_b])
    # doc 18 Amendment 1: one calibration score per distinct sample (no pseudo-replication)
    cal_sample = np.concatenate([b.idx for b in cal_b])[null]
    order = np.random.default_rng(seed).permutation(len(cal_sample))
    _, first = np.unique(cal_sample[order], return_index=True)
    keep = np.sort(order[first])
    is_error = np.concatenate([b.is_error for b in test_b])
    kinds = np.concatenate([b.kind for b in test_b])
    grp = np.concatenate([[(vi or {}).get("group", "") for vi in b.value_info] for b in test_b])
    pool_ids = np.repeat(np.arange(len(test_b)) // C["bh_pool_batches"], n)

    # doc 18 §5: features for shift-aware calibration = witness of the recorded sample + latent report
    def feats(bs):
        Z, _ = space.to_latent(np.vstack([b.r for b in bs]))
        Z = np.clip(np.nan_to_num(Z, nan=0.0), -10, 10)
        return Z if F is None else np.hstack([np.vstack([b.w for b in bs]), Z])
    f_cal, f_test = feats(cal_b)[null][keep], feats(test_b)
    w_cal, w_test = density_ratio_weights(f_cal, f_test, seed)
    km_train = F[tr] if F is not None else np.clip(np.nan_to_num(space.to_latent(Y[tr])[0]), -10, 10)
    km_part = (lambda bs: np.vstack([b.w for b in bs])) if F is not None else \
        (lambda bs: np.clip(np.nan_to_num(space.to_latent(np.vstack([b.r for b in bs]))[0]), -10, 10))
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=4, n_init=10, random_state=seed).fit(km_train)
    g_cal, g_test = km.predict(km_part(cal_b))[null][keep], km.predict(km_part(test_b))
    counts_g = np.bincount(g_cal, minlength=4)
    big = np.where(counts_g >= 200)[0]
    remap = {g: (g if counts_g[g] >= 200 else
                 big[np.argmin(np.linalg.norm(km.cluster_centers_[big] - km.cluster_centers_[g], axis=1))])
             for g in range(4)} if len(big) else {g: 0 for g in range(4)}
    g_cal, g_test = np.vectorize(remap.get)(g_cal), np.vectorize(remap.get)(g_test)

    methods = list(test_s[0].keys())
    results, pvals, rejs = [], {}, {}
    for m in methods:
        cal_m, test_m = stack(cal_s, m)[null][keep], stack(test_s, m)
        met, p, rej_d = detection_metrics(cal_m, test_m, is_error, pool_ids, C["q"])
        rej = rej_d["bh"]
        for sub, mask in [("swap", kinds == "swap"), ("value", kinds == "value")] + \
                [(f"value:{g}", grp == g) for g in sorted(set(grp) - {""})]:
            met[f"power[{sub}]"] = float(rej[mask].mean()) if mask.any() else None
            met[f"n[{sub}]"] = int(mask.sum())
        # doc 18: A1 recall at a 5% re-test budget; A2 shift-aware calibration
        met["recall_at_5pct"], flagged = recall_at_budget(test_m, is_error, pool_ids, 0.05, seed)
        met["recall_at_5pct[swap]"] = float(flagged[kinds == "swap"].mean()) if (kinds == "swap").any() else None
        met["recall_at_5pct[value]"] = float(flagged[kinds == "value"].mean()) if (kinds == "value").any() else None
        cal_f = np.nan_to_num(cal_m, nan=np.inf)
        test_f_ = np.nan_to_num(test_m, nan=np.inf)
        pw = weighted_conformal_pvalues(cal_f, test_f_, w_cal, w_test)
        met["weighted_fdr"], met["weighted_power"], _ = fdr_from_pvalues(pw, is_error, pool_ids, C["q"])
        pm = mondrian_pvalues(cal_f, g_cal, test_f_, g_test)
        met["mondrian_fdr"], met["mondrian_power"], _ = fdr_from_pvalues(pm, is_error, pool_ids, C["q"])
        met["n_cal_distinct"] = int(len(keep))
        results.append({"method": m, "cal_mode": "injected", **met})
        pvals[m], rejs[m] = p, rej
    attr = {"cal_mode": "injected", **_attribution(test_f, test_b, rejs["Full"], M["range"], rejs["B0_range"])}
    preds = _predictions(test_s, test_f, test_b, pvals, methods)
    sample_idx = [int(b.idx[j]) for b in test_b for j in range(n)]
    partner_idx = [int(b.idx[b.pi[j]]) for b in test_b for j in range(n)]
    for row, si, pj in zip(preds, sample_idx, partner_idx):
        row["sample_idx"], row["measured_sample_idx"] = si, pj
    return results, attr, preds


FILES = ("metrics_by_setting.csv", "attribution_by_setting.csv", "predictions.csv.gz")
SETTING_KEYS = ["seed", "lambda", "ordering"]


def prepare_resume(run, C, smoke):
    """Validate a previous run folder and return the set of settings already finished.

    Safe resume requires: same config (hash), same code (no change to src/, scripts/, configs/
    since the run's commit), and each finished setting present in all three result files.
    Rows of a setting that was only partly written are dropped. Each setting draws from its own
    RNG seeded by (seed, rung, ordering), so skipping finished settings does not change the
    others: a resumed run gives the same numbers as an uninterrupted one.
    """
    import json
    import subprocess
    old = json.loads((run / "config.json").read_text())
    if old.get("config_hash") != config_hash(C) or old.get("smoke") != smoke:
        raise SystemExit(f"Cannot resume: config differs from the one used in {run.name}.")
    prov = json.loads((run / "provenance.json").read_text())
    # the method code and configs must be identical; runner-script changes are allowed but recorded
    # (the resume equivalence is tested: tests/test_resume.py)
    diff = subprocess.run(["git", "diff", "--quiet", prov["git_commit"], "HEAD", "--", "src", "configs"],
                          cwd=ROOT).returncode
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src", "configs"], cwd=ROOT).returncode
    if diff or dirty:
        raise SystemExit(f"Cannot resume: method code or configs changed since commit {prov['git_commit'][:7]}. "
                         "Start a new run instead.")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if not all((run / f).exists() for f in FILES):
        return set(), prov
    frames = {f: pd.read_csv(run / f, **({"compression": "gzip"} if f.endswith(".gz") else {})) for f in FILES}
    done = None
    for df in frames.values():
        keys = set(map(tuple, df[SETTING_KEYS].astype(str).drop_duplicates().to_numpy()))
        done = keys if done is None else done & keys
    for f, df in frames.items():   # rewrite each file with complete settings only
        keep = df[SETTING_KEYS].astype(str).apply(tuple, axis=1).isin(done)
        df[keep].to_csv(run / f, index=False, **({"compression": "gzip"} if f.endswith(".gz") else {}))
    prov.setdefault("resumed", []).append({"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                           "settings_already_done": len(done), "resumed_with_commit": head})
    return done, prov


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--resume", help="path of an interrupted run folder to continue")
    args = ap.parse_args()
    C = yaml.safe_load(Path(args.config).read_text())
    if args.smoke:
        C = {**C, "seeds": C["seeds"][:1], "rungs": ["W0", "W3"], "orderings": ["random"],
             "name": C["name"] + "_smoke"}
    D, Wt, space = load(C["tag"])

    if args.resume:
        run = Path(args.resume).resolve()
        done, prov = prepare_resume(run, C, args.smoke)
        write_json(run / "provenance.json", prov)
        print(f"resuming {run}: {len(done)} settings already done", flush=True)
    else:
        run = new_run_dir(ROOT / "results" / "runs", C["name"], ROOT)
        prov = provenance(ROOT)
        write_json(run / "config.json", {**C, "config_hash": config_hash(C), "smoke": args.smoke})
        write_json(run / "provenance.json", prov)
        done = set()
        print(f"run dir: {run}  status: {prov['status']}", flush=True)

    import gc
    first = not done
    for seed in C["seeds"]:
        for ordering in C["orderings"]:
            for rung in C["rungs"]:
                if (str(seed), str(rung), str(ordering)) in done:
                    continue
                t0 = time.time()
                res, attr, preds = run_setting(C, D, Wt, space, rung, ordering, seed, args.smoke)
                tag = {"seed": seed, "lambda": rung, "ordering": ordering}
                # append to disk after every setting: bounded memory, and a crash keeps finished work
                for fname, rows, kw in (("metrics_by_setting.csv", [{**tag, **r} for r in res], {}),
                                        ("attribution_by_setting.csv", [{**tag, **attr}], {}),
                                        ("predictions.csv.gz", [{**tag, **p} for p in preds], {"compression": "gzip"})):
                    pd.DataFrame(rows).to_csv(run / fname, mode="w" if first else "a", header=first, index=False, **kw)
                first = False
                del preds
                gc.collect()
                full = next(r for r in res if r["method"] == "Full")
                best = max((r for r in res if not r["method"].startswith("Full")), key=lambda r: r["bh_power"])
                print(f"seed={seed} {ordering:9s} {rung:8s} Full power={full['bh_power']:.3f} "
                      f"fdr={full['bh_fdr']:.3f} | best baseline {best['method']} {best['bh_power']:.3f} "
                      f"({time.time() - t0:.0f}s)", flush=True)

    prov["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    write_json(run / "provenance.json", prov)
    # label from the config's dataset tag (runs before 2026-10-03 always said ICRAF-ISRIC; doc 26 §3)
    source = {"icraf8": "ICRAF-ISRIC", "kssl3": "KSSL"}.get(C["tag"], C["tag"])
    write_json(run / "metrics.json", {"evidence_tag": f"REAL DATA + INJECTED ERRORS ({source})",
                                      "note": "column 'lambda' holds the witness rung name"})
    print("done:", run)


if __name__ == "__main__":
    main()
