# EdaphNet — Research & Patent Charter

**Date:** 2026-09-23 · **Status:** living document, updated at every stage gate
**Companion docs:** `07_development_and_publication_workflow.md` (full plan),
`decision_log.md` (why each choice was made), `invention_log.md` (dated invention records,
**confidential**).

This charter governs how EdaphNet is built. The project exists to produce (1) a publishable,
reproducible research contribution and (2) if and only if one survives a prior-art search, a
patentable technical mechanism. A working product is a by-product.

> This document is engineering guidance, not legal advice. Patentability, filing strategy and
> claim drafting must be decided with a registered patent agent or attorney.

---

## 1. Research-integrity rules

Every number, claim and figure in this repository and in any manuscript carries one evidence tag:

| Tag | Meaning | May appear in the paper as |
|---|---|---|
| **DEMONSTRATED** | Measured on real held-out data; script + artifact + config exist | a result |
| **MEASURED-SYNTHETIC** | Measured, but on injected or simulated data | a controlled / simulation result, labelled as such |
| **ASSUMED** | Design input not measured by us (e.g. `soil_agronomic_prior.json`) | an assumption, with sensitivity analysis |
| **HYPOTHESIS** | Pre-registered, not yet tested | a hypothesis |
| **FUTURE** | Not attempted | future work |

Hard rules:
1. No number is written anywhere unless a script produced it and the run record exists (§7).
2. Negative results are reported. A hypothesis that fails is changed to "refuted", not deleted.
3. A claim is never upgraded (e.g. MEASURED-SYNTHETIC → DEMONSTRATED) without new evidence.
4. Novelty statements always use the hedged form: *"No substantially identical method was
   identified in the sources searched up to <date>."*

---

## 2. Problem definition (v1; freeze after the prior-art search in Stage 1)

**Domain problem.** Soil-test reports drive fertiliser and crop decisions, but they contain
errors: sample mix-ups within a lab batch, unit and decimal errors, transcription or OCR errors,
and analytical outliers. Today the checks are either nothing, fixed range limits, or lab-internal
QC that the end user never sees. Retesting everything is too expensive.

**Research problem.** Can *independent, cheap evidence*, namely a calibrated photograph of the
same soil sample plus agronomic and internal-consistency knowledge, detect, *explain* and
*prioritise* errors in a soil-test report with statistical error control?

**Objectives**
- O1. Estimate image-observable soil properties (colour, texture, SOC) with calibrated,
  coverage-guaranteed intervals.
- O2. Detect erroneous lab values with a controlled false-discovery rate.
- O3. Identify the *type* of error and propose the corrected value where the error is invertible.
- O4. Detect sample swaps within a lab batch.
- O5. Recommend retests that maximise errors caught per unit cost.

**Research questions and measurable outcomes**

| RQ | Question | Primary metric | Success threshold (pre-register) |
|---|---|---|---|
| RQ1 | Which soil properties are predictable from a calibrated phone image beyond a regional baseline? | RMSE, RPIQ, skill vs. baseline | CI of skill excludes 0 on held-out sites |
| RQ2 | Do conformal intervals keep coverage across devices, regions and moisture states? | per-group coverage | within ±0.03 of 1−α |
| RQ3 | Does the image modality improve error detection over lab-only consistency checks? | AUPRC, TPR@5%FPR on **real** errors | paired CI excludes 0 |
| RQ4 | Can error type and corrected value be recovered? | type accuracy; % correctly restored | beats "flag-only" baseline |
| RQ5 | Can batch sample-swaps be detected? | swap detection AUROC; localisation accuracy | beats per-sample thresholding |
| RQ6 | Does decision-impact-weighted retesting beat standard policies? | recall@budget, cost per error found | beats best baseline, CI excludes 0 |

---

## 3. Literature gap map (to be verified in Stage 1; nothing here is yet DEMONSTRATED)

