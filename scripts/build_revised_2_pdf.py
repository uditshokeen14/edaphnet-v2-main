import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RESULTS_DIR = ROOT / "results"

SRC_HTML = REPORTS_DIR / "EdaphNet_IEEE_Transactions_Paper.html"
OUT_HTML_REPORTS = REPORTS_DIR / "EdaphNet_Review_Revised_2.html"
OUT_HTML_RESULTS = RESULTS_DIR / "EdaphNet_Review_Revised_2.html"

OUT_PDF_REPORTS = REPORTS_DIR / "EdaphNet_Review_Revised_2.pdf"
OUT_PDF_RESULTS = RESULTS_DIR / "EdaphNet_Review_Revised_2.pdf"

SRC_DOCX = REPORTS_DIR / "EdaphNet_Review_Revised.docx"
OUT_DOCX_REPORTS = REPORTS_DIR / "EdaphNet_Review_Revised_2.docx"
OUT_DOCX_RESULTS = RESULTS_DIR / "EdaphNet_Review_Revised_2.docx"

def main():
    content = SRC_HTML.read_text(encoding="utf-8")
    
    # Ensure Title reflects the paper and revised status
    content = content.replace("<title>Cyber-Physical Quality Assurance of Analytical Laboratories - IEEE Transactions</title>",
                              "<title>Cyber-Physical Quality Assurance of Analytical Laboratories - EdaphNet Review Revised 2</title>")
    
    # Ensure attribution qualifier is explicit in the abstract
    old_attr = "In root-cause fault attribution, EdaphNet achieves 97–100% accuracy, compared with 24–29% for rule-based heuristics."
    new_attr = "In root-cause fault attribution, EdaphNet achieves 97–100% accuracy in the spectrometer setting, compared with 24–29% for rule-based heuristics."
    if old_attr in content:
        content = content.replace(old_attr, new_attr)
        print("Updated attribution qualifier in abstract.")
    else:
        print("Note: attribution qualifier already present or formatted.")

    # Write out the revised HTML files
    OUT_HTML_REPORTS.write_text(content, encoding="utf-8")
    OUT_HTML_RESULTS.write_text(content, encoding="utf-8")
    print(f"Wrote HTML to {OUT_HTML_REPORTS} and {OUT_HTML_RESULTS}")

    # Render PDF using Headless Chrome or Edge
    browser = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(browser):
        browser = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    print(f"Rendering PDF with {browser}...")
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUT_PDF_REPORTS}",
        OUT_HTML_REPORTS.resolve().as_uri()
    ]
    subprocess.run(cmd, check=True)
    print(f"Generated PDF at {OUT_PDF_REPORTS} ({OUT_PDF_REPORTS.stat().st_size / 1024:.1f} KB)")

    # Copy PDF to results
    shutil.copy2(OUT_PDF_REPORTS, OUT_PDF_RESULTS)
    print(f"Copied PDF to {OUT_PDF_RESULTS} ({OUT_PDF_RESULTS.stat().st_size / 1024:.1f} KB)")

    # Also copy DOCX to Review_Revised_2.docx
    if SRC_DOCX.exists():
        shutil.copy2(SRC_DOCX, OUT_DOCX_REPORTS)
        shutil.copy2(SRC_DOCX, OUT_DOCX_RESULTS)
        print(f"Copied DOCX to {OUT_DOCX_REPORTS} and {OUT_DOCX_RESULTS}")

if __name__ == "__main__":
    main()
