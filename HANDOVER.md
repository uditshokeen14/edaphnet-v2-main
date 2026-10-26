# EdaphNet: what to do next (without Claude)

Written 3 October 2026. This file lists everything left to do, in order, with exact steps.
Nothing here needs an AI assistant. Tick items off as you go.

---

## Where the project stands

- **Research: complete as a first study.** Pre-registered KSSL test done (doc 21): main claim A1
  failed; A1-c, A2, A3 passed. Exploratory analyses in docs 23 and 26.
- **Paper: draft v0.2** in `docs/paper/draft_v0.md` (PDF: `reports/EdaphNet_Paper_Draft_v0.pdf`).
  All review fixes that need code are done (doc 26, decision D-025).
- **Faculty report:** `reports/EdaphNet_Faculty_Discussion.pdf`.
- **Demo for presentations:** `python scripts/serve_demo.py`, then open http://localhost:8000 and
  press **Guided demo**.
- **App layer** (`app/`): separate from the paper. The leaf model is not trained yet (step 9 below).

The paper's one question: *when is a cheap check of a soil sample good enough to catch mistakes in
its lab report?* Main results: colour catches swaps (+0.10) but loses wrong values (−0.08); a
spectrometer wins overall (+0.09); the method names the right error type 97–100% (spectrometer);
who wins depends on the error mix (colour wins from 60–70% swaps); calibration-sample reuse
silently breaks false-alarm control.

---

## 1. Save everything to GitHub (5 minutes)

```powershell
cd "D:\MY DATA\Downloads\new_to_do-main\edaphnet-v2"
git status
git add -A
git commit -m "Review fixes: gross-error diagnosis, error-mix figure, 5-seed run, abstract, method diagram, reproduce guide (D-025)"
git push origin main
```
If GitHub asks you to log in, sign in as Sudeep-Sharma1 in the browser window. If it asks for a
password in the terminal, use a **personal access token** (GitHub → Settings → Developer settings →
Fine-grained tokens → repository `edaphnet-v2`, permission Contents: Read and write).

## 2. Meet your guide (this week)

1. Send the email (drafted in our conversation) with `reports/EdaphNet_Faculty_Discussion.pdf`.
2. Ask the six questions in section 6 of that report. The two that decide everything:
   - Submit now with simulated errors and calculated colour, or wait for real photos?
   - Does the paper need Indian soil data?
3. Agree co-authors and the AI-assistance statement (draft in step 6).

## 3. Formal literature search (1–2 days, needs university library access)

1. Log in to **Scopus** or **Web of Science** through your library.
2. Run these searches (record every one, even with zero hits):
   - `"soil" AND ("laboratory report" OR "lab report") AND ("error detection" OR "quality control")`
   - `"soil" AND ("sample swap" OR "sample mix-up" OR "mislabel*")`
   - `"soil" AND ("smartphone" OR "digital camera") AND ("verification" OR "validation") AND "laboratory"`
   - `("sample swap" OR "mislabel*") AND ("detection") AND ("independent measurement" OR "witness")`
   - `"conformal" AND ("outlier" OR "anomaly") AND ("laboratory" OR "measurement")`
3. For each search add one row to `docs/search_log.csv`:
   `date,database,query_string,hits,screened,included,notes`
4. Read the titles and abstracts. If any paper already does **joint swap + value-error checking of
   soil lab reports with an independent observation**, tell your guide: the novelty claim in §2
   ("Gap") must change.
5. Delete "[To be confirmed by the formal search.]" from §2 of the draft only after this is done.

## 4. Check every citation (1 day)

Open each source and confirm it says what the draft says. Fix or remove any that do not.

