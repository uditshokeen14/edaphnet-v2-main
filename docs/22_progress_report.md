# EdaphNet — Progress Report

**Date:** 2 October 2026 · **Project folder:** `edaphnet-v2` · **Repository:** https://github.com/Sudeep-Sharma1/edaphnet-v2
**Purpose of this report:** a complete, plain-language account of what has been done, what was
found (including what failed), and what remains. Every number below comes from a committed run
record or document, named in brackets.

---

## 1. The project in one paragraph

Soil test reports are sometimes wrong: a sample is swapped with another one (the farmer gets
someone else's results), or a single value is corrupted (a ×10 decimal slip, a unit mix-up, swapped
digits or columns). Nobody checks this for the end user, and re-testing everything is expensive.
EdaphNet asks whether a cheap, independent observation of the same soil sample (a **witness**,
mainly its colour as a phone camera would see it) can tell a laboratory **which reports to re-test**
and **what went wrong**. The core method is a joint model that checks a whole laboratory batch at
once, considering possible swaps and a library of error types together.

## 2. How the research question evolved

| Version | Claim | Outcome |
|---|---|---|
| v1 (doc 11) | A phone-grade photo lets us flag erroneous reports with a guaranteed false-alarm rate (FDR 10%) | **Failed** (step 5, doc 17), partly because of a calibration-design error of mine (D-016/D-017) |
| v2 (doc 18, pre-registered) | With a 5% re-test budget, the method finds more errors than the best existing method, with a phone-grade colour witness | **Failed** on new data (KSSL, doc 21) |
| Current framing | When is a cheap witness enough? Detectability of report errors, calibration requirements, error attribution | Supported by the evidence so far (docs 13, 14, 19, 21) |

Both main claims were written down **before** the tests that decided them (pre-registration), and
their failures are reported, not hidden.

## 3. Work completed, step by step

| Step | What was done | Output |
|---|---|---|
| 1. Prior-art search | Papers, patents, products. Most single ideas already exist (phone soil sensing, validating lab values against predictions, swap detection in genomics, cleanlab, conformal FDR). Remaining gap: joint swap + value-error checking with a cheap witness, a detectability map, a benchmark | docs 09, 10 |
| 2. Problem specification | Formal model, 9 error types, structured swap patterns, 7 baselines + rule-based repair, 6 hypotheses with pass/fail rules fixed in advance | doc 11 |
| 3. Simulation study | Method, baselines and statistics built and tested on synthetic soils (30 settings) | doc 13 |
| 4a. Real-data audit | Open Soil Spectral Library downloaded, licences checked, data audited (with a corrected counting mistake) | doc 12 |
| 4b. Witness ladder | Soil colour computed from real spectra; measured how much colour reveals about each property | doc 14 |
| 5. Go/no-go on real data | ICRAF-ISRIC (3,473 samples), 42 settings | doc 17 |
| 5b. Diagnosis | Found the cause of the false-alarm failure (calibration-sample reuse) | D-016, D-017 |
| 5c. Pre-registered test on new data | KSSL (19,746 samples), 50 settings, automatic verdict script | docs 18, 21 |
| 6 (preparation) | Data-collection protocol, Excel templates, photo-processing module, colour model | doc 15, `templates/`, `phone.py` |
| 8 (start) | Paper skeleton and draft (Introduction, Related work, Method, Data, Protocol) | doc 16, `docs/paper/draft_v0.md` |
| Demos | Command-line demo, presentation page, live demo with photo + report | `scripts/demo.py`, `demo_site/` |

## 4. What was built

**Research code** (`src/edaphnet2/`, Python):

| Module | Function |
|---|---|
| `inference.py` | The method: joint batch inference over swap hypotheses × error types; score, explanation, correction |
| `operators.py`, `swaps.py` | Error library (decimal, unit, digit transposition, column swap, gross error) and swap patterns |
| `witness.py`, `real_data.py`, `space.py` | Witness models, real-data transforms, colour from spectra, property sets |
| `baselines.py` | 7 comparison methods incl. cleanlab (Zhou et al. 2023) |
| `conformal.py`, `metrics.py` | False-alarm control (conformal p-values, BH), re-test-budget metric, weighted / per-group calibration |
| `phone.py` | Photo processing: colour-card correction, true soil colour, blur / exposure / texture |
| `tracking.py` | Run records (config, code version, environment) for reproducibility |

**Scripts:** experiment runners (synthetic, real, resumable), data builders, analysis (verdicts,
detectability), photo processing, colour model training, demos.
**Tests:** 23 automatic tests (plus one slow end-to-end resume test), all passing.

## 5. Data used

| Dataset | Samples | Properties | Licence | Role |
|---|---|---|---|---|
| Synthetic (T0) | generated | 8 | — | testing the mechanism |
| ICRAF-ISRIC (OSSL) | 3,473 (553 profiles) | pH, OC, clay, sand, CEC, K, Ca, Mg | CC-BY | step 5 |
| KSSL Vis-NIR (OSSL) | 19,746 (6,999 locations) | OC, N, total C | CC-BY | pre-registered test |
| LUCAS | ~40,000 | 10 properties | needs access request | not used yet |

