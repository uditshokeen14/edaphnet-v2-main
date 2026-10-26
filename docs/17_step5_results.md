# Step 5 — Go/No-Go Results on Real Data (ICRAF-ISRIC + injected errors)

> **CORRECTION (2026-10-01, D-016/D-017):** §2's explanation ("calibration-vs-test soil shift") is
> **only partly right**. A diagnostic on the calibration split showed that the main cause of the
> baselines' 40–90% false alarms was **my experiment design**: the 511 calibration samples were
> reused across 400 batches, and every reuse was counted as an independent calibration score
> (pseudo-replication), so the p-values were far too small. With one score per distinct sample, the
> baselines' FDR falls to ≤ 0.07, but with only ~259–511 distinct samples almost nothing can be
> flagged at all. Full is additionally sensitive to profile shift at W1 (FDR 0.39 even after the
> fix). Consequence: the step-5 primary comparison at FDR 0.10 ran with a **flawed calibration
> procedure for every method**, so it is not a valid test of H1 in either direction. The recorded
> verdict ("not passed") stands as the outcome of the pre-registered analysis; it is not
> re-labelled. The clean test is the amendment-v2 run on KSSL (doc 18).

**Run:** `results/runs/20260925-011337_real_icraf8_2be2820` (method code `2be2820`; resumed once
with identical method code, D-012/`--resume`). 42 settings = 7 witness rungs × 2 batch orderings
× 3 seeds; 300 test batches per setting (24 reports each; ≈ 5% erroneous reports).
**Evidence tag:** real lab values and real witnesses (colour/bands/spectrum from lab spectra),
**injected** errors. Calibration: injection-aware (D-010).

---

## 1. Pre-registered primary test (doc 11 §7, reframed by D-010/D-011)

**Primary metric:** power at FDR 0.10 (conformal p-values + BH per pool of 50 batches).
**Decision rule, fixed before the run:** the phone claim needs Full > best baseline at W1
(ΔE ≤ 2) with the CI excluding 0 **in both orderings**.

| Ordering | Rung | Full power | Best baseline (power) | Diff | Seed-bootstrap CI* |
|---|---|---|---|---|---|
| random | W1 ΔE0 | 0.157 | B2 0.125 | +0.032 | (−0.006, 0.091) |
| random | W1 ΔE2 | 0.163 | B2 0.114 | +0.049 | (0.006, 0.117) |
| clustered | W1 ΔE0 | 0.069 | B5 0.122 | **−0.053** | (−0.078, −0.035) |
| clustered | W1 ΔE2 | 0.113 | B2 0.127 | −0.014 | (−0.028, 0.013) |
| random | W2 | 0.269 | B2 0.122 | +0.146 | (0.079, 0.212) |
| random | W3 | 0.542 | B4 0.340 | +0.202 | (0.153, 0.235) |
| clustered | W3 | 0.170 | B4 0.130 | +0.040 | (0.000, 0.070) |

\*3 seeds only; these intervals are indicative, not reliable.

**Verdict under the pre-registered rule: NOT PASSED.** With a colour-only (phone-grade)
witness, the gain is not clearly above zero in the random ordering and is negative in the
clustered ordering. **The claim "a phone photo enables better verification at controlled FDR"
is not supported by this test and is dropped in its current form.**

## 2. Error control failed for almost every method (H3)

Realised FDR at nominal q = 0.10 (mean of 3 seeds):

| | W0 | W1 ΔE0 | W1 ΔE2 | W2 | W3 |
|---|---|---|---|---|---|
| **Full (random / clustered)** | 0.00 / 0.00 | 0.03 / 0.00 | 0.14 / 0.14 | 0.07 / 0.12 | 0.10 / 0.09 |
| B0 range | 0.51 / 0.54 | 0.52 / 0.39 | 0.51 / 0.50 | 0.52 / 0.51 | 0.52 / 0.57 |
| B2 lab-only | 0.44 / 0.57 | 0.52 / 0.37 | 0.51 / 0.50 | 0.48 / 0.61 | 0.45 / 0.59 |
| B7 cleanlab | 0.16 / 0.26 | 0.41 / 0.42 | 0.50 / 0.39 | 0.52 / 0.35 | 0.43 / 0.36 |
| B1 rules | ≈ 0.85–0.89 in every setting | | | | |

Full stays near q (worst 0.24, random W1 ΔE4), but most baselines are far above it.
**Consequence:** the baselines' "power" at q = 0.10 is inflated by false alarms. The primary
comparison is therefore **not a fair like-for-like comparison**, in either direction.