| Draft text | What to check |
|---|---|
| [SOIL 2025], line ~57 | 8 service labs, 28% of SOC observations outside NAPT acceptable range |
| [refs 1–7 in doc 09] | replace with real references (author, year) from `docs/09_*` |
| LandPKS | phone Munsell colour with in-frame reference |
| US 8,352,394 | lab value vs predicted value in process industry |
| [AJCP 2018; Clin Chem 2023] | ML delta checks for wrong-blood-in-tube |
| Broman et al. 2014; Crosscheck | genomic sample-swap detection |
| Zhou et al. 2023 (cleanlab regression) | label-error scores for regression |
| Bates et al. 2023; Jin & Candès 2023 | conformal p-values + BH |
| Schmidinger et al. 2026 | uncertainty-guided rejection in soil spectroscopy |
| **Add:** Zenodo 10.5281/zenodo.22876123 (Sept 2026) | smartphone SOC imaging across 4 phones; cite in §2 "Soil properties from images" |

## 5. Requests to send (30 minutes, then wait)

- **LUCAS topsoil data** (free): https://esdac.jrc.ec.europa.eu/content/lucas-2018-topsoil-data
  (fill the request form; use your institutional email and your guide's name).
- **IP office:** ask whether a patent is still possible. Tell them the repository
  (github.com/Sudeep-Sharma1/edaphnet-v2) was public for a period before being made private; the
  exact dates are in the GitHub history. **Do this before posting any preprint.**
- **VIT VAIAL soil lab** (only if your guide agrees): the drafted request for 30–50 tested samples.

## 6. Finalise the paper text (1 day)

1. **AI-assistance statement.** Replace the placeholder in the draft's Reproducibility statement.
   A starting point to agree with your guide:
   > "Code, analyses and draft text were developed with the assistance of an AI model (Claude,
   > Anthropic). The authors designed the study, fixed all pre-registration rules, checked every
   > result against the run records and take full responsibility for the content."
2. Remove the first line "DRAFT v0 — not for circulation" and the HTML comment block at the top.
3. Choose the journal with your guide (suggested: SOIL, European Journal of Soil Science,
   Computers and Electronics in Agriculture) and reformat to its template (word limit, reference style).
4. Rebuild the PDF:
   ```powershell
   & "C:\Program Files\Python314\python.exe" scripts/make_paper_figures.py
   & "C:\Program Files\Python314\python.exe" scripts/build_report_pdf.py --paper
   ```

## 7. Zenodo DOI for the code (30 minutes)

Zenodo's automatic GitHub link only works for public repositories. With a private repository:
1. On GitHub: Code → Download ZIP (or `git archive -o edaphnet-v2.zip HEAD`).
2. Go to https://zenodo.org → log in → New upload → upload the ZIP.
3. Type: Software. Title: "EdaphNet v2: code and run records". Licence: as in the repository.
4. You can **reserve a DOI** before publishing it, put the DOI in the paper, and publish the record
   when the paper is accepted (or when your guide and the IP office agree).

## 8. Submit

Submit only after: guide sign-off, search done, citations checked, IP question answered, AI
statement agreed, DOI reserved. In the cover letter, say plainly that the main pre-registered claim
failed and that the paper reports when a cheap witness is and is not enough.

## 9. Optional: app leaf model (2 minutes)

```powershell
& "C:\Program Files\Python314\python.exe" scripts/app_leaf_train.py
& "C:\Program Files\Python314\python.exe" app/server.py      # then http://localhost:8001
```
Report the **PlantDoc** accuracy it prints as the honest number (not the PlantVillage one).

## 10. Paper 2 (later)

Real phone photos of soils with lab values (pilot of 30–50 samples, protocol in doc 15) and real
errors from blind duplicates with a partner laboratory. Pre-register the rules before collecting
data, as in doc 18.

---

## If something breaks

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | use `"C:\Program Files\Python314\python.exe"`, not the `.venv` Python |
| Laptop runs out of memory | close Chrome and the IDE; never run two experiments at once |
| A long run stopped | rerun with `--resume results/runs/<run folder>` (same numbers) |
| Demo page says server offline | start `python scripts/serve_demo.py` first and keep that window open |
| Data missing on a new computer | `python scripts/download_ossl.py`, then the steps in `REPRODUCE.md` |
