# Problem Specification & Pre-Registration Draft (Step 2 deliverable)

**Date:** 2026-09-23 · **Status:** DRAFT v1. It becomes frozen when (a) the supervisor signs off
and (b) it is registered (e.g. OSF) **before any Step-5 test-set result is computed**.
**Depends on:** doc 09 (research design), doc 10 (prior-art matrix v1).

Changes after freezing are allowed only as dated amendments at the end of this file, each with
a reason. Anything not specified here is **exploratory** and must be labelled so in the paper.

---

## 1. Problem statement

A soil-testing lab analyses samples in **batches** (trays). Reports can be wrong in two
structurally different ways:
1. **Swap errors:** a report belongs to a different physical sample in the batch (labelling,
   tray-position or data-entry misalignment).
2. **Value errors:** an individual reported value is corrupted (unit or decimal mistake,
   transposition, column swap, gross analytical error).

For every sample we also have an independent **witness**: an observation of the *same physical
sample* that the lab process cannot corrupt (a phone image; in Steps 3–5 a proxy derived from
spectra). The witness is **weak**: it predicts some properties moderately and others barely.

**Task.** Given one batch of reports and witnesses:
- (T-a) flag erroneous reports with the **false discovery rate controlled at level q**;
- (T-b) for each flag, attribute the error: swap (and with which sample) vs. value error (which
  property, which corruption type);
- (T-c) propose a corrected value or re-assignment with an uncertainty statement;
- (T-d) characterise which errors are detectable at which witness strength.

---

## 2. Formal model

### 2.1 Notation

| Symbol | Meaning |
|---|---|
| b | a batch; n = batch size; positions 1…n in processing order |
| i | physical sample index; j = report index (report j is *recorded* as sample j) |
| k = 1…p | soil properties (candidate list §4) |
| xᵢ ∈ ℝᵖ | true property vector of sample i |
| yᵢ = xᵢ + εᵢ | correctly measured lab values; εᵢ = analytical repeatability noise (per-property CV from lab QC literature) |
| wᵢ | witness observation of sample i |
| π | latent permutation: report j actually measured sample π(j); identity = no swap |
| cⱼₖ ∈ 𝒞 | latent corruption type of cell (j,k); c = id means uncorrupted |
| Tᶜ | corruption operator; rⱼₖ = T^{cⱼₖ}( y_{π(j),k} ) is the reported value |

### 2.2 Generative model

```
π        ~ P(π)                 structured swap prior (§2.3)
cⱼₖ      ~ Cat(θ)               corruption prior, θ_id ≈ 1 − small rates (§2.4)
xᵢ | wᵢ  ~ p_φ(x | w)           witness model: calibrated multivariate predictive distribution
yᵢ | xᵢ  ~ N(xᵢ, Σ_ε)           lab repeatability
rⱼ       = T^{cⱼ}( y_{π(j)} )   observed report
```

Report-internal knowledge (constraints, e.g. sand+silt+clay = 100, and the regional joint
distribution) enters through p_φ, which is conditioned on the witness **and** the population
prior. It is therefore a *joint* distribution over the p properties (Gaussian copula over
transformed marginals, §3.2). This lets a single corrupted cell be detected through its
inconsistency with the other cells even when the witness is uninformative for that property.

### 2.3 Swap prior P(π): the structured hypothesis set 𝒮

Exact inference over all n! permutations is impossible and unnecessary. Real mix-ups are
structured (Broman et al. 2014 observed off-by-one/two plate shifts). The hypothesis set:

| Class | Description | Size | Prior mass (default, tunable on dev only) |
|---|---|---|---|
| S0 | identity | 1 | 1 − ρ |
| S1 | adjacent transposition (i, i+1) | n−1 | 0.5 ρ |
| S2 | block shift by ±1 or ±2 over a contiguous run [a, b] | O(n²) | 0.3 ρ |
| S3 | arbitrary pair transposition (i, j) | O(n²) | 0.2 ρ |

At most one swap event per batch in the default model; two events is an exploratory extension.
Mass is spread uniformly within each class. ρ = per-batch swap prevalence parameter.

### 2.4 Corruption library 𝒞 (value errors)

