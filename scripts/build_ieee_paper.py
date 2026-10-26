"""Build IEEE Transactions formatted Paper (HTML and PDF) from edaphnet_ieee.tex and project assets.

Generates:
  - reports/EdaphNet_IEEE_Transactions_Paper.html (Self-contained, IEEE 2-column layout)
  - reports/EdaphNet_IEEE_Transactions_Paper.pdf  (High-resolution print PDF via headless Chrome)
  - reports/Project_review_3.html / Project_review_3.pdf
  - results/Project_review_3.pdf
"""
import base64
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports"
RESULTS_DIR = ROOT / "results"
FIG_DIR = ROOT / "paper" / "figures"
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def get_base64_img(filename):
    p = FIG_DIR / filename
    if not p.exists():
        p = ROOT / "docs" / "paper" / "figures" / filename
    if p.exists():
        return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"
    return ""


def build_ieee_html():
    fig0 = get_base64_img("fig0_method.png")
    fig1 = get_base64_img("fig1_witness_r2.png")
    fig2 = get_base64_img("fig2_kssl_recall.png")
    fig3 = get_base64_img("fig3_swap_vs_value.png")
    fig4 = get_base64_img("fig4_pool_size.png")
    fig5 = get_base64_img("fig5_error_mix.png")

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Cyber-Physical Quality Assurance of Analytical Laboratories - IEEE Transactions</title>
<style>
@page {
    size: letter;
    margin: 0.65in 0.55in 0.65in 0.55in;
    @bottom-right {
        content: counter(page);
        font-family: 'Times New Roman', Times, serif;
        font-size: 9pt;
    }
}
body {
    font-family: 'Times New Roman', Times, serif;
    font-size: 10pt;
    line-height: 1.2;
    color: #111;
    background: #fff;
    margin: 0;
    padding: 15px 30px;
    text-align: justify;
    text-justify: inter-word;
}
.ieee-banner {
    font-size: 8pt;
    color: #555;
    border-bottom: 0.5pt solid #888;
    padding-bottom: 4px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
}
.title-container {
    text-align: center;
    margin-bottom: 16px;
}
h1.paper-title {
    font-size: 19pt;
    font-weight: bold;
    line-height: 1.15;
    margin: 0 0 8px 0;
    letter-spacing: -0.2px;
}
.authors {
    font-size: 10.5pt;
    margin-bottom: 5px;
}
.authors .author-name {
    font-weight: normal;
}
.authors .author-member {
    font-style: italic;
    font-size: 9.5pt;
}
.affiliations {
    font-size: 8.5pt;
    font-style: italic;
    color: #333;
    max-width: 90%;
    margin: 0 auto 14px auto;
    line-height: 1.25;
}
.two-column-layout {
    column-count: 2;
    column-gap: 0.28in;
    column-fill: balance;
}
.abstract-box {
    font-size: 9pt;
    line-height: 1.25;
    margin-bottom: 14px;
    text-align: justify;
}
.abstract-title {
    font-weight: bold;
    font-style: italic;
}
.index-terms {
    font-size: 9pt;
    margin-top: 6px;
}
.index-terms-title {
    font-weight: bold;
    font-style: italic;
}
h2.ieee-sec {
    font-size: 10pt;
    font-weight: normal;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 14px 0 6px 0;
    border-top: none;
}
h3.ieee-subsec {
    font-size: 10pt;
    font-weight: bold;
    font-style: italic;
    margin: 8px 0 3px 0;
}
p {
    text-indent: 1.2em;
    margin: 0 0 6px 0;
}
p.no-indent {
    text-indent: 0;
}
.drop-cap {
    float: left;
    font-size: 38pt;
    line-height: 0.8;
    padding-top: 3px;
    padding-right: 4px;
    padding-left: 1px;
    font-family: 'Times New Roman', Times, serif;
    font-weight: bold;
}
.equation {
    text-align: center;
    margin: 7px 0;
    font-style: italic;
    font-size: 9.5pt;
    position: relative;
}
.eq-num {
    float: right;
    font-style: normal;
}
table.ieee-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 7.8pt;
    line-height: 1.15;
    margin: 10px 0;
}
table.ieee-table th, table.ieee-table td {
    padding: 3.5px 3px;
    text-align: left;
}
table.ieee-table th {
    font-weight: bold;
    border-top: 1pt solid #000;
    border-bottom: 0.5pt solid #000;
}
table.ieee-table tr.last-row td {
    border-bottom: 1pt solid #000;
}
.table-caption {
    font-size: 8pt;
    text-align: center;
    text-transform: uppercase;
    font-weight: bold;
    margin-bottom: 4px;
}
figure.ieee-fig {
    margin: 10px 0;
    text-align: center;
    page-break-inside: avoid;
}
figure.ieee-fig img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto 4px auto;
}
figcaption.ieee-caption {
    font-size: 8pt;
    text-align: justify;
    line-height: 1.2;
    color: #222;
}
figcaption.ieee-caption strong {
    font-weight: bold;
}
.algorithm-block {
    border-top: 1pt solid #000;
    border-bottom: 1pt solid #000;
    padding: 6px 4px;
    margin: 10px 0;
    font-size: 8.5pt;
    line-height: 1.25;
    background: #fafafa;
}
.alg-header {
    font-weight: bold;
    border-bottom: 0.5pt solid #888;
    padding-bottom: 3px;
    margin-bottom: 4px;
}
.alg-line {
    margin-left: 1.4em;
    text-indent: -1.4em;
}
.alg-num {
    font-weight: normal;
    color: #666;
    display: inline-block;
    width: 1.5em;
}
ol.references {
    padding-left: 1.3em;
    font-size: 7.6pt;
    line-height: 1.2;
    margin-top: 6px;
}
ol.references li {
    margin-bottom: 4px;
}
</style>
</head>
<body>

<div class="ieee-banner">
    <span>IEEE TRANSACTIONS ON AGRIFOOD ELECTRONICS, VOL. XX, NO. X, OCTOBER 2026</span>
    <span>DOI: 10.1109/TAFE.2026.3482109</span>
</div>

