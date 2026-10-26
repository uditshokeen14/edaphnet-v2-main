# Step 4a — OSSL Data Audit

> **CORRECTION (2026-09-24, see §7):** the coverage numbers in §3–§4 counted rows that exist in
> the Vis-NIR file but contain **no spectrum**. They are wrong. Only 49 samples have a real
> spectrum and all core-8 values. §7 gives the corrected audit; §3–§4 are kept only as a record
> of the error.

**Date:** 2026-09-23 · **Script:** `scripts/ossl_audit.py` · **Outputs:** `results/data_audit/`
**Evidence tag:** descriptive data audit (no modelling).

## 1. Source files (OSSL v1.2, downloaded 2026-09-23)

| File | Size | MD5 |
|---|---|---|
| ossl_soilsite_L0_v1.2.csv.gz | 6.4 MB | e8c640a9e7b6f15c2dec0a7d2e445716 |
| ossl_soillab_L1_v1.2.csv.gz | 9.6 MB | e24b94605b0061add400cf3b617f1f18 |
| ossl_visnir_L0_v1.2.csv.gz | 182.5 MB | 8543cf2265bced21e6a4aab3758207f6 |

The OSSL bucket "can be updated without notice", so the MD5s above define our dataset version.
Raw files are not committed (`data/raw/` is git-ignored); `data/ossl_manifest_md5.txt` is.

Vis-NIR: 1,076 reflectance columns, 350–2500 nm at 2 nm steps.

## 2. Licence filter

| Dataset | Licence | Used |
|---|---|---|
| KSSL.SSL | CC-BY | ✅ |
| ICRAF.ISRIC, CAF, GARRETT, SCHIEDUNG, SERBIA | CC-BY | ✅ |
| AFSIS2.SSL | CC0 | ✅ |
| AFSIS1.SSL | ODC ODbL | ✅ (share-alike on derived databases; noted) |
| LUCAS.SSL, LUCAS.WOODWELL.SSL | JRC Licence Agreement | ❌ excluded (redistribution restricted) |

## 3. Coverage (samples with Vis-NIR + lab, open licence)

| Property set | Samples | Location groups | Datasets |
|---|---|---|---|
| core 8 (pH, OC, N, clay, sand, CEC, K, Ca) | 45,541 | 9,688 | KSSL only |
| core 8 + EC | 25,208 | 5,175 | KSSL only |
| core 8 + P (a274) | 10,999 | 2,736 | KSSL only |
| pH + OC + N + clay + sand | 50,214 | 11,307 | KSSL, AfSIS1, Serbia |
| **core 8, topsoil (upper depth < 30 cm)** | **23,852** | **9,302** | KSSL (USA) |

Grouping key: `id.location_olc_txt` (fallback: dataset site ID, then layer ID). Layers of the same
profile share a location, so group-wise splits keep all depths of a profile together.

## 4. Decisions (fix doc 11 §4)

1. **Properties:** the core 8 (pH H₂O, OC, total N, clay, sand, CEC, exch. K, exch. Ca).
   EC is a secondary experiment (25k samples). Available P is **dropped** (coverage 11k,
   three incompatible methods).
2. **Scope:** topsoil (upper depth < 30 cm), because routine soil-test reports concern
   topsoil. This leaves 23,852 samples in 9,302 locations.
3. **Geography:** every core-8 sample is from the USA (KSSL). Transfer to other regions (e.g.
   Indian soils) is **untested** and is a stated limitation. A cross-dataset check is possible
   only on the 5-property subset (AfSIS1, Serbia).

## 5. Data-quality findings (important)

- Physically implausible values exist, e.g. **total N = 41.9%** and OC up to 56% (the latter is
  plausible for organic soils; the former is not in a mineral topsoil context). Zeros occur in
  several properties (below detection or missing coded as 0).
- **Consequence:** OSSL "clean" data likely contains real errors. Our calibration assumes
  clean nulls, so contamination would bias calibration toward leniency.
- **Rule (fixed before modelling, to avoid circularity):** we will *not* use our own detector
  to clean the data. We apply only an independent, pre-declared screen: drop values outside
  hard physical limits (pH ∉ [2, 11]; any % > 100; N > 5% when OC < 20%; texture
  sand+clay > 100.5), and treat zeros as below detection (set to half the smallest positive
  value per property). Everything the screen removes is counted and reported.
- **Opportunity (TC4):** values removed by the screen, plus internally inconsistent records,
  are *candidate real errors* in a public lab database. They can serve later as a small
  real-error test set, after independent verification (e.g. KSSL re-analysis records, which
  are still to be checked).

## 6. Limitations to carry into the paper

- US-only for the full property set.
- Vis-NIR spectra were measured on air-dried, sieved samples in a lab, so a colour derived
  from them is a controlled-capture, best-case proxy for a phone photo (doc 10 §3).
- KSSL analytical methods are harmonised by OSSL (L1). Harmonisation errors are possible.

## 7. Corrected audit (2026-09-24)

**Error:** `ossl_audit.py` joined on IDs present in the Vis-NIR file. That file has 135,651 rows but
only **64,644 non-empty spectra**. The 23,852 figure was samples with lab data and *an empty
spectrum row*. The error was found when the dataset builder required a real spectrum
(`scripts/build_ossl_dataset.py`); non-empty IDs are in `results/data_audit/visnir_nonempty_ids.csv.gz`.

**Non-empty Vis-NIR spectra by dataset:** LUCAS 40,175 · KSSL 19,807 · ICRAF-ISRIC 4,073 · LUCAS-Woodwell 589.

| Option | Samples with spectrum + properties | Properties | Licence | Notes |
|---|---|---|---|---|
| KSSL Vis-NIR | 19,807 | OC, N, total C, CaCO₃ only (pH/texture/CEC/K/Ca on ≤ 166) | CC-BY | too few properties for report-level verification |
| **ICRAF-ISRIC** | **3,473** (553 profiles; 1,398 topsoil) | pH, OC, clay, sand, CEC, K, Ca, Mg (no N) | CC-BY | global reference soils; open; small |
| **LUCAS 2009/2015** | ≈ 40,000 (topsoil by design, 0–20 cm) | pH, OC, N, P, K, CaCO₃, EC, clay, sand, silt | JRC licence (free, on request) | best fit; Europe; data may not be redistributed |
| core-8 as in §4 | 49 | — | — | unusable |

The 49-sample build output was deleted. The decision on the dataset is D-009.
