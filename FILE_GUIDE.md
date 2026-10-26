# File guide: every file in EdaphNet v2, what is in it and what it is for

Written 3 October 2026. **Role** tells you where each file belongs:
**Paper** = used for the paper's results · **Record** = documents what was decided or found ·
**Demo** = for showing the project · **App** = the separate farmer app (not in the paper) ·
**Future** = for paper 2 (real photos) · **Tool** = helper.

Start with: `README.md` (overview) → `HANDOVER.md` (what to do next) → `docs/paper/draft_v0.md` (the paper).

---

## Top-level files

| File | What it is | Role |
|---|---|---|
| `README.md` | Project overview in simple words: problem, progress, findings, mistakes corrected, folder guide, data licences | Record |
| `HANDOVER.md` | Step-by-step list of everything left to do (guide meeting, search, citations, IP, Zenodo, submission) | Record |
| `REPRODUCE.md` | Exact commands from data download to every table and figure in the paper | Paper |
| `HOW_TO_RUN.md` | How to install, test, run demos and experiments, with troubleshooting | Tool |
| `FILE_GUIDE.md` | This file | Record |
| `requirements.txt` | Python packages needed | Tool |
| `pytest.ini` | Test settings (the slow resume test is skipped by default) | Tool |
| `pyrefly.toml` | Tells the VS Code type checker where the code is | Tool |
| `.gitignore` | Keeps big or private files off GitHub (raw data, models, app images, `invention_log.md`) | Tool |
| `.gitattributes` | Line-ending rules for git | Tool |

## `src/edaphnet2/`: the research method (frozen at commit 095deaa)

| File | What it does | Role |
|---|---|---|
| `inference.py` | **The method.** Scores a whole batch of reports under swap hypotheses × error types; gives each report a suspicion score, an explanation and a correction | Paper |
| `operators.py` | The error library: ×10, ÷10, unit confusion, digit transposition, column swap, gross error; also injects random errors for tests | Paper |
| `swaps.py` | Swap patterns: neighbour swaps, tray shifts (rotations), random pairs | Paper |
| `witness.py` | Witness models: predict each sample's properties (with uncertainty) from colour or spectrum | Paper |
| `baselines.py` | The 7 comparison methods B0–B7 (range checks, rules, lab-only model, witness interval, swap matcher, supervised classifier, cleanlab) | Paper |
| `conformal.py` | Conformal p-values and Benjamini–Hochberg false-alarm control | Paper |
| `metrics.py` | Evaluation: errors found at a 5% re-test budget, power, FDR, per pool of 50 batches | Paper |
| `space.py` | How each property is stored and printed (decimals, log/logit scale) for synthetic and real data | Paper |
| `real_data.py` | Loads OSSL data; property sets (ICRAF 8 properties, KSSL 3); colour (CIELAB) from spectra | Paper |
| `properties.py` | Soil properties for the synthetic (T0) data | Paper |
| `simulate.py` | Synthetic data generator: soils, weak witness, lab batches, error injection | Paper |
| `tracking.py` | Run records: config, code version, environment, timing for every experiment | Paper |
| `phone.py` | Real-photo processing: colour-card correction, true soil colour, blur/exposure checks, texture | Future / Demo |

## `scripts/`: programs you run

**Experiments and data (Paper)**

| File | What it does |
|---|---|
| `download_ossl.py` | Downloads the 3 OSSL data files and checks their MD5 checksums |
| `ossl_audit.py` | Audits the OSSL data: what is usable, licences, coverage (doc 12) |
| `build_ossl_dataset.py` | Builds the clean ICRAF and KSSL datasets with location-disjoint splits |
| `fit_witness_ladder.py` | Fits colour / bands / spectrum witnesses and measures how much each reveals (R²) |
| `run_sim.py` | Runs the synthetic experiment (doc 13) |
| `run_real.py` | Runs the real-data experiments (ICRAF, KSSL, unknown errors); resumable |
| `mismatch_ops.py` | Error types the method does *not* know (×100, gross ×4–8, neighbour copy, dropped digit), used by `run_real.py` |
| `diag_calibration.py` | Diagnoses the calibration mistake (pseudo-replication) |

**Analyses (Paper)**

