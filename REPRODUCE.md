# Reproducing the paper, from data download to every number

Every command below was used to produce a result in `docs/paper/draft_v0.md`. Run them from the
project folder with the **main Python** (it has numpy, pandas, scikit-learn, LightGBM, matplotlib):

```powershell
cd "D:\MY DATA\Downloads\new_to_do-main\edaphnet-v2"
$PY = "C:\Program Files\Python314\python.exe"
& $PY -m pip install -r requirements.txt
& $PY -m pytest -q                      # quick check that the code works
```

Times are for the original laptop (CPU only, 7.8 GB RAM). **Never run two experiments at once.**
Seeds are fixed: the same code and data give the same numbers. Every experiment writes a run folder
in `results/runs/` (configuration, code version, environment, results). The run folders used in the
paper are already in the repository, so steps 3–4 work without re-running steps 1–2.

## 1. Data (≈ 10 minutes, ≈ 200 MB)

```powershell
& $PY scripts/download_ossl.py          # 3 OSSL v1.2 files, MD5-verified against data/ossl_manifest_md5.txt
& $PY scripts/ossl_audit.py             # data audit (doc 12)
& $PY scripts/build_ossl_dataset.py --dataset ICRAF.ISRIC --props icraf8 --tag icraf8
& $PY scripts/build_ossl_dataset.py --dataset KSSL.SSL --props kssl3 --tag kssl3 --split-seed 20261001
& $PY scripts/fit_witness_ladder.py --tag icraf8     # colour / bands / spectrum witnesses (doc 14)
& $PY scripts/fit_witness_ladder.py --tag kssl3      # (doc 21, Figure 2 of the paper)
```

## 2. Experiments

| Paper section | Command | Run folder used in the paper | Time |
|---|---|---|---|
| §7.1 simulation | `& $PY scripts/run_sim.py --config configs/sim_t0.yaml` | `20260923-230637_sim_t0_d75f3b6` | ≈ 3.2 h |
| §7.3 ICRAF test | `& $PY scripts/run_real.py --config configs/real_icraf8.yaml` | `20260925-011337_real_icraf8_2be2820` | ≈ 4 h (incl. one resume) |
| §7.7 calibration diagnostic | `& $PY scripts/diag_calibration.py` | `20261001-233621_diag_calibration_f928f0e` (final of two) | minutes |
| §7.4 **pre-registered KSSL test** | `& $PY scripts/run_real.py --config configs/real_kssl3.yaml` | `20261001-234902_real_kssl3_095deaa` | ≈ 15 h wall clock |
| §7.6 unknown errors, 1 seed | `& $PY scripts/run_real.py --config configs/real_kssl3_mismatch.yaml` | `20261002-172716_real_kssl3_mismatch_7099ff1` | ≈ 10 min |
| §7.6 unknown errors, 5 seeds | `& $PY scripts/run_real.py --config configs/real_kssl3_mismatch5.yaml` | `20261003-154345_real_kssl3_mismatch5_d54e40c` | ≈ 50 min |

If a long run stops, continue it with `--resume results/runs/<run folder>` (identical numbers;
see `HOW_TO_RUN.md` §4).

## 3. Analyses (read the stored predictions; minutes each)

```powershell
$K = "results/runs/20261001-234902_real_kssl3_095deaa"
& $PY scripts/analyse_amendment.py $K            # §7.4 pre-registered verdict (A1, A1-c, A2, A3)
& $PY scripts/summarise_runs.py $K               # summary tables
& $PY scripts/detectability_table.py $K          # detectability by error type (doc 19)
& $PY scripts/exploratory_tables.py $K --ci      # §7.5 swaps vs values, ablations (doc 23)
& $PY scripts/rescore_pools.py $K --pools 1 5 10 50   # §7.7 power vs pool size
& $PY scripts/diag_gross.py $K                   # §7.5 gross-error diagnosis (doc 26)
& $PY scripts/error_mix.py $K                    # §7.9 error-mix sensitivity (doc 26), also draws Figure 6
& $PY scripts/exploratory_tables.py results/runs/20261003-154345_real_kssl3_mismatch5_d54e40c --ci   # §7.6, incl. by error type
```

Outputs of exploratory analyses go to `results/exploratory/<run folder>/`, never into the run folder.

## 4. Figures and PDF

```powershell
& $PY scripts/make_paper_figures.py              # Figures 1–5 -> docs/paper/figures/ (Figure 6: error_mix.py)
& $PY scripts/build_report_pdf.py --paper        # reports/EdaphNet_Paper_Draft_v0.pdf (needs Chrome or Edge)
```

Figure files keep their original names: `fig0_method.png` is Figure 1, `fig1_witness_r2.png` is
Figure 2, … , `fig5_error_mix.png` is Figure 6.

## What is not reproducible from this repository

- Nothing in the paper depends on the app layer (`app/`), the demos, or `data/app_raw/`.
- The decision log (`docs/decision_log.md`) and the git history record when each rule was fixed
  relative to the data it judged; that ordering cannot be re-created by re-running code.
