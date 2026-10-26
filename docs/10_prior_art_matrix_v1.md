# Prior-Art Matrix v1 (Step 1 deliverable)

**Date:** 2026-09-23 · **Method:** targeted web search of papers, Google Patents and vendor
pages (not yet a full systematic review in Scopus/WoS). Builds on doc 09.
**Legend:** ● fully covers · ◐ partially covers · ○ does not cover · ? unverified

## 1. Matrix: what each prior work already covers

Columns are the elements of our candidate method (doc 09 §2):
**E1** flag a lab value using a prediction from other information · **E2** independent sensing
of the *same physical specimen* · **E3** the sensor is *weak / cheap* (phone-grade) · **E4**
attributes the *error type* (unit, decimal, transposition…) · **E5** proposes a *corrected
value* · **E6** detects *sample swaps* · **E7** *joint* swap + value-error inference over a
batch with a structured (tray/plate) prior · **E8** finite-sample *FDR* guarantee on flags ·
**E9** soil domain.

| # | Work | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | E9 |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | US 8,352,394 B2, Rockwell 2008 (lab validation via predicted values) | ● | ◐ process sensors | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| P2 | Zhou, Mueller et al. 2023, *Detecting errors in a numerical response via any regression model* (arXiv 2305.16583) | ● | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| P3 | Bates et al. 2023, *Testing for outliers with conformal p-values* | ◐ | ○ | ○ | ○ | ○ | ○ | ○ | ● | ○ |
| P4 | Jin & Candès 2023, *Selection by prediction with conformal p-values* (JMLR) | ◐ | ○ | ○ | ○ | ○ | ○ | ○ | ● | ○ |
| P5 | Peng et al. 2025, *Conformal prediction with cellwise outliers* | ◐ cell level | ○ | ○ | ○ | ◐ imputes | ○ | ○ | ◐ coverage | ○ |
| P6 | Clinical WBIT ML (multi-analyte delta checks; AJCP 2018, Clin Chem 2023) | ● | ○ uses history | ○ | ○ | ○ | ● | ○ | ○ | ○ |
| P7 | US 7,783,582 (Bayesian-net clinical-lab error detection with synthetic errors) | ● | ○ | ○ | ◐ ? | ? | ? | ○ | ○ | ○ |
| P8 | Clinical unit harmonisation / correction framework (2025) | ◐ range | ○ | ○ | ● units | ● | ○ | ○ | ○ | ○ |
| P9 | Broman et al. 2014 / R/lineup (expression ↔ genotype mix-ups) | ● | ● | ○ strong | ○ | ○ | ● + correction | ◐ observed plate shifts, no prior in model | ○ | ○ |
| P10 | Crosscheck (ENCODE), probabilistic multi-omics matching (2019) | ● | ● | ○ strong | ○ | ○ | ● | ○ | ○ | ○ |
| P11 | MIR spectra flag wet-lab inconsistencies (Seybold 2019, KSSL) | ● | ● | ○ lab spectrometer | ? | ? | ? | ○ | ○ | ● |
| P12 | Schmidinger et al. 2026 (uncertainty-based rejection, Vis-NIR) | ◐ reverse direction | ● | ○ | ○ | ○ | ○ | ○ | ○ | ● |
| P13 | LUCAS topsoil: photo of each sample "so samples can be checked in the laboratory" | ◐ manual | ● | ● | ○ | ○ | ◐ manual | ○ | ○ | ● |
| P14 | Soil LIMS vendors (rule validation, barcodes/RFID) | ◐ rules | ○ | ○ | ○ | ○ | ◐ prevention, not detection | ○ | ○ | ● |
| P15 | Smartphone soil-property papers (SOC, texture, EC, Fe, Munsell; LandPKS) | ○ | ● | ● | ○ | ○ | ○ | ○ | ○ | ● |
| P16 | CN108732129B (farmland soil components from images) | ◐ reverse: lab corrects image | ● | ? | ○ | ○ | ○ | ○ | ○ | ● |

**No soil lab-error benchmark was found.** LimeSoDa (31 soil datasets) and REIN
(data-cleaning benchmark) are the nearest, and neither has soil lab errors.

## 2. What this changes in our novelty claim

