"""EXPLORATORY (doc 23): is "power ~ 0 with a colour witness" partly mechanical?

Benjamini-Hochberg can only flag a report in a pool of m reports if its p-value is <= q*k/m. With
~2,800 distinct calibration samples the smallest p-value is ~1/2,800, and pools of 50 batches have
m = 1,200 reports. This script re-applies BH to the STORED conformal p-values of a finished run
using smaller pools (in batches), and reports power and realised FDR per method. The p-values are
not recomputed, so nothing about the registered analysis changes.

    python scripts/rescore_pools.py results/runs/<run_dir> --pools 1 5 10 50
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
Q = 0.10


def bh(p, q):
    m = len(p)
    o = np.argsort(p)
    ok = np.nonzero(p[o] <= q * np.arange(1, m + 1) / m)[0]
    r = np.zeros(m, bool)
    if len(ok):
        r[o[: ok[-1] + 1]] = True
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--pools", type=int, nargs="+", default=[1, 5, 10, 50])
    args = ap.parse_args()
    run = Path(args.run)
    head = pd.read_csv(run / "predictions.csv.gz", nrows=0).columns
    methods = [c[2:] for c in head if c.startswith("p:")]
    use = ["seed", "lambda", "ordering", "batch", "kind"] + [f"p:{m}" for m in methods]
    acc = {}   # (pool, lambda, ordering, method) -> [tp, n_err, list of fdp]
    for chunk in pd.read_csv(run / "predictions.csv.gz", usecols=use, chunksize=100_000):
        for (seed, lam, ordg), g in chunk.groupby(["seed", "lambda", "ordering"]):
            err = (g["kind"] != "clean").to_numpy()
            b = g["batch"].to_numpy()
            for P in args.pools:
                pid = b // P
                for m in methods:
                    p = g[f"p:{m}"].to_numpy(float)
                    a = acc.setdefault((P, lam, ordg, m), [0, 0, []])
                    for u in np.unique(pid):
                        ix = pid == u
                        r = bh(p[ix], Q)
                        a[0] += int((r & err[ix]).sum())
                        a[1] += int(err[ix].sum())
                        a[2].append(float((r & ~err[ix]).sum() / r.sum()) if r.sum() else 0.0)
    rows = [{"pool_batches": P, "lambda": lam, "ordering": o, "method": m, "power": a[0] / max(a[1], 1),
             "fdr": float(np.mean(a[2])), "n_pools": len(a[2])} for (P, lam, o, m), a in acc.items()]
    T = pd.DataFrame(rows)
    out = ROOT / "results" / "exploratory" / run.name
    out.mkdir(parents=True, exist_ok=True)
    T.to_csv(out / "rescore_pools.csv", index=False)
    pd.set_option("display.width", 220)
    focus = T[T.method.isin(["Full", "B5_supervised", "B7_cleanlab", "B2_labonly", "B4_swaponly"])]
    for o in sorted(T.ordering.unique()):
        print(f"\n== {o}: power (FDR) at q = {Q}, by pool size in batches")
        f = focus[focus.ordering == o].copy()
        f["cell"] = f.apply(lambda r: f"{r.power:.3f} ({r.fdr:.2f})", axis=1)
        print(f.pivot_table(index=["lambda", "method"], columns="pool_batches", values="cell", aggfunc="first").to_string())
    print("\nsaved:", out / "rescore_pools.csv")


if __name__ == "__main__":
    main()