| Method family | What it does | Known or expected limitation | Baseline we must run |
|---|---|---|---|
| Smartphone/RGB soil-property estimation (colour → SOC, texture) | Point predictions from images | Usually random image-level splits, no calibrated uncertainty, no use for *verification* | Colour/texture features + PLSR/RF; fine-tuned CNN; DINOv2 + ridge |
| Vis-NIR / MIR spectroscopy | Accurate property prediction | Needs a spectrometer; not phone-based | Cited as upper bound, not re-implemented (unless data is available) |
| Soil-lab QC / proficiency testing (ring tests, reference samples) | Checks lab accuracy at the *lab* level | Does not check an individual report for an individual farmer; invisible to the user | Range checks; L1 internal-consistency rules |
| Clinical-lab autoverification & **delta checks** | Flags implausible patient results vs. rules and history; detects specimen mix-ups | **Closest methodological prior art.** Uses the patient's own history, not an independent sensing modality | Re-implement a delta-check / multivariate plausibility baseline (L2, L4) |
| Tabular anomaly detection (Isolation Forest, copulas, autoencoders) | Unsupervised outliers | No error *type*, no correction, no FDR guarantee | Isolation Forest; Gaussian copula |
| Cross-modal inconsistency detection (image–text, table–image) | Flags modality conflicts | Not in soil or agriculture; learned consistency, not calibrated tests | Learned stacker on concatenated features |
| Conformal prediction / conformal outlier detection | Valid p-values, coverage | General tool; not applied to soil-report verification | Split-conformal per-property test without fusion |
| Adaptive sampling / VoI in soil science | Where to sample in space | Targets mapping, not retesting of existing reports | Random, rule-only, max-uncertainty retest policies |
| Document AI / OCR for lab reports | Structured extraction | Engineering; errors propagate silently | pdfplumber; OCR + regex |

**Candidate gap (hypothesis):** no prior system uses an *independent imaging modality of the
same physical sample* to perform *statistically controlled, error-type-aware* verification of an
individual soil-test report and to rank retests by *decision impact*. The Stage 1 search exists
to try to refute this.

---

## 4. Component classification: ordinary vs. candidate contribution

This is the most important table for both the paper and a patent. Only the rows marked **C**
or **I** are worth spending research effort on.

- **O** = ordinary implementation (necessary, but not a contribution)
- **C** = candidate research contribution
- **I** = candidate inventive mechanism (possible patent relevance, **subject to prior-art search**)

| Component | Class | Reasoning |
|---|---|---|
| FastAPI backend, PostgreSQL, queue, Docker, frontend | O | Standard engineering |
| OCR / table extraction of reports | O | Standard; only its *error model* matters to us |
| Unit normalisation, range checks, texture sum = 100 | O | Textbook |
| CNN / DINOv2 property regressors | O | Commodity models |
| Conformal intervals (as a tool) | O | Established method |
| Dataset audit + leakage-free re-split (existing C0/A1–A4) | C | Publishable finding; not patentable (a finding, not a mechanism) |
| Paired image–lab dataset with blind-duplicate error ground truth | C | Dataset contribution; not patentable |
| Negative result: pH/NPK not identifiable from RGB under leakage-free evaluation | C | Scientific finding |
| **M1: Error-hypothesis inversion test** | **I** | See §5 |
| **M2: Batch-assignment sample-swap detection** | **I** | See §5 |
| **M3: Capture-uncertainty propagation** | **I (weaker)** | See §5 |
| **M4: Decision-impact-weighted retest selection** | **C / I (weaker)** | See §5 |
| Existing C1 bridge, C2 gates, C3 abstention, C5 contradiction | C (graded in doc 04 / 06) | C5 is the prototype of M1's cross-modal layer |

---

## 5. Candidate core mechanisms (the potential inventive core)

Each is a **HYPOTHESIS** until built and measured, and **unsearched** for prior art until
Stage 1 is complete.

