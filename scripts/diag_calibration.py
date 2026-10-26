"""Phase 2 diagnostic: did step-5 error control fail because of calibration-vs-test soil shift?

Uses ONLY the step-5 calibration split (never the step-5 test split). The cal split's samples
are divided into two halves A (calibration) and B (evaluation) in two ways:
  exchangeable  - samples assigned at random (A and B contain the same kinds of soil)
  shift         - whole profiles assigned to A or B (A and B contain different soils, as in step 5)
Prediction registered before running (doc 17 §2): realised FDR stays near q under
'exchangeable' and rises under 'shift', and rises much more for the baselines than for Full.

    python scripts/diag_calibration.py
"""
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from edaphnet2 import baselines as B  # noqa: E402
from edaphnet2.inference import InferenceConfig, infer_batch, loglik_none  # noqa: E402
from edaphnet2.metrics import detection_metrics  # noqa: E402
from edaphnet2.tracking import new_run_dir, provenance, write_json  # noqa: E402
from edaphnet2.witness import FixedGaussianModel  # noqa: E402
from run_real import load, make_batch, sample_indices  # noqa: E402

CONFIG = dict(tag="icraf8", seeds=[11, 22], rungs=["W1_dE0", "W3"], ordering="random",
              batch_size=24, n_cal_batches=200, n_test_batches=150, bh_pool_batches=25,
              inject={"swap_batch_prob": 0.2, "value_error_rate": 0.025},
              prior={"rho": 0.1, "eps": 0.05}, q=0.10)


def scores(b, M, cfg):
    sp = cfg.space
    R, MU = b.r, b.mu
    return {"Full": infer_batch(R, MU, M["wit"], cfg)["score"],
            "B0_range": M["range"].score(R),
            "B2_labonly": B.population_score(R, M["pop"], sp, pop_mean=np.zeros(sp.P)),
            "B3_marginal": B.marginal_witness_score(R, MU, M["wit"], sp),
            "B4_swaponly": B.hungarian_score(loglik_none(R, MU, M["wit"], sp))}


def main():
    C = CONFIG
    D, Wt, space = load(C["tag"])
    Y = space.print_values(D["X"])
    split, groups, depth = D["split"], D["groups"], D["depth"]
    cal = np.where(split == "cal")[0]
    tr = np.where(split == "train")[0]
    run = new_run_dir(ROOT / "results" / "runs", "diag_calibration", ROOT)
    write_json(run / "config.json", C)
    write_json(run / "provenance.json", provenance(ROOT))
    rows = []
    for seed in C["seeds"]:
        for rung in C["rungs"]:
            for mode in ("exchangeable", "shift"):
                t0 = time.time()
                rng = np.random.default_rng([seed, zlib.crc32(rung.encode()), zlib.crc32(mode.encode())])
                if mode == "exchangeable":
                    perm = rng.permutation(cal)
                    A, Bp = np.sort(perm[: len(cal) // 2]), np.sort(perm[len(cal) // 2:])
                else:
                    ug = rng.permutation(np.unique(groups[cal]))
                    gA = set(ug[: len(ug) // 2])
                    A = cal[np.isin(groups[cal], list(gA))]
                    Bp = cal[~np.isin(groups[cal], list(gA))]
                MU = Wt[f"{rung}__mu"]
                M = {"wit": FixedGaussianModel(Wt[f"{rung}__S"]), "pop": FixedGaussianModel(Wt["W0__S"]),
                     "range": B.RangeCheck(space).fit(Y[tr])}
                cfg = InferenceConfig(rho=C["prior"]["rho"], eps=C["prior"]["eps"], space=space)
                n = C["batch_size"]

                def collect(pool, k):
                    bs, ss = [], []
                    for _ in range(k):
                        b = make_batch(sample_indices(pool, groups, depth, n, C["ordering"], rng),
                                       Y, MU, None, space, rng, C["inject"])
                        bs.append(b); ss.append(scores(b, M, cfg))
                    return bs, ss
                cb, cs = collect(A, C["n_cal_batches"])
                tb, ts = collect(Bp, C["n_test_batches"])
                null = np.concatenate([~b.is_error for b in cb])
                is_err = np.concatenate([b.is_error for b in tb])
                pools = np.repeat(np.arange(len(tb)) // C["bh_pool_batches"], n)
                # follow-up hypothesis (registered in D-016 before this re-run): reusing the same
                # calibration samples across batches makes conformal p-values anti-conservative;
                # keeping one score per distinct calibration sample should restore validity
                cal_sample = np.concatenate([b.idx for b in cb])[null]
                first = np.unique(cal_sample, return_index=True)[1]
                for m in cs[0]:
                    cal_all = np.concatenate([s[m] for s in cs])[null]
                    for cal_variant, cal_s in (("all_reused", cal_all), ("one_per_sample", cal_all[first])):
                        met, _, _ = detection_metrics(cal_s, np.concatenate([s[m] for s in ts]), is_err, pools, C["q"])
                        rows.append({"seed": seed, "rung": rung, "mode": mode, "cal_variant": cal_variant,
                                     "method": m, "n_cal_scores": len(cal_s), "n_cal_samples": len(A),
                                     "fdr": met["bh_fdr"], "power": met["bh_power"], "auprc": met["auprc"]})
                print(f"seed={seed} {rung} {mode:12s} done ({time.time() - t0:.0f}s)", flush=True)
                pd.DataFrame(rows).to_csv(run / "diag_results.csv", index=False)
    d = pd.DataFrame(rows)
    print(d.pivot_table(index=["rung", "method"], columns=["mode", "cal_variant"], values="fdr").round(3).to_string())
    print("run:", run)


if __name__ == "__main__":
    main()
