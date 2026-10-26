# Amendment-v2 Pre-Registered Test on KSSL: Results

**Run:** `results/runs/20261001-234902_real_kssl3_095deaa` (method commit `095deaa`, status clean;
50 settings = 5 rungs × 2 orderings × 5 seeds, all completed).
**Analysis:** `scripts/analyse_amendment.py`, committed in `7fb9b73` (23:49, the minute the run started) and edited once in `0fea0b0` (23:56) **while the run was in progress**, after testing it on a copy of the first two finished settings. That edit only made A3 report "not evaluable" instead of "fail" when no cell qualifies, and added an incomplete-run warning; the pass/fail thresholds were not changed, and the final A3 verdict does not depend on it (two cells qualified). The verdict was computed after the run finished.
**Data:** KSSL Vis-NIR (OSSL v1.2, CC-BY), 19,746 samples / 6,999 locations; properties OC, N, total C.
**Evidence tag:** real lab values + real-spectrum-derived witnesses + **injected** errors.

## Verdict (pre-registered rules, doc 18 §4)

| Hypothesis | Rule | Result |
|---|---|---|
| **A1** re-test ranking with a colour witness | ≥ +0.05, CI > 0 at W1 ΔE0 and ΔE2 (random) | ❌ **FAIL**: +0.001 (CI −0.022, 0.023) and +0.014 (CI −0.008, 0.038) |
| A1-c non-inferiority, clustered | ≥ −0.02 | ✅ pass (+0.013, +0.010) |
| A2 shift-aware calibration keeps FDR ≤ 0.12 | every cell, weighted or Mondrian | ✅ pass (all cells ≤ 0.07), but at W0–W1 power ≈ 0 |
| A3 attribution beats rule repair by ≥ 0.20 | cells with ≥ 30 flagged value errors | ✅ pass in the two eligible cells (W3): 0.97–1.00 vs 0.24–0.29 |

## Recall at a 5% re-test budget (Full vs best baseline, pooled over 5 seeds)

| Rung | Ordering | Full | Best baseline | Diff [95% CI] | Full: swaps / values |
|---|---|---|---|---|---|
| W0 | random | 0.238 | 0.271 (B5) | −0.033 [−0.049, −0.016] | 0.05 / 0.45 |
| **W1 ΔE0** | random | 0.416 | 0.415 (B5) | **+0.001 [−0.022, 0.023]** | 0.46 / 0.37 |
| **W1 ΔE2** | random | 0.410 | 0.396 (B5) | **+0.014 [−0.008, 0.038]** | 0.44 / 0.38 |
| W1 ΔE4 | random | 0.382 | 0.354 (B5) | +0.028 [0.010, 0.049] | 0.35 / 0.43 |
| W3 | random | 0.604 | 0.512 (B5) | +0.092 [0.069, 0.113] | 0.75 / 0.42 |
| W1 ΔE0 | clustered | 0.355 | 0.342 (B5) | +0.013 [−0.011, 0.039] | 0.31 / 0.41 |
| W3 | clustered | 0.522 | 0.446 (B5) | +0.076 [0.054, 0.098] | 0.60 / 0.44 |

## Interpretation

1. **The pre-registered primary claim failed.** With a phone-grade colour witness, the joint model
   does not find meaningfully more errors within a 5% budget than the best existing approach.
2. **The best competitor is B5**, a supervised classifier trained on the *same injected error mix*
   as the test (stated in doc 11 §6 as an advantage it would not have in practice). It combines
   simple checks with B4 swap matching. In practice the true error mix is unknown.
3. **With a spectrometer-grade witness (W3), Full wins clearly** (+0.08 to +0.09, CI > 0, both
   orderings). This was not the pre-registered claim and is reported as a secondary,
   witness-strength finding (consistent with T0, doc 13).
4. **Calibrated error control works once calibration is done correctly** (≈ 2,800 distinct
   calibration samples, one score per sample): realised FDR ≤ 0.09 for every method. With a
   colour witness it flags almost nothing at q = 0.10; only a strong witness has power.
5. **Attribution remains the method's clearest strength** (97–100% vs 24–29%), but only where
   enough errors are flagged (W3).
6. **Colour-friendly caveat (doc 18 §6):** even with all-carbon properties and a strong colour
   signal (R² ≈ 0.7), the colour witness did not beat B5. This weakens the phone claim further.

## Consequences

- No "phone-based re-test" claim. The paper follows the A1-fail framing (doc 16 title B):
  detectability across witness strength, calibration requirements, attribution, and the
  spectrometer-grade result as a secondary finding.
- The combined policy (draft amendment v3, doc 20) is the remaining method idea. B5's strength
  suggests it should be included as a component.