### M1: Error-hypothesis inversion with calibrated cross-modal evidence

For a report value *y* of property *j*, define a finite library of corruption operators
𝒯 = {identity, ×10, ÷10, ppm↔kg/ha, P↔P₂O₅, K↔K₂O, digit transposition, column swap j↔k, …}.
For each T ∈ 𝒯, compute a conformal p-value that T⁻¹(y) is consistent with (a) the image model's
calibrated predictive distribution for the same physical sample, (b) the report's other values
(conditional model), and (c) internal constraints. Report:
- whether *identity* is rejected, at an FDR level controlled across properties and samples;
- which T best restores consistency (the error type);
- the restored value T⁻¹(y) and its interval, as a *suggested correction*, never an automatic one.

*Why it may be inventive:* standard detectors say "anomalous". M1 says "this looks like a
kg/ha value entered as ppm, and the corrected value 18 mg/kg is consistent with the photograph".
It combines a structured corruption library with evidence from a physically independent sensor
and statistical error control.
*Closest expected prior art:* clinical autoverification and delta-check rules; data-cleaning
systems that repair unit errors (e.g. rule-based repair in databases).
*Must be searched before claiming anything.*

### M2: Batch-assignment sample-swap detection

Within a lab batch of *n* samples with *n* images and *n* reports, build a cost matrix
Cₐᵦ = nonconformity of report *b* given image *a*. Solve the optimal assignment (Hungarian
algorithm). A swap is flagged when the optimal assignment differs from the recorded one and a
permutation test on the cost reduction is significant. The output names *which* samples appear
swapped.

*Why it may be inventive:* per-sample checks cannot tell "this value is wrong" from "this
report belongs to a different sample". Assignment-level reasoning can.
*Closest expected prior art:* clinical specimen mix-up detection (multi-analyte, genotype-based);
record-linkage methods.

### M3: Capture-uncertainty propagation

The colour-correction residual from the in-frame reference card (ΔE after fitting), together
with blur and exposure quality scores, is propagated into the image model's interval width
(e.g. as a conformal score normaliser or Mondrian bin). Poor captures automatically widen
intervals and weaken accusations against the lab value.

*Why it matters for patents:* it ties the method to a concrete physical measurement process
(reference target in frame → correction → quantified uncertainty). This is the kind of
*technical effect* that software-related claims generally need, for example in India under
Section 3(k).
*Closest expected prior art:* colour-card calibration apps for soil or urine test strips, and
image-quality-aware medical imaging. Likely crowded, so it is weaker on its own.

### M4: Decision-impact-weighted retest selection

Priority(i, j) = P(error | evidence) × ΔDecision(i, j) / Cost(j). ΔDecision is how much the
downstream fertiliser or crop recommendation would change if the value were replaced by its
image-consistent alternative. Selection is greedy under a budget, with sequential updating after
each retest outcome.

*Why it may be a contribution:* it prioritises errors that *matter to the decision*, not merely
large ones.
*Closest expected prior art:* VoI in experimental design; cost-sensitive active learning;
adaptive soil sampling. Likely a research contribution rather than a strong patent claim.

**Working plan:** M1 + M2 form the core invention candidate. M3 supplies the technical
anchoring, and M4 is the decision layer. Final selection happens only after Stage 1.

---

## 6. Patent-protection rules (read before sharing anything)

1. **Disclosure destroys novelty.** Publishing a paper, preprint, public GitHub repo, poster,
   thesis, demo video or public web demo *before filing* can count as prior art against your own
   application. India offers only narrow grace-period exceptions; Europe has effectively none;
   the US has a 1-year grace period for the inventor's own disclosure. **File first, publish after.**
2. **Keep M1–M4 confidential** until a patent professional has advised on them. The audit paper
   (P1) does *not* disclose M1–M4 and can be published. Check its text before submission.
