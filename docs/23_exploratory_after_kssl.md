# Exploratory Analyses After the KSSL Verdict

**Date:** 2 October 2026 · **Decision log:** D-020
**Status: EXPLORATORY.** None of these analyses was pre-registered. They do not change the
registered verdict (doc 21: A1 failed; A1-c, A2, A3 passed). They are reported to explain *why* the
verdict came out as it did and to generate hypotheses for the next registered test (doc 20).
The method code in `src/` was not changed. Outputs go to `results/exploratory/`, never into the
registered run folder.

**Scripts:** `scripts/exploratory_tables.py` (§1–2), `scripts/rescore_pools.py` (§3),
`scripts/mismatch_ops.py` + `configs/real_kssl3_mismatch.yaml` (§4).
**Data:** registered KSSL run `20261001-234902_real_kssl3_095deaa` (§1–3); new mismatch run (§4).

All numbers: share of erroneous reports found when the top 5% of reports per pool of 50 batches are
re-tested; 95% intervals from a cluster bootstrap over pools (2,000 resamples).

---

## 1. Swaps versus value errors

**Full minus the best existing method (B5, supervised), random batches**

| Witness | All errors | Swaps | Value errors |
|---|---|---|---|
| None (W0) | −0.033 [−0.050, −0.016] | +0.010 [−0.006, +0.026] | −0.080 [−0.114, −0.049] |
| Colour, perfect (W1 ΔE0) | +0.001 [−0.021, +0.024] | **+0.114 [+0.069, +0.156]** | **−0.119 [−0.143, −0.095]** |
| Colour, good phone (W1 ΔE2) | +0.014 [−0.009, +0.038] | **+0.103 [+0.064, +0.139]** | **−0.082 [−0.116, −0.050]** |
| Colour, noisy phone (W1 ΔE4) | +0.027 [+0.008, +0.049] | +0.088 [+0.052, +0.126] | −0.042 [−0.070, −0.015] |
| Spectrometer (W3) | +0.092 [+0.070, +0.113] | **+0.231 [+0.205, +0.258]** | −0.084 [−0.112, −0.058] |

Clustered batches show the same pattern (swaps +0.091 to +0.196, values −0.062 to −0.128).

**Reading.** The registered A1 failure (overall ≈ 0 with a colour witness) hides two effects of
opposite sign. With a phone-grade colour witness, EdaphNet finds **10–11 points more swapped
reports** than the best existing method (CI excludes 0), and **8–12 points fewer wrong values**.
With equal numbers of swaps and value errors (as injected), the two cancel. **The real-world error
mix therefore decides whether the method pays off**: the more swaps relative to wrong values, the
better it does.

**Where value errors are lost (W1 ΔE2, random):** gross analytical errors (Full 0.03 vs B5 0.26)
and ×10 slips (0.68 vs 0.80). Column swaps and ÷10 are found about equally well (0.72–0.78).

## 2. Ablations: what each component contributes (Full minus variant)

| Witness | Component removed | Swaps | Value errors |
|---|---|---|---|
| W1 ΔE2 | swap hypotheses | +0.386 [+0.332, +0.437] | −0.067 [−0.085, −0.049] |
| W1 ΔE2 | witness | +0.398 [+0.345, +0.449] | −0.035 [−0.051, −0.021] |
| W1 ΔE2 | corruption library | **−0.070 [−0.091, −0.050]** | **+0.023 [+0.010, +0.037]** |
| W1 ΔE2 | structured swap prior | −0.007 [−0.027, +0.013] | +0.005 [+0.001, +0.010] |
| W3 | swap hypotheses | +0.564 [+0.521, +0.608] | −0.077 [−0.100, −0.055] |
| W3 | corruption library | −0.013 [−0.020, −0.006] | +0.005 [−0.008, +0.017] |

**Reading.**
- Swap hypotheses and the witness are what make swaps findable (+0.39 to +0.56).
- Under a fixed budget they **cost value errors** (−0.04 to −0.08): budget slots go to suspected swaps.
- The corruption library is a trade-off rather than a pure gain or loss: it **helps value errors
  slightly (+0.02)** and **costs swaps more (−0.05 to −0.07)** at colour settings. At W3 both
  effects are near 0.
- The structured swap prior has no effect, again (H6 not supported).

## 3. Calibration and pool size: is "power ≈ 0" partly mechanical?

Registered analysis: BH at q = 0.10 per pool of 50 batches (1,200 reports). The stored conformal
p-values were re-tested with smaller pools. Power (realised FDR), random batches:

| Witness | Method | Pool 1 batch | 5 | 10 | 50 (registered) |
|---|---|---|---|---|---|
| W1 ΔE0 | **Full** | **0.250 (0.09)** | 0.082 (0.11) | 0.027 (0.14) | 0.000 (0.00) |
| W1 ΔE0 | B5 | 0.267 (0.09) | 0.153 (0.10) | 0.128 (0.11) | 0.071 (0.10) |
| W1 ΔE2 | **Full** | **0.185 (0.10)** | 0.041 (0.07) | 0.019 (0.11) | 0.005 (0.03) |
| W1 ΔE2 | B5 | 0.246 (0.11) | 0.128 (0.08) | 0.097 (0.09) | 0.051 (0.04) |
| W3 | **Full** | **0.573 (0.07)** | 0.403 (0.07) | 0.348 (0.09) | 0.235 (0.07) |
| W3 | B5 | 0.423 (0.10) | 0.322 (0.10) | 0.280 (0.11) | 0.242 (0.12) |

**Reading.**
- **Yes, largely mechanical.** With a colour witness and the registered pools, Full flagged almost
  nothing (≤ 0.005). Testing one batch at a time restores power to **0.19–0.25** while realised FDR
  stays at about q (0.09–0.10).
- Why: BH needs p ≤ q·k/m. Full's errors concentrate its evidence in a few reports per batch, and in
  a pool of m = 1,200 those few small p-values (floor ≈ 1/2,800) do not meet the threshold.
- B5 is less sensitive to pool size. It keeps power at large pools, but its realised FDR
  rises to 0.16–0.17 in some clustered settings at pools of 10–50 (above q).
- **Implication for practice:** per-batch error control is natural for a laboratory (a tray is
  released at once) and gives Full usable power with a colour witness. This is a hypothesis for the
  next registered test, not a result: the pool size was chosen after seeing these numbers.

## 4. Library mismatch: errors the model does not know

**Run:** `results/runs/20261002-172716_real_kssl3_mismatch_7099ff1` (1 seed, 4 settings; status clean).
Value errors were drawn **only** from four types outside the method's library: ×100/÷100,
×4–8 (or ÷4–8) gross errors, a value copied from the neighbouring report, and a dropped digit.
Swaps were injected as usual.

**Caveat:** B5 is trained on dev batches built with the *same* injection settings, so here it was
trained on these unknown error types too. It again had the advantage of knowing the true error mix.
With one seed and ~160–250 errors per cell, intervals are wide. **Update (2026-10-03):** repeated with five seeds in doc 26 §3; same pattern, narrower intervals.

**Full minus B5, re-testing the top 5%**

| Witness | Ordering | All errors | Swaps | Value errors (unknown types) |
|---|---|---|---|---|
| W1 ΔE2 | random | +0.029 [−0.017, +0.084] | **+0.100 [+0.021, +0.174]** | −0.068 [−0.098, −0.036] |
| W1 ΔE2 | clustered | −0.014 [−0.064, +0.057] | +0.085 [−0.014, +0.278] | −0.116 [−0.160, −0.073] |
| W3 | random | +0.053 [+0.034, +0.080] | +0.132 [+0.063, +0.230] | −0.010 [−0.059, +0.035] |
| W3 | clustered | +0.130 [+0.072, +0.187] | +0.256 [+0.189, +0.307] | −0.060 [−0.112, −0.019] |

**Share found by type (W1 ΔE2, random):** ×100 slips: Full 1.00, B5 1.00 · ×4–8 gross: 0.39 vs
0.54 · neighbour copy: 0.43 vs 0.52 · dropped digit: 0.22 vs 0.22.

**Reading.**
- **The pattern from §1 holds for unknown errors.** The swap advantage persists (+0.10 with a
  colour witness, CI > 0 in random batches), and the value-error deficit persists (−0.07 to −0.12).
- **Large unknown errors are found by everyone** (×100: ~100%). The method does not need them in its
  library to catch them, because they are implausible for any soil.
- **Subtle unknown errors are hard for every method:** dropped digits ~12–22%, neighbour copies
  ~23–53%. A copied neighbour value is a plausible soil value by construction.
- Removing the library changes value-error detection little for unknown types (+0.03, CI includes 0).
  The library's value is mainly for the error types it names.


## 5. Summary for the paper (exploratory, to be confirmed by a registered test)

1. A cheap colour witness **is enough to find swapped samples** (+10 points over the best existing
   method), **not to find wrong values** (−8 to −12 points). The real error mix decides the overall
   benefit.
2. The corruption library trades swap sensitivity for slightly better value-error detection.
3. "No power with a colour witness" was largely caused by the choice of pool size; per-batch control
   restores power at the nominal FDR.
4. The swap advantage and the value-error deficit both persist when the value errors are of types
   the method does not know (§4).
5. These motivate amendment v3 (doc 20): a combined policy (EdaphNet for swaps + a value checker such
   as B5) with per-batch error control, tested on new data.
