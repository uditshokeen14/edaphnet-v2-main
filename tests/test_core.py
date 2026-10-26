import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edaphnet2 import operators, swaps  # noqa: E402
from edaphnet2.conformal import benjamini_hochberg, conformal_pvalues  # noqa: E402
from edaphnet2.inference import InferenceConfig, infer_batch  # noqa: E402
from edaphnet2.properties import IDX, P, latent_corr, to_latent, to_natural  # noqa: E402
from edaphnet2.simulate import Generator, oracle_r2  # noqa: E402
from edaphnet2.witness import GaussianModel  # noqa: E402


def test_correlation_positive_definite():
    assert np.all(np.linalg.eigvalsh(latent_corr()) > 0)


def test_transform_roundtrip():
    z = np.random.default_rng(0).standard_normal((50, P))
    z2, lj = to_latent(to_natural(z))
    assert np.allclose(z, z2) and np.all(np.isfinite(lj))


def test_transposition_is_involution():
    for v, d in [(0.16, 2), (6.8, 1), (123.4, 1), (0.105, 3)]:
        for c in operators.transpose_candidates(v, d):
            assert v in operators.transpose_candidates(c, d)
    assert 0.61 in operators.transpose_candidates(0.16, 2)


def test_hypothesis_prior_normalised_and_contains_truth():
    r = np.array([6.8, 1.2, 0.12, 25.0, 15.0, 0.4, 8.0, 15.0])
    hs = operators.enumerate_hypotheses(r, 0.05)
    assert np.isclose(np.exp(hs.log_prior).sum(), 1.0)
    bad = r.copy(); bad[IDX["pH"]] = 68.0
    hs = operators.enumerate_hypotheses(bad, 0.05)
    assert any(np.allclose(y, r) for y in hs.y)


def test_swap_hypotheses_are_permutations():
    for cls, moved in swaps.enumerate_swaps(9):
        js = [j for j, _ in moved]; is_ = [i for _, i in moved]
        assert sorted(js) == sorted(is_) and all(j != i for j, i in moved), cls


def test_conformal_pvalues_uniform_under_null():
    rng = np.random.default_rng(1)
    p = conformal_pvalues(rng.standard_normal(2000), rng.standard_normal(20000))
    assert abs(np.mean(p <= 0.1) - 0.1) < 0.01


def test_weighted_pvalues_equal_unweighted_when_weights_are_one():
    from edaphnet2.metrics import weighted_conformal_pvalues
    rng = np.random.default_rng(2)
    cal, test = rng.standard_normal(500), rng.standard_normal(300)
    pw = weighted_conformal_pvalues(cal, test, np.ones(500), np.ones(300))
    assert np.allclose(pw, conformal_pvalues(cal, test))


def test_recall_at_budget_perfect_scores():
    from edaphnet2.metrics import recall_at_budget
    is_err = np.zeros(200, bool); is_err[:5] = True
    s = is_err.astype(float)
    r, flagged = recall_at_budget(s, is_err, np.zeros(200, int), budget=0.05)
    assert r == 1.0 and flagged.sum() == 10


def test_bh_known_example():
    p = np.array([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216])
    assert benjamini_hochberg(p, 0.05).sum() == 2


def test_oracle_r2_increases_with_lambda():
    assert np.all(oracle_r2(4.0) >= oracle_r2(1.0)) and np.all(oracle_r2(0.0) == 0)


@pytest.fixture(scope="module")
def fitted():
    g = Generator(lam=4.0, rng=np.random.default_rng(3))
    _, W, Y = g.samples(4000)
    return g, GaussianModel().fit(Y, W)


def test_decimal_error_detected_and_attributed(fitted):
    g, model = fitted
    b = g.batch(12)
    R = b.r.copy()
    R[3, IDX["pH"]] = round(R[3, IDX["pH"]] * 10, 1)
    out = infer_batch(R, model.mean(b.w), model, InferenceConfig())
    assert np.argmax(out["score"]) == 3
    assert out["kind"][3] == "value" and out["value_op"][3][1] == "x10@pH"


def test_swap_detected_with_strong_witness(fitted):
    g, model = fitted
    rng = np.random.default_rng(5)
    hits = 0
    for _ in range(20):
        b = g.batch(12)
        # swap two samples that differ strongly in organic carbon (the colour-driven property)
        oc = b.y[:, IDX["OC"]]
        i, j = int(np.argmin(oc)), int(np.argmax(oc))
        R = b.y.copy(); R[[i, j]] = R[[j, i]]
        out = infer_batch(R, model.mean(b.w), model, InferenceConfig())
        hits += out["kind"][i] == "swap" and out["partner"][i] == j
    assert hits >= 15
