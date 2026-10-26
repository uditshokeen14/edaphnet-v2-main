"""Build reports/EdaphNet_Progress_Report.pdf from docs/22_progress_report.md.

No PDF library needed: the Markdown is converted to a print-styled HTML page (with two charts drawn
by matplotlib from the committed run records), then printed to PDF by headless Chrome or Edge.
Run with a Python that has matplotlib (e.g. the main Python install):

    "C:\\Program Files\\Python314\\python.exe" scripts/build_report_pdf.py
"""
import base64
import html
import io
import re
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "22_progress_report.md"
OUT_DIR = ROOT / "reports"
RUN_KSSL = ROOT / "results/runs/20261001-234902_real_kssl3_095deaa"
LADDER_KSSL = ROOT / "results/runs/20261001-234621_witness_ladder_kssl3_8148163"
LADDER_ICRAF = ROOT / "results/runs/20260925-003906_witness_ladder_icraf8_7050ab6"
BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
IMG_BASE = None
INK, MUTED, ACCENT, BAR, LINE = "#1c2220", "#59645f", "#7a5520", "#c9b28c", "#d6ddd9"


# ------------------------------------------------------------------ minimal Markdown -> HTML
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"(?<![\"'>])(https?://[^\s<]+)", r'<a href="\1">\1</a>', s)
    return s


def md_to_html(md):
    out, lines, i = [], md.splitlines(), 0
    para = []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            flush(); i += 1; continue
        if ln.startswith("#"):
            flush()
            lvl = len(ln) - len(ln.lstrip("#"))
            out.append(f"<h{lvl}>{inline(ln[lvl:].strip())}</h{lvl}>"); i += 1; continue
        mimg = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", ln.strip())
        if mimg and IMG_BASE is not None:
            flush()
            data = base64.b64encode((IMG_BASE / mimg.group(2)).read_bytes()).decode()
            out.append(f'<figure><img src="data:image/png;base64,{data}" alt="{html.escape(mimg.group(1))}"></figure>')
            i += 1; continue
        if ln.strip() == "---":
            flush(); out.append("<hr>"); i += 1; continue
        if ln.lstrip().startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            head, body = rows[0], [r for r in rows[2:]]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
                       + "</tbody></table>")
            continue
        m = re.match(r"^(\s*)(-|\d+\.)\s+(.*)", ln)
        if m:
            flush()
            tag = "ol" if m.group(2)[0].isdigit() else "ul"
            start = m.group(2)[:-1] if tag == "ol" else None
            items = []
            while i < len(lines):
                m2 = re.match(r"^(\s*)(-|\d+\.)\s+(.*)", lines[i])
                if m2:
                    items.append(m2.group(3)); i += 1
                elif lines[i][:1].isspace() and lines[i].strip() and items:   # indented continuation
                    items[-1] += " " + lines[i].strip(); i += 1
                else:
                    break
            attr = f' start="{start}"' if start and start != "1" else ""
            out.append(f"<{tag}{attr}>" + "".join(f"<li>{inline(t)}</li>" for t in items) + f"</{tag}>")
            continue
        para.append(ln.strip()); i += 1
    flush()
    return "\n".join(out)


# ------------------------------------------------------------------ charts from run records
def fig_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    return base64.b64encode(buf.getvalue()).decode()


