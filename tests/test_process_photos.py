"""End-to-end check of scripts/process_photos.py on synthetic photos (no real images needed)."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_phone import CAMERA, TRUE_SOIL_LAB, synthetic_photo  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
from edaphnet2 import phone  # noqa: E402


def test_process_photos_cli(tmp_path):
    photos = tmp_path / "photos"
    photos.mkdir()
    for shot in (1, 2):
        img, corners, soil = synthetic_photo(CAMERA, exposure=0.8, seed=shot)
        np.save(photos / f"EDN-F01-S01_P1_IN_DRY_{shot}.npy", img)
    # one badly blurred, over-exposed photo that should be rejected
    np.save(photos / "EDN-F01-S01_P1_IN_DRY_3.npy", np.ones_like(img))
    geom = {"default": {"chart_corners": [list(c) for c in corners], "soil_box": [60, 160, 240, 250]}}
    (photos / "geometry.json").write_text(json.dumps(geom))
    out = tmp_path / "photos.csv"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "process_photos.py"), "--photos", str(photos),
                    "--geometry", str(photos / "geometry.json"), "--out", str(out)], check=True, capture_output=True)
    df = pd.read_csv(out)
    assert len(df) == 3 and df["usable"].sum() == 2
    ok = df[df["usable"]]
    for _, r in ok.iterrows():
        assert phone.delta_e00(np.array([r.L, r.a, r.b]), TRUE_SOIL_LAB) < 2.0
    assert set(ok["moisture"]) == {"DRY"} and set(ok["phone_id"]) == {"P1"}
