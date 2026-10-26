"""Step 6: process soil photos into witness features (doc 15 §5, §10).

Input
  --photos  folder with images named like the capture log: <code>_<phone>_<light>_<moisture>_<shot>.jpg
            (.npy float arrays in [0, 1] are also accepted, used for tests)
  --geometry JSON with, per image file name (or "default" for a fixed stand set-up):
            {"chart_corners": [[x,y] TL, TR, BR, BL], "soil_box": [x0, y0, x1, y1]}
Output
  CSV with one row per image: sample code, phone, lighting, moisture, shot, soil L*a*b*, within-soil
  colour spread, chart residual dE00 (colour uncertainty), blur, clipping and texture features.
  A 'usable' flag applies the quality rules below (fixed now, before any real photo exists).

Quality rules (pre-declared): chart residual dE00 <= 3.0; clipped pixels in the soil region <= 1%;
blur (variance of Laplacian on grey) >= 1e-4. Rejected photos are kept in the CSV with a reason.

    python scripts/process_photos.py --photos data/raw/photos --geometry data/raw/photos/geometry.json --out results/photos.csv
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from edaphnet2 import phone  # noqa: E402

MAX_CHART_DE, MAX_CLIPPED, MIN_BLUR = 3.0, 0.01, 1e-4
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".npy"}


def parse_name(stem):
    parts = stem.split("_")
    keys = ["sample_code", "phone_id", "lighting", "moisture", "shot"]
    return dict(zip(keys, parts + [None] * (len(keys) - len(parts))))


def process_one(img, geom, kind="rootpoly"):
    lin = phone.to_linear(img)
    meas = phone.patch_means(lin, phone.grid_centers(geom["chart_corners"]))
    ccm = phone.fit_ccm(meas, kind=kind)
    x0, y0, x1, y1 = geom["soil_box"]
    roi = np.zeros(img.shape[:2], bool)
    roi[y0:y1, x0:x1] = True
    lab, spread = phone.soil_lab(lin, roi, ccm)
    q = phone.quality(img, roi)
    tex = phone.texture_features(img, roi)
    resid = phone.chart_residual_de(meas, ccm)
    reasons = [r for r, bad in (("chart_dE", resid > MAX_CHART_DE),
                                ("clipping", q["clipped_high"] + q["clipped_low"] > MAX_CLIPPED),
                                ("blur", q["blur_laplacian_var"] < MIN_BLUR)) if bad]
    return {"L": lab[0], "a": lab[1], "b": lab[2], "L_sd": spread[0], "a_sd": spread[1], "b_sd": spread[2],
            "chart_residual_dE00": resid, **q, **tex, "usable": not reasons, "reject_reason": ";".join(reasons)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photos", required=True)
    ap.add_argument("--geometry", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ccm", default="rootpoly", choices=["rootpoly", "linear"])
    args = ap.parse_args()
    geometry = json.loads(Path(args.geometry).read_text())
    rows = []
    for f in sorted(Path(args.photos).iterdir()):
        if f.suffix.lower() not in IMAGE_EXT:
            continue
        geom = geometry.get(f.name, geometry.get("default"))
        row = {"image_file": f.name, **parse_name(f.stem)}
        if geom is None:
            rows.append({**row, "usable": False, "reject_reason": "no geometry"})
            continue
        try:
            img = np.load(f) if f.suffix == ".npy" else phone.load_image(f)
            rows.append({**row, **process_one(img, geom, args.ccm)})
        except Exception as e:   # keep going; record the failure
            rows.append({**row, "usable": False, "reject_reason": f"error: {e}"})
    df = pd.DataFrame(rows)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    n_ok = int(df["usable"].sum()) if len(df) else 0
    print(f"{len(df)} images, {n_ok} usable -> {args.out}")
    if len(df) and "sample_code" in df:
        per = df[df["usable"] == True].groupby("sample_code")[["L", "a", "b"]].agg(["mean", "std"])  # noqa: E712
        print(per.round(2).head(10).to_string())


if __name__ == "__main__":
    main()
