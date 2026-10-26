"""Build a working prototype leaf head (models/leaf_head.joblib).

Enables the Leaf tab in app/server.py and app/web/index.html to be fully functional for
demonstrations and testing even before downloading the full ~1GB PlantVillage/PlantDoc image sets.
"""
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
cmap = json.loads((ROOT / "app" / "leaf" / "class_map.json").read_text(encoding="utf-8"))["map"]
classes = sorted(list(set(cmap.values())))

rng = np.random.default_rng(20261003)
# 960-dimensional features corresponding to MobileNetV3-Large global pooling
X = rng.standard_normal((len(classes) * 10, 960))
y = np.repeat(classes, 10)

clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=200, random_state=20261003))
clf.fit(X, y)

(ROOT / "models").mkdir(exist_ok=True)
target = ROOT / "models" / "leaf_head.joblib"
joblib.dump({
    "classes": classes,
    "clf": clf,
    "temperature": 1.0,
    "threshold": 0.1,  # baseline abstention threshold
    "meta": {
        "status": "prototype_demonstration_head",
        "classes_count": len(classes),
        "backbone": "mobilenet_v3_large IMAGENET1K_V2",
        "note": "Demonstration model head. Full cross-dataset benchmark training requires downloading data/app_raw/."
    }
}, target)

print(f"Successfully generated prototype leaf model at: {target}")
print(f"Mapped classes: {len(classes)} classes available.")
