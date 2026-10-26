# EdaphNet App Layer — Design and Methodology (v1)

**Date:** 3 October 2026 · **Status:** design written **before** any app data was downloaded or any
model trained. Changes are recorded as dated amendments at the end.
**Scope:** an application built on top of the research code. The paper stays about checking soil
laboratory reports (docs 18–23); nothing here is a paper claim.

---

## 1. Purpose and boundaries

A farmer-facing tool that, from phone photos and (optionally) a lab report, gives:
1. the likely **soil type / soil properties** from a soil photo,
2. a ranked list of **suitable crops** for that soil and climate, with reasons,
3. a likely **leaf disease** from a leaf photo, with management information,
4. a **check of the soil lab report** (the research method, `src/edaphnet2/`).

**Boundaries (stated in the app and in the viva):** the tool gives *advice with uncertainty*, not a
diagnosis. Every answer shows how confident it is, says "not sure" when the input is outside what the
model has seen, and points to a soil-testing lab or an extension officer for decisions.

## 2. Architecture

```
phone camera / upload ──► app/web (one page: soil photo, leaf photo, lab report)
                              │
                              ▼
                        app/server.py (one backend, Python standard library)
              ┌───────────────┼───────────────────┬──────────────────────┐
              ▼               ▼                   ▼                      ▼
      app/soil model    app/leaf model     app/crop suitability   src/edaphnet2 (research:
      (colour + texture (disease classes)  (rules from FAO        report check, colour
       features)                            ECOCROP + soil         correction, colour model)
                                            profiles)
                              ▲
                     app/knowledge (JSON + SOURCES.md)
```

Re-used from the research code without change: colour-card correction and photo-quality checks
(`phone.py`), the colour → soil-property model (`train_colour_brain.py`), the report checker
(`inference.py`), and the run-record tracking (`tracking.py`).

## 3. Soil model (`app/soil`)

**Task.** Two outputs, kept separate:
- (a) **soil properties** (OC, and texture where data allows) from colour + texture. This is the
  existing research colour model plus texture features. Reported with 90% ranges.
- (b) **soil type** (black / red / alluvial / laterite / clay / sandy) as a classification.

**Why both.** Properties drive crop suitability; a type label is what farmers recognise. "Type"
labels mix different axes (origin vs texture: the old project's audit found Alluvial ↔ Clay label
conflicts), so the app uses type only as a friendly label, and properties for decisions.

**Data (candidates; nothing downloaded yet).**

| Source | Content | Notes / risk |
|---|---|---|
| IRSID (IEEE DataPort) | original photos of Indian soils (sand, clay, sandy loam, loam, loamy sand), Andhra Pradesh | texture classes, original photos: **preferred**. Licence and size to confirm |
| Kaggle "Multiclass Soil Image Dataset" | alluvial, black, clay, laterite | scraped/web-like images; licence unclear; **test for duplicates and leakage before use** |
| Roboflow soil sets | alluvial, black, clay, red, laterite | mixed origins; same caution |
| Old project images (`new_to_do`) | 4 classes | audit found 2.3× duplication and 100% test contamination: **excluded** |
| Our own photos (doc 15 protocol) | phone + colour card, with lab values | the only data with ground truth; final test set |

**Method.** Colour features after colour-card correction (CIELAB) + texture features
(`phone.texture_features`), then a small classifier (logistic regression / LightGBM), compared with a
small pretrained CNN (MobileNetV3 or EfficientNet-B0, frozen features + linear head). CPU only.

**Evaluation.** Group splits by **photo session / field / source website** (never by image), after
MD5 + perceptual-hash de-duplication. Metrics: macro-F1, per-class recall, calibration (ECE), and an
**out-of-source test**: train on public sets, test on our own phone photos. The out-of-source score
is the number reported to users and in the viva.

## 4. Crop suitability (`app/crop`)

**Task.** Rank crops for a field from: soil properties (from the lab report if available, otherwise
from the soil model with its uncertainty), plus climate (rainfall, temperature) entered by the user
or looked up by district.

**"Multi-soil".** Instead of one soil label, the soil model gives a probability over soil types /
property ranges. Suitability is averaged over that uncertainty (the same idea as the old project's
posterior-propagating bridge), so a field that "could be red or laterite" gets crops that suit both.

