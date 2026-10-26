# EdaphNet v2: Checking Soil Lab Reports with a Photo

> **In one sentence:** soil lab reports sometimes contain mistakes (a sample mixed up with
> another, or a wrong number). This project tests whether a **cheap photo of the same soil
> sample** can help **find those mistakes, explain them and suggest the fix**, while keeping
> false alarms under control.

**Goal of the project:** a research paper (and possibly a patent later). A working app comes
last, and only if the method is proven to work.

**Last updated:** 2026-10-02

---

## 1. The problem, in simple words

A farmer sends soil to a lab and receives a report (pH, organic carbon, potassium, ...). The
report can be wrong in two ways:

| Type of mistake | Example |
|---|---|
| **Swap**: the report belongs to a *different* sample | Tray positions 7 and 8 were mixed up, so farmer A gets farmer B's results |
| **Wrong value**: one number is wrong | pH typed as **68** instead of **6.8**; potassium in the wrong unit; digits swapped (0.16 → 0.61); two columns swapped |

Nobody checks this for the farmer, and re-testing everything is too expensive.

**Our idea:** a photo of the soil is an independent "witness". The photo cannot change when the
lab makes a typing mistake. If the report says "very high organic carbon" but the photo shows a
pale soil, something is probably wrong. The method looks at **the whole lab batch at once**
(usually 24 samples), so it can also tell *which two samples were swapped*.

---

## 2. Progress at a glance

| Step | What | Status |
|---|---|---|
| 1 | Search papers, patents and products (what already exists?) | ✅ Done |
| 2 | Write the exact problem, method and hypotheses | ✅ Drafted (needs supervisor sign-off) |
| 3 | Test the method on synthetic data | ✅ Done |
| 4a | Download and check real soil data (OSSL) | ✅ Done (with a corrected mistake, see §5) |
| 4b | Measure how much soil colour reveals, on real data | ✅ Done |
| 5 | **Go/no-go test on real data** | ✅ Done: **did not pass** the pre-registered rule (see below) |
| 6 | Collect our own photos + lab reports | 📝 Protocol written; waiting for decisions |
| 5b | **Diagnose the step-5 failure + new pre-registered plan** | ✅ Done (cause found: my calibration design error) |
| 5c | **Pre-registered test on new data (KSSL)** | ✅ Done: main claim **failed** with a colour witness; wins with a spectrometer (`docs/21`) |
| 7 | Backend / app | ⏸ Only if step 5 passes |
| 8 | Write the paper | 📝 **Full draft v0** (`docs/paper/draft_v0.md`, PDF in `reports/`), tagged `v0.9-draft` |

---

## 3. What was done in each step (details)

### Step 1: What already exists? (`docs/09`, `docs/10`)

We searched papers, patents and products. **Most of the individual ideas already exist:**

| Idea | Already done by |
|---|---|
| Predicting soil properties from phone photos | Many papers (organic carbon, texture, colour), the LandPKS app |
| Checking a lab value against a predicted value | A patent from 2008 (Rockwell, paper industry) |
| Finding mixed-up samples by matching two kinds of data | Genetics research (Broman 2014) |
| Finding wrong numbers with a model | Zhou et al. 2023 (cleanlab) |
| Hospital-lab checks for mixed-up blood samples | Clinical lab research |
| Statistical control of false alarms | Standard statistics (Benjamini–Hochberg, conformal p-values) |

**What we did not find anywhere (our possible contribution):**
1. One model that finds **swaps and wrong values together across a whole batch**, using a
   **cheap photo** as the witness.
2. A **"detectability map"**: which mistakes can be found with how good a photo.
3. A **public benchmark** (test dataset) of soil lab reports with real errors.

We also found evidence that the problem is real: in one study of 8 labs, 28% of soil-carbon
results were outside the accepted range.

### Step 2: The exact plan (`docs/11`)

- A statistical model of how mistakes happen: swaps (neighbours, shifted rows, random pairs)
  and 9 kinds of wrong values (×10, ÷10, unit mix-ups, digit swaps, column swaps, big lab errors).
- 7 baselines (existing methods) to beat, plus a rule-based comparison:

| ID | Baseline |
|---|---|
| B0 | Simple range checks |
| B1 | Soil-science consistency rules |
| B2 | Lab-data-only statistical check (no photo) |
| B3 | Check each value against the photo separately |
| B4 | Swap-only matching (like the genetics method) |
| B5 | A machine-learning classifier trained on examples of errors |
| B7 | cleanlab (Zhou et al. 2023), the closest existing method |
| B6 | Rule-based unit/decimal repair (used to compare error *explanations*, not detection) |

- 6 hypotheses, each with a pass/fail rule decided **before** seeing results.
- Main score: **power** = share of real mistakes caught while **false alarms stay ≤ 10%**.