3. **Keep the repository private.** If any version of this project was ever pushed to a public
   repository or shared publicly, record what, where and when in `invention_log.md` and tell the
   patent professional. It may already be prior art.
4. **Invention records:** each mechanism gets a dated entry in `invention_log.md` (conception
   date, inventors, description, drawings, first reduction to practice, evidence). Git commits
   give a timestamped trail, so the project must be under version control.
5. **Inventorship ≠ authorship.** Inventors are those who conceived the claimed mechanism. Record
   contributions per mechanism, not per paper.
6. **Provisional filing:** India (and the US) allow a provisional application, which secures a
   priority date while experiments continue (complete specification within 12 months). The usual
   sequence is: prior-art search → invention disclosure → provisional filing → then the preprint
   or paper.
7. **Institutional IP:** if this is university work, the institution's IP policy may own or
   co-own the invention. Check before filing.

### Prior-art search plan (Stage 1)

| Source | Use |
|---|---|
| Google Patents, Espacenet, Lens.org, InPASS (Indian Patent Office), USPTO Patent Public Search | Patents and applications |
| Scopus / Web of Science / Google Scholar / arXiv / AGRIS | Papers |
| Commercial systems: soil-testing apps, lab LIMS vendors, clinical autoverification products | Existing products (prior art includes products in public use) |
| CPC classes to scan (verify codes during search) | G01N 33/24 (soil / earth materials analysis), G06T 7/90 (colour analysis in images), G06V (image recognition), G16H 10/40 (lab analysis data, the clinical analogue), G06Q 50/02 (agriculture), G06F 18 (pattern recognition) |
| Query families | per mechanism: synonyms × domain (soil / clinical lab / generic data cleaning) × technique (conformal, assignment, unit-error repair, delta check) |

The output is a prior-art matrix per mechanism: reference, date, jurisdiction, which elements of
M1–M4 it discloses, and the distinguishing features that remain. **Any mechanism fully disclosed
by one reference is dropped from the invention list** (it may remain a paper component if the
application is new).

---

## 7. Experiment tracking standard

Every experiment run writes `results/runs/<YYYYMMDD-HHMMSS>_<experiment>_<shortsha>/` containing:

| File | Content |
|---|---|
| `config.json` | full resolved config (no defaults hidden in code) |
| `provenance.json` | git commit SHA + dirty flag, data manifest hash (MD5 of split files), seed(s), Python and package versions, hardware, start and end time |
| `metrics.json` | all metrics with CIs, **evidence tag**, n, unit of analysis |
| `predictions.csv` | per-sample predictions (so any metric can be recomputed) |
| `log.txt` | stdout/stderr |

Rules: a run on a dirty working tree is marked `exploratory` and cannot feed a paper table.
Paper tables are generated only from run records by a script (`scripts/07_results_table.py`
pattern), never typed by hand. Data files are versioned by hashed manifests (DVC optional).

---

## 8. Performance parameters to measure

| Component | Accuracy / quality | Uncertainty | Systems | Robustness |
|---|---|---|---|---|
| Property regression | RMSE, MAE, R², RPIQ, CCC, bias | coverage, width, CRPS, NLL | inference ms (CPU/phone), params, peak RAM | leave-region-out, leave-device-out, dry/moist, no colour card, blur/JPEG sweeps |
| Soil-class head (existing) | acc, macro-F1, balanced acc, per-class recall | ECE, Brier, NLL, conformal set size | ms, params | same as above |
| Extraction | field P/R/F1, value accuracy, unit accuracy, CER | extraction-confidence calibration | seconds per page | unseen lab format, scan quality |
| Error detection (M1) | AUROC, **AUPRC**, TPR@FPR, realised FDR, type accuracy, correction accuracy | p-value calibration (uniform under null) | ms per report | error prevalence 1–10%, unseen error types |
| Swap detection (M2) | AUROC, localisation accuracy | permutation-test calibration | runtime vs. batch size *n* (scalability: O(n³) Hungarian) | batch size, partial image coverage |
| Retest (M4) | recall@budget, cost per error found, net benefit | — | — | cost-model sensitivity |
| End-to-end API | — | — | p50/p95 latency, throughput, memory | concurrent users |

