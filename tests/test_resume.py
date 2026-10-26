"""A resumed step-5 run must give exactly the same numbers as an uninterrupted run."""
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "results" / "runs"
CMD = [sys.executable, "scripts/run_real.py", "--config", "configs/real_icraf8.yaml", "--smoke"]


@pytest.mark.slow
@pytest.mark.skipif(not (ROOT / "data" / "processed" / "witness_icraf8.npz").exists(), reason="needs processed data")
def test_resume_reproduces_uninterrupted_run():
    before = set(RUNS.glob("*smoke*"))
    subprocess.run(CMD, cwd=ROOT, check=True, capture_output=True)
    full_run = (set(RUNS.glob("*smoke*")) - before).pop()
    ref = pd.read_csv(full_run / "metrics_by_setting.csv")

    # simulate an interruption after the first setting
    part = full_run.with_name(full_run.name + "_interrupted")
    shutil.copytree(full_run, part)
    for f in ("metrics_by_setting.csv", "attribution_by_setting.csv", "predictions.csv.gz"):
        kw = {"compression": "gzip"} if f.endswith(".gz") else {}
        df = pd.read_csv(part / f, **kw)
        df[df["lambda"] == "W0"].to_csv(part / f, index=False, **kw)
    subprocess.run(CMD + ["--resume", str(part)], cwd=ROOT, check=True, capture_output=True)
    got = pd.read_csv(part / "metrics_by_setting.csv")
    try:
        pd.testing.assert_frame_equal(ref.reset_index(drop=True), got.reset_index(drop=True))
    finally:
        shutil.rmtree(full_run); shutil.rmtree(part)
