# Step 8 — Paper Skeleton (v2, updated 2026-10-01)

> **What changed in v2:** the v1 headline ("phone photo verification at controlled FDR") failed
> (doc 17), and the step-5 FDR failure was traced mainly to my calibration-design error (D-017).
> The paper now follows **amendment v2** (doc 18): re-test ranking (A1), shift-aware calibration
> (A2), attribution (A3), detectability (A4). The v1 sections below remain as the base; the
> table here overrides where they differ.

## v2 working title (pending the KSSL verdict)

- **If A1 passes:** *Which soil test reports should a laboratory re-test? Joint batch-level
  detection and explanation of sample swaps and value errors using an independent sample
  witness*
- **If A1 fails:** *When is a cheap witness enough? Detectability of errors in soil laboratory
  reports, and why calibrated error control needs thousands of verified reports*

## v2 claim → evidence

| Claim | Evidence | Status |
|---|---|---|
| Re-test ranking beats existing methods with a colour witness (A1) | KSSL pre-registered run; LUCAS confirmation | ⏳ running |
| The advantage comes from swap detection; value errors need a dedicated checker | doc 19 (exploratory), KSSL A4 | partly (exploratory) |
| Attribution beats rule-based repair (A3) | T0 + ICRAF (89–98% vs 37–51%) + KSSL | partly |
| Calibrated FDR control needs many distinct verified calibration reports; sample reuse invalidates it | diagnostic runs `20261001-233051`, `20261001-233621` (D-016/D-017) | ✅ (diagnostic) |
| Shift-aware calibration (weighted / Mondrian) restores FDR (A2) | KSSL run | ⏳ |
| Colour witness strength depends strongly on the property set and dataset (OC R² 0.37 ICRAF vs 0.72 KSSL) | docs 14, KSSL ladder | ✅ |
| A phone photo is sufficient in practice | step 6 real photos | ❌ not claimable |
| Weak witnesses suffice (H2); structured swap prior helps (H6) | refuted / not supported | report as negatives |

## v2 extra sections

- **Methodological lesson (Methods/Discussion):** pseudo-replication in calibration sets for
  conformal error control, how it was detected, and the fix (one score per distinct sample).
- **Detectability (Results):** doc 19 tables, replaced by the pre-registered KSSL A4 table.

---

# (v1 skeleton, kept for reference)

**Date:** 2026-09-25 · **Status:** skeleton. Every section is mapped to the document or run that
supplies its content, and marked ✅ ready / ⏳ waiting on a step / ❌ missing.
**Rule:** no number enters the paper unless it comes from a run record (`results/runs/`). All
numbers below that are not yet available are shown as `[STEP 5]` / `[STEP 6]` placeholders,
never estimated.

> Reminder (one line, per project decision): a paper or preprint describing the joint batch
> method publicly discloses it. Decide on any patent filing **before** submitting or posting it.

---

## Working titles (choose after step 5)

- A. *Photographs as independent witnesses: joint detection and attribution of sample swaps and
  value errors in soil laboratory reports with false-discovery-rate control*
- B. *When is a cheap witness enough? A detectability map for verifying soil test reports*
  (if step 5 fails the phone claim, doc 11 §7 decision table)

## Target venues (to confirm scope and fees at submission time)

| Venue | Fit |
|---|---|
| *Computers and Electronics in Agriculture* | method + agricultural application |
| *Geoderma* | only if the soil-science validation (step 6) is strong |
| *Precision Agriculture* / *Smart Agricultural Technology* | applied verification tool |
| *Data in Brief* / *Scientific Data* | separate data paper for the step-6 benchmark (TC4) |

---

## Section map

