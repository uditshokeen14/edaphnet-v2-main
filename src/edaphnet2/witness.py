"""Witness model p(z | w) and population model p(z).

T0 is Gaussian in latent space, so a linear-Gaussian conditional is the correct model here:
z_lab = a + M w + e, e ~ N(0, S), with S including lab repeatability noise. Fitted on clean
training reports only. T1 replaces this with quantile GBM + Gaussian copula (doc 11 §3.2).
"""
import numpy as np

from .properties import P, to_latent


class GaussianModel:
    """N(mu(w), S) in latent space; mu(w) = a + M w, or constant when no witness is used."""

    def fit(self, Y, W=None):
        Z, _ = to_latent(Y)
        if not np.all(np.isfinite(Z)):
            raise ValueError("training reports must be positive where required")
        X = np.ones((len(Z), 1)) if W is None else np.hstack([np.ones((len(Z), 1)), W])
        self.beta, *_ = np.linalg.lstsq(X, Z, rcond=None)
        E = Z - X @ self.beta
        self.S = np.cov(E, rowvar=False)
        self.uses_witness = W is not None
        Sinv = np.linalg.inv(self.S)
        self.L = np.linalg.cholesky(Sinv)          # Sinv = L L^T
        self.logdet = np.linalg.slogdet(self.S)[1]
        self.sd = np.sqrt(np.diag(self.S))
        return self

    def mean(self, W=None, n=None):
        if not self.uses_witness:
            return np.repeat(self.beta[:1], n if W is None else len(W), axis=0)
        return np.hstack([np.ones((len(W), 1)), W]) @ self.beta

    def logpdf_latent(self, Z, MU):
        """log N(Z; MU, S) with broadcasting over leading dims; nan rows -> -inf."""
        D = (Z - MU) @ self.L
        q = np.sum(D * D, axis=-1)
        out = -0.5 * (q + self.logdet + Z.shape[-1] * np.log(2 * np.pi))
        return np.where(np.isfinite(out), out, -np.inf)


class FixedGaussianModel:
    """Witness model with precomputed latent means per sample and a residual covariance S
    (real data: fitted in scripts/fit_witness_ladder.py). Same interface as GaussianModel."""

    def __init__(self, S):
        self.S = np.asarray(S, float)
        self.L = np.linalg.cholesky(np.linalg.inv(self.S))
        self.logdet = np.linalg.slogdet(self.S)[1]
        self.sd = np.sqrt(np.diag(self.S))

    def logpdf_latent(self, Z, MU):
        D = (Z - MU) @ self.L
        q = np.sum(D * D, axis=-1)
        out = -0.5 * (q + self.logdet + Z.shape[-1] * np.log(2 * np.pi))
        return np.where(np.isfinite(out), out, -np.inf)
