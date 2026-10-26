import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

KB = json.loads((ROOT / "app" / "knowledge" / "diseases.json").read_text(encoding="utf-8"))


def test_every_disease_class_has_sourced_info():
    cmap = json.loads((ROOT / "app" / "leaf" / "class_map.json").read_text(encoding="utf-8"))["map"]
    pv_disease = {c for c in cmap.values() if not c.endswith("healthy")}
    assert pv_disease <= set(KB["diseases"])                       # every class the app can show
    for k, v in KB["diseases"].items():
        assert v["source"] in KB["sources"] and KB["sources"][v["source"]].startswith("https://"), k
        assert v["manage"] and v["cause"] and v["name"], k
        assert not k.endswith("healthy")


def test_no_doses_in_advice():
    import re
    text = json.dumps(KB["diseases"])
    assert not re.search(r"\d+\s*(g|ml|kg|l)\s*/", text, flags=re.I)   # products and doses are left to officers


def test_crops_endpoint_single_ph_and_range():
    from app.server import crops
    one = crops({"ph": "6.5", "rain_mm": "1800", "temp_c": "27"})
    assert one["mode"] == "single pH" and len(one["crops"]) == 25
    assert {c["name"]: c for c in one["crops"]}["Rice"]["score"] == 1.0
    rng = crops({"ph": "", "rain_mm": 800, "temp_c": 22, "irrigated": True})
    assert rng["mode"].startswith("pH unknown")
    assert all(c["worst_score"] <= c["score"] for c in rng["crops"])
    assert all("rainfall" not in c["factors"] for c in rng["crops"])   # irrigated: rainfall not a factor


def test_decode_image_reads_a_data_url():
    import base64
    import io
    from PIL import Image
    from app.server import decode_image
    buf = io.BytesIO()
    Image.new("RGB", (40, 20), (120, 80, 40)).save(buf, "JPEG")
    im = decode_image("data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode())
    assert im.size == (40, 20) and im.mode == "RGB"
