"""Soil properties used in the T0 simulation.

Each property has a marginal transform between a latent standard-normal coordinate z and the
reported value x (natural units). The latent vector is jointly Gaussian (Gaussian copula),
so the joint model is exact in T0. Marginal parameters are plausible topsoil values chosen
for the simulation (ASSUMED). They are not fitted to any dataset; T1 replaces them with OSSL.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Prop:
    name: str
    kind: str        # "normal" or "lognormal"
    loc: float       # mean (normal) or median (lognormal)
    scale: float     # sd (normal) or log-sd (lognormal)
    decimals: int    # reporting precision
    unit: str
    lab_cv: float    # analytical repeatability: sd (normal) or CV (lognormal)


PROPS = (
    Prop("pH", "normal", 6.5, 1.0, 1, "pH units", 0.10),
    Prop("OC", "lognormal", 1.0, 0.6, 2, "%", 0.05),
    Prop("N", "lognormal", 0.10, 0.6, 3, "%", 0.05),
    Prop("clay", "lognormal", 25.0, 0.5, 1, "%", 0.05),
    Prop("CEC", "lognormal", 15.0, 0.5, 1, "cmol(+)/kg", 0.05),
    Prop("K", "lognormal", 0.40, 0.6, 2, "cmol(+)/kg", 0.05),
    Prop("Ca", "lognormal", 8.0, 0.7, 1, "cmol(+)/kg", 0.05),
    Prop("P", "lognormal", 15.0, 0.8, 1, "mg/kg", 0.08),
)
NAMES = tuple(p.name for p in PROPS)
P = len(PROPS)
IDX = {n: i for i, n in enumerate(NAMES)}

# Latent correlations (ASSUMED, agronomically motivated): OC-N strong, clay-CEC, CEC-bases,
# pH-Ca. Everything else is 0. Checked positive definite in tests.
_PAIRS = {
    ("OC", "N"): 0.90, ("clay", "CEC"): 0.70, ("OC", "CEC"): 0.40, ("CEC", "Ca"): 0.60,
    ("CEC", "K"): 0.40, ("pH", "Ca"): 0.50, ("clay", "K"): 0.30, ("OC", "P"): 0.20,
    ("N", "CEC"): 0.35, ("clay", "Ca"): 0.35,
}


def latent_corr():
    R = np.eye(P)
    for (a, b), r in _PAIRS.items():
        R[IDX[a], IDX[b]] = R[IDX[b], IDX[a]] = r
    return R


def lab_noise_sd():
    """Repeatability noise expressed in latent z units."""
    return np.array([p.lab_cv / p.scale for p in PROPS])


def to_natural(z):
    """Latent z (..., P) -> natural units."""
    z = np.asarray(z, float)
    x = np.empty_like(z)
    for k, p in enumerate(PROPS):
        if p.kind == "normal":
            x[..., k] = p.loc + p.scale * z[..., k]
        else:
            x[..., k] = p.loc * np.exp(p.scale * z[..., k])
    return x


def to_latent(x):
    """Natural units (..., P) -> latent z and log|dz/dx| per cell.

    Non-positive values of a lognormal property have zero density: z = nan, logjac = -inf.
    """
    x = np.asarray(x, float)
    z = np.empty_like(x)
    lj = np.empty_like(x)
    for k, p in enumerate(PROPS):
        xk = x[..., k]
        if p.kind == "normal":
            z[..., k] = (xk - p.loc) / p.scale
            lj[..., k] = -np.log(p.scale)
        else:
            with np.errstate(divide="ignore", invalid="ignore"):
                pos = xk > 0
                z[..., k] = np.where(pos, np.log(np.where(pos, xk, 1.0) / p.loc) / p.scale, np.nan)
                lj[..., k] = np.where(pos, -np.log(p.scale * np.where(pos, xk, 1.0)), -np.inf)
    return z, lj


def round_report(x):
    """Apply per-property reporting precision."""
    x = np.array(x, float)
    for k, p in enumerate(PROPS):
        x[..., k] = np.round(x[..., k], p.decimals)
    return x
