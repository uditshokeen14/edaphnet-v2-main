"""Real-data (T1, OSSL/KSSL) utilities: property definitions, the pre-declared physical
screen (doc 12 §5), latent transforms, and witness construction from Vis-NIR spectra.

Witness ladder (doc 10 §3, doc 11 §5):
  W1  CIELAB colour computed from 380–780 nm reflectance (CIE 1931 2°, D65)
  W2  mean reflectance in 10 equal bins over 400–700 nm
  W3  full 350–2500 nm spectrum, resampled to 10 nm (PCA is fitted later on train only)
"""
import numpy as np

PROPERTIES = {  # short name -> (OSSL column, transform, unit)
    "pH": ("ph.h2o_usda.a268_index", "identity", "pH units"),
    "OC": ("oc_usda.c729_w.pct", "log", "%"),
    "N": ("n.tot_usda.a623_w.pct", "log", "%"),
    "clay": ("clay.tot_usda.a334_w.pct", "logit100", "%"),
    "sand": ("sand.tot_usda.c60_w.pct", "logit100", "%"),
    "CEC": ("cec_usda.a723_cmolc.kg", "log", "cmol(+)/kg"),
    "K": ("k.ext_usda.a725_cmolc.kg", "log", "cmol(+)/kg"),
    "Ca": ("ca.ext_usda.a722_cmolc.kg", "log", "cmol(+)/kg"),
    "Mg": ("mg.ext_usda.a724_cmolc.kg", "log", "cmol(+)/kg"),
    "Ctot": ("c.tot_usda.a622_w.pct", "log", "%"),
    "CaCO3": ("caco3_usda.a54_w.pct", "log", "%"),
}
PROPERTY_SETS = {
    "kssl_core8": ("pH", "OC", "N", "clay", "sand", "CEC", "K", "Ca"),
    "icraf8": ("pH", "OC", "clay", "sand", "CEC", "K", "Ca", "Mg"),   # ICRAF-ISRIC has no N
    "kssl3": ("OC", "N", "Ctot"),   # doc 18 §6: CaCO3 coverage 46.5% < 50%, so it is excluded
}
CORE = {n: PROPERTIES[n] for n in PROPERTY_SETS["kssl_core8"]}   # backward compatibility
NAMES = tuple(CORE)


# ------------------------------------------------------------ pre-declared physical screen

def physical_screen(df, names=NAMES):
    """Boolean mask of rows that pass the doc-12 §5 limits, plus per-rule removal counts.

    Rules were fixed before any modelling and never use a fitted model. Rules whose
    properties are not in `names` are skipped.
    """
    names = list(names)
    pct = [n for n in ("OC", "N", "clay", "sand", "Ctot", "CaCO3") if n in names]
    rules = {"pH outside [2, 11]": ~df["pH"].between(2, 11) if "pH" in names else None,
             "percentage > 100": (df[pct] > 100).any(axis=1) if pct else None,
             "N > 5% with OC < 20%": ((df["N"] > 5) & (df["OC"] < 20)) if {"N", "OC"} <= set(names) else None,
             "sand + clay > 100.5": ((df["sand"] + df["clay"]) > 100.5) if {"sand", "clay"} <= set(names) else None,
             "negative value": (df[names] < 0).any(axis=1)}
    rules = {k: v for k, v in rules.items() if v is not None}
    bad = np.zeros(len(df), bool)
    counts = {}
    for name, m in rules.items():
        m = m.to_numpy()
        counts[name] = int(m.sum())
        bad |= m
    counts["total removed"] = int(bad.sum())
    return ~bad, counts


def fill_zeros(df, names=NAMES):
    """Zeros = below detection: set to half the smallest positive value of that property."""
    df = df.copy()
    info = {}
    for n in names:
        if PROPERTIES[n][1] == "identity":
            continue
        z = df[n] <= 0
        if z.any():
            floor = df.loc[df[n] > 0, n].min() / 2
            df.loc[z, n] = floor
        info[n] = int(z.sum())
    return df, info


# ------------------------------------------------------------ latent transform

class LatentTransform:
    """Per-property monotone transform to an approximately Gaussian, standardised latent z.

    identity (pH), log (positive skewed), logit of x/100 (texture fractions, clipped to
    [0.5, 99.5] %). Mean and SD are fitted on the training split only.
    """
    EPS = 0.5

    def __init__(self, names=NAMES):
        self.names = tuple(names)
        self.kinds = [PROPERTIES[n][1] for n in self.names]

    def _fwd(self, X):
        Z = np.empty_like(X, dtype=float)
        LJ = np.empty_like(X, dtype=float)
        for k, kind in enumerate(self.kinds):
            x = X[:, k].astype(float)
            with np.errstate(divide="ignore", invalid="ignore"):
                if kind == "identity":
                    Z[:, k], LJ[:, k] = x, 0.0
                elif kind == "log":
                    Z[:, k] = np.where(x > 0, np.log(np.where(x > 0, x, 1)), np.nan)
                    LJ[:, k] = np.where(x > 0, -np.log(np.where(x > 0, x, 1)), -np.inf)
                else:
                    p = np.clip(x, self.EPS, 100 - self.EPS) / 100
                    Z[:, k] = np.log(p / (1 - p))
                    LJ[:, k] = -np.log(100 * p * (1 - p))
        return Z, LJ

    def fit(self, X):
        Z, _ = self._fwd(X)
        self.mu, self.sd = np.nanmean(Z, axis=0), np.nanstd(Z, axis=0)
        return self

    def to_latent(self, X):
        """Returns standardised z and log|dz/dx| per cell."""
        Z, LJ = self._fwd(np.atleast_2d(X))
        return (Z - self.mu) / self.sd, LJ - np.log(self.sd)

    def to_natural(self, Z):
        Z = np.atleast_2d(Z) * self.sd + self.mu
        X = np.empty_like(Z)
        for k, kind in enumerate(self.kinds):
            X[:, k] = Z[:, k] if kind == "identity" else (
                np.exp(Z[:, k]) if kind == "log" else 100 / (1 + np.exp(-Z[:, k])))
        return X


# ------------------------------------------------------------ witnesses from spectra

def _cie_tables(wl):
    import colour
    cmfs = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
    d65 = colour.SDS_ILLUMINANTS["D65"]
    xyz_bar = np.column_stack([np.interp(wl, cmfs.wavelengths, cmfs.values[:, i]) for i in range(3)])
    S = np.interp(wl, d65.wavelengths, d65.values)
    return xyz_bar, S


def spectra_to_lab(R, wl):
    """CIELAB (D65, 2°) of reflectance spectra R (n, len(wl)); wl in nm.

    Uses the 380–780 nm part of the spectrum. Returns (n, 3) = L*, a*, b*.
    """
    import colour
    m = (wl >= 380) & (wl <= 780)
    w = wl[m]
    xyz_bar, S = _cie_tables(w)
    k = 1.0 / np.trapezoid(S * xyz_bar[:, 1], w)
    XYZ = k * np.column_stack([np.trapezoid(R[:, m] * (S * xyz_bar[:, i]), w, axis=1) for i in range(3)])
    white = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]
    return colour.XYZ_to_Lab(XYZ, illuminant=white)


def coarse_bands(R, wl, lo=400, hi=700, n=10):
    edges = np.linspace(lo, hi, n + 1)
    return np.column_stack([R[:, (wl >= a) & (wl < b)].mean(axis=1) for a, b in zip(edges[:-1], edges[1:])])


def resample_full(R, wl, step=10):
    keep = (wl % step) == 0
    return R[:, keep], wl[keep]
