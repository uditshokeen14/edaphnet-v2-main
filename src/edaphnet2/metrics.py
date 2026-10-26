"""Evaluation metrics (doc 11 §7).

Multiple testing is applied per *pool* of batches (default 50 batches, about one lab-day of
reports) rather than over the whole test set. FDR is estimated as the mean false discovery
proportion over pools, with FDP = 0 when a pool has no rejections.

Note (design constraint): a conformal p-value cannot be below 1/(N_cal + 1), so BH can only
reject k reports in a pool of m if 1/(N_cal + 1) <= q k / m. The calibration set must be
large relative to the pool size.
"""
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from .conformal import benjamini_hochberg, benjamini_yekutieli, conformal_pvalues


def recall_at_budget(scores, is_error, pool_ids, budget=0.05, seed=0):
    """Doc 18 §3: in each pool, flag the ceil(budget * pool size) highest scores (random
    tie-breaking); recall = flagged errors / all errors, summed over pools."""
    rng = np.random.default_rng(seed)
    s = np.nan_to_num(np.asarray(scores, float), nan=np.inf, posinf=1e300)
    hit = tot = 0
    flagged = np.zeros(len(s), bool)
    for pool in np.unique(pool_ids):
        idx = np.where(pool_ids == pool)[0]
        k = int(np.ceil(budget * len(idx)))
        order = np.lexsort((rng.random(len(idx)), -s[idx]))   # by score desc, ties random
        top = idx[order[:k]]
        flagged[top] = True
        hit += int(is_error[top].sum())
        tot += int(is_error[idx].sum())
    return hit / max(tot, 1), flagged


def weighted_conformal_pvalues(cal_scores, test_scores, w_cal, w_test):
    """Covariate-shift conformal p-values (Tibshirani et al. 2019):
    p_j = (sum_i w_i 1{s_i >= s_j} + w_j) / (sum_i w_i + w_j)."""
    order = np.argsort(cal_scores)
    cs, cw = np.asarray(cal_scores)[order], np.asarray(w_cal)[order]
    tail = np.concatenate([np.cumsum(cw[::-1])[::-1], [0.0]])   # sum of weights with s >= cs[i]
    pos = np.searchsorted(cs, test_scores, side="left")
    num = tail[pos] + w_test
    return np.minimum(1.0, num / (cw.sum() + w_test))


def density_ratio_weights(F_cal, F_test, seed=0):
    """Weights ~ p_test(x) / p_cal(x) from a logistic classifier (probabilities clipped to
    [0.01, 0.99]); returns (w_cal, w_test)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    X = np.vstack([F_cal, F_test])
    y = np.r_[np.zeros(len(F_cal)), np.ones(len(F_test))]
    X = np.nan_to_num(StandardScaler().fit_transform(X), nan=0.0, posinf=10, neginf=-10)
    p = LogisticRegression(max_iter=1000, random_state=seed).fit(X, y).predict_proba(X)[:, 1]
    p = np.clip(p, 0.01, 0.99)
    w = p / (1 - p) * (len(F_cal) / len(F_test))
    return w[: len(F_cal)], w[len(F_cal):]


def mondrian_pvalues(cal_scores, cal_groups, test_scores, test_groups):
    p = np.ones(len(test_scores))
    for g in np.unique(test_groups):
        m = test_groups == g
        p[m] = conformal_pvalues(np.asarray(cal_scores)[cal_groups == g], np.asarray(test_scores)[m])
    return p


def fdr_from_pvalues(p, is_error, pool_ids, q):
    rej = np.zeros(len(p), bool)
    fdps = []
    for pool in np.unique(pool_ids):
        m = pool_ids == pool
        r = benjamini_hochberg(p[m], q)
        rej[m] = r
        fdps.append(np.sum(r & ~is_error[m]) / r.sum() if r.sum() else 0.0)
    return float(np.mean(fdps)), int(np.sum(rej & is_error)) / max(1, int(is_error.sum())), rej


def detection_metrics(cal_scores, test_scores, is_error, pool_ids, q):
    p = conformal_pvalues(cal_scores, test_scores)
    out, rejections = {}, {}
    for name, proc in (("bh", benjamini_hochberg), ("by", benjamini_yekutieli)):
        rej = np.zeros(len(p), bool)
        fdps = []
        for pool in np.unique(pool_ids):
            m = pool_ids == pool
            r = proc(p[m], q)
            rej[m] = r
            n_rej = r.sum()
            fdps.append(np.sum(r & ~is_error[m]) / n_rej if n_rej else 0.0)
        tp = int(np.sum(rej & is_error))
        out[f"{name}_power"] = tp / max(1, int(is_error.sum()))
        out[f"{name}_fdr"] = float(np.mean(fdps))
        out[f"{name}_fdr_se"] = float(np.std(fdps, ddof=1) / np.sqrt(len(fdps))) if len(fdps) > 1 else None
        out[f"{name}_n_flag"] = int(rej.sum())
        rejections[name] = rej
    s = np.nan_to_num(np.asarray(test_scores, float), nan=np.inf, posinf=1e300)
    out["auprc"] = float(average_precision_score(is_error, s))
    out["auroc"] = float(roc_auc_score(is_error, s))
    out["prevalence"] = float(is_error.mean())
    out["min_attainable_p"] = 1 / (len(cal_scores) + 1)
    return out, p, rejections