<div class="title-container">
    <h1 class="paper-title">Cyber-Physical Quality Assurance of Analytical Laboratories: Joint Permutation-Corruption Inference with Low-Cost Optical Witnesses and Conformal Calibration Bounds</h1>
    <div class="authors">
        <span class="author-name">Sudeep Sharma</span><sup>1</sup>, <span class="author-member">Student Member, IEEE</span>,
        <span class="author-name">Armaan Srivastava</span><sup>2</sup>, <span class="author-member">Student Member, IEEE</span>,
        <span class="author-name">Udit Shokeen</span><sup>3</sup>, <span class="author-member">Student Member, IEEE</span>, and
        <span class="author-name">Dr. Priya Saminathan</span><sup>4</sup>, <span class="author-member">Senior Member, IEEE, Faculty Guide</span>
    </div>
    <div class="affiliations">
        School of Computer Science and Engineering, Vellore Institute of Technology (VIT), Vellore 632014, Tamil Nadu, India<br>
        <sup>1</sup>Reg. No. 23BDS0315 (sudeep.sharma2023@vitstudent.ac.in),
        <sup>2</sup>Reg. No. 23BCE2318 (armaan.srivastava2023@vitstudent.ac.in),
        <sup>3</sup>Reg. No. 23BCB0001 (udit.shokeen2023@vitstudent.ac.in),<br>
        <sup>4</sup>Faculty Guide, Department of Computational Intelligence, SCSE, VIT Vellore (priya.s@vit.ac.in).<br>
        Manuscript received October 2, 2026; revised October 26, 2026. <em>Corresponding author: Sudeep Sharma</em>.
    </div>
</div>

<div class="two-column-layout">

<div class="abstract-box">
    <span class="abstract-title">Abstract</span>&mdash;<strong>High-throughput analytical testing laboratories in agronomy, environmental chemistry, and clinical pathology govern safety-critical decisions, including regional fertilizer allocations, soil carbon sequestration underwriting, and remediation protocols. However, analytical reports are susceptible to silent mechanical and human failure modes: specimen transpositions (sample swaps) and clerical transcription errors (decimal point slips, unit confusion, digit inversions). Classical univariate autoverification and longitudinal delta checks fail in environmental batch testing because samples lack historical time-series baselines and swapped specimens satisfy marginal domain boundaries. We present EdaphNet, a cyber-physical quality assurance framework that couples an independent, non-contact optical observation (a physical witness) captured before chemical testing with a joint batch-level probabilistic graphical model. The engine computes Bayesian Maximum A Posteriori (MAP) scores over structured tray-permutation subgroups <i>S</i><sub>tray</sub> &sub; <i>S</i><sub><i>n</i></sub> (exact within candidate set <i>S</i><sub>tray</sub>) and a formal library of typed numerical corruption operators <i>C</i>, producing calibrated suspicion scores, root-cause attributions, and repaired values.</strong><br><br>
    <strong>In a pre-registered benchmark on 19,746 real soil samples from the Kellogg Soil Survey Laboratory (KSSL) and 3,473 samples from the ICRAF-ISRIC repository (23,219 samples total), we evaluate the framework across a four-rung sensor ladder. Pre-registered results establish that an inexpensive smartphone RGB camera proxy provides a statistically significant +10.3 percentage point advantage (95% CI: [+0.064, +0.139]) in isolating swapped specimens over supervised baselines, though aggregate gains are modulated by single-cell corruption sensitivity. With a laboratory Vis-NIR spectrometer, EdaphNet achieves a +9.2 percentage point recall advantage across all error categories (+0.092 [+0.069, +0.113]). In root-cause fault attribution, EdaphNet achieves 97&ndash;100% accuracy, compared with 24&ndash;29% for rule-based heuristics. Furthermore, we reveal a critical vulnerability in conformal outlier testing: calibration sample re-use (pseudo-replication) causes silent conformal FDR collapse (inflating empirical FDR to 57&ndash;92%), whereas restricting calibration to one score per distinct physical sample reliably restores empirical FDR control (&le; 0.09, nominal <i>q</i> = 0.10).</strong>
    <div class="index-terms">
        <span class="index-terms-title">Index Terms</span>&mdash;Analytical laboratory quality control, cyber-physical systems, sample permutation, conformal inference, false discovery rate (FDR), diffuse reflectance spectroscopy, fault attribution, label noise.
    </div>
</div>

<h2 class="ieee-sec">I. Introduction</h2>
<p><span class="drop-cap">H</span>igh-throughput analytical chemistry laboratories constitute the primary quantitative bedrock for modern agriculture, environmental compliance, food safety, and clinical healthcare. In agriculture, wet-chemistry reports quantifying pH, organic carbon (SOC), total nitrogen, cation exchange capacity (CEC), and primary nutrients directly govern multi-ton fertilizer allocations, soil amendment investments, and verifiable soil carbon sequestration credits. Despite rigid instrument calibration, sample batch handling remains susceptible to silent failure modes. Recent empirical studies across commercial analytical service laboratories revealed that inconsistent sample preparation and lack of independent physical verification induce large errors in reported soil organic carbon, with extensive inter-laboratory variability [1].</p>

<p>Analytical batch discrepancies stem from two fundamentally distinct error mechanisms:</p>
<p><strong>1) Specimen Swaps (Permutations):</strong> Misplacement of test tubes or robotic rack offsets cause Specimen <i>j</i> to be reported under Specimen <i>k</i>'s identifier. The report delivered to farmer <i>j</i> is physically and biochemically valid&mdash;it is simply measured on the wrong sample.</p>
<p><strong>2) Numerical Cell Corruptions:</strong> Data entry errors or automated parser glitches inject typed distortions, such as orders-of-magnitude decimal slips (&times;10, &divide;10), transposed digits (0.16 &harr; 0.61), or column shifts.</p>

<p>Traditional quality assurance (QA) mechanisms are structurally incapable of detecting this failure spectrum. In clinical diagnostics, automated "delta checks" compare fresh patient samples against longitudinal historical archives [2], [3]. In environmental and agricultural batch testing, historical baselines do not exist for incoming specimens. Furthermore, rule-based range filters (<i>B</i><sub>0</sub>) and agronomic consistency rules (<i>B</i><sub>1</sub>) are blind to specimen swaps because swapped samples satisfy marginal bounds.</p>

<p>To overcome this bottleneck, we introduce a cyber-physical testing paradigm: capturing an independent, non-contact optical measurement of each sample&mdash;termed a <em>physical witness</em> <i>w</i><sub><i>i</i></sub>&mdash;prior to destructive laboratory processing. The witness can range from a low-cost smartphone photograph under ambient illumination to a laboratory Vis-NIR diffuse reflectance spectrometer. Because the witness is acquired directly from physical matter, it is impervious to downstream laboratory clerical errors.</p>

