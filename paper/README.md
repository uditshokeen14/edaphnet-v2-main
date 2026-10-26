# EdaphNet IEEE Transactions Publication Package

This directory contains the complete, publication-ready **IEEE Transactions / Conference submission bundle** for the EdaphNet research paper.

## Title
**Cyber-Physical Quality Assurance of Analytical Laboratories: Joint Permutation-Corruption Inference with Low-Cost Optical Witnesses and Conformal Calibration Bounds**

---

## Directory Structure

```
paper/
├── IEEEtran.cls           # Official standard IEEE Transactions document class
├── edaphnet_ieee.tex      # Full IEEE two-column LaTeX manuscript source
├── references.bib         # 20+ complete BibTeX references (IEEE, ACM, Ann. Statist., etc.)
├── README.md              # Instructions for compilation and submission
└── figures/               # High-resolution figures generated from experiment runs
    ├── fig0_method.png        # Fig. 1: Method architecture & cyber-physical pipeline
    ├── fig1_witness_r2.png    # Fig. 3: R² cross-validated across optical sensor ladder
    ├── fig2_kssl_recall.png   # Fig. 4: Pre-registered KSSL benchmark recall at 5% budget
    ├── fig3_swap_vs_value.png # Fig. 5: Swaps vs. numerical corruption trade-off decomposition
    ├── fig4_pool_size.png     # Fig. 2: Conformal calibration & pool-size FDR dynamics
    └── fig5_error_mix.png     # Fig. 6: Sensitivity curve across varying batch error compositions
```

---

## Output Formats Built

- **IEEE Two-Column PDF**: [`reports/EdaphNet_IEEE_Transactions_Paper.pdf`](../reports/EdaphNet_IEEE_Transactions_Paper.pdf) (816 KB)
- **IEEE Interactive HTML**: [`reports/EdaphNet_IEEE_Transactions_Paper.html`](../reports/EdaphNet_IEEE_Transactions_Paper.html)

To regenerate the PDF and HTML:
```bash
python scripts/build_ieee_paper.py
```

---

## Compiling via LaTeX / Overleaf

1. **Overleaf**: Upload the `paper/` directory as a ZIP file. Select `edaphnet_ieee.tex` as the main document. Overleaf will compile using standard pdfLaTeX.
2. **Local TeXLive / MikTeX**:
   ```bash
   pdflatex edaphnet_ieee.tex
   bibtex edaphnet_ieee
   pdflatex edaphnet_ieee.tex
   pdflatex edaphnet_ieee.tex
   ```

---

## Target IEEE Venues

- **IEEE Transactions on AgriFood Electronics (TAFE)** *(Primary Recommendation)*
- **IEEE Transactions on Instrumentation and Measurement (TIM)**
- **IEEE Transactions on Artificial Intelligence (TAI)**
- **IEEE Access** *(Rapid Multidisciplinary Review)*
- **IEEE SENSORS Journal** / **IEEE MetroAgriFor** / **IEEE I2MTC**
