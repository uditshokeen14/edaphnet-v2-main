#!/usr/bin/env python3
"""Generate IEEE Transactions formatted DOCX document for EdaphNet paper / review."""

import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RESULTS_DIR = ROOT / "results"
FIG_DIR = ROOT / "docs" / "paper" / "figures"


def set_cell_margins(cell, top=50, bottom=50, left=60, right=60):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_borders(cell, top=None, bottom=None, left=None, right=None):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge, border in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        if border:
            el = OxmlElement(f'w:{edge}')
            el.set(qn('w:val'), border.get('val', 'single'))
            el.set(qn('w:sz'), str(border.get('sz', 4)))
            el.set(qn('w:space'), '0')
            el.set(qn('w:color'), border.get('color', '000000'))
            tcBorders.append(el)
        else:
            el = OxmlElement(f'w:{edge}')
            el.set(qn('w:val'), 'none')
            tcBorders.append(el)
    tcPr.append(tcBorders)


def create_document():
    doc = Document()

    # Page setup - standard IEEE 0.65 in margins
    for section in doc.sections:
        section.top_margin = Inches(0.65)
        section.bottom_margin = Inches(0.65)
        section.left_margin = Inches(0.6)
        section.right_margin = Inches(0.6)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # Base style
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(9.5)
    style_normal.font.color.rgb = RGBColor(0x11, 0x11, 0x11)

    # Document Banner
    p_banner = doc.add_paragraph()
    p_banner.paragraph_format.space_after = Pt(8)
    r_b1 = p_banner.add_run("IEEE TRANSACTIONS ON AGRIFOOD ELECTRONICS, REGULAR PAPER\tDOI: 10.1109/TAFE.2026.XXXXXXX")
    r_b1.font.size = Pt(8)
    r_b1.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(10)
    r_title = p_title.add_run(
        "Cyber-Physical Quality Assurance of Analytical Laboratories:\n"
        "Joint Permutation-Corruption Inference with Low-Cost Optical Witnesses and Conformal Calibration Bounds"
    )
    r_title.bold = True
    r_title.font.size = Pt(18)

    # Author Block
    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_after = Pt(3)

    def add_author(p, name, status):
        r1 = p.add_run(name)
        r1.font.size = Pt(10.5)
        r2 = p.add_run(f", {status}, ")
        r2.font.size = Pt(9.5)
        r2.italic = True

    add_author(p_auth, "Sudeep Sharma", "Student Member, IEEE")
    add_author(p_auth, "Armaan Srivastava", "Student Member, IEEE")
    add_author(p_auth, "Udit Shokeen", "Student Member, IEEE")
    r_p = p_auth.add_run("and ")
    r_p.font.size = Pt(10.5)
    r_pg = p_auth.add_run("Dr. Priya Saminathan")
    r_pg.font.size = Pt(10.5)
    r_pgs = p_auth.add_run(", Senior Member, IEEE (Faculty Guide)")
    r_pgs.font.size = Pt(9.5)
    r_pgs.italic = True

    # Affiliations
    p_aff = doc.add_paragraph()
    p_aff.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_aff.paragraph_format.space_after = Pt(2)
    r_aff = p_aff.add_run(
        "School of Computer Science and Engineering, Vellore Institute of Technology, Vellore 632014, Tamil Nadu, India\n"
        "Emails: {sudeep.sharma2023, armaan.srivastava2023, udit.shokeen2023}@vitstudent.ac.in; priya.s@vit.ac.in"
    )
    r_aff.font.size = Pt(8.5)
    r_aff.italic = True
    r_aff.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    p_corr = doc.add_paragraph()
    p_corr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_corr.paragraph_format.space_after = Pt(12)
    r_corr = p_corr.add_run(
        "Manuscript received October 2, 2026; revised October 26, 2026. Corresponding author: Sudeep Sharma."
    )
    r_corr.font.size = Pt(8)
    r_corr.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    # Abstract Box
    tbl_abs = doc.add_table(rows=1, cols=1)
    tbl_abs.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_abs = tbl_abs.rows[0].cells[0]
    cell_abs.width = Inches(7.3)
    set_cell_borders(
        cell_abs,
        top={'val': 'single', 'sz': 4, 'color': '888888'},
        bottom={'val': 'single', 'sz': 4, 'color': '888888'},
        left={'val': 'single', 'sz': 4, 'color': '888888'},
        right={'val': 'single', 'sz': 4, 'color': '888888'}
    )
    set_cell_margins(cell_abs, top=120, bottom=120, left=140, right=140)

    p_a = cell_abs.paragraphs[0]
    p_a.paragraph_format.line_spacing = 1.15
    p_a.paragraph_format.space_after = Pt(4)
    r_at = p_a.add_run("Abstract—")
    r_at.bold = True
    r_at.italic = True
    r_at.font.size = Pt(8.5)
    r_ab = p_a.add_run(
        "High-throughput analytical testing laboratories in agronomy, environmental chemistry, and clinical pathology govern safety-critical decisions, "
        "including regional fertilizer allocations, soil carbon sequestration underwriting, and remediation protocols. However, analytical reports are susceptible "
        "to silent mechanical and human failure modes: specimen transpositions (sample swaps) and clerical transcription errors (decimal point slips, unit confusion, "
        "digit inversions). Classical univariate autoverification and longitudinal delta checks fail in environmental batch testing because samples lack historical "
        "time-series baselines and swapped specimens satisfy marginal domain boundaries. We present EdaphNet, a cyber-physical quality assurance framework that "
        "couples an independent, non-contact optical observation (a physical witness) captured before chemical testing with a joint batch-level probabilistic "
        "graphical model. The engine computes Bayesian Maximum A Posteriori (MAP) scores over structured tray-permutation subgroups S_tray subset S_n "
        "(exact within candidate set S_tray) and a formal library of typed numerical corruption operators C, producing calibrated suspicion scores, "
        "root-cause attributions, and repaired values.\n\n"
        "The framework is evaluated on 19,746 real soil samples from the Kellogg Soil Survey Laboratory (KSSL) and 3,473 samples from the ICRAF-ISRIC repository "
        "(23,219 samples total) across a conceptual four-rung sensor ladder (W_0–W_3), with three sensor tiers (W_0, W_1, W_3) empirically benchmarked on KSSL "
        "under pre-registered evaluation protocols. In confirmatory testing, the primary pre-registered hypothesis A1—that a commodity smartphone camera proxy "
        "would outperform the best existing baseline in overall error recall across an equal mix of errors—was refuted (+0.014 [-0.008, +0.038] with good phone optics "
        "Delta E = 2). In contrast, with continuous laboratory Vis-NIR spectroscopy (W_3), EdaphNet achieves a statistically significant confirmatory gain of "
        "+9.2 percentage points (+0.092 [+0.069, +0.113], p < 0.001) across all error categories. An exploratory post-hoc sub-analysis establishes that commodity "
        "phone optics provide a decisive +10.3 percentage point advantage (95% CI: [+0.064, +0.139]) specifically in isolating physical specimen swaps, offset by a "
        "-8.2 percentage point deficit on isolated numerical value slips; the method crosses into an overall advantage once swaps comprise >= 60–70% of batch failures. "
        "For root-cause fault attribution, EdaphNet achieves 84–92% accuracy in simulation, 89–98% on ICRAF color data, and 97–100% on KSSL spectrometer data "
        "(against 24–29% on KSSL and 32–51% on ICRAF/simulation for rule heuristics), with 87–99% exact swap-partner identification accuracy under high-information witnesses. "
        "Furthermore, we demonstrate that conformal false discovery rate (FDR) control collapses under calibration sample re-use (pseudo-replication, inflating realized FDR "
        "to 57–92%), whereas restricting calibration to one score per distinct physical sample reliably restores empirical FDR control (0.000–0.090 in pre-registered "
        "50-batch pools, and 0.03–0.11 across pool sizes 1 to 50 batches, nominal q = 0.10)."
    )
    r_ab.font.size = Pt(8.5)

    p_idx = cell_abs.add_paragraph()
    p_idx.paragraph_format.space_before = Pt(4)
    r_idxt = p_idx.add_run("Index Terms—")
    r_idxt.bold = True
    r_idxt.italic = True
    r_idxt.font.size = Pt(8.5)
    r_idx = p_idx.add_run(
        "Analytical laboratory quality control, cyber-physical systems, sample permutation, conformal inference, false discovery rate (FDR), "
        "diffuse reflectance spectroscopy, fault attribution, label noise."
    )
    r_idx.font.size = Pt(8.5)

    p_sep = doc.add_paragraph()
    p_sep.paragraph_format.space_after = Pt(6)

    def add_heading_1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(10.5)
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.italic = True
        r.font.size = Pt(10)
        return p

    def add_body_p(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(text)
        return p

    def add_figure(img_path, caption_text):
        if img_path.exists():
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(6)
            p_img.paragraph_format.space_after = Pt(3)
            doc.add_picture(str(img_path), width=Inches(6.2))
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_cap.paragraph_format.left_indent = Inches(0.2)
            p_cap.paragraph_format.right_indent = Inches(0.2)
            p_cap.paragraph_format.space_after = Pt(8)
            r = p_cap.add_run(caption_text)
            r.font.size = Pt(8.5)
            r.italic = False

    # -------------------------------------------------------------
    # I. INTRODUCTION
    # -------------------------------------------------------------
    add_heading_1("I. INTRODUCTION")
    add_body_p(
        "High-throughput analytical testing laboratories serve as the empirical foundation for agriculture, clinical diagnostics, "
        "environmental safety, and industrial chemical processing. In agricultural soil analysis, laboratory measurements of pH, organic carbon (SOC), "
        "total nitrogen (N), cation exchange capacity (CEC), and primary nutrients dictate high-stakes agronomic decisions, including regional fertilizer "
        "application, soil amendments, and verifiable carbon credit underwriting. Despite extensive internal quality controls and instrument calibrations, "
        "routine batch processing remains vulnerable to human handling and clerical errors. Recent empirical studies across commercial analytical service laboratories "
        "revealed that sample-processing differences (sieving, grinding, drying, and analytical quantification) induce extensive inter-laboratory "
        "variability in reported soil organic carbon [1]."
    )
    add_body_p(
        "Analytical batch errors fall into two fundamentally distinct structural failure modes:\n"
        "1) Specimen Swaps (Permutations): Misplacement of physical sample containers or automated tray rotations cause Sample j to be reported under "
        "Sample k's identifier. The report delivered to farmer j is chemically valid—it simply corresponds to the wrong physical parcel.\n"
        "2) Numerical Value Corruptions: Typographical transcription errors or automated software parsing glitches inject typed corruptions, "
        "including orders-of-magnitude decimal point shifts (x10, /10), digit transpositions (0.16 <-> 0.61), or column interchanges."
    )
    add_body_p(
        "Conventional quality assurance (QA) frameworks are fundamentally unequipped to resolve this duality. In clinical pathology, automated "
        "'delta checks' compare current measurements against a patient's historical longitudinal time series [2], [3]. In environmental testing, historical "
        "baselines rarely exist for an incoming batch. Furthermore, univariate range filters (B_0) and agronomic consistency rules (B_1) are structurally "
        "blind to sample swaps because swapped samples satisfy marginal domain boundaries."
    )
    add_body_p(
        "To address this challenge, we introduce a cyber-physical testing paradigm: capturing an independent, non-contact optical observation of each "
        "physical specimen—termed a physical witness w_i—prior to destructive laboratory digestion. The witness can range from an inexpensive smartphone "
        "photograph under ambient lighting to a continuous diffuse reflectance Vis-NIR spectrometer. Because the optical witness is acquired directly from "
        "the physical sample matter, it is impervious to downstream laboratory clerical errors."
    )

    add_figure(
        FIG_DIR / "fig0_method.png",
        "Fig. 1. Architecture of the EdaphNet cyber-physical verification engine. An optical sensor captures a physical witness w_i of each specimen. "
        "A multi-property latent Gaussian process estimates the joint property distribution p(z | w_i). The joint inference engine enumerates "
        "tray-permutation hypotheses pi in S_tray against corruption operators T_c in C across the entire batch R, producing calibrated suspicion ranks, "
        "fault attributions, and repair recommendations."
    )

    add_body_p(
        "In this paper, we propose EdaphNet, a joint batch-level probabilistic verification framework. Rather than evaluating specimens in isolation, "
        "EdaphNet performs Bayesian joint inference over the combinatorial space of structured sample permutations (S_tray) and typed value-corruption operators (C). "
        "Within the structured candidate set S_tray, the posterior evaluation is computed exactly. We evaluate the framework on 23,219 real soil samples "
        "from global repositories under pre-registered evaluation protocols."
    )

    # -------------------------------------------------------------
    # II. RELATED WORK & PRIOR ART TAXONOMY
    # -------------------------------------------------------------
    add_heading_1("II. RELATED WORK & PRIOR ART TAXONOMY")
    add_body_p(
        "A targeted literature survey across IEEE Xplore, Scopus, Web of Science, and PubMed examined prior art across four relevant methodological fields:"
    )
    add_heading_2("A. Optical Soil Sensing and Smartphone Colorimetry")
    add_body_p(
        "Optical diffuse reflectance spectroscopy (Vis-NIR, 350–2500 nm) has been widely adopted for rapid non-destructive soil assessment [5], [6]. "
        "Recent initiatives have deployed mobile applications (e.g., LandPKS [7]) to record soil color and estimate physical soil characteristics using mobile devices. "
        "However, existing optical sensing methods are deployed exclusively as predictive estimators. EdaphNet inverts this paradigm: using optical sensing "
        "as an independent verification witness to audit high-precision wet-chemistry lab reports."
    )
    add_heading_2("B. Autoverification and Delta Checks in Laboratory QA")
    add_body_p(
        "Industrial process patents (e.g., US Patent 8,352,394 [8]) describe checking lab values against model predictions. In clinical chemistry, "
        "autoverification rules and multi-analyte machine-learning delta checks detect 'wrong-blood-in-tube' (WBIT) errors by comparing fresh draws "
        "against historical patient archives [2], [3]. In environmental and agricultural soil testing, specimens are sampled cross-sectionally without historical "
        "records; EdaphNet overcomes this by leveraging batch-level physical constraints."
    )
    add_heading_2("C. Specimen Mislabelling in Genomics & Soil Predictability")
    add_body_p(
        "In high-throughput genetics, sample mix-ups are detected by matching two distinct data modalities (e.g., SNP microarrays and RNA sequencing) "
        "derived from the same subject (Broman et al. [9]). While genomic matching relies on near-deterministic genetic signatures (R^2 approx 1.0), "
        "agricultural soil witnesses are noisy, low-dimensional, and weak: with good smartphone camera color (W_1, Delta E = 2), optical witnesses explain at most "
        "R^2 <= 0.15–0.16 for mineral, cation, and texture properties on ICRAF (clay 0.07, sand <= 0, CEC 0.05, Mg 0.06, K <= 0, Ca 0.13, pH 0.15), rising to "
        "R^2 = 0.35 for ICRAF SOC and R^2 = 0.70 (70%) for KSSL SOC. Under uncorrupted perfect color (W_1, Delta E = 0), ICRAF SOC reaches R^2 = 0.37, "
        "pH reaches R^2 = 0.27, and Ca reaches R^2 = 0.23, while texture and other cations remain <= 0.16. Under laboratory Vis-NIR spectroscopy (W_3), "
        "predictability reaches R^2 = 0.60–0.66 across ICRAF properties and R^2 = 0.90 for KSSL SOC and C_tot. Selective uncertainty rejection strategies "
        "in diffuse reflectance spectroscopy (Schmidinger et al. [10]) allow models to abstain on out-of-distribution spectra, but do not model clerical laboratory failures; "
        "EdaphNet complements spectral uncertainty with a structured permutation and transcription error model."
    )
    add_heading_2("D. Label Error Diagnostics and Conformal Hypothesis Testing")
    add_body_p(
        "Data-centric machine learning frameworks, such as confident learning and Cleanlab (Zhou et al. [4]), detect label errors in continuous numerical response "
        "variables and regression tasks. In statistical inference, distribution-free outlier detection using conformal p-values combined with the Benjamini-Hochberg (BH) "
        "procedure provides rigorous False Discovery Rate (FDR) control [11], [12]; foundational conformal prediction theory is established by Angelopoulos & Bates [13] "
        "and Vovk et al. [14]. EdaphNet adopts conformal p-values for thresholding but reveals a critical failure mode: pseudo-replication under calibration sample re-use, "
        "formalizing the sampling requirements necessary to guarantee finite-sample valid FDR control."
    )

    # TABLE I - Formatted to 7.0 inches width with explicit column widths
    p_t1_title = doc.add_paragraph()
    p_t1_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1_title.paragraph_format.space_before = Pt(8)
    p_t1_title.paragraph_format.space_after = Pt(2)
    r_t1t = p_t1_title.add_run("TABLE I\nTAXONOMY AND COMPARISON OF LABORATORY QUALITY ASSURANCE METHODOLOGIES")
    r_t1t.bold = True
    r_t1t.font.size = Pt(8.5)

    table1 = doc.add_table(rows=7, cols=6)
    table1.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_widths = [Inches(1.7), Inches(1.0), Inches(1.0), Inches(1.1), Inches(1.1), Inches(1.1)]

    t1_data = [
        ["Methodology", "Batch Joint Inference", "Physical Witness", "Permutation Model (pi)", "Typed Error Library (C)", "Root-Cause Attribution"],
        ["Range Filters (B0, B1) [This work]", "No", "None", "No", "Heuristic bounds", "24–29% (B6, KSSL)"],
        ["Clinical Delta Checks [3]", "No", "Historical tests", "Pairwise", "No", "No"],
        ["Genomic Mix-up Matching [9]", "Yes", "DNA genotype", "Pairwise", "No", "Swap Only"],
        ["Cleanlab Label Diagnostics [4]", "No", "Covariates", "No", "Continuous Residual", "No"],
        ["Conformal Outlier Testing [11], [12]", "No", "Covariates", "No", "No", "No"],
        ["EdaphNet (Proposed)", "Yes", "RGB / Vis-NIR", "Structured S_tray", "Formal Library C", "97–100% (KSSL W3)"]
    ]
    for row_idx, row in enumerate(table1.rows):
        for col_idx, cell in enumerate(row.cells):
            cell.text = t1_data[row_idx][col_idx]
            cell.width = col_widths[col_idx]
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.paragraphs[0].paragraph_format.space_after = Pt(2)
            cell.paragraphs[0].paragraph_format.space_before = Pt(2)
            for r in cell.paragraphs[0].runs:
                r.font.size = Pt(7.5)
                if row_idx == 0 or row_idx == 6:
                    r.bold = True
            top_b = {'val': 'single', 'sz': 8, 'color': '000000'} if row_idx == 0 else ({'val': 'single', 'sz': 4, 'color': '888888'} if row_idx in [1, 6] else None)
            bot_b = {'val': 'single', 'sz': 8, 'color': '000000'} if row_idx == 6 else ({'val': 'single', 'sz': 4, 'color': '000000'} if row_idx == 0 else None)
            set_cell_borders(cell, top=top_b, bottom=bot_b)
            set_cell_margins(cell, top=40, bottom=40, left=40, right=40)

    p_post_t1 = doc.add_paragraph()
    p_post_t1.paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------
    # III. PROBLEM FORMULATION
    # -------------------------------------------------------------
    add_heading_1("III. MATHEMATICAL PROBLEM FORMULATION")
    add_body_p(
        "Consider an analytical laboratory batch processing n physical specimens arranged in an automated rack or micro-plate tray (typically n = 24). "
        "Prior to digestion, a non-contact optical sensor records a physical witness w_i in R^d for each tray position i in {1, ..., n}. "
        "Downstream, analytical instrumentation outputs a batch of multivariate reports R = (r_1, ..., r_n), where each report r_j in R^P "
        "contains P measured chemical analytes (e.g., SOC, N, total carbon, pH, CEC)."
    )
    add_heading_2("A. Structured Tray Permutation Subgroup")
    add_body_p(
        "Specimen transpositions are modeled as bijections pi: {1, ..., n} -> {1, ..., n}. While the full symmetric group S_n contains n! candidate "
        "permutations, physical mishandling errors conform to spatial laboratory tray geometries. We define a structured "
        "candidate set S_tray subset S_n comprising: (1) identity pi_0(j) = j (1 permutation); (2) all pairwise transpositions (j, k) across the tray "
        "(C(24, 2) = 276 permutations for n = 24, which directly subsume the 23 adjacent swaps pi_adj(j, j+1)); and (3) cyclic tray rotations by +/-1 or +/-2 positions "
        "(4 permutations). In total, S_tray contains exactly 1 + 276 + 4 = 281 candidate permutations for a 24-well micro-plate, rendering exact Bayesian evaluation "
        "computationally tractable."
    )
    add_heading_2("B. Typed Numerical Corruption Operator Library")
    add_body_p(
        "Clerical transcription errors are modeled via a library of typed corruption operators C = {T_c}. For a true analyte value x, an observed value "
        "is generated by r = T_c(x). The library C formalizes: (1) identity T_none(x) = x; (2) order-of-magnitude decimal slips T_x10(x) = 10x, "
        "T_div10(x) = 0.1x; (3) common unit conversion mismatches T_unit(x); (4) digit transpositions T_transp(x); (5) column interchanges; and "
        "(6) gross scaling corruptions T_gross(x) = gamma * x, where gamma in [0.2, 5.0]."
    )
    add_heading_2("C. Permutation Prior Formulation")
    add_body_p(
        "The prior distribution P(pi) over S_tray assigns probability mass 1 - rho to the null hypothesis of no specimen swap (identity pi_0), where "
        "rho in (0, 1) denotes the prior probability that a tray experienced an operational handling failure (set to rho = 0.10 in benchmark experiments). "
        "The remaining probability mass rho is partitioned across three mechanical classes: adjacent transpositions (class mass 0.50), cyclic block rotations "
        "(class mass 0.30), and non-adjacent pair transpositions (class mass 0.20), distributed uniformly within each mechanical class."
    )
    add_heading_2("D. Multi-Property Latent Gaussian Process")
    add_body_p(
        "Because optical witnesses and laboratory chemical properties operate on disparate scales and non-Gaussian marginals, we apply monotonic "
        "quantile scalers g_p: R -> R mapping each reported property to latent coordinates z = g(r) ~ N(0, I). Conditional on the physical witness w_i, "
        "the latent vector follows a multivariate Gaussian distribution:"
    )
    
    p_eq1 = doc.add_paragraph()
    p_eq1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq1.paragraph_format.space_before = Pt(4)
    p_eq1.paragraph_format.space_after = Pt(4)
    r_eq1 = p_eq1.add_run("z_i | w_i ~ N( mu(w_i),  Sigma )                                          (1)")
    r_eq1.font.size = Pt(9.5)
    r_eq1.italic = True

    add_body_p(
        "Here, mu(w_i) in R^P is an out-of-fold gradient-boosted regression estimate predicting latent chemistry from the optical witness, and "
        "Sigma in R^(P x P) is the empirical residual covariance matrix. The off-diagonal covariance terms capture geochemical dependencies among "
        "soil analytes (e.g., stoichiometric ratios between organic carbon and total nitrogen), allowing the framework to flag anomalous values even "
        "when the optical witness is weakly predictive for a specific analyte."
    )

    # -------------------------------------------------------------
    # IV. JOINT INFERENCE ENGINE
    # -------------------------------------------------------------
    add_heading_1("IV. THE JOINT INFERENCE ENGINE")
    add_body_p(
        "For a candidate assignment pairing report r_j with physical specimen position i, the marginal likelihood integrates over corruption hypotheses in C:"
    )

    p_eq2 = doc.add_paragraph()
    p_eq2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq2.paragraph_format.space_before = Pt(4)
    p_eq2.paragraph_format.space_after = Pt(4)
    r_eq2 = p_eq2.add_run("L(j, i) = sum_{c in C} P(c) * phi( g(T_c^{-1}(r_j));  mu(w_i), Sigma ) * |J_{g o T_c^{-1}}(r_j)|           (2)")
    r_eq2.font.size = Pt(9.5)
    r_eq2.italic = True

    add_body_p(
        "where phi(.; mu, Sigma) denotes the multivariate Gaussian density and J represents the change-of-variables Jacobian determinant. "
        "The joint posterior over tray permutation hypotheses pi in S_tray is scored relative to the identity assignment:"
    )

    p_eq3 = doc.add_paragraph()
    p_eq3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq3.paragraph_format.space_before = Pt(4)
    p_eq3.paragraph_format.space_after = Pt(4)
    r_eq3 = p_eq3.add_run("P(pi | R, W) proportional to P(pi) * prod_{j=1}^n [ L(j, pi(j)) / L(j, j) ]                            (3)")
    r_eq3.font.size = Pt(9.5)
    r_eq3.italic = True

    add_body_p(
        "Normalizing posterior probabilities over S_tray yields the marginal probability that report j was transposed, P(moved_j) = sum_{pi: pi(j) != j} P(pi | R, W). "
        "Combining this with the probability of uncorrupted analytical transcription yields the clean-report posterior and final suspicion score s_j:"
    )

    p_eq4 = doc.add_paragraph()
    p_eq4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq4.paragraph_format.space_before = Pt(4)
    p_eq4.paragraph_format.space_after = Pt(4)
    r_eq4 = p_eq4.add_run("P(clean_j) = [1 - P(moved_j)] * P(c = none | r_j, w_j),      s_j = 1 - P(clean_j)                 (4)")
    r_eq4.font.size = Pt(9.5)
    r_eq4.italic = True

    add_body_p(
        "Algorithm 1 details the complete batch inference routine. On an AMD Ryzen 5 7520U laptop-class mobile processor (4 cores, 8 threads, 2.80 GHz base clock), "
        "full batch inference over 281 candidate hypotheses across a 24-well rack executes in exactly 18 milliseconds (17.9 +- 1.2 ms). The 18 ms latency encompasses "
        "feature prediction mu(w_i), cell likelihood matrix evaluation L(j, i), hypothesis summation across all 281 candidates, and exact posterior normalization, "
        "comfortably fitting within high-throughput laboratory digestion timelines."
    )

    # ALGORITHM 1 BOX
    p_alg = doc.add_paragraph()
    p_alg.paragraph_format.space_before = Pt(6)
    p_alg.paragraph_format.space_after = Pt(6)
    p_alg.paragraph_format.left_indent = Inches(0.2)
    p_alg.paragraph_format.right_indent = Inches(0.2)
    r_alg = p_alg.add_run(
        "Algorithm 1: Batch Permutation–Attribution Inference Engine\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "Input: Analytical reports R = (r_1, ..., r_n), physical witnesses W = (w_1, ..., w_n),\n"
        "       witness predictor mu(.), covariance Sigma, permutation space S_tray, corruption library C.\n"
        "Output: Suspicion vector s in [0, 1]^n, fault attribution A, repaired reports R_hat.\n"
        " 1: Predict latent witness chemistry: z_hat_i <- mu(w_i), for all i in {1, ..., n}\n"
        " 2: for j = 1 to n do\n"
        " 3:     for i = 1 to n do\n"
        " 4:         Compute cell marginal log-likelihood ell(j, i) <- log L(j, i) via Eq. (2)\n"
        " 5: for pi in S_tray do\n"
        " 6:     log P(pi | R, W) <- log P(pi) + sum_{j: pi(j) != j} [ ell(j, pi(j)) - ell(j, j) ]\n"
        " 7: Normalize posterior P(pi | R, W) analytically across S_tray\n"
        " 8: for j = 1 to n do\n"
        " 9:     P(moved_j) <- sum_{pi in S_tray: pi(j) != j} P(pi | R, W)\n"
        "10:     P(clean_j) <- (1 - P(moved_j)) * P(c = none | r_j, w_j)\n"
        "11:     Suspicion score s_j <- 1 - P(clean_j)\n"
        "12:     Determine MAP fault attribution A_j and repaired report r_hat_j\n"
        "13: return s, A, R_hat\n"
        "─────────────────────────────────────────────────────────────────────────────"
    )
    r_alg.font.name = 'Consolas'
    r_alg.font.size = Pt(7.8)

    # -------------------------------------------------------------
    # V. CONFORMAL CALIBRATION & PSEUDO-REPLICATION
    # -------------------------------------------------------------
    add_heading_1("V. CONFORMAL CALIBRATION & PSEUDO-REPLICATION")
    add_body_p(
        "To establish rigorous false-alarm guarantees, EdaphNet maps raw suspicion scores s_j to distribution-free conformal p-values using an independent "
        "calibration dataset D_cal = {(r_k^cal, w_k^cal)}_{k=1}^N of verified clean specimens. The conformal p-value is calculated as:"
    )

    p_eq5 = doc.add_paragraph()
    p_eq5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq5.paragraph_format.space_before = Pt(4)
    p_eq5.paragraph_format.space_after = Pt(4)
    r_eq5 = p_eq5.add_run("p_j = [ 1 + sum_{k=1}^N I( s_k^cal >= s_j ) ] / (N + 1)                                (5)")
    r_eq5.font.size = Pt(9.5)
    r_eq5.italic = True

    add_body_p(
        "Applying the Benjamini-Hochberg (BH) procedure at nominal FDR level q = 0.10 guarantees that under exchangeability [11], [14], False Discovery Rate "
        "satisfies FDR = E[ |False Alarms| / max(1, |Flagged|) ] <= q. Under covariate shift, conformal validity is preserved via weighted conformality [16]."
    )

    add_figure(
        FIG_DIR / "fig4_pool_size.png",
        "Fig. 2. Empirical verification of conformal calibration across pool sizes. In the initial real-data experiment, reusing calibration soils across simulated "
        "batches resulted in severe FDR inflation (57–92%). Enforcing non-replicated calibration (one score per distinct physical sample) restores empirical FDR "
        "control (0.03–0.11 across pool sizes 1 to 50 batches for EdaphNet, and 0.000–0.090 in pre-registered 50-batch pools, nominal q = 0.10). "
        "However, statistical power at fixed nominal q depends strongly on evaluation pool size relative to calibration denominator N."
    )

    add_body_p(
        "Methodological Finding 1 (Calibration Pseudo-Replication): In the initial real-data experiment, empirical FDR collapsed for all baselines (realized FDR 57–92%). "
        "Diagnostic investigation revealed that sampling the same finite set of calibration specimens repeatedly across batches violates exchangeability (identified in "
        "scripts/diag_calibration.py:80-96). Sample re-use creates discrete duplicate spikes in the empirical distribution of s^cal, artificially driving conformal p-values "
        "down and triggering false alarm surges. Enforcing one score per distinct physical sample (N approx 2,800 on KSSL) restored empirical FDR below the target 0.10 threshold "
        "(0.000–0.090 in pre-registered pools, and 0.03–0.11 across pool sizes 1 to 50 batches)."
    )

    # -------------------------------------------------------------
    # VI. EXPERIMENTAL BENCHMARK SETUP
    # -------------------------------------------------------------
    add_heading_1("VI. EXPERIMENTAL BENCHMARK SETUP")
    add_body_p(
        "A. Benchmark Datasets: We rigorously evaluate EdaphNet on two global open-source spectral libraries:\n"
        "1) KSSL Vis-NIR (Primary Pre-Registered Benchmark): 19,746 soil samples from 6,999 distinct geographical locations across the United States. "
        "Properties: Soil Organic Carbon (SOC), Total Nitrogen (N), and Total Carbon (C_tot). Protocol pre-registered in docs/18_preregistered_amendment_v2.md on 2026-10-01 "
        "prior to unblinding test evaluations (code frozen at commit 095deaa).\n"
        "2) ICRAF-ISRIC Spectral Library: 3,473 soil profiles from 553 global sites across Africa, Asia, and Latin America. Properties: pH, SOC, Clay, Sand, CEC, K, Ca, and Mg.\n"
        "Spatial splits strictly follow geographic site identifiers: 50% training, 15% calibration, and 35% evaluation."
    )
    add_body_p(
        "B. The Sensor Witness Ladder: We establish a conceptual four-rung sensor ladder:\n"
        "• W_0 (Uninformative): Prior demographic covariance only.\n"
        "• W_1 (Commodity RGB Colorimetry): CIELAB color simulated under standard D65 illuminant with sensor noise Delta E in {0, 2, 4, 8}.\n"
        "• W_2 (Multispectral): 10 discrete visible wavelength bands (piloted on ICRAF; omitted from KSSL due to lack of camera data).\n"
        "• W_3 (Laboratory Vis-NIR Spectrometer): High-resolution diffuse reflectance (350–2500 nm, 100 PCA features)."
    )

    add_figure(
        FIG_DIR / "fig1_witness_r2.png",
        "Fig. 3. Cross-validated coefficient of determination (R^2) across witness sensor tiers on unseen geographic locations. Under good smartphone camera optics "
        "(W_1, Delta E = 2), predictability reaches R^2 = 0.70 for KSSL SOC and R^2 = 0.35 for ICRAF SOC (R^2 = 0.15 for pH), but drops to R^2 <= 0.07 for texture "
        "and potassium. Under perfect color (W_1, Delta E = 0), ICRAF SOC reaches R^2 = 0.37 and pH reaches R^2 = 0.27, while minerals and texture remain R^2 <= 0.16. "
        "Laboratory spectroscopy (W_3) achieves R^2 = 0.60–0.66 across ICRAF properties and R^2 = 0.90 for KSSL SOC."
    )

    add_body_p(
        "C. Competitive Baselines: EdaphNet is compared against seven QA baselines: Range Filters (B_0), Agronomic Heuristics (B_1), Unconditional Generative Density (B_2), "
        "Marginal Optical Witness Residuals (B_3), Genomic-Style Bipartite Matcher (B_4), Supervised Gradient-Boosted Classifier (B_5), and Cleanlab Confident Learning (B_7) [4]."
    )

    # -------------------------------------------------------------
    # VII. EMPIRICAL RESULTS & ANALYSIS
    # -------------------------------------------------------------
    add_heading_1("VII. EMPIRICAL RESULTS & ANALYSIS")
    add_heading_2("A. Primary Pre-Registered KSSL Benchmark")
    add_body_p(
        "The primary evaluation criterion was specified in a pre-registered protocol prior to unblinding test evaluations: "
        "Recall at a 5% re-test budget across 50-batch pools over 5 random seeds. Table II and Fig. 4 present the pre-registered results on 19,746 KSSL soils."
    )

    # TABLE II
    p_t2_title = doc.add_paragraph()
    p_t2_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_title.paragraph_format.space_before = Pt(8)
    p_t2_title.paragraph_format.space_after = Pt(2)
    r_t2t = p_t2_title.add_run("TABLE II\nPRE-REGISTERED DETECTION RECALL AT A 5% RE-TEST BUDGET (KSSL BENCHMARK, 19,746 SAMPLES)")
    r_t2t.bold = True
    r_t2t.font.size = Pt(8.5)

    table2 = doc.add_table(rows=6, cols=5)
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2_data = [
        ["Witness Modality", "EdaphNet Recall", "Best Baseline", "Difference", "95% Bootstrap CI"],
        ["W_0 (Prior Only)", "0.238", "0.271 (B_5)", "-0.033", "[-0.049, -0.016]"],
        ["W_1 (Color, Delta E = 0)", "0.416", "0.415 (B_5)", "+0.001", "[-0.022, +0.023]"],
        ["W_1 (Phone, Delta E = 2)", "0.410", "0.396 (B_5)", "+0.014", "[-0.008, +0.038]"],
        ["W_1 (Noisy, Delta E = 4)", "0.382", "0.354 (B_5)", "+0.028", "[+0.010, +0.049]"],
        ["W_3 (Spectrometer)", "0.604", "0.512 (B_5)", "+0.092", "[+0.069, +0.113]"]
    ]
    for row_idx, row in enumerate(table2.rows):
        for col_idx, cell in enumerate(row.cells):
            cell.text = t2_data[row_idx][col_idx]
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.paragraphs[0].paragraph_format.space_after = Pt(2)
            cell.paragraphs[0].paragraph_format.space_before = Pt(2)
            for r in cell.paragraphs[0].runs:
                r.font.size = Pt(8)
                if row_idx == 0 or row_idx == 5:
                    r.bold = True
            top_b = {'val': 'single', 'sz': 8, 'color': '000000'} if row_idx == 0 else ({'val': 'single', 'sz': 4, 'color': '888888'} if row_idx in [1, 5] else None)
            bot_b = {'val': 'single', 'sz': 8, 'color': '000000'} if row_idx == 5 else ({'val': 'single', 'sz': 4, 'color': '000000'} if row_idx == 0 else None)
            set_cell_borders(cell, top=top_b, bottom=bot_b)
            set_cell_margins(cell, top=60, bottom=60, left=60, right=60)

    p_post_t2 = doc.add_paragraph()
    p_post_t2.paragraph_format.space_after = Pt(6)

    add_body_p(
        "Crucially, the pre-registered hypothesis A1—that a commodity smartphone camera witness would outperform all existing methods by at least "
        "5 percentage points under an injected equal error mix—was refuted (+0.014 difference, 95% CI [-0.008, +0.038]). However, with laboratory Vis-NIR spectroscopy (W_3), "
        "EdaphNet decisively outperforms the strongest supervised baseline by +9.2 percentage points (0.604 vs. 0.512, p < 0.001)."
    )

    add_figure(
        FIG_DIR / "fig2_kssl_recall.png",
        "Fig. 4. Pre-registered detection recall across the witness ladder on the KSSL benchmark at a 5% re-test budget. Points indicate 5-seed pooled means "
        "with 95% bootstrap confidence intervals. The spectrometer witness (W_3) provides a decisive +9.2 percentage-point improvement."
    )

    add_heading_2("B. Decomposing the Trade-Off: Swaps vs. Numerical Corruptions")
    add_body_p(
        "Decomposing detection recall by specific error mechanism reveals why aggregate phone color performance was muted: "
        "(1) On specimen swaps, EdaphNet provides an overwhelming advantage: +10.3 percentage points (+0.103, 95% CI: [+0.064, +0.139]) over baseline B_5 "
        "using smartphone color, and +23.1 percentage points (+0.231, 95% CI: [+0.205, +0.258]) using spectroscopy. "
        "(2) Conversely, on isolated numerical corruptions, EdaphNet trails supervised baseline B_5 by -8.2 percentage points (-0.082, 95% CI: [-0.116, -0.050]). "
        "Diagnostic investigation revealed that baseline B_5 implicitly learned the hard stoichiometric inequality SOC <= 1.05 * total carbon. "
        "Because EdaphNet's continuous Gaussian prior models correlation without enforcing hard inequality cutoffs, isolated numerical slips that violated "
        "this inequality were captured more aggressively by the supervised baseline."
    )

    add_figure(
        FIG_DIR / "fig3_swap_vs_value.png",
        "Fig. 5. Difference in detection recall between EdaphNet and supervised baseline B_5 decomposed into specimen swaps and numerical corruptions. "
        "EdaphNet provides an extraordinary +10.3 pp gain on swaps with smartphone color and +23.1 pp with spectroscopy, while trailing on isolated numerical typos."
    )

    add_heading_2("C. Root-Cause Fault Attribution")
    add_body_p(
        "Beyond flagging anomalous reports, EdaphNet's joint combinatorial formulation diagnoses the exact operational fault mechanism (identifying the specific "
        "swap partner or typed corruption operator). As documented in Table III, EdaphNet achieves 84–92% fault attribution in simulation, 89–98% on ICRAF color data, "
        "and 97–100% on KSSL spectrometer data (against 24–29% on KSSL and 32–51% on ICRAF/simulation for rule-based heuristics). "
        "Exact swap-partner identification reaches 87–99% accuracy across high-information witness settings, and 95–98% on KSSL W_3."
    )

    # TABLE III
    p_t3_title = doc.add_paragraph()
    p_t3_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3_title.paragraph_format.space_before = Pt(8)
    p_t3_title.paragraph_format.space_after = Pt(2)
    r_t3t = p_t3_title.add_run("TABLE III\nROOT-CAUSE FAULT ATTRIBUTION AND SWAP-PARTNER IDENTIFICATION ACCURACY")
    r_t3t.bold = True
    r_t3t.font.size = Pt(8.5)

    table3 = doc.add_table(rows=4, cols=4)
    table3.alignment = WD_TABLE_ALIGNMENT.CENTER
    t3_data = [
        ["Dataset & Setting", "Fault Type (EdaphNet)", "Swap-Partner Accuracy", "Rule Heuristic (B6)"],
        ["Simulation (T0)", "84% – 92%", "86% – 98%", "32% – 50%"],
        ["ICRAF (Color W1 / W3)", "89% – 98%", "75% – 99%", "37% – 51%"],
        ["KSSL (Spectrometer W3)", "97% – 100%", "95% – 98%", "24% – 29%"]
    ]
    for row_idx, row in enumerate(table3.rows):
        for col_idx, cell in enumerate(row.cells):
            cell.text = t3_data[row_idx][col_idx]
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.paragraphs[0].paragraph_format.space_after = Pt(2)
            cell.paragraphs[0].paragraph_format.space_before = Pt(2)
            for r in cell.paragraphs[0].runs:
                r.font.size = Pt(8)
                if row_idx == 0 or row_idx == 3:
                    r.bold = True
            top_b = {'val': 'single', 'sz': 8, 'color': '000000'} if row_idx == 0 else ({'val': 'single', 'sz': 4, 'color': '888888'} if row_idx in [1, 3] else None)
            bot_b = {'val': 'single', 'sz': 8, 'color': '000000'} if row_idx == 3 else ({'val': 'single', 'sz': 4, 'color': '000000'} if row_idx == 0 else None)
            set_cell_borders(cell, top=top_b, bottom=bot_b)
            set_cell_margins(cell, top=60, bottom=60, left=60, right=60)

    p_post_t3 = doc.add_paragraph()
    p_post_t3.paragraph_format.space_after = Pt(6)

    add_heading_2("D. Sensitivity to Error Mix")
    add_body_p(
        "Because laboratory error rates vary across robotic automation levels, we performed sensitivity analysis varying the swap share omega from 0.1 to 0.9. "
        "With smartphone color, EdaphNet's performance advantage expands monotonically with swap prevalence, crossing over into a decisive net advantage once "
        "swaps account for >= 60–70% of batch failures. With spectroscopy, the crossover occurs at just 30% swaps. This demonstrates that for highly automated "
        "facilities where transcription errors are eliminated by digital LIMS and sample swaps dominate, low-cost optical witnesses provide decisive protection."
    )

    add_figure(
        FIG_DIR / "fig5_error_mix.png",
        "Fig. 6. Sensitivity of detection advantage (EdaphNet minus B_5) to the proportion of specimen swaps among batch errors. With smartphone color, "
        "EdaphNet outperforms the supervised baseline when swaps represent >= 60–70% of errors; with spectroscopy, crossover occurs at 30% swaps."
    )

    # -------------------------------------------------------------
    # VIII. DEPLOYMENT & DISCUSSION
    # -------------------------------------------------------------
    add_heading_1("VIII. CYBER-PHYSICAL DEPLOYMENT & DISCUSSION")
    add_body_p(
        "To synthesize our findings into operational laboratory practice, we developed a combined two-stage autoverification policy: the system first executes "
        "EdaphNet's joint permutation engine to detect specimen swaps, and subsequently applies deterministic domain boundary checks to catch numeric slips. "
        "Tested on KSSL batches with phone-grade color witnesses (Delta E = 2), the combined policy achieves balanced recall of 0.20–0.25 on swaps and 0.222 on "
        "value corruptions, providing robust protection across both failure modes."
    )
    add_body_p(
        "Operational deployment considerations indicate that the 18 ms inference runtime (17.9 +- 1.2 ms for 281 candidate hypotheses on an AMD Ryzen 5 7520U "
        "laptop-class mobile processor, 4 cores, 8 threads, 2.80 GHz) enables seamless real-time integration into micro-plate workflows. "
        "The 18 ms latency encompasses witness feature prediction, cell likelihood evaluation, hypothesis summation across all 281 permutations, and exact posterior "
        "normalization, enabling inline verification before chemical digestion."
    )

    # -------------------------------------------------------------
    # IX. CONCLUSION
    # -------------------------------------------------------------
    add_heading_1("IX. CONCLUSION & FUTURE WORK")
    add_body_p(
        "EdaphNet establishes a cyber-physical paradigm for laboratory quality assurance, combining non-destructive optical witness sensing with joint Bayesian "
        "inference over structured tray permutations (exact within candidate set S_tray) and typed corruption operators. Evaluated on 23,219 soil samples from KSSL and ICRAF-ISRIC, "
        "while the primary pre-registered claim of an overall advantage for phone color was refuted (+0.014 [-0.008, +0.038]), confirmatory results established a decisive "
        "+9.2 percentage point advantage under laboratory spectroscopy (+0.092 [+0.069, +0.113], p < 0.001). Exploratory sub-analyses revealed that commodity RGB phone color "
        "provides a potent +10.3 percentage point boost specifically in catching specimen swaps, offset by a deficit on isolated numerical slips. In root-cause fault attribution, "
        "EdaphNet achieved 84–92% accuracy in simulation, 89–98% on ICRAF color data, and 97–100% on KSSL spectrometer data (against 24–29% on KSSL for rule-based heuristics), "
        "with 87–99% exact swap-partner identification. Furthermore, we showed that conformal FDR control collapses under calibration pseudo-replication and demonstrated "
        "that non-replicated calibration reliably restores distribution-free validity. Future work includes field validation with in-situ Indian agricultural soil trays "
        "and robotic integration."
    )

    # ACKNOWLEDGMENT
    add_heading_1("ACKNOWLEDGMENT")
    add_body_p(
        "The authors express their deepest gratitude to their faculty guide, Dr. Priya Saminathan, Department of Computational Intelligence, School of "
        "Computer Science and Engineering, Vellore Institute of Technology, Vellore, for her mentorship, technical domain insights, and rigorous guidance. "
        "We also acknowledge VIT Vellore for computational infrastructure and the USDA-NRCS Kellogg Soil Survey Laboratory and ICRAF-ISRIC for providing "
        "open agricultural spectral repositories."
    )

    # REPRODUCIBILITY STATEMENT
    add_heading_1("REPRODUCIBILITY & DATA AVAILABILITY STATEMENT")
    add_body_p(
        "All code, configuration files, trained model weights, and automated evaluation logs are version-controlled and publicly accessible at "
        "https://github.com/Sudeep-Sharma1/edaphnet-v2. The benchmark utilizes open data from the Open Soil Spectral Library (OSSL v1.2, CC-BY 4.0). "
        "Every reported metric, confidence interval, and figure is directly reproducible via committed scripts."
    )

    # -------------------------------------------------------------
    # REFERENCES
    # -------------------------------------------------------------
    add_heading_1("REFERENCES")
    refs = [
        "[1] R. J. Even, M. B. Machmuller, J. M. Lavallee, T. J. Zelikova, and M. F. Cotrufo, \"Large errors in soil carbon measurements attributed to inconsistent sample processing,\" SOIL, vol. 11, no. 1, pp. 17–34, Jan. 2025, doi: 10.5194/soil-11-17-2025.",
        "[2] J. O. Westgard and S. A. Westgard, Basic QC Practices: Training in Statistical Quality Control for Healthcare Laboratories, 4th ed., Madison, WI, USA: Westgard Quality Corporation, 2020.",
        "[3] M. W. Rosenbaum and J. M. Baron, \"Using machine learning-based multianalyte delta checks to detect wrong blood in tube errors,\" Am. J. Clin. Pathol., vol. 150, no. 6, pp. 555–566, Dec. 2018, doi: 10.1093/ajcp/aqy085.",
        "[4] H. Zhou, J. Mueller, M. Kumar, J.-L. Wang, and J. Lei, \"Detecting errors in a numerical response via any regression model,\" J. Data-centric Mach. Res., vol. 1, pp. 1–25, 2024, arXiv:2305.16583.",
        "[5] R. A. Viscarra Rossel et al., \"A global spectral library to characterize the world's soil,\" Earth-Sci. Rev., vol. 155, pp. 198–230, Apr. 2016, doi: 10.1016/j.earscirev.2016.01.012.",
        "[6] J. L. Safanelli et al., \"Open Soil Spectral Library (OSSL): Building reproducible soil calibration models through open development and community engagement,\" PLOS ONE, vol. 20, no. 1, p. e0296545, Jan. 2025, doi: 10.1371/journal.pone.0296545.",
        "[7] J. E. Herrick et al., \"The global Land-Potential Knowledge System (LandPKS): Supporting evidence-based, site-specific land use and management through cloud computing, mobile applications, and crowdsourcing,\" J. Soil Water Conserv., vol. 68, no. 1, pp. 5A–12A, Jan./Feb. 2013, doi: 10.2489/jswc.68.1.5A.",
        "[8] B. K. Stephenson, D. G. Hoch, and L. P. Collette, III, \"Validation of laboratory test data based on predicted values of property-of-interest,\" U.S. Patent 8,352,394 B2, Jan. 8, 2013.",
        "[9] K. W. Broman et al., \"Identification and correction of sample mix-ups in expression genetic studies,\" G3: Genes, Genomes, Genetics, vol. 5, no. 10, pp. 2177–2186, Oct. 2015, doi: 10.1534/g3.115.019778.",
        "[10] J. Schmidinger, R. Gebbers, M.-O. Gasser, V. Barkov, G. M. Wu, and V. I. Adamchuk, \"Rejections based on predictive uncertainty enable reliable routine soil spectroscopy,\" arXiv preprint arXiv:2606.21179, June 2026.",
        "[11] S. Bates, E. Candès, L. Lei, Y. Romano, and M. Sesia, \"Testing for outliers with conformal p-values,\" Ann. Statist., vol. 51, no. 1, pp. 149–178, Feb. 2023, doi: 10.1214/22-AOS2244.",
        "[12] Y. Jin and E. J. Candès, \"Selection by prediction with conformal p-values,\" J. Amer. Statist. Assoc., vol. 118, no. 544, pp. 2533–2545, Dec. 2023, doi: 10.1080/01621459.2023.2185532.",
        "[13] A. N. Angelopoulos and S. Bates, \"Conformal prediction: A gentle introduction,\" Found. Trends Mach. Learn., vol. 16, no. 4, pp. 494–591, 2023, doi: 10.1561/2200000101.",
        "[14] V. Vovk, A. Gammerman, and G. Shafer, Algorithmic Learning in a Random World, New York, NY, USA: Springer, 2005.",
        "[15] Y. Benjamini and Y. Hochberg, \"Controlling the false discovery rate: A practical and powerful approach to multiple testing,\" J. Roy. Statist. Soc. Ser. B, vol. 57, no. 1, pp. 289–300, 1995, doi: 10.1111/j.2517-6161.1995.tb02031.x.",
        "[16] R. J. Tibshirani, R. Foygel Barber, E. J. Candès, and A. Ramdas, \"Conformal prediction under covariate shift,\" in Adv. Neural Inf. Process. Syst. (NeurIPS), vol. 32, pp. 2530–2540, Dec. 2019."
    ]
    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.left_indent = Inches(0.3)
        p_ref.paragraph_format.first_line_indent = Inches(-0.3)
        p_ref.paragraph_format.space_after = Pt(3)
        r = p_ref.add_run(ref)
        r.font.size = Pt(8.5)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Deliverables: Project_review_3.docx, EdaphNet_Review_Revised_2.docx, EdaphNet_Review_Revised.docx
    out_targets = [
        REPORTS_DIR / "Project_review_3.docx",
        RESULTS_DIR / "Project_review_3.docx",
        RESULTS_DIR / "EdaphNet_Review_Revised_2.docx",
        REPORTS_DIR / "EdaphNet_Review_Revised.docx",
        RESULTS_DIR / "EdaphNet_Review_Revised.docx",
    ]
    for target in out_targets:
        doc.save(str(target))
        print(f"Successfully generated DOCX at: {target}")


if __name__ == "__main__":
    create_document()
