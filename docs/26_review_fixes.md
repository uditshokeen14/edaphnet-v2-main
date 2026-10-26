# Analyses After the External Review of Draft v0

**Date:** 3 October 2026 · **Decision log:** D-025
**Status: EXPLORATORY.** None of these analyses was pre-registered. They do not change the
registered KSSL verdict (doc 21: A1 failed; A1-c, A2, A3 passed). They answer points raised in an
external review of `docs/paper/draft_v0.md` (an AI-assisted review that the student obtained from a
separate Claude session). The method code in `src/` was not changed.

**Scripts:** `scripts/diag_gross.py` (§1), `scripts/error_mix.py` (§2), `configs/real_kssl3_mismatch5.yaml` +
`scripts/exploratory_tables.py` (§3), `scripts/make_paper_figures.py` (§4).
**Outputs:** `results/exploratory/20261001-234902_real_kssl3_095deaa/` (§1–2),
`results/exploratory/20261003-154345_real_kssl3_mismatch5_d54e40c/` (§3), `docs/paper/figures/` (§4).

---

## 1. Why EdaphNet finds so few gross analytical errors

**Question (review).** Doc 23 reports gross-error recall of 0.03 for Full vs 0.26 for B5 (good-phone
colour, random batches), and several Full variants give exactly 0.034. Bug or real?

**Findings** (`gross_recall_by_method.csv`, `gross_full_explanations.csv`, `gross_recall_by_property.csv`):

| (W1 ΔE2, random; 208 gross errors) | Full | B5 | B1 rules |
|---|---|---|---|
| Recall at 5% budget | 0.034 | 0.255 | 0.207 |
| Median percentile of the score within its pool | 0.75 | 0.80 | 0.77 |
| Recall, gross error on OC | 0.104 | 0.433 | 0.343 |
| Recall, gross error on total C | 0.000 | 0.328 | 0.197 |
| Recall, gross error on N | 0.000 | 0.050 | 0.100 |

1. **No scoring artefact.** No method's budget cut fell inside a tie of zero scores in any pool.
   The identical 0.034 = 7/208 for Full, Full-nolibrary and Full-nowitness is a small-count
   coincidence; without a witness (W0) the variants are identical by construction.
2. **Full notices gross errors but not strongly enough.** It ranks them above most reports (median
   75th percentile) but the top 5% is filled first by swaps and ×10 slips with near-certain
   posteriors.
3. **Misattribution.** Of the 201 gross errors Full did not flag, it explained 178 as a digit
   transposition (90) or a column interchange (88).
4. **The baselines use a hard constraint.** B1 checks OC ≤ 1.05 × total C; B5 learns it from the
   injected training mix. Gross errors on OC and total C break this constraint; gross errors on N
   break none and are hard for every method. Full's Gaussian witness model represents the
   correlation between carbon properties but not the inequality.

**Conclusion.** A real modelling limitation, not a bug. Paper §7.5 and §8 updated; adding hard
property constraints to the likelihood is a direct extension (not done: method frozen).

## 2. Error-mix sensitivity

**Question (review).** The injected mix (≈ 50% swaps) is arbitrary and the colour verdict depends on it.

