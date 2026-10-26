"""Download the three Open Soil Spectral Library v1.2 files used in this project and verify them.

The files come from the OSSL public bucket (CC-BY data; see README "Data sources"). Their MD5
checksums are fixed in data/ossl_manifest_md5.txt (recorded at the original download,
doc 12) and were checked against the bucket on 2026-10-03. A file that is already present with the
right checksum is not downloaded again. About 200 MB in total.

    python scripts/download_ossl.py
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ossl"
BASE = "https://storage.googleapis.com/soilspec4gg-public/"
MANIFEST = ROOT / "data" / "ossl_manifest_md5.txt"
EXPECTED = {   # fallback if the manifest file is missing (same values as doc 12)
    "ossl_soilsite_L0_v1.2.csv.gz": "e8c640a9e7b6f15c2dec0a7d2e445716",
    "ossl_soillab_L1_v1.2.csv.gz": "e24b94605b0061add400cf3b617f1f18",
    "ossl_visnir_L0_v1.2.csv.gz": "8543cf2265bced21e6a4aab3758207f6",
}


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def expected():
    if not MANIFEST.exists():
        return EXPECTED
    out = {}
    for line in MANIFEST.read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            out[name.lstrip("*")] = digest
    return out


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    bad = []
    for name, digest in expected().items():
        dest = RAW / name
        if dest.exists() and md5(dest) == digest:
            print(f"ok (already present)  {name}")
            continue
        print(f"downloading {name} ...", flush=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        urllib.request.urlretrieve(BASE + name, tmp)
        got = md5(tmp)
        if got != digest:
            bad.append(name)
            print(f"  CHECKSUM MISMATCH: expected {digest}, got {got}; file kept as {tmp.name}")
            continue
        tmp.replace(dest)
        print(f"  ok  {name}")
    if bad:
        sys.exit(f"{len(bad)} file(s) failed verification: {bad}. The online version may have changed.")
    print("All OSSL files present and verified in", RAW)


if __name__ == "__main__":
    main()