| # | Section | Content | Source | Status |
|---|---|---|---|---|
| 0 | **Abstract** | problem → method → data → key result → limitation | all | ⏳ STEP 5 |
| 1 | **Introduction** | soil tests drive fertiliser decisions; reports contain swaps and value errors (evidence: 28% of SOC results outside NAPT range, SOIL 2025); no independent check exists for the end user; contributions list | doc 09 §1.6, doc 11 §1 | ✅ draftable |
| 2 | **Related work** | (a) smartphone soil sensing; (b) lab validation against predictions (US 8,352,394); (c) clinical WBIT / delta checks; (d) sample-swap detection in genomics (Broman 2014, Crosscheck); (e) numeric label-error detection (Zhou et al. 2023 / cleanlab); (f) conformal outlier testing and FDR (Bates et al.; Jin & Candès); (g) uncertainty-based rejection in soil spectroscopy (Schmidinger 2026) | doc 09, doc 10 | ⚠️ needs the **formal Scopus/WoS search** (doc 11 §11) |
| 3 | **Problem statement** | batch, witness, swap vs. value error; tasks T-a…T-d | doc 11 §1–2 | ✅ |
| 4 | **Method** | generative model; structured swap set; corruption library; exact joint inference; attribution and correction; conformal p-values + BH; **injection-aware calibration** | doc 11 §2, D-010, `src/edaphnet2/inference.py` | ✅ (update §2.6 with injection-aware calibration) |
| 5 | **Data** | T0 simulation; OSSL/ICRAF-ISRIC (3,473 samples, 553 profiles); witness ladder; licence and audit (including the corrected audit) | docs 12, 14 | ✅ |
| 6 | **Experimental protocol** | baselines B0–B7; metrics (power at FDR 0.10, realised FDR, AUPRC, attribution); profile-grouped splits; pooled BH; seeds; pre-registered hypotheses and decision rules | doc 11 §6–9, configs | ✅ |
| 7 | **Results: simulation** | power vs. witness strength; ablations; attribution; FDR | doc 13, run `20260923-230637_sim_t0_d75f3b6` | ✅ |
| 8 | **Results: real data + injected errors** | same tables on ICRAF-ISRIC across W0–W3 | run `20260925-011337_real_icraf8_2be2820` | ⏳ STEP 5 |
| 9 | **Results: real photos, real errors** | phone-witness R² vs. ladder; ΔE between phones; real duplicate errors | doc 15 | ⏳ STEP 6 |
| 10 | **Detectability map** | detection probability vs. witness informativeness and error size (H5) | T0 + step-5 predictions | ❌ analysis not yet run |
| 11 | **Discussion** | when a photo is enough (and when not); swaps as the main benefit; practical workflow for labs | docs 13, 14 | ⏳ |
| 12 | **Limitations** | synthetic → proxy → real gap; colour from lab spectra is a best case; ICRAF is global reference soils, not Indian farms; injected error mix is assumed; K/Ca/Mg zeros; FDR under dependence is empirical, not guaranteed | docs 12–14, doc 11 §10 | ✅ draftable |
| 13 | **Conclusion** | — | — | ⏳ |
| — | **Reproducibility statement** | code, configs, seeds, run records, data licences, `HOW_TO_RUN.md` | repo | ✅ |
| — | **Supplement** | full metric tables; search log (PRISMA); decision log; negative results (H2, H6) | `results/`, docs | ⏳ |

## Planned figures and tables

| ID | What | Data | Status |
|---|---|---|---|
| Fig 1 | Problem illustration: a lab batch, a swap, a ×10 error, the photo witness | schematic | ❌ to draw |
| Fig 2 | Method overview: hypotheses → joint likelihood → posterior → conformal p-values → BH flags + explanations | schematic | ❌ to draw |
| Fig 3 | Power at FDR 0.10 vs. witness strength, Full vs. best baseline (T0) | doc 13 | ✅ data ready |
| Fig 4 | Witness ladder: R² per property per rung (real data) | doc 14 | ✅ data ready |
| Fig 5 | Power vs. rung on real data, Full vs. baselines | step 5 | ⏳ |
| Fig 6 | Detectability map | H5 analysis | ❌ |
| Tab 1 | Prior work vs. elements E1–E9 | doc 10 §1 | ✅ |
| Tab 2 | Baselines and what they represent | doc 11 §6 | ✅ |
| Tab 3 | Ablations (T0 and real) | doc 13 §3 + step 5 | ⏳ |
| Tab 4 | Attribution accuracy vs. rule-based repair | doc 13 §4 + step 5 | ⏳ |
| Tab 5 | Hypotheses and outcomes (supported / refuted) | doc 13 §6 + step 5 | ⏳ |

## Claim → evidence table (what we may and may not write)

| Claim | Evidence needed | Status |
|---|---|---|
| The joint model beats per-value, swap-only, supervised and cleanlab baselines when the witness is moderately informative | T0 ✅ (MEASURED-SYNTHETIC); real + injected ⏳ | partly |
| A phone photo is a sufficient witness | step 5 (proxy) + step 6 (real photos) | ❌ not yet claimable |
| The gain comes mainly from swap detection | T0 ablation ✅; real ⏳ | partly |
| Error attribution is more accurate than rule-based repair | T0 ✅ (84–92% vs 32–50%); real ⏳ | partly |
| FDR is controlled | **empirical only**; clean calibration fails; injection-aware mostly holds in T0 | ⚠️ must be phrased as empirical; needs a larger run |
| Weak witnesses are enough | **refuted** (H2) | report as a negative result |
| Structured swap prior helps | **not supported** (H6) | report as a negative result |
| A public benchmark with real errors | step 6 | ❌ |

## Open work before submission (checklist)

- [ ] Step 5 complete and analysed; go/no-go decided by the pre-registered rule
- [ ] Larger FDR-validity run (more seeds and pools) for injection-aware calibration
- [ ] Detectability-map analysis (H5)
- [ ] Sensitivity run without K/Ca/Mg (zero-inflated properties)
- [ ] LUCAS confirmation run (after access is granted)
- [ ] Formal literature search logged (`docs/search_log.csv`)
- [ ] Step 6 real photos + real errors (for any "phone" claim)
- [ ] Supervisor sign-off on doc 11 and the final hypotheses table
- [ ] Figures 1–2 drawn; all other figures generated by script from run records
- [ ] Decide on patent filing **before** any public preprint