**Method.** For each pool of 50 batches and swap share π ∈ {0.1, …, 0.9}: keep N = ⌊min(#swaps,
#values)/0.9⌋ errors (same N for every π), round(πN) of them swaps; keep clean reports in proportion
N/#errors, so prevalence and the 5% budget are as registered; rank by the stored scores. 20
resamples per pool; 95% cluster bootstrap over pools (30 pools per setting). **Approximation:**
scores were computed in the original batches and are not recomputed.

**Findings** (`error_mix.csv`; Figure 6 of the paper). EdaphNet minus B5:

| Swap share | Colour ΔE2, random | Colour ΔE2, clustered | Spectrometer, random |
|---|---|---|---|
| 10% | −0.054 [−0.081, −0.027] | −0.065 [−0.084, −0.047] | −0.026 [−0.046, −0.006] |
| 30% | −0.020 [−0.041, +0.003] | −0.028 [−0.047, −0.010] | +0.022 [+0.005, +0.040] |
| 50% | +0.008 [−0.013, +0.029] | +0.007 [−0.014, +0.028] | +0.076 [+0.056, +0.095] |
| 60% | +0.024 [+0.001, +0.048] | +0.025 [−0.001, +0.053] | +0.097 [+0.079, +0.116] |
| 70% | +0.041 [+0.018, +0.066] | +0.045 [+0.018, +0.076] | +0.127 [+0.105, +0.149] |
| 90% | +0.066 [+0.037, +0.095] | +0.086 [+0.051, +0.123] | +0.170 [+0.146, +0.196] |

- With colour, EdaphNet beats B5 once 60–70% of errors are swaps; with a spectrometer, from 30%.
- EdaphNet beats the swap-only matcher B4 at every mix (colour +0.06 to +0.13; spectrometer +0.10 to +0.13).
- Rule checks (B1) fall from ≈ 0.27 to ≈ 0.08 as swaps replace value errors.
- The registered mix (52–56% swaps) sits at the colour crossover, which explains the A1 result.

## 3. Unknown error types with five seeds

**Question (review).** §7.6 rested on one seed with wide intervals.

**Run.** `results/runs/20261003-154345_real_kssl3_mismatch5_d54e40c`, seeds 11–15 (seed 11 repeats the
original run), 4 settings each, config identical to `real_kssl3_mismatch.yaml` except name and seeds.
The run record says `status: exploratory` because the new config file was not yet committed when the
run started; the full config is stored in the run folder.

**Reproducibility check.** Seed 11 reproduced the original one-seed run exactly (all 48 rows of
`metrics_by_setting.csv`, maximum absolute difference 0.0).

**Findings** (`results/exploratory/20261003-154345_real_kssl3_mismatch5_d54e40c/swap_value_ablation.csv`).
EdaphNet minus B5 (B5 was the best baseline in every cell), 5 seeds:

| Witness, ordering | All errors | Swaps | Value errors | (1 seed, for comparison: swaps / values) |
|---|---|---|---|---|
| Colour ΔE2, random | +0.027 [+0.009, +0.047] | **+0.103 [+0.069, +0.137]** | **−0.057 [−0.078, −0.036]** | +0.100 [+0.021, +0.174] / −0.068 [−0.098, −0.036] |
| Colour ΔE2, clustered | +0.018 [−0.012, +0.049] | +0.105 [+0.062, +0.147] | −0.078 [−0.105, −0.050] | +0.085 [−0.014, +0.278] / −0.116 [−0.160, −0.073] |
| Spectrometer, random | +0.057 [+0.040, +0.073] | +0.147 [+0.118, +0.176] | −0.032 [−0.056, −0.009] | +0.132 [+0.063, +0.230] / −0.010 [−0.059, +0.035] |
| Spectrometer, clustered | +0.110 [+0.082, +0.137] | +0.230 [+0.196, +0.258] | −0.030 [−0.056, −0.003] | +0.256 [+0.189, +0.307] / −0.060 [−0.112, −0.019] |

By unknown error type (colour ΔE2, random; Full vs B5): ×100 0.99 vs 0.91; gross ×4–8 0.40 vs 0.61;
neighbour copy 0.42 vs 0.49; dropped digit 0.14 vs 0.16.

- The one-seed pattern holds with intervals 2–3× narrower: more swaps found, fewer wrong values.
- With unknown error types and colour, the overall difference is small but positive in random
  batches (+0.027, interval above 0), unlike the registered test with known types (+0.014,
  interval including 0). Not a registered result.
- Large unknown errors are found by all methods; subtle ones (dropped digit, neighbour copy) are
  hard for all; gross ×4–8 errors again favour B5 (consistent with §1).

**Record labelling error found.** `scripts/run_real.py` wrote the hard-coded label
"REAL DATA + INJECTED ERRORS (ICRAF-ISRIC)" into `metrics.json` for every run, including all KSSL
runs. Only this label is wrong; the dataset used is recorded correctly in each run's `config.json`
(`"tag": "kssl3"`) and in the folder name. The script now derives the label from the config tag;
the earlier run records were left unchanged.

## 4. Figures and text

- Figure 5 (pool size; file `fig4_pool_size.png`): FDR labels no longer overlap (label placement
  depends on which line is higher; near-zero points stack labels above).
- New Figure 1 (`fig0_method.png`): method diagram.
- Abstract: exploratory results marked; "needs thousands of distinct verified reports" replaced by
  the mechanical statement (BH over m reports can reject only when at least m / (q(N + 1)) reports
  reach the p-value floor 1/(N + 1): ≈ 5 for the registered pool, < 1 for one batch); B5's power
  advantage with colour stated.
- Attribution made a main result (§7.8), with the caveat that it was evaluable only with a spectrometer.

## 5. Not done (needs the student or supervisor)

Formal Scopus/WoS search and [verify] citations; Zenodo DOI; patent decision (repository was public
for a period); AI-assistance statement wording; supervisor sign-off; LUCAS request.
