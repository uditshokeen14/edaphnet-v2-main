"""EXPLORATORY (D-025): why does Full find so few gross analytical errors on KSSL?

Doc 23 reports gross-error recall at a 5% budget of 0.03 for Full vs 0.26 for B5 (W1 ΔE2, random), and
a review noted that several Full variants give exactly the same value. This script reads the
registered run's predictions (chunked, read-only) and reports, per witness rung and ordering:
  1. gross-error recall at the 5% budget for every method (same flagging rule as
     scripts/exploratory_tables.py, including its shared random tie-break);
  2. how many gross errors each Full variant scores exactly 0 (ties), and whether the budget cut
     falls inside that tie, which would make variants share identical flags;
  3. where gross errors rank inside their pool (median percentile of the score);
  4. what Full thinks a flagged/unflagged gross error is (full_kind / full_op group);
  5. recall split by affected property (G@OC, G@N, G@Ctot).
Outputs go to results/exploratory/<run name>/gross_*.csv, never into the run folder.

    python scripts/diag_gross.py results/runs/<run_dir>
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from exploratory_tables import BUDGET, POOL  # noqa: E402


def pool_stats(g, methods, seed):
    """Flags (inside 5% budget), score percentile within pool, and the score at the budget cut."""
    rng = np.random.default_rng(int(seed))
    n = len(g)
    flags = {m: np.zeros(n, bool) for m in methods}
    pct = {m: np.zeros(n) for m in methods}
    cut_zero = {m: 0 for m in methods}
    pools = g["batch"].to_numpy() // POOL
    for p in np.unique(pools):
        idx = np.where(pools == p)[0]
        k = int(np.ceil(BUDGET * len(idx)))
        tie = rng.random(len(idx))
        for m in methods:
            s = np.nan_to_num(g[f"s:{m}"].to_numpy(float)[idx], nan=np.inf, posinf=1e300)
            order = np.lexsort((tie, -s))
            flags[m][idx[order[:k]]] = True
            rank = np.empty(len(idx)); rank[order] = np.arange(len(idx))
            pct[m][idx] = 1 - rank / max(1, len(idx) - 1)          # 1 = most suspicious
            cut_zero[m] += int(s[order[k - 1]] <= 0)               # budget cut inside the zero-score tie
    return flags, pct, cut_zero, len(np.unique(pools))


def op_group(kind, op):
    if kind in ("clean", "none") or not isinstance(op, str):
        return str(kind)
    return f"{kind}:{op.split('@')[0]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    args = ap.parse_args()
    run = Path(args.run)
    head = pd.read_csv(run / "predictions.csv.gz", nrows=0).columns
    methods = [c[2:] for c in head if c.startswith("s:")]
    use = ["seed", "lambda", "ordering", "batch", "kind", "true_op", "full_kind", "full_op"] + [f"s:{m}" for m in methods]
    recs, cuts = [], []
    for chunk in pd.read_csv(run / "predictions.csv.gz", usecols=use, chunksize=100_000):
        for (seed, lam, ordg), g in chunk.groupby(["seed", "lambda", "ordering"]):
            g = g.reset_index(drop=True)
            fl, pct, cz, npool = pool_stats(g, methods, seed)
            cuts.append({"lambda": lam, "ordering": ordg, "pools": npool, **{f"cut_at_zero:{m}": cz[m] for m in methods}})
            gross = g["true_op"].astype(str).str.startswith("G@").to_numpy()
            if not gross.any():
                continue
            d = g.loc[gross, ["true_op", "full_kind", "full_op"]].copy()
            d["lambda"], d["ordering"] = lam, ordg
            d["prop"] = d["true_op"].str.split("@").str[1]
            d["full_says"] = [op_group(k, o) for k, o in zip(d["full_kind"], d["full_op"])]
            for m in methods:
                d[f"flag:{m}"] = fl[m][gross]
                d[f"pct:{m}"] = pct[m][gross]
                d[f"zero:{m}"] = g.loc[gross, f"s:{m}"].to_numpy(float) <= 0
            recs.append(d)
    R = pd.concat(recs, ignore_index=True)
    C = pd.DataFrame(cuts).groupby(["lambda", "ordering"]).sum(numeric_only=True).reset_index()
    out = ROOT / "results" / "exploratory" / run.name
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for (lam, ordg), g in R.groupby(["lambda", "ordering"]):
        c = C[(C["lambda"] == lam) & (C["ordering"] == ordg)].iloc[0]
        for m in methods:
            rows.append({"lambda": lam, "ordering": ordg, "method": m, "n_gross": len(g),
                         "recall_at_5pct": round(float(g[f"flag:{m}"].mean()), 4),
                         "share_scored_zero": round(float(g[f"zero:{m}"].mean()), 3),
                         "median_pool_percentile": round(float(g[f"pct:{m}"].median()), 3),
                         "pools_cut_inside_zero_tie": f"{int(c[f'cut_at_zero:{m}'])}/{int(c['pools'])}"})
    T = pd.DataFrame(rows)
    T.to_csv(out / "gross_recall_by_method.csv", index=False)

    says = (R.groupby(["lambda", "ordering", "flag:Full", "full_says"]).size().rename("n").reset_index()
            .sort_values(["lambda", "ordering", "flag:Full", "n"], ascending=[True, True, True, False]))
    says.to_csv(out / "gross_full_explanations.csv", index=False)
    prop = (R.groupby(["lambda", "ordering", "prop"])[["flag:Full", "flag:B5_supervised", "flag:B1_rules"]].mean()
            .round(3).reset_index())
    prop.to_csv(out / "gross_recall_by_property.csv", index=False)

    pd.set_option("display.width", 200)
    focus = T[T["method"].isin(["Full", "Full-noswap", "Full-uniformprior", "Full-nolibrary", "Full-nowitness",
                                "B1_rules", "B5_supervised", "B4_swaponly"])]
    print(focus.to_string(index=False))
    print("\nWhat Full says about gross errors (W1_dE2, random):")
    print(says[(says["lambda"] == "W1_dE2") & (says["ordering"] == "random")].head(12).to_string(index=False))
    print("\nRecall by affected property:")
    print(prop.to_string(index=False))
    print("\nwritten to", out)


if __name__ == "__main__":
    main()
