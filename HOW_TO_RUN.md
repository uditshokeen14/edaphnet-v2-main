# How to Run EdaphNet v2

All commands are for **PowerShell** or the **VS Code terminal** on Windows.

## 0. One-time setup

1. VS Code: **Ctrl+Shift+P → "Python: Select Interpreter" → Python 3.14**
   (`C:\Program Files\Python314\python.exe`, **not** the `.venv` one).
2. Open a terminal (**Terminal → New Terminal**) and run:

```powershell
cd "D:\MY DATA\Downloads\new_to_do-main\edaphnet-v2"
pip install -r requirements.txt
```

## 1. Check that everything works (≈ 10 seconds)

```powershell
python -m pytest -q
```
Expected: `34 passed, 1 deselected` (the slow resume test runs with `python -m pytest -m slow -o addopts=""`).

## 1b. Demo (≈ 10 seconds)

Checks one batch of real soil reports with two planted mistakes (a swap and a ×10 slip) and
shows which reports to re-test, why, and the suggested fix:

```powershell
python scripts/demo.py                    # colour witness (good phone)
python scripts/demo.py --witness W3       # spectrometer witness
python scripts/demo.py --seed 7           # another batch / other mistakes
```
Needs `data/processed/t1_kssl3.npz` and `witness_kssl3.npz` (rebuild: section 5 with `--dataset KSSL.SSL --props kssl3 --tag kssl3 --split-seed 20261001`).

## 1b-live. Live demo (photo + lab report -> result, runs the real model)

```powershell
python scripts/train_colour_brain.py      # one time only: builds models/ (about 1 minute)
python scripts/serve_demo.py              # then open http://localhost:8000
```
Pick a soil photo (or upload one with a colour card), edit the lab report (or press
"Make N x10" / "Report of a different soil"), and press **Run check**. The page shows:
1 colour correction, 2 what the colour predicts vs the report, 3 the report's rank in a batch of
12 real reports, and the final verdict. Stop the server with Ctrl+C.
Example photos are simulated from real KSSL soil colours (no real photos collected yet).
**Your own photo:** click "Upload your own photo…". With a colour card in the photo, click the card's
4 corners and then 2 corners of the soil. Without one, tick "My photo has no colour card" and click
2 corners of the soil only (the result is then marked as not reliable). Leave the lab report empty
to only predict OC, N and total C from the photo.

## 1c. Presentation page (for faculty / demos)

Open `demo_site\index.html` by double-clicking it. It works in any browser without internet
(fonts fall back to system fonts offline). It contains the problem, how it works, an interactive
batch checker on real KSSL reports, the result charts and the pre-registered verdicts.
Rebuild after new results: `python scripts/build_demo_page.py`.

## 1d. Field assistant app (leaf disease, soil photo, crops, report check)

Uses the main Python (it needs torch / torchvision / Pillow for the leaf model):

```powershell
$PY = "C:\Program Files\Python314\python.exe"
& $PY scripts/train_colour_brain.py       # one time: soil colour model (if models\ is empty)
& $PY scripts/app_leaf_features.py        # one time: leaf image features (~20 min, needs data\app_raw)
& $PY scripts/app_leaf_train.py           # one time: leaf model (~2 min) -> models\leaf_head.joblib
& $PY app/server.py                       # then open http://localhost:8001
```
Tabs: **Leaf** (photo → crop + disease or "not sure", with sourced management advice), **Soil
photo** (colour → OC / N / total C with ranges), **Crops** (pH, rainfall, temperature → ranked
crops; leave pH empty if unknown), **Check lab report** (photo + report → verdict).
**From a phone:** run `& $PY app/server.py --host 0.0.0.0`, connect the phone to the same Wi-Fi,
and open `http://<laptop IP>:8001` (find the IP with `ipconfig`). The photo buttons open the camera.
If Windows asks, allow Python through the firewall on private networks only.

## 1e. Streamlit dashboard & Cloud Deployment

To run the full Streamlit dashboard:

```powershell
streamlit run streamlit_app.py
```
Then open http://localhost:8501. For free 1-click cloud deployment on Streamlit Community Cloud, Hugging Face Spaces, or Render, see `DEPLOYMENT.md`.

## 2. Quick demo runs (≈ 1–3 minutes each, 10% of the data)

```powershell
# Step 3: synthetic data
python scripts/run_sim.py --config configs/sim_t0.yaml --smoke

# Step 5: real soil data (ICRAF-ISRIC)
python scripts/run_real.py --config configs/real_icraf8.yaml --smoke
```
Each output line shows:
- **power**: fraction of real errors caught (higher is better)
- **fdr**: fraction of flags that were false alarms (target ≤ 0.10)
- **best baseline**: the strongest existing method in that setting

## 3. See results

```powershell
python scripts/summarise_runs.py results/runs/20260923-230637_sim_t0_d75f3b6
```
Or open these in Excel from `results\runs\<run folder>\`:
`summary_by_method.csv`, `metrics_by_setting.csv`, `summary_attribution.csv`.

## 4. Full experiments (long; do not run two at once, the laptop has 7.8 GB RAM)

```powershell
python scripts/run_sim.py  --config configs/sim_t0.yaml        # ≈ 2.5 h
python scripts/run_real.py --config configs/real_icraf8.yaml   # ≈ 3 h
```
Seeds are fixed, so the same code and data give the same numbers.

**If a long run stops** (laptop slept, window closed, power cut), continue it without losing
finished settings. Use the run folder printed at the start of the run:

```powershell
python -u scripts/run_real.py --config configs/real_icraf8.yaml --resume results/runs/<run folder> >> results/real_icraf8_full.log 2>&1
```
The resumed run gives exactly the same numbers as an uninterrupted one (checked by
`python -m pytest -m slow -o addopts=""`). Resume refuses to start if the method code or configs
changed since the run began.

**Before a long run:** stop the laptop from sleeping while plugged in
(`powercfg /change standby-timeout-ac 0`) and keep the lid open. A locked screen is fine.

## 5. Rebuild the real dataset (only if `data\processed\` is missing)

```powershell
python scripts/ossl_audit.py
python scripts/build_ossl_dataset.py --dataset ICRAF.ISRIC --props icraf8 --tag icraf8
python scripts/fit_witness_ladder.py --tag icraf8
```
This needs the raw OSSL files in `data\raw\ossl\` (download links in `docs\12_data_audit_ossl.md`).

## 6. Read the findings

Open in VS Code and press **Ctrl+Shift+V** for a formatted view:
`docs\13_step3_simulation_results.md`, `docs\14_step4b_witness_ladder.md`, `docs\decision_log.md`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named ...` | run `pip install -r requirements.txt` again |
| `d:\MY : The term is not recognized` | VS Code is using the `.venv`; do step 0.1 |
| `MemoryError` | close other programs; never run two full experiments at once |
| `FileNotFoundError ... t1_icraf8.npz` | run section 5 |
