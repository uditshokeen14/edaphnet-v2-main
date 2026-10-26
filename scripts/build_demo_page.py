"""Build demo_site/index.html: a self-contained page (no server, no internet) for presenting the
project. Demo batches are computed here with the real model on real KSSL test samples; every
result number is read from a committed run record, never typed by hand.

    python scripts/build_demo_page.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from edaphnet2 import baselines as B  # noqa: E402
from edaphnet2.inference import InferenceConfig, infer_batch  # noqa: E402
from edaphnet2.witness import FixedGaussianModel  # noqa: E402
from run_real import load  # noqa: E402

RUN_KSSL = ROOT / "results/runs/20261001-234902_real_kssl3_095deaa"
RUN_ICRAF = ROOT / "results/runs/20260925-011337_real_icraf8_2be2820"
LADDER_KSSL = ROOT / "results/runs/20261001-234621_witness_ladder_kssl3_8148163"
LADDER_ICRAF = ROOT / "results/runs/20260925-003906_witness_ladder_icraf8_7050ab6"
WITNESSES = {"W0": "No photo", "W1_dE2": "Phone colour", "W3": "Spectrometer"}
N_BATCHES, N = 12, 12


def human(op, names):
    if op == "none":
        return ""
    kind, _, target = op.partition("@")
    if kind == "x10":
        return f"{target} looks 10× too high"
    if kind == "/10":
        return f"{target} looks 10× too low"
    if kind == "TR":
        return f"digits of {target} look transposed"
    if kind == "CS":
        a, b = target.split("<->")
        return f"{a} and {b} look swapped"
    if kind == "G":
        return f"{target} looks off (analytical error)"
    return f"{target}: {kind}"


def lab_to_hex(lab):
    import warnings
    warnings.filterwarnings("ignore")
    import colour
    white = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]
    rgb = colour.XYZ_to_sRGB(colour.Lab_to_XYZ(lab, white))
    rgb = np.clip(rgb, 0, 1)
    return "#" + "".join(f"{int(round(v * 255)):02x}" for v in rgb)


def demo_batches():
    D, Wt, space = load("kssl3")
    names = list(space.names)
    Y = space.print_values(D["X"])
    test = np.where(D["split"] == "test")[0]
    pop = FixedGaussianModel(Wt["W0__S"])
    cfg = InferenceConfig(rho=0.1, eps=0.05, space=space)
    out = []
    for seed in range(1, N_BATCHES + 1):
        rng = np.random.default_rng(seed)
        idx = rng.choice(test, N, replace=False)
        truth = Y[idx]
        rep = truth.copy()
        a, b = sorted(int(v) for v in rng.choice(N, 2, replace=False))
        rep[[a, b]] = rep[[b, a]]
        c = int(rng.choice([j for j in range(N) if j not in (a, b)]))
        k = int(rng.integers(len(names)))
        rep[c, k] = space.print_values((rep[c] * np.where(np.arange(len(names)) == k, 10, 1))[None])[0, k]
        lab_only = B.population_score(rep, pop, space, pop_mean=np.zeros(space.P))
        batch = {"id": seed, "names": names, "planted": {"swap": [a, b], "value": [c, names[k]]},
                 "reports": rep.round(4).tolist(), "truth": truth.round(4).tolist(),
                 "colour": [lab_to_hex(l) for l in D["lab"][idx]],
                 "lab_only_score": np.round(lab_only, 3).tolist(), "witness": {}}
        for w in WITNESSES:
            r = infer_batch(rep, Wt[f"{w}__mu"][idx], FixedGaussianModel(Wt[f"{w}__S"]), cfg)
            rows = []
            for j in range(N):
                if r["kind"][j] == "swap" and r["partner"][j] >= 0:
                    why, fix = f"looks swapped with #{int(r['partner'][j]) + 1}", None
                else:
                    g, op, y, _ = r["value_op"][j]
                    why = human(op, names) if g != "none" else ""
                    fix = [float(v) for v in np.round(y, 4)] if g != "none" else None
                rows.append({"score": round(float(r["score"][j]), 3), "why": why, "fix": fix})
            batch["witness"][w] = rows
        out.append(batch)
    return out


def results():
    lk = pd.read_csv(LADDER_KSSL / "witness_ladder_metrics.csv")
    li = pd.read_csv(LADDER_ICRAF / "witness_ladder_metrics.csv")
    pick = lambda df, rung, props: {p: round(float(df[(df.rung == rung) & (df.property == p)]["r2_latent_test"].iloc[0]), 2) for p in props}  # noqa: E731
    ladder = {"kssl": {w: pick(lk, w, ["OC", "N", "Ctot"]) for w in ("W1_dE0", "W1_dE2", "W1_dE4", "W3")},
              "icraf": {w: pick(li, w, ["OC", "pH", "Ca", "clay", "CEC", "K", "sand"]) for w in ("W1_dE0", "W1_dE2", "W1_dE4", "W3")}}
    a1 = pd.read_csv(RUN_KSSL / "amendment_A1.csv")
    a1 = a1[a1.ordering == "random"]
    order = ["W0", "W1_dE0", "W1_dE2", "W1_dE4", "W3"]
    a1_rows = [{"rung": r, **{k: round(float(a1[a1["lambda"] == r][k].iloc[0]), 3)
                               for k in ("full_recall", "best_recall", "diff", "ci_low", "ci_high")},
                "best": str(a1[a1["lambda"] == r]["best_baseline"].iloc[0])} for r in order]
    verdict = json.loads((RUN_KSSL / "amendment_verdict.json").read_text())
    det = pd.read_csv(RUN_ICRAF / "detectability_table.csv")
    det = det[det.ordering == "random"]
    det_rows = []
    for fam in ["swap", "column-swap", "decimal", "unit", "gross", "digit-transposition"]:
        row = {"family": fam}
        for w in ("W0", "W1_dE0", "W3"):
            x = det[(det.family == fam) & (det["lambda"] == w)]
            row[w] = {"full": round(float(x["full"].iloc[0]), 2), "gain": round(float(x["gain"].iloc[0]), 2)}
        det_rows.append(row)
    return {"ladder": ladder, "a1": a1_rows, "verdict": verdict, "detectability": det_rows,
            "runs": {"kssl": RUN_KSSL.name, "icraf": RUN_ICRAF.name}}


def main():
    data = {"batches": demo_batches(), "results": results(), "witnesses": WITNESSES}
    tpl = (ROOT / "demo_site" / "template.html").read_text(encoding="utf-8")
    page = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
    # web version (fragment; the hosting viewer adds the document skeleton)
    (ROOT / "demo_site" / "web.html").write_text(page, encoding="utf-8")
    # standalone version: double-click to open in any browser, works offline
    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '</head>\n<body>\n')
    full = head + page + "\n</body>\n</html>\n"
    (ROOT / "demo_site" / "index.html").write_text(full, encoding="utf-8")
    print("wrote demo_site/index.html and web.html", f"({len(full) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
