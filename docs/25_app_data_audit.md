# App Step 1 — Data Collection and Audit

**Date:** 3 October 2026 · **Design:** docs/24 · **Scripts:** `scripts/app_build_crops.py`,
`scripts/app_audit_images.py` · **Outputs:** `app/knowledge/crops.json`, `results/app_audit/`,
`data/app_raw/MANIFEST.csv` (raw files are git-ignored).

## 1. Downloads (approved 2026-10-02)

| Item | Source | Licence | Status |
|---|---|---|---|
| FAO EcoCrop CSV | github.com/OpenCLIM/ecocrop `EcoCrop_DB.csv` (1.6 MB) | Open Government Licence v3; cite the repository | ✅ |
| torchvision 0.28.0 (CPU) | PyTorch index, matched to installed torch 2.13.0 (no torch upgrade) | BSD | ✅ |
| PlantDoc | github.com/pratikkayal/PlantDoc-Dataset (934 MB) | CC BY 4.0 (LICENSE.txt) | ✅ |
| PlantVillage (colour) | github.com/spMohanty/PlantVillage-Dataset, `raw/color` only (sparse checkout) | CC BY-SA 3.0 (README_HF.md) | ✅ |
| Soil image sets (IRSID, Kaggle, Roboflow) | — | — | ⬜ need logins; user action |

## 2. Crop knowledge base (FAO EcoCrop)

25 common Indian crops, all found (finger millet is listed as *Eleusine coracana ssp. coracana*).
For each: optimal and absolute ranges of temperature, annual rainfall and pH, plus optimal texture,
depth, drainage, salinity and fertility classes. Every crop keeps its `ecoport_code`, and the file
records the CSV's MD5, so every number is traceable. Missing values are left empty, not guessed
(e.g. maize has no texture class in EcoCrop).

## 3. PlantDoc audit

| Item | Value |
|---|---|
| Files in repository (train + test) | 2,578 |
| On disk | 2,572 (87 files had "?" in their names, which Windows forbids; recovered under safe names; 6 lost because their safe names collided) |
| Readable images | 2,564 (1 unreadable) |
| Classes | 28 in train, 27 in test |
| Split | 2,328 train / 236 test |
| Images per class | 2 to 191 (very unbalanced) |
| **Exact duplicates (MD5)** | 12 groups; **11 cross the train/test split**; **9 have conflicting class labels** |
| **Visual duplicates (dHash)** | 47 groups (95 images); **14 cross the split**; **27 have conflicting labels** |

**Consequences (rules fixed now, before any training):**
1. The official PlantDoc train/test split leaks; it will **not** be used as-is.
2. Duplicate groups with conflicting labels are **removed** (the label cannot be trusted).
3. Remaining duplicate groups are kept together on one side of any split.
4. PlantDoc is used only as a **cross-dataset test set** (docs/24 §5), on the classes it shares with
   PlantVillage, after cleaning.

## 4. PlantVillage audit

| Item | Value |
|---|---|
| Images / classes | 54,305 / 38 (14 crops), all readable |
| Images per class | 152 (Potato healthy) to 5,507 (Orange citrus greening): strongly unbalanced |
| Exact duplicates (MD5) | 21 groups (42 images), no conflicting labels |
| Visual duplicates (dHash) | 24 groups (48 images), no conflicting labels |
| **Shared with PlantDoc** | **0 visual duplicates**, so PlantDoc is an independent test set |

**Caveat.** PlantVillage has no leaf, plant or session identifiers, and several photos of the same
leaf can differ slightly. Exact-hash checks do not catch these, so a random split *within*
PlantVillage can still be optimistic. That is one more reason the headline accuracy will be the
cross-dataset (PlantDoc) and field-photo result, not PlantVillage's own test split.

**Rules (fixed before training):** keep one image per duplicate group; balance classes by weighting
(no oversampling of duplicates); train/validation split within PlantVillage only for model selection;
report PlantDoc (cleaned, shared classes) and own field photos as the test results.

## 5. Still needed from the user

- Soil image data: IRSID (IEEE DataPort) and Kaggle need an account to download; Roboflow needs an
  API key. Alternatively, start with our own phone photos (doc 15).
- Own field leaf photos (the final, honest test set).
