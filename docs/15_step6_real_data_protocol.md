# Step 6 — Real Paired Data Collection Protocol (draft v1)

**Date:** 2026-09-25 · **Status:** DRAFT. Needs supervisor review and, if required by your
institution, ethics/consent approval before collection starts.
**Purpose:** produce the first dataset that pairs **smartphone photographs** of soil samples with
**full laboratory reports** of the *same physical samples*, plus repeat analyses that reveal
**real** lab errors. It turns steps 3–5 (synthetic / proxy witness) into DEMONSTRATED evidence.

---

## 1. What this dataset must answer

| Question | Why it matters | Measured by |
|---|---|---|
| Q1. How informative is a *real* phone photo about each property? | Step 3: the method only helps if witness R² ≈ 0.3–0.7 on colour-linked properties (doc 13 §7) | R² per property on held-out samples; compared with the W1/W2 ladder (doc 14) |
| Q2. How much does colour differ between phones and lighting? | Sets the realistic ΔE (step 4b ran ΔE 0, 2, 4, 8 as a sweep) | ΔE between repeated captures of the same sample |
| Q3. Does a photo add texture information that spectrum-colour lacks? | W1 may *under*-estimate a photo for clay/sand (doc 14 §4.4) | R² of image texture features vs colour-only |
| Q4. Does it transfer to Indian soils? | All current data is global or US reference soils | Performance of models trained on ICRAF-ISRIC, applied to the new samples |
| Q5. How often do *real* lab reports contain errors, and which types? | Injected error mixes are assumptions (doc 11 §10) | Blind duplicate discrepancies; transcription checks |
| Q6. Does the full method work end-to-end with real photos + real reports? | The DEMONSTRATED claim of the paper | Step-5 pipeline on this data (swaps and value errors computational + planted) |

## 2. Sample size (planning estimate)

- **Target: 250–300 physical samples; minimum 200.**
- Justification (Q1): for a true R² ≈ 0.35, the standard error at n = 200 is ≈ 0.054
  (95% CI ≈ ±0.11); at n = 300 it is ≈ 0.044 (±0.09). That is enough to tell "colour-only
  level" (≈ 0.35) from "weak" (≈ 0.1) and from "strong" (≈ 0.6).
- Swap detection (Q6) does **not** need hundreds of real swaps. A swap is a mismatch between a
  photo and a report, so once every sample has a trusted photo–report pair, swaps can be created
  computationally by re-pairing reports within simulated batches, exactly as in step 5, now
  with real photos. Planted physical swaps (§6) add realism to the labelling process.
- **Diversity matters more than count:** ≥ 3 regions / soil types (e.g. red, black/vertisol,
  alluvial, laterite), a range of organic matter, from ≥ 30 distinct fields. Keep the field ID:
  it is the grouping unit for all splits.

## 3. Lab analysis panel

| Priority | Properties | Reason |
|---|---|---|
| **Required** | pH, EC, organic carbon, available N, P, K (the Indian Soil Health Card panel) | Realistic report format; routine and cheap |
| **Required** | Texture: sand, silt, clay | Texture test for Q3; overlaps ICRAF-ISRIC |
| Recommended | CEC, exchangeable Ca, Mg | Overlap with ICRAF-ISRIC (Q4); internal-consistency rules |
| Optional | S, Zn, Fe, Cu, Mn, B | Complete SHC report; not colour-linked (expected negative controls) |

Ask the lab for: method names (e.g. Walkley-Black OC, Olsen/Bray P), units, detection limits,
and the **original report files** (PDF/paper). Report formatting errors are part of what we study.

## 4. Blind duplicates (real-error ground truth, Q5)

- **25% of samples** (e.g. 70 of 280) are split into two sub-samples with **different, unrelated
  codes** and sent in the same submission. The lab must not know which pairs are duplicates.
- **~10% of samples** also go to a **second lab**.
- A pair whose results differ beyond the method's published repeatability is a *candidate real
  error*. Candidates are classified (transcription, unit, swap, analytical) by re-checking lab
  records where the lab allows it.
- Budget note: duplicates add ~35% to lab cost. If the budget is tight, keep duplicates and
  reduce the optional panel, not the reverse.

## 5. Photo capture protocol (Q1–Q3)

**Sample preparation:** air-dry → crush gently → sieve < 2 mm (same as the lab) → spread ≈ 1 cm
deep in a flat dish or tray (e.g. a 9 cm Petri dish), surface levelled with a spatula.

