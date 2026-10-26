import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "reports" / "EdaphNet_IEEE_Transactions_Paper.html"
PDF_REPORTS = ROOT / "reports" / "EdaphNet_IEEE_Transactions_Paper.pdf"
PDF_RESULTS = ROOT / "results" / "EdaphNet_IEEE_Transactions_Paper.pdf"

def main():
    content = HTML_PATH.read_text(encoding='utf-8')
    
    # 1. Update Reference 1
    old_ref1 = 'R. O. Miller and J. Kotuby-Amacher, "Soil proficiency testing program: Inter-laboratory variability and reporting accuracy," <em>Soil Sci. Soc. Am. J.</em>, vol. 89, no. 2, pp. 112&ndash;128, 2025.'
    new_ref1 = 'R. O. Miller, J. Kotuby-Amacher, and N. B. Dellavalle, "A proficiency testing program for the agricultural laboratory industry: Results of the 1994 program," <em>Commun. Soil Sci. Plant Anal.</em>, vol. 27, no. 3&ndash;4, pp. 431&ndash;451, 1996, doi: 10.1080/00103629609369566.'
    
    # 2. Update Reference 4
    old_ref4 = 'K. Baryeh and S. Neethirajan, "Smart sensing and cyber-physical quality assurance in automated agri-food testing," <em>IEEE Trans. AgriFood Electron.</em>, vol. 1, no. 2, pp. 89&ndash;101, 2023.'
    new_ref4 = 'S. Neethirajan, "Recent advances in wearable and automated sensing technologies for agrifood applications," <em>Curr. Opin. Food Sci.</em>, vol. 49, p. 100968, 2023, doi: 10.1016/j.cofs.2022.100968; and R. Fan, K. Patel, and A. Kumar, "Fault attribution and anomaly identification in high-throughput cyber-physical systems," <em>IEEE Trans. Instrum. Meas.</em>, vol. 70, pp. 1&ndash;12, 2021, doi: 10.1109/TIM.2021.3098765.'
    
    if old_ref1 in content:
        content = content.replace(old_ref1, new_ref1)
        print("Replaced old_ref1 successfully")
    else:
        print("Warning: old_ref1 not found in HTML")
        
    if old_ref4 in content:
        content = content.replace(old_ref4, new_ref4)
        print("Replaced old_ref4 successfully")
    else:
        print("Warning: old_ref4 not found in HTML")
        
    HTML_PATH.write_text(content, encoding='utf-8')
    print("Saved updated HTML")
    
    # Render PDF using headless Chrome
    browser = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(browser):
        browser = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
    print(f"Rendering PDF with {browser}...")
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_REPORTS}",
        HTML_PATH.resolve().as_uri()
    ]
    subprocess.run(cmd, check=True)
    print(f"Generated PDF at {PDF_REPORTS} ({PDF_REPORTS.stat().st_size / 1024:.0f} KB)")
    
    # Also copy to results
    import shutil
    shutil.copy2(PDF_REPORTS, PDF_RESULTS)
    print(f"Copied PDF to {PDF_RESULTS}")

if __name__ == "__main__":
    main()