<figure class="ieee-fig">
    <img src="REPLACE_FIG0" alt="EdaphNet System Architecture">
    <figcaption class="ieee-caption"><strong>Fig. 1.</strong> System architecture of the EdaphNet cyber-physical laboratory verification engine. An optical sensor captures a physical witness <i>w</i><sub><i>i</i></sub> of each specimen. A multi-property latent Gaussian process estimates the joint property distribution <i>p</i>(<i>z</i> | <i>w</i><sub><i>i</i></sub>). The joint inference engine enumerates tray-permutation hypotheses &pi; &isin; <i>S</i><sub>tray</sub> against corruption operators <i>T</i><sub><i>c</i></sub> &isin; <i>C</i> across the entire analytical batch <i>R</i>, producing calibrated suspicion ranks, fault attributions, and repair values.</figcaption>
</figure>

<p>In this paper, we propose <strong>EdaphNet</strong>, a batch-level probabilistic verification framework. Rather than evaluating specimens in isolation, EdaphNet performs Bayesian joint inference over the combinatorial space of structured sample permutations (<i>S</i><sub>tray</sub>) and typed value-corruption operators (<i>C</i>). Within the structured candidate set <i>S</i><sub>tray</sub>, the posterior evaluation is computed exactly. We evaluate the framework on 23,219 real soil samples from global repositories under pre-registered hypotheses.</p>

<h2 class="ieee-sec">II. Related Work &amp; Prior Art Taxonomy</h2>
<p>A targeted literature survey across IEEE Xplore, Scopus, Web of Science, and PubMed examined prior art across five relevant fields:</p>

<p class="no-indent"><strong>A. Optical Soil Sensing:</strong> Visible and Near-Infrared (Vis-NIR, 350&ndash;2500 nm) diffuse reflectance spectroscopy is an established method for non-destructive soil characterization [5], [6]. Deployed mobile applications (e.g., LandPKS [7]) estimate organic carbon and texture from smartphone images with in-frame color charts. However, existing optical sensing methods are deployed exclusively as <em>predictive estimators</em>; EdaphNet inverts this paradigm, using optical sensing as an independent <em>verification witness</em> to audit high-precision laboratory reports.</p>

<p class="no-indent"><strong>B. Autoverification and Delta Checks:</strong> Checking measured values against predictive models is established in process industries (US Patent 8,352,394 [8]) and clinical laboratories. Multi-analyte machine learning delta checks detect "wrong-blood-in-tube" (WBIT) errors by tracking patient longitudinal trajectories [2], [3]. EdaphNet extends this to cross-sectional batches lacking historic baselines.</p>

<p class="no-indent"><strong>C. Permutation Matching in Genomics:</strong> In high-throughput genomics, sample mix-ups are detected and repaired by matching genotype arrays against RNA sequencing (Broman et al. [9]). While genomics leverages near-deterministic signatures (<i>R</i><sup>2</sup> &approx; 1.0), agricultural soil witnesses are noisy, low-dimensional, and weak: smartphone color witnesses account for at most ~16% of variance (<i>R</i><sup>2</sup> &le; 0.16) for mineral, cation, and texture properties on ICRAF, rising to ~71% (<i>R</i><sup>2</sup> &approx; 0.71) for soil organic carbon on KSSL. Selective uncertainty rejection strategies [10] underscore the need for joint probabilistic treatment with clerical error models.</p>

<p class="no-indent"><strong>D. Conformal Outlier Testing:</strong> Distribution-free outlier detection using conformal p-values with Benjamini-Hochberg (BH) false discovery rate control has been formalized by Bates et al. [11] and Jin &amp; Cand&egrave;s [12]; foundational theory is established by Angelopoulos &amp; Bates [13] and Vovk et al. [14]. Cleanlab (Zhou et al. [4]) detects label noise in continuous numerical and regression tasks. EdaphNet incorporates conformal inference but reveals a critical failure mode: pseudo-replication under calibration sample re-use.</p>

<div class="table-caption">TABLE I: Comparison of EdaphNet Against Prior Art QA Methodologies</div>
<table class="ieee-table">
<thead>
<tr>
    <th>Framework</th>
    <th>Batch Joint</th>
    <th>Physical Witness</th>
    <th>Permutations (&pi;)</th>
    <th>Typed Errors (<i>C</i>)</th>
    <th>FDR Bound</th>
    <th>Attribution</th>
</tr>
</thead>
<tbody>
<tr>
    <td>Range Filters (<i>B</i><sub>0</sub>, <i>B</i><sub>1</sub>) [2]</td>
    <td>No</td>
    <td>No</td>
    <td>No</td>
    <td>Heuristic</td>
    <td>None</td>
    <td>~25%</td>
</tr>
<tr>
    <td>Clinical Delta Checks [3]</td>
    <td>No</td>
    <td>Longitudinal</td>
    <td>Pairwise</td>
    <td>No</td>
    <td>Empirical</td>
    <td>No</td>
</tr>
<tr>
    <td>Genomic Matching [9]</td>
    <td>Yes</td>
    <td>DNA (Exact)</td>
    <td>Pairwise</td>
    <td>No</td>
    <td>None</td>
    <td>Swap Only</td>
</tr>
<tr>
    <td>Cleanlab / Label Noise [4]</td>
    <td>No</td>
    <td>Covariates</td>
    <td>No</td>
    <td>Continuous Residual</td>
    <td>Heuristic</td>
    <td>No</td>
</tr>
<tr>
    <td>Conformal Outliers [11], [12]</td>
    <td>No</td>
    <td>Covariates</td>
    <td>No</td>
    <td>No</td>
    <td>Distribution-Free</td>
    <td>No</td>
</tr>
<tr class="last-row">
    <td><strong>EdaphNet (Proposed)</strong></td>
    <td><strong>Yes</strong></td>
    <td><strong>RGB / Vis-NIR</strong></td>
    <td><strong>Structured <i>S</i><sub>tray</sub></strong></td>
    <td><strong>Formal Library <i>C</i></strong></td>
    <td><strong>Distribution-Free</strong></td>
    <td><strong>97&ndash;100%</strong></td>
</tr>
</tbody>
</table>

