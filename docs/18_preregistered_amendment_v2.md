# Pre-Registered Amendment v2: Re-test Ranking and Shift-Robust Calibration

**Date:** 2026-10-01 · **Status:** REGISTERED by git commit before any evaluation on the new
dataset. Supervisor review is still pending; any later change is a dated amendment below.
**Follows:** doc 11 (v1 specification), doc 17 (step-5 failure), D-014.

---

## 0. Why this amendment exists

Step 5 failed the v1 primary test (power at FDR 0.10 with a phone-grade witness). Two things
were learned from it:
1. As a **ranking** of suspicious reports, the joint model beat every baseline in every setting
   (exploratory, AUPRC).
2. **Error control broke** for almost every method; the post-hoc diagnosis is calibration-vs-test
   soil shift.

Both are post-hoc observations. This amendment turns them into **new, falsifiable hypotheses**
and fixes how they will be tested **on data never used before**. The ICRAF-ISRIC step-5 results
stay as reported (failed); they are not re-analysed under these new rules.

## 1. New research question

> When a soil lab can re-test only a small fraction of its reports, which reports should it
> re-test, and can it tell what went wrong with them?

This matches practice: re-testing has a cost, so labs work with a **re-test budget**, not with a
statistical guarantee.

## 2. Hypotheses

| ID | Hypothesis | Role |
|---|---|---|
| **A1** | With a re-test budget of 5% of reports, Full finds more erroneous reports than the best baseline | **primary** |
| A1-c | In clustered batches, Full is not worse than the best baseline | non-inferiority check |
| A2 | Shift-aware calibration (weighted or per-group) restores realised FDR ≤ 0.12 where pooled calibration fails | secondary |
| A3 | Full's error-type attribution beats rule-based repair (B6) by ≥ 0.20 | secondary (H4 replication) |
| A4 | Detection rate by error type and witness rung (detectability table) | descriptive |

## 3. Metrics (exact definitions)

- **Recall at budget (A1):** within each pool of 50 batches (1,200 reports), flag the
  ⌈0.05 × 1,200⌉ = 60 highest-scoring reports, breaking ties at random (seeded). Recall = flagged
  true errors / all true errors, summed over all pools of a setting. No calibration is involved,
  so A1 does not depend on the shift problem.
- **Realised FDR (A2):** as in v1 (BH at q = 0.10 per pool; mean FDP over pools).
- **Attribution (A3):** as in v1.

## 4. Pass / fail rules (fixed now)

| Hypothesis | Pass if |
|---|---|
| **A1** | At **W1 ΔE0 and W1 ΔE2 separately**, random ordering: Full − best baseline recall@5% ≥ **0.05**, with the 95% cluster-bootstrap CI (2,000 resamples over pools, pooled across seeds) **excluding 0** |
| A1-c | At W1 ΔE0 and ΔE2, clustered ordering: Full − best baseline ≥ **−0.02** (point estimate) |
| A2 | For Full, at least one shift-aware method keeps realised FDR ≤ 0.12 in **every** rung × ordering cell |
| A3 | Full attribution accuracy − B6 ≥ 0.20 in every rung with ≥ 30 flagged value errors |

"Best baseline" is chosen **per setting** among B0, B1, B2, B3, B4, B5, B7 by the same metric,
which favours the baselines.

**Consequences:**
- A1 pass (KSSL) → the paper's main claim is A1, to be confirmed on LUCAS when available.
- A1 fail → there is no method claim. The paper becomes the diagnostic/detectability study (doc 16, title B).
- A2 is reported whatever the outcome. A pass becomes a secondary contribution; a fail is a
  stated limitation.

## 5. Calibration methods for A2 (implemented before the test)

1. **Pooled** (v1): conformal p-values from all calibration nulls.
2. **Weighted conformal** (covariate-shift conformal; Tibshirani et al. 2019, with BH as in
   Jin & Candès 2023): weights = estimated density ratio test/calibration, from a logistic
   classifier separating calibration reports from test-pool reports. Features: the witness
   (if any) + the latent report values. Classifier probabilities are clipped to [0.01, 0.99].
3. **Mondrian (per group):** k-means (k = 4) on witness features (lab-only features for W0),
   fitted on the training split. p-values use calibration nulls of the same group only; a group
   with < 200 calibration nulls is merged with its nearest group.

## 6. Data (new, never used for evaluation)

- **KSSL Vis-NIR subset of OSSL v1.2** (CC-BY; file MD5 in `data/ossl_manifest_md5.txt`).
- Properties: the largest set with complete values among {OC, N, total C, CaCO₃}. If CaCO₃
  coverage is below 50%, the set is {OC, N, total C}.
- All depths; split by location (`id.location_olc_txt`) 50 / 15 / 35, seed **20261001**,
  asserted group-disjoint.
- Witness ladder: W0, W1 ΔE0, W1 ΔE2, W1 ΔE4, W3 (same construction as doc 14).
- The step-5 ICRAF-ISRIC data is **not** reused for evaluation under this amendment.
- **Confirmation dataset:** LUCAS (once access is granted), same rules, property set fixed when
  its audit is done and recorded as an amendment *before* evaluation.

## 7. Experimental settings

Batch size 24; 400 calibration, 200 dev, 300 test batches per setting; BH/budget pool = 50
batches; injected errors as in v1 (swap events in 20% of batches; value errors 2.5% per report);
inference prior ρ = 0.1, ε = 0.05; **5 seeds** (11, 22, 33, 44, 55); orderings random + clustered
(location/profile, as in step 5); methods Full, Full ablations, B0–B5, B7 (cleanlab).

## 8. Integrity

- The method (`src/edaphnet2/inference.py`, operators, swaps, witness) is **frozen** at the commit
  that registers this file. The only additions before the test are: the recall@budget metric, the
  weighted and Mondrian calibration, and the KSSL data builder.
- Every KSSL run must have git status *clean* and report its commit.
- Results are reported in full, including failures.

## Amendments

**Amendment 1 (2026-10-01, before any KSSL evaluation; D-017).** Calibration p-values use **one
score per distinct calibration sample** (one occurrence chosen at random with the setting seed),
not every occurrence across calibration batches. Reason: the diagnostic on the step-5 calibration
split (runs `20261001-233051`, `20261001-233621`) showed that reusing ~259 distinct samples as
~4,600 calibration scores makes conformal p-values anti-conservative (pseudo-replication):
B0 FDR 0.57 → 0.00 and B2 0.63 → 0.07 under exchangeable halves once de-duplicated. This applies
to pooled, weighted and Mondrian calibration (A2). A1 (recall at budget) uses no calibration and
is unaffected. The number of distinct calibration samples is reported for every setting.