### Step 3: Test on synthetic data (`docs/13`)

We simulated soil samples, photos of varying quality, lab batches and injected mistakes
(3 seeds × 2 batch types × 5 photo qualities).

| Photo quality (how much it reveals about organic carbon) | Our method catches | Best existing method catches |
|---|---|---|
| None / weak (0–14%) | 25–28% | 24–27% → **no real gain** |
| Moderate (37%) | 32–39% | 27–28% |
| **Good (66%)** | **51–65%** | 31–42% → **+20 to +25 points** |
| Strong (83%) | 73–78% | 55–66% |

**What we learned:**
- ✅ The method **clearly wins when the photo is moderately informative**, but **not when the
  photo is weak**. Our original idea ("even a weak photo is enough") was **wrong** and was
  changed. This is an honest, recorded change of claim.
- ✅ Almost all of the gain comes from **finding swaps**.
- ✅ It **explains** mistakes well: the right error type 84–92% of the time (rules: 32–50%), and
  the right swap partner 89–98% of the time with a good photo.
- ⚠️ False-alarm control needed a fix (**"injection-aware calibration"**). Without it, false
  alarms reached 18%. With it, they mostly stay near 10%, but this still needs a larger test.
- ❌ One design idea (a special prior for swap patterns) gave no benefit.

*These are synthetic results: they show the idea can work, not that it works on real soil.*

### Step 4a: Real soil data (`docs/12`)

- Downloaded the **Open Soil Spectral Library (OSSL)**: lab results plus light spectra
  (visible and near-infrared) of real soil samples.
- Only openly licensed data is used. LUCAS (Europe) is excluded for now because its licence
  needs a request.
- ⚠️ **Mistake found and corrected:** the first count said 23,852 usable samples. It had
  counted empty spectrum rows. The true number with all needed values was **49**. The mistake,
  the correction and the reason are all recorded in `docs/12` §7 and `docs/decision_log.md` (D-009).
- Chosen instead: **ICRAF-ISRIC**, 3,473 real soil samples from 553 soil profiles worldwide,
  with pH, organic carbon, clay, sand, CEC, K, Ca and Mg.

### Step 4b: How much does soil colour reveal? (`docs/14`)

From each sample's spectrum we computed the **colour a camera would see** (CIELAB), then added
phone-like colour noise (ΔE 0, 2, 4, 8). Share of each property explained, on unseen soil profiles:

| Witness | Organic carbon | pH | Ca | Clay | CEC | K | Sand |
|---|---|---|---|---|---|---|---|
| Colour, perfect | **37%** | 27% | 23% | 16% | 11% | 7% | 2% |
| Colour, good phone (ΔE 2) | **35%** | 15% | 13% | 7% | 5% | ~0 | ~0 |
| Colour, poor phone (ΔE 8) | **25%** | ~0 | ~0 | ~0 | ~0 | ~0 | ~0 |
| Full spectrometer | 60% | 62% | 65% | 66% | 63% | 39% | 46% |

**Meaning:** colour reliably tells us about **organic carbon**, a little about pH and calcium,
and almost nothing about texture or potassium. Compared with step 3, a colour-only photo sits at
the **low end** of the range where our method helps, so we expect **at most a modest gain** from a
phone. We wrote this down *before* running step 5.

### Step 5: Go/no-go test on real data (`docs/17`)

Real lab values + real witnesses + injected mistakes; our method vs all baselines;
7 witness levels × 2 batch types × 3 seeds = 42 settings (all finished).

**Result under the rule we fixed in advance: NOT PASSED.**

| What we measured | Result |
|---|---|
| Mistakes caught at 10% false alarms, colour-only photo | Small gain in random batches (+3 to +5 points), **no gain or worse** in clustered batches → the "phone photo" claim is **dropped** in its current form |
| False-alarm control | **Broke for almost all methods** (baselines had 40–90% false alarms). Ours stayed near 10% but not always within the limit |
| Ranking of suspicious reports (AUPRC, a secondary measure) | **Ours is best in every setting and every seed**; with colour only it is about **2× better** (0.43 vs 0.24) in random batches |
| Explaining the mistake | Right error type **89–98%** of the time (rules: 37–51%) |

**Why false alarms broke:** the calibration data came from only 82 soil profiles and the test
data from 195 different ones. Test soils that looked unusual compared with the calibration soils
were flagged even when their reports were correct. This is a real, useful finding: **checking
lab reports needs calibration data that covers the soils being tested.**

**What we must not do:** fix this and re-test on the same data. Any fix must be written down
first and tested on **new** data (LUCAS or our own step-6 data).

