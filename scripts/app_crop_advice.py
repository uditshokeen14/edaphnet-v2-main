"""Crop suitability advice from the command line (app layer, docs/24 §4).

    python scripts/app_crop_advice.py --ph 6.5 --rain 1200 --temp 26
    python scripts/app_crop_advice.py --ph-range 5.5 7.5 --rain 800 --temp 24 --texture medium
    python scripts/app_crop_advice.py --ph 8.0 --rain 400 --temp 24 --irrigated

Scores: 1 = every factor inside the crop's optimal EcoCrop range; 0 = some factor outside its
absolute range. "Limited by" names the factor that keeps the score down.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.crop.suitability import Field, ph_range_scenarios, rank_crops  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--ph", type=float, help="measured soil pH")
    g.add_argument("--ph-range", type=float, nargs=2, metavar=("LOW", "HIGH"), help="pH known only as a range")
    ap.add_argument("--rain", type=float, required=True, help="annual rainfall, mm")
    ap.add_argument("--temp", type=float, required=True, help="mean temperature in the growing season, deg C")
    ap.add_argument("--texture", choices=["light", "medium", "heavy"])
    ap.add_argument("--irrigated", action="store_true")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    scen = (ph_range_scenarios(*a.ph_range, a.rain, a.temp, a.texture, a.irrigated) if a.ph_range
            else Field(a.ph, a.rain, a.temp, a.texture, a.irrigated))
    res = rank_crops(scen)
    multi = bool(a.ph_range)
    print(f"{'Crop':26s} {'score':>6s}" + (f" {'worst':>6s}" if multi else "") + "  limited by / factor scores")
    for r in res[: a.top]:
        fac = ", ".join(f"{k} {v:.2f}" for k, v in r.factors.items())
        lim = "" if r.limiting == "none" else f"limited by {r.limiting}; "
        nd = f"  (no EcoCrop data: {', '.join(r.no_data)})" if r.no_data else ""
        print(f"{r.name:26s} {r.score:6.2f}" + (f" {r.worst_score:6.2f}" if multi else "") + f"  {lim}{fac}{nd}")
    print("\nSource: FAO EcoCrop ranges (app/knowledge/crops.json). Advice only; confirm with your local "
          "agriculture officer.")


if __name__ == "__main__":
    main()
