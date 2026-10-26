# EdaphNet v2 — Prior-Art Review (v0) and Research Design

**Date:** 2026-09-23 · **Status:** v0 from a first web search. Every item marked *(verify)*
must be confirmed from the full text before it is cited in a paper.
**Supersedes:** the soil-type → crop-recommendation framing as the *core* research. That work
stays as a possible separate audit paper (doc 04 §E).

---

## 1. What already exists (so we do not rebuild it)

### 1.1 Predicting soil properties from phone images: **crowded**
- SOC/SOM from smartphone images: reflectance images + perturbation, illumination studies,
  moisture effects, deep metric learning (500 samples), smartphone + topography in the
  Indo-Gangetic Plains [1–4].
- Texture from smartphone images with a dark capture chamber [5]; EC from spectroscopy +
  smartphone images [6]; free Fe-oxides from smartphone colour [7].
- pH/N/P/K "from images" papers exist [8], mostly small and colorimetric (reagent-based) or
  weakly validated.
- Munsell colour from a phone with an in-frame reference card is **deployed in a free app**
  (LandPKS Soil ID) [9].
- Known open problems they report: device-to-device inconsistency, illumination, and
  generalisation beyond controlled capture [1, 2].

**Conclusion:** image → property prediction, colour calibration with a reference card, and
CNN vs. handcrafted comparisons are **not contributions**. They are tools we use.

### 1.2 Checking a lab value against a predicted value: **exists, in other domains**
- **US 8,352,394 B2** (Rockwell Automation, priority 2008): validates lab data by predicting the
  property from other lab and sensor measurements and checking whether the lab value is inside
  an acceptable range. Domain: process manufacturing (paper). No images, no error typing, no
  batch/swap reasoning, no statistical error control [10].
- Clinical labs: autoverification and delta checks. **ML multi-analyte delta checks detect
  "wrong blood in tube" (specimen mix-up)** better than univariate rules and staff review
  [11, 12]. These use the *patient's previous results*, not an independent measurement of the
  same specimen.
- **US 7,783,582:** Bayesian-network detection of clinical-lab errors trained with *synthetic
  errors* [13] *(verify claims)*.
- Clinical unit-of-measure harmonisation and correction frameworks; decimal-point and
  digit-transposition detection patents [14] *(verify)*.

**Conclusion:** "flag a lab value that disagrees with a prediction", "detect unit/decimal
errors" and "train on injected errors" are **not novel ideas by themselves**.

### 1.3 Detecting sample swaps by matching two data types: **exists (genomics)**
- Broman et al. 2014: predict genotype from expression data, detect mismatched samples, **find
  the correct partner and correct the swap**. They observed **off-by-one / off-by-two plate
  errors** (systematic pipetting shifts). Implemented in R/lineup [15].
- CrosscheckFingerprints (ENCODE): swap detection via genotype concordance [16].
- Both rely on a **strong witness** (genotype is near-deterministic).

**Conclusion:** cross-modal matching for swap detection is established. Applying it to soil
is only a transfer, unless the *weak-witness* problem (§2) is solved.

### 1.4 Soil-lab QC with an independent sensor: **partially exists (spectroscopy)**
- MIR spectra used to identify analytical outliers and "inconsistencies in wet laboratory
  analyses" at USDA KSSL (Seybold et al. 2019, SSSAJ) [17] *(full text blocked; verify exact
  claims)*.
- Spectra-based internal QC with unsupervised random forests to cluster and flag samples [18]
  *(verify source)*.
- **Schmidinger et al., June 2026:** uncertainty-guided *rejection* of Vis-NIR predictions,
  sending uncertain samples back to conventional lab analysis (TabPFN/TabICL foundation
  models) [19]. The direction is the **reverse** of ours: it verifies the *prediction*, not the
  *lab report*.
- Conformal prediction for soil spectral models (MC-CP, SOIL 2025) [20].

**Conclusion:** "sensor checks lab" exists with **strong, expensive witnesses** (MIR/Vis-NIR
spectrometers, lab-internal). Uncertainty-aware soil models with conformal intervals exist.

### 1.5 Existing practice: **LUCAS photographs soil samples for lab checking**
- In the EU LUCAS topsoil survey, "a photograph of each site and soil sample is taken through a
  standard protocol that allows the samples to be checked in the laboratory" [21]. This is
  **manual, prior practice** of using photos to verify samples. It is prior art for the *idea*.
  It is also potentially a **large paired dataset** (LUCAS 2015: 21,859 samples with clay,
  silt, sand, pH, OC, CaCO₃, N, P, K, EC) *(verify that soil-sample photos, not just
  point/landscape photos, are downloadable, and their licence)*.

### 1.6 The problem is real
- Across 8 service labs, **28% of SOC observations fell outside the NAPT acceptable range**
  (8% TC, 15% SIC); one lab's inorganic-carbon result was 118× the others' [22].
