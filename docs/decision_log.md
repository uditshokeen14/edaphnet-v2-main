# Decision Log

Append-only. One entry per significant technical or research decision. Never edit past
entries; supersede them with a new entry.

Format: `D-### · date · decision · alternatives considered · reason · evidence tag · status`

---

**D-001 · 2026-09-23 · Build the backend before the frontend.**
Alternatives: frontend first; both in parallel.
Reason: the research contribution lives in the backend pipeline (models, uncertainty,
verification). The existing `app/static/index.html` is enough for demos until the API stabilises.
Evidence: n/a (planning). Status: active.

**D-002 · 2026-09-23 · Reframe the image's role from "predict lab chemistry" to "independent
evidence for verifying lab reports".**
Alternatives: predict pH/NPK from images.
Reason: RGB has no direct signal for pH, N, P, K or EC (README §25). Verification uses the image
for what it can plausibly measure. Image-based pH/NPK is kept as a hypothesis to falsify (H2).
Evidence: ASSUMED (physical argument); H2 to be tested. Status: active.

**D-003 · 2026-09-23 · Adopt the Research & Patent Charter (`08_research_and_patent_charter.md`).**
Includes evidence tags, the run-record standard, the stage-card requirement, and file-before-publish
for mechanisms M1–M4. Status: active.

**D-004 · 2026-09-23 · Rebuild from scratch around "weak-witness verification of soil lab
reports" (doc 09).**
Alternatives: image → property prediction (crowded, refs 1–9 in doc 09); per-value
predicted-interval validation (prior art: US 8,352,394); swap detection by matching (prior art:
Broman 2014).
Reason: the first prior-art search leaves only the weak-witness regime (joint batch error model,
error attribution, FDR control, detectability map) without an identified equivalent.
Evidence: prior-art v0 (web search only; items marked "verify" are open). Status: provisional;
freeze after the doc 09 §7 checks.

**D-005 · 2026-09-23 · Step 1 complete: narrow the novelty claim to TC1 (joint batch inference
with a weak witness), TC3 (detectability map) and TC4 (benchmark); treat E1/E6/E8 as prior-art
tools (doc 10).** Add Zhou et al. 2023 as required baseline B7.
**Use OSSL (CC-licensed KSSL/ICRAF/AfSIS subsets) as the T1 dataset with a witness-strength
ladder W0–W4.** Colour-from-spectra (W1) is an optimistic phone proxy; a real phone noise model
and real photos (T2) are still required. Evidence: prior-art v1 (targeted search). Status: active.

**D-006 · 2026-09-23 · Step 2: problem specification drafted (doc 11).**
Key choices: exact inference over a *structured* swap hypothesis set (identity, adjacent,
block-shift, pair) instead of all permutations; ≤1 corrupted cell per report; Gaussian-copula
witness model; conformal p-values + BH with BY as the conservative check (dependence caveat
declared); primary metric = power at FDR 0.10; decision rules for H1 success/failure fixed in
advance. Status: DRAFT until supervisor sign-off and registration.

**D-007 · 2026-09-23 · Step 3 design fixes found in smoke runs.**
(1) Conformal p-values cannot go below 1/(N_cal+1). BH is therefore applied per pool of 50
batches (~one lab-day), with 400 calibration batches per mode. (2) Clean-batch calibration showed
inflated FDR in smoke runs (clean reports that share a batch with an error get higher joint
scores; this is the dependence caveat in doc 11 §2.6). Added **injection-aware calibration**
(calibrate on clean reports inside injected batches) as a second mode, and both modes are
reported. Evidence: smoke runs only (tiny n). Status: active.

**D-008 · 2026-09-23 · Step 4a data audit (doc 12).** Use OSSL open-licence subsets; exclude
LUCAS (JRC licence). Fix the property set to the core 8, restricted to topsoil (<30 cm):
23,852 KSSL samples in 9,302 location groups. Drop available P (sparse, mixed methods); EC
secondary. Real data contains implausible values: a pre-declared physical-limits screen is used,
never our own detector (to avoid circularity). Limitation: USA only. Status: active.

**D-009 · 2026-09-24 · CORRECTION to D-008: the OSSL audit counted empty spectrum rows.**
The real coverage: core-8 + spectrum = 49 samples (unusable). Candidate datasets are
ICRAF-ISRIC (3,473 samples, 8 properties, CC-BY, available now) and LUCAS (~40k topsoil samples,
10 properties, JRC licence, free on request). KSSL Vis-NIR only has carbon/N/CaCO₃. The
property set in doc 11 §4 is re-opened. Status: awaiting user decision on the LUCAS licence request.

**D-010 · 2026-09-24 · Step 3 (T0) results (doc 13).** Full beats the best baseline by +0.12 to
+0.25 power at FDR 0.10 for moderate/strong witnesses, ≈0 for weak ones. H2 is refuted in T0
(the gain peaks at a moderate witness). The gain is almost entirely from swap detection; the
library mainly buys attribution (84–92% vs 32–50%). Clean calibration violates FDR, so
injection-aware calibration is adopted as the default. H6 is not supported. The research claim is
reframed from a "weak" to a "moderately informative" witness band. Evidence: MEASURED-SYNTHETIC.
Status: active.

