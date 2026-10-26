"""T0 generator (doc 11 §5): synthetic samples, weak witness, lab batches, error injection.

Witness: w = lam * B z + eta, eta ~ N(0, I_d). B mimics a colour sensor (d = 3): the first
axis tracks darkness (organic carbon, carbonate/Ca), the second redness (clay), the third
is weak. lam sets witness strength; lam = 0 means an uninformative witness.
"""
from dataclasses import dataclass

import numpy as np

from . import operators, swaps
from .properties import IDX, P, PROPS, lab_noise_sd, latent_corr, round_report, to_natural


def witness_loadings():
    B = np.zeros((3, P))
    B[0, IDX["OC"]] = -0.8
    B[0, IDX["Ca"]] = 0.3
    B[0, IDX["clay"]] = -0.1
    B[1, IDX["clay"]] = 0.5
    B[1, IDX["K"]] = 0.1
    B[2, IDX["clay"]] = 0.2
    B[2, IDX["pH"]] = 0.2
    return B


def oracle_r2(lam, R=None, B=None):
    """Population R^2 of each latent property from the witness (best linear predictor)."""
    R = latent_corr() if R is None else R
    B = witness_loadings() if B is None else B
    if lam == 0:
        return np.zeros(P)
    C = lam * B @ R                        # cov(w, z): (d, P)
    Sw = lam ** 2 * B @ R @ B.T + np.eye(B.shape[0])
    return np.einsum("dk,de,ek->k", C, np.linalg.inv(Sw), C)


@dataclass
class Batch:
    w: np.ndarray         # (n, d) witness of sample i (position i)
    y: np.ndarray         # (n, P) correct printed report for sample i
    r: np.ndarray         # (n, P) reports as delivered (report j recorded as sample j)
    pi: np.ndarray        # (n,) true permutation: report j measured sample pi[j]
    swap_class: str       # "none" or S1/S2/S3
    is_error: np.ndarray  # (n,) bool
    kind: list            # (n,) "clean" | "swap" | "value"
    value_info: list      # (n,) dict for value errors (group, op, cells) else None


class Generator:
    def __init__(self, lam, rng, ordering="random", farm_size=6, homogeneity=0.6):
        self.lam, self.rng = lam, rng
        self.ordering, self.farm_size, self.h = ordering, farm_size, homogeneity
        self.R = latent_corr()
        self.Lr = np.linalg.cholesky(self.R)
        self.B = witness_loadings()
        self.noise = lab_noise_sd()

    def _latent(self, m):
        return self.rng.standard_normal((m, P)) @ self.Lr.T

    def samples(self, m):
        """m independent samples: (z, w, printed clean report y)."""
        z = self._latent(m)
        return z, self._witness(z), self._report(z)

    def _witness(self, z):
        return self.lam * z @ self.B.T + self.rng.standard_normal((len(z), self.B.shape[0]))

    def _report(self, z):
        y = to_natural(z + self.rng.standard_normal(z.shape) * self.noise)
        return _print(y)

    def batch_latent(self, n):
        if self.ordering == "random":
            return self._latent(n)
        # clustered: consecutive farms share a latent component (marginals stay N(0, R))
        n_farms = -(-n // self.farm_size)
        u = np.repeat(self._latent(n_farms), self.farm_size, axis=0)[:n]
        return np.sqrt(self.h) * u + np.sqrt(1 - self.h) * self._latent(n)

    def batch(self, n, swap_batch_prob=0.0, value_error_rate=0.0):
        z = self.batch_latent(n)
        w, y = self._witness(z), self._report(z)
        pi, swap_class = np.arange(n), "none"
        if self.rng.random() < swap_batch_prob:
            swap_class, pi = swaps.random_swap(n, self.rng)
        r = y[pi].copy()
        kind = ["swap" if pi[j] != j else "clean" for j in range(n)]
        info = [None] * n
        for j in range(n):
            if kind[j] == "clean" and self.rng.random() < value_error_rate:
                rc, inf = operators.apply_random_corruption(y[j], self.rng)
                r[j] = _print(rc[None, :])[0]
                if np.allclose(r[j], y[j]):
                    continue  # corruption invisible after printing: not an error
                kind[j], info[j] = "value", inf
        is_error = np.array([k != "clean" for k in kind])
        return Batch(w, y, r, pi, swap_class, is_error, kind, info)


def _print(x):
    """Round to reporting precision; a positive property never prints as 0."""
    x = round_report(x)
    for k, p in enumerate(PROPS):
        if p.kind == "lognormal":
            x[..., k] = np.maximum(x[..., k], 10.0 ** -p.decimals)
    return x
