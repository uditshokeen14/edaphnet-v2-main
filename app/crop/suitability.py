"""Crop suitability from soil + climate using FAO EcoCrop ranges (docs/24 §4).

Per factor (pH, rainfall, temperature, texture) a score in [0, 1]:
  1 inside the optimal range, linear fall to 0 at the absolute limits, 0 outside them.
Crop score = minimum over factors (Liebig's law of the minimum); the factor giving the minimum is
reported as the limiting factor. Factors without EcoCrop data are skipped and reported as "no data".

"Multi-soil": the soil may be uncertain (a pH range, or several possible soils with weights). The
score is the weighted mean over those scenarios, and the worst scenario is reported too.
No machine learning and no numbers that are not in app/knowledge/crops.json.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

KNOWLEDGE = Path(__file__).resolve().parents[1] / "knowledge" / "crops.json"
TEXTURES = ("light", "medium", "heavy")


LOCAL = KNOWLEDGE.with_name("crops_local.json")


def load_crops(path=KNOWLEDGE, local=LOCAL):
    """EcoCrop ranges, optionally overridden by sourced Indian values in crops_local.json.

    An override is applied only if it names its source (`source` and `page`); otherwise it is
    rejected, so no unsourced number can reach the app. Each crop records which fields were
    overridden (`overridden`)."""
    crops = json.loads(Path(path).read_text(encoding="utf-8"))["crops"]
    if Path(local).exists():
        over = json.loads(Path(local).read_text(encoding="utf-8")).get("overrides", [])
        by_name = {c["name"]: c for c in crops}
        for o in over:
            if not (o.get("source") and o.get("page")):
                raise ValueError(f"override for {o.get('name')} has no source/page; refusing to use it")
            c = by_name[o["name"]]
            for k, v in o["values"].items():
                c[k] = v
                c.setdefault("overridden", {})[k] = f"{o['source']}, {o['page']}"
    return crops


def trapezoid(x, opt, abs_):
    """Score of value x for optimal range opt=[a, b] and absolute range abs_=[lo, hi]."""
    a, b = opt
    lo, hi = abs_
    if None in (a, b):
        return None
    lo = a if lo is None else lo
    hi = b if hi is None else hi
    if a <= x <= b:
        return 1.0
    if x < a:
        return 0.0 if x <= lo or a == lo else (x - lo) / (a - lo)
    return 0.0 if x >= hi or b == hi else (hi - x) / (hi - b)


def texture_score(texture, opt, abs_):
    """1 if the field's texture class is listed as optimal (or 'wide'), 0.5 if only in the absolute
    list, 0 otherwise. None if EcoCrop gives no texture information."""
    if opt is None and abs_ is None:
        return None
    norm = lambda s: {w.strip() for w in (s or "").lower().replace(";", ",").split(",") if w.strip()}  # noqa: E731
    o, a = norm(opt), norm(abs_)
    if "wide" in o or texture in o:
        return 1.0
    if "wide" in a or texture in a:
        return 0.5
    return 0.0


@dataclass
class Field:
    """One soil/climate scenario. ph and texture describe the soil; climate is per site."""
    ph: float
    rain_mm: float
    temp_c: float
    texture: Optional[str] = None          # 'light' | 'medium' | 'heavy' | None (unknown)
    irrigated: bool = False
    weight: float = 1.0
    label: str = ""


@dataclass
class CropResult:
    name: str
    score: float
    worst_score: float
    limiting: str
    factors: dict = field(default_factory=dict)
    no_data: list = field(default_factory=list)


def score_crop(crop, f):
    factors, no_data = {}, []
    s = trapezoid(f.ph, crop["ph_opt"], crop["ph_abs"])
    factors["pH"] = s
    if not f.irrigated:
        factors["rainfall"] = trapezoid(f.rain_mm, crop["rain_opt"], crop["rain_abs"])
    factors["temperature"] = trapezoid(f.temp_c, crop["temp_opt"], crop["temp_abs"])
    if f.texture:
        factors["texture"] = texture_score(f.texture, crop.get("texture_opt"), crop.get("texture_abs"))
    for k in [k for k, v in factors.items() if v is None]:
        no_data.append(k)
        del factors[k]
    if not factors:
        return 0.0, "no data", {}, no_data
    limiting = min(factors, key=lambda k: factors[k])
    return factors[limiting], limiting, factors, no_data


def rank_crops(scenarios, crops=None):
    """Rank crops over one or more weighted soil/climate scenarios ("multi-soil")."""
    crops = crops or load_crops()
    if isinstance(scenarios, Field):
        scenarios = [scenarios]
    wsum = sum(s.weight for s in scenarios)
    out = []
    for c in crops:
        per = [score_crop(c, s) for s in scenarios]
        mean = sum(p[0] * s.weight for p, s in zip(per, scenarios)) / wsum
        worst_i = min(range(len(per)), key=lambda i: per[i][0])
        score, limiting, factors, no_data = per[worst_i]
        out.append(CropResult(c["name"], round(mean, 3), round(score, 3),
                              limiting if score < 1 else "none", {k: round(v, 3) for k, v in factors.items()},
                              no_data))
    return sorted(out, key=lambda r: (-r.score, -r.worst_score, r.name))


def ph_range_scenarios(ph_lo, ph_hi, rain_mm, temp_c, texture=None, irrigated=False, n=5):
    """A pH known only as a range (e.g. from a soil-type description) -> n equally weighted scenarios."""
    step = (ph_hi - ph_lo) / (n - 1) if n > 1 else 0
    return [Field(ph_lo + i * step, rain_mm, temp_c, texture, irrigated, 1.0, f"pH {ph_lo + i * step:.1f}")
            for i in range(n)]
