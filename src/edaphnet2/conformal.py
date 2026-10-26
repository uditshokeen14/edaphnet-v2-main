"""Conformal p-values and multiple-testing procedures (tools; Bates et al. 2023)."""
import numpy as np


def conformal_pvalues(cal_scores, test_scores):
    """p_j = (1 + #{cal >= s_j}) / (N + 1). Valid for exchangeable clean test reports."""
    cal = np.sort(np.asarray(cal_scores, float))
    s = np.asarray(test_scores, float)
    n_ge = len(cal) - np.searchsorted(cal, s, side="left")
    return (1 + n_ge) / (len(cal) + 1)


def benjamini_hochberg(p, q):
    """Boolean rejection mask for BH at level q."""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    thresh = q * np.arange(1, m + 1) / m
    below = np.nonzero(p[order] <= thresh)[0]
    rej = np.zeros(m, bool)
    if len(below):
        rej[order[: below[-1] + 1]] = True
    return rej


def benjamini_yekutieli(p, q):
    m = len(p)
    return benjamini_hochberg(p, q / np.sum(1.0 / np.arange(1, m + 1)))
