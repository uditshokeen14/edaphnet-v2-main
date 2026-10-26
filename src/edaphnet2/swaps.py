"""Structured swap hypothesis set S (doc 11 §2.3).

A hypothesis is a permutation pi of report -> measured sample, stored sparsely as the list
of moved (report j, sample i) pairs. Classes:
  S1  adjacent transposition (j, j+1)
  S2  cyclic rotation by +-1 of a contiguous block of length >= 3, or by +-2 of length >= 5
      (the off-by-one / off-by-two tray shifts reported by Broman et al. 2014)
  S3  transposition of a non-adjacent pair
Identity (no swap) is S0.
"""
import numpy as np


def _rotation(a, b, s):
    """Block [a, b] inclusive rotated by s: report j measured sample a + (j - a + s) mod L."""
    L = b - a + 1
    return [(j, a + (j - a + s) % L) for j in range(a, b + 1)]


def enumerate_swaps(n):
    """Return list of (class, moved_pairs) for a batch of size n (identity excluded)."""
    hyps = []
    for j in range(n - 1):
        hyps.append(("S1", [(j, j + 1), (j + 1, j)]))
    for s, min_len in ((1, 3), (2, 5)):
        for L in range(min_len, n + 1):
            for a in range(0, n - L + 1):
                b = a + L - 1
                for sign in (+1, -1):
                    hyps.append(("S2", _rotation(a, b, sign * s)))
    for i in range(n):
        for j in range(i + 2, n):
            hyps.append(("S3", [(i, j), (j, i)]))
    return hyps


def log_prior(hyps, rho, class_mass=None, uniform=False):
    """Log prior of each non-identity hypothesis, plus log prior of identity.

    Structured (default): class masses {S1: .5, S2: .3, S3: .2} * rho, uniform within class.
    uniform=True: rho spread evenly over all hypotheses (ablation H6).
    """
    class_mass = class_mass or {"S1": 0.5, "S2": 0.3, "S3": 0.2}
    if uniform:
        lp = np.full(len(hyps), np.log(rho) - np.log(len(hyps)))
    else:
        counts = {}
        for c, _ in hyps:
            counts[c] = counts.get(c, 0) + 1
        lp = np.array([np.log(rho * class_mass[c]) - np.log(counts[c]) for c, _ in hyps])
    return np.log1p(-rho), lp


def random_swap(n, rng, class_mass=None):
    """Draw one swap event for injection. Returns (class, perm array pi with pi[j] = sample)."""
    class_mass = class_mass or {"S1": 1 / 3, "S2": 1 / 3, "S3": 1 / 3}
    classes = list(class_mass)
    c = classes[rng.choice(len(classes), p=np.array(list(class_mass.values())) / sum(class_mass.values()))]
    pi = np.arange(n)
    if c == "S1":
        j = rng.integers(n - 1)
        pi[j], pi[j + 1] = j + 1, j
    elif c == "S2":
        s = 1 if n < 5 or rng.random() < 0.7 else 2
        L = rng.integers(3 if s == 1 else 5, min(n, 8) + 1)
        a = rng.integers(0, n - L + 1)
        for j, i in _rotation(a, a + L - 1, s * (1 if rng.random() < 0.5 else -1)):
            pi[j] = i
    else:
        i, j = sorted(rng.choice(n, 2, replace=False))
        while j == i + 1:
            i, j = sorted(rng.choice(n, 2, replace=False))
        pi[i], pi[j] = j, i
    return c, pi
