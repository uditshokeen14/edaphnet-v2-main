# Step 3 — T0 Simulation Results

**Run:** `results/runs/20260923-230637_sim_t0_d75f3b6` (git `d75f3b6`, status *clean*)
**Summary script:** `scripts/summarise_runs.py` → `summary_*.csv` in the run folder
**Evidence tag:** **MEASURED-SYNTHETIC.** Synthetic Gaussian-copula data in which the method's
model family matches the generator, so these results are an **optimistic, best-case** test of
the mechanism. They say nothing about real soils or real photos.

Setting: batch size 24; injected error prevalence ≈ 5% of reports (swap events in 20% of
batches, value errors 2.5% per report); q = 0.10; BH per pool of 50 batches; 300 test batches,
400 calibration batches per mode, 3 seeds.

## 1. Witness strength λ → predictive R² (oracle)

| λ | OC | N | clay | CEC | pH | K | Ca | P |
|---|---|---|---|---|---|---|---|---|
| 0.5 | 0.14 | 0.11 | 0.07 | 0.05 | 0.01 | 0.02 | 0.03 | 0.01 |
| 1.0 | 0.37 | 0.30 | 0.24 | 0.16 | 0.05 | 0.05 | 0.09 | 0.02 |
| 2.0 | 0.66 | 0.54 | 0.55 | 0.34 | 0.15 | 0.12 | 0.18 | 0.03 |
| 4.0 | 0.83 | 0.67 | 0.81 | 0.50 | 0.37 | 0.18 | 0.28 | 0.03 |

## 2. Power at FDR 0.10 (injection-aware calibration, mean of 3 seeds)

| Ordering | Method | λ=0 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| random | **Full** | 0.27 | 0.26 | **0.39** | **0.65** | **0.78** |
| random | best baseline | 0.26 (B7) | 0.25 (B7) | 0.27 (B7) | 0.42 (B5) | 0.66 (B5) |
| clustered | **Full** | 0.28 | 0.25 | 0.32 | **0.51** | **0.73** |
| clustered | best baseline | 0.27 (B7) | 0.24 (B7) | 0.28 (B7) | 0.31 (B5) | 0.55 (B5) |

Full − best baseline: **+0.12 to +0.25** for λ ≥ 1 (random) and λ ≥ 2 (clustered);
**≈ 0 (≤ 0.01)** for λ ≤ 0.5. With only 3 seeds the seed-bootstrap CIs are not reliable
intervals; they are reported in `summary_full_vs_best_baseline.csv` for completeness only.

## 3. Where the gain comes from (ablations)

| Ablation | Effect vs Full |
|---|---|
| − swap hypotheses (`Full-noswap`) | power falls to the B7 level (e.g. random λ=2: 0.65 → 0.29). **The gain is almost entirely swap detection.** |
| − witness (`Full-nowitness`) | power ≈ 0.26 at every λ: value errors are still found from the lab-internal joint model; swaps are not |
| − corruption library (`Full-nolibrary`) | power −0.01 to −0.04; realised FDR higher. Main role of the library is **attribution**, not detection |
| uniform vs structured swap prior | no consistent difference: **H6 not supported** in T0 |

## 4. Attribution among correctly flagged errors (injection-aware calibration)

- Value errors: correct kind 99–100%; **correct operator 84–92%**, vs **32–50%** for the
  rule-based unit/decimal repair baseline (B6).
- Swaps: correct partner 72% (λ=1), 89–91% (λ=2), 96–98% (λ=4). At λ ≤ 0.5, swaps are
  essentially never flagged.

## 5. Error control (H3: realised FDR ≤ q + 0.02 = 0.12)

- **Clean-batch calibration fails for the joint methods:** Full up to 0.18, `Full-nolibrary`
  0.21, `Full-uniformprior` 0.23. This confirms the dependence caveat in doc 11 §2.6.
- **Injection-aware calibration** keeps Full at 0.06–0.12 in 9 of 10 settings; one exceedance
  (clustered, λ=0.5: 0.142). Several *baselines* also show values of 0.12–0.13, which suggests
  the FDR estimates are noisy (only 6 pools per seed). H3 needs a larger run before any
  claim is made.

## 6. What this means for the hypotheses (T0 only)

| Hypothesis | T0 outcome |
|---|---|
| H1: Full beats the best baseline | **Supported** for moderate/strong witnesses (λ ≥ 1–2); **not** at λ ≤ 0.5 |
| H2: advantage largest for the *weakest* witness | **Refuted in T0.** Gain ≈ 0 at the weakest witness, peaks at λ = 2 (OC R² ≈ 0.66, clay ≈ 0.55), and shrinks at λ = 4 as baselines catch up |
| H3: FDR validity | Clean calibration: **violated**. Injection-aware: **mostly holds, not yet established** |
| H4: attribution beats rules | **Supported** (84–92% vs 32–50%) |
| H5: detectability map | not yet analysed (per-report predictions saved) |
| H6: structured swap prior helps | **Not supported** |

## 7. Consequences for the research claim

1. The contribution is **not** "weak witnesses are enough". It is closer to: *joint batch
   inference turns a moderately informative, cheap witness (R² ≈ 0.3–0.7 on colour-linked
   properties) into swap detection and error attribution that per-value, swap-only and
   supervised baselines do not achieve.* Whether a real phone photo reaches that band is
   exactly what Steps 4–5 must measure.
2. Injection-aware calibration is necessary, not optional. It is a candidate methodological
   contribution in its own right, and must be tested with larger runs (more pools, more seeds).
3. The structured swap prior can be dropped or kept as a design detail; it is not a claim.
4. Required before step 5: (a) a larger H3 run; (b) replace the simplified B7 with the authors'
   implementation; (c) the H5 detectability analysis from the saved predictions.
