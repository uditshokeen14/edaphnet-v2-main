"""Step-6 photo pipeline tests on synthetic photos with known colours."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edaphnet2 import phone  # noqa: E402

TRUE_SOIL_LAB = np.array([42.0, 9.0, 18.0])   # a brown topsoil


def lab_to_lin_srgb(lab):
    colour = phone._colour()
    white = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]
    return colour.XYZ_to_RGB(colour.Lab_to_XYZ(lab, white), "sRGB", apply_cctf_encoding=False)


def synthetic_photo(camera_matrix, exposure=1.0, noise=0.003, seed=0):
    """A 4x6 chart (top) and a soil patch (bottom), seen through a 'camera' that mixes channels
    (camera_matrix), scales exposure and adds noise; output is sRGB-encoded in [0, 1]."""
    rng = np.random.default_rng(seed)
    H, W = 260, 300
    lin = np.full((H, W, 3), 0.18)
    ref = phone.reference_linear_srgb()
    corners = [(10, 10), (290, 10), (290, 130), (10, 130)]
    for k, (x, y) in enumerate(phone.grid_centers(corners)):
        x, y = int(x), int(y)
        lin[y - 8:y + 9, x - 8:x + 9] = ref[k]
    soil = np.zeros((H, W), bool)
    soil[160:250, 60:240] = True
    lin[soil] = lab_to_lin_srgb(TRUE_SOIL_LAB)
    seen = np.clip(exposure * lin @ camera_matrix.T, 0, 1)
    img = phone.to_encoded(seen) + rng.normal(0, noise, seen.shape)
    return np.clip(img, 0, 1), corners, soil


CAMERA = np.array([[0.85, 0.12, 0.03], [0.06, 0.88, 0.06], [0.02, 0.15, 0.83]])


def test_reference_chart_white_patch_is_bright_and_neutral():
    lab = phone.lin_srgb_to_lab(phone.reference_linear_srgb())
    white = lab[18]                    # patch 19 = white 9.5
    assert white[0] > 90 and abs(white[1]) < 2 and abs(white[2]) < 3


def test_colour_correction_recovers_soil_colour():
    img, corners, soil = synthetic_photo(CAMERA, exposure=0.8)
    lin = phone.to_linear(img)
    meas = phone.patch_means(lin, phone.grid_centers(corners))
    raw_lab, _ = phone.soil_lab(lin, soil, {"M": np.eye(3), "kind": "linear"})
    for kind in ("linear", "rootpoly"):
        ccm = phone.fit_ccm(meas, kind=kind)
        lab, _ = phone.soil_lab(lin, soil, ccm)
        assert phone.delta_e00(lab, TRUE_SOIL_LAB) < 2.0, kind
        assert phone.chart_residual_de(meas, ccm) < 2.5, kind
    assert phone.delta_e00(raw_lab, TRUE_SOIL_LAB) > 3.0      # uncorrected camera is off


def test_blur_detected():
    from scipy import ndimage
    img, _, soil = synthetic_photo(CAMERA, noise=0.02)
    blurred = np.stack([ndimage.gaussian_filter(img[..., c], 3) for c in range(3)], axis=-1)
    assert phone.quality(blurred, soil)["blur_laplacian_var"] < phone.quality(img, soil)["blur_laplacian_var"]


def test_texture_features_distinguish_coarse_from_fine():
    rng = np.random.default_rng(1)
    from scipy import ndimage
    fine = rng.random((200, 200))
    coarse = ndimage.zoom(rng.random((25, 25)), 8, order=0)
    roi = np.ones((200, 200), bool)
    f = phone.texture_features(np.repeat(fine[..., None], 3, -1), roi)
    c = phone.texture_features(np.repeat(coarse[..., None], 3, -1), roi)
    assert f["dog_var_s1"] > c["dog_var_s1"]