| ID | Operator | Example |
|---|---|---|
| id | none | — |
| D+ / D− | ×10 / ÷10 (decimal slip) | pH 6.8 → 68 |
| U-OC | % ↔ g/kg (×10 / ÷10) | OC 1.2 % recorded as 1.2 g/kg |
| U-P | P ↔ P₂O₅ (×2.29 / ÷2.29) | |
| U-K | K ↔ K₂O (×1.205) ; cmol(+)/kg ↔ mg/kg (×391) | |
| U-ha | mg/kg ↔ kg/ha (×2.24, 15 cm, ρ_b 1.5; stated assumption) | |
| TR | adjacent-digit transposition | 0.16 → 0.61 |
| CS | column swap between two properties k, k′ within the report | P and K interchanged |
| G | gross analytical error: multiplicative factor ~ LogUniform(0.33, 3) excluding [0.8, 1.25] | |

At most one corrupted cell per report (default; two is exploratory). Operators are applied
only where the resulting value is plausible-looking: an injected error the range check (B0)
would trivially catch is still injected, but reported separately as "trivial".

### 2.5 Inference (proposed method, "Full")

For each π ∈ 𝒮 the batch log-likelihood factorises over reports. For each report, the
corruption is marginalised by enumeration (≤ 1 + p·|𝒞| hypotheses):

```
L(π) = Σⱼ log Σ_{c ∈ 𝒞ⱼ} P(c) · p( T^{c}⁻¹(rⱼ) | w_{π(j)} ) · |J_c|
```

p(y | w) = ∫ N(y; x, Σ_ε) p_φ(x | w) dx; J_c is the Jacobian of the inverse operator. The
posterior over (π, c) is normalised over the enumerated set. Complexity is
O(|𝒮| · n · p · |𝒞|) = O(n³ p |𝒞|) worst case with S3. It is exact over the hypothesis set,
with no approximation.

**Outputs per report j:**
- error score sⱼ = 1 − P(π(j) = j and cⱼ = id | batch)
- MAP attribution (swap partner, or (k, c))
- corrected value T^{ĉ}⁻¹(rⱼₖ) with the predictive interval from p_φ

### 2.6 Error control (T-a)

- **Calibration set:** batches of *clean* reports from calibration sites (disjoint from witness
  training and test sites), scored by the same procedure.
