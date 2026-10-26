"""Live demo server: soil photo + lab report -> each pipeline step -> result.

Standard library only (http.server); runs the real model code. Start it and open the page:

    python scripts/serve_demo.py            # then open http://localhost:8000

Pipeline per request (same code as the experiments):
  1 photo with a ColorChecker  -> colour correction (phone.py), chart residual ΔE00, photo quality
  2 corrected soil colour      -> "colour brain" (models/colour_brain_kssl3.joblib) -> predicted
                                  OC / N / total C with 90% ranges
  3 lab report vs prediction   -> per-value consistency
  4 report placed in a batch of 11 real KSSL test reports -> joint batch model (inference.py)
                                  -> suspicion ranking with explanations

The built-in example photos are SIMULATED: real KSSL soils' colours (from their lab spectra)
rendered through an imperfect camera, with a colour card in the frame. They are labelled as such.
"""
import base64
import json
import struct
import sys
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from edaphnet2 import phone  # noqa: E402
from edaphnet2.inference import InferenceConfig, infer_batch  # noqa: E402
from edaphnet2.witness import FixedGaussianModel  # noqa: E402
from run_real import load  # noqa: E402

PAGE = ROOT / "demo_site" / "live.html"
BRAIN = ROOT / "models" / "colour_brain_kssl3.joblib"
WITNESS = "W1_dE2"          # witness model for the batch: colour with phone-like noise
CAMERA = np.array([[0.86, 0.11, 0.03], [0.07, 0.87, 0.06], [0.03, 0.14, 0.83]])   # a colour-shifting camera
W_IMG, H_IMG = 640, 440
CHART = [(20, 20), (620, 20), (620, 200), (20, 200)]
SOIL_BOX = [150, 230, 490, 420]