### Step 5b: Why step 5 failed, and the new plan (`docs/17` correction, `docs/18`, `docs/19`)

- **The real cause of the false-alarm problem was a mistake in my experiment design:** the same
  calibration soils were reused hundreds of times and each copy was counted as new evidence. Fixing
  this (one score per soil) brought false alarms for the existing methods from 57–63% down to
  0–7%. But with only ~260 calibration soils almost nothing can be flagged, so **a lab needs
  thousands of verified past reports** to set a reliable alarm line.
- **New goal, written down before testing (`docs/18`):** "if a lab re-tests the top 5% most
  suspicious reports, does our method find more mistakes?" Pass rule: at least +5 points over the
  best existing method, clearly above zero, with a colour-only photo.
- **Which mistakes can be found (`docs/19`, exploratory):** our method's advantage is **finding
  swapped samples** (+14 to +27 points with colour). For single wrong values (like ×10), a
  simple range check is better. Next design idea: combine both (to be tested on new data).

### Step 5c: Test on new data (KSSL, `docs/21`)

- 19,746 real US soil samples (organic carbon, nitrogen, total carbon) from 6,999 locations,
  never used before. Colour explains 72% of organic carbon here (37% on ICRAF), so this is a
  **colour-friendly** test: a pass would not prove the method works for pH or nutrients.
- **Result (rules fixed in advance):** with a phone-grade colour photo, re-testing the top 5% found
  about the same number of mistakes as the best existing method (+0.1 to +1.4 points, not
  significant) → **main claim failed**. With a spectrometer, our method found **+8 to +9 points
  more** (significant). False alarms were under control for all methods once calibration was
  done correctly, and error explanations were 97–100% correct (vs 24–29% for rules).
- **Try it:** `python scripts/demo.py` and `python scripts/demo.py --witness W3`.

### Step 6: Plan for collecting our own data (`docs/15`, `templates/`)

- 250–300 soil samples (minimum 200) from at least 3 regions and 30 fields (Indian soils).
- Lab tests: Soil Health Card set (pH, EC, OC, N, P, K) + texture (+ CEC, Ca, Mg if affordable).
- **25% of samples sent twice under secret codes** (and 10% to a second lab) to catch *real* lab mistakes.
- Photos: colour card and QR code in every picture, phone on a stand, 2 phones, 2 lighting
  conditions, dry and moist. A cheap minimum version is 1 phone and 3 photos per sample.
- Excel templates in `templates/` for the sample log, photo log, lab results (typed twice by two
  people) and the private duplicate key.

---

## 4. Main findings so far (honest summary)

1. **Most individual techniques already exist.** The possible novelty is the *combination
   inside one batch model* plus the detectability map and the benchmark.
2. **In simulation, the method beats all baselines, but only with a moderately informative photo.**
3. **On real data, soil colour mainly reveals organic carbon.**
4. **Step 5 did not pass the pre-registered test.** A phone-grade photo did not give a clear
   gain at a controlled false-alarm rate.
5. **But the detector itself is strong:** it ranks suspicious reports far better than every
   existing method and explains mistakes correctly. The weak point is turning scores into
   trustworthy alarms when the soils differ from the calibration soils, and that breaks *every*
   method.
6. **The method's strongest point is finding and explaining swaps**, not single wrong values.

## 5. Mistakes we made and corrected (kept on record on purpose)

| # | Mistake | Fix | Where |
|---|---|---|---|
| 1 | Data count included empty spectrum rows (23,852 instead of 49) | Recounted; changed dataset to ICRAF-ISRIC | `docs/12` §7, D-009 |
| 2 | Hypothesis H2 ("weak photo is enough") | Refuted by step 3; claim reframed | `docs/13`, D-010 |
| 3 | Step-5 run used too much memory | Lean runner that saves after each setting | D-012 |
| 4 | Random seed changed between runs | Stable seed; reproducibility verified | D-012 |

---

## 6. Folder guide

```
edaphnet-v2/
├── README.md            ← this file
├── HOW_TO_RUN.md        ← step-by-step commands to run everything yourself
├── docs/                ← all research documents (read these for details)
│   ├── 08_research_and_patent_charter.md   rules: honesty, evidence labels, tracking
│   ├── 09_prior_art_and_research_design.md step 1: what exists, research design
│   ├── 10_prior_art_matrix_v1.md           step 1: detailed comparison with 16 prior works
│   ├── 11_problem_specification.md         step 2: exact method + hypotheses
│   ├── 12_data_audit_ossl.md               step 4a: real data audit (+ correction)
│   ├── 13_step3_simulation_results.md      step 3: results
│   ├── 14_step4b_witness_ladder.md         step 4b: results
│   ├── 15_step6_real_data_protocol.md      step 6: data collection plan
│   ├── decision_log.md                     every decision and why (D-001 … D-013)
│   ├── search_log.csv                      literature search log (to be completed)
│   └── invention_log.md                    private (not in git)
├── src/edaphnet2/       ← the research code (the method, baselines, statistics)
├── scripts/             ← programs that run experiments and build data
├── configs/             ← settings for each experiment
├── tests/               ← automatic checks (16 tests)
├── templates/           ← Excel templates for step 6 data collection
├── data/                ← raw and processed data (large files not in git)
│   └── preview/         ← small CSV copies you can open in Excel
└── results/runs/        ← one folder per experiment run, with all numbers
```

