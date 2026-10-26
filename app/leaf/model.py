"""Leaf disease model (docs/24 §5): frozen ImageNet MobileNetV3-Large features + a logistic-regression
head, temperature-scaled, with a "not sure" answer below a confidence threshold.

Needs torch, torchvision and Pillow (the main Python install). The first use downloads the
torchvision ImageNet weights (~21 MB) into the torch cache.
"""
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "leaf_head.joblib"
_BACKBONE = None


def backbone():
    """MobileNetV3-Large up to global pooling -> 960-d feature vector. Loaded once."""
    global _BACKBONE
    if _BACKBONE is None:
        import torch
        from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large
        w = MobileNet_V3_Large_Weights.IMAGENET1K_V2
        net = mobilenet_v3_large(weights=w).eval()
        torch.set_num_threads(max(1, (torch.get_num_threads() or 2)))
        _BACKBONE = (net, w.transforms())
    return _BACKBONE


def features_from_pil(images):
    """List of PIL images -> (n, 960) float32 features."""
    import torch
    net, tf = backbone()
    with torch.no_grad():
        x = torch.stack([tf(im.convert("RGB")) for im in images])
        f = net.avgpool(net.features(x)).flatten(1)
    return f.numpy().astype(np.float32)


def features_from_paths(paths, batch=16):
    from PIL import Image
    out = []
    for i in range(0, len(paths), batch):
        ims = []
        for p in paths[i:i + batch]:
            with Image.open(p) as im:
                ims.append(im.convert("RGB").copy())
        out.append(features_from_pil(ims))
    return np.vstack(out) if out else np.zeros((0, 960), np.float32)


def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


class LeafModel:
    """Loaded head: classes, logistic-regression weights, temperature, abstention threshold."""

    def __init__(self, path=MODEL_PATH):
        import joblib
        b = joblib.load(path)
        self.classes, self.clf, self.T, self.threshold = b["classes"], b["clf"], b["temperature"], b["threshold"]
        self.meta = b.get("meta", {})

    def proba(self, feats):
        return softmax(self.clf.decision_function(feats) / self.T)

    def predict_pil(self, image, top=3):
        p = self.proba(features_from_pil([image]))[0]
        order = np.argsort(-p)[:top]
        best = float(p[order[0]])
        return {"top": [{"class": self.classes[i], "crop": self.classes[i].split("___")[0].replace("_", " "),
                         "condition": self.classes[i].split("___")[-1].replace("_", " ").strip(),
                         "probability": round(float(p[i]), 3)} for i in order],
                "confident": best >= self.threshold, "threshold": self.threshold}