# ------------------------------------------------------------------ setup (once)
class Engine:
    def __init__(self):
        import joblib
        if not BRAIN.exists():
            raise SystemExit("models/colour_brain_kssl3.joblib missing: run  python scripts/train_colour_brain.py")
        self.D, self.Wt, self.space = load("kssl3")
        self.names = list(self.space.names)
        self.brain = joblib.load(BRAIN)
        self.S = self.Wt[f"{WITNESS}__S"]
        self.sd = np.sqrt(np.diag(self.S))
        self.model = FixedGaussianModel(self.S)
        self.cfg = InferenceConfig(rho=0.1, eps=0.05, space=self.space)
        self.Y = self.space.print_values(self.D["X"])
        train_lab = self.D["lab"][self.D["split"] == "train"]
        self.lab_lo, self.lab_hi = np.percentile(train_lab, 0.5, axis=0), np.percentile(train_lab, 99.5, axis=0)
        test = np.where(self.D["split"] == "test")[0]
        rng = np.random.default_rng(2026)
        self.batch_idx = rng.choice(test, 11, replace=False)      # fixed neighbours for the batch view
        order = test[np.argsort(self.D["lab"][test, 0])]           # examples from dark to light soil
        self.examples = [int(order[int(q * (len(order) - 1))]) for q in (0.04, 0.2, 0.4, 0.6, 0.8, 0.96)]

    # ---------------- simulated photo of one real soil sample
    def photo(self, i, seed):
        rng = np.random.default_rng(seed)
        lin = np.full((H_IMG, W_IMG, 3), 0.16)
        ref = phone.reference_linear_srgb()
        half = 22
        for k, (x, y) in enumerate(phone.grid_centers(CHART)):
            x, y = int(x), int(y)
            lin[y - half:y + half, x - half:x + half] = ref[k]
        x0, y0, x1, y1 = SOIL_BOX
        soil = lab_to_lin(self.D["lab"][i])
        grain = np.exp(rng.normal(0, 0.10, (y1 - y0, x1 - x0, 1)))   # granular texture
        lin[y0:y1, x0:x1] = soil * grain
        cast = np.diag(rng.uniform(0.92, 1.08, 3))                     # lighting colour cast
        seen = np.clip(0.85 * lin @ (CAMERA @ cast).T, 0, 1)
        img = phone.to_encoded(seen) + rng.normal(0, 0.006, seen.shape)
        return (np.clip(img, 0, 1) * 255).round().astype(np.uint8)

    def example_list(self):
        out = []
        for n, i in enumerate(self.examples):
            out.append({"id": n, "label": f"Soil {chr(65 + n)}", "png": png_b64(self.photo(i, 100 + n)),
                        "corners": CHART, "soil_box": SOIL_BOX,
                        "report": {k: float(v) for k, v in zip(self.names, self.Y[i])}})
        return {"names": self.names, "units": {"OC": "%", "N": "%", "Ctot": "%"}, "examples": out,
                "witness": WITNESS}

    # ---------------- full pipeline
    def analyze(self, req):
        w, h = int(req["width"]), int(req["height"])
        rgba = np.frombuffer(base64.b64decode(req["rgba"]), dtype=np.uint8).reshape(h, w, 4)
        img = rgba[..., :3].astype(float) / 255.0
        corners = [tuple(map(float, c)) for c in req["corners"]] if req.get("corners") else None
        x0, y0, x1, y1 = [int(round(v)) for v in req["soil_box"]]
        x0, x1 = sorted((max(0, x0), min(w, x1)))
        y0, y1 = sorted((max(0, y0), min(h, y1)))
        roi = np.zeros((h, w), bool)
        roi[y0:y1, x0:x1] = True
        if roi.sum() < 50:
            raise ValueError("The soil area is too small. Select a larger area of soil.")

        # 1 colour correction (only possible with a colour card in the photo)
        lin = phone.to_linear(img)
        identity = {"M": np.eye(3), "kind": "linear"}
        raw_lab, _ = phone.soil_lab(lin, roi, identity)
        q = phone.quality(img, roi)
        warnings = []
        if corners is not None:
            chart_w = np.linalg.norm(np.subtract(corners[1], corners[0]))
            half = max(2, int(chart_w / 6 * 0.18))
            meas = phone.patch_means(lin, phone.grid_centers(corners), half=half)
            ccm = phone.fit_ccm(meas, kind="rootpoly")
            resid = phone.chart_residual_de(meas, ccm)
            lab, spread = phone.soil_lab(lin, roi, ccm)
            usable = resid <= 3.0 and q["clipped_high"] + q["clipped_low"] <= 0.01
        else:
            resid, ccm = None, identity
            lab, spread = phone.soil_lab(lin, roi, identity)
            usable = False
            warnings.append("No colour card: the camera's colour could not be corrected, so the predicted values "
                            "are less reliable.")
        if req.get("moist_hint", True) and lab[0] < 30:
            warnings.append("The soil looks very dark. Moist soil looks darker than dry soil, and the model was "
                            "trained on dried, sieved samples, so carbon may be over-estimated.")

        # 2 colour brain: predicted properties with 90% ranges
        mu = np.array([self.brain["models"][n].predict(lab[None, :])[0] for n in self.names])
        tf = self.space.tf
        nat = lambda z: tf.to_natural(z[None, :])[0]  # noqa: E731
        pred, lo, hi = nat(mu), nat(mu - 1.645 * self.sd), nat(mu + 1.645 * self.sd)
        pred, lo, hi = np.minimum(pred, 100), np.minimum(lo, 100), np.minimum(hi, 100)   # % cannot exceed 100
        outside = [f"{c} {v:.0f} (training soils {a:.0f} to {b:.0f})"
                   for c, v, a, b in zip(("L*", "a*", "b*"), lab, self.lab_lo, self.lab_hi) if not a <= v <= b]
        if outside:
            warnings.append("This colour is outside the range of the soils the model learned from ("
                            + "; ".join(outside) + "), so the prediction is an extrapolation and not trustworthy.")
        reliable = corners is not None and usable and not outside

        step1 = {"corrected": corners is not None, "reliable": bool(reliable),
                 "chart_residual_dE00": round(resid, 2) if resid is not None else None, "usable": bool(usable),
                 "blur": q["blur_laplacian_var"], "clipped": round(q["clipped_high"] + q["clipped_low"], 4),
                 "raw_lab": [round(float(v), 1) for v in raw_lab], "lab": [round(float(v), 1) for v in lab],
                 "raw_hex": lab_to_hex(raw_lab), "hex": lab_to_hex(lab),
                 "spread": [round(float(v), 1) for v in spread], "warnings": warnings}
        prediction = [{"name": n, "predicted": round(float(pred[k]), 3), "lo": round(float(lo[k]), 3),
                       "hi": round(float(hi[k]), 3)} for k, n in enumerate(self.names)]
        report = req.get("report") or {}
        if not any(report.get(n) not in (None, "") for n in self.names):     # predict-only mode
            return {"step1": step1, "step2": [{**v, "reported": None, "z": None, "status": "no report"}
                                              for v in prediction], "step4": None}

        # 3 report vs prediction
        rep = np.array([float(report[n]) for n in self.names])
        z_rep, _ = self.space.to_latent(rep[None, :])
        zscore = (z_rep[0] - mu) / self.sd
        per_value = []
        for k, n in enumerate(self.names):
            a = abs(zscore[k]) if np.isfinite(zscore[k]) else 99
            per_value.append({"name": n, "reported": rep[k], "predicted": round(float(pred[k]), 3),
                              "lo": round(float(lo[k]), 3), "hi": round(float(hi[k]), 3),
                              "z": round(float(zscore[k]), 2) if np.isfinite(zscore[k]) else None,
                              "status": "consistent" if a < 1.645 else ("unusual" if a < 2.576 else "suspicious")})

        # 4 batch check: this report at position 12 among 11 real reports
        R = np.vstack([self.Y[self.batch_idx], self.space.print_values(rep[None, :])])
        MU = np.vstack([self.Wt[f"{WITNESS}__mu"][self.batch_idx], mu[None, :]])
        colours = [lab_to_hex(l) for l in self.D["lab"][self.batch_idx]] + [lab_to_hex(lab)]
        out = infer_batch(R, MU, self.model, self.cfg)
        rank = np.empty(len(R), int)
        rank[np.argsort(-out["score"])] = np.arange(1, len(R) + 1)
        rows = []
        for j in range(len(R)):
            g, op, y, _ = out["value_op"][j]
            if out["kind"][j] == "swap" and out["partner"][j] >= 0:
                why = f"looks swapped with #{int(out['partner'][j]) + 1}"
            elif g != "none":
                why = describe(op)
                k = int(np.argmax(np.abs(np.asarray(y) - R[j]) > 1e-9))
                if abs(y[k] - R[j][k]) > 1e-9:
                    why += f"; suggest {self.names[k]} = {y[k]:.3g}"
            else:
                why = ""
            rows.append({"pos": j + 1, "yours": j == len(R) - 1, "values": [float(v) for v in R[j]],
                         "score": round(float(out["score"][j]), 3), "rank": int(rank[j]),
                         "why": why if out["score"][j] > 0.15 else "", "colour": colours[j]})
        mine = rows[-1]
        verdict = ("re-test" if mine["rank"] <= 2 and mine["score"] > 0.15 else
                   "check" if mine["score"] > 0.15 else "looks fine")
        if not reliable:
            verdict = "unreliable photo"
        return {"step1": step1, "step2": per_value, "step4": {"rows": rows, "verdict": verdict}}


