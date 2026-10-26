# Knowledge-base sources

Every number in `app/knowledge/*.json` must have an entry here (dataset or document, version or
date accessed, licence, and the exact table/page it came from). Entries without a source are not
allowed in the app.

| Key | Source | Version / accessed | Licence | Location in source |
|---|---|---|---|---|
| `crops.json` (all values) | FAO EcoCrop database, CSV copy from github.com/OpenCLIM/ecocrop (`EcoCrop_DB.csv`), please cite that repository | downloaded 2026-10-02; MD5 in `crops.json` → `source_md5` | Open Government Licence v3 (repository); FAO EcoCrop | one row per crop, identified by `ecoport_code` |
| `diseases.json` (26 disease/pest classes) | PlantVillage (Penn State) crop "infos" pages for apple, cherry, maize, grape, orange, peach, bell pepper, potato, squash, strawberry, tomato; Kerala Agricultural University (tomato late blight); NC State Extension (TYLCV); UF/IFAS Extension (ToMV); University of Delaware Cooperative Extension (two-spotted spider mite). Exact URL per entry in `diseases.json` → `sources` | accessed 2026-10-02 | short paraphrases with attribution; no text copied at length | per-disease section of each page |
