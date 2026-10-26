# Detectability Findings (A4 / TC3), Exploratory

**Date:** 2026-10-01 · **Script:** `scripts/detectability_table.py`
**Runs analysed:** T0 simulation `20260923-230637_sim_t0_d75f3b6`; step-5 ICRAF
`20260925-011337_real_icraf8_2be2820`.
**Evidence tag:** EXPLORATORY. Both runs predate amendment v2. The pre-registered A4 table comes
from the KSSL run.

**Metric:** share of each error type found within a 5% re-test budget (top 5% of reports per
pool of 50 batches). "Best baseline" is chosen **separately for each error type**, which is an
oracle choice a lab could not make, so the gains shown for Full are **pessimistic**.

## 1. Real data (ICRAF-ISRIC, random batches): Full | gain over the best baseline

| Error type | W0 (none) | W1 colour ΔE0 | W1 ΔE2 | W1 ΔE8 | W2 bands | W3 spectrum |
|---|---|---|---|---|---|---|
| **swap** | 0.03 \| −0.01 | **0.54 \| +0.27** | 0.42 \| +0.18 | 0.31 \| +0.14 | 0.57 \| +0.26 | **0.87 \| +0.16** |
| column swap | 0.76 \| +0.06 | 0.61 \| −0.07 | 0.57 \| −0.07 | 0.66 \| −0.11 | 0.70 \| −0.04 | 0.66 \| −0.01 |
| decimal (×10, ÷10) | 0.40 \| −0.04 | 0.34 \| **−0.21** | 0.39 \| −0.17 | 0.35 \| −0.18 | 0.36 \| −0.13 | 0.49 \| −0.11 |
| unit confusion | 0.39 \| +0.01 | 0.29 \| −0.03 | 0.25 \| −0.02 | 0.26 \| −0.03 | 0.20 \| −0.04 | 0.31 \| −0.09 |
| gross analytical | 0.22 \| 0.00 | 0.13 \| −0.03 | 0.17 \| −0.09 | 0.13 \| −0.09 | 0.13 \| −0.06 | 0.11 \| −0.04 |
| digit transposition | 0.10 \| +0.02 | 0.05 \| −0.09 | 0.05 \| −0.09 | 0.10 \| −0.04 | 0.09 \| −0.05 | 0.08 \| −0.08 |

Clustered batches show the same pattern, with smaller swap gains (+0.06 to +0.11).

## 2. Synthetic data (T0, random batches): Full | gain

| Error type | λ = 0 | 1 | 2 | 4 |
|---|---|---|---|---|
| swap | 0.03 \| −0.01 | 0.37 \| +0.13 | **0.75 \| +0.19** | 0.92 \| +0.11 |
| decimal | 0.97 \| +0.01 | 0.93 \| −0.01 | 0.95 \| −0.02 | 0.95 \| −0.01 |
| column swap | 0.88 \| +0.02 | 0.91 \| −0.01 | 0.96 \| +0.02 | 0.87 \| −0.03 |
| digit transposition | 0.49 \| +0.04 | 0.57 \| 0.00 | 0.32 \| −0.05 | 0.57 \| +0.01 |
| unit | 0.33 \| +0.01 | 0.28 \| −0.01 | 0.31 \| −0.03 | 0.28 \| −0.06 |
| gross | 0.53 \| −0.04 | 0.36 \| −0.07 | 0.39 \| −0.09 | 0.54 \| −0.04 |

## 3. Findings

1. **The method's advantage is entirely in swaps.** On real data with a colour-only witness it
   finds 14–27 points more swapped reports than the best baseline (random batches).
2. **Swaps are invisible without a witness** (3% at W0), as expected: a swapped report is a
   perfectly plausible report of a different soil.
3. **Value errors are where the method is weak on real data.** Decimal slips are found much less
   often than by the best single baseline (−11 to −21 points). In simulation the gap is ~0.
   Two likely reasons: (a) under a fixed budget the method spends slots on suspected swaps;
   (b) real soil distributions are wider and heavier-tailed than the Gaussian-copula model
   assumes, so a ×10 value is less surprising to the model than to a simple range check.
4. **Some errors are hard for every method:** digit transpositions (5–10% on real data) and gross
   analytical errors (11–22%). They often produce plausible values; only repeat analysis finds them.
5. **Consequence for design (future work, not applied now; the method is frozen for the KSSL
   test):** a combined re-test policy, with the joint model for swaps and a dedicated
   heavy-tailed value checker for single values, should dominate both. It must be pre-registered
   and tested on new data (LUCAS / step 6).

## 4. Detectability statement (draft for the paper)

> With a colour-only witness, sample swaps become detectable (from ~3% to ~40–55% within a 5%
> re-test budget on real soils with injected errors), whereas detecting single wrong values does
> not benefit from the witness. Decimal and column swaps are mostly found by simple checks;
> digit transpositions and moderate analytical errors remain largely undetectable without
> re-analysis.
