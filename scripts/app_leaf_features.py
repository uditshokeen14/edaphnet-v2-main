"""App Step 3a: extract leaf-image features once (docs/24 §5, rules in doc 25 §3–4).

PlantVillage (training): one image per duplicate group (MD5 and dHash from MANIFEST.csv), at most
CAP images per class (seeded random), features from MobileNetV3-Large.
PlantDoc (cross-dataset test): duplicate groups with conflicting labels removed, one image per
remaining duplicate group, all classes mapped to PlantVillage (app/leaf/class_map.json).

Writes data/app_raw/leaf_features.npz (git-ignored). Run with the main Python:
    "C:\\Program Files\\Python314\\python.exe" scripts/app_leaf_features.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.leaf.model import features_from_paths  # noqa: E402

RAW = ROOT / "data" / "app_raw"
CAP, SEED = 600, 20261003


def dedup(df, drop_conflicts):
    if drop_conflicts:
        for key in ("md5", "dhash"):
            bad = df.groupby(key)["class"].nunique()
            df = df[~df[key].isin(bad[bad > 1].index)]
    return df.drop_duplicates("md5").drop_duplicates("dhash")


def main():
    m = pd.read_csv(RAW / "MANIFEST.csv")
    cmap = json.loads((ROOT / "app" / "leaf" / "class_map.json").read_text(encoding="utf-8"))["map"]
    pv = dedup(m[m.dataset == "plantvillage"], drop_conflicts=True)
    pv = pd.concat([g.sample(min(len(g), CAP), random_state=SEED) for _, g in pv.groupby("class")])
    pd_ = dedup(m[m.dataset == "plantdoc"], drop_conflicts=True)
    pd_ = pd_[pd_["class"].isin(cmap)].copy()
    pd_["pv_class"] = pd_["class"].map(cmap)
    print(f"PlantVillage after dedup + cap {CAP}: {len(pv)} images, {pv['class'].nunique()} classes")
    print(f"PlantDoc after cleaning: {len(pd_)} images, {pd_['class'].nunique()} classes")
    out = {}
    for name, df, base in (("pv", pv, RAW / "plantvillage" / "raw" / "color"), ("pd", pd_, RAW / "plantdoc")):
        t0 = time.time()
        paths = [str(base / p) for p in df["path"]]
        feats, keep = [], []
        for i in range(0, len(paths), 256):           # chunks: bounded memory, visible progress
            chunk = paths[i:i + 256]
            try:
                feats.append(features_from_paths(chunk))
                keep.extend(range(i, i + len(chunk)))
            except Exception as e:                   # skip a bad chunk image by image
                for j, p in enumerate(chunk):
                    try:
                        feats.append(features_from_paths([p])); keep.append(i + j)
                    except Exception:
                        print("  skipped unreadable:", p, str(e)[:60])
            print(f"  {name}: {min(i + 256, len(paths))}/{len(paths)} ({time.time() - t0:.0f}s)", flush=True)
        df = df.iloc[keep]
        out[f"{name}_X"] = np.vstack(feats)
        out[f"{name}_y"] = (df["class"] if name == "pv" else df["pv_class"]).to_numpy()
        out[f"{name}_path"] = df["path"].to_numpy()
        if name == "pd":
            out["pd_orig_class"] = df["class"].to_numpy()
            out["pd_orig_split"] = df["split"].to_numpy()
    np.savez_compressed(RAW / "leaf_features.npz", **out)
    print("saved", RAW / "leaf_features.npz")


if __name__ == "__main__":
    main()
