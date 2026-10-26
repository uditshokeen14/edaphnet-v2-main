"""Paper figures, generated only from committed run records (no numbers typed by hand).

  fig1_witness_r2.png     R² by witness and property (KSSL + ICRAF witness ladders)
  fig2_kssl_recall.png    pre-registered KSSL test: recall at 5% budget, EdaphNet vs best baseline
  fig3_swap_vs_value.png  exploratory: Full minus B5 for swaps and for value errors, by witness
  fig4_pool_size.png      exploratory: BH power vs pool size (stored p-values), Full vs B5

Needs matplotlib (main Python):  "C:\\Program Files\\Python314\\python.exe" scripts/make_paper_figures.py
"""
import re
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper" / "figures"
RUN = "20261001-234902_real_kssl3_095deaa"
INK, MUTED, ACCENT, BAR, LINE, GREY = "#1c2220", "#59645f", "#7a5520", "#c9b28c", "#d6ddd9", "#9aa6a1"
RUNGS = ["W0", "W1_dE0", "W1_dE2", "W1_dE4", "W3"]
RUNG_LABEL = {"W0": "None", "W1_dE0": "Colour\n(perfect)", "W1_dE2": "Colour\n(good phone)",
              "W1_dE4": "Colour\n(noisy phone)", "W3": "Spectro-\nmeter"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": LINE, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT / name)


def fig1():
    lk = pd.read_csv(ROOT / "results/runs/20261001-234621_witness_ladder_kssl3_8148163/witness_ladder_metrics.csv")
    li = pd.read_csv(ROOT / "results/runs/20260925-003906_witness_ladder_icraf8_7050ab6/witness_ladder_metrics.csv")
    rows = [("KSSL", lk, p) for p in ("OC", "N", "Ctot")] + [("ICRAF", li, p) for p in ("OC", "pH", "Ca", "clay", "CEC", "K", "sand")]
    get = lambda df, r, p: max(0.0, float(df[(df.rung == r) & (df.property == p)]["r2_latent_test"].iloc[0]))  # noqa: E731
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    x = range(len(rows))
    for off, rung, col, lab in ((-0.27, "W1_dE0", "#e2d3b5", "Colour, perfect"), (0, "W1_dE2", BAR, "Colour, good phone (ΔE 2)"),
                                (0.27, "W3", ACCENT, "Spectrometer")):
        ax.bar([v + off for v in x], [get(df, rung, p) for _, df, p in rows], 0.27, color=col, label=lab)
    ax.set_xticks(list(x), [f"{p}\n{d}" for d, _, p in rows])
    ax.set_ylim(0, 1); ax.set_ylabel("R² (unseen locations)")
    ax.grid(axis="y", color=LINE, lw=0.6); ax.set_axisbelow(True)
    ax.axvline(2.5, color=LINE, lw=1)
    ax.legend(frameon=False, ncol=3, loc="upper right", fontsize=8)
    save(fig, "fig1_witness_r2.png")


def fig2():
    a = pd.read_csv(ROOT / "results/runs" / RUN / "amendment_A1.csv")
    a = a[a.ordering == "random"].set_index("lambda").loc[RUNGS]
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    x = range(len(a))
    ax.bar([v - 0.2 for v in x], a["best_recall"], 0.4, color=GREY, label="Best existing method (B5)")
    ax.bar([v + 0.2 for v in x], a["full_recall"], 0.4, color=ACCENT, label="EdaphNet")
    lo, hi = a["best_recall"] + a["ci_low"], a["best_recall"] + a["ci_high"]
    ax.errorbar([v + 0.2 for v in x], a["full_recall"], yerr=[a["full_recall"] - lo, hi - a["full_recall"]],
                fmt="none", ecolor=INK, capsize=3, lw=1)
    for v, d in zip(x, a["diff"]):
        ax.text(v, 0.02, f"{d:+.3f}", ha="center", color="white", fontsize=8, fontweight="bold")
    ax.set_xticks(list(x), [RUNG_LABEL[r] for r in RUNGS]); ax.set_ylim(0, 0.75)
    ax.set_ylabel("Errors found\n(top 5% re-tested)")
    ax.grid(axis="y", color=LINE, lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    save(fig, "fig2_kssl_recall.png")


def parse_ci(s):
    m = re.match(r"([+-][\d.]+) \[([+-][\d.]+), ([+-][\d.]+)\]", str(s))
    return tuple(float(v) for v in m.groups()) if m else (float("nan"),) * 3


def fig3():
    t = pd.read_csv(ROOT / "results/exploratory" / RUN / "swap_value_ablation.csv")
    t = t[(t.ordering == "random")]
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    for k, (subset, col, lab) in enumerate((("swaps", ACCENT, "Swapped samples"), ("value errors", GREY, "Wrong values"))):
        est = [parse_ci(t[(t["lambda"] == r) & (t.subset == subset)]["Full-best [95% CI]"].iloc[0]) for r in RUNGS]
        xs = [v + (k - 0.5) * 0.3 for v in range(len(RUNGS))]
        ax.bar(xs, [e[0] for e in est], 0.3, color=col, label=lab)
        ax.errorbar(xs, [e[0] for e in est], yerr=[[e[0] - e[1] for e in est], [e[2] - e[0] for e in est]],
                    fmt="none", ecolor=INK, capsize=3, lw=1)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(range(len(RUNGS)), [RUNG_LABEL[r] for r in RUNGS])
    ax.set_ylabel("EdaphNet minus B5\n(errors found, top 5%)")
    ax.grid(axis="y", color=LINE, lw=0.6); ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    save(fig, "fig3_swap_vs_value.png")


def fig4():
    t = pd.read_csv(ROOT / "results/exploratory" / RUN / "rescore_pools.csv")
    t = t[t.ordering == "random"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.7), sharey=True)
    for ax, rung, title in ((axes[0], "W1_dE2", "Colour, good phone"), (axes[1], "W3", "Spectrometer")):
        both = {m: t[(t["lambda"] == rung) & (t.method == m)].set_index("pool_batches").sort_index()
                for m in ("Full", "B5_supervised")}
        for m, col, lab in (("Full", ACCENT, "EdaphNet"), ("B5_supervised", GREY, "B5")):
            s, other = both[m], both["B5_supervised" if m == "Full" else "Full"]
            ax.plot(s.index, s.power, "-o", color=col, label=lab, ms=4)
            for pb, r in s.iterrows():   # label above the higher point, below the lower one: no overlaps
                low = min(r.power, float(other["power"][pb])) < 0.07          # lower label would hit the axis:
                dy = 7 if r.power >= float(other["power"][pb]) else -13      # stack both labels above instead
                if low:
                    dy = 18 if r.power >= float(other["power"][pb]) else 6
                ax.annotate(f"{r.fdr:.2f}", (pb, r.power), textcoords="offset points", xytext=(0, dy),
                            ha="center", fontsize=7, color=col)
        ax.set_ylim(0, max(float(both[m].power.max()) for m in both) * 1.25)
        ax.set_xscale("log"); ax.set_xticks([1, 5, 10, 50], ["1", "5", "10", "50\n(registered)"])
        ax.set_title(title, fontsize=9, color=INK); ax.set_xlabel("Pool size (batches of 24)")
        ax.grid(color=LINE, lw=0.6); ax.set_axisbelow(True)
    axes[0].set_ylabel("Power at q = 0.10\n(labels: realised FDR)")
    axes[0].legend(frameon=False, fontsize=8)
    save(fig, "fig4_pool_size.png")


def fig0():
    """Method overview (drawn, no data)."""
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    ax.set_xlim(0, 100); ax.set_ylim(0, 40); ax.axis("off")

    def box(x, y, w, h, title, body, fill="#ffffff", edge=LINE):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fill, ec=edge, lw=1))
        ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="top", fontsize=8.2, fontweight="bold", color=INK)
        ax.text(x + w / 2, y + h - 6.4, body, ha="center", va="top", fontsize=6.5, color=MUTED, linespacing=1.35)

    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=9, color=ACCENT, lw=1.2,
                                     shrinkA=0, shrinkB=0))

    box(0.5, 23, 16, 15, "Lab batch", "24 reports\n(OC, N, total C …)\nas printed")
    box(0.5, 2, 16, 15, "Witness", "independent look\nat each sample:\ncolour or spectrum")
    box(20.5, 2, 17, 15, "Witness model", "predicts each\nsample's properties\nwith uncertainty\n(μ, Σ)")
    box(41.5, 10, 31, 28, "Joint batch inference", "all hypotheses scored together\n\nno error\nswaps: neighbours, shifted rows,\nrandom pairs\n"
        "value errors: ×10, ÷10, digit\ntransposition, unit, column swap,\ngross", fill="#f6efe4", edge=ACCENT)
    box(76.5, 23, 22.5, 15, "Per report", "suspicion score,\nmost likely error,\nsuggested correction")
    box(76.5, 2, 22.5, 15, "Lab decision", "re-test the top 5%\n(or conformal p-values\n+ BH at q = 0.10)")
    arrow(17.3, 9.5, 19.7, 9.5)            # witness -> witness model
    arrow(38.3, 9.5, 40.7, 15)             # witness model -> inference
    arrow(17.3, 30.5, 40.7, 30.5)          # lab batch -> inference
    arrow(73.3, 30.5, 75.7, 30.5)          # inference -> per report
    arrow(87.75, 22.2, 87.75, 17.8)        # per report -> decision
    save(fig, "fig0_method.png")


if __name__ == "__main__":
    fig0(); fig1(); fig2(); fig3(); fig4()