## 6. Key results

### 6.1 Simulation (doc 13, synthetic)
The method beats all baselines **only when the witness is moderately informative** (e.g. +20 to
+25 points in errors found at 10% false alarms when colour explains ~66% of organic carbon), not
with a weak witness. Its gain comes almost entirely from **finding swaps**.

### 6.2 What colour reveals on real soils (docs 14, 21)

| | Organic C | Nitrogen | pH | Clay / sand / CEC / K |
|---|---|---|---|---|
| ICRAF colour (perfect / good phone) | 0.37 / 0.35 | — | 0.27 / 0.15 | ≤ 0.16 / ≤ 0.07 |
| KSSL colour (perfect / good phone) | 0.72 / 0.70 | 0.55 / 0.54 | — | — |
| Spectrometer | 0.60–0.90 | 0.73 | 0.62 | 0.39–0.66 |

(R², share of variation explained on unseen locations.) Colour mainly knows **carbon**.

### 6.3 Pre-registered test on KSSL (doc 21): errors found when re-testing the top 5%

| Witness | EdaphNet | Best existing method | Difference [95% CI] |
|---|---|---|---|
| None | 0.24 | 0.27 | −0.03 |
| Colour, perfect | 0.42 | 0.42 | **+0.00 [−0.02, 0.02]** |
| Colour, good phone | 0.41 | 0.40 | **+0.01 [−0.01, 0.04]** |
| Spectrometer | **0.60** | 0.51 | **+0.09 [0.07, 0.11]** |

**Verdict:** A1 (main claim) **failed**; A1-c, A2 (false alarms ≤ 12%) and A3 (attribution)
**passed**. Note on A2: with a colour witness the method flagged almost nothing (power ≈ 0), so A2 passed by
staying silent at those settings; only the spectrometer setting combined low false alarms with real power.

### 6.4 Other findings
- **Error explanation:** right error type 89–98% (ICRAF) and 97–100% (KSSL, spectrometer), vs
  24–51% for rule-based repair.
- **Which errors can be found (doc 19):** with a colour witness, swaps go from ~3% to ~40–55% found;
  single wrong values are found better by simple checks; digit transpositions and moderate
  analytical errors stay hard for every method.
- **Calibration lesson (D-017):** reliable false-alarm control needs **thousands of distinct
  verified reports**; reusing calibration samples silently breaks it.

## 7. Mistakes made and corrected (kept on record)

| Mistake | Correction |
|---|---|
| Data audit counted empty spectrum rows (23,852 instead of 49 usable) | Recounted; switched to ICRAF-ISRIC (doc 12 §7) |
| "Weak witness is enough" (H2) | Refuted by simulation; claim reframed (D-010) |
| Experiment runner ran out of memory; seeds not reproducible | Lean runner, stable seeds, resume feature with equivalence test (D-012) |
| Calibration reused samples (pseudo-replication), inflating false alarms | Diagnosed on data not used for testing; fixed by one score per sample (D-016, D-017) |

## 8. Demos and frontend

| Demo | How to run | Shows |
|---|---|---|
| Command line | `python scripts/demo.py` (`--witness W3`) | one batch, planted swap + ×10 error, re-test list |
| Presentation page | open `demo_site/index.html` | problem, method, interactive batches, charts, verdicts (works offline) |
| Live demo | `python scripts/serve_demo.py` → http://localhost:8000 | photo → colour correction → prediction → report check → batch ranking, running the real model |

The example photos in the demos are **simulated** from real soils' lab-measured colours; no real
photos have been collected yet.

## 9. Reproducibility

Every experiment writes a run record (configuration, code version, environment, results). Seeds
are fixed and runs can be resumed with identical results. The pass/fail rules and the verdict
script were committed before the data they judge. Data licences and attribution are in the README.

## 10. What remains

**Needs decisions or actions from you / your supervisor**
1. Supervisor review of the plan and the new framing (docs 11, 18, 21).
2. LUCAS access request (free): https://esdac.jrc.ec.europa.eu/content/lucas2015-topsoil-data
3. Formal literature search in Scopus / Web of Science (log in `docs/search_log.csv`).
4. Step-6 decisions: budget, soil types and regions, laboratory, photo protocol (doc 15 §11).

**Research work**
5. Combined re-test policy (EdaphNet for swaps + a value checker), pre-registered and tested on new
   data (draft: doc 20).
6. Real phone photos + lab reports of Indian soils with blind duplicates (doc 15): the only way to
   test real phones, which also capture texture.
7. LUCAS confirmation run.
8. Paper: Results, Discussion, Abstract; journal choice.

**Engineering (only if the research supports it)**
9. A web backend and app for laboratories (step 7).

## 11. Honest bottom line

The method works well when the witness is strong (spectrometer): it finds more errors than existing
methods and explains them correctly. A phone-grade colour photo, at least as approximated from
laboratory spectra, is **not enough** to beat the best existing method on average. The publishable
contribution is therefore the careful, pre-registered study of **when a cheap witness is enough**,
together with the calibration lesson and the explanation accuracy, unless real phone photos (step 6)
or the combined policy change that picture.