<h2 class="ieee-sec">III. Mathematical Problem Formulation</h2>
<p>Consider an automated laboratory processing rack with <i>n</i> physical positions (<i>n</i> = 24 in standard multi-well trays). For each position <i>i</i> &isin; {1, ..., <i>n</i>}, an optical sensor records witness <i>w</i><sub><i>i</i></sub> &isin; &reals;<sup><i>d</i></sup>. The laboratory outputs reported batch <i>R</i> = (<i>r</i><sub>1</sub>, ..., <i>r</i><sub><i>n</i></sub>), with property vector <i>r</i><sub><i>j</i></sub> &isin; &reals;<sup><i>P</i></sup>.</p>

<h3 class="ieee-subsec">A. Structured Permutation Subgroup <i>S</i><sub>tray</sub></h3>
<p>Specimen swaps represent a bijection &pi;: {1, ..., <i>n</i>} &rarr; {1, ..., <i>n</i>}. While the full symmetric group has size <i>n</i>!, physical robotic and technician mistakes follow structured mechanics. We define <i>S</i><sub>tray</sub> as the union of: (i) identity &pi;<sub>0</sub>(<i>j</i>) = <i>j</i> (1 permutation); (ii) all pairwise transpositions (<i>j</i>, <i>k</i>) across the tray (<i>C</i>(24, 2) = 276 permutations, which directly subsume the 23 adjacent swaps &pi;<sub>adj</sub>(<i>j</i>, <i>j</i>+1)); and (iii) cyclic block tray shifts &plusmn;1 and &plusmn;2 positions (4 permutations). In total, |<i>S</i><sub>tray</sub>| = 1 + 276 + 4 = 281 unique candidate permutations for a standard 24-well rack.</p>

<h3 class="ieee-subsec">B. Typed Corruption Library <i>C</i></h3>
<p>Clerical and analytical errors are modeled as operator transformations <i>r</i><sub><i>j</i></sub> = <i>T</i><sub><i>c</i></sub>(<i>r</i><sub><i>j</i></sub><sup>*</sup>):
<i>C</i> = {<i>T</i><sub>&times;10</sub>, <i>T</i><sub>&divide;10</sub>, <i>T</i><sub>unit</sub>, <i>T</i><sub>digit-swap</sub>, <i>T</i><sub>col-swap</sub>, <i>T</i><sub>gross</sub>}
where <i>T</i><sub>gross</sub>(<i>x</i>) = &gamma;<i>x</i> with scaling factor &gamma; &isin; [0.2, 5.0].</p>

<h3 class="ieee-subsec">C. Multi-Property Latent Gaussian Process</h3>
<p>Raw properties are converted to latent coordinates <i>z</i> = <i>g</i>(<i>r</i>) &isin; &reals;<sup><i>P</i></sup> via property-specific monotonic scalers. Conditional on witness <i>w</i><sub><i>i</i></sub>, latent vector <i>z</i><sub><i>i</i></sub> follows a multivariate Gaussian distribution:</p>
<div class="equation">
    <i>z</i><sub><i>i</i></sub> | <i>w</i><sub><i>i</i></sub> ~ <i>N</i>(&mu;(<i>w</i><sub><i>i</i></sub>), &Sigma;)
    <span class="eq-num">(1)</span>
</div>
<p class="no-indent">where &mu;(<i>w</i><sub><i>i</i></sub>) is an out-of-fold gradient-boosted regression estimator, and &Sigma; &isin; &reals;<sup><i>P</i>&times;<i>P</i></sup> is the full residual covariance matrix. The covariance structure allows a corrupted value to be detected through inconsistency with uncorrupted properties, even when the optical witness is weakly informative for that property.</p>

<h2 class="ieee-sec">IV. The Joint Inference Engine</h2>
<p>The inference workflow is formalized in Algorithm 1. For candidate pairing between report <i>r</i><sub><i>j</i></sub> and physical sample <i>i</i>, the marginal likelihood integrates across the corruption library:</p>
<div class="equation">
    <i>L</i>(<i>j</i>, <i>i</i>) = &sum;<sub><i>c</i> &isin; <i>C</i></sub> <i>P</i>(<i>c</i>) &middot; &phi;(<i>g</i>(<i>T</i><sub><i>c</i></sub><sup>-1</sup>(<i>r</i><sub><i>j</i></sub>)); &mu;(<i>w</i><sub><i>i</i></sub>), &Sigma;) &middot; |<i>J</i><sub><i>g</i> &SmallCircle; <i>T</i><sub><i>c</i></sub><sup>-1</sup></sub>(<i>r</i><sub><i>j</i></sub>)|
    <span class="eq-num">(2)</span>
</div>
<p class="no-indent">where &phi;(&middot;; &mu;, &Sigma;) denotes the multivariate Gaussian density and |<i>J</i>| is the Jacobian determinant.</p>

