"""Proposed method ("Full"): joint inference over structured swaps and typed value errors
for one lab batch (doc 11 §2.5).

For report j and candidate sample i:
    l(j, i) = log sum_c P(c) p(T_c^-1(r_j) | w_i) |J_c|
Swap hypotheses pi in S change which sample each report is scored against:
    log P(pi | batch) = log P(pi) + sum_{moved j} [ l(j, pi(j)) - l(j, j) ] + const.
The report error score is 1 - P(report clean), where
    P(clean_j) = (1 - P(j moved)) * P(c_j = none | r_j, w_j).
Inference is exact over the enumerated hypothesis set.
"""
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from . import operators, swaps
from .space import T0


@dataclass
class InferenceConfig:
    rho: float = 0.2                  # assumed per-batch swap probability (prior)
    eps: float = 0.05                 # assumed per-report value-error probability (prior)
    groups: tuple = operators.GROUPS  # corruption library; () = no value-error hypotheses
    use_swaps: bool = True
    uniform_swap_prior: bool = False
    class_mass: dict = field(default_factory=lambda: {"S1": 0.5, "S2": 0.3, "S3": 0.2})
    space: object = T0


@lru_cache(maxsize=16)
def _swap_index(n):
    hyps = swaps.enumerate_swaps(n)
    h_idx, js, is_ = [], [], []
    for h, (_, moved) in enumerate(hyps):
        for j, i in moved:
            h_idx.append(h); js.append(j); is_.append(i)
    return hyps, np.array(h_idx), np.array(js), np.array(is_)


def report_hypotheses(R, cfg):
    """Enumerate value-error hypotheses once per report (reusable across witness models)."""
    out = []
    for r in R:
        hs = operators.enumerate_hypotheses(r, cfg.eps if cfg.groups else 0.0, cfg.groups, cfg.space)
        Z, LJ = cfg.space.to_latent(hs.y)
        out.append((hs, Z, LJ.sum(axis=1) + hs.log_jac))
    return out


def _lse(a, axis):
    m = np.max(a, axis=axis, keepdims=True)
    m = np.where(np.isfinite(m), m, 0.0)
    return np.squeeze(m, axis) + np.log(np.sum(np.exp(a - m), axis=axis))


def loglik_matrix(hyp_list, MU, model):
    """l[j, i] and per-(j, j) hypothesis log terms for attribution.

    Hypothesis sets are padded to a common length (padding has log prior -inf) so the
    whole batch is evaluated in one vectorised call.
    """
    n, Hmax, P_ = len(hyp_list), max(len(h[0].log_prior) for h in hyp_list), MU.shape[1]
    Z = np.zeros((n, Hmax, P_))
    base = np.full((n, Hmax), -np.inf)
    for j, (hs, Zj, lj) in enumerate(hyp_list):
        H = len(hs.log_prior)
        Z[j, :H] = np.nan_to_num(Zj, nan=0.0)
        base[j, :H] = np.where(np.isfinite(Zj).all(axis=1), hs.log_prior + lj, -np.inf)
    t = base[:, :, None] + model.logpdf_latent(Z[:, :, None, :], MU[None, None, :, :])  # (n, H, n)
    ell = _lse(t, axis=1)
    self_terms = [t[j, :len(hyp_list[j][0].log_prior), j] for j in range(n)]
    return ell, self_terms


def infer_batch(R, MU, model, cfg, hyp_list=None, precomputed=None):
    """Score one batch. R: (n, P) reports; MU: (n, P) witness means of samples 1..n.

    precomputed: (hyp_list, ell, self_terms) from an earlier call with the same library and
    witness model; lets ablations that only change the swap prior reuse the likelihoods.
    """
    n = len(R)
    if precomputed is not None:
        hyp_list, ell, self_terms = precomputed
    else:
        hyp_list = hyp_list if hyp_list is not None else report_hypotheses(R, cfg)
        ell, self_terms = loglik_matrix(hyp_list, MU, model)
    diag = np.diag(ell)

    p_moved = np.zeros(n)
    partner = np.full(n, -1)
    if cfg.use_swaps and n > 1:
        hyps, h_idx, js, is_ = _swap_index(n)
        lp0, lph = swaps.log_prior(hyps, cfg.rho, cfg.class_mass, cfg.uniform_swap_prior)
        with np.errstate(invalid="ignore"):
            delta = np.bincount(h_idx, weights=ell[js, is_] - diag[js], minlength=len(hyps))
        delta = np.nan_to_num(delta, nan=-np.inf)
        logits = np.concatenate([[lp0], lph + delta])
        post = np.exp(logits - _lse(logits, 0))
        ph = post[1:]
        p_moved = np.bincount(js, weights=ph[h_idx], minlength=n)
        # MAP partner per report among hypotheses that move it
        order = np.argsort(ph[h_idx])          # ascending: later writes win
        partner[js[order]] = is_[order]

    q_none = np.empty(n)
    value_op = []
    for j, t in enumerate(self_terms):
        post_c = np.exp(t - _lse(t, 0))
        q_none[j] = post_c[0]
        k = 1 + int(np.argmax(post_c[1:])) if len(t) > 1 else 0
        hs = hyp_list[j][0]
        value_op.append((hs.group[k], hs.op[k], hs.y[k], float(post_c[k])))

    p_value_err = (1 - p_moved) * (1 - q_none)
    score = 1 - (1 - p_moved) * q_none
    kind = np.where(p_moved >= p_value_err, "swap", "value")
    return {
        "score": score, "p_moved": p_moved, "p_value_err": p_value_err,
        "kind": kind, "partner": partner, "value_op": value_op,
        "precomputed": (hyp_list, ell, self_terms),
    }


def loglik_none(R, MU, model, space=T0):
    """log p(r_j | no corruption, w_i) for all (j, i): input to the swap-only baseline B4."""
    Z, LJ = space.to_latent(R)
    return model.logpdf_latent(Z[:, None, :], MU[None, :, :]) + LJ.sum(axis=1)[:, None]
