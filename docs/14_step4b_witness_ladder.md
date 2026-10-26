# Step 4b — Witness Ladder on Real Soil Data (ICRAF-ISRIC)

**Run:** `results/runs/20260925-003906_witness_ladder_icraf8_7050ab6`
**Scripts:** `scripts/build_ossl_dataset.py --dataset ICRAF.ISRIC --props icraf8`, `scripts/fit_witness_ladder.py`
**Evidence tag:** real lab data and real spectra. W1 colour is *computed* from lab spectra of
dried, sieved samples, so it is a **best-case proxy** for a phone photo. The ΔE sweep adds
capture noise; real phone images are still required (T2).

## 1. Data (D-009, D-011)

- ICRAF-ISRIC (CC-BY), 3,473 samples, 553 profiles, all depths, global reference soils.
- Properties: pH, OC, clay, sand, CEC, K, Ca, Mg (no N in this dataset).
- Split by profile: train 1,726 (276 profiles) / cal 511 (82) / test 1,236 (195). No profile
  crosses splits (asserted in code).
- Physical screen removed 0 samples. **Zeros:** K 769 (22%), Mg 564, Ca 464, OC 15, clay 15.
  These were set to half the minimum positive value per the pre-declared rule, which creates a
  spike at the floor for K, Ca and Mg (see §4).
- Colour range: L* 29–76, a* 1–22, b* 6–35 (1st–99th percentile), i.e. very diverse soils.

## 2. How much each witness knows: R² on the test split (latent scale)

| Rung | OC | pH | Ca | Mg | CEC | clay | K | sand |
|---|---|---|---|---|---|---|---|---|
| W0 none | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **W1 colour, no noise** | **0.37** | 0.27 | 0.23 | 0.13 | 0.11 | 0.16 | 0.07 | 0.02 |
| W1 colour, ΔE = 2 | 0.35 | 0.15 | 0.13 | 0.06 | 0.05 | 0.07 | −0.01 | −0.09 |
| W1 colour, ΔE = 4 | 0.30 | 0.04 | 0.06 | −0.01 | −0.01 | −0.01 | −0.05 | −0.14 |
| W1 colour, ΔE = 8 | 0.25 | 0.01 | 0.03 | −0.02 | −0.04 | −0.01 | −0.03 | −0.12 |
| W2 10 visible bands | 0.37 | 0.29 | 0.24 | 0.12 | 0.11 | 0.14 | 0.00 | −0.03 |
| W3 full Vis-NIR | 0.60 | 0.62 | 0.65 | 0.60 | 0.63 | 0.66 | 0.39 | 0.46 |

Negative R² means worse than predicting the training mean: the model fits noise.

## 3. Uncertainty calibration (90% intervals, test split)

- Split-conformal: 0.83–1.00 coverage; Gaussian (from out-of-fold residuals): 0.87–0.94.
- Under-coverage for sand (0.83–0.89) and CEC (0.84–0.88) reflects profile-to-profile
  shift: calibration uses only 82 profiles. This matters for step 5's error control and must
  be monitored there.

## 4. Interpretation (mapped onto the T0 simulation, doc 13)

| Real witness | Comparable T0 strength | T0 gain of Full over best baseline |
|---|---|---|
| Colour, noise-free (OC 0.37, clay 0.16) | ≈ λ = 1 (OC 0.37, clay 0.24) | +0.04 to +0.12 |
| Colour, phone noise ΔE ≥ 4 (only OC survives, 0.25–0.30) | between λ = 0.5 and 1 | ≈ 0 to small |
| Full Vis-NIR (0.4–0.66 on all properties) | ≈ λ = 2 | +0.20 to +0.25 |

**Honest reading:**
1. A computed soil colour carries real information about **organic carbon** (robust to capture
   noise) and some about pH/Ca, but little about texture, CEC or K. That is consistent with
   the smartphone literature (doc 09 §1.1).
2. On this evidence, a **colour-only phone witness sits at the low end** of the band where the
   joint method helped in simulation. A **modest** gain is plausible if capture is well
   controlled (colour card, ΔE ≤ 2); with poor capture the gain is expected to vanish.
3. A full spectrum is a strong witness, but it needs a spectrometer, which contradicts the
   "cheap" premise. It serves as the upper reference.
4. A real phone *image* also carries texture information (granularity, aggregates) that a
   spectrum-derived colour lacks, so W1 may *under*estimate a photo for clay/sand. This
   cannot be tested without real photos (T2).

## 5. Consequences for step 5

- Step 5 runs the full pipeline (Full + baselines + injection-aware calibration) on ICRAF-ISRIC
  with W0, W1(ΔE 0/2/4/8), W2 and W3. This is the pre-registered go/no-go (doc 11 §7, reframed
  by D-010).
- **Kill/reframe rule (restated before running):** if Full's advantage over the best baseline at
  W1 (ΔE ≤ 2) has a CI including 0, the phone-based claim is dropped. The paper then becomes
  "spectrometer-grade witness verification + detectability map" (doc 11 §7 decision table).
- Sensitivity analysis: repeat without K, Ca and Mg (the zero-inflated properties).
