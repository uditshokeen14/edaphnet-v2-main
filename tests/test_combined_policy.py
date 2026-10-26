import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edaphnet2.combined_policy import budget_split_flagged, reciprocal_rank_fusion, student_t_score
from edaphnet2.space import T0


def test_reciprocal_rank_fusion_basic():
    # scores_swap: item 0 highest, item 1 middle, item 2 lowest
    s_swap = np.array([10.0, 5.0, 1.0])
    # scores_value: item 2 highest, item 1 middle, item 0 lowest
    s_val = np.array([0.1, 0.5, 0.9])

    fused = reciprocal_rank_fusion(s_swap, s_val, k=60)
    assert len(fused) == 3
    # item 1 is rank 2 in both -> 1/(60+2) + 1/(60+2) = 2/62 = ~0.032258
    # item 0 is rank 1 and 3 -> 1/61 + 1/63 = ~0.032264
    # item 2 is rank 3 and 1 -> 1/63 + 1/61 = ~0.032264
    assert np.all(np.isfinite(fused))
    assert fused[0] > 0
    assert fused[1] > 0


def test_reciprocal_rank_fusion_empty():
    fused = reciprocal_rank_fusion([], [])
    assert len(fused) == 0


def test_budget_split_flagged():
    n = 100
    pool_ids = np.zeros(n, int)
    s_swap = np.linspace(0, 1, n)
    s_val = np.linspace(1, 0, n)

    # Budget 5%: ceil(0.05 * 100) = 5
    # K_swap = 5 // 2 = 2 (items 99, 98)
    # K_val = 5 - 2 = 3 (items 0, 1, 2)
    flagged = budget_split_flagged(s_swap, s_val, pool_ids, budget=0.05, seed=42)
    assert flagged.sum() == 5
    assert flagged[99] and flagged[98]
    assert flagged[0] and flagged[1] and flagged[2]


def test_budget_split_multi_pool():
    n = 200
    pool_ids = np.repeat([0, 1], 100)
    s_swap = np.random.randn(n)
    s_val = np.random.randn(n)

    flagged = budget_split_flagged(s_swap, s_val, pool_ids, budget=0.05, seed=42)
    # Each pool of 100 has 5 flagged reports -> 10 total
    assert flagged.sum() == 10
    assert flagged[:100].sum() == 5
    assert flagged[100:].sum() == 5


def test_student_t_score():
    R = np.array([
        [6.5, 2.0, 15.0, 50.0, 18.0, 0.4, 8.0, 2.0],       # normal report
        [65.0, 20.0, 150.0, 500.0, 180.0, 4.0, 80.0, 20.0]  # extreme outlier
    ])
    sd = np.ones(T0.P)
    scores = student_t_score(R, sd, space=T0, df=4.0)

    assert len(scores) == 2
    assert np.all(np.isfinite(scores))
    assert scores[1] > scores[0]  # outlier has higher score
