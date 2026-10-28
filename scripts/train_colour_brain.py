"""Step 6 "brain": colour (CIELAB) -> soil properties, trained on large spectral libraries, ready to
apply to phone colours from scripts/process_photos.py.

For each dataset tag (icraf8, kssl3): LightGBM per property on the latent (transformed) scale,
trained on the TRAIN split only. The training colour gets phone-like noise (isotropic CIELAB
noise with mean |dE| = 2, fixed now) so the model does not rely on colour precision a phone
cannot deliver. Evaluated on the TEST split with and without the noise.

Saves models/colour_brain_<tag>.joblib (git-ignored; rebuild with this script).

    python scripts/train_colour_brain.py --tags icraf8 kssl3
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from edaphnet2.real_data import LatentTransform  # noqa: E402

TRAIN_DE, SEED = 2.0, 20261002
PARAMS = dict(n_estimators=300, learning_rate=0.05, num_leaves=15, min_child_samples=20,
              subsample=0.8, subsample_freq=1, colsample_bytree=1.0, verbose=-1)


def noisy(lab, de, rng):
    return lab + rng.standard_normal(lab.shape) * de / np.sqrt(8 / np.pi) if de > 0 else lab


def main():
    import joblib
    import lightgbm as lgb
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="+", default=["icraf8", "kssl3"])
    args = ap.parse_args()
    (ROOT / "models").mkdir(exist_ok=True)
    report = {}
    for tag in args.tags:
        D = np.load(ROOT / "data" / "processed" / f"t1_{tag}.npz", allow_pickle=True)
        names = [str(n) for n in D["names"]]
        X, lab, split = D["X"], D["lab"], D["split"]
        tr, te = split == "train", split == "test"
        tf = LatentTransform(names).fit(X[tr])
        Z, _ = tf.to_latent(X)
        rng = np.random.default_rng(SEED)
        Ltr = noisy(lab[tr], TRAIN_DE, rng)
        models, res = {}, {}
        for k, n in enumerate(names):
            m = lgb.LGBMRegressor(random_state=SEED, **PARAMS).fit(Ltr, Z[tr, k])
            models[n] = m
            res[n] = {}
            for de in (0.0, 2.0, 4.0):
                pred = m.predict(noisy(lab[te], de, rng))
                res[n][f"r2_test_dE{de:g}"] = float(1 - np.mean((Z[te, k] - pred) ** 2) / np.var(Z[te, k]))
        meta = {"models": models, "names": names, "tf_mu": tf.mu, "tf_sd": tf.sd,
                "kinds": tf.kinds, "train_dE": TRAIN_DE, "seed": SEED,
                "features": ["L*", "a*", "b*"], "source": f"t1_{tag} train split"}
        wt_path = ROOT / "data" / "processed" / f"witness_{tag}.npz"
        if wt_path.exists():
            Wt = np.load(wt_path, allow_pickle=True)
            if "W1_dE2__S" in Wt:
                meta["S"] = Wt["W1_dE2__S"]
            lab_tr = lab[tr]
            meta["lab_lo"] = np.percentile(lab_tr, 0.5, axis=0)
            meta["lab_hi"] = np.percentile(lab_tr, 99.5, axis=0)
            test_idx = np.where(te)[0]
            rng_demo = np.random.default_rng(2026)
            b_idx = rng_demo.choice(test_idx, min(11, len(test_idx)), replace=False)
            order = test_idx[np.argsort(lab[test_idx, 0])]
            ex_idx = [int(order[int(q * (len(order) - 1))]) for q in (0.04, 0.2, 0.4, 0.6, 0.8, 0.96)]
            from edaphnet2.space import RealSpace
            sp = RealSpace(tf)
            Y_all = sp.print_values(X)
            meta["batch_Y"] = Y_all[b_idx]
            meta["batch_mu"] = Wt["W1_dE2__mu"][b_idx] if "W1_dE2__mu" in Wt else None
            meta["batch_lab"] = lab[b_idx]
            meta["examples_Y"] = Y_all[ex_idx]
            meta["examples_lab"] = lab[ex_idx]
        joblib.dump(meta, ROOT / "models" / f"colour_brain_{tag}.joblib")
        report[tag] = res
        print(tag, json.dumps({n: {k: round(v, 3) for k, v in r.items()} for n, r in res.items()}, indent=1))
    (ROOT / "results" / "colour_brain_report.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
