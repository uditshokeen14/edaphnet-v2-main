"""EXPLORATORY (doc 23): swap-vs-value and ablation tables at a 5% re-test budget.

For each witness rung x ordering: recall at budget for Full, its ablations and the best baseline,
split by error kind (swap / value) and by value-error type. With --ci: 95% cluster-bootstrap
intervals over pools for "Full minus X". Reads predictions.csv.gz in chunks (memory-light) and
writes to results/exploratory/<run name>/, never into the run folder.

    python scripts/exploratory_tables.py results/runs/<run_dir> [--ci]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASELINES = ["B0_range", "B1_rules", "B2_labonly", "B3_marginal", "B4_swaponly", "B5_supervised", "B7_cleanlab"]
POOL, BUDGET, NBOOT = 50, 0.05, 2000


def vtype(kind, op):
    if kind != "value":
        return kind
    return str(op).split("@")[0]


def flags_for(g, methods, seed):
    """Boolean 'inside the 5% budget' per report and method, pool by pool."""
    rng = np.random.default_rng(int(seed))
    out = {m: np.zeros(len(g), bool) for m in methods}
    pools = (g["batch"].to_numpy() // POOL)
    for p in np.unique(pools):
        idx = np.where(pools == p)[0]
        k = int(np.ceil(BUDGET * len(idx)))
        tie = rng.random(len(idx))
        for m in methods:
            s = np.nan_to_num(g[f"s:{m}"].to_numpy(float)[idx], nan=np.inf, posinf=1e300)
            out[m][idx[np.lexsort((tie, -s))[:k]]] = True
    return out, pools


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--ci", action="store_true")
    args = ap.parse_args()
    run = Path(args.run)
    head = pd.read_csv(run / "predictions.csv.gz", nrows=0).columns
    methods = [c[2:] for c in head if c.startswith("s:")]
    use = ["seed", "lambda", "ordering", "batch", "kind", "true_op"] + [f"s:{m}" for m in methods]
    recs = []
    for chunk in pd.read_csv(run / "predictions.csv.gz", usecols=use, chunksize=100_000):
        for (seed, lam, ordg), g in chunk.groupby(["seed", "lambda", "ordering"]):
            g = g.reset_index(drop=True)
            fl, pools = flags_for(g, methods, seed)
            err = (g["kind"] != "clean").to_numpy()
            d = pd.DataFrame({"lambda": lam, "ordering": ordg, "seed": seed,
                              "pool": [f"{seed}-{lam}-{ordg}-{p}" for p in pools],
                              "etype": [vtype(k, o) for k, o in zip(g["kind"], g["true_op"])]})[err]
            for m in methods:
                d[m] = fl[m][err]
            recs.append(d)
    # note: a pool split across two chunks counts as two pools (pools are 1,200 rows; effect is small)
    R = pd.concat(recs, ignore_index=True)
    base = [m for m in BASELINES if m in methods]
    full_like = [m for m in methods if m.startswith("Full")]
    rows, rng = [], np.random.default_rng(0)
    for (lam, ordg), g in R.groupby(["lambda", "ordering"]):
        best = max(base, key=lambda m: g[m].mean())
        for subset, h in [("all errors", g), ("swaps", g[g.etype == "swap"]), ("value errors", g[g.etype != "swap"])] + \
                [(f"value: {t}", g[g.etype == t]) for t in sorted(set(g.etype) - {"swap"})]:
            if len(h) == 0:
                continue
            row = {"lambda": lam, "ordering": ordg, "subset": subset, "n_errors": len(h), "best_baseline": best,
                   **{m: round(float(h[m].mean()), 3) for m in full_like + [best]}}
            if args.ci and subset in ("all errors", "swaps", "value errors"):
                pools = h["pool"].to_numpy()
                up = np.unique(pools)
                pos = {p: np.where(pools == p)[0] for p in up}
                for other in [best] + [m for m in full_like if m != "Full"]:
                    diffs = h["Full"].to_numpy(float) - h[other].to_numpy(float)
                    bs = []
                    for _ in range(NBOOT):
                        pick = rng.choice(up, len(up))
                        ix = np.concatenate([pos[p] for p in pick])
                        bs.append(diffs[ix].mean())
                    lab = "best" if other == best else other
                    row[f"Full-{lab} [95% CI]"] = f"{diffs.mean():+.3f} [{np.percentile(bs, 2.5):+.3f}, {np.percentile(bs, 97.5):+.3f}]"
            rows.append(row)
    T = pd.DataFrame(rows)
    out = ROOT / "results" / "exploratory" / run.name
    out.mkdir(parents=True, exist_ok=True)
    T.to_csv(out / "swap_value_ablation.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    show = ["lambda", "ordering", "subset", "n_errors", "Full", "Full-noswap", "Full-nolibrary", "Full-nowitness", "best_baseline"]
    show = [c for c in show if c in T] + [c for c in T.columns if c not in show and c not in full_like]
    print(T[[c for c in show if c in T]].to_string(index=False))
    print("\nsaved:", out / "swap_value_ablation.csv")


if __name__ == "__main__":
    main()