- ~1 in 1,000 clinical specimens are WBIT errors [11]. The soil-lab equivalent rate is
  **unknown**, and measuring it is itself a contribution.

---

## 2. The gap that survives the search (hypothesis, not yet claimed)

Every verification system found uses a **strong witness**: genotype, MIR spectra, patient
history or process sensors. A phone photograph is a **weak witness**. It is informative for
colour, SOC and texture, and nearly uninformative for P, K and micronutrients.

> **Research question:** Can a *weak, cheap, independent witness* (a smartphone image of the
> same physical sample), combined with lab-internal constraints, provide **statistically valid**
> detection, **attribution** and **correction** of errors in soil laboratory reports, and under
> what conditions is it enough?

Why this is different from "combining techniques":

| Prior work | What it lacks that we target |
|---|---|
| Rockwell US 8,352,394 | per-value range check only: no error-type attribution, no batch/permutation reasoning, no FDR guarantee, strong process sensors |
| Clinical WBIT ML | patient history as witness; supervised on synthetic swaps; no independent sensing of the specimen |
| Broman / lineup | strong genetic witness; swaps only; no value-corruption types |
| MIR / Vis-NIR QC | expensive lab spectrometer; flags outliers, does not attribute error type or cover report-transcription errors |
| Schmidinger 2026 | verifies predictions, not lab reports |
| LUCAS photo protocol | manual, qualitative |

### Candidate technical contributions (to validate)

**TC1: Joint batch error model with a weak witness.** For a lab batch of *n* samples, jointly
infer:
- a latent **permutation** π (swaps), with a *structured prior* concentrated on
  physically plausible errors: adjacent-position swaps and off-by-k tray shifts (the pattern
  Broman observed in plates);
- per-cell **corruption types** from a library (×10, ÷10, unit confusion, P↔P₂O₅, K↔K₂O,
  digit transposition, column swap, gross analytical error);
- latent true values.

The likelihood combines (a) the calibrated image-model predictive distribution, (b)
internal-consistency constraints, and (c) regional multivariate priors. The key idea is that
**pooling weak evidence across properties and across the batch structure** can yield power that
no per-value check has. *Hypothesis H-TC1:* the structured joint model detects swaps and value
errors with higher power at equal FDR than per-value and swap-only baselines.

**TC2: Finite-sample error control.** Turn the posterior scores into conformal p-values
calibrated on clean batches, then select flags with FDR control (conformal selection
framework, e.g. Jin & Candès 2023 *(verify and cite as a tool, not a contribution)*). The
contribution is the *application to structured, batch-level lab errors*, and showing that
validity holds empirically under realistic shifts.

**TC3: Detectability map (scientific result).** Characterise, empirically and analytically,
*which error types are detectable at what rate* as a function of witness informativeness
(per-property image R² or mutual information), error magnitude, batch size and soil diversity.
Example: "swaps between soils differing by ≥ X in Munsell value are detectable with power ≥ 0.8
at FDR 0.05; P errors below ×3 are not." This is a result, not a technique, and it holds even
if TC1's gain is small.

**TC4: Benchmark and error model.** A paired image + lab dataset with **real** errors (blind
duplicates / lab QC records) and an empirically grounded error-injection model. It would be
the first benchmark for soil lab-report verification *(verify no such benchmark exists)*.

**Explicitly NOT contributions:** the image regressor, colour calibration, OCR, unit
conversion, conformal intervals per se, the backend.

---

## 3. Baselines we must beat

| ID | Baseline | Represents |
|---|---|---|
| B0 | Fixed agronomic range checks | current practice |
| B1 | Internal-consistency rules (texture sum, CEC bounds, OM/OC) | lab QC rules |
| B2 | Lab-only multivariate outlier model (Isolation Forest, Gaussian copula, conditional GBM residuals) | multi-analyte delta check without history |
| B3 | Per-value predicted-interval check using the image model | Rockwell-style validation |
| B4 | Swap-only cross-modal matching (Hungarian on image–report costs, no structure prior) | Broman/lineup transferred |
| B5 | Supervised classifier on injected errors (GBM on features of B1–B4) | clinical WBIT-ML style |
| B6 | Unit/decimal rule-based repair (range test on candidate conversions) | clinical unit harmonisation |
| Full | TC1 + TC2 | ours |

## 4. Metrics

Detection: AUROC, **AUPRC**, power at target FDR, **realised FDR**, TPR@FPR. Attribution:
error-type accuracy (confusion matrix). Correction: % errors restored to within lab
repeatability. Swaps: detection AUROC, exact localisation accuracy. Witness: per-property RMSE,
R², RPIQ, conformal coverage per group. Cost: runtime vs. batch size *n* and
corruption-library size. Statistics: cluster bootstrap over batches and samples, paired tests,
Holm correction, ≥5 seeds for simulations.

## 5. Ablations

Remove image witness (→ B1+B2 level); remove structure prior (uniform permutations); remove
corruption library (flag-only); per-value instead of joint inference; conformal vs. raw
posterior thresholds; witness quality degraded (colour card off, blur); batch size 5–96.