| File | What it does |
|---|---|
| `analyse_amendment.py` | Applies the pre-registered pass/fail rules to the KSSL run (doc 21) |
| `summarise_runs.py` | Summary tables from a run folder |
| `detectability_table.py` | Which error types each witness makes findable (doc 19) |
| `exploratory_tables.py` | Swaps vs values, ablations, with bootstrap intervals (doc 23) |
| `rescore_pools.py` | False-alarm control vs pool size (doc 23 §3, Figure 5) |
| `diag_gross.py` | Why gross errors are rarely found (doc 26 §1) |
| `error_mix.py` | Who wins as the share of swaps changes; draws Figure 6 (doc 26 §2) |
| `make_paper_figures.py` | Draws paper Figures 1–5 from the run records |
| `build_report_pdf.py` | Builds the progress-report PDF, or the paper PDF with `--paper` |

**Demos (Demo)**

| File | What it does |
|---|---|
| `demo.py` | Command-line demo: one batch with a planted swap and ×10 error |
| `serve_demo.py` | Live demo server for `demo_site/live.html` (photo + report → result) |
| `build_demo_page.py` | Builds the offline presentation page `demo_site/index.html` (and `web.html`) |
| `train_colour_brain.py` | Trains the colour → OC/N/total C model used by the live demo |

**Real photos, step 6 (Future)**

| File | What it does |
|---|---|
| `process_photos.py` | Turns a folder of soil photos (with colour card) into witness features, following doc 15 |

**App (App)**

| File | What it does |
|---|---|
| `app_build_crops.py` | Builds `app/knowledge/crops.json` from FAO EcoCrop |
| `app_crop_advice.py` | Crop suggestions from the command line |
| `app_audit_images.py` | Audits PlantVillage / PlantDoc images (duplicates, label conflicts) |
| `app_leaf_features.py` | Extracts leaf-image features with MobileNetV3 |
| `app_leaf_train.py` | Trains and tests the leaf-disease model (not run yet) |

## `configs/`: experiment settings (Paper)

| File | Experiment |
|---|---|
| `sim_t0.yaml` | Synthetic experiment |
| `real_icraf8.yaml` | First real-data test (ICRAF) |
| `real_kssl3.yaml` | **The pre-registered KSSL test** |
| `real_kssl3_mismatch.yaml` | Unknown-error test, 1 seed |
| `real_kssl3_mismatch5.yaml` | Unknown-error test, 5 seeds |

## `tests/`: automatic checks (34 tests)

| File | Checks |
|---|---|
| `test_core.py` | The method, error library, swaps, conformal control, metrics |
| `test_real_data.py` | Real-data loading, transforms, colour from spectra |
| `test_resume.py` | A resumed run gives identical numbers (slow; run separately) |
| `test_phone.py`, `test_process_photos.py` | Photo processing (colour card, quality checks) |
| `test_app_crop.py`, `test_app_server.py` | App: crop scoring, disease knowledge sources, server endpoints |

## `docs/`: written records

| File | What it is | Role |
|---|---|---|
| `08_research_and_patent_charter.md` | Goals and integrity rules for the research and possible patent | Record |
| `09_prior_art_and_research_design.md` | What already exists (papers, patents, products) and the research design | Record |
| `10_prior_art_matrix_v1.md` | Table comparing prior work with this project | Record |
| `11_problem_specification.md` | The formal plan: model, error types, baselines, hypotheses, pass/fail rules (pre-registered v1) | Paper |
| `12_data_audit_ossl.md` | OSSL data audit, with a corrected counting mistake | Paper |
| `13_step3_simulation_results.md` | Simulation results | Paper |
| `14_step4b_witness_ladder.md` | How much colour reveals on real soils | Paper |
| `15_step6_real_data_protocol.md` | Protocol for collecting real photos and lab reports, blind duplicates | Future |
| `16_paper_skeleton.md` | Early outline of the paper | Record |
| `17_step5_results.md` | First real-data test (failed; with correction note) | Paper |
| `18_preregistered_amendment_v2.md` | The pre-registered rules for the KSSL test | Paper |
| `19_detectability_findings.md` | Which errors each witness can find | Paper |
| `20_amendment_v3_DRAFT.md` | Draft plan for the next registered test (combined policy) | Future |
| `21_kssl_preregistered_results.md` | **The pre-registered KSSL verdict** | Paper |
| `22_progress_report.md` | Plain-language progress report (source of the progress PDF) | Record |
| `23_exploratory_after_kssl.md` | Exploratory analyses: swaps vs values, ablations, pool size, unknown errors | Paper |
| `24_app_design.md` | App design and methods | App |
| `25_app_data_audit.md` | App data audit (PlantVillage, PlantDoc, EcoCrop) | App |
| `26_review_fixes.md` | Analyses after the external review: gross errors, error mix, 5 seeds | Paper |
| `decision_log.md` | Every decision D-001 … D-025, dated, with reasons | Record |
| `search_log.csv` | Literature-search log (the formal Scopus/WoS search still has to be added) | Record |
| `paper/draft_v0.md` | **The paper** | Paper |
| `paper/figures/fig0…fig5.png` | Paper Figures 1–6 (file numbers are one lower than figure numbers) | Paper |
| `invention_log.md` | Invention notes (on your computer only, never on GitHub) | Record |