**Diagnosed cause (post hoc, to be tested):** calibration uses the cal split, which has only
**82 profiles / 511 distinct samples** (reused across 400 batches), while test batches come from
**195 different profiles**. Soils in the test pool that are more extreme than anything in the
calibration pool get the minimum conformal p-value, so BH flags many clean reports. Conformal
validity assumes calibration and test nulls are exchangeable; under **profile-level shift with
a small calibration pool**, that assumption fails. Full is less affected because its scores are
conditioned on the witness and on the other values in the report.

## 3. Secondary, threshold-free comparison (AUPRC; exploratory, not the primary metric)

| Ordering | Rung | Full | Best baseline | Diff (min–max over seeds) |
|---|---|---|---|---|
| random | W0 | 0.207 | 0.191 (B5) | +0.016 (0.004–0.033) |
| random | **W1 ΔE0** | **0.430** | 0.235 (B7) | **+0.195 (0.188–0.200)** |
| random | W1 ΔE2 | 0.358 | 0.211 (B5) | +0.146 (0.134–0.170) |
| random | W1 ΔE8 | 0.301 | 0.205 (B5) | +0.097 (0.045–0.134) |
| random | W2 | 0.473 | 0.230 (B4) | +0.243 |
| random | W3 | 0.695 | 0.487 (B4) | +0.208 |
| clustered | W1 ΔE0 | 0.259 | 0.223 (B5) | +0.036 (0.019–0.044) |
| clustered | W1 ΔE2 | 0.298 | 0.222 (B7) | +0.076 (0.055–0.118) |
| clustered | W3 | 0.419 | 0.269 (B4) | +0.150 |

(Prevalence ≈ 0.05, so a random ranking has AUPRC ≈ 0.05.)

**Reading:** as a *ranking* of which reports to check first, Full is better than every baseline
in **every rung, both orderings and every seed** (one exception: clustered W0, where it is on
par). With a colour-only witness it roughly doubles AUPRC in random batches. The advantage is
much smaller in clustered batches.

## 4. Ablations (AUPRC, random ordering, W1 ΔE0)

| Variant | AUPRC | Meaning |
|---|---|---|
| Full | 0.430 | — |
| − swaps (`Full-noswap`) | 0.225 | swap modelling gives most of the gain (as in T0) |
| − witness (`Full-nowitness`) | 0.206 | the photo proxy is what makes swaps findable |
| − corruption library (`Full-nolibrary`) | 0.384 | the library adds detection *and* attribution |
| uniform swap prior | 0.429 | structured prior: no effect (H6 again not supported) |

## 5. Attribution (among correctly flagged errors)

- Correct error type for value errors: **89–98%**, vs **37–51%** for rule-based repair (B6):
  H4 supported on real data.
- Correct swap partner: 89–93% at W1 ΔE0, 75–87% at W2, 87–99% at W3 (small counts at W1 ΔE8).

## 6. Why the clustered ordering is so hard

Clustered batches here are **consecutive depth layers of the same soil profile**. Neighbouring
samples are near-identical in colour and chemistry, so a swap between them is almost
undetectable, and matters little agronomically. Real lab trays usually group samples by farm
(different fields), which is less extreme. This is a limitation of how the clustered condition
was built. It is **not** a reason to discard it: the pre-registered rule includes it.

## 7. Hypotheses after step 5

| Hypothesis | T0 (synthetic) | Step 5 (real + injected) |
|---|---|---|
| H1: Full beats baselines at FDR 0.10 with a phone-grade witness | supported (moderate witness) | **not supported** (primary rule) |
| H1′ (secondary, exploratory): Full ranks errors better (AUPRC) | — | **supported in all settings** |
| H2: gain largest for the weakest witness | refuted | refuted (gain grows with witness strength) |
| H3: FDR controlled | mostly (injection-aware) | **failed for baselines; Full near q but not within +0.02 everywhere** |
| H4: attribution beats rules | supported | **supported** |
| H6: structured swap prior helps | not supported | not supported |

## 8. What this means (honest conclusion)

1. **The pre-registered go/no-go did not pass.** We do not claim that a phone photo enables
   better verification at controlled FDR.
2. **The underlying detector is strong:** it ranks errors far better than all existing methods
   and explains them correctly. The weak link is **turning scores into trustworthy flags**
   (calibration under profile shift), which breaks *every* method on this data.
3. This points to a specific, testable research question: **how to calibrate lab-report
   verification when soils in use differ from soils in the calibration set** (e.g.
   group-conditional or weighted conformal calibration, larger and more diverse calibration pools).
4. **Forking-paths rule:** any fix designed after seeing these results must be pre-registered
   as an amendment and tested on data **not used here** (LUCAS, or step-6 data). Re-tuning on
   the ICRAF test split would invalidate the result.

## 9. Decisions (see D-014)

- The paper can no longer be "phone-based verification works" (working title A). The candidate
  framing becomes working title B: a detectability study plus a ranking/attribution method, with
  the calibration failure reported as a finding.
- Next research step: an amended, pre-registered calibration experiment on independent data.
