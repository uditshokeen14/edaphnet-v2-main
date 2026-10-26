"""App Step 1: build app/knowledge/crops.json from FAO ECOCROP (OpenCLIM copy of EcoCrop_DB.csv).

Only crops common in India are kept. Every value is copied from one ECOCROP row (identified by its
EcoPortCode), so each number is traceable. Missing values stay missing (no guessing).

    python scripts/app_build_crops.py
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "app_raw" / "ecocrop" / "EcoCrop_DB.csv"
OUT = ROOT / "app" / "knowledge" / "crops.json"

# common Indian crops: (name shown in the app, ECOCROP scientific name)
CROPS = [
    ("Rice", "Oryza sativa"), ("Wheat", "Triticum aestivum"), ("Maize", "Zea mays"),
    ("Sorghum (jowar)", "Sorghum bicolor"), ("Pearl millet (bajra)", "Pennisetum glaucum"),
    ("Finger millet (ragi)", "Eleusine coracana ssp. coracana"), ("Chickpea (chana)", "Cicer arietinum"),
    ("Pigeon pea (arhar/tur)", "Cajanus cajan"), ("Green gram (moong)", "Vigna radiata"),
    ("Black gram (urad)", "Vigna mungo"), ("Groundnut", "Arachis hypogaea"), ("Soybean", "Glycine max"),
    ("Mustard", "Brassica juncea"), ("Sesame (til)", "Sesamum indicum"), ("Cotton", "Gossypium hirsutum"),
    ("Sugarcane", "Saccharum officinarum"), ("Potato", "Solanum tuberosum"), ("Tomato", "Lycopersicon esculentum"),
    ("Onion", "Allium cepa"), ("Chilli", "Capsicum annuum"), ("Okra (bhindi)", "Abelmoschus esculentus"),
    ("Banana", "Musa acuminata"), ("Mango", "Mangifera indica"), ("Tea", "Camellia sinensis"),
    ("Turmeric", "Curcuma longa"),
]
FIELDS = {"temp_opt": ("TOPMN", "TOPMX"), "temp_abs": ("TMIN", "TMAX"),
          "rain_opt": ("ROPMN", "ROPMX"), "rain_abs": ("RMIN", "RMAX"),
          "ph_opt": ("PHOPMN", "PHOPMX"), "ph_abs": ("PHMIN", "PHMAX")}
TEXT = {"texture_opt": "TEXT", "texture_abs": "TEXTR", "depth_opt": "DEP", "drainage_opt": "DRA",
        "salinity_opt": "SAL", "fertility_opt": "FER"}


def num(v):
    try:
        f = float(v)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def main():
    df = pd.read_csv(SRC, encoding="latin-1", low_memory=False)
    md5 = hashlib.md5(SRC.read_bytes()).hexdigest()
    out, missing = [], []
    for name, sci in CROPS:
        hit = df[df["ScientificName"].str.strip().str.lower() == sci.lower()]
        if hit.empty:
            missing.append(sci)
            continue
        r = hit.iloc[0]
        crop = {"name": name, "scientific_name": sci, "ecoport_code": int(r["EcoPortCode"]),
                "units": {"temp": "degC", "rain": "mm/year", "ph": "pH"}}
        for k, (lo, hi) in FIELDS.items():
            crop[k] = [num(r[lo]), num(r[hi])]
        for k, col in TEXT.items():
            v = r[col]
            crop[k] = None if pd.isna(v) else str(v).strip()
        out.append(crop)
    OUT.write_text(json.dumps({"source": "FAO EcoCrop via OpenCLIM/ecocrop EcoCrop_DB.csv (OGL v3)",
                               "source_md5": md5, "crops": out}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} crops written to {OUT}; not found: {missing}")
    for c in out[:6]:
        print(f"  {c['name']:24s} pH opt {c['ph_opt']}  rain opt {c['rain_opt']}  temp opt {c['temp_opt']}  texture {c['texture_opt']}")


if __name__ == "__main__":
    main()