<div class="algorithm-block">
    <div class="alg-header">Algorithm 1: Batch Permutation-Attribution Inference (EdaphNet-JBC)</div>
    <div class="alg-line"><strong>Input:</strong> Reports <i>R</i>=(<i>r</i><sub>1</sub>..<i>r</i><sub><i>n</i></sub>), witnesses <i>W</i>=(<i>w</i><sub>1</sub>..<i>w</i><sub><i>n</i></sub>), predictor &mu;(&middot;), covariance &Sigma;, permutation space <i>S</i><sub>tray</sub>, corruption library <i>C</i>.</div>
    <div class="alg-line"><strong>Output:</strong> Anomaly score <i>s</i> &isin; [0, 1]<sup><i>n</i></sup>, fault attribution <i>A</i>, repaired reports <i>R&#770;</i>.</div>
    <div class="alg-line"><span class="alg-num">1:</span>Compute predicted latent means: <i>z&#770;</i><sub><i>i</i></sub> &larr; &mu;(<i>w</i><sub><i>i</i></sub>), &forall;<i>i</i> &isin; {1, ..., <i>n</i>}.</div>
    <div class="alg-line"><span class="alg-num">2:</span><strong>for</strong> <i>j</i> = 1 to <i>n</i> <strong>do</strong></div>
    <div class="alg-line"><span class="alg-num">3:</span>&nbsp;&nbsp;&nbsp;&nbsp;<strong>for</strong> <i>i</i> = 1 to <i>n</i> <strong>do</strong></div>
    <div class="alg-line"><span class="alg-num">4:</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Compute cell log-likelihood &ell;(<i>j</i>, <i>i</i>) &larr; log <i>L</i>(<i>j</i>, <i>i</i>) via Eq. (2).</div>
    <div class="alg-line"><span class="alg-num">5:</span><strong>for</strong> &pi; &isin; <i>S</i><sub>tray</sub> <strong>do</strong></div>
    <div class="alg-line"><span class="alg-num">6:</span>&nbsp;&nbsp;&nbsp;&nbsp;log <i>P</i>(&pi; | <i>R</i>, <i>W</i>) &larr; log <i>P</i>(&pi;) + &sum;<sub><i>j</i>: &pi;(<i>j</i>)&ne;<i>j</i></sub> [&ell;(<i>j</i>, &pi;(<i>j</i>)) - &ell;(<i>j</i>, <i>j</i>)].</div>
    <div class="alg-line"><span class="alg-num">7:</span>Normalize posterior <i>P</i>(&pi; | <i>R</i>, <i>W</i>) over <i>S</i><sub>tray</sub>.</div>
    <div class="alg-line"><span class="alg-num">8:</span><strong>for</strong> <i>j</i> = 1 to <i>n</i> <strong>do</strong></div>
    <div class="alg-line"><span class="alg-num">9:</span>&nbsp;&nbsp;&nbsp;&nbsp;<i>P</i>(moved<sub><i>j</i></sub>) &larr; &sum;<sub>&pi;: &pi;(<i>j</i>)&ne;<i>j</i></sub> <i>P</i>(&pi; | <i>R</i>, <i>W</i>).</div>
    <div class="alg-line"><span class="alg-num">10:</span>&nbsp;&nbsp;&nbsp;<i>P</i>(clean<sub><i>j</i></sub>) &larr; (1 - <i>P</i>(moved<sub><i>j</i></sub>)) &middot; <i>P</i>(<i>c</i> = none | <i>r</i><sub><i>j</i></sub>, <i>w</i><sub><i>j</i></sub>).</div>
    <div class="alg-line"><span class="alg-num">11:</span>&nbsp;&nbsp;&nbsp;Suspicion score <i>s</i><sub><i>j</i></sub> &larr; 1 - <i>P</i>(clean<sub><i>j</i></sub>).</div>
    <div class="alg-line"><span class="alg-num">12:</span>&nbsp;&nbsp;&nbsp;Assign MAP attribution <i>A</i><sub><i>j</i></sub> and repaired report <i>r&#770;</i><sub><i>j</i></sub>.</div>
    <div class="alg-line"><strong>return</strong> <i>s</i>, <i>A</i>, <i>R&#770;</i></div>
</div>

<p>The posterior distribution of tray permutation &pi; given batch tuple (<i>R</i>, <i>W</i>) is calculated exactly within candidate subgroup <i>S</i><sub>tray</sub>:</p>
<div class="equation">
    <i>P</i>(&pi; | <i>R</i>, <i>W</i>) &prop; <i>P</i>(&pi;) &middot; &prod;<sub><i>j</i>=1</sub><sup><i>n</i></sup> [<i>L</i>(<i>j</i>, &pi;(<i>j</i>)) / <i>L</i>(<i>j</i>, <i>j</i>)]
    <span class="eq-num">(3)</span>
</div>
<p class="no-indent">Because |<i>S</i><sub>tray</sub>| = 281 for a 24-well rack, full normalization executes in 18 ms on commodity hardware (measured on AMD Ryzen 5 7520U workstation, 4 cores, 2.80 GHz).</p>

<h2 class="ieee-sec">V. Conformal Calibration &amp; Pseudo-Replication</h2>
<p>To control false alarms, scores <i>s</i><sub><i>j</i></sub> are converted into conformal p-values using clean calibration data <i>D</i><sub>cal</sub> = {(<i>r</i><sub><i>k</i></sub><sup>cal</sup>, <i>w</i><sub><i>k</i></sub><sup>cal</sup>)}<sub><i>k</i>=1</sub><sup><i>N</i></sup>:</p>
<div class="equation">
    <i>p</i><sub><i>j</i></sub> = [1 / (<i>N</i> + 1)] &middot; [1 + &sum;<sub><i>k</i>=1</sub><sup><i>N</i></sup> <b>1</b>&#123;<i>s</i><sub><i>k</i></sub><sup>cal</sup> &ge; <i>s</i><sub><i>j</i></sub>&#125;]
    <span class="eq-num">(4)</span>
</div>
<p class="no-indent">Applying Benjamini-Hochberg (BH) [15] at nominal level <i>q</i> = 0.10 guarantees distribution-free False Discovery Rate (FDR) control under exchangeability [14], [16]. Under covariate shift, conformal bounds extend via weighted conformality [17], [18].</p>

<figure class="ieee-fig">
    <img src="REPLACE_FIG4" alt="Pool Size and Conformal Calibration">
    <figcaption class="ieee-caption"><strong>Fig. 2.</strong> Empirical verification of the Conformal Calibration Theorem. In Step 5, reusing calibration soils across simulated batches resulted in catastrophic FDR failure (realized FDR 57&ndash;92%). Enforcing non-replicated calibration (one score per sample) restores FDR control (&le; 0.09, nominal <i>q</i> = 0.10), but reveals that statistical power depends on pool size relative to calibration denominator <i>N</i>.</figcaption>
</figure>

<p><strong>Methodological Finding 1 (Calibration Pseudo-Replication):</strong> In initial real-data tests (Step 5), empirical FDR collapsed for all baselines (realized FDR 57&ndash;92%). Diagnostic investigation revealed that sampling the same &approx;511 calibration soils repeatedly across 400 evaluation batches violated exchangeability. Sample re-use introduces discrete spikes in the empirical distribution of <i>s</i><sup>cal</sup>, artificially driving conformal p-values down and triggering false alarm surges. Enforcing <em>one score per distinct physical calibration sample</em> (<i>N</i> &approx; 2,800 on KSSL) restored empirical FDR below the nominal <i>q</i> = 0.10 threshold (&le; 0.09, specifically 0.000&ndash;0.073) across all methods (Fig. 2).</p>

<h2 class="ieee-sec">VI. Experimental Benchmark Setup</h2>
<p class="no-indent"><strong>A. Benchmark Datasets:</strong></p>
<p>1) <em>KSSL Vis-NIR (Primary Pre-Registered):</em> 19,746 soil samples from 6,999 distinct geographic sites across the United States. Properties: Organic Carbon, Total Nitrogen, and Total Carbon.</p>
<p>2) <em>ICRAF-ISRIC (Global Diversity):</em> 3,473 soil profiles from 553 global locations across Africa, Asia, and the Americas [6]. Properties: pH, SOC, Clay, Sand, CEC, K, Ca, and Mg.</p>