- Conformal p-value per test report: pⱼ = (1 + #{calibration scores ≥ sⱼ}) / (N_cal + 1).
- Flags = Benjamini–Hochberg at level q over all test reports in the evaluation pool.
- **Known caveat (stated up front):** joint scoring induces dependence between reports in a
  batch, so the PRDS condition behind BH with conformal p-values (Bates et al.) is not
  guaranteed. We therefore (i) report **empirical** FDR in every setting and (ii) also run
  Benjamini–Yekutieli (valid under arbitrary dependence) as a conservative check.

---

## 3. Components and their status

| Component | Role | Contribution? |
|---|---|---|
| 3.1 Witness proxies W0–W4 (§5) | provide wᵢ | No: data construction |
| 3.2 Witness model p_φ(x \| w): per-property quantile GBM + Gaussian copula over PIT residuals, conformalised | calibrated joint predictive distribution | No: established tools |
| 3.3 Structured hypothesis enumeration + typed corruption marginalisation (§2.3–2.5) | joint inference | **Yes: TC1 candidate** |
| 3.4 Conformal p-values + BH | error control | No: tool (Bates; Jin & Candès) |
| 3.5 Detectability analysis (§7, H5) | characterisation | **Yes: TC3 candidate** |
| 3.6 Benchmark protocol + error injector | evaluation | **Yes: TC4 candidate (with real errors in T2)** |

---

## 4. Properties (candidate list, final after the Step-4 data audit)

pH (H₂O), organic carbon, total N, clay, sand, CEC, exchangeable K, exchangeable Ca. EC and
available P are included **only if** OSSL coverage with harmonised methods is ≥ 50% of the
selected samples (to be checked in Step 4). Selection criterion: routine soil-test properties
with enough harmonised coverage. The criterion is fixed now; the list is fixed after the audit.

---

## 5. Data

| Tier | Source | Witness | Errors | Evidence tag |
|---|---|---|---|---|
| T0 (Step 3) | fully synthetic: Gaussian copula with a correlation structure fitted to OSSL summary statistics | synthetic, informativeness set by parameter λ | injected (§2.3–2.4) | MEASURED-SYNTHETIC |
| T1 (Steps 4–5) | OSSL v1.2, CC-licensed subsets (KSSL, ICRAF-ISRIC, AfSIS) | ladder W0–W4 from each sample's own spectrum | injected | real data + injected errors |
| T2 (Step 6) | own paired set + blind duplicates / lab re-test records | real phone images | **real** | DEMONSTRATED |

**Witness ladder (T1):**
- W0: none
- W1: colour only (CIELAB from 400–700 nm reflectance under D65 / 2° observer, plus a phone
  noise model)
- W2: 10 coarse visible bands
- W3: full Vis-NIR
- W4: MIR

**Phone noise model for W1:** additive noise in CIELAB with covariance estimated from
repeated phone captures of the same samples. Until our own captures exist, use literature
values of inter-phone ΔE₀₀ (sweep ΔE₀₀ ∈ {0, 2, 4, 8}) and report results across the sweep.

**Splits (T1):** grouped by site/profile ID (never by sample). 50% witness-model training,
15% conformal/score calibration, 35% test. Split files hashed and frozen before any Step-5 run.
Hyperparameters are tuned on the training sites only (inner CV).

**Batch construction:** size n ∈ {6, 12, **24**, 48, 96} (24 = default). Two orderings:
- *random* (heterogeneous batches)
- *clustered*: samples from the same site or region are adjacent, as in real labs where one
  farm's samples go together. Neighbours are then similar, so adjacent swaps are **harder to
  detect and less harmful**. This is a realism condition that must be reported.

**Error injection:** report-level error prevalence ∈ {1%, **5%**, 10%}. Swap vs. value errors
50/50 by default. Within value errors, types are uniform over 𝒞. Results are reported per
type. The true field mix is unknown; measuring it is part of T2.

---

## 6. Baselines (all get the same witness model, calibration data and BH procedure)

| ID | Baseline | Represents |
|---|---|---|
| B0 | per-property fixed range checks (agronomic limits) | current practice |
| B1 | internal-consistency rules (texture sum, CEC ≥ Σ exchangeable bases, C:N band, OC–N relation) | lab rule-based QC |
| B2 | lab-only multivariate plausibility: Gaussian-copula density of the report (no witness) | multi-analyte check without history |
| B3 | per-value witness check: conformal interval of p_φ(x_k \| w) per cell, no joint model | Rockwell-style validation (US 8,352,394) |
| B4 | swap-only matching: Hungarian assignment on report-vs-witness cost, permutation test | Broman / lineup transferred |
| B5 | supervised GBM trained on injected errors (features from B1–B4) | clinical WBIT-ML style |
| B6 | rule-based unit/decimal repair: test candidate conversions against range | clinical unit harmonisation |
| B7 | Zhou et al. 2023 veracity scores (regression-based numeric error detection) | closest ML prior art |

B5 is trained on **dev-site** batches with the same injection distribution. This gives it an
advantage (it sees the error mix), which is stated.

---

## 7. Hypotheses (pre-registered)

Primary metric: **report-level power at empirical FDR level q = 0.10** (TPR among erroneous
reports when BH at q). Secondary: AUPRC, realised FDR, type-attribution accuracy, correction
accuracy (within 2× repeatability SD), swap exact-recovery rate.

| ID | Hypothesis | Test | Success criterion |
|---|---|---|---|
| **H1** (TC1) | At W1, n=24, prevalence 5%, Full has higher power than the best of B2, B3, B4, B5, B7 | paired over identical test batches; cluster bootstrap over batches (2,000) | Δpower ≥ 0.05 absolute **and** 95% CI > 0, in both random and clustered orderings |
| **H2** (TC1 mechanism) | The joint model's advantage is largest for weak witnesses: Δpower(W1) > Δpower(W4) | interaction contrast, bootstrap | CI of the difference > 0 |
| **H3** (validity) | Realised FDR ≤ q + 0.02 in every setting of the grid | per-setting binomial CI | no setting's CI lower bound exceeds q + 0.02 |
| **H4** (attribution) | Among true detections, Full's error-type accuracy exceeds B6 + B4 combined | paired bootstrap | CI > 0 |
| **H5** (TC3) | Detection power for a swap (i, i′) is predicted by the witness-space separation D(i, i′) (symmetric KL between p_φ(·\|wᵢ) and p_φ(·\|wᵢ′)); likewise for value errors by the corruption magnitude relative to the predictive SD | logistic model of detection vs. D; held-out settings | out-of-setting AUC of the power model ≥ 0.8 |
| **H6** (structure prior) | The structured prior (S1–S3 weights) beats a uniform permutation prior on adjacent/shift swaps without losing > 0.02 power on random pair swaps | paired bootstrap | both conditions hold |

**Multiplicity:** Holm correction over the H1 comparisons (5 baselines). H2–H6 are secondary
and are reported with unadjusted CIs, labelled as such.

**Seeds and replication:** 5 seeds × ≥ 500 test batches per setting. The seeds are fixed in
the config before the run.

### Decision rules (fixed now)

| Outcome | Consequence for the paper |
|---|---|
| H1 ✔, H3 ✔ | TC1 is claimable on T1 (real data + injected errors); proceed to T2 |
| H1 ✘, H3 ✔ | TC1 dropped as a *method* claim. Paper = TC3 (detectability map) + TC4 (benchmark); B-best reported as recommended practice |
| H3 ✘ | Error control is not claimed; report BY results; investigate the dependence |
| H1 ✔ only at W3–W4 | Contribution is a spectrometer-based verifier, **not** a phone-based one; reframe |

---

## 8. Ablations (pre-registered list)

1. Full − witness (→ joint lab-only model)
2. Full − swap hypotheses (value errors only)
3. Full − corruption library (swaps + "generic outlier" only)
4. Joint copula → independent marginals
5. Structured prior → uniform prior
6. Conformal BH → raw posterior threshold at 0.5
7. Witness-noise sweep ΔE₀₀ ∈ {0, 2, 4, 8}
8. Batch size n ∈ {6 … 96}
9. Prevalence ∈ {1, 5, 10}%
10. Library mismatch: test errors include an operator **not** in 𝒞 (robustness to unknown
    error types)

## 9. Systems metrics

Runtime per batch vs. n and |𝒞| (CPU, single thread), peak memory, and witness-model training
time. Target (not a hypothesis): < 1 s per batch of 24 on a laptop CPU.

---

## 10. Threats to validity (declared in advance)

- **Injected ≠ real errors.** T1 results support mechanism and relative ranking only;
  real-error performance needs T2.
- **W1 is optimistic.** Spectrometer colour has no capture noise or texture information. The
  ΔE sweep bounds the effect, and T2 is required.
- **OSSL is mostly US/Africa.** Transfer to Indian soils is untested.
- **Circularity risk.** B5 and the error injector share the same library; ablation 10 tests
  robustness to unknown types.
- **The copula model may be misspecified** for some properties (e.g. EC, P); check PIT
  histograms and report per-property calibration.

---

## 11. Formal literature search protocol (to run with institutional access)

- **Databases:** Scopus, Web of Science, IEEE Xplore, AGRIS, arXiv, Google Patents, Espacenet.
- **Query blocks** (combine with AND across blocks, OR within):
  - A (domain): soil OR "soil test*" OR "soil laborator*" OR "soil analys*"
  - B (task): error OR mix-up OR swap OR mislabel* OR verification OR validation OR
    plausibility OR "quality control" OR outlier
  - C (witness): image OR photo* OR smartphone OR camera OR colo?r OR spectr*
  - D (method, second pass without A): "conformal" AND ("outlier" OR "error detection") ;
    "sample swap" OR "sample mix-up" OR "wrong blood in tube"
- **Log** per query: database, date, exact string, hit count, number screened, included
  (template in `docs/search_log.csv`).
- **Inclusion:** any work that performs E1–E8 of doc 10 in any domain (for method prior art),
  or soil property estimation with uncertainty (for related work).
- The PRISMA-style flow numbers go in the paper's supplementary material.

---

## Amendments

_None yet._
