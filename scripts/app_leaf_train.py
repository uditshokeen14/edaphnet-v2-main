"""App Step 3b: train and evaluate the leaf-disease head (docs/24 §5).

Rules fixed before any PlantDoc result was seen:
  - PlantVillage split 80/20 (stratified, seed 20261003) for training / validation;
  - the regularisation C is chosen on PlantVillage validation only, from {0.1, 1.0};
  - temperature scaling fitted on PlantVillage validation;
  - abstention threshold fixed at 0.5 (top calibrated probability) before testing;
  - headline result = PlantDoc (cross-dataset), all 28 mapped classes; PlantVillage validation is
    reported but is known to be optimistic (doc 25 §4).

    "C:\\Program Files\\Python314\\python.exe" scripts/app_leaf_train.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
SEED, THRESHOLD = 20261003, 0.5
OUT = ROOT / "results" / "app_leaf"


def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def nll(z, y_idx, T):
    p = softmax(z / T)
    return -np.mean(np.log(p[np.arange(len(y_idx)), y_idx] + 1e-12))


def evaluate(name, P, y, classes, threshold):
    pred = np.array(classes)[P.argmax(1)]
    conf = P.max(1)
    acc = accuracy_score(y, pred)
    crop = lambda s: np.array([c.split("___")[0] for c in s])  # noqa: E731
    acc_crop = float(np.mean(crop(pred) == crop(y)))
    keep = conf >= threshold
    return {"set": name, "n": int(len(y)), "accuracy": round(float(acc), 4),
            "macro_f1": round(float(f1_score(y, pred, average="macro", labels=sorted(set(y)))), 4),
            "crop_accuracy": round(acc_crop, 4),
            "coverage_at_threshold": round(float(keep.mean()), 4),
            "accuracy_when_confident": round(float(np.mean(pred[keep] == y[keep])), 4) if keep.any() else None,
            "accuracy_when_not_sure": round(float(np.mean(pred[~keep] == y[~keep])), 4) if (~keep).any() else None}


def main():
    d = np.load(ROOT / "data" / "app_raw" / "leaf_features.npz", allow_pickle=True)
    X, y = d["pv_X"], d["pv_y"].astype(str)
    Xtr, Xva, ytr, yva = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    best = None
    for C in (0.1, 1.0):
        clf = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=3000, class_weight="balanced"))
        clf.fit(Xtr, ytr)
        a = accuracy_score(yva, clf.predict(Xva))
        print(f"C={C}: PlantVillage validation accuracy {a:.4f}", flush=True)
        if best is None or a > best[0]:
            best = (a, C, clf)
    _, C, clf = best
    classes = list(clf.classes_)
    idx = {c: i for i, c in enumerate(classes)}
    zva = clf.decision_function(Xva)
    T = float(minimize_scalar(lambda lt: nll(zva, np.array([idx[c] for c in yva]), np.exp(lt)),
                              bounds=(-3, 3), method="bounded").x)
    T = float(np.exp(T))
    res = [evaluate("PlantVillage validation (optimistic)", softmax(zva / T), yva, classes, THRESHOLD)]
    Xpd, ypd = d["pd_X"], d["pd_y"].astype(str)
    Ppd = softmax(clf.decision_function(Xpd) / T)
    res.append(evaluate("PlantDoc cross-dataset (headline)", Ppd, ypd, classes, THRESHOLD))
    pepper = d["pd_orig_class"].astype(str) != "Bell_pepper leaf spot"
    res.append(evaluate("PlantDoc without the assumed pepper mapping", Ppd[pepper], ypd[pepper], classes, THRESHOLD))

    # coverage-accuracy curve on PlantDoc (for the report; the threshold is NOT re-chosen from it)
    conf, ok = Ppd.max(1), (np.array(classes)[Ppd.argmax(1)] == ypd)
    curve = [{"threshold": t, "coverage": round(float((conf >= t).mean()), 3),
              "accuracy": round(float(ok[conf >= t].mean()), 3) if (conf >= t).any() else None}
             for t in (0.0, 0.3, 0.5, 0.7, 0.9)]
    per_class = (pd.DataFrame({"true": ypd, "ok": ok}).groupby("true")["ok"].agg(["mean", "size"])
                 .rename(columns={"mean": "recall", "size": "n"}).sort_values("recall"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metrics.json").write_text(json.dumps({"C": C, "temperature": round(T, 3), "threshold": THRESHOLD,
                                                  "results": res, "plantdoc_coverage_curve": curve}, indent=1))
    per_class.to_csv(OUT / "plantdoc_per_class_recall.csv")
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump({"classes": classes, "clf": clf, "temperature": T, "threshold": THRESHOLD,
                 "meta": {"C": C, "seed": SEED, "backbone": "mobilenet_v3_large IMAGENET1K_V2",
                          "trained_on": "PlantVillage colour, dedup, <=600/class, 80% split"}},
                ROOT / "models" / "leaf_head.joblib")
    print(json.dumps(res, indent=1))
    print("coverage curve (PlantDoc):", curve)
    print("lowest per-class recall on PlantDoc:\n", per_class.head(8).round(3).to_string())


if __name__ == "__main__":
    main()
