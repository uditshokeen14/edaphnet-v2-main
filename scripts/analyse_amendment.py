"""Apply the pre-registered amendment-v2 rules (doc 18 §4) to a finished run.

A1   recall at a 5% re-test budget, Full vs best baseline (chosen per rung x ordering among
     B0-B5, B7 by the same metric), 95% cluster-bootstrap CI over pools (pooled across seeds).
     Pass: diff >= 0.05 and CI lower bound > 0 at W1_dE0 AND W1_dE2, random ordering.
A1-c clustered ordering at W1_dE0 and W1_dE2: diff >= -0.02.
A2   for Full: weighted or Mondrian FDR <= 0.12 in every rung x ordering cell (mean over seeds).
A3   Full value-operator accuracy - B6 >= 0.20 wherever >= 30 value errors were flagged.
A4   descriptive: recall at budget by error type and rung (Full).

    python scripts/analyse_amendment.py results/runs/<run_dir>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASELINES = ["B0_range", "B1_rules", "B2_labonly", "B3_marginal", "B4_swaponly", "B5_supervised", "B7_cleanlab"]
POOL_BATCHES, BUDGET, N_BOOT = 50, 0.05, 2000


def pool_hits(df, methods, seed):
    """Per pool: number of errors and number found within the budget, for each method."""
    rng = np.random.default_rng(seed)
    out = []
    for pool, g in df.groupby(df["batch"] // POOL_BATCHES):
        err = (g["kind"] != "clean").to_numpy()
        k = int(np.ceil(BUDGET * len(g)))
        tie = rng.random(len(g))
        row = {"pool": pool, "errors": int(err.sum())}
        for m in methods:
            s = np.nan_to_num(g[f"s:{m}"].to_numpy(float), nan=np.inf, posinf=1e300)
            top = np.lexsort((tie, -s))[:k]
            row[m] = int(err[top].sum())
            for kind in ("swap", "value"):
                mk = (g["kind"] == kind).to_numpy()
                row[f"{m}|{kind}"] = int((err & mk)[top].sum())
                row[f"errors|{kind}"] = int(mk.sum())
        out.append(row)
    return pd.DataFrame(out)


def main(run):
    run = Path(run)
    C = json.loads((run / "config.json").read_text())
    methods = None
    tables = []
    for chunk in pd.read_csv(run / "predictions.csv.gz", chunksize=200_000):
        if methods is None:
            methods = [c[2:] for c in chunk.columns if c.startswith("s:")]
        keep = ["seed", "lambda", "ordering", "batch", "kind"] + [f"s:{m}" for m in methods]
        tables.append(chunk[keep])
    P = pd.concat(tables, ignore_index=True)
    del tables

    ph = []
    for (seed, rung, ordering), g in P.groupby(["seed", "lambda", "ordering"]):
        t = pool_hits(g, methods, int(seed))
        t["seed"], t["lambda"], t["ordering"] = seed, rung, ordering
        ph.append(t)
    ph = pd.concat(ph, ignore_index=True)

    rows = []
    rng = np.random.default_rng(0)
    for (rung, ordering), g in ph.groupby(["lambda", "ordering"]):
        rec = {m: g[m].sum() / g["errors"].sum() for m in methods}
        best = max(BASELINES, key=lambda m: rec.get(m, -1))
        idx = rng.integers(0, len(g), (N_BOOT, len(g)))
        E = g["errors"].to_numpy()[idx].sum(axis=1)
        diff_b = (g["Full"].to_numpy()[idx].sum(axis=1) - g[best].to_numpy()[idx].sum(axis=1)) / E
        rows.append({"lambda": rung, "ordering": ordering, "full_recall": rec["Full"], "best_baseline": best,
                     "best_recall": rec[best], "diff": rec["Full"] - rec[best],
                     "ci_low": float(np.percentile(diff_b, 2.5)), "ci_high": float(np.percentile(diff_b, 97.5)),
                     "n_pools": len(g), "n_errors": int(g["errors"].sum()),
                     **{f"recall:{m}": rec[m] for m in methods},
                     "full_recall|swap": g["Full|swap"].sum() / max(1, g["errors|swap"].sum()),
                     "full_recall|value": g["Full|value"].sum() / max(1, g["errors|value"].sum())})
    A1 = pd.DataFrame(rows)

    def cell(r, o):
        x = A1[(A1["lambda"] == r) & (A1["ordering"] == o)]
        return x.iloc[0] if len(x) else None

    verdict = {}
    a1 = [cell(r, "random") for r in ("W1_dE0", "W1_dE2")]
    if any(c is None for c in a1 + [cell(r, "clustered") for r in ("W1_dE0", "W1_dE2")]):
        print("WARNING: run incomplete; verdict not valid")
    verdict["A1"] = all(c is not None and c["diff"] >= 0.05 and c["ci_low"] > 0 for c in a1)
    a1c = [cell(r, "clustered") for r in ("W1_dE0", "W1_dE2")]
    verdict["A1-c"] = all(c is not None and c["diff"] >= -0.02 for c in a1c)

    m = pd.read_csv(run / "metrics_by_setting.csv")
    full = m[m["method"] == "Full"].groupby(["lambda", "ordering"])[["bh_fdr", "weighted_fdr", "mondrian_fdr",
                                                                     "bh_power", "weighted_power", "mondrian_power",
                                                                     "n_cal_distinct"]].mean()
    verdict["A2"] = bool(((full["weighted_fdr"] <= 0.12) | (full["mondrian_fdr"] <= 0.12)).all())
    allm = m.groupby(["method"])[["bh_fdr", "weighted_fdr", "mondrian_fdr"]].mean()

    a = pd.read_csv(run / "attribution_by_setting.csv")
    att = a.groupby(["lambda", "ordering"])[["value_flagged", "value_op_ok", "b6_value_flagged", "b6_op_ok"]].sum()
    att["full_op_acc"] = att["value_op_ok"] / att["value_flagged"].clip(lower=1)
    att["b6_op_acc"] = att["b6_op_ok"] / att["b6_value_flagged"].clip(lower=1)
    elig = att[att["value_flagged"] >= 30]
    # rule applies only to cells with >= 30 flagged value errors; none eligible -> not evaluable
    verdict["A3"] = (bool(((elig["full_op_acc"] - elig["b6_op_acc"]) >= 0.20).all())
                     if len(elig) else "not evaluable (no cell with >= 30 flagged value errors)")

    A1.to_csv(run / "amendment_A1.csv", index=False)
    full.to_csv(run / "amendment_A2_full.csv")
    att.to_csv(run / "amendment_A3.csv")
    (run / "amendment_verdict.json").write_text(json.dumps(verdict, indent=2))

    pd.set_option("display.width", 220)
    cols = ["lambda", "ordering", "full_recall", "best_baseline", "best_recall", "diff", "ci_low", "ci_high",
            "full_recall|swap", "full_recall|value", "n_errors"]
    print("A1: recall at 5% budget\n", A1[cols].round(3).to_string(index=False))
    print("\nA2: Full FDR by calibration (mean over seeds)\n", full.round(3).to_string())
    print("\nA2: all methods, mean FDR\n", allm.round(3).to_string())
    print("\nA3: attribution\n", att[["value_flagged", "full_op_acc", "b6_op_acc"]].round(3).to_string())
    print("\nVERDICT (pre-registered rules, doc 18 §4):", json.dumps(verdict))


if __name__ == "__main__":
    main(sys.argv[1])