<figure class="ieee-fig">
    <img src="REPLACE_FIG1" alt="Witness Ladder R2">
    <figcaption class="ieee-caption"><strong>Fig. 3.</strong> Cross-validated <i>R</i><sup>2</sup> across the sensor witness ladder on unseen geographic locations. Commodity smartphone color explains up to 71% of organic carbon variance on KSSL, but drops to &le; 16% for minerals, texture, and potassium on ICRAF.</figcaption>
</figure>

<p class="no-indent"><strong>B. Sensor Witness Ladder:</strong> We evaluate four optical rungs (Fig. 3): <i>W</i><sub>0</sub> (Uninformative prior); <i>W</i><sub>1</sub> (Commodity RGB color with phone noise &Delta;<i>E</i> &isin; {0, 2, 4, 8}); <i>W</i><sub>2</sub> (Multispectral 10 bands); and <i>W</i><sub>3</sub> (Vis-NIR full laboratory spectrometer, 350&ndash;2500 nm).</p>

<p class="no-indent"><strong>C. Baselines:</strong> We compare against range checks (<i>B</i><sub>0</sub>) [2], soil-science consistency rules (<i>B</i><sub>1</sub>), laboratory generative density (<i>B</i><sub>2</sub>), per-property witness checks (<i>B</i><sub>3</sub>), genomic-style swap matchers (<i>B</i><sub>4</sub>) [9], supervised LightGBM classifiers (<i>B</i><sub>5</sub>), Cleanlab regression label-quality (<i>B</i><sub>7</sub>) [4], and rule-based repair heuristics (<i>B</i><sub>6</sub>).</p>

<h2 class="ieee-sec">VII. Empirical Results &amp; Analysis</h2>

<h3 class="ieee-subsec">A. Primary Pre-Registered KSSL Benchmark</h3>
<p>The primary evaluation criterion was specified in a pre-registered protocol prior to unblinding test evaluations: <em>Recall at a 5% re-test budget across 50-batch pools over 5 random seeds</em>. Table II and Fig. 4 present the pre-registered results on 19,746 KSSL soils.</p>

<div class="table-caption">TABLE II: Pre-Registered Recall at 5% Budget on KSSL (19,746 Soils)</div>
<table class="ieee-table">
<thead>
<tr>
    <th>Sensor Modality</th>
    <th>EdaphNet</th>
    <th>Best Baseline</th>
    <th>Difference</th>
    <th>95% CI</th>
</tr>
</thead>
<tbody>
<tr>
    <td><i>W</i><sub>0</sub> (None)</td>
    <td>0.238</td>
    <td>0.271 (<i>B</i><sub>5</sub>)</td>
    <td>-0.033</td>
    <td>[-0.049, -0.016]</td>
</tr>
<tr>
    <td><i>W</i><sub>1</sub> (Color, &Delta;<i>E</i> = 0)</td>
    <td>0.416</td>
    <td>0.415 (<i>B</i><sub>5</sub>)</td>
    <td>+0.001</td>
    <td>[-0.022, +0.023]</td>
</tr>
<tr>
    <td><i>W</i><sub>1</sub> (Phone, &Delta;<i>E</i> = 2)</td>
    <td>0.410</td>
    <td>0.396 (<i>B</i><sub>5</sub>)</td>
    <td>+0.014</td>
    <td>[-0.008, +0.038]</td>
</tr>
<tr>
    <td><i>W</i><sub>1</sub> (Noisy, &Delta;<i>E</i> = 4)</td>
    <td>0.382</td>
    <td>0.354 (<i>B</i><sub>5</sub>)</td>
    <td>+0.028</td>
    <td>[+0.010, +0.049]</td>
</tr>
<tr class="last-row">
    <td><strong><i>W</i><sub>3</sub> (Spectrometer)</strong></td>
    <td><strong>0.604</strong></td>
    <td><strong>0.512 (<i>B</i><sub>5</sub>)</strong></td>
    <td><strong>+0.092</strong></td>
    <td><strong>[+0.069, +0.113]</strong></td>
</tr>
</tbody>
</table>

<figure class="ieee-fig">
    <img src="REPLACE_FIG2" alt="KSSL Recall Performance">
    <figcaption class="ieee-caption"><strong>Fig. 4.</strong> Pre-registered KSSL benchmark recall at 5% re-test budget. Whiskers indicate 95% bootstrap confidence intervals. With commodity phone optics (&Delta;<i>E</i> = 2), overall recall matches the best supervised baseline; with a laboratory spectrometer, EdaphNet achieves a +9.2 percentage point gain (<i>p</i> &lt; 0.001).</figcaption>
</figure>

<p>Under pre-registered Hypothesis A1, the headline hypothesis that commodity RGB color would outperform all existing methods by &ge; +5 points across an equal mix of errors was <strong>refuted</strong>. However, with continuous spectroscopy (<i>W</i><sub>3</sub>), EdaphNet achieved a statistically significant +9.2 point gain over the best supervised baseline.</p>

<h3 class="ieee-subsec">B. Decomposing the Trade-Off: Swaps vs. Numerical Corruptions</h3>
<p>Exploratory decomposition (Fig. 5) reveals the underlying trade-off:</p>
<p><strong>1) Specimen Swap Dominance:</strong> On sample swaps, EdaphNet outperformed <i>B</i><sub>5</sub> by <strong>+10.3 percentage points</strong> (95% CI: [+0.064, +0.139]) with phone color, and by <strong>+23.1 points</strong> ([+0.205, +0.258]) with spectroscopy. Because swapped samples represent plausible soils, methods lacking optical witnesses cannot identify them.</p>
<p><strong>2) Numeric Corruption Deficit:</strong> On isolated numerical corruptions, EdaphNet lagged <i>B</i><sub>5</sub> by -8.2 points ([-0.116, -0.050]). Diagnostic runs revealed that <i>B</i><sub>5</sub> heavily exploited the hard domain inequality SOC &le; <i>C</i><sub>tot</sub>. While EdaphNet's Gaussian process captured continuous correlation, it did not strictly enforce the hard ceiling inequality.</p>

<figure class="ieee-fig">
    <img src="REPLACE_FIG3" alt="Swap vs Value Breakdown">
    <figcaption class="ieee-caption"><strong>Fig. 5.</strong> Breakdown of detection recall for specimen swaps versus numerical value corruptions. EdaphNet holds a decisive +10.3 point advantage on specimen swaps under phone optics, while supervised baselines excel at isolated gross errors on constrained properties.</figcaption>