Statistics: unit of analysis is the physical sample. Use cluster-bootstrap CIs, paired tests
(Wilcoxon; DeLong / bootstrap for AUC; McNemar), Holm correction, ≥3 seeds (5 for headline
numbers).

---

## 9. Ablation matrix (core invention)

| Ablation | Tests the contribution of |
|---|---|
| Full − image evidence (lab-only) | the independent sensor (RQ3, the make-or-break test) |
| Full − internal-consistency layer | lab constraints |
| Full − corruption library (flag-only) | M1's error-type inversion (RQ4) |
| Per-sample checks vs. batch assignment | M2 (RQ5) |
| Fixed-width vs. capture-uncertainty-aware intervals | M3 |
| Magnitude-weighted vs. decision-impact-weighted retest | M4 (RQ6) |
| Cauchy vs. Fisher vs. learned fusion | fusion design |
| Conformal vs. raw-Gaussian p-values | error control |

---

## 10. Documentation → paper / patent mapping

| Paper section | Source document | Patent-specification use |
|---|---|---|
| Abstract, Introduction | §2 of this charter + results | Field of invention, background |
| Related work | Stage 1 literature matrix | Prior art discussion |
| Problem statement | §2 | Problem solved |
| Methodology | §5 + `03_architecture.md` | Detailed description, embodiments |
| System architecture | `07` §A2, API/DB spec | System claims, drawings |
| Experiments, Results | run records → generated tables | Examples / working embodiments |
| Discussion, Limitations | evidence tags, refuted hypotheses | — |
| Conclusion, Future work | FUTURE-tagged items | Alternative embodiments |

---

## 11. Stage card (required at every major stage)

```
STAGE <n>: <name>
1. What we implement      :
2. Why it is necessary    :
3. Potential novelty      : (O / C / I, and why)
4. Compare against        :
5. Experiments            :
6. Data to collect        :
7. Paper documentation    :
8. Patent relevance       : (none / supporting / candidate, and whether a prior-art search is needed)
Evidence status on exit   :
```

### STAGE 0: Research infrastructure and baseline truth (current)

1. **What:** put the project under private git; add the run-record standard (§7); finish the
   held-out evaluation of the soil-class models; recalibrate C5 on real posteriors; open
   `decision_log.md` and `invention_log.md`.
2. **Why:** there are currently no version control and no dated records. Nothing is
   reproducible or attributable, and the soil-class results table is still empty.
3. **Novelty:** none (O). This is infrastructure.
4. **Compare against:** existing 6-backbone table (`results_tables.md`).
5. **Experiments:** E6 (soil class, 644-image test set, ≥3 seeds); C5 recalibration.
6. **Data:** none new.
7. **Paper:** Methods → reproducibility statement; Results → the soil-class table for P1.
8. **Patent:** supporting only. Git history and the invention log give the dated record needed
   later.

### STAGE 1: Prior-art search and problem freeze (next)

1. **What:** the systematic literature + patent search from §6; per-mechanism prior-art matrix;
   freeze §2 and select the core mechanism(s).
2. **Why:** building M1–M4 before this risks reinventing an existing solution.
3. **Novelty:** determines it.
4. **Compare against:** everything in §3.
5. **Experiments:** none. Optionally, a small synthetic prototype of M1 to make the idea
   concrete (tag MEASURED-SYNTHETIC).
6. **Data:** start lab contacts for the paired set (long lead time).
7. **Paper:** Related-work draft; gap statement.
8. **Patent:** critical. Output is a go / narrow / drop decision per mechanism, and an invention
   disclosure for any survivor to take to a patent professional.
