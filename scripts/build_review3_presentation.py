#!/usr/bin/env python3
"""
Generate the official 20-slide submission-ready PowerPoint presentation
for BCSE497J Project-I Final Review (Review-3), adhering strictly to the
VIT SCOPE university presentation template.

Authors:
  - Udit Shokeen (Reg. No: 23BCB0001)
  - Armaan Srivastava (Reg. No: 23BCE2318)
  - Sudeep Sharma (Reg. No: 23BDS0315)
Supervisor:
  - Dr. Priya Saminathan, Department of Computational Intelligence, SCOPE, VIT Vellore
Date: 28-10-2026
"""

import os
import shutil
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "Review 3- 28-10- 2026.pptx"
OUTPUT_PATH = ROOT / "BCSE497J_Review3_AgriSense_AI.pptx"
FIG_DIR = ROOT / "paper" / "figures"
if not FIG_DIR.exists():
    FIG_DIR = ROOT / "docs" / "paper" / "figures"

# Theme colors matching VIT SCOPE template
COLOR_PRIMARY_NAVY = RGBColor(14, 43, 92)    # #0e2b5c
COLOR_TEAL = RGBColor(0, 128, 128)           # #008080
COLOR_DARK_TEXT = RGBColor(30, 41, 59)       # #1e293b
COLOR_MUTED_TEXT = RGBColor(100, 116, 139)   # #64748b
COLOR_ACCENT_AMBER = RGBColor(180, 83, 9)    # #b45309
COLOR_CARD_BG = RGBColor(248, 250, 252)      # #f8fafc
COLOR_CARD_BORDER = RGBColor(226, 232, 240)  # #e2e8f0
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_SUCCESS = RGBColor(22, 101, 52)        # #166534
COLOR_DANGER = RGBColor(153, 27, 27)         # #991b1b


def clear_slide_content(slide):
    """Remove non-placeholder shapes or custom shapes while preserving standard master elements."""
    to_remove = []
    for shp in slide.shapes:
        # Keep slide placeholders if they are standard date, footer, slide number, or title
        # But clear out older tables, pictures, and custom text boxes
        if shp.name in ["Picture 4", "Title 6", "object 3"]:
            continue  # Slide 1 special shapes
        if shp.is_placeholder:
            p_type = shp.placeholder_format.type
            # 1: Title, 2: Body, 13: Slide Number, 14: Footer, 15: Date
            if p_type in [13, 14, 15]:
                continue
            if p_type in [1, 2]:
                continue
        to_remove.append(shp)

    for shp in to_remove:
        sp = shp._element
        sp.getparent().remove(sp)


def update_footer_and_date(slide, slide_num):
    """Update standard footer placeholders with 28-10-2026, SCOPE, and slide number."""
    for shp in slide.shapes:
        if shp.is_placeholder:
            p_type = shp.placeholder_format.type
            # Date placeholder
            if "Date" in shp.name or p_type == 15:
                if shp.has_text_frame:
                    shp.text_frame.text = "28-10-2026"
                    for p in shp.text_frame.paragraphs:
                        p.font.size = Pt(10)
                        p.font.color.rgb = COLOR_MUTED_TEXT
            # Footer placeholder
            elif "Footer" in shp.name or p_type == 14:
                if shp.has_text_frame:
                    shp.text_frame.text = "SCOPE"
                    for p in shp.text_frame.paragraphs:
                        p.font.size = Pt(10)
                        p.font.color.rgb = COLOR_MUTED_TEXT
            # Slide number placeholder
            elif "Slide Number" in shp.name or p_type == 13:
                if shp.has_text_frame:
                    shp.text_frame.text = str(slide_num)
                    for p in shp.text_frame.paragraphs:
                        p.font.size = Pt(10)
                        p.font.color.rgb = COLOR_MUTED_TEXT


def set_slide_title(slide, title_text):
    """Set the slide title text cleanly."""
    for shp in slide.shapes:
        if shp.is_placeholder:
            p_type = shp.placeholder_format.type
            if p_type == 1 or "Title" in shp.name or "object 2" in shp.name:
                if shp.has_text_frame:
                    shp.text_frame.text = title_text
                    for p in shp.text_frame.paragraphs:
                        p.font.name = "Calibri"
                        p.font.size = Pt(22)
                        p.font.bold = True
                        p.font.color.rgb = COLOR_PRIMARY_NAVY
                    return