## 6. Data strategy (cheapest first)

| Tier | Data | Validates | Evidence tag |
|---|---|---|---|
| T0 | Pure simulation with controllable witness informativeness | method mechanics, TC3 curves | MEASURED-SYNTHETIC |
| T1 | **LUCAS** real lab values (+ photos if usable) and **Photogranulometry** (images + PSD) with injected errors | TC1/TC2 under real data distributions | MEASURED-SYNTHETIC (errors) on real data |
| T2 | Own paired collection: ≥200 samples, controlled photos, ≥20–30% blind duplicates, possibly a partner lab's historical QC/re-test records | TC1–TC4 on **real** errors | DEMONSTRATED |

**Go/no-go after T1:** if Full does not beat B2 + B4 at equal FDR with a CI excluding 0, the
weak-witness verification claim is dropped. TC3 (detectability map) can still be published as
a characterisation study.

---

## 7. Open prior-art checks before freezing the problem

1. Full text of Seybold 2019 [17] and the RF-proximity QC paper [18]: do they attribute error
   types or detect swaps?
2. LUCAS: are soil-sample photos public? What do they show (bare sample vs. ground cover)?
   Licence.
3. Conformal selection / FDR literature (Jin & Candès 2023 and follow-ups): has anyone applied
   it to lab or measurement-error detection?
4. Patent databases (Espacenet, Google Patents, InPASS): queries "soil" × {verification,
   validation, mix-up, swap, image} and "laboratory result" × "image of specimen".
5. Commercial: soil-lab LIMS vendors and ag-tech apps that cross-check reports.
6. Any benchmark for soil lab-report error detection.

---

## Sources (first search, 2026-09-23)

1. Soil organic matter prediction using smartphone-captured digital images (reflectance image, perturbation). https://www.sciencedirect.com/science/article/abs/pii/S1537511021001422
2. Optimizing image-based SOM prediction: illumination type and intensity. https://www.sciencedirect.com/science/article/pii/S2772375525001558
3. Deep metric learning for SOM prediction from smartphone images. https://www.sciencedirect.com/science/article/pii/S0168169925008348
4. Smartphone imagery + topography for SOC, Indo-Gangetic Plains. https://www.sciencedirect.com/science/article/abs/pii/S0168169925013857
5. Predicting soil texture from smartphone-captured digital images. https://www.sciencedirect.com/science/article/abs/pii/S0016706120310958
6. Predicting soil EC using spectroscopy and smartphone images. https://www.sciencedirect.com/science/article/abs/pii/S0341816223004101
7. Smartphone soil colour + ML for free iron oxide. https://link.springer.com/article/10.1007/s11119-025-10270-0
8. Prediction of soil pH using smartphone image processing. https://www.researchgate.net/publication/332968910
9. LandPKS: smartphone camera vs. Munsell charts. https://landpotential.org/knowledge/measurement-soil-color-comparison-smartphone-camera-munsell-color-charts
10. US 8,352,394 B2, Validation of laboratory test data based on predicted values. https://patents.google.com/patent/US8352394B2/en
11. ML-based multianalyte delta checks for WBIT errors (AJCP). https://pubmed.ncbi.nlm.nih.gov/30169595/
12. ML model for routine detection of WBIT in CBC (Clinical Chemistry). https://dx.doi.org/10.1093/clinchem/hvad100
13. US 7,783,582, Bayesian-network detection of clinical-lab errors using synthetic errors. https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7783582
14. Automated standardisation and harmonisation of laboratory units. https://www.sciencedirect.com/science/article/pii/S138650562500348X
15. Broman et al. 2014, Identification and correction of sample mix-ups in expression genetic data. https://arxiv.org/abs/1402.2633
16. Detecting sample swaps in diverse NGS data types (Crosscheck). https://www.nature.com/articles/s41467-020-17453-5
17. Seybold et al. 2019, Application of MIR spectroscopy in soil survey (SSSAJ). https://acsess.onlinelibrary.wiley.com/doi/full/10.2136/sssaj2019.06.0205
18. Bridging the gap between soil spectroscopy and traditional laboratory. https://www.sciencedirect.com/science/article/abs/pii/S0016706122003366
19. Schmidinger et al. 2026, Rejections based on predictive uncertainty enable reliable routine soil spectroscopy. https://arxiv.org/abs/2606.21179
20. Monte Carlo conformal prediction for deep-learning soil spectral models (SOIL 2025). https://soil.copernicus.org/articles/11/553/2025/
21. LUCAS Soil review / topsoil module description. https://bsssjournals.onlinelibrary.wiley.com/doi/10.1111/ejss.12499 ; LUCAS 2018 topsoil: https://esdac.jrc.ec.europa.eu/content/lucas-2018-topsoil-data
22. Large errors in soil carbon measurements attributed to inconsistent sample processing (SOIL 2025). https://soil.copernicus.org/articles/11/17/2025/
