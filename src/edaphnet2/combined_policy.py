"""Combined re-test policy (doc 20: Amendment v3).

Combines the joint model's swap posterior with a dedicated value-error score:
  - Variant P1: Reciprocal Rank Fusion of P(report moved) and a value-error score.
  - Variant P2: 50/50 split of the re-test budget between top swap and top value suspects.
  - Student-t B2: Heavy-tailed multivariate/marginal plausibility baseline.
"""
from math import lgamma, log, pi
import numpy as np

from .space import T0


def reciprocal_rank_fusion(scores_swap, scores_value, k=60):
    """P1: Reciprocal-rank fusion of swap posteriors and value-error scores.

    Score = 1/(k + rank_swap) + 1/(k + rank_value), where rank 1 is highest score.
    """
    s_a = np.nan_to_num(np.asarray(scores_swap, float), nan=-1e9, neginf=-1e9)
    s_b = np.nan_to_num(np.asarray(scores_value, float), nan=-1e9, neginf=-1e9)
    n = len(s_a)
    if n == 0:
        return np.zeros(0, float)

    rank_a = np.empty(n, int)
    order_a = np.argsort(-s_a)
    rank_a[order_a] = np.arange(1, n + 1)

    rank_b = np.empty(n, int)
    order_b = np.argsort(-s_b)
    rank_b[order_b] = np.arange(1, n + 1)

    return 1.0 / (k + rank_a) + 1.0 / (k + rank_b)


def budget_split_flagged(scores_swap, scores_value, pool_ids, budget=0.05, seed=0):
    """P2: Half of the re-test budget goes to the top swap posteriors, half to

    top value-error scores (duplicates passed to the next in line).

    Returns a boolean mask of flagged reports across the evaluated pools.
    """
    rng = np.random.default_rng(seed)
    s_sw = np.nan_to_num(np.asarray(scores_swap, float), nan=-1e9, neginf=-1e9)
    s_val = np.nan_to_num(np.asarray(scores_value, float), nan=-1e9, neginf=-1e9)
    flagged = np.zeros(len(s_sw), bool)

    for pool in np.unique(pool_ids):
        idx = np.where(pool_ids == pool)[0]
        n_p = len(idx)
        k_tot = int(np.ceil(budget * n_p))
        k_sw = k_tot // 2
        k_v = k_tot - k_sw

        # Order swap candidates
        order_sw = np.lexsort((rng.random(n_p), -s_sw[idx]))
        top_sw = idx[order_sw[:k_sw]]
        flagged[top_sw] = True

        # Order remaining candidates by value score
        remain = idx[order_sw[k_sw:]]
        if len(remain) > 0 and k_v > 0:
            order_val = np.lexsort((rng.random(len(remain)), -s_val[remain]))
            top_val = remain[order_val[:k_v]]
            flagged[top_val] = True

    return flagged


def student_t_score(R, pop_sd, space=T0, df=4.0):
    """Heavy-tailed variant of B2 (Student-t marginals with df degrees of freedom).

    Higher score = less probable under the population model = more suspicious.
    """
    Z, LJ = space.to_latent(R)
    sd = np.maximum(pop_sd, 1e-6)

    # Student-t log-density:
    # const = lgamma((df+1)/2) - lgamma(df/2) - 0.5*log(pi*df) - log(sd)
    const = lgamma((df + 1.0) / 2.0) - lgamma(df / 2.0) - 0.5 * log(pi * df) - np.log(sd)
    u = Z / sd
    log_kernel = -0.5 * (df + 1.0) * np.log1p((u ** 2) / df)
    log_marginals = const + log_kernel

    # Joint density with Jacobian correction
    log_dens = log_marginals.sum(axis=1) + LJ.sum(axis=1)
    return -log_dens