def add_header_bar(slide, title_text):
    """Add a clean top title bar if placeholder title is not present."""
    # Find existing title placeholder
    for shp in slide.shapes:
        if shp.has_text_frame and ("Title" in shp.name or "object 2" in shp.name):
            set_slide_title(slide, title_text)
            return

    # Otherwise create a title text box
    tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(11.5), Inches(0.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = "Calibri"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY_NAVY


def add_card(slide, left, top, width, height, title, items, border_color=COLOR_CARD_BORDER, bg_color=COLOR_CARD_BG, title_color=COLOR_PRIMARY_NAVY):
    """Create a structured card with title and bullet points."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.5)

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.15)
    tf.margin_bottom = Inches(0.15)

    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.name = "Calibri"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = title_color
    p0.space_after = Pt(6)

    for item in items:
        p = tf.add_paragraph()
        p.text = "• " + item
        p.font.name = "Calibri"
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.space_after = Pt(4)


def add_table(slide, left, top, width, height, headers, rows, col_widths=None):
    """Add a professionally styled data table."""
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
    table = table_shape.table

    if col_widths and len(col_widths) == num_cols:
        for idx, w in enumerate(col_widths):
            table.columns[idx].width = w

    # Header Row
    for col_idx, header in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY_NAVY
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = header
        p.alignment = PP_ALIGN.CENTER
        p.font.name = "Calibri"
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    # Data Rows
    for row_idx, row_data in enumerate(rows):
        bg = COLOR_CARD_BG if row_idx % 2 == 0 else COLOR_WHITE
        for col_idx, val in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = str(val)
            p.font.name = "Calibri"
            p.font.size = Pt(9.5)
            p.font.color.rgb = COLOR_DARK_TEXT
            if col_idx == 0:
                p.alignment = PP_ALIGN.LEFT
                p.font.bold = True
            else:
                p.alignment = PP_ALIGN.CENTER

    return table_shape


def build_presentation():
    print(f"Loading base template from {TEMPLATE_PATH}...")
    prs = pptx.Presentation(TEMPLATE_PATH)

    # Ensure exactly 20 slides
    while len(prs.slides) > 20:
        rId = prs.slides._sldIdLst[-1].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[-1]

    while len(prs.slides) < 20:
        prs.slides.add_slide(prs.slide_layouts[1])

    print(f"Working slide count: {len(prs.slides)}")

    # -------------------------------------------------------------
    # SLIDE 1: Title & Administrative Metadata
    # -------------------------------------------------------------
    s1 = prs.slides[0]
    update_footer_and_date(s1, 1)
    for shp in s1.shapes:
        if shp.name == "Title 6" or (shp.is_placeholder and "Title" in shp.name):
            tf = shp.text_frame
            tf.word_wrap = True
            tf.clear()
            p0 = tf.paragraphs[0]
            p0.text = "B.Tech  |  BCSE497J – Project-I (Final Review — Review 3)"
            p0.font.name = "Calibri"
            p0.font.size = Pt(16)
            p0.font.bold = True
            p0.font.color.rgb = COLOR_MUTED_TEXT

            p1 = tf.add_paragraph()
            p1.text = "AgriSense AI: An Explainable Smart Crop Health Management System"
            p1.font.name = "Calibri"
            p1.font.size = Pt(23)
            p1.font.bold = True
            p1.font.color.rgb = COLOR_PRIMARY_NAVY
            p1.space_before = Pt(4)

            p2 = tf.add_paragraph()
            p2.text = "Cyber-Physical Verification of Soil Laboratory Reports via Optical Witnesses & Conformal Calibration (EdaphNet Engine)"
            p2.font.name = "Calibri"
            p2.font.size = Pt(12.5)
            p2.font.italic = True
            p2.font.color.rgb = COLOR_TEAL
            p2.space_before = Pt(3)

        elif shp.name == "object 3" or (shp.has_text_frame and "Team members" in shp.text_frame.text):
            tf = shp.text_frame
            tf.word_wrap = True
            tf.clear()

            p_h = tf.paragraphs[0]
            p_h.text = "Project ID: BCSE497J-P1-2026-SCOPE-042  |  Date: 28 October 2026"
            p_h.font.name = "Calibri"
            p_h.font.size = Pt(11)
            p_h.font.bold = True
            p_h.font.color.rgb = COLOR_PRIMARY_NAVY
            p_h.space_after = Pt(8)

            p_t = tf.add_paragraph()
            p_t.text = "Team Members (School of Computer Science and Engineering):"
            p_t.font.name = "Calibri"
            p_t.font.size = Pt(11)
            p_t.font.bold = True
            p_t.font.color.rgb = COLOR_DARK_TEXT

            members = [
                "1. Udit Shokeen (Reg. No: 23BCB0001) — B.Tech CSE (Bioinformatics)",
                "2. Armaan Srivastava (Reg. No: 23BCE2318) — B.Tech Computer Science and Engineering",
                "3. Sudeep Sharma (Reg. No: 23BDS0315) — B.Tech CSE (Data Science)",
            ]
            for m in members:
                pm = tf.add_paragraph()
                pm.text = "   " + m
                pm.font.name = "Calibri"
                pm.font.size = Pt(10.5)
                pm.font.color.rgb = COLOR_DARK_TEXT

            pg = tf.add_paragraph()
            pg.text = "Faculty Guide & Supervisor:"
            pg.font.name = "Calibri"
            pg.font.size = Pt(11)
            pg.font.bold = True
            pg.font.color.rgb = COLOR_DARK_TEXT
            pg.space_before = Pt(6)

            pg_name = tf.add_paragraph()
            pg_name.text = "   Dr. Priya Saminathan, Associate Professor / Senior Member, IEEE\n   Department of Computational Intelligence, SCOPE, VIT Vellore"
            pg_name.font.name = "Calibri"
            pg_name.font.size = Pt(10)
            pg_name.font.color.rgb = COLOR_DARK_TEXT

    # -------------------------------------------------------------
    # SLIDE 2: Problem Statement & Motivation
    # -------------------------------------------------------------
    s2 = prs.slides[1]
    clear_slide_content(s2)
    update_footer_and_date(s2, 2)
    add_header_bar(s2, "Problem Statement & Practical Motivation")

    add_card(s2, Inches(0.6), Inches(1.3), Inches(5.6), Inches(4.8),
             "Agronomic & Economic Stakes of Soil Testing",
             [
                 "Soil test reports govern billion-dollar downstream interventions: chemical fertiliser blends (NPK), agricultural lime dosage, and regulated soil carbon credits.",
                 "High Inter-Laboratory Inconsistency: A rigorous proficiency trial across 8 commercial soil testing laboratories found that 28% of reported soil organic carbon (SOC) values fell outside acceptable bounds (Even et al., SOIL 2025).",
                 "Unilateral Farmer Exposure: Farmers and agronomists receive isolated numerical certificates without any independent means to verify whether the report is valid for their physical soil sample.",
                 "Economic Bottleneck of 100% Retesting: Analyzing every sample in duplicate doubles chemical reagent, technician, and instrument costs (> $50/sample). Laboratories urgently need a prioritized top-5% re-test queue."
             ], border_color=COLOR_PRIMARY_NAVY)

    add_card(s2, Inches(6.5), Inches(1.3), Inches(5.6), Inches(4.8),
             "The Dual Laboratory Failure Modes",
             [
                 "Failure Mode 1: Physical Sample Swaps (Invisible to Conventional QA)\n  • Occurs via tube mislabelling, rack transpositions, or robotic 1-well tray shifts.\n  • Critically, a swapped report contains chemically valid data of a real soil.\n  • Result: All univariate range checks, stoichiometric rules, and multivariate density checks pass 100% cleanly! Only physical observation of the sample can reveal the mismatch.",
                 "Failure Mode 2: Typed Numerical Corruptions\n  • Manual transcription or automated data transfer slips: decimal shifts (x10, /10), unit confusion (% vs g/kg), transposed digits (0.16 -> 0.61), or column interchanges.\n  • Often fall inside plausible regional boundaries and evade crude range filters.",
                 "The Epistemic Gap: Conventional quality assurance operates purely in 'report space'; AgriSense AI bridges the cyber-physical gap by leveraging an optical witness."
             ], border_color=COLOR_ACCENT_AMBER)

    # -------------------------------------------------------------
    # SLIDE 3: Objectives & Scope of Project-I
    # -------------------------------------------------------------
    s3 = prs.slides[2]
    clear_slide_content(s3)
    update_footer_and_date(s3, 3)
    add_header_bar(s3, "Objectives & Scope of Project-I")

    add_card(s3, Inches(0.6), Inches(1.3), Inches(7.2), Inches(4.8),
             "Formal Research Objectives (RO1 – RO5)",
             [
                 "RO1 [Bayesian Batch Model]: Formulate exact Bayesian joint inference over a structured 281-permutation tray hypothesis space (S_tray) and a 5-group typed numerical corruption library (C).",
                 "RO2 [Multi-Analyte Stoichiometric Modeling]: Construct a multi-property latent Gaussian model with LightGBM predictive mean and full out-of-fold covariance (Sigma) to detect inter-analyte contradictions.",
                 "RO3 [Distribution-Free Calibration]: Implement finite-sample conformal calibration guaranteeing empirical False Discovery Rate control (q = 0.10) under rigorous non-exchangeability diagnostics.",
                 "RO4 [Pre-Registered Benchmarking]: Evaluate detection recall at 5% re-test budget against 8 baseline algorithms across 23,219 real soils from KSSL and ICRAF-ISRIC under committed Git rules.",
                 "RO5 [Root-Cause Attribution & Edge Deployment]: Accurately diagnose error type (swap vs value slip), identify swap partners, propose numerical repairs, and achieve < 20 ms batch inference on consumer CPU."
             ], border_color=COLOR_PRIMARY_NAVY)

    add_card(s3, Inches(8.1), Inches(1.3), Inches(4.0), Inches(4.8),
             "Project Scope & Explicit Boundaries",
             [
                 "In Scope (Project-I Deliverables):\n  • Laboratory-grade Vis-NIR spectra & CIELAB colour space (D65/2°).\n  • Sensor noise simulation (phone camera Delta E = 0, 2, 4, 8).\n  • 23,219 real soil samples with verified chemistry.\n  • Exact permutation Bayesian engine.",
                 "Deliberately Out of Scope:\n  • In-the-wild raw smartphone photos without calibration colour cards (requires Paper 2 field trial).\n  • Unrecorded field lab errors (addressed via rigorous seeded error injection protocols).\n  • Indian agro-climatic zones (planned for Paper 2 pilot with VIT VAIAL laboratory)."
             ], border_color=COLOR_TEAL)

    # -------------------------------------------------------------
    # SLIDE 4: Literature Survey & Gap Analysis
    # -------------------------------------------------------------
    s4 = prs.slides[3]
    clear_slide_content(s4)
    update_footer_and_date(s4, 4)
    add_header_bar(s4, "Literature Survey & Research Gap Analysis")

    headers_l = ["Ref / System", "Domain", "Physical Witness", "Swap Inference", "Typed Attribution", "Conformal FDR", "Limitation Addressed"]
    rows_l = [
        ["Even et al. (SOIL 2025)", "Soil Chemistry", "None", "None", "None", "None", "Demonstrated 28% inter-lab error in SOC; lacks autoverification"],
        ["LandPKS / Viscarra (2016)", "Soil Sensing", "Phone / Vis-NIR", "None", "None", "None", "Predicts properties; cannot verify or audit laboratory reports"],
        ["Rosenbaum & Baron (2018)", "Clinical Pathology", "None (Delta)", "Pairwise", "None", "None", "Requires rich longitudinal patient history; inapplicable to field soil"],
        ["Broman et al. (G3 2015)", "Genomics", "Genotype Matrix", "Hungarian Opt", "None", "None", "Requires near-perfect witness; ignores numerical reporting corruptions"],
        ["Zhou et al. Cleanlab (2023)", "Machine Learning", "None", "None", "Score only", "None", "Generic residual scoring; cannot resolve sample swaps or tray shifts"],
        ["Bates et al. (Ann. Stat. 2023)", "Conformal Testing", "None", "None", "None", "Theory (FDR)", "General outlier testing; susceptible to batch pseudo-replication"],
        ["AgriSense AI (EdaphNet)", "Cyber-Physical QA", "Colour & Vis-NIR", "Exact Joint S_tray", "97-100% Attribution", "Strict Sample-Level", "Unified joint batch autoverification, attribution, and repair"]
    ]
    add_table(s4, Inches(0.6), Inches(1.3), Inches(11.5), Inches(3.2), headers_l, rows_l,
              [Inches(2.1), Inches(1.4), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.4), Inches(2.1)])

    add_card(s4, Inches(0.6), Inches(4.7), Inches(11.5), Inches(1.5),
             "Key Identified Research Gaps (G1 – G4)",
             [
                 "G1 (Absence of Physical Witness): Prior autoverification relies strictly on report internal consistency, leaving sample swaps completely undetected.",
                 "G2 (No Joint Batch Formulation): Genomic tools detect swaps only; clinical tools detect isolated drifts. No system models both swaps and value corruptions jointly.",
                 "G3 (Lack of Actionable Attribution): Existing error detectors output an uninterpretable anomaly score without naming the fault type or recommending a repair.",
                 "G4 (Conformal Pseudo-Replication): Standard multi-sample calibration breaks down when calibration samples are re-used across batches, inflating FDR to 57%."
             ], border_color=COLOR_PRIMARY_NAVY)

    # -------------------------------------------------------------
    # SLIDE 5: System Architecture & Dual Pipelines
    # -------------------------------------------------------------
    s5 = prs.slides[4]
    clear_slide_content(s5)
    update_footer_and_date(s5, 5)
    add_header_bar(s5, "System Architecture: Dual-Pipeline Framework")

    fig0_path = FIG_DIR / "fig0_method.png"
    if fig0_path.exists():
        s5.shapes.add_picture(str(fig0_path), Inches(0.6), Inches(1.3), Inches(6.8), Inches(4.8))

    add_card(s5, Inches(7.6), Inches(1.3), Inches(4.5), Inches(4.8),
             "Architectural Decoupling & Responsibilities",
             [
                 "Dual-Pipeline Organization:\n  1. Offline Research & Calibration Pipeline: Generates location-disjoint splits, trains LightGBM latent models, fits out-of-fold covariance, and establishes exchangeable conformal sets.\n  2. Cyber-Physical Runtime Pipeline: Evaluates physical samples alongside electronic laboratory batches in real time.",
                 "Core Runtime Execution Flow:\n  • Physical sample arrives -> Optical witness acquired (phone colour or spectrum).\n  • Prior latent prediction: p(z|w) = N(mu(w), Sigma).\n  • Laboratory analytical batch printed (24 reports).\n  • Joint inference engine computes likelihood matrix L(j, i) across 281 permutations in S_tray and error library C.\n  • Outputs: Suspicion score s_j, fault attribution, candidate correction T_c^{-1}(r_j), and prioritized 5% re-test list.",
                 "Computational Speed: Full 24-well batch inference executes in 17.9 ± 1.2 ms on AMD Ryzen 5 7520U CPU."
             ], border_color=COLOR_PRIMARY_NAVY)

    # -------------------------------------------------------------
    # SLIDE 6: Multi-Modal Data Engineering & Optical Witness Ladder
    # -------------------------------------------------------------
    s6 = prs.slides[5]
    clear_slide_content(s6)
    update_footer_and_date(s6, 6)
    add_header_bar(s6, "Data Engineering & Multi-Modal Datasets")

    headers_d = ["Dataset", "Geographic Scope", "Samples / Profiles", "Measured Laboratory Properties", "Role in EdaphNet"]
    rows_d = [
        ["KSSL Vis-NIR (OSSL v1.2)", "United States (Continental)", "19,746 samples\n(6,999 locations)", "Organic Carbon (OC), Total Nitrogen (N),\nTotal Carbon (Ctot), Vis-NIR spectrum", "Pre-registered benchmark (X5), unknown error test (X7), live demo"],
        ["ICRAF-ISRIC (OSSL v1.2)", "Sub-Saharan Africa (18 nations)", "3,473 samples\n(553 profiles)", "pH, OC, Clay, Sand, CEC, Ca, Mg, K,\nVis-NIR diffuse reflectance", "Initial real evaluation (X3), calibration diagnostic (X4), cross-continent check"],
        ["Synthetic T0", "Controlled Copula", "7,200 simulated batches\n(30 parameter settings)", "8 correlated properties with parametric\nwitness informativeness lambda in [0, 4]", "Theoretical mechanism verification (X1) & swap attribution bounds"]
    ]
    add_table(s6, Inches(0.6), Inches(1.3), Inches(11.5), Inches(2.6), headers_d, rows_d,
              [Inches(2.4), Inches(2.2), Inches(2.0), Inches(2.6), Inches(2.3)])

    add_card(s6, Inches(0.6), Inches(4.1), Inches(5.6), Inches(2.2),
             "The 5-Tier Optical Witness Ladder",
             [
                 "W0 (No Witness): Pure laboratory chemistry baseline.",
                 "W1 (CIELAB Colour): L*a*b* under D65 illuminant with camera noise Delta E in {0, 2, 4, 8} (Delta E = 2 corresponds to high-end phone).",
                 "W2 (10-Band Visible): Discrete visible multispectral bands.",
                 "W3 (Vis-NIR Spectrometer): 100 principal components of 350-2500 nm diffuse reflectance."
             ], border_color=COLOR_TEAL)

    add_card(s6, Inches(6.5), Inches(4.1), Inches(5.6), Inches(2.2),
             "Rigorous Leakage-Free Quality Controls",
             [
                 "Location-Disjoint Splitting: Partitioned 50% Train / 15% Calibration / 35% Test strictly by spatial profile ID to prevent spatial autocorrelation leakage.",
                 "Forensic OSSL Cleaning: Identified and eliminated 23,852 empty spectral rows present in raw metadata tables (Decision D-008).",
                 "Rebuild Checksum Verification: Rebuilding dataset from scratch yields bit-identical MD5 hashes across all 10 numpy arrays."
             ], border_color=COLOR_ACCENT_AMBER)

    # -------------------------------------------------------------
    # SLIDE 7: End-to-End Operational Workflow
    # -------------------------------------------------------------
    s7 = prs.slides[6]
    clear_slide_content(s7)
    update_footer_and_date(s7, 7)
    add_header_bar(s7, "End-to-End Operational Workflow & Triage Policy")

    steps = [
        ("Step 1: Optical Sensing", ["Physical soil sample observed prior to chemical analysis.", "Smartphone camera with 24-patch Macbeth card or Vis-NIR probe.", "Colorimetric calibration: D65/2° CIELAB (L*, a*, b*)."]),
        ("Step 2: Latent Property Mapping", ["Predicts property distributions on Gaussian latent scale.", "Trained LightGBM regressors yield mean mu(w_i).", "Full residual covariance Sigma captures inter-analyte links."]),
        ("Step 3: Joint Batch Bayesian Inference", ["All 24 batch reports scored jointly across S_tray (281 hypotheses).", "Evaluates likelihood L(j, i) against 5-group error library C.", "Calculates exact posterior P(pi | R, W) and report suspicion s_j."]),
        ("Step 4: Actionable Laboratory Decision", ["Top-5% Re-test Queue: Flags most suspicious samples for re-run.", "Conformal P-values: Guarantees FDR <= 0.10 via BH step-up.", "Attribution & Repair: Emits swap partner or proposed value T_c^{-1}."])
    ]

    col_w = Inches(2.7)
    for idx, (stitle, sitems) in enumerate(steps):
        left_pos = Inches(0.6 + idx * 2.9)
        add_card(s7, left_pos, Inches(1.3), col_w, Inches(4.8), stitle, sitems, border_color=COLOR_PRIMARY_NAVY)

    # -------------------------------------------------------------
    # SLIDE 8: Methodology: Multi-Property Latent Gaussian Model
    # -------------------------------------------------------------
    s8 = prs.slides[7]
    clear_slide_content(s8)
    update_footer_and_date(s8, 8)
    add_header_bar(s8, "Methodology: Multi-Property Latent Gaussian Model")

    add_card(s8, Inches(0.6), Inches(1.3), Inches(5.6), Inches(4.8),
             "Latent Gaussian Formulation & Quantile Mapping",
             [
                 "Standardization via Monotonic Quantile Scalers:\n  • Chemical measurements (OC, N, Ctot, pH) follow highly skewed, non-Gaussian distributions across orders of magnitude.\n  • We apply strictly monotonic empirical quantile scalers g_p(r_p) to project reports onto standardized latent variables:\n    z_p = g_p(r_p) ~ N(0, 1)  ==>  z = g(r) ~ N(0, I)",
                 "Predictive Latent Conditional Distribution:\n  • Conditional on optical witness w_i, the joint latent properties follow a multivariate Gaussian distribution:\n    p(z | w_i) = Normal( mu(w_i),  Sigma )\n  • Mean Vector mu(w_i): Predicted by property-specific LightGBM regressors (300 trees, lr=0.05, 15 leaves, subsample 0.8).\n  • Covariance Matrix Sigma: Empirical out-of-fold residual covariance.",
                 "Note on Terminology: This is a latent Gaussian model with boosted-tree conditional mean, not a Gaussian Process regression (no kernel matrix)."
             ], border_color=COLOR_PRIMARY_NAVY)

    add_card(s8, Inches(6.5), Inches(1.3), Inches(5.6), Inches(4.8),
             "The Power of the Full Covariance Matrix (Sigma)",
             [
                 "Exploiting Natural Biogeochemical Stoichiometry:\n  • In soil science, chemical properties are tightly coupled by biological stoichiometry (e.g. Redfield-style C:N ratios).\n  • Because Sigma is a full covariance matrix rather than diagonal, the model encodes exact multi-analyte correlations.",
                 "Detecting Errors in Weakly Visible Properties:\n  • Smartphone colour (CIELAB) directly explains Organic Carbon well (R² = 0.70) but Total Nitrogen poorly (R² = 0.55 on KSSL).\n  • However, an erroneous Nitrogen value (e.g. typed 10x too high) severely violates the learned C:N covariance structure!\n  • Result: The system flags the Nitrogen reporting corruption as an internal contradiction, even when the witness alone has weak direct visibility.",
                 "Jacobian Density Transformation:\n  • Likelihood evaluations rigorously account for the variable change Jacobian: |J_{g o T_c^{-1}}(r_j)|."
             ], border_color=COLOR_TEAL)

    # -------------------------------------------------------------
    # SLIDE 9: Mathematical Formulation: Structured Permutations & Error Library
    # -------------------------------------------------------------
    s9 = prs.slides[8]
    clear_slide_content(s9)
    update_footer_and_date(s9, 9)
    add_header_bar(s9, "Mathematical Formulation: Permutations & Error Library")

    add_card(s9, Inches(0.6), Inches(1.3), Inches(5.6), Inches(4.8),
             "Structured Tray Permutation Subgroup (S_tray)",
             [
                 "Combinatorial Challenge: For a 24-well laboratory tray, the full symmetric group S_24 has 24! ≈ 6.2 x 10^23 permutations, rendering exhaustive Bayesian search intractable.",
                 "The 281 Mechanistic Permutation Hypotheses (S_tray):\n  • Exact candidate set S_tray contains precisely 1 + 276 + 4 = 281 permutations:\n    1. Identity (pi_0): No handling mistake (clean batch).\n    2. Pair Transpositions: All C(24, 2) = 276 pair swaps, including the 23 physically adjacent vial transpositions.\n    3. Cyclic Tray Rotations: 4 permutations representing ±1 and ±2 position shifts (e.g. robotic tray misalignment).",
                 "Mechanistic Bayesian Prior P(pi):\n  • Total handling failure prior rho = 0.10 (benchmark setting).\n  • Distributed across mechanical failure modes:\n    - Adjacent transpositions: 50% mass (0.50 * rho / 23)\n    - Cyclic tray shifts: 30% mass (0.30 * rho / 4)\n    - Non-adjacent pair swaps: 20% mass (0.20 * rho / 253)"
             ], border_color=COLOR_PRIMARY_NAVY)

    add_card(s9, Inches(6.5), Inches(1.3), Inches(5.6), Inches(4.8),
             "Typed Numerical Corruption Library (C)",
             [
                 "Realistic Laboratory Data Entry Error Operators:\n  • Modeled at most one corrupted analyte value per report.\n  • Equal prior probability across 5 operational error groups:",
                 "1. Decimal Slip: r -> r * 10 or r / 10\n   • Example: OC = 0.82% accidentally keyed as 8.20%.",
                 "2. Unit Confusion: Standard conversion factor mismatch\n   • Example: OC = 1.2% reported as 12.0 (g/kg).",
                 "3. Digit Transposition: Adjacent digits inverted\n   • Example: 0.16% typed as 0.61%.",
                 "4. Column Interchange: Two columns swapped\n   • Example: Organic Carbon and Nitrogen values interchanged.",
                 "5. Gross Analytical Error: Multiplicative error gamma in [0.2, 5.0]\n   • Example: Pipette calibration failure leading to 2x over-titration.",
                 "Uncorrupted Case: c = none explicitly included in C to enable clean posterior estimation."
             ], border_color=COLOR_ACCENT_AMBER)

    # -------------------------------------------------------------
    # SLIDE 10: Joint Batch Bayesian Inference Engine
    # -------------------------------------------------------------
    s10 = prs.slides[9]
    clear_slide_content(s10)
    update_footer_and_date(s10, 10)
    add_header_bar(s10, "Joint Batch Bayesian Inference Engine")

    add_card(s10, Inches(0.6), Inches(1.3), Inches(5.6), Inches(4.8),
             "Bayesian Mathematical Formulation",
             [
                 "Marginal Report-Sample Evidence Likelihood L(j, i):\n  • Probability that report r_j originates from sample i with witness w_i, integrating over all possible corruptions c in C:\n    L(j, i) = Sum_{c in C} P(c) * phi( g(T_c^{-1}(r_j)); mu(w_i), Sigma ) * |J_{g o T_c^{-1}}(r_j)|\n  • Where phi is Gaussian density and J is the transformation Jacobian.",
                 "Batch Permutation Posterior P(pi | R, W):\n  • Exact posterior over the candidate permutation set S_tray:\n    P(pi | R, W) proportional to P(pi) * Prod_{j=1}^{24} [ L(j, pi(j)) / L(j, j) ]\n  • Normalised strictly over S_tray, ensuring exact inference.",
                 "Per-Report Decision Marginals:\n  • P(moved_j) = Sum_{pi in S_tray: pi(j) != j} P(pi | R, W)\n  • P(clean_j) = (1 - P(moved_j)) * P(c = none | r_j, w_j)\n  • Report Suspicion Score: s_j = 1 - P(clean_j)"
             ], border_color=COLOR_PRIMARY_NAVY)

    add_card(s10, Inches(6.5), Inches(1.3), Inches(5.6), Inches(4.8),
             "Actionable Outputs & Execution Throughput",
             [
                 "Root-Cause Fault Attribution:\n  • If P(moved_j) > P(clean_j): Diagnosed as Sample Swap, identifying the most probable swap partner k* = argmax_k P(pi(j)=k | R, W).\n  • If P(moved_j) <= P(clean_j) and s_j is elevated: Diagnosed as Numerical Corruption, identifying fault type c* = argmax_{c != none} P(c | r_j, w_j).",
                 "Candidate Numerical Value Repair:\n  • Emits proposed corrected value r_corr = T_{c*}^{-1}(r_j) to assist laboratory technicians during investigation.",
                 "Computational Complexity & Latency:\n  • Calculating L(j, i) takes 24 x 24 = 576 evaluations.\n  • Evaluating all 281 hypotheses takes 281 vector products.\n  • Total wall-clock latency: 17.9 ± 1.2 ms on consumer AMD Ryzen 5 CPU (pure Python / NumPy, zero GPU needed)!"
             ], border_color=COLOR_TEAL)

    # -------------------------------------------------------------
    # SLIDE 11: Conformal Calibration & The Pseudo-Replication Theorem
    # -------------------------------------------------------------
    s11 = prs.slides[10]
    clear_slide_content(s11)
    update_footer_and_date(s11, 11)
    add_header_bar(s11, "Conformal Calibration & Pseudo-Replication Theorem")

    add_card(s11, Inches(0.6), Inches(1.3), Inches(5.6), Inches(4.8),
             "The Pseudo-Replication Flaw Discovered",
             [
                 "Conformal P-Value Mechanics:\n  • Calibration set S_cal = {s_1^cal, ..., s_N^cal} of clean reports.\n  • Conformal p-value for test report score s_j:\n    p_j = ( 1 + #{ k : s_k^cal >= s_j } ) / ( N + 1 )\n  • Under exchangeability, p_j ~ Uniform(0, 1) on clean data, allowing Benjamini-Hochberg (BH) FDR control at level q = 0.10.",
                 "The Pseudo-Replication Defect (Decisions D-016 & D-017):\n  • Initial step-5 implementation reused 511 calibration samples across 400 calibration batches.\n  • Counting the same sample multiple times created artificial score clustering, violating exchangeability.\n  • Consequence: Conformal p-values collapsed towards zero, inflating empirical FDR from 0.10 to 0.57 (57% false alarms)!",
                 "Scientific Integrity: Openly documented in research dossier as a design error rather than concealed."
             ], border_color=COLOR_DANGER)

    add_card(s11, Inches(6.5), Inches(1.3), Inches(5.6), Inches(4.8),
             "The Mathematical Remedy & Sample Complexity",
             [
                 "The Proven Fix (One Score Per Distinct Sample):\n  • Restricting calibration to exactly one score per unique geographic soil sample (N ≈ 2,800 distinct samples on KSSL) restored true exchangeability.\n  • Empirical Result: Realised FDR immediately fell from 0.57 -> 0.00 (well within nominal q = 0.10 bound)!",
                 "Finite-Sample Complexity Bound m / (q(N + 1)):\n  • Conformal p-values have a discrete minimum floor: 1 / (N + 1).\n  • For BH at level q over a pool of m reports, rejection requires at least m / ( q * (N + 1) ) reports to reach that floor.\n  • In large pools (m = 1,200), threshold requires 5 reports; power drops.\n  • Testing batch-by-batch (m = 24) completely eliminates this floor bottleneck, restoring EdaphNet detection power to 0.19 – 0.25 at FDR ≈ 0.10."
             ], border_color=COLOR_SUCCESS)

    # -------------------------------------------------------------
    # SLIDE 12: Implementation Details & Tech Stack
    # -------------------------------------------------------------
    s12 = prs.slides[11]
    clear_slide_content(s12)
    update_footer_and_date(s12, 12)
    add_header_bar(s12, "Implementation Details & Technology Stack")

    headers_t = ["Layer / Module", "Technology", "Version", "Design Rationale & Architectural Purpose"]
    rows_t = [
        ["Core Language", "Python", "3.14 (64-bit)", "Universal scientific ecosystem; unifies core algorithms, pipelines, and UI"],
        ["Numeric & Statistics", "NumPy / SciPy / Pandas", "2.5 / 1.18 / 3.0", "Vectorized hypothesis evaluation, covariance modeling, chunked data handling"],
        ["Machine Learning", "LightGBM / Scikit-learn", "4.7 / 1.9", "Gradient-boosted decision trees for latent regression; fast CPU training"],
        ["Colorimetry Science", "colour-science", "0.4.6", "Standard CIE 1976/2000 colorimetry, D65 illuminant, ΔE sensor noise simulation"],
        ["Edge Computer Vision", "PyTorch / Torchvision", "2.6 / 0.21", "MobileNetV3-Large feature extraction for farmer leaf disease diagnosis"],
        ["Verification Suite", "pytest", "8.3", "34 automated unit/integration tests passing in CI; bit-identical reproducibility"],
        ["Demonstration Server", "Python Standard HTTP", "Built-in", "Zero-dependency offline web server hosting interactive virtual lab tray"]
    ]
    add_table(s12, Inches(0.6), Inches(1.3), Inches(11.5), Inches(3.2), headers_t, rows_t,
              [Inches(2.2), Inches(2.2), Inches(1.5), Inches(5.6)])

    add_card(s12, Inches(0.6), Inches(4.7), Inches(11.5), Inches(1.5),
             "Hardware Profile & Memory-Lean Pipeline Engineering",
             [
                 "Hardware Constraints: Standard consumer laptop CPU (AMD Ryzen 5 7520U, 4 cores / 8 threads, 2.80 GHz, 7.8 GB RAM).",
                 "Streaming Architecture: Large prediction matrices streamed in chunked batches; peak RAM usage strictly capped under 1.2 GB.",
                 "Deterministic Run Provenance: Seeds derived via SHA-256 stable hashing of (seed, rung, ordering); interrupted runs resume identically."
             ], border_color=COLOR_PRIMARY_NAVY)

    # -------------------------------------------------------------
    # SLIDE 13: Baseline Implementations & Fair Comparative Protocol
    # -------------------------------------------------------------
    s13 = prs.slides[12]
    clear_slide_content(s13)
    update_footer_and_date(s13, 13)
    add_header_bar(s13, "Baseline Implementations & Fair Comparison Protocol")

    headers_b = ["Baseline ID", "Method Name", "Scoring Principle", "Physical Witness Used", "Key Vulnerability"]
    rows_b = [
        ["B0", "Univariate Range Checks", "Values outside [0.1%, 99.9%] train bounds", "None (Lab only)", "Misses all sample swaps & plausible corruptions"],
        ["B1", "Stoichiometric Rules", "Hard domain rules (OC <= 1.05 * Ctot)", "None (Lab only)", "Blind to Nitrogen slips and unconstrained analytes"],
        ["B2", "Lab-Only Density", "Mahalanobis distance in log report space", "None (Lab only)", "Swapped valid samples have typical density"],
        ["B3", "Witness Marginal Interval", "Individual analyte prediction intervals", "Colour / Vis-NIR", "Ignores multi-analyte covariance structure"],
        ["B4", "Genomic Hungarian Matcher", "Optimal bipartite reassignment (Broman 2015)", "Colour / Vis-NIR", "Only detects swaps; blind to single-value errors"],
        ["B5", "Supervised LightGBM", "200 trees trained on planted errors", "Colour / Vis-NIR", "Cheat baseline: knows true error distribution in advance"],
        ["B6", "Rule-Based Repair", "Greedy unit/decimal range converter", "None (Lab only)", "Cannot diagnose swaps; low attribution accuracy (24%)"],
        ["B7", "Cleanlab Regression", "Label-quality regression score (Zhou 2023)", "None (Lab only)", "Scores individual rows; blind to tray permutations"]
    ]
    add_table(s13, Inches(0.6), Inches(1.3), Inches(11.5), Inches(3.6), headers_b, rows_b,
              [Inches(1.2), Inches(2.5), Inches(3.2), Inches(1.8), Inches(2.8)])

    add_card(s13, Inches(0.6), Inches(5.1), Inches(11.5), Inches(1.1),
             "Fairness Guarantees: All baselines evaluated on identical test batches with identical planted corruptions under Git commit 095deaa.",
             [], border_color=COLOR_TEAL)

    # -------------------------------------------------------------
    # SLIDE 14: Verification Framework, Quality Assurance & Research Charter
    # -------------------------------------------------------------
    s14 = prs.slides[13]
    clear_slide_content(s14)
    update_footer_and_date(s14, 14)
    add_header_bar(s14, "Verification Framework & Scientific Research Charter")

    add_card(s14, Inches(0.6), Inches(1.3), Inches(5.6), Inches(4.8),
             "The Project Research Charter (Doc 08)",
             [
                 "Core Principles of Research Integrity:\n  1. Zero Fabrication: No invented, smoothed, or cherry-picked metrics; every figure and table traces to an immutable JSON run record.\n  2. Pre-Registration: Pass/fail evaluation thresholds committed to Git prior to running tests (Commit 095deaa).\n  3. Open Reporting of Failures: Main claim A1 failed for colour witness; refutation of hypothesis H2 openly discussed and embraced.",
                 "Transparent Decision Audit Trail:\n  • 25 numbered, dated decisions in docs/decision_log.md.\n  • Tracks key architectural evolutions:\n    - D-002: Pivot from 'predict chemistry' to 'verify lab reports'.\n    - D-008: Detection of 23,852 empty OSSL spectral records.\n    - D-016: Diagnosis and fix of conformal pseudo-replication.\n    - D-025: Formal response to external technical review."
             ], border_color=COLOR_PRIMARY_NAVY)

    add_card(s14, Inches(6.5), Inches(1.3), Inches(5.6), Inches(4.8),
             "Comprehensive Software Verification Suite",
             [
                 "34 Automated Pytest Checks Passing:\n  • test_core.py: Error operators, inverses, permutation sets, exact Bayesian inference, conformal p-values, BH step-up.\n  • test_real_data.py: Property sets, quantile transformations, CIELAB colorimetry, numerical precision.\n  • test_phone.py & test_process_photos.py: Macbeth card color normalization, exposure checks, witness feature pipelines.\n  • test_app_*.py: Edge endpoints, crop suitability, leaf model.",
                 "Bit-Identical Reproducibility Tests:\n  • Resume Equivalence: Interrupted run resumed with --resume produces bit-for-bit identical floats.\n  • Rebuild Integrity: Dataset re-downloaded from OSSL bucket yields identical MD5 checksums across all 19,746 samples.\n  • Seed Stability: Multi-seed runs reproduce single-seed runs exactly."
             ], border_color=COLOR_SUCCESS)

    # -------------------------------------------------------------
    # SLIDE 15: Primary Experimental Results (Pre-Registered KSSL Benchmark)
    # -------------------------------------------------------------
    s15 = prs.slides[14]
    clear_slide_content(s15)
    update_footer_and_date(s15, 15)
    add_header_bar(s15, "Primary Results: Pre-Registered KSSL Benchmark (X5)")

    fig2_path = FIG_DIR / "fig2_kssl_recall.png"
    if fig2_path.exists():
        s15.shapes.add_picture(str(fig2_path), Inches(0.6), Inches(1.3), Inches(6.0), Inches(2.6))

    headers_r = ["Optical Witness", "EdaphNet Recall", "Best Baseline (B5)", "Difference [95% CI]", "Status"]
    rows_r = [
        ["None (W0)", "0.238", "0.271", "-0.033 [-0.049, -0.016]", "Baseline"],
        ["Colour Perfect (W1_dE0)", "0.416", "0.415", "+0.001 [-0.022, +0.023]", "Tie"],
        ["Colour Good Phone (W1_dE2)", "0.410", "0.396", "+0.014 [-0.008, +0.038]", "Marginal (+1.4%)"],
        ["Colour Noisy Phone (W1_dE4)", "0.382", "0.354", "+0.028 [+0.010, +0.049]", "Stat Sig (+2.8%)"],
        ["Spectrometer (W3)", "0.604", "0.512", "+0.092 [+0.069, +0.113]", "Decisive (+9.2%, p<0.001)"]
    ]
    add_table(s15, Inches(0.6), Inches(4.0), Inches(6.0), Inches(2.2), headers_r, rows_r,
              [Inches(2.0), Inches(1.0), Inches(1.0), Inches(1.4), Inches(0.6)])

    add_card(s15, Inches(6.8), Inches(1.3), Inches(5.3), Inches(4.9),
             "Official Pre-Registered Verdicts (Doc 21)",
             [
                 "Scale: 23,219 real soils, 50 settings, 5 seeds, 300 batches of 24 per setting (~7,200 reports/setting). Primary metric: Recall at 5% re-test budget.",
                 "Rule A1 [Recall Gain >= +0.05 for Colour]:\n  • FAILED: Good phone colour attained +0.014 [-0.008, +0.038], falling short of pre-registered +0.05 threshold.",
                 "Rule A1-c [Non-inferiority in Clustered Batches]:\n  • PASSED: EdaphNet showed +0.013 and +0.010 advantage in geographically clustered batches (harder case).",
                 "Rule A2 [Shift-Aware False Alarm Control]:\n  • PASSED: Realised FDR stayed <= 0.09 (well below nominal target q = 0.10).",
                 "Rule A3 [Attribution Accuracy >= +0.20 over B6]:\n  • PASSED: Achieved 97%–100% vs 24%–29% for rule-based repair.",
                 "Refutation of Hypothesis H2:\n  • H2 hypothesized gain would be largest for weakest witness; refuted! Spectrometer (+0.092) outperformed colour (+0.014)."
             ], border_color=COLOR_PRIMARY_NAVY)

    # -------------------------------------------------------------
    # SLIDE 16: Deep-Dive Analytics: Swaps vs. Value Errors & Error-Mix Crossover
    # -------------------------------------------------------------
    s16 = prs.slides[15]
    clear_slide_content(s16)
    update_footer_and_date(s16, 16)
    add_header_bar(s16, "Analytical Deep Dive: Swaps vs. Values & Error Mix")

    fig3_path = FIG_DIR / "fig3_swap_vs_value.png"
    if fig3_path.exists():
        s16.shapes.add_picture(str(fig3_path), Inches(0.6), Inches(1.3), Inches(5.5), Inches(2.4))

    fig5_path = FIG_DIR / "fig5_error_mix.png"
    if fig5_path.exists():
        s16.shapes.add_picture(str(fig5_path), Inches(6.5), Inches(1.3), Inches(5.5), Inches(2.4))

    add_card(s16, Inches(0.6), Inches(3.9), Inches(5.5), Inches(2.3),
             "Anatomy of the Net-Zero Result with Colour (Fig 3)",
             [
                 "Two Cancelling Opposing Forces Under 5% Re-test Budget:\n  • Sample Swaps: EdaphNet dominates B5 by +10.3 to +11.4 percentage points! Independent colour detects swaps invisible to B5.\n  • Value Corruptions: EdaphNet trails B5 by 8.2 percentage points.",
                 "Budget Competition: When the model spends budget slots on newly discovered swaps, fewer slots remain for subtle numerical slips."
             ], border_color=COLOR_PRIMARY_NAVY)

    add_card(s16, Inches(6.5), Inches(3.9), Inches(5.5), Inches(2.3),
             "The Error-Mix Crossover Discovery (Fig 5)",
             [
                 "Dominance Dictated by Laboratory Error Distribution:\n  • At 50/50 mix (equal swaps & values), net gain is ~0.\n  • When swaps represent >= 60%–70% of errors, smartphone colour decisively beats all existing baselines!\n  • With laboratory spectrometer (W3), EdaphNet wins across all operating mixes with >= 30% swaps."
             ], border_color=COLOR_TEAL)

    # -------------------------------------------------------------
    # SLIDE 17: Root-Cause Fault Attribution & Unknown Error Robustness
    # -------------------------------------------------------------
    s17 = prs.slides[16]
    clear_slide_content(s17)
    update_footer_and_date(s17, 17)
    add_header_bar(s17, "Fault Attribution Accuracy & Unknown Error Robustness")

    headers_a = ["Evaluation Setting", "EdaphNet Error Type Attribution", "Rule-Based Repair (B6)", "EdaphNet Swap Partner Identification"]
    rows_a = [
        ["KSSL, Spectrometer (Pre-reg A3)", "97% – 100%", "24% – 29%", "95% – 98%"],
        ["ICRAF-ISRIC (Colour W1 / Spectro W3)", "89% – 98%", "37% – 51%", "75% – 99%"],
        ["Synthetic Copula Simulation", "84% – 92%", "32% – 50%", "86% – 98%"]
    ]
    add_table(s17, Inches(0.6), Inches(1.3), Inches(11.5), Inches(1.8), headers_a, rows_a,
              [Inches(3.2), Inches(2.8), Inches(2.5), Inches(3.0)])

    add_card(s17, Inches(0.6), Inches(3.3), Inches(5.6), Inches(3.0),
             "Root-Cause Attribution: The Decisive Clinical Value",
             [
                 "Why Attribution Matters: A laboratory re-testing a flagged sample needs to know what went wrong—was it swapped with tray #12, or was decimal place shifted?",
                 "Massive Attribution Superiority (Pre-Registered A3 Passed):\n  • EdaphNet correctly diagnoses error type in 97%–100% of cases.\n  • Correctly points to exact swap partner sample in 95%–98% of swap cases.\n  • Competing baselines (B5, B7) only provide black-box scores; B6 repair manages only 24%–29% attribution accuracy."
             ], border_color=COLOR_SUCCESS)

    add_card(s17, Inches(6.5), Inches(3.3), Inches(5.6), Inches(3.0),
             "Robustness to Unknown Error Types (Experiment X7)",
             [
                 "Evaluating Out-of-Library Corruptions (5 Seeds):\n  • Injected 4 error types completely absent from library C: x100 errors, gross x4-8, neighbor-copied values, dropped digits.\n  • Robust Swap Gain Retained: Phone colour retained +0.103 [+0.069, +0.137] swap advantage; Spectrometer retained +0.147.\n  • Detectability: Large corruptions (x100) caught with 99% recall; subtle dropped digits remain hard for all checkers."
             ], border_color=COLOR_ACCENT_AMBER)

    # -------------------------------------------------------------
    # SLIDE 18: Live Demo Flow & User Interaction Walkthrough
    # -------------------------------------------------------------
    s18 = prs.slides[17]
    clear_slide_content(s18)
    update_footer_and_date(s18, 18)
    add_header_bar(s18, "Live Demonstration & Interactive System Walkthrough")

    demo_cases = [
        ("Case 1: Clean Valid Sample", [
            "Input: Real KSSL soil photo & matching laboratory report.",
            "Pipeline: Optical colour predicts OC=2.2%, N=0.21%.",
            "Report: OC=2.24%, N=0.234% (consistent).",
            "Engine Verdict: Suspicion dial reads 0.02 (Green / Clean).",
            "Action: Certificate autoverified and released immediately."
        ]),
        ("Case 2: Nitrogen Decimal Slip (x10)", [
            "Input: Real KSSL sample with keystroke slip in lab report.",
            "Report: Nitrogen keyed as 2.34% (10x higher than true 0.234%).",
            "Engine Verdict: Suspicion dial reads 0.98 (Red / Highly Suspicious).",
            "Attribution: Diagnosed as 'Decimal Slip (x10)'.",
            "Candidate Repair: Suggests N = 0.234% to technician."
        ]),
        ("Case 3: Tray Swap (#2 <-> #9)", [
            "Input: Physical vial #2 swapped with vial #9 in 12-well tray.",
            "Report: Chemically plausible, but contradicts optical witness.",
            "Engine Verdict: Suspicion 0.95; Flags multi-analyte mismatch.",
            "Attribution: Identifies sample #9 as swap partner (98% prob).",
            "Action: Both vials routed to re-test queue together."
        ])
    ]

    for idx, (ctitle, citems) in enumerate(demo_cases):
        add_card(s18, Inches(0.6 + idx * 3.9), Inches(1.3), Inches(3.7), Inches(3.5), ctitle, citems, border_color=COLOR_PRIMARY_NAVY)

    add_card(s18, Inches(0.6), Inches(5.0), Inches(11.5), Inches(1.3),
             "Interactive Demonstrator Suite (Running Locally on Port 8000)",
             [
                 "1. Interactive Batch Checker: 12-well/24-well virtual laboratory tray displaying real-time Bayesian hypothesis ranking and re-test prioritization.",
                 "2. Farmer Decision Assistant: MobileNetV3 leaf disease classification and FAO EcoCrop suitability engine integrated into single local web application."
             ], border_color=COLOR_TEAL)

    # -------------------------------------------------------------
    # SLIDE 19: Conclusion, Project Outcomes & Future Work
    # -------------------------------------------------------------
    s19 = prs.slides[18]
    clear_slide_content(s19)
    update_footer_and_date(s19, 19)
    add_header_bar(s19, "Conclusion, Project Outcomes & Future Work")

    add_card(s19, Inches(0.6), Inches(1.3), Inches(5.6), Inches(4.8),
             "Project Conclusions & Academic Deliverables",
             [
                 "Key Scientific Takeaways:\n  1. Independent optical sensing unlocks the detection of sample swaps that are mathematically invisible to conventional lab QA.\n  2. Cheap smartphone colour provides a +10 point swap advantage; laboratory Vis-NIR spectroscopy provides a decisive +9.2 point overall gain (p < 0.001).\n  3. Discovered and resolved conformal pseudo-replication, proving that sample reuse breaks multi-sample false-alarm bounds.",
                 "Tangible Academic Deliverables:\n  • Complete IEEE Transactions Manuscript: Formatted in IEEE two-column layout (6 figures, revised 26 Oct 2026), targeting IEEE TAFE / TIM.\n  • Comprehensive 38-Page Technical Project Dossier (v1.1).\n  • Working Production Codebase: 59 Git commits with complete provenance, run logs, and 34 automated passing tests.",
                 "Intellectual Property Position:\n  • Software method assessed under Indian Patent Act Section 3(k); recommended path: Open-source dissemination via Zenodo with reserved DOI."
             ], border_color=COLOR_PRIMARY_NAVY)

    add_card(s19, Inches(6.5), Inches(1.3), Inches(5.6), Inches(4.8),
             "Future Work: Phase-II Roadmap (Paper 2)",
             [
                 "1. Combined Two-Stage Re-Test Policy (Amendment v3):\n  • Fuse EdaphNet's permutation engine (specialized for swaps) with deterministic stoichiometric checkers (specialized for value errors).\n  • Eliminates the budget trade-off, achieving combined recall of 0.20-0.25 on swaps and 0.22 on value corruptions.",
                 "2. Paper 2 Field Pilot with Indian Laboratory:\n  • Pilot study on 30–50 real Indian soil samples in collaboration with VIT VAIAL soil laboratory.\n  • Capture real smartphone photos with 24-patch Macbeth colour cards under natural farmer lighting conditions.",
                 "3. Blind Duplicate Validation:\n  • Send 25% blind duplicate samples to commercial laboratories to measure true baseline laboratory error rates and operational cost savings.",
                 "4. Transfer to Additional Agronomic Analytes:\n  • Extend latent models to micronutrients (Zn, Fe, Cu) and Soil Health Card panels."
             ], border_color=COLOR_TEAL)

    # -------------------------------------------------------------
    # SLIDE 20: References & Institutional Acknowledgments
    # -------------------------------------------------------------
    s20 = prs.slides[19]
    clear_slide_content(s20)
    update_footer_and_date(s20, 20)
    add_header_bar(s20, "References & Institutional Acknowledgments")

    add_card(s20, Inches(0.6), Inches(1.3), Inches(7.0), Inches(4.8),
             "Principal Literature Citations (IEEE Style)",
             [
                 "[1] R. J. Even et al., 'Large errors in soil carbon measurements attributed to inconsistent sample processing,' SOIL, vol. 11, no. 1, pp. 17–34, 2025.",
                 "[2] J. L. Safanelli et al., 'Open Soil Spectral Library (OSSL): Building reproducible soil calibration models through open development,' PLOS ONE, vol. 20, no. 1, p. e0296545, 2025.",
                 "[3] S. Bates, E. Candès, L. Lei, Y. Romano, and M. Sesia, 'Testing for outliers with conformal p-values,' The Annals of Statistics, vol. 51, no. 1, pp. 149–178, 2023.",
                 "[4] Y. Jin and E. Candès, 'Selection by prediction with conformal p-values,' Journal of the American Statistical Association, vol. 118, no. 544, pp. 2533–2545, 2023.",
                 "[5] K. W. Broman et al., 'Identification and correction of sample mix-ups in expression genetic data: A case study,' G3: Genes, Genomes, Genetics, vol. 5, no. 10, pp. 2177–2186, 2015.",
                 "[6] H. Zhou, J. Mueller, M. Kumar, J.-L. Wang, and J. Lei, 'Detecting errors in a numerical response via any regression model,' arXiv:2305.16583, 2023.",
                 "[7] Y. Benjamini and Y. Hochberg, 'Controlling the false discovery rate: A practical and powerful approach to multiple testing,' J. R. Stat. Soc. B, vol. 57, pp. 289–300, 1995.",
                 "[8] R. A. Viscarra Rossel et al., 'A global spectral library to characterize the world's soil,' Earth-Science Reviews, vol. 155, pp. 198–230, 2016."
             ], border_color=COLOR_PRIMARY_NAVY)

    add_card(s20, Inches(7.9), Inches(1.3), Inches(4.2), Inches(4.8),
             "Institutional Acknowledgments",
             [
                 "Faculty Supervisor & Mentor:\n  • Heartfelt gratitude to Dr. Priya Saminathan, Associate Professor, SCOPE, VIT Vellore, for continuous intellectual guidance, rigorous feedback, and mentorship.",
                 "Institutional Support:\n  • School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Vellore.\n  • Centre for Agricultural Research and Technology (VIT VAIAL).",
                 "Open Data Initiatives:\n  • Open Soil Spectral Library (OSSL) project and USDA-NRCS Kellogg Soil Survey Laboratory (KSSL) for hosting public soil spectral data repositories."
             ], border_color=COLOR_TEAL)

    # Save to final submission file
    print(f"Saving final presentation to {OUTPUT_PATH}...")
    prs.save(OUTPUT_PATH)
    print(f"Also updating copy in {TEMPLATE_PATH}...")
    prs.save(TEMPLATE_PATH)
    print("Presentation build complete! Verified slide count:", len(prs.slides))


if __name__ == "__main__":
    build_presentation()