**D-011 · 2026-09-25 · Step 4b on ICRAF-ISRIC (doc 14).** Proceed with ICRAF-ISRIC (open, 3,473
samples, 8 properties incl. Mg, no N, all depths); LUCAS to follow once the user obtains access.
Phone-noise sweep uses ΔE76 (Euclidean CIELAB) instead of ΔE00 (amends doc 11 §5; simpler, and
monotone in the same direction). Result: colour-only witness R² for OC 0.37 (0.30 at ΔE 4),
pH 0.27, texture/CEC/K ≤ 0.16, which is about T0 λ≈1. Full Vis-NIR ≈ T0 λ≈2. Expectation stated
before step 5: at most a modest gain for a colour-only witness. Status: active.

**D-012 · 2026-09-25 · Two bugs fixed in the step-5 runner before any full result was produced.**
(1) Out-of-memory on the 7.8 GB laptop: per-batch intermediates (hypothesis sets, likelihood
matrices) were kept for all 900 batches. The runner now keeps only kind/partner/operator and
writes results to disk after each setting. (2) Reproducibility: the per-setting seed used
Python's salted `hash()` of the rung name, so numbers changed between processes. It now uses
`zlib.crc32`, and two identical smoke runs are verified equal. Step 3 (T0) was not affected
(numeric seeds). The failed partial run was deleted. Status: fixed.

**D-013 · 2026-09-25 · Step 6 protocol drafted (doc 15) while step 5 runs.** 250–300 samples
(min 200) from ≥3 regions/≥30 fields; SHC panel + texture (+ CEC/Ca/Mg if affordable); 25% blind
duplicates + 10% second lab for real-error ground truth; ColorChecker + QR code in every photo;
2 phones × 2 lights × 2 moisture × 3 shots (minimum version: 3 images); photos blind to lab
results; swaps evaluated computationally on trusted pairs plus optional planted physical swaps.
Status: DRAFT, needs supervisor/ethics review and budget decisions.

**D-014 · 2026-09-25 · Step 5 go/no-go: NOT PASSED under the pre-registered rule (doc 17).**
Power at FDR 0.10 with a colour-only witness: +0.03/+0.05 (random), −0.05/−0.01 (clustered),
so the "phone photo enables verification at controlled FDR" claim is dropped in its current
form. Error control failed for most baselines (realised FDR 0.4–0.9); the post-hoc diagnosis is
profile shift between a small calibration pool (82 profiles) and the test pool (195). Secondary,
exploratory result: Full has the best AUPRC in all 14 rung × ordering cells (e.g. 0.43 vs 0.24 at
W1 ΔE0 random); attribution 89–98% vs 37–51% (H4 supported). Next: pre-register a calibration
amendment and test it only on independent data (LUCAS or step-6), never on the ICRAF test split.
Paper framing moves to working title B (doc 16). Status: active.

**D-015 · 2026-10-01 · Pre-registered amendment v2 (doc 18), committed before any evaluation on
new data.** New primary hypothesis A1: recall at a 5% re-test budget, Full vs best baseline, on
KSSL Vis-NIR (never used for evaluation), pass = ≥ +0.05 with the CI excluding 0 at W1 ΔE0 and ΔE2.
Secondary: A2 shift-aware calibration (weighted and Mondrian conformal), A3 attribution, A4
detectability table. The method code is frozen. Status: registered; supervisor review pending.

**D-016 · 2026-10-01 · Calibration diagnostic (run 20261001-233051_diag_calibration): the soil-shift
explanation is only partly supported.** Baselines B0/B2 show realised FDR 0.57/0.63 even when the
calibration and evaluation halves are exchangeable, so shift alone cannot explain the failure. New
hypothesis, recorded before re-running: in step 5, calibration batches reused the same samples
(511 distinct samples → 9,600 scores), so conformal p-values were computed as if from 9,600
independent nulls. This is anti-conservative (pseudo-replication; my experiment-design error).
Test: keep one score per distinct calibration sample and check whether FDR returns to ≈ q under
exchangeability. Status: testing.

**D-017 · 2026-10-01 · D-016 hypothesis confirmed (run 20261001-233621_diag_calibration).** One
score per distinct calibration sample restores FDR ≤ q under exchangeability (B0 0.57→0.00, B2
0.63→0.07), but with ~259 distinct samples power falls to ≈ 0 (the p-value floor of 1/260 is too
coarse for BH on 600-report pools). Findings: (1) the step-5 FDR failure was mainly my
calibration-design error (pseudo-replication), and doc 17 is corrected; (2) FDR control needs
thousands of distinct verified calibration reports; (3) Full remains shift-sensitive at W1 (FDR
0.39 after the fix). Amendment 1 to doc 18 (de-duplicated calibration) is registered before any
KSSL evaluation. Status: active.

