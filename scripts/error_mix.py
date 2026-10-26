"""EXPLORATORY (D-025): who wins as the share of swaps among errors changes?

The registered KSSL test injected swaps and value errors in roughly equal numbers, and with a colour
witness the overall verdict depends on that mix (doc 23 §1). This script re-scores the registered
run's stored scores under other mixes. For each pool of 50 batches and each target swap share pi:
  - keep N = floor(min(#swaps, #value errors) / 0.9) errors, of which round(pi*N) are swaps
    (the same N for every pi, so only the mix changes);
  - keep clean reports in proportion N / (original #errors), so the error prevalence and the
    registered 5% re-test budget are unchanged;
  - flag the top 5% by each method's stored score (random tie-break) and count errors found.
Repeated R times with different subsamples; 95% intervals for Full minus B5 from a cluster bootstrap
over pools. Approximation: scores were computed in the original batches and are not recomputed.

Writes results/exploratory/<run>/error_mix.csv and docs/paper/figures/fig5_error_mix.png.
    "C:\\Program Files\\Python314\\python.exe" scripts/error_mix.py results/runs/<run_dir>
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from exploratory_tables import BUDGET, POOL  # noqa: E402

METHODS = ["Full", "B5_supervised", "B4_swaponly", "B1_rules"]
SHARES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
RUNGS, R, NBOOT = ["W1_dE2", "W3"], 20, 1000


def load(run):
    use = ["seed", "lambda", "ordering", "batch", "kind"] + [f"s:{m}" for m in METHODS]
    parts = [c[c["lambda"].isin(RUNGS)] for c in pd.read_csv(run / "predictions.csv.gz", usecols=use, chunksize=200_000)]
    return pd.concat(parts, ignore_index=True)


def pools_of(g):
    out = []
    for (seed, p), h in g.groupby([g["seed"], g["batch"] // POOL]):
        kind = h["kind"].to_numpy()
        assert set(kind) <= {"clean", "swap", "value"}, set(kind)
        out.append({"kind": kind, "S": {m: np.nan_to_num(h[f"s:{m}"].to_numpy(float), nan=np.inf, posinf=1e300) for m in METHODS}})
    return out


def found_counts(pool, pi, rng):
    kind = pool["kind"]
    sw, va, cl = (np.where(kind == k)[0] for k in ("swap", "value", "clean"))
    n_err = len(sw) + len(va)
    N = int(np.floor(min(len(sw), len(va)) / 0.9))
    if N < 2:
        return None
    ks = int(round(pi * N))
    keep = np.concatenate([rng.choice(sw, ks, replace=False), rng.choice(va, N - ks, replace=False),
                           rng.choice(cl, int(round(len(cl) * N / n_err)), replace=False)])
    k = int(np.ceil(BUDGET * len(keep)))
    tie = rng.random(len(keep))
    is_sw, is_va = kind[keep] == "swap", kind[keep] == "value"
    res = {"N": N, "n_swap": ks}
    for m in METHODS:
        top = np.lexsort((tie, -pool["S"][m][keep]))[:k]
        res[f"found:{m}"] = int(is_sw[top].sum() + is_va[top].sum())
        res[f"found_swap:{m}"] = int(is_sw[top].sum())
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--figure-only", action="store_true", help="redraw the figure from the saved CSV")
    args = ap.parse_args()
    run = Path(args.run)
    if args.figure_only:
        return figure(pd.read_csv(ROOT / "results" / "exploratory" / run.name / "error_mix.csv"))
    D = load(run)
    rows = []
    for (lam, ordg), g in D.groupby(["lambda", "ordering"]):
        pools = pools_of(g)
        obs = float((g["kind"] == "swap").sum() / (g["kind"] != "clean").sum())
        for pi in SHARES:
            per_pool = []                                    # pool -> mean found / N over repetitions
            for j, pool in enumerate(pools):
                acc = {m: 0.0 for m in METHODS}; NN = 0
                for r in range(R):
                    res = found_counts(pool, pi, np.random.default_rng([r, int(pi * 100), j]))
                    if res is None:
                        break
                    NN += res["N"]
                    for m in METHODS:
                        acc[m] += res[f"found:{m}"]
                if NN:
                    per_pool.append({"N": NN, **acc})
            P = pd.DataFrame(per_pool)
            rec = {m: P[m].sum() / P["N"].sum() for m in METHODS}
            boot, rng = [], np.random.default_rng(0)
            for _ in range(NBOOT):
                b = P.iloc[rng.integers(0, len(P), len(P))]
                boot.append((b["Full"].sum() - b["B5_supervised"].sum()) / b["N"].sum())
            lo, hi = np.percentile(boot, [2.5, 97.5])
            rows.append({"lambda": lam, "ordering": ordg, "swap_share": pi, "registered_share": round(obs, 3),
                         "pools": len(P), **{m: round(rec[m], 4) for m in METHODS},
                         "Full_minus_B5": round(rec["Full"] - rec["B5_supervised"], 4),
                         "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4)})
            print(rows[-1], flush=True)
    T = pd.DataFrame(rows)
    out = ROOT / "results" / "exploratory" / run.name
    out.mkdir(parents=True, exist_ok=True)
    T.to_csv(out / "error_mix.csv", index=False)
    print("wrote", out / "error_mix.csv")
    figure(T)


def figure(T):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from make_paper_figures import ACCENT, GREY, INK, LINE, MUTED, save
    t = T[T.ordering == "random"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.9), sharey=True)
    for ax, lam, title in ((axes[0], "W1_dE2", "Colour, good phone"), (axes[1], "W3", "Spectrometer")):
        s = t[t["lambda"] == lam].sort_values("swap_share")
        for m, col, ls, lab in (("Full", ACCENT, "-", "EdaphNet"), ("B5_supervised", GREY, "-", "B5 (best existing)"),
                                ("B4_swaponly", MUTED, ":", "B4 (swap matcher)"), ("B1_rules", MUTED, "--", "B1 (rules)")):
            ax.plot(s.swap_share, s[m], ls, color=col, lw=1.8 if m in ("Full", "B5_supervised") else 1.1, marker="o" if m == "Full" else None,
                    ms=3.5, label=lab)
        reg = float(s["registered_share"].iloc[0])
        ax.axvline(reg, color=LINE, lw=1.2, zorder=0)
        ax.text(reg, 0.02, " registered mix", color=MUTED, fontsize=7, va="bottom")
        ax.set_title(title, fontsize=9, color=INK); ax.set_xlabel("Share of swaps among errors")
        ax.set_xticks([0.1, 0.3, 0.5, 0.7, 0.9]); ax.set_ylim(0, 0.75)
        ax.grid(color=LINE, lw=0.6); ax.set_axisbelow(True)
    axes[0].set_ylabel("Errors found at 5% re-test budget")
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, frameon=False, fontsize=7.5, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.06))
    fig.subplots_adjust(bottom=0.24)
    save(fig, "fig5_error_mix.png")


if __name__ == "__main__":
    main()