def charts():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": LINE,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})

    # Figure 1: witness strength
    lk = pd.read_csv(LADDER_KSSL / "witness_ladder_metrics.csv")
    li = pd.read_csv(LADDER_ICRAF / "witness_ladder_metrics.csv")
    rows = [("KSSL", lk, p) for p in ("OC", "N", "Ctot")] + [("ICRAF", li, p) for p in ("OC", "pH", "clay", "CEC", "K")]
    labels = [f"{p}\n({d})" for d, _, p in rows]
    get = lambda df, r, p: float(df[(df.rung == r) & (df.property == p)]["r2_latent_test"].iloc[0])  # noqa: E731
    col = [max(0, get(df, "W1_dE2", p)) for _, df, p in rows]
    spe = [max(0, get(df, "W3", p)) for _, df, p in rows]
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    x = range(len(rows))
    ax.bar([v - 0.2 for v in x], col, 0.4, color=BAR, label="Colour, good phone (ΔE 2)")
    ax.bar([v + 0.2 for v in x], spe, 0.4, color=ACCENT, label="Spectrometer")
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, 1); ax.set_ylabel("R² on unseen locations")
    ax.grid(axis="y", color=LINE, lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    f1 = fig_png(fig); plt.close(fig)

    # Figure 2: pre-registered KSSL result
    a1 = pd.read_csv(RUN_KSSL / "amendment_A1.csv")
    a1 = a1[a1.ordering == "random"].set_index("lambda").loc[["W0", "W1_dE0", "W1_dE2", "W1_dE4", "W3"]]
    names = ["No witness", "Colour\n(perfect)", "Colour\n(good phone)", "Colour\n(noisy phone)", "Spectrometer"]
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    x = range(len(a1))
    ax.bar([v - 0.2 for v in x], a1["best_recall"], 0.4, color="#9aa6a1", label="Best existing method")
    ax.bar([v + 0.2 for v in x], a1["full_recall"], 0.4, color=ACCENT, label="EdaphNet")
    lo = a1["best_recall"] + a1["ci_low"]
    hi = a1["best_recall"] + a1["ci_high"]
    ax.errorbar([v + 0.2 for v in x], a1["full_recall"], yerr=[a1["full_recall"] - lo, hi - a1["full_recall"]],
                fmt="none", ecolor=INK, capsize=3, lw=1)
    for v, d in zip(x, a1["diff"]):
        ax.text(v, 0.02, f"{d:+.3f}", ha="center", color="white" if abs(d) > 0 else INK, fontsize=8, fontweight="bold")
    ax.set_xticks(list(x), names); ax.set_ylim(0, 0.75)
    ax.set_ylabel("Share of errors found\n(top 5% re-tested)")
    ax.grid(axis="y", color=LINE, lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    f2 = fig_png(fig); plt.close(fig)
    return f1, f2


CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font: 10.3pt/1.5 "Segoe UI", Calibri, Arial, sans-serif; color: #1c2220; margin: 0; }
h1 { font: 600 22pt/1.2 Georgia, "Times New Roman", serif; margin: 0 0 4pt; }
h2 { font: 600 14pt/1.25 Georgia, serif; margin: 18pt 0 6pt; padding-top: 6pt; border-top: 1px solid #d6ddd9; page-break-after: avoid; }
h3 { font: 600 11pt/1.3 "Segoe UI", Arial, sans-serif; margin: 12pt 0 4pt; color: #7a5520; page-break-after: avoid; }
p { margin: 0 0 7pt; } ul, ol { margin: 0 0 8pt; padding-left: 18pt; } li { margin-bottom: 3pt; }
hr { display: none; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 10pt; font-size: 9pt; page-break-inside: avoid; }
th { text-align: left; background: #efe4d2; color: #1c2220; font-weight: 600; padding: 4pt 6pt; border-bottom: 1px solid #c9b28c; }
td { padding: 4pt 6pt; border-bottom: 1px solid #e3e8e5; vertical-align: top; }
code { font-family: Consolas, "Courier New", monospace; font-size: 8.8pt; background: #f1f3f1; padding: 0 2pt; border-radius: 2pt; }
a { color: #7a5520; text-decoration: none; }
.cover { border-bottom: 3px solid #7a5520; padding-bottom: 10pt; margin-bottom: 8pt; }
.cover .eyebrow { font: 600 8pt Consolas, monospace; letter-spacing: .12em; text-transform: uppercase; color: #7a5520; }
.cover .sub { color: #59645f; font-size: 11pt; }
figure { margin: 6pt 0 12pt; page-break-inside: avoid; }
figure img { width: 100%; }
figcaption { font-size: 8.8pt; color: #59645f; }
"""


def main():
    md = SRC.read_text(encoding="utf-8")
    md = re.sub(r"^# .*\n", "", md, count=1)        # title goes on the cover block
    body = md_to_html(md)
    f1, f2 = charts()
    fig1 = (f'<figure><img src="data:image/png;base64,{f1}" alt="Witness strength chart"><figcaption>'
            "Figure 1. How much each witness reveals about each soil property (R², unseen locations). "
            "Colour mainly knows carbon; a spectrometer knows much more. Source: witness-ladder run records.</figcaption></figure>")
    fig2 = (f'<figure><img src="data:image/png;base64,{f2}" alt="Pre-registered result chart"><figcaption>'
            "Figure 2. Pre-registered KSSL test: share of erroneous reports found when the top 5% are re-tested "
            "(random batches, 5 seeds). Numbers at the bottom: EdaphNet minus best existing method; whiskers: 95% "
            f"interval of that difference. Source: {RUN_KSSL.name}.</figcaption></figure>")
    body = body.replace("<h3>6.3", fig1 + "<h3>6.3", 1).replace("<h3>6.4", fig2 + "<h3>6.4", 1)
    cover = ('<div class="cover"><div class="eyebrow">Research progress report · 2 October 2026</div>'
             "<h1>EdaphNet</h1><div class=\"sub\">Checking soil laboratory reports with an independent sample "
             "witness: what has been done, what was found, and what remains</div></div>")
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>EdaphNet Progress Report</title>'
            f"<style>{CSS}</style></head><body>{cover}{body}</body></html>")
    OUT_DIR.mkdir(exist_ok=True)
    html_path = OUT_DIR / "EdaphNet_Progress_Report.html"
    pdf_path = OUT_DIR / "EdaphNet_Progress_Report.pdf"
    html_path.write_text(page, encoding="utf-8")
    browser = next((b for b in BROWSERS if Path(b).exists()), None)
    if browser is None:
        raise SystemExit(f"No Chrome/Edge found. Open {html_path} in a browser and use Print -> Save as PDF.")
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    print("wrote", pdf_path, f"({pdf_path.stat().st_size / 1024:.0f} KB)")


def paper():
    """PDF of docs/paper/draft_v0.md with its figures embedded."""
    global IMG_BASE
    src = ROOT / "docs" / "paper" / "draft_v0.md"
    IMG_BASE = src.parent
    md = src.read_text(encoding="utf-8")
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"^# .*\n", "", md, count=1)
    m = re.search(r"\*\*Title:\*\* (.+?)\n\n", md, re.S)
    if m is None:
        raise SystemExit("The draft needs a '**Title:** ...' line.")
    title = m.group(1).replace("\n", " ")
    md = re.sub(r"\*\*Title:\*\*.+?\n\n(\*\(The A1-pass.*?\)\*\n)?", "", md, count=1, flags=re.S)
    body = md_to_html(md)
    cover = ('<div class="cover"><div class="eyebrow">Manuscript draft v0 · not for circulation · 2 October 2026</div>'
             f"<h1 style=\"font-size:17pt\">{html.escape(title)}</h1><div class=\"sub\">EdaphNet project · "
             "results traceable to run records in the repository</div></div>")
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>EdaphNet Draft</title>'
            f"<style>{CSS}</style></head><body>{cover}{body}</body></html>")
    OUT_DIR.mkdir(exist_ok=True)
    html_path, pdf_path = OUT_DIR / "EdaphNet_Paper_Draft_v0.html", OUT_DIR / "EdaphNet_Paper_Draft_v0.pdf"
    html_path.write_text(page, encoding="utf-8")
    browser = next((b for b in BROWSERS if Path(b).exists()), None)
    if browser is None:
        raise SystemExit(f"No Chrome/Edge found. Open {html_path} in a browser and use Print -> Save as PDF.")
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    print("wrote", pdf_path, f"({pdf_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    import sys
    paper() if "--paper" in sys.argv else main()