**D-018 · 2026-10-01 · Exploratory detectability tables (doc 19).** On real ICRAF data, Full's
advantage is entirely in swaps (+0.14 to +0.27 within a 5% budget with a colour-only witness);
for value errors it is worse than the best per-type baseline (decimal −0.11 to −0.21).
Proposed future design: a combined re-test policy (joint model for swaps + a heavy-tailed value
checker). It is NOT applied now (the method is frozen for the KSSL test) and must be
pre-registered and tested on new data. Status: recorded.

**D-019 · 2026-10-02 · KSSL pre-registered test (doc 21): A1 FAILED** (+0.001 / +0.014 at W1 ΔE0 /
ΔE2, CIs include 0; best baseline B5 supervised). A1-c, A2 and A3 passed (A2 with ~0 power at
W0–W1; A3 only evaluable at W3). Secondary: with a spectrometer witness (W3), Full beats B5 by
+0.08–0.09 (CI > 0). The phone-based method claim is withdrawn; the paper uses the A1-fail framing.
Status: final for amendment v2.

**D-020 · 2026-10-02 · Exploratory analyses after the KSSL verdict (doc 23, in progress), and two
honesty corrections.** (1) Doc 21 now states that the analysis script was edited once (0fea0b0,
23:56) while the KSSL run was in progress, after testing it on two finished settings. The edit
concerned only the A3 "not evaluable" edge case; thresholds unchanged; final verdict unaffected.
(2) The progress report now notes that A2 passed with power ≈ 0 at colour settings. New
exploratory code (not part of any registered test): library-mismatch injector, swap/value and
ablation tables, BH pool-size rescoring. Status: analyses pending (laptop memory).

**D-021 · 2026-10-02 · Day-1 exploratory analyses complete (doc 23).** (1) Swap vs value: with a
phone-grade colour witness, Full finds +0.10 [+0.06, +0.14] more swaps and −0.08 [−0.12, −0.05]
fewer value errors than B5 (KSSL, random); the two cancel in the registered A1 metric. (2) The
library is a trade-off (values +0.02, swaps −0.07). (3) "Power ≈ 0" at colour settings is largely
mechanical: per-batch BH gives power 0.19–0.25 at realised FDR ≈ 0.10. (4) The pattern holds for
unknown error types (mismatch run, 1 seed). All exploratory; they motivate amendment v3 (doc 20),
which must be registered and tested on new data. Status: recorded.

**D-022 · 2026-10-02 · Day 2: paper draft v0 complete.** Title switched to the A1-fail framing
("When is a cheap witness enough?"). Results §7.1–7.8 (registered and exploratory clearly separated),
Discussion and limitations, Abstract, Conclusion; four figures generated from run records
(`scripts/make_paper_figures.py`); PDFs in `reports/`. Release tag v0.9-draft. Next: supervisor review.

**D-023 · 2026-10-03 · App layer started as a separate application (docs/24, `app/`).** Soil model,
multi-soil crop suitability (rule-based, FAO ECOCROP), leaf disease model (train PlantVillage, test
PlantDoc + own field photos), sourced knowledge base, one server + camera page. Not part of the
paper; research code unchanged. Old-project images excluded (contamination). Downloads await user
approval. Status: Step 0 done.

**D-024 · 2026-10-03 · App Step 2: crop suitability v1 (rule-based, FAO EcoCrop).** Trapezoid score
per factor, minimum over factors, limiting factor reported, multi-soil averaging with a worst case.
Sanity check found EcoCrop's global ranges too strict for some Indian practice (wheat, mustard on
alkaline soils), so sourced Indian overrides (`crops_local.json`, source and page enforced in code)
are required before the ranking is presented as validated. Status: v1 done; validation pending.

**D-025 · 2026-10-03 · Response to an external review of draft v0 (doc 26).** An AI-assisted review
(separate Claude session, obtained by the student) judged the paper publishable as a detectability
study after fixes. Done, all exploratory and not pre-registered: (1) gross-error diagnosis: a
modelling limitation, not a bug (Full misattributes gross errors to transposition/column swap and
does not use the OC ≤ total C constraint that B1/B5 exploit; identical 0.034 values are 7/208
counts); (2) error-mix sensitivity by re-ranking stored scores: with colour EdaphNet beats B5 from
60–70% swaps, with a spectrometer from 30%; (3) five-seed repeat of the unknown-error run (seeds
11–15; record marked exploratory because its config was uncommitted at start); (4) abstract and
text corrected (exploratory results marked; the "thousands of reports" claim replaced by the
p-value-floor argument; B5's power advantage with colour stated); method diagram; Figure 5 labels;
`scripts/download_ossl.py` and `REPRODUCE.md`. Method code unchanged (frozen at 095deaa).
Status: recorded.
