"""Evaluation script for Amendment v3: Combined Re-Test Policy (doc 20).

Evaluates candidate combined policies on real soil data with injected errors:
  - Full joint model (inference.py)
  - Baselines: B0, B1, B2 Gaussian, B2 Student-t, B5 supervised, B7 cleanlab
  - P1: Reciprocal Rank Fusion of Full's p_moved and value score
  - P2: 50/50 Budget Split between swap suspects and value suspects

Tests hypotheses:
  - C1: Combined policy recall at 5% budget vs Full and best baseline
  - C2: Retention of swap detection advantage
  - C3: Removal of value error deficit

Outputs results to results/exploratory/combined_policy_evaluation.csv
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from edaphnet2 import baselines as B, operators, swaps
from edaphnet2.combined_policy import budget_split_flagged, reciprocal_rank_fusion, student_t_score
from edaphnet2.inference import InferenceConfig, infer_batch
from edaphnet2.metrics import recall_at_budget
from edaphnet2.real_data import LatentTransform
from edaphnet2.space import RealSpace
from edaphnet2.witness import FixedGaussianModel
from run_real import load, make_batch, sample_indices


def evaluate_combined(tag="kssl3", rung="W1_dE2", seed=11, smoke=True):
    print(f"--- Evaluating Combined Policy on {tag} ({rung}) seed={seed} smoke={smoke} ---")
    D, Wt, space = load(tag)
    Y = space.print_values(D["X"])
    split, groups, depth = D["split"], D["groups"], D["depth"]
    MU = Wt[f"{rung}__mu"]
    F = Wt.get(f"{rung}__F")

    tr = np.where(split == "train")[0]
    te = np.where(split == "test")[0]

    M = {
        "wit": FixedGaussianModel(Wt[f"{rung}__S"]),
        "pop": FixedGaussianModel(Wt["W0__S"]),
        "range": B.RangeCheck(space).fit(Y[tr]),
    }
    cfg = InferenceConfig(rho=0.5, eps=0.01, space=space)

    # Standard injection parameters
    inj = {
        "swap_batch_prob": 0.5,
        "value_error_rate": 0.05,
    }

    n_batch = 24
    num_batches = 10 if smoke else 50
    rng = np.random.default_rng(seed)

    # Generate test batches
    batches = []
    p_moved_list, p_val_err_list, full_score_list = [], [], []
    b2_gauss_list, b2_student_list, b0_list, b1_list = [], [], [], []
    is_error_list, is_swap_list, is_val_list = [], [], []
    pool_ids = []

    pop_sd = np.sqrt(np.diag(Wt["W0__S"])) if Wt["W0__S"].ndim == 2 else np.sqrt(Wt["W0__S"])

    for b_idx in range(num_batches):
        idx = sample_indices(te, groups, depth, n_batch, "random", rng)
        b = make_batch(idx, Y, MU, F, space, rng, inj)
        batches.append(b)

        R = b.r
        mu = b.mu
        res = infer_batch(R, mu, M["wit"], cfg)

        full_score_list.append(res["score"])
        p_moved_list.append(res["p_moved"])
        p_val_err_list.append(res["p_value_err"])

        b0_list.append(M["range"].score(R))
        b1_list.append(B.rule_score(R, space))
        b2_gauss_list.append(B.population_score(R, M["pop"], space, pop_mean=np.zeros(space.P)))
        b2_student_list.append(student_t_score(R, pop_sd, space, df=4.0))

        is_error_list.append(b.is_error)
        is_swap_list.append(np.array([k == "swap" for k in b.kind]))
        is_val_list.append(np.array([k == "value" for k in b.kind]))
        pool_ids.append(np.full(n_batch, b_idx // 2))  # 2 batches per pool

    # Concatenate across batches
    is_error = np.concatenate(is_error_list)
    is_swap = np.concatenate(is_swap_list)
    is_val = np.concatenate(is_val_list)
    pools = np.concatenate(pool_ids)

    scores = {
        "Full": np.concatenate(full_score_list),
        "B0_range": np.concatenate(b0_list),
        "B1_rules": np.concatenate(b1_list),
        "B2_gauss": np.concatenate(b2_gauss_list),
        "B2_student_t": np.concatenate(b2_student_list),
    }
    p_moved = np.concatenate(p_moved_list)
    p_val_err = np.concatenate(p_val_err_list)

    # Variant P1: Rank fusion with Student-t B2
    scores["P1_fusion_student"] = reciprocal_rank_fusion(p_moved, scores["B2_student_t"])
    scores["P1_fusion_gauss"] = reciprocal_rank_fusion(p_moved, scores["B2_gauss"])

    # Compute recall at 5% budget for each scoring method
    metrics = []
    for name, s in scores.items():
        rec_all, flagged = recall_at_budget(s, is_error, pools, budget=0.05, seed=seed)
        rec_swap = float(is_swap[flagged].sum() / max(is_swap.sum(), 1))
        rec_val = float(is_val[flagged].sum() / max(is_val.sum(), 1))
        metrics.append({
            "method": name,
            "recall_all": round(float(rec_all), 4),
            "recall_swap": round(float(rec_swap), 4),
            "recall_value": round(float(rec_val), 4),
        })

    # Variant P2: 50/50 Budget split selection
    flagged_p2_student = budget_split_flagged(p_moved, scores["B2_student_t"], pools, budget=0.05, seed=seed)
    rec_all_p2_student = float(is_error[flagged_p2_student].sum() / max(is_error.sum(), 1))
    rec_sw_p2_student = float(is_swap[flagged_p2_student].sum() / max(is_swap.sum(), 1))
    rec_val_p2_student = float(is_val[flagged_p2_student].sum() / max(is_val.sum(), 1))
    metrics.append({
        "method": "P2_split_student",
        "recall_all": round(rec_all_p2_student, 4),
        "recall_swap": round(rec_sw_p2_student, 4),
        "recall_value": round(rec_val_p2_student, 4),
    })

    flagged_p2_gauss = budget_split_flagged(p_moved, scores["B2_gauss"], pools, budget=0.05, seed=seed)
    rec_all_p2_gauss = float(is_error[flagged_p2_gauss].sum() / max(is_error.sum(), 1))
    rec_sw_p2_gauss = float(is_swap[flagged_p2_gauss].sum() / max(is_swap.sum(), 1))
    rec_val_p2_gauss = float(is_val[flagged_p2_gauss].sum() / max(is_val.sum(), 1))
    metrics.append({
        "method": "P2_split_gauss",
        "recall_all": round(rec_all_p2_gauss, 4),
        "recall_swap": round(rec_sw_p2_gauss, 4),
        "recall_value": round(rec_val_p2_gauss, 4),
    })

    df = pd.DataFrame(metrics).sort_values("recall_all", ascending=False)
    out_dir = ROOT / "results" / "exploratory"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"combined_policy_{tag}_{rung}.csv"
    df.to_csv(csv_path, index=False)

    print("\nResults summary (Recall at 5% Budget):")
    print(df.to_string(index=False))
    print(f"\nSaved results to: {csv_path}")

    # Hypothesis check:
    full_row = df[df.method == "Full"].iloc[0]
    best_comb = df[df.method.isin(["P1_fusion_student", "P2_split_student", "P1_fusion_gauss", "P2_split_gauss"])].iloc[0]
    best_base = df[df.method.isin(["B0_range", "B1_rules", "B2_gauss", "B2_student_t"])].iloc[0]

    verdict = {
        "dataset": tag,
        "witness": rung,
        "seed": seed,
        "smoke": smoke,
        "best_combined": best_comb["method"],
        "combined_recall_all": best_comb["recall_all"],
        "full_recall_all": full_row["recall_all"],
        "best_baseline_recall_all": best_base["recall_all"],
        "gain_over_full": round(best_comb["recall_all"] - full_row["recall_all"], 4),
        "gain_over_best_baseline": round(best_comb["recall_all"] - best_base["recall_all"], 4),
        "swap_retention": round(best_comb["recall_swap"] - full_row["recall_swap"], 4),
        "value_gain_vs_full": round(best_comb["recall_value"] - full_row["recall_value"], 4),
    }

    verdict_path = out_dir / f"combined_policy_verdict_{tag}_{rung}.json"
    verdict_path.write_text(json.dumps(verdict, indent=2))
    print(f"Saved verdict to: {verdict_path}")
    return df, verdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="kssl3")
    parser.add_argument("--witness", default="W1_dE2")
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    evaluate_combined(tag=args.tag, rung=args.witness, seed=args.seed, smoke=args.smoke)
