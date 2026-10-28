"""Render Mermaid diagrams (.mmd) to SVG and high-resolution PNG using Headless Chrome."""
import html
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MERMAID_JS_URL = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"
LOCAL_MERMAID = ROOT / ".pytest_cache" / "mermaid.min.js"

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def get_browser():
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    raise RuntimeError("Neither Chrome nor Edge was found on the system.")


def ensure_mermaid_js():
    if not LOCAL_MERMAID.exists() or LOCAL_MERMAID.stat().st_size < 10000:
        print("Downloading Mermaid.js...")
        LOCAL_MERMAID.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(MERMAID_JS_URL, LOCAL_MERMAID)
        print(f"Saved Mermaid.js to {LOCAL_MERMAID} ({LOCAL_MERMAID.stat().st_size} bytes)")
    return LOCAL_MERMAID.read_text(encoding="utf-8")


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    margin: 0;
    padding: 30px;
    background-color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    display: inline-block;
  }}
  #container {{
    display: inline-block;
  }}
  .mermaid svg {{
    max-width: none !important;
    height: auto !important;
  }}
</style>
<script>
{mermaid_js}
</script>
</head>
<body>
<div id="container">
  <pre class="mermaid">
{diagram_source}
  </pre>
</div>
<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'neutral',
    themeVariables: {{
      fontSize: '14px',
      fontFamily: "'Segoe UI', Arial, sans-serif"
    }},
    flowchart: {{
      useMaxWidth: false,
      htmlLabels: true,
      curve: 'basis'
    }}
  }});
</script>
</body>
</html>
"""


def render_diagram(browser, js_content, mmd_path, svg_out, png_out, window_size="2800,2200"):
    print(f"\n--- Processing {mmd_path.name} ---")
    source = mmd_path.read_text(encoding="utf-8")
    page_html = HTML_TEMPLATE.format(mermaid_js=js_content, diagram_source=source)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_html = Path(tmp_dir) / "render.html"
        tmp_user_data = Path(tmp_dir) / "chrome_user_data"
        tmp_html.write_text(page_html, encoding="utf-8")

        file_url = tmp_html.as_uri()

        # Step 1: Extract SVG via dump-dom
        cmd_dump = [
            browser,
            "--headless=new",
            f"--user-data-dir={tmp_user_data}",
            "--virtual-time-budget=10000",
            "--dump-dom",
            file_url,
        ]
        res = subprocess.run(cmd_dump, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        dom = res.stdout

        svg_match = re.search(r"(<svg[^>]*id=\"mermaid-[^\"]*\"[^>]*>.*?</svg>)", dom, re.DOTALL)
        if not svg_match:
            # Fallback to any svg
            svg_match = re.search(r"(<svg[^>]*>.*?</svg>)", dom, re.DOTALL)

        if svg_match:
            svg_str = svg_match.group(1)
            # Ensure proper xmlns
            if "xmlns=" not in svg_str:
                svg_str = svg_str.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"')
            svg_out.write_text(svg_str, encoding="utf-8")
            print(f"[OK] Generated SVG: {svg_out} ({svg_out.stat().st_size} bytes)")
        else:
            print("[WARN] Could not extract SVG from DOM. DOM snippet:", dom[:500])

        # Step 2: High-resolution PNG Screenshot
        cmd_shot = [
            browser,
            "--headless=new",
            f"--user-data-dir={tmp_user_data}",
            f"--window-size={window_size}",
            "--virtual-time-budget=10000",
            f"--screenshot={png_out}",
            file_url,
        ]
        subprocess.run(cmd_shot, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if png_out.exists() and png_out.stat().st_size > 1000:
            print(f"[OK] Generated PNG: {png_out} ({png_out.stat().st_size} bytes)")
        else:
            print(f"[WARN] PNG generation failed for {png_out}")


def main():
    browser = get_browser()
    print(f"Using browser: {browser}")
    js_content = ensure_mermaid_js()

    render_diagram(
        browser=browser,
        js_content=js_content,
        mmd_path=DOCS / "system_architecture.mmd",
        svg_out=DOCS / "system_architecture.svg",
        png_out=DOCS / "system_architecture.png",
        window_size="2800,2600",
    )

    render_diagram(
        browser=browser,
        js_content=js_content,
        mmd_path=DOCS / "system_workflow.mmd",
        svg_out=DOCS / "system_workflow.svg",
        png_out=DOCS / "system_workflow.png",
        window_size="3200,3400",
    )


if __name__ == "__main__":
    main()
