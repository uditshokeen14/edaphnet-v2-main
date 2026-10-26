"""Step 4a: OSSL data audit (doc 11 §4: property list is fixed after this audit).

Answers, for OSSL samples that have a Vis-NIR scan and an open licence:
  - how many samples / locations per dataset,
  - coverage of each candidate property (and of combinations),
  - which grouping key to use for site-grouped splits.

    python scripts/ossl_audit.py
Outputs: results/data_audit/ (json + csv + md). No modelling happens here.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ossl"
OUT = ROOT / "results" / "data_audit"

EXCLUDED_LICENCES = {"JRC License Agreement"}   # LUCAS: redistribution restricted

CANDIDATES = {
    "pH": "ph.h2o_usda.a268_index",
    "OC": "oc_usda.c729_w.pct",
    "N": "n.tot_usda.a623_w.pct",
    "clay": "clay.tot_usda.a334_w.pct",
    "sand": "sand.tot_usda.c60_w.pct",
    "silt": "silt.tot_usda.c62_w.pct",
    "CEC": "cec_usda.a723_cmolc.kg",
    "K": "k.ext_usda.a725_cmolc.kg",
    "Ca": "ca.ext_usda.a722_cmolc.kg",
    "Mg": "mg.ext_usda.a724_cmolc.kg",
    "EC": "ec_usda.a364_ds.m",
    "CaCO3": "caco3_usda.a54_w.pct",
    "P_a274": "p.ext_usda.a274_mg.kg",
    "P_a270": "p.ext_usda.a270_mg.kg",
    "P_a1070": "p.ext_usda.a1070_mg.kg",
}
CORE = ["pH", "OC", "N", "clay", "sand", "CEC", "K", "Ca"]   # doc 11 §4 candidate list
KEY = ["dataset.code_ascii_txt", "id.layer_uuid_txt"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    site = pd.read_csv(RAW / "ossl_soilsite_L0_v1.2.csv.gz", low_memory=False)
    lab = pd.read_csv(RAW / "ossl_soillab_L1_v1.2.csv.gz", low_memory=False)
    vis_meta = pd.read_csv(RAW / "ossl_visnir_L0_v1.2.csv.gz",
                           usecols=KEY + ["scan.visnir.model.name_utf8_txt",
                                          "scan.visnir.method.preparation_any_txt"], dtype=str)
    wl = [c for c in pd.read_csv(RAW / "ossl_visnir_L0_v1.2.csv.gz", nrows=0).columns
          if c.startswith("scan_visnir.")]

    df = vis_meta.drop_duplicates(KEY).merge(lab, on=KEY, how="inner").merge(
        site[KEY + ["id.location_olc_txt", "id.dataset.site_ascii_txt",
                    "dataset.license.title_ascii_txt", "layer.upper.depth_usda_cm",
                    "location.country_iso.3166_txt"]], on=KEY, how="left")
    n_all = len(df)
    df = df[~df["dataset.license.title_ascii_txt"].isin(EXCLUDED_LICENCES)].copy()

    # grouping key: location code if present, else dataset site id, else the layer itself
    df["group"] = (df["id.location_olc_txt"].fillna(df["id.dataset.site_ascii_txt"])
                   .fillna(df["id.layer_uuid_txt"]))
    df["group"] = df["dataset.code_ascii_txt"] + "|" + df["group"].astype(str)

    per_ds = df.groupby("dataset.code_ascii_txt").agg(
        samples=("id.layer_uuid_txt", "size"), groups=("group", "nunique"),
        licence=("dataset.license.title_ascii_txt", "first"))

    cov = pd.DataFrame({name: df.groupby("dataset.code_ascii_txt")[col].apply(lambda s: s.notna().sum())
                        for name, col in CANDIDATES.items()})
    cov.loc["TOTAL"] = cov.sum()

    have = {name: df[col].notna() for name, col in CANDIDATES.items()}
    combos = {}
    for label, props in {
        "core8": CORE,
        "core8+EC": CORE + ["EC"],
        "core8+P_a274": CORE + ["P_a274"],
        "core8-Ca": [p for p in CORE if p != "Ca"],
        "pH+OC+N+clay+sand": ["pH", "OC", "N", "clay", "sand"],
    }.items():
        m = pd.concat([have[p] for p in props], axis=1).all(axis=1)
        combos[label] = {"samples": int(m.sum()), "groups": int(df.loc[m, "group"].nunique()),
                         "by_dataset": df.loc[m, "dataset.code_ascii_txt"].value_counts().to_dict()}

    summary = {
        "evidence_tag": "DATA AUDIT (descriptive)",
        "files_md5": (RAW.parent / "ossl_manifest_md5.txt").read_text().splitlines(),
        "visnir_rows_joined_with_lab": n_all,
        "after_licence_filter": len(df),
        "excluded_licences": sorted(EXCLUDED_LICENCES),
        "wavelength_columns": len(wl), "wavelength_first_last": [wl[0], wl[-1]],
        "combinations": combos,
    }
    (OUT / "ossl_audit.json").write_text(json.dumps(summary, indent=2))
    per_ds.to_csv(OUT / "ossl_per_dataset.csv")
    cov.to_csv(OUT / "ossl_property_coverage.csv")
    df[KEY + ["group"]].to_csv(OUT / "ossl_eligible_ids.csv.gz", index=False, compression="gzip")

    print(per_ds.to_string(), "\n")
    print(cov.to_string(), "\n")
    print(json.dumps(combos, indent=1))


if __name__ == "__main__":
    sys.exit(main())
