import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edaphnet2.real_data import (NAMES, LatentTransform, coarse_bands, physical_screen,  # noqa: E402
                                 spectra_to_lab)

WL = np.arange(350, 2501, 2).astype(float)


def test_flat_reflectance_is_neutral_grey():
    lab = spectra_to_lab(np.full((1, len(WL)), 0.5), WL)[0]
    assert abs(lab[1]) < 0.5 and abs(lab[2]) < 0.5
    assert 75 < lab[0] < 77          # L* of 50% reflectance ~ 76.07


def test_red_soil_is_redder_than_grey():
    red = np.where(WL > 600, 0.45, 0.15)[None, :]
    assert spectra_to_lab(red, WL)[0, 1] > 20


def test_darker_is_lower_lightness():
    assert spectra_to_lab(np.full((1, len(WL)), 0.1), WL)[0, 0] < spectra_to_lab(np.full((1, len(WL)), 0.4), WL)[0, 0]


def test_coarse_bands_shape():
    assert coarse_bands(np.random.rand(4, len(WL)), WL).shape == (4, 10)


def test_latent_roundtrip():
    rng = np.random.default_rng(0)
    X = np.column_stack([rng.uniform(4, 9, 100), rng.lognormal(0, 1, 100), rng.lognormal(-2, 1, 100),
                         rng.uniform(5, 60, 100), rng.uniform(5, 80, 100), rng.lognormal(2.5, .5, 100),
                         rng.lognormal(-1, .6, 100), rng.lognormal(2, .7, 100)])
    t = LatentTransform().fit(X)
    Z, LJ = t.to_latent(X)
    assert np.allclose(t.to_natural(Z), X) and np.all(np.isfinite(LJ))


def test_physical_screen_flags_impossible_nitrogen():
    df = pd.DataFrame([[6.5, 1.0, 0.1, 20, 40, 10, .3, 5], [6.5, 1.0, 41.9, 20, 40, 10, .3, 5]], columns=NAMES)
    ok, counts = physical_screen(df)
    assert ok.tolist() == [True, False] and counts["N > 5% with OC < 20%"] == 1
