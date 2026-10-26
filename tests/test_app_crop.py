import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.crop.suitability import (Field, load_crops, ph_range_scenarios, rank_crops,  # noqa: E402
                                  texture_score, trapezoid)


def test_trapezoid_shape():
    opt, abs_ = [6.0, 7.0], [5.0, 8.0]
    assert trapezoid(6.5, opt, abs_) == 1.0
    assert trapezoid(5.5, opt, abs_) == 0.5
    assert trapezoid(7.5, opt, abs_) == 0.5
    assert trapezoid(4.9, opt, abs_) == 0.0 and trapezoid(8.1, opt, abs_) == 0.0
    assert trapezoid(6.5, [None, None], abs_) is None


def test_texture_score():
    assert texture_score("medium", "heavy, medium", "wide") == 1.0
    assert texture_score("light", "heavy, medium", "medium, light") == 0.5
    assert texture_score("light", "heavy", "heavy") == 0.0
    assert texture_score("light", None, None) is None


def test_all_25_crops_loaded():
    assert len(load_crops()) == 25


def test_wet_warm_field_favours_rice_over_pearl_millet():
    r = {c.name: c for c in rank_crops(Field(ph=6.2, rain_mm=1800, temp_c=27))}
    assert r["Rice"].score == 1.0
    assert r["Pearl millet (bajra)"].score < r["Rice"].score
    assert r["Pearl millet (bajra)"].limiting == "rainfall"


def test_irrigation_removes_rainfall_limit():
    dry = {c.name: c for c in rank_crops(Field(ph=6.5, rain_mm=300, temp_c=25))}
    irr = {c.name: c for c in rank_crops(Field(ph=6.5, rain_mm=300, temp_c=25, irrigated=True))}
    assert irr["Rice"].score > dry["Rice"].score and dry["Rice"].limiting == "rainfall"


def test_multi_soil_averages_and_reports_worst_case():
    sc = ph_range_scenarios(5.0, 8.5, rain_mm=800, temp_c=22)
    r = {c.name: c for c in rank_crops(sc)}
    single = {c.name: c for c in rank_crops(Field(ph=6.5, rain_mm=800, temp_c=22))}
    assert r["Wheat"].worst_score <= r["Wheat"].score <= single["Wheat"].score


def test_local_override_requires_a_source(tmp_path):
    import json
    import pytest
    from app.crop.suitability import KNOWLEDGE
    bad = tmp_path / "local.json"
    bad.write_text(json.dumps({"overrides": [{"name": "Wheat", "values": {"ph_opt": [6.5, 8.0]}}]}))
    with pytest.raises(ValueError):
        load_crops(KNOWLEDGE, bad)
    good = tmp_path / "local2.json"
    good.write_text(json.dumps({"overrides": [{"name": "Wheat", "values": {"ph_opt": [6.5, 8.0]},
                                               "source": "test doc", "page": "p. 1"}]}))
    wheat = next(c for c in load_crops(KNOWLEDGE, good) if c["name"] == "Wheat")
    assert wheat["ph_opt"] == [6.5, 8.0] and "ph_opt" in wheat["overridden"]