**Method (transparent, rule-based first).** For each crop, FAO ECOCROP gives optimal and absolute
ranges for pH, temperature, rainfall, texture and depth. Suitability per factor is a trapezoid (1 in
the optimal range, falling to 0 at the absolute limits); the crop score is the minimum over factors
(Liebig's law of the minimum), and the limiting factor is shown as the reason. No machine learning
here: there is no reliable public dataset of crop outcomes for these soils, and the old project's
crop CSV was found to be likely synthetic (doc 04, old project).

**Data.** FAO ECOCROP (`EcoCrop_DB.csv` via the OpenCLIM repository); Indian soil-type property
profiles from ICAR / NBSS&LUP / state agricultural university publications (every value with page
reference in `app/knowledge/SOURCES.md`).

**Evaluation.** No accuracy claim without outcome data. Instead: (i) agreement with published
state-level crop recommendations for major soil zones (qualitative check by an agronomist), and (ii)
sensitivity: how often the top-3 crops change when soil properties move within their uncertainty.

## 5. Leaf disease model (`app/leaf`)

**Task.** Classify a leaf photo into crop + disease (or healthy), or say "not sure".

**Data.**

| Source | Content | Licence | Role |
|---|---|---|---|
| PlantVillage | ~54,300 images, 38 classes, 14 crops; lab photos on plain backgrounds | CC0 / CC BY-SA 3.0 depending on the copy (to confirm) | training |
| PlantDoc | 2,598 images, 27 classes (17 diseases, 10 healthy), field-like web images | CC BY 4.0 | **test** (cross-dataset) |
| Our field photos | phone photos from Indian farms | ours | final test |

**Known pitfall.** Models trained on PlantVillage reach ~99% on its own test split but drop sharply
on field photos, partly because they learn the plain background. Recent work reports this
cross-dataset gap explicitly (e.g. TinyCNN, arXiv 2609.20290). **We will report the PlantDoc and
field-photo accuracy as the headline number, not the PlantVillage number.**

**Method.** Transfer learning with a small pretrained CNN (MobileNetV3-Small / EfficientNet-B0),
background augmentation (random backgrounds, crops, colour jitter), class mapping to the classes
shared by PlantVillage and PlantDoc. An abstention rule: if the top probability (after temperature
scaling) is below a threshold set on a validation set, answer "not sure". CPU training on a subset
is feasible; full training may need a free GPU session (Colab/Kaggle).

**Evaluation.** Accuracy and macro-F1 on (i) PlantVillage held-out, (ii) PlantDoc (shared classes),
(iii) our field photos; per-class recall; coverage vs accuracy curve for the abstention rule.

## 6. Knowledge base (`app/knowledge`)

- `diseases.json`: for each disease class, the symptoms, cause, and management advice, from ICAR /
  state agricultural university / FAO extension documents.
- `crops.json`: ECOCROP ranges for the crops shown to users (Indian crops first).
- `soil_profiles.json`: typical property ranges per soil type (Indian sources).
- **Rule:** every value has a row in `SOURCES.md`. A value without a source is not shown in the app.

## 7. Server and web page

- **Server:** extend the existing standard-library server (`scripts/serve_demo.py`) into
  `app/server.py`, with endpoints `/api/soil`, `/api/crops`, `/api/leaf`, `/api/report-check`.
- **Web page:** one page with three tabs (Soil, Crops, Leaf), upload or **camera capture**
  (`<input type="file" accept="image/*" capture="environment">` works on phones), and the report
  checker. Every result shows confidence and "not sure" states.

## 8. Data rules (apply to every dataset)

1. Record source, licence, version, download date and MD5 of every file (`data/app_raw/MANIFEST.csv`).
2. De-duplicate (MD5 + perceptual hash) **before** splitting.
3. Split by **photo session / field / source**, never by image.
4. The test set is frozen before training starts.
5. Report the out-of-source / field result as the main number.

## 9. Dependencies and downloads (need approval before Step 1 runs)

| Item | Why | Approx. size |
|---|---|---|
| `torchvision` (+ pretrained MobileNetV3/EfficientNet-B0 weights) | image models | ~10 MB package + 10–25 MB weights |
| PlantVillage (colour images) | leaf training | about 1–2 GB (to confirm) |
| PlantDoc | leaf test | about 1 GB (to confirm) |
| FAO ECOCROP CSV | crop ranges | < 5 MB |
| IRSID and other soil image sets | soil model | to confirm |

Laptop limits: CPU only, 7.8 GB RAM. Training uses small models and batches; long trainings may be
moved to a free GPU notebook.

## 10. Plan

| Step | Content | Time |
|---|---|---|
| 0 | Structure + this document | ½ day ✅ |
| 1 | Download (after approval) and audit data: manifest, licences, duplicates, splits | 2–4 days |
| 2 | Soil model + crop suitability | 3–5 days |
| 3 | Leaf model with cross-dataset test | 3–5 days |
| 4 | Knowledge base with sources | 2–3 days |
| 5 | Server + web page with camera | 2–3 days |
| 6 | Field test with own photos; honest results table | after step-6 data |

## Amendments

**Amendment 1 (2026-10-03): EcoCrop sanity check.** The crop tool reproduces EcoCrop's ranges
correctly, but some global ranges disagree with Indian practice: wheat's optimal pH is 6.0–7.0 (score
0.33 at pH 8.0), and mustard's is 5.5–6.5 (absolute maximum 8.0), although both are widely grown on
alkaline Indo-Gangetic and Rajasthan soils. Therefore: (1) `app/knowledge/crops_local.json` holds
Indian overrides, each of which must cite its source and page (enforced in code); (2) the tool is
not presented as validated until its rankings for typical soil zones have been checked against
ICAR / state agricultural university recommendations by an agronomist (§4 evaluation).