## `results/`: outputs

| Path | What it holds | Role |
|---|---|---|
| `runs/<date>_<name>_<commit>/` | One folder per experiment: `config.json`, `provenance.json` (code version), `metrics_by_setting.csv`, `attribution_by_setting.csv`; `predictions.csv.gz` stays on your computer (too big for GitHub) | Paper |
| `runs/20261001-234902_real_kssl3_095deaa/` | **The pre-registered KSSL test**, incl. `amendment_verdict.json` | Paper |
| `exploratory/<run>/` | Exploratory tables (swap/value, pool size, gross errors, error mix) | Paper |
| `data_audit/` | OSSL audit outputs and dataset build summaries | Paper |
| `*.log`, `logs/` | Console logs of the long runs | Record |
| `colour_brain_report.json` | Accuracy of the live demo's colour model | Demo |
| `app_audit/` | App image-audit outputs and the leaf feature log | App |

## `data/`

| Path | What it holds | On GitHub? |
|---|---|---|
| `ossl_manifest_md5.txt` | Checksums of the 3 OSSL files | yes |
| `splits/t1_*_split.csv.gz` | Which sample is in train / calibration / test (location-disjoint) | yes |
| `raw/ossl/` | The 3 OSSL data files (≈ 200 MB); get them with `download_ossl.py` | no |
| `processed/` | Clean datasets and witness predictions (`t1_*.npz`, `witness_*.npz`) | no |
| `app_raw/` | PlantVillage, PlantDoc, EcoCrop and leaf features (app only) | no |

`models/` (on your computer only): the live demo's colour models; the leaf model once trained.

## `reports/`: PDFs to share

| File | What it is |
|---|---|
| `EdaphNet_Paper_Draft_v0.pdf` / `.html` | The paper as PDF |
| `EdaphNet_Faculty_Discussion.pdf` / `.html` | Status, problems and decisions, for your guide |
| `EdaphNet_Progress_Report.pdf` / `.html` | Earlier progress report (2 October) |

## `demo_site/`: pages for presenting (Demo)

| File | What it is | How to open |
|---|---|---|
| `index.html` | Offline presentation page: problem, method, interactive batch checker, result charts, verdicts | Double-click |
| `web.html` | Same page, version used for the shareable web link | Double-click |
| `template.html` | Template that `build_demo_page.py` fills in | (not opened directly) |
| `live.html` | **Live demo** with animations and Guided demo (photo + report → result) | `python scripts/serve_demo.py`, then http://localhost:8000 |

## `templates/`: data-collection sheets for step 6 (Future)

| File | What it is |
|---|---|
| `sample_log.csv` | One row per soil sample collected |
| `capture_log.csv` | One row per photo (phone, light, moisture) |
| `lab_results.csv` | Lab values per sample |
| `duplicate_key.csv` | Secret key linking blind duplicates (keep away from the lab) |
| `README.md` | How to fill them in |

## `app/`: the farmer app (App, not in the paper)

| File | What it is |
|---|---|
| `server.py` | One backend: leaf, soil, crops, report check (`python app/server.py` → http://localhost:8001) |
| `web/index.html` | The app page: 4 tabs, phone camera |
| `crop/suitability.py` | Crop scoring from pH, rainfall, temperature, texture (FAO EcoCrop rules) |
| `leaf/model.py` | Leaf-disease model (MobileNetV3 features + classifier, "not sure" rule) |
| `leaf/class_map.json` | PlantDoc → PlantVillage class mapping |
| `knowledge/crops.json` | Requirements of 25 Indian crops (FAO EcoCrop) |
| `knowledge/crops_local.json` | Indian overrides (empty; each needs a source and page) |
| `knowledge/diseases.json` | Cause and management for 26 diseases/pests, each with a source URL |
| `knowledge/SOURCES.md` | Where every app value comes from |
| `README.md` files | Status of each part |
