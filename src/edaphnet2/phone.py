"""Step 6 "eyes": from a phone photo with an X-Rite/Calibrite ColorChecker 24 in the frame to a
calibrated soil colour (CIELAB, D65/2°), texture descriptors and photo-quality checks.

Pipeline (doc 15 §5, §10):
  1. the user (or a detector, later) gives the 4 outer corners of the 24-patch chart
  2. mean linear-RGB of each patch                         -> patch_means()
  3. colour-correction matrix fitted to the chart reference -> fit_ccm() (linear or root-polynomial)
  4. soil region -> corrected linear RGB -> XYZ -> CIELAB    -> soil_lab()
  5. quality: blur, clipping, and the chart fit residual ΔE00 -> quality(); the residual is the
     per-photo colour uncertainty that the witness model can use

Works on float arrays (H, W, 3) in [0, 1] (sRGB-encoded). load_image() needs Pillow, which is
optional (not installed in every environment; add `pillow` to requirements when step 6 starts).
"""
import numpy as np

_CHART = "ColorChecker24 - After November 2014"


def _colour():
    import warnings
    warnings.filterwarnings("ignore", module="colour")
    import colour
    return colour


def reference_linear_srgb():
    """Reference linear sRGB (D65) of the 24 chart patches, row-major from dark skin (1) to black (24)."""
    colour = _colour()
    cc = colour.CCS_COLOURCHECKERS[_CHART]
    xyY = np.array(list(cc.data.values()))
    XYZ = colour.xyY_to_XYZ(xyY)
    d65 = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]
    XYZ65 = colour.chromatic_adaptation(XYZ, colour.xy_to_XYZ(cc.illuminant), colour.xy_to_XYZ(d65))
    return colour.XYZ_to_RGB(XYZ65, "sRGB", apply_cctf_encoding=False)


def to_linear(img):
    return _colour().cctf_decoding(np.clip(img, 0, 1), function="sRGB")


def to_encoded(lin):
    return _colour().cctf_encoding(np.clip(lin, 0, 1), function="sRGB")


def grid_centers(corners, rows=4, cols=6):
    """Patch centres from the chart's 4 outer corners [(x, y) top-left, top-right, bottom-right,
    bottom-left], by bilinear interpolation. Returns (rows*cols, 2) as (x, y)."""
    tl, tr, br, bl = [np.asarray(c, float) for c in corners]
    out = []
    for r in range(rows):
        v = (r + 0.5) / rows
        left, right = tl + v * (bl - tl), tr + v * (br - tr)
        for c in range(cols):
            u = (c + 0.5) / cols
            out.append(left + u * (right - left))
    return np.array(out)


def patch_means(img_lin, centers, half=6):
    """Robust (median) linear RGB in a (2*half+1)^2 window around each centre."""
    H, W, _ = img_lin.shape
    vals = []
    for x, y in np.round(centers).astype(int):
        win = img_lin[max(0, y - half):min(H, y + half + 1), max(0, x - half):min(W, x + half + 1)]
        vals.append(np.median(win.reshape(-1, 3), axis=0))
    return np.array(vals)


def _features(rgb, kind):
    rgb = np.clip(rgb, 0, None)
    if kind == "linear":
        return rgb
    if kind == "rootpoly":   # root-polynomial degree 2 (Finlayson et al. 2015): exposure-invariant
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        return np.stack([r, g, b, np.sqrt(r * g), np.sqrt(g * b), np.sqrt(r * b)], axis=-1)
    raise ValueError(kind)


def fit_ccm(measured_lin, reference_lin=None, kind="rootpoly"):
    """Least-squares colour-correction matrix from measured to reference linear RGB."""
    ref = reference_linear_srgb() if reference_lin is None else reference_lin
    M, *_ = np.linalg.lstsq(_features(measured_lin, kind), ref, rcond=None)
    return {"M": M, "kind": kind}


def apply_ccm(rgb_lin, ccm):
    return np.clip(_features(rgb_lin, ccm["kind"]) @ ccm["M"], 0, None)


def lin_srgb_to_lab(rgb_lin):
    colour = _colour()
    XYZ = colour.RGB_to_XYZ(rgb_lin, "sRGB", apply_cctf_decoding=False)
    white = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]
    return colour.XYZ_to_Lab(XYZ, white)


def delta_e00(lab1, lab2):
    return _colour().delta_E(lab1, lab2, method="CIE 2000")


def chart_residual_de(measured_lin, ccm, reference_lin=None):
    """Mean ΔE00 between corrected chart patches and their reference: per-photo colour error."""
    ref = reference_linear_srgb() if reference_lin is None else reference_lin
    return float(np.mean(delta_e00(lin_srgb_to_lab(apply_ccm(measured_lin, ccm)), lin_srgb_to_lab(ref))))


def soil_lab(img_lin, roi_mask, ccm):
    """Median corrected CIELAB of the soil region and its within-region spread (SD of L*, a*, b*)."""
    px = img_lin[roi_mask]
    lab = lin_srgb_to_lab(apply_ccm(px, ccm))
    return np.median(lab, axis=0), lab.std(axis=0)


def quality(img, roi_mask=None):
    """Blur (variance of the Laplacian of grey), fractions of clipped pixels."""
    from scipy import ndimage
    grey = img[..., :3].mean(axis=-1)
    region = grey if roi_mask is None else np.where(roi_mask, grey, np.nan)
    lap = ndimage.laplace(grey)
    lapv = lap if roi_mask is None else lap[roi_mask]
    return {"blur_laplacian_var": float(np.nanvar(lapv)),
            "clipped_high": float(np.nanmean(region >= 0.99)),
            "clipped_low": float(np.nanmean(region <= 0.01))}


def texture_features(img, roi_mask, scales=(1, 2, 4, 8)):
    """Scale-space texture of the soil region (granularity proxy without extra packages):
    variance of band-pass (difference-of-Gaussians) grey at several scales, relative to total
    variance, plus gradient energy. Units are pixels, so photos must be taken at a fixed
    distance or rescaled using the ruler (doc 15 §5)."""
    from scipy import ndimage
    grey = img[..., :3].mean(axis=-1)
    tot = float(np.var(grey[roi_mask])) + 1e-12
    feats = {}
    prev = grey
    for s in scales:
        g = ndimage.gaussian_filter(grey, s)
        feats[f"dog_var_s{s}"] = float(np.var((prev - g)[roi_mask]) / tot)
        prev = g
    gy, gx = np.gradient(grey)
    feats["grad_energy"] = float(np.mean((gx ** 2 + gy ** 2)[roi_mask]))
    return feats


def load_image(path):
    try:
        from PIL import Image
    except ImportError as e:
        raise ImportError("Reading photos needs Pillow: pip install pillow") from e
    return np.asarray(Image.open(path).convert("RGB"), dtype=float) / 255.0