**Key code files**

| File | What it does |
|---|---|
| `src/edaphnet2/inference.py` | **The method**: joint batch model for swaps + wrong values |
| `src/edaphnet2/operators.py` | The list of mistake types (×10, units, digit swaps, ...) |
| `src/edaphnet2/swaps.py` | The kinds of sample swaps considered |
| `src/edaphnet2/baselines.py` | The existing methods we compare against |
| `src/edaphnet2/conformal.py` | False-alarm control (conformal p-values, Benjamini–Hochberg) |
| `src/edaphnet2/real_data.py` | Real soil data: colour from spectra, transforms, data checks |
| `scripts/run_sim.py` | Step 3 experiment (synthetic) |
| `scripts/run_real.py` | Step 5 experiment (real data) |
| `scripts/summarise_runs.py` | Turns a run into summary tables |

---

## 7. How to run it

**Reproduce the paper from scratch:** see **`REPRODUCE.md`** (data download → every table and figure).
**What to do next:** see **`HANDOVER.md`** (step-by-step list of the remaining manual tasks).
**What every file is:** see **`FILE_GUIDE.md`**.

**Presentation page:** open `demo_site/index.html` in a browser (interactive demo + results).

**Live demo (photo + report → result):** `python scripts/train_colour_brain.py` once, then `python scripts/serve_demo.py` and open http://localhost:8000.


See **`HOW_TO_RUN.md`**. Short version:

```powershell
cd "D:\MY DATA\Downloads\new_to_do-main\edaphnet-v2"
pip install -r requirements.txt
python -m pytest -q                                                   # 34 passed
python scripts/run_real.py --config configs/real_icraf8.yaml --smoke  # quick demo
```

---

## 8. What is needed from you

1. **Supervisor review** of `docs/11` (the plan and pass/fail rules).
2. **LUCAS data request** (free): https://esdac.jrc.ec.europa.eu/content/lucas2015-topsoil-data.
   It gives about 40,000 European soil samples for a larger test.
3. **Formal literature search** in Scopus or Web of Science through your university (record it
   in `docs/search_log.csv`).
4. **Step 6 decisions:** budget, regions, lab, and the photo protocol version (`docs/15` §11).

## 9. Next steps

1. **Write down (pre-register) a calibration fix** (e.g. group-aware or weighted conformal
   calibration, bigger and more diverse calibration pool) *before* testing it.
2. Test it **only on new data**: LUCAS (needs your access request) or our own step-6 data.
3. Detectability map analysis (which mistakes can be found with which photo quality).
4. Start step 6 data collection after approval.
5. Paper skeleton (step 8), linking each section to these documents and results.

## 10. Research integrity rules we follow

- No number is reported unless a script produced it and a run record exists.
- Negative results and our own mistakes are kept and reported, not deleted.
- Each result is labelled: synthetic, real data + injected errors, or real errors.
- Pass/fail rules are written **before** running the experiment.

---

## Data sources, licences and attribution

| Data | Source | Licence | Use here |
|---|---|---|---|
| ICRAF-ISRIC soil spectral library | via Open Soil Spectral Library (OSSL) v1.2, Soil Spectroscopy for Global Good | CC-BY 4.0 | step 4b/5 experiments |
| USDA NRCS KSSL Vis-NIR library | via OSSL v1.2 | CC-BY 4.0 | amendment-v2 test |
| LUCAS topsoil | ESDAC / JRC | JRC licence agreement | **not used**; excluded until access is granted |

Please cite the Open Soil Spectral Library (Safanelli et al. 2025, *PLOS One*,
https://doi.org/10.1371/journal.pone.0296545) and the original dataset providers (ICRAF/ISRIC,
USDA NRCS KSSL) when using derived files. Raw OSSL files are not redistributed; scripts
download-free rebuild everything from the OSSL files listed in `data/ossl_manifest_md5.txt`.
Processed files (`data/processed/`) are reproducible with `HOW_TO_RUN.md` §5 and are no longer
tracked in git (two early ICRAF-derived files remain in the commit history, shared under CC-BY
with the attribution above).
