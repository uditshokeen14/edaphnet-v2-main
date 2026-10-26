"""Summarise a simulation run: mean ± SD over seeds per (ordering, lambda, method, cal_mode),
paired Full-vs-baseline power differences with a seed-level bootstrap CI, FDR check against
q, and attribution accuracy. Writes summary files into the run directory.

    python scripts/summarise_runs.py results/runs/<run_dir>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def boot_ci(x, n=5000, seed=0):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    m = rng.choice(x, (n, len(x)), replace=True).mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main(run):
    run = Path(run)
    C = json.loads((run / "config.json").read_text())
    q = C["q"]
    m = pd.read_csv(run / "metrics_by_setting.csv")
    a = pd.read_csv(run / "attribution_by_setting.csv")
    keys = ["cal_mode", "ordering", "lambda", "method"]

    agg = m.groupby(keys).agg(power=("bh_power", "mean"), power_sd=("bh_power", "std"),
                              fdr=("bh_fdr", "mean"), fdr_sd=("bh_fdr", "std"),
                              fdr_max_seed=("bh_fdr", "max"), by_power=("by_power", "mean"),
                              by_fdr=("by_fdr", "mean"), auprc=("auprc", "mean"),
                              power_swap=("power[swap]", "mean"),
                              power_value=("power[value]", "mean")).reset_index()
    agg["fdr_ok"] = agg["fdr"] <= q + 0.02
    agg.to_csv(run / "summary_by_method.csv", index=False)

    # paired differences Full - best non-Full method per setting (seed-level pairing)
    rows = []
    for (cm, o, lam), g in m.groupby(["cal_mode", "ordering", "lambda"]):
        piv = g.pivot(index="seed", columns="method", values="bh_power")
        base = [c for c in piv.columns if not c.startswith("Full")]
        best = piv[base].mean().idxmax()
        d = piv["Full"] - piv[best]
        rows.append({"cal_mode": cm, "ordering": o, "lambda": lam, "best_baseline": best,
                     "full_power": piv["Full"].mean(), "best_baseline_power": piv[best].mean(),
                     "diff": d.mean(), "diff_ci_seed_boot": boot_ci(d), "n_seeds": len(d)})
    diffs = pd.DataFrame(rows)
    diffs.to_csv(run / "summary_full_vs_best_baseline.csv", index=False)

    att = a.groupby(["cal_mode", "ordering", "lambda"])[
        ["swap_kind_acc", "swap_partner_acc", "value_kind_acc", "value_op_acc", "b6_op_acc"]].mean().reset_index()
    att.to_csv(run / "summary_attribution.csv", index=False)

    pd.set_option("display.width", 220)
    pd.set_option("display.max_rows", 500)
    for cm in ("injected", "clean"):
        print(f"\n===== calibration mode: {cm}  (q = {q}) =====")
        t = agg[agg.cal_mode == cm].pivot_table(index=["ordering", "method"], columns="lambda",
                                                 values="power").round(3)
        print("POWER (mean over seeds)\n", t.to_string())
        t = agg[agg.cal_mode == cm].pivot_table(index=["ordering", "method"], columns="lambda",
                                                 values="fdr").round(3)
        print("\nREALISED FDR (mean over seeds)\n", t.to_string())
    print("\n===== Full vs best baseline (power) =====")
    print(diffs.round(3).to_string(index=False))
    print("\n===== Attribution (Full; B6 = rule-based unit/decimal repair) =====")
    print(att.round(3).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1])
