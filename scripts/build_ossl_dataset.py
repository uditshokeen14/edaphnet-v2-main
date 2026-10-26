"""Step 4b-1: build the frozen T1 dataset from OSSL.

  samples of one OSSL dataset with all lab values of a property set AND a non-empty Vis-NIR spectrum
  -> pre-declared physical screen (doc 12 §5) -> zero handling
  -> witnesses: CIELAB (W1), 10 visible bands (W2), 10-nm full spectrum (W3)
  -> location-grouped split 50 / 15 / 35 (train / cal / test), seed fixed below

    python scripts/build_ossl_dataset.py --dataset ICRAF.ISRIC --props icraf8 --tag icraf8
Outputs: data/processed/t1_<tag>.npz (git-ignored, reproducible), data/splits/t1_<tag>_split.csv.gz
(committed), results/data_audit/t1_build.json (committed).
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from edaphnet2.real_data import PROPERTIES, PROPERTY_SETS, coarse_bands, fill_zeros, physical_screen, resample_full, spectra_to_lab  # noqa: E402

RAW = ROOT / "data" / "raw" / "ossl"
KEY = ["dataset.code_ascii_txt", "id.layer_uuid_txt"]
SPLIT_SEED = 20260924
SPLIT_FRAC = {"train": 0.50, "cal": 0.15, "test": 0.35}
MAX_DEPTH_TOP = 30


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="ICRAF.ISRIC")
    ap.add_argument("--props", default="icraf8", choices=list(PROPERTY_SETS))
    ap.add_argument("--max-depth", type=float, default=None, help="keep layers with upper depth < this (cm); default: all depths")
    ap.add_argument("--tag", default="icraf8")
    ap.add_argument("--split-seed", type=int, default=SPLIT_SEED)
    args = ap.parse_args()
    NAMES = PROPERTY_SETS[args.props]
    CORE = {n: PROPERTIES[n] for n in NAMES}
    ids = pd.read_csv(ROOT / "results" / "data_audit" / "ossl_eligible_ids.csv.gz")
    lab = pd.read_csv(RAW / "ossl_soillab_L1_v1.2.csv.gz", low_memory=False)
    site = pd.read_csv(RAW / "ossl_soilsite_L0_v1.2.csv.gz", low_memory=False,
                       usecols=KEY + ["layer.upper.depth_usda_cm"])
    df = ids.merge(lab[KEY + [c for c, _, _ in CORE.values()]], on=KEY).merge(site, on=KEY, how="left")
    df = df.rename(columns={c: n for n, (c, _, _) in CORE.items()})
    log = {"dataset": args.dataset, "property_set": list(NAMES), "max_depth": args.max_depth,
           "eligible_ids_from_audit": len(ids)}
    df = df[df["dataset.code_ascii_txt"] == args.dataset]
    log["in_dataset"] = len(df)
    df = df[df[list(NAMES)].notna().all(axis=1)]
    log["all_properties_complete"] = len(df)
    if args.max_depth is not None:
        df = df[df["layer.upper.depth_usda_cm"] < args.max_depth]
    log["after_depth_filter"] = len(df)

    # spectra: stream the big file, keep only wanted rows with a real spectrum
    want = set(df["id.layer_uuid_txt"])
    kept = []
    wl = None
    for ch in pd.read_csv(RAW / "ossl_visnir_L0_v1.2.csv.gz", chunksize=5000, low_memory=False):
        ch = ch[ch["id.layer_uuid_txt"].isin(want)]
        if ch.empty:
            continue
        cols = [c for c in ch.columns if c.startswith("scan_visnir.")]
        if wl is None:
            wl = np.array([float(c.split(".")[1].split("_")[0]) for c in cols])
        vis = (wl >= 380) & (wl <= 780)
        R = ch[cols].to_numpy(dtype=np.float32)
        ok = np.isfinite(R[:, vis]).all(axis=1) & (np.isfinite(R).mean(axis=1) > 0.95)
        kept.append((ch.loc[ok, KEY].reset_index(drop=True), R[ok]))
    spec_ids = pd.concat([k for k, _ in kept], ignore_index=True)
    R = np.vstack([r for _, r in kept])
    spec_ids["_row"] = np.arange(len(spec_ids))
    spec_ids = spec_ids.drop_duplicates(KEY)
    df = df.merge(spec_ids, on=KEY, how="inner")
    log["with_nonempty_spectrum"] = len(df)

    ok, screen = physical_screen(df, NAMES)
    df = df[ok].reset_index(drop=True)
    log["physical_screen"] = screen
    log["after_screen"] = len(df)
    df, zeros = fill_zeros(df, NAMES)
    log["zeros_set_to_half_min_positive"] = zeros

    R = R[df["_row"].to_numpy()].astype(float)
    # fill the few missing NIR points by linear interpolation along wavelength
    for i in np.where(~np.isfinite(R).all(axis=1))[0]:
        f = np.isfinite(R[i])
        R[i] = np.interp(wl, wl[f], R[i, f])

    lab_w = spectra_to_lab(R, wl)
    bands = coarse_bands(R, wl)
    full, wl10 = resample_full(R, wl)

    # location-grouped split
    groups = df["group"].to_numpy()
    ug = np.unique(groups)
    rng = np.random.default_rng(args.split_seed)
    perm = rng.permutation(len(ug))
    cut1 = int(SPLIT_FRAC["train"] * len(ug))
    cut2 = cut1 + int(SPLIT_FRAC["cal"] * len(ug))
    assign = {}
    for j, gi in enumerate(perm):
        assign[ug[gi]] = "train" if j < cut1 else ("cal" if j < cut2 else "test")
    split = np.array([assign[g] for g in groups])
    for a in ("train", "cal", "test"):
        for b in ("train", "cal", "test"):
            if a < b:
                assert not set(groups[split == a]) & set(groups[split == b]), "group leak"

    out = ROOT / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / f"t1_{args.tag}.npz", X=df[list(NAMES)].to_numpy(float), names=np.array(NAMES),
                        lab=lab_w, bands=bands, full=full, wl10=wl10, split=split, groups=groups,
                        uuid=df["id.layer_uuid_txt"].to_numpy(), depth=df["layer.upper.depth_usda_cm"].to_numpy())
    (ROOT / "data" / "splits").mkdir(exist_ok=True)
    sp = pd.DataFrame({"id.layer_uuid_txt": df["id.layer_uuid_txt"], "group": groups, "split": split})
    split_path = ROOT / "data" / "splits" / f"t1_{args.tag}_split.csv.gz"
    sp.to_csv(split_path, index=False, compression="gzip")

    log.update({
        "split_seed": args.split_seed, "split_fractions_of_groups": SPLIT_FRAC,
        "split_samples": pd.Series(split).value_counts().to_dict(),
        "split_groups": {s: int(len(set(groups[split == s]))) for s in SPLIT_FRAC},
        "split_file_md5": hashlib.md5(split_path.read_bytes()).hexdigest(),
        "witness_dims": {"W1_lab": 3, "W2_bands": int(bands.shape[1]), "W3_full_10nm": int(full.shape[1])},
        "lab_summary": {c: [float(np.percentile(lab_w[:, i], q)) for q in (1, 50, 99)]
                        for i, c in enumerate(["L*", "a*", "b*"])},
        "property_summary": {n: [float(np.percentile(df[n], q)) for q in (1, 50, 99)] for n in NAMES},
    })
    (ROOT / "results" / "data_audit" / f"t1_{args.tag}_build.json").write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    sys.exit(main())