**In every photo:**
- a **colour reference card**: X-Rite/Calibrite ColorChecker (Classic Mini or Passport) is
  preferred. A printed card is **not** acceptable (inks vary). If the budget allows only one
  item, buy the colour card;
- a **printed QR code / label with the sample code** (prevents our own mix-ups and lets
  software read the ID);
- a **scale** (ruler) for texture features.

**Capture set per sample (24 images):**
- **2 phones** (different brands; record the model) × **2 lighting conditions** (indoor diffuse
  daylight near a window; shade outdoors, never direct sun) × **2 moisture states** (dry; moist
  after a fixed water volume, e.g. 2 mL, sprayed and left 5 minutes) × **3 shots**
  (re-position the phone between shots).
- Phone **fixed on a stand at ~20–25 cm**, camera parallel to the sample, no flash, no zoom,
  HDR/"beauty"/AI scene modes **off**. Use RAW/DNG if the phone supports it, plus JPEG.
- **Photos are taken before lab results are known** (blinding), by a person who does not
  handle the lab submission sheet if possible.

**Minimum viable version (low budget):** 1 phone × 1 lighting × dry only × 3 shots = 3 images
per sample. It still answers Q1, Q4 and Q6, but not Q2 (phone variation).

## 6. Planted physical swaps (optional, Q6 realism)

A third person (not the analyst) swaps the labels of a few sample pairs **before** lab
submission and records them in a sealed file (e.g. 1–2 pairs per 24-sample batch; ~10 pairs in
total). The analyst runs the method blind, then the file is opened. Tell the lab this is a QC
study so the swapped results are not treated as their error.

## 7. Records and file naming

- One row per physical sample in `templates/sample_log.csv` (created with this document).
- Sample code format: `EDN-<field>-<sample>`, e.g. `EDN-F07-S03`. Duplicates get **new random
  codes**; the key mapping duplicates is kept separately (`templates/duplicate_key.csv`) and not
  shared with the lab.
- Image file name: `<code>_<phone>_<light>_<moisture>_<shot>.jpg`, e.g.
  `EDN-F07-S03_P1_IN_DRY_2.jpg`. The per-image log is `templates/capture_log.csv`.
- Raw lab reports are stored unchanged (scanned or PDF) under `data/raw/lab_reports/`; values are
  typed into `templates/lab_results.csv` **twice by two people** (double entry), so
  transcription errors are ours and measurable, not silent.

## 8. Ethics, consent, licensing

- Farmer / landowner consent for sampling and for publishing anonymised results.
- Location stored at field level, and released only as a coarse grid cell (e.g. 0.1°).
- Agree with the lab in advance that anonymised results may be published.
- Planned release licence: CC-BY 4.0 for images + lab values (TC4 benchmark).

## 9. Timeline (indicative)

| Weeks | Task |
|---|---|
| 1–2 | Supervisor review; ethics/consent; lab quotes; buy colour card and phone stand |
| 2–3 | Pilot: 10 samples through the full protocol; fix problems; measure time per sample |
| 3–8 | Field sampling (≥ 30 fields, ≥ 3 regions) and preparation |
| 4–10 | Photography (blind to lab results); lab submission in batches of 24 with duplicates |
| 8–14 | Lab results arrive; double data entry; duplicate analysis |
| 12–16 | Phone witness pipeline (colour-card correction → CIELAB + texture features) and step-5 re-run on real photos |

## 10. What will be built in code during step 6

- `edaphnet2/phone.py`: ColorChecker detection and colour correction (e.g. with the
  `colour-checker-detection` package), CIELAB extraction from the soil region, texture features
  (GLCM, LBP, granulometry), and image-quality checks (blur, exposure).
- A step-5 runner variant that uses phone features as the witness.
- Validation of Q2: ΔE between phones/lighting for the same sample, which replaces the assumed
  ΔE sweep with a measured one.

## 11. Decisions needed from you / your supervisor

1. Budget: number of samples and whether CEC/Ca/Mg are affordable.
2. Which regions / fields you can access.
3. Which lab(s): a government Soil Testing Laboratory, a university lab, a private lab?
4. Whether planted physical swaps (§6) are acceptable to the lab.
5. Full protocol (24 images/sample) or the minimum version (3 images/sample).