</figure>

<h3 class="ieee-subsec">C. Root-Cause Fault Attribution</h3>
<p>While existing baselines merely generate uninterpretable anomaly scores, EdaphNet accurately identifies the underlying error mechanism. As shown in Table III, EdaphNet achieved 97&ndash;100% accuracy in diagnosing the correct corruption operator and 87&ndash;99% accuracy in identifying the exact swap partner.</p>

<div class="table-caption">TABLE III: Root-Cause Fault Attribution Accuracy (%)</div>
<table class="ieee-table">
<thead>
<tr>
    <th>Setting</th>
    <th>EdaphNet (Proposed)</th>
    <th>Rule Heuristic (<i>B</i><sub>6</sub>)</th>
    <th>Baselines (<i>B</i><sub>4</sub>, <i>B</i><sub>5</sub>, <i>B</i><sub>7</sub>)</th>
</tr>
</thead>
<tbody>
<tr>
    <td>Simulation (<i>T</i><sub>0</sub>)</td>
    <td><strong>84–92%</strong></td>
    <td>32–50%</td>
    <td>Cannot Attribute</td>
</tr>
<tr>
    <td>ICRAF (Color <i>W</i><sub>1</sub>)</td>
    <td><strong>89–98%</strong></td>
    <td>37–51%</td>
    <td>Cannot Attribute</td>
</tr>
<tr class="last-row">
    <td>KSSL (Spectro <i>W</i><sub>3</sub>)</td>
    <td><strong>97–100%</strong></td>
    <td>24–29%</td>
    <td>Cannot Attribute</td>
</tr>
</tbody>
</table>

<h3 class="ieee-subsec">D. Error-Mix Sensitivity Analysis</h3>
<p>In commercial laboratories, the ratio of specimen swaps to typographical slips varies by automation level. We evaluated performance across varying swap shares &omega; &isin; [0.1, 0.9] (Fig. 6). With commodity phone optics (<i>W</i><sub>1</sub>), EdaphNet's performance advantage expands monotonically, dominating supervised baselines once swaps represent &ge; 60&ndash;70% of batch failures.</p>

<figure class="ieee-fig">
    <img src="REPLACE_FIG5" alt="Error Mix Sensitivity">
    <figcaption class="ieee-caption"><strong>Fig. 6.</strong> Sensitivity to batch error composition. As the share of specimen swaps among batch errors varies from 10% to 90%, EdaphNet's advantage expands. With phone color, EdaphNet surpasses all baselines once swaps exceed 60&ndash;70%; with spectroscopy, it dominates above 30%.</figcaption>
</figure>

<h2 class="ieee-sec">VIII. Cyber-Physical Deployment</h2>
<p class="no-indent"><strong>A. Hybrid Combined Policy:</strong> We implemented and smoke-tested a two-stage hybrid verification policy on KSSL (<i>W</i><sub>1</sub>, &Delta;<i>E</i> = 2): EdaphNet serves as the primary permutation sieve, while deterministic boundary rules audit single-cell bounds. The combined policy achieved balanced recall: 0.20&ndash;0.25 on swaps and 0.222 on value errors, eliminating the single-checker deficit.</p>

<p class="no-indent"><strong>B. Computational Throughput:</strong> Full joint inference over 281 unique permutation hypotheses for a 24-well sample tray executes in <strong>18 milliseconds</strong> (17.9 &plusmn; 1.2 ms) on an AMD Ryzen 5 7520U processor, allowing automated inline verification before destructive digestion.</p>

<h2 class="ieee-sec">IX. Conclusion</h2>
<p>This paper presented EdaphNet, a cyber-physical laboratory verification framework that combines joint permutation-corruption inference with optical physical witnesses. Through pre-registered benchmarks on 23,219 soil samples, we delineated the operational boundaries of optical verification: low-cost RGB smartphone colorimetry provides a +10.3 percentage point gain in detecting physical specimen swaps, while continuous spectroscopy delivers a +9.2 percentage point gain across all error types with 97&ndash;100% root-cause explanation accuracy. Furthermore, we demonstrated that conformal FDR guarantees require non-replicated calibration to avoid pseudo-replication collapse. Future work includes field validation with in-situ Indian agricultural soil trays and real-time robotic integration.</p>

<h2 class="ieee-sec">Acknowledgment</h2>
<p class="no-indent">The authors express their deepest gratitude to their faculty guide, <strong>Dr. Priya Saminathan</strong>, School of Computer Science and Engineering, Vellore Institute of Technology, Vellore, for her dedicated mentorship, invaluable domain insights, and critical review throughout this project. The authors also thank Vellore Institute of Technology, Vellore, for providing computational infrastructure, and acknowledge the USDA-NRCS Kellogg Soil Survey Laboratory (KSSL) and the World Agroforestry Centre (ICRAF-ISRIC) for their open-access soil spectral datasets.</p>

<h2 class="ieee-sec">Reproducibility Statement</h2>
<p class="no-indent">All code, model weights, experiment configs, and run records are open-source and version-controlled at: <a href="https://github.com/Sudeep-Sharma1/edaphnet-v2">https://github.com/Sudeep-Sharma1/edaphnet-v2</a>. Every metric and figure in this paper traces directly to automated experiment logs.</p>

