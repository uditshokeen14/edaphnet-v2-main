"""EdaphNet app server (docs/24 §7): one backend for the farmer-facing page in app/web.

Standard library HTTP server; run with the main Python (it needs torch for the leaf model):

    "C:\\Program Files\\Python314\\python.exe" app/server.py        # then open http://localhost:8001

Endpoints (POST, JSON in / JSON out):
  /api/soil          soil photo -> colour -> predicted OC / N / total C with 90% ranges (research model)
  /api/report-check  soil photo + lab report -> consistency + batch check (research method)
  /api/crops         pH (or a pH range) + rainfall + temperature (+ texture, irrigation) -> ranked crops
  /api/leaf          leaf photo -> top-3 crop/disease with confidence, "not sure", management info
GET /api/status says which parts are available. Each model is loaded on first use; if one is missing
(models/ is git-ignored), only that tab reports an error.
"""
import base64
import io
import json
import sys
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.crop.suitability import Field, load_crops, ph_range_scenarios, rank_crops  # noqa: E402

PAGE = ROOT / "app" / "web" / "index.html"
DISEASES = json.loads((ROOT / "app" / "knowledge" / "diseases.json").read_text(encoding="utf-8"))
MAX_BODY = 12 * 1024 * 1024          # 12 MB request limit (the page shrinks photos before sending)
SOIL_BOX_FRACTION = 0.5              # without a marked area, use the central half of the photo


class Lazy:
    """Load an engine once, on first use, and remember a load error instead of crashing."""

    def __init__(self, factory):
        self.factory, self.lock = factory, threading.Lock()
        self.obj: Any = None
        self.error: str | None = None

    def get(self) -> Any:
        with self.lock:
            if self.obj is None and self.error is None:
                try:
                    self.obj = self.factory()
                except BaseException as e:          # SystemExit from a missing model file included
                    self.error = str(e) or type(e).__name__
        if self.error:
            raise RuntimeError(self.error)
        return self.obj


def _soil_engine():
    from serve_demo import Engine
    return Engine()


def _leaf_engine():
    from app.leaf.model import MODEL_PATH, LeafModel
    if not MODEL_PATH.exists():
        raise RuntimeError("models/leaf_head.joblib missing: run  scripts/app_leaf_features.py  then  "
                           "scripts/app_leaf_train.py")
    return LeafModel()


SOIL, LEAF = Lazy(_soil_engine), Lazy(_leaf_engine)
CROPS = load_crops()


def decode_image(data_url):
    from PIL import Image, ImageOps, UnidentifiedImageError
    raw = base64.b64decode(data_url.split(",", 1)[-1])
    try:
        im = Image.open(io.BytesIO(raw))
    except UnidentifiedImageError:
        raise ValueError("This file is not a readable image (use a JPEG or PNG photo).") from None
    return ImageOps.exif_transpose(im).convert("RGB")      # phone photos carry a rotation tag


# ------------------------------------------------------------------ endpoint logic
def soil(req, with_report=False):
    im = decode_image(req["image"])
    w, h = im.size
    box = req.get("soil_box")
    if not box:
        m = (1 - SOIL_BOX_FRACTION) / 2
        box = [w * m, h * m, w * (1 - m), h * (1 - m)]
    rgba = np.dstack([np.asarray(im), np.full((h, w), 255, np.uint8)])
    out = SOIL.get().analyze({"width": w, "height": h, "rgba": base64.b64encode(rgba.tobytes()).decode(),
                              "corners": req.get("corners"), "soil_box": box,
                              "report": req.get("report") if with_report else None})
    out["soil_box"] = [round(float(v)) for v in box]
    out["note"] = ("Soil type (black / red / alluvial ...) is not predicted yet: no audited soil-image "
                   "dataset has been used (docs/25). Only colour-based properties are shown.")
    return out


def crops(req):
    texture = req.get("texture") or None
    irrigated = bool(req.get("irrigated"))
    rain, temp = float(req["rain_mm"]), float(req["temp_c"])
    if req.get("ph") not in (None, ""):
        scenarios = Field(ph=float(req["ph"]), rain_mm=rain, temp_c=temp, texture=texture, irrigated=irrigated)
        mode = "single pH"
    else:                                              # pH unknown: average over a range ("multi-soil")
        lo, hi = float(req.get("ph_lo") or 5.0), float(req.get("ph_hi") or 8.5)
        scenarios = ph_range_scenarios(min(lo, hi), max(lo, hi), rain, temp, texture=texture, irrigated=irrigated)
        mode = f"pH unknown: averaged over pH {min(lo, hi):g}-{max(lo, hi):g}"
    res = rank_crops(scenarios, CROPS)
    overridden = {c["name"]: c.get("overridden", []) for c in CROPS}
    rows = [{**asdict(r), "overridden": overridden.get(r.name, [])} for r in res]
    return {"mode": mode, "crops": rows,
            "note": "Rule-based ranking from FAO EcoCrop ranges (law of the minimum). Not yet checked "
                    "against ICAR / state university recommendations (docs/24 Amendment 1): treat as a "
                    "starting list to discuss with an extension officer."}


def leaf(req):
    model = LEAF.get()
    out = model.predict_pil(decode_image(req["image"]))
    for t in out["top"]:
        info = DISEASES["diseases"].get(t["class"])
        if info:
            t["info"] = {**info, "source_url": DISEASES["sources"][info["source"]]}
        t["healthy"] = t["class"].endswith("healthy")
    out["classes_known"] = sorted({c.split("___")[0].replace("_", " ") for c in model.classes})
    out["general_note"] = DISEASES["general_note"]
    out["model_note"] = model.meta
    return out


def status():
    from app.leaf.model import MODEL_PATH
    metrics = ROOT / "results" / "app_leaf" / "metrics.json"
    return {"leaf_model": MODEL_PATH.exists(),
            "soil_model": (ROOT / "models" / "colour_brain_kssl3.joblib").exists(),
            "crops": len(CROPS), "diseases": len(DISEASES["diseases"]),
            "leaf_metrics": json.loads(metrics.read_text()) if metrics.exists() else None}


ROUTES = {"/api/soil": soil, "/api/report-check": lambda r: soil(r, with_report=True),
          "/api/crops": crops, "/api/leaf": leaf}


# ------------------------------------------------------------------ HTTP
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/status":
            self._send(200, status())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        fn = ROUTES.get(self.path)
        if fn is None:
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            return self._send(413, {"error": "photo too large"})
        try:
            self._send(200, fn(json.loads(self.rfile.read(n))))
        except Exception as e:     # show the reason in the page
            self._send(400, {"error": str(e)})

    def log_message(self, format, *args):
        pass


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--host", default="127.0.0.1", help="0.0.0.0 to open it from a phone on the same Wi-Fi")
    args = ap.parse_args()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"EdaphNet app running at  http://localhost:{args.port}   (Ctrl+C to stop)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
