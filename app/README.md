# EdaphNet App Layer (separate from the research code)

This folder is an **application built on top of** the research in `src/edaphnet2/`. It is not part
of the paper. The research code is imported, never modified from here.

| Folder | Purpose | Status |
|---|---|---|
| `soil/` | soil-type / soil-property image model | properties: reuses the research colour model; soil **type**: on hold (no audited image set, docs/25) |
| `crop/` | multi-soil crop suitability from soil + climate | ✅ v1 (EcoCrop rules; not yet validated for India, docs/24 Amendment 1) |
| `leaf/` | leaf disease image model | ✅ v1: MobileNetV3 features + logistic head, "not sure" rule; PlantDoc cross-dataset result in docs/27 (planned) |
| `knowledge/` | disease information and crop requirements, every number with a source | ✅ `crops.json` (EcoCrop), `diseases.json` (26 classes, sourced) |
| `web/` | upload + camera page | ✅ `web/index.html` (4 tabs) |
| `server.py` | one backend for everything | ✅ `/api/leaf`, `/api/soil`, `/api/crops`, `/api/report-check` |

Design and methodology: `docs/24_app_design.md` (the document to defend in the viva).
Raw downloaded datasets go to `data/app_raw/` (git-ignored).

**Run:** `"C:\Program Files\Python314\python.exe" app/server.py`, then open http://localhost:8001 (details in `HOW_TO_RUN.md` §1d).
