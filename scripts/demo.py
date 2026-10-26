"""Demo: check one lab batch of REAL soil reports (KSSL test split, never used for training) with
two planted mistakes, and print which reports to re-test, why, and the suggested correction.

    python scripts/demo.py                    # colour witness with phone-like noise (dE 2)
    python scripts/demo.py --witness W3       # full spectrometer witness
    python scripts/demo.py --seed 7           # a different random batch and different mistakes

Honest framing: this shows ONE batch. Whether the planted mistakes are found depends on the soils
drawn. Across 300 x 5 test batches (doc 21), with a colour witness the method found ~44% of
swapped reports and ~38% of wrong values within a 5% re-test budget; with a spectrometer, ~75%
of swaps.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from edaphnet2 import baselines as B  # noqa: E402
from edaphnet2.inference import InferenceConfig, infer_batch  # noqa: E402
from edaphnet2.witness import FixedGaussianModel  # noqa: E402
from run_real import load  # noqa: E402

WITNESS_NAMES = {"W0": "no witness", "W1_dE0": "colour (perfect capture)", "W1_dE2": "colour (good phone)",
                 "W1_dE4": "colour (noisy phone)", "W3": "full Vis-NIR spectrometer"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="kssl3")
    ap.add_argument("--witness", default="W1_dE2", choices=list(WITNESS_NAMES))
    ap.add_argument("--n", type=int, default=12, help="batch size")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--budget", type=int, default=2, help="how many reports the lab can re-test")
    args = ap.parse_args()

    D, Wt, space = load(args.tag)
    names = list(space.names)
    Y = space.print_values(D["X"])
    test = np.where(D["split"] == "test")[0]
    rng = np.random.default_rng(args.seed)
    idx = rng.choice(test, args.n, replace=False)
    truth = Y[idx]
    reports = truth.copy()

    # plant mistake 1: two reports swapped (pair of tray positions)
    a, b = sorted(rng.choice(args.n, 2, replace=False))
    reports[[a, b]] = reports[[b, a]]
    # plant mistake 2: a decimal slip (x10) on one value of another report
    c = int(rng.choice([j for j in range(args.n) if j not in (a, b)]))
    k = int(rng.integers(len(names)))
    reports[c, k] = space.print_values((reports[c] * np.where(np.arange(len(names)) == k, 10, 1))[None])[0, k]

    MU = Wt[f"{args.witness}__mu"][idx]
    model = FixedGaussianModel(Wt[f"{args.witness}__S"])
    cfg = InferenceConfig(rho=0.1, eps=0.05, space=space)
    out = infer_batch(reports, MU, model, cfg)
    lab_only = B.population_score(reports, FixedGaussianModel(Wt["W0__S"]), space, pop_mean=np.zeros(space.P))

    order = np.argsort(-out["score"])
    rank = np.empty(args.n, int)
    rank[order] = np.arange(1, args.n + 1)
    rank_lab = np.empty(args.n, int)
    rank_lab[np.argsort(-lab_only)] = np.arange(1, args.n + 1)

    print("=" * 96)
    print(f"EdaphNet demo: one lab batch of {args.n} real soil reports (KSSL, unseen test samples)")
    print(f"Witness: {WITNESS_NAMES[args.witness]}   |   Re-test budget: {args.budget} reports")
    print(f"Planted mistakes: reports #{a + 1} and #{b + 1} SWAPPED; report #{c + 1} has {names[k]} x10")
    print("=" * 96)
    hdr = f"{'#':>3} {'reported ' + ' / '.join(names):<34} {'score':>6} {'rank':>4} {'lab-only rank':>13}  explanation"
    print(hdr)
    print("-" * 96)
    for j in order:
        vals = " / ".join(f"{v:g}" for v in reports[j])
        if out["kind"][j] == "swap" and out["partner"][j] >= 0:
            why = f"looks SWAPPED with #{out['partner'][j] + 1}"
        else:
            g, op, y, pr = out["value_op"][j]
            why = f"value error {op}: suggest {' / '.join(f'{v:.3g}' for v in y)}" if g != "none" else ""
        flag = " <= RE-TEST" if rank[j] <= args.budget else ""
        planted = " [planted]" if j in (a, b, c) else ""
        print(f"{j + 1:>3} {vals:<34} {out['score'][j]:>6.3f} {rank[j]:>4} {rank_lab[j]:>13}  "
              f"{why if out['score'][j] > 0.2 else ''}{flag}{planted}")
    print("-" * 96)
    found = [p for p in (a, b, c) if rank[p] <= args.budget]
    found_lab = [p for p in (a, b, c) if rank_lab[p] <= args.budget]
    print(f"Planted mistakes inside the re-test budget: EdaphNet {len(found)}/3, lab-only check {len(found_lab)}/3")
    print(f"Truth for #{c + 1}: {' / '.join(f'{v:g}' for v in truth[c])}   "
          f"(#{a + 1} true: {' / '.join(f'{v:g}' for v in truth[a])}, #{b + 1} true: {' / '.join(f'{v:g}' for v in truth[b])})")
    print("Note: one batch is an illustration, not evidence. See docs/21 for the pre-registered results.")


if __name__ == "__main__":
    main()