# ------------------------------------------------------------------ helpers
def lab_to_lin(lab):
    colour = phone._colour()
    white = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]
    return np.clip(colour.XYZ_to_RGB(colour.Lab_to_XYZ(lab, white), "sRGB", apply_cctf_encoding=False), 0, 1)


def lab_to_hex(lab):
    rgb = phone.to_encoded(lab_to_lin(np.asarray(lab, float)))
    return "#" + "".join(f"{int(round(v * 255)):02x}" for v in rgb)


def describe(op):
    kind, _, t = op.partition("@")
    return {"x10": f"{t} looks 10x too high", "/10": f"{t} looks 10x too low",
            "TR": f"digits of {t} look transposed", "G": f"{t} looks off (analytical error)"}.get(
        kind, f"{t.replace('<->', ' and ')} look swapped" if kind == "CS" else op)


def png_b64(arr):
    """Minimal PNG encoder (RGB, 8-bit) so no imaging package is needed."""
    h, w, _ = arr.shape
    raw = b"".join(b"\x00" + arr[y].tobytes() for y in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    return base64.b64encode(png).decode()


# ------------------------------------------------------------------ HTTP
class Handler(BaseHTTPRequestHandler):
    engine = None

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
        elif self.path == "/api/examples":
            self._send(200, self.engine.example_list())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/analyze":
            return self._send(404, {"error": "not found"})
        try:
            req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self._send(200, self.engine.analyze(req))
        except Exception as e:     # show the reason in the page
            self._send(400, {"error": str(e)})

    def log_message(self, fmt, *args):
        pass


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    print("Loading model and data ...", flush=True)
    Handler.engine = Engine()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"EdaphNet live demo running at  http://localhost:{args.port}   (Ctrl+C to stop)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
