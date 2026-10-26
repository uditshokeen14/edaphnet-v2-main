"""Baselines B0–B7 (doc 11 §6). Every baseline returns one error score per report
(higher = more suspicious). All scores go through the same conformal + BH procedure.
All functions take a property `space` (T0 synthetic by default).
"""
import numpy as np
from scipy.optimize import linear_sum_assignment

from .operators import DECIMAL_OPS
from .space import T0


# B0 ------------------------------------------------------------------ fixed range checks
class RangeCheck:
    """Per-property plausible range = [0.1%, 99.9%] quantiles of clean training reports."""

    def __init__(self, space=T0):
        self.space = space

    def fit(self, Y):
        self.lo = np.quantile(Y, 0.001, axis=0)
        self.hi = np.quantile(Y, 0.999, axis=0)
        return self

    def score(self, R):
        span = self.hi - self.lo
        below = np.maximum(0, self.lo - R) / span
        above = np.maximum(0, R - self.hi) / span
        return np.max(below + above, axis=1)

    def attribute(self, r):
        """B6: first decimal/unit conversion whose inverse brings every cell into range."""
        names, idx = self.space.names, self.space.idx
        bad = np.where((r < self.lo) | (r > self.hi))[0]
        if len(bad) == 0:
            return None
        ops = [(k, f"{n}@{names[k]}", f) for k in bad for n, f in DECIMAL_OPS]
        ops += [(idx[p], f"{n}@{p}", f) for p, n, f in self.space.unit_ops if idx[p] in bad]
        for k, name, f in ops:
            y = r.copy(); y[k] = r[k] / f
            if np.all((y >= self.lo) & (y <= self.hi)):
                return name
        return None


# B1 ------------------------------------------------------------ internal-consistency rules
def rule_score(R, space=T0):
    """Rules that apply to the properties present:
    C:N ratio outside [7, 20]; sum of exchangeable bases (K, Ca, Mg) above CEC;
    sand + clay above 100 %."""
    idx = space.idx
    s = np.zeros(len(R))
    if {"OC", "N"} <= set(idx):
        cn = R[:, idx["OC"]] / R[:, idx["N"]]
        s += np.maximum(0, 7 - cn) / 7 + np.maximum(0, cn - 20) / 20
    bases = [b for b in ("K", "Ca", "Mg") if b in idx]
    if "CEC" in idx and bases:
        tot = R[:, [idx[b] for b in bases]].sum(axis=1)
        s += np.maximum(0, tot - R[:, idx["CEC"]]) / np.maximum(R[:, idx["CEC"]], 1e-9)
    if {"sand", "clay"} <= set(idx):
        s += np.maximum(0, R[:, idx["sand"]] + R[:, idx["clay"]] - 100) / 100
    if {"OC", "Ctot"} <= set(idx):   # organic C cannot exceed total C (added for KSSL; favours B1)
        s += np.maximum(0, R[:, idx["OC"]] - 1.05 * R[:, idx["Ctot"]]) / np.maximum(R[:, idx["Ctot"]], 1e-9)
    return s


# B2 ------------------------------------------------ lab-only multivariate plausibility
def population_score(R, pop_model, space=T0, pop_mean=None):
    Z, LJ = space.to_latent(R)
    MU = pop_model.mean(n=len(R)) if pop_mean is None else np.broadcast_to(pop_mean, Z.shape)
    return -(pop_model.logpdf_latent(Z, MU) + LJ.sum(axis=1))


# B3 ------------------------------------------------ per-value witness interval check
def marginal_witness_score(R, MU, model, space=T0):
    Z, _ = space.to_latent(R)
    return np.max(np.abs(Z - MU) / model.sd, axis=1)


# B4 ------------------------------------------------ swap-only cross-modal matching
def hungarian_score(ell_none):
    """ell_none[j, i] = log p(r_j | no corruption, w_i).

    Optimal assignment of reports to samples; score = log-likelihood gain of the assigned
    sample over the recorded one (0 when the assignment keeps the report in place).
    """
    rows, cols = linear_sum_assignment(-ell_none)
    gain = ell_none[rows, cols] - np.diag(ell_none)[rows]
    s = np.zeros(len(ell_none))
    s[rows] = gain
    return s


# B7 ------------------------------------------------ regression-based numeric error score
class RegressionVeracity:
    """Simplified linear re-implementation in the spirit of Zhou, Mueller et al. 2023 (T0 only)."""

    def __init__(self, space=T0):
        self.space = space

    def fit(self, Y, W=None):
        Z, _ = self.space.to_latent(Y)
        self.use_w = W is not None
        self.coef, self.sd = [], []
        for k in range(self.space.P):
            X = self._design(Z, W, k)
            b, *_ = np.linalg.lstsq(X, Z[:, k], rcond=None)
            self.coef.append(b)
            self.sd.append(np.std(Z[:, k] - X @ b))
        return self

    def _design(self, Z, W, k):
        cols = [np.ones((len(Z), 1)), np.delete(Z, k, axis=1)]
        if self.use_w:
            cols.append(W)
        return np.hstack(cols)

    def predict(self, R, W=None):
        Z, _ = self.space.to_latent(R)
        return Z, np.column_stack([self._design(Z, W, k) @ self.coef[k] for k in range(self.space.P)])

    def score(self, R, W=None):
        Z, pred = self.predict(R, W)
        return np.max(np.abs(Z - pred) / np.array(self.sd), axis=1)


class CleanlabOutre:
    """B7 (reference implementation): cleanlab's regression label-quality score
    (method="outre"; Zhou, Mueller et al. 2023, arXiv 2305.16583).

    Per property k, the "label" is the reported latent value and the prediction comes from a
    LightGBM model of property k given the other reported properties and the witness features,
    trained on clean training reports. cleanlab scores are dataset-level (they use neighbours
    among the scored reports), so they are computed over one whole evaluation pool at a time.
    Report error score = 1 - min_k quality_k.
    """

    def __init__(self, space, seed=0):
        self.space, self.seed = space, seed

    def _X(self, Z, W, k):
        cols = [np.delete(Z, k, axis=1)]
        if W is not None:
            cols.append(W)
        return np.hstack(cols)

    def fit(self, Y, W=None):
        import lightgbm as lgb
        Z, _ = self.space.to_latent(Y)
        self.models = [lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=15,
                                         random_state=self.seed, verbose=-1).fit(self._X(Z, W, k), Z[:, k])
                       for k in range(self.space.P)]
        return self

    def score_pool(self, R, W=None):
        from cleanlab.regression.rank import get_label_quality_scores
        Z, _ = self.space.to_latent(R)
        Zc = np.nan_to_num(Z, nan=50.0, posinf=50.0, neginf=-50.0)
        q = np.column_stack([
            get_label_quality_scores(Zc[:, k], self.models[k].predict(self._X(Zc, W, k)), method="outre")
            for k in range(self.space.P)])
        return 1 - q.min(axis=1)