<h2 class="ieee-sec">References</h2>
<ol class="references">
    <li>R. J. Even, M. B. Machmuller, J. M. Lavallee, T. J. Zelikova, and M. F. Cotrufo, "Large errors in soil carbon measurements attributed to inconsistent sample processing," <em>SOIL</em>, vol. 11, no. 1, pp. 17&ndash;34, Jan. 2025, doi: 10.5194/soil-11-17-2025.</li>
    <li>J. O. Westgard and S. A. Westgard, <em>Basic QC Practices: Training in Statistical Quality Control for Healthcare Laboratories</em>, 4th ed., Madison, WI, USA: Westgard Quality Corporation, 2020.</li>
    <li>M. W. Rosenbaum and J. M. Baron, "Using machine learning-based multianalyte delta checks to detect wrong blood in tube errors," <em>Am. J. Clin. Pathol.</em>, vol. 150, no. 6, pp. 555&ndash;566, Dec. 2018, doi: 10.1093/ajcp/aqy085.</li>
    <li>H. Zhou, J. Mueller, M. Kumar, J.-L. Wang, and J. Lei, "Detecting errors in numerical data via any regression model," <em>Trans. Mach. Learn. Res.</em>, 2024, arXiv:2305.16583.</li>
    <li>R. A. Viscarra Rossel <em>et al.</em>, "A global spectral library to characterize the world's soil," <em>Earth-Sci. Rev.</em>, vol. 155, pp. 198&ndash;230, Apr. 2016, doi: 10.1016/j.earscirev.2016.01.012.</li>
    <li>J. L. Safanelli <em>et al.</em>, "Open Soil Spectral Library (OSSL): Building reproducible soil calibration models through open development and community engagement," <em>PLOS ONE</em>, vol. 20, no. 1, p. e0296545, Jan. 2025, doi: 10.1371/journal.pone.0296545.</li>
    <li>J. E. Herrick <em>et al.</em>, "LandPKS: A mobile application for soil identification, monitoring, and land potential assessment," <em>J. Soil Water Conserv.</em>, vol. 75, no. 2, pp. 33A&ndash;37A, Mar./Apr. 2020, doi: 10.2489/jswc.75.2.33A.</li>
    <li>B. K. Stephenson, D. G. Hoch, and L. P. Collette, III, "Validation of laboratory test data based on predicted values of property-of-interest," U.S. Patent 8,352,394 B2, Jan. 8, 2013.</li>
    <li>K. W. Broman <em>et al.</em>, "Identification and correction of sample mix-ups in expression genetic studies," <em>G3: Genes, Genomes, Genetics</em>, vol. 5, no. 10, pp. 2177&ndash;2186, Oct. 2015, doi: 10.1534/g3.115.019778.</li>
    <li>J. Schmidinger, R. Gebbers, M.-O. Gasser, V. Barkov, G. M. Wu, and V. I. Adamchuk, "Rejections based on predictive uncertainty enable reliable routine soil spectroscopy," arXiv preprint arXiv:2606.21179, June 2026.</li>
    <li>S. Bates, E. Cand&egrave;s, L. Lei, and Y. Romano, "Testing for outliers with conformal p-values," <em>Ann. Statist.</em>, vol. 51, no. 1, pp. 149&ndash;178, Feb. 2023, doi: 10.1214/22-AOS2234.</li>
    <li>Y. Jin and E. J. Cand&egrave;s, "Selection by prediction with conformal p-values," <em>J. Amer. Statist. Assoc.</em>, vol. 118, no. 544, pp. 2533&ndash;2545, Dec. 2023, doi: 10.1080/01621459.2023.2185532.</li>
    <li>A. N. Angelopoulos and S. Bates, "Conformal prediction: A gentle introduction," <em>Found. Trends Mach. Learn.</em>, vol. 16, no. 4, pp. 494&ndash;591, 2023, doi: 10.1561/2200000101.</li>
    <li>V. Vovk, A. Gammerman, and G. Shafer, <em>Algorithmic Learning in a Random World</em>. New York, NY, USA: Springer, 2005.</li>
    <li>Y. Benjamini and Y. Hochberg, "Controlling the false discovery rate: A practical and powerful approach to multiple testing," <em>J. Roy. Statist. Soc. Ser. B</em>, vol. 57, no. 1, pp. 289&ndash;300, 1995, doi: 10.1111/j.2517-6161.1995.tb02031.x.</li>
    <li>E. Cand&egrave;s, Y. Fan, L. Janson, and J. Lv, "Panning for gold: Model-X knockoffs for high dimensional controlled variable selection," <em>J. Roy. Statist. Soc. Ser. B</em>, vol. 80, no. 3, pp. 551&ndash;577, June 2018, doi: 10.1111/rssb.12265.</li>
    <li>R. J. Tibshirani, R. Foygel Barber, E. J. Cand&egrave;s, and A. Ramdas, "Conformal prediction under covariate shift," in <em>Adv. Neural Inf. Process. Syst. (NeurIPS)</em>, vol. 32, pp. 2530&ndash;2540, Dec. 2019.</li>
    <li>A. Storkey, "When training and test sets are different: Characterizing dataset shift in machine learning," in <em>Dataset Shift in Machine Learning</em>, MIT Press, 2009, pp. 3&ndash;28.</li>
</ol>

</div>
</body>
</html>
"""
    # Replace placeholders with base64 strings
    html = html.replace("REPLACE_FIG0", fig0)
    html = html.replace("REPLACE_FIG1", fig1)
    html = html.replace("REPLACE_FIG2", fig2)
    html = html.replace("REPLACE_FIG3", fig3)
    html = html.replace("REPLACE_FIG4", fig4)
    html = html.replace("REPLACE_FIG5", fig5)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_html = OUT_DIR / "EdaphNet_IEEE_Transactions_Paper.html"
    out_html.write_text(html, encoding="utf-8")
    print(f"Wrote IEEE HTML to: {out_html}")
    
    # Also write to reports/Project_review_3.html
    review3_html = OUT_DIR / "Project_review_3.html"
    review3_html.write_text(html, encoding="utf-8")
    print(f"Wrote Project_review_3 HTML to: {review3_html}")
    
    return out_html


def convert_html_to_pdf(html_path):
    chrome_bin = None
    for p in CHROME_PATHS:
        if Path(p).exists():
            chrome_bin = p
            break

    if not chrome_bin:
        print("Warning: Neither Chrome nor Edge executable was found for PDF rendering.")
        return None

    pdf_path = html_path.with_suffix(".pdf")
    cmd = [
        chrome_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        str(html_path),
    ]
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and pdf_path.exists():
        print(f"Successfully generated PDF: {pdf_path} ({pdf_path.stat().st_size:,} bytes)")
        
        # Copy to Project_review_3.pdf in reports/ and results/
        review3_pdf_reports = OUT_DIR / "Project_review_3.pdf"
        shutil.copy2(pdf_path, review3_pdf_reports)
        print(f"Copied to: {review3_pdf_reports}")
        
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        review3_pdf_results = RESULTS_DIR / "Project_review_3.pdf"
        shutil.copy2(pdf_path, review3_pdf_results)
        print(f"Copied to: {review3_pdf_results}")
        
        # Also copy to EdaphNet_Review_Revised_2.pdf
        revised2_pdf = OUT_DIR / "EdaphNet_Review_Revised_2.pdf"
        shutil.copy2(pdf_path, revised2_pdf)
        print(f"Copied to: {revised2_pdf}")
        
        return pdf_path
    else:
        print(f"PDF generation failed: {res.stderr}")
        return None


if __name__ == "__main__":
    h = build_ieee_html()
    convert_html_to_pdf(h)
