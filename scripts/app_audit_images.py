"""App Step 1: audit downloaded image datasets before any training (docs/24 §8).

For every image: dataset, split, class, path, size, MD5 and a 64-bit difference hash (dHash, a visual
fingerprint that survives re-compression and resizing). Reports:
  - images and classes per dataset/split,
  - exact duplicates (same MD5) and visual duplicates (same dHash), within and across splits,
  - overlap between datasets (e.g. a PlantDoc test image that also appears in PlantVillage),
  - unreadable files.
Writes data/app_raw/MANIFEST.csv and results/app_audit/<dataset>_audit.json.

Needs Pillow (main Python):  "C:\\Program Files\\Python314\\python.exe" scripts/app_audit_images.py plantdoc plantvillage
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "app_raw"
OUT = ROOT / "results" / "app_audit"
EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
LAYOUT = {  # dataset -> (folder, function(path relative to folder) -> (split, class))
    "plantdoc": ("plantdoc", lambda p: (p.parts[0], p.parts[1])),            # train|test/<class>/img
    "plantvillage": ("plantvillage/raw/color", lambda p: ("all", p.parts[0])),  # <class>/img
}


def dhash(path):
    from PIL import Image
    with Image.open(path) as im:
        g = im.convert("L").resize((9, 8))
        px = list(g.getdata())
    bits = [px[r * 9 + c] > px[r * 9 + c + 1] for r in range(8) for c in range(8)]
    return f"{sum(b << i for i, b in enumerate(bits)):016x}"


def scan(name):
    folder, split_class = LAYOUT[name]
    base = RAW / folder
    rows, bad = [], []
    for f in sorted(base.rglob("*")):
        if f.suffix.lower() not in EXT or not f.is_file():
            continue
        rel = f.relative_to(base)
        try:
            split, cls = split_class(rel)
            rows.append({"dataset": name, "split": split, "class": cls, "path": str(rel).replace("\\", "/"),
                         "bytes": f.stat().st_size, "md5": hashlib.md5(f.read_bytes()).hexdigest(), "dhash": dhash(f)})
        except Exception as e:      # unreadable or unexpected layout
            bad.append({"path": str(rel), "error": str(e)[:120]})
    return pd.DataFrame(rows), bad


def dup_report(df):
    out = {}
    for key in ("md5", "dhash"):
        g = df.groupby(key)
        sizes = g.size()
        dup_groups = sizes[sizes > 1]
        cross_split = int((g["split"].nunique() > 1).sum())
        cross_class = int((g["class"].nunique() > 1).sum())
        out[key] = {"duplicate_groups": int(len(dup_groups)), "images_in_duplicate_groups": int(dup_groups.sum()),
                    "groups_spanning_splits": cross_split, "groups_with_conflicting_classes": cross_class}
    return out


def main():
    names = sys.argv[1:] or list(LAYOUT)
    OUT.mkdir(parents=True, exist_ok=True)
    frames = []
    for name in names:
        df, bad = scan(name)
        frames.append(df)
        rep = {"dataset": name, "images": len(df), "unreadable": len(bad), "unreadable_examples": bad[:5],
               "classes": int(df["class"].nunique()) if len(df) else 0,
               "per_split": df.groupby("split").size().to_dict() if len(df) else {},
               "per_class_min_max": [int(df.groupby("class").size().min()), int(df.groupby("class").size().max())] if len(df) else None,
               "duplicates": dup_report(df) if len(df) else {}}
        (OUT / f"{name}_audit.json").write_text(json.dumps(rep, indent=1))
        df.groupby(["split", "class"]).size().rename("images").to_csv(OUT / f"{name}_class_counts.csv")
        print(json.dumps({k: v for k, v in rep.items() if k != "unreadable_examples"}, indent=1))
    allm = pd.concat(frames, ignore_index=True)
    allm.to_csv(RAW / "MANIFEST.csv", index=False)
    if len(names) > 1:
        cross = allm.groupby("dhash")["dataset"].nunique()
        n = int((cross > 1).sum())
        print(f"visual duplicates shared between datasets: {n}")
        (OUT / "cross_dataset.json").write_text(json.dumps({"shared_dhash_groups": n}, indent=1))


if __name__ == "__main__":
    main()
