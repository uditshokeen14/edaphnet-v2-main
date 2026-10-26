"""Detectability table (doc 18 A4 / TC3): share of each error type found within a 5% re-test
budget, per witness level, for Full and for the best baseline of each cell.

Descriptive only. For runs analysed before amendment v2 (the T0 simulation, the step-5 ICRAF run)
the output is EXPLORATORY and must be labelled as such.

    python scripts/detectability_table.py results/runs/<run_dir>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASELINES = ["B0_range", "B1_rules", "B2_labonly", "B3_marginal", "B4_swaponly", "B5_supervised",
             "B7_regression", "B7_cleanlab"]
POOL, BUDGET = 50, 0.05


def error_type(row_kind, swap_class, true_op):
    if row_kind == "swap":
        return f"swap:{swap_class}"
    if row_kind == "value":
        op = str(true_op)
        prop = op.split("@")[-1]
        if op.startswith("G@"):
            return f"gross@{prop}"
        if op.startswith("TR@"):
            return f"digit-transposition@{prop}"
        if op.startswith("CS@"):
            return "column-swap"
        if op.startswith(("x10", "/10")):
            return f"decimal@{prop}"
        return f"unit@{prop}"
    return "clean"


def main(run):
    run = Path(run)
    head = pd.read_csv(run / "predictions.csv.gz", nrows=1).columns
    methods = [c[2:] for c in head if c.startswith("s:") and (c[2:] == "Full" or c[2:] in BASELINES)]
    use = ["seed", "lambda", "ordering", "batch", "kind", "swap_class", "true_op"] + [f"s:{m}" for m in methods]
    found = []
    for chunk in pd.read_csv(run / "predictions.csv.gz", usecols=use, chunksize=150_000):
        chunk["etype"] = [error_type(k, s, o) for k, s, o in zip(chunk["kind"], chunk["swap_class"], chunk["true_op"])]
        chunk["pool"] = chunk["batch"] // POOL
        for (seed, lam, ordg, pool), g in chunk.groupby(["seed", "lambda", "ordering", "pool"]):
            k = int(np.ceil(BUDGET * len(g)))
            rng = np.random.default_rng(int(seed))
            tie = rng.random(len(g))
            rec = {"lambda": lam, "ordering": ordg}
            for m in methods:
                s = np.nan_to_num(g[f"s:{m}"].to_numpy(float), nan=np.inf, posinf=1e300)
                flag = np.zeros(len(g), bool)
                flag[np.lexsort((tie, -s))[:k]] = True
                for et, fl in zip(g["etype"], flag):
                    if et != "clean":
                        found.append((lam, ordg, m, et, fl))
    # note: a pool split across chunk boundaries is treated as two pools (small effect, descriptive only)
    F = pd.DataFrame(found, columns=["lambda", "ordering", "method", "etype", "found"])
    F["family"] = F["etype"].str.split("[:@]", regex=True).str[0]
    tab = F.groupby(["ordering", "lambda", "family", "method"])["found"].agg(["mean", "size"]).reset_index()
    full = tab[tab.method == "Full"].rename(columns={"mean": "full", "size": "n"}).drop(columns="method")
    base = tab[tab.method != "Full"].sort_values("mean").groupby(["ordering", "lambda", "family"]).tail(1)
    base = base.rename(columns={"mean": "best_baseline", "method": "which"}).drop(columns="size")
    out = full.merge(base, on=["ordering", "lambda", "family"])
    out["gain"] = out["full"] - out["best_baseline"]
    out.to_csv(run / "detectability_table.csv", index=False)
    pd.set_option("display.width", 200)
    for o in sorted(out["ordering"].unique()):
        print(f"\n== {o}: share of errors found within a 5% re-test budget (Full | gain over best baseline)")
        p = out[out.ordering == o].pivot(index="family", columns="lambda", values="full").round(2)
        g = out[out.ordering == o].pivot(index="family", columns="lambda", values="gain").round(2)
        print(p.astype(str).add(" | ").add(g.map(lambda v: f"{v:+.2f}")).to_string())
    print("\nsaved:", run / "detectability_table.csv")


if __name__ == "__main__":
    main(sys.argv[1])