| Element | Status after v1 | Consequence |
|---|---|---|
| E1 flag via prediction | **Prior art** (P1, P2, P6) | Tool, not a contribution. P2 becomes a **required baseline (B7)** |
| E8 FDR via conformal p-values | **Prior art** (P3, P4) | Tool; cite. Our only claim is showing validity holds under *structured* lab errors |
| E6 swap detection by cross-modal matching | **Prior art** (P9, P10), strong witnesses | Transfer only. Baseline B4 = P9-style matching |
| E4/E5 error type + correction | Partial prior art (P8 units, P7 ?) | Only novel as part of E7 with an independent witness |
| E2+E3+E9 weak independent soil witness | Manual prior practice (P13); prediction-only papers (P15) | **Open** for *automated, statistical* verification |
| **E7 joint swap + typed-corruption inference with structured batch prior, driven by a weak witness** | **No equivalent found** | **Core candidate contribution (TC1)** |
| **Detectability map vs. witness strength** | **No equivalent found** | **Candidate contribution (TC3)** |
| **Soil lab-report verification benchmark with real errors** | **No equivalent found** | **Candidate contribution (TC4)** |

**Honest risk:** a reviewer may call TC1 "Broman + Bates + a unit table". The defence has to
be *experimental*: show that the joint model detects errors that **each component alone
misses** at equal FDR, specifically in the weak-witness regime. If that gain is not
measurable, TC1 is not a contribution, and the paper rests on TC3 + TC4.

## 3. Data finding that changes the plan

**Open Soil Spectral Library (OSSL v1.2):** 65,063 Vis-NIR and 91,631 MIR scans with harmonised
lab data (pH, C, N, P, K, CEC, texture, EC, …). The KSSL, ICRAF-ISRIC and AfSIS subsets are
Creative Commons; LUCAS inside OSSL is under the JRC licence.

This enables a **witness-strength ladder on real soil data, with no collection needed**:

| Rung | Witness derived from the same real sample | Strength |
|---|---|---|
| W0 | none (lab-only) | — |
| W1 | **colour only**: CIE XYZ → CIELAB/sRGB from 400–700 nm reflectance, plus measured phone-camera noise | weak (phone-like) |
| W2 | coarse visible bands (e.g. 10 bands) | weak-moderate |
| W3 | full Vis-NIR 350–2500 nm | strong |
| W4 | MIR | very strong (≈ P11 setting) |

W1 approximates a *calibrated* phone photo but **lacks texture and real capture noise**. It is
therefore an optimistic proxy for colour-driven properties and says nothing about texture from
images. This limitation must be stated. The noise model must be fitted from real phone images
(Photogranulometry and/or our own set), and T2 real phone data remains required before any
DEMONSTRATED claim.

## 4. Still unresolved

| Item | Why it matters | Next action |
|---|---|---|
| LUCAS soil-sample photos: public or not? | Would give real phone-like photos + lab data at scale | Eurostat photo sets list only point + 4 landscape photos. The 2018 surveyor manual is a scanned PDF. Email ESDAC/Eurostat |
| Seybold 2019 full text (P11) | Does MIR QC attribute types or detect swaps? | Get via library access |
| US 7,783,582 claims (P7) | Error-type attribution? | Read claims |
| KSSL replicate / re-analysis records | Possible source of **real** lab errors (upgrades T1 toward DEMONSTRATED) | Check the KSSL database for duplicate analyses |
| Formal systematic search (Scopus/WoS) | Needed for the paper's related-work rigour | Run with logged queries in Step 2 |

## Sources (in addition to doc 09)

- Zhou et al. 2023, Detecting errors in a numerical response: https://arxiv.org/abs/2305.16583
- Bates et al., Testing for outliers with conformal p-values: https://arxiv.org/abs/2104.08279
- Jin & Candès 2023, Selection by prediction with conformal p-values: https://jmlr.org/papers/volume24/22-1176/22-1176.pdf
- Peng et al. 2025, Conformal prediction with cellwise outliers: https://arxiv.org/abs/2505.04986
- Probabilistic multi-omics data matching for sample errors: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6615984/
- US20170169215A1, mislabelled samples via label propagation: https://patents.google.com/patent/US20170169215
- CN108732129B, farmland soil components from images: https://patents.google.com/patent/CN108732129B/en
- Open Soil Spectral Library (PLOS One): https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0296545 ; data: https://zenodo.org/records/7599269
- LUCAS primary data and photos (Eurostat): https://ec.europa.eu/eurostat/web/lucas/database/primary-data
- LUCAS 2015 topsoil (spectra, request form): https://esdac.jrc.ec.europa.eu/content/lucas2015-topsoil-data
- LimeSoDa benchmark: https://arxiv.org/abs/2502.20139
- REIN data-cleaning benchmark: https://arxiv.org/abs/2302.04702
- Colour from visible reflectance spectra (Viscarra Rossel et al.): https://www.researchgate.net/publication/223723277_Colour_space_models_for_soil_science
- Soil LIMS example: https://www.lablynx.com/industries/soil-testing-lims/
