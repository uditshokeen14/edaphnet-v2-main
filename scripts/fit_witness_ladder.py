"""Step 4b-2: fit witness models for every rung of the witness ladder and measure how much
each rung knows about each soil property (the x-axis of the detectability map, TC3).

Rungs:
  W0            no witness (training mean)
  W1_dE{0,2,4,8} CIELAB colour + isotropic Gaussian noise with mean |noise| = dE (CIE76 units),
                 a sweep over phone-capture quality (doc 11 §5; dE76 used instead of dE00, D-011)
  W2            10 visible bands
  W3            full Vis-NIR (10 nm) -> log(1/R) -> PCA(30), PCA fitted on train only

Model per rung and property: LightGBM regression on the latent (transformed, standardised)
property, fixed hyperparameters (no tuning). Residual covariance S from 5-fold group
out-of-fold predictions on train. Outputs are what step 5 needs: latent means for the cal and
test splits, S, and the transform parameters.

    python scripts/fit_witness_ladder.py --tag icraf8
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from edaphnet2.real_data import LatentTransform  # noqa: E402
from edaphnet2.tracking import new_run_dir, provenance, write_json  # noqa: E402

SEED = 20260925
DE_GRID = (0.0, 2.0, 4.0, 8.0)
LGB_PARAMS = dict(n_estimators=300, learning_rate=0.05, num_leaves=15, min_child_samples=20,
                  subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1)


def rungs(D, rng):
    """Witness feature matrices for all samples (split-independent except W3's PCA)."""
    lab, bands, full, split = D["lab"], D["bands"], D["full"], D["split"]
    out = {"W0": None}
    for de in DE_GRID:
        sigma = de / np.sqrt(8 / np.pi)          # E|N(0, s^2 I_3)| = s * sqrt(8/pi)
        out[f"W1_dE{de:g}"] = lab + rng.standard_normal(lab.shape) * sigma
    out["W2"] = bands
    A = np.log(1 / np.clip(full, 1e-4, None))
    tr = split == "train"
    mu = A[tr].mean(axis=0)
    U, s, Vt = np.linalg.svd(A[tr] - mu, full_matrices=False)
    out["W3"] = (A - mu) @ Vt[:30].T
    return out


def fit_predict(Xtr, ytr, Xte, seed):
    import lightgbm as lgb
    return lgb.LGBMRegressor(random_state=seed, **LGB_PARAMS).fit(Xtr, ytr).predict(Xte)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="icraf8")
    args = ap.parse_args()
    D = dict(np.load(ROOT / "data" / "processed" / f"t1_{args.tag}.npz", allow_pickle=True))
    names = [str(n) for n in D["names"]]
    X, split, groups = D["X"], D["split"], D["groups"]
    tr, ca, te = split == "train", split == "cal", split == "test"

    tf = LatentTransform(names).fit(X[tr])
    Z, _ = tf.to_latent(X)
    rng = np.random.default_rng(SEED)
    W = rungs(D, rng)

    from sklearn.model_selection import GroupKFold
    folds = list(GroupKFold(n_splits=5).split(np.zeros(tr.sum()), groups=groups[tr]))

    run = new_run_dir(ROOT / "results" / "runs", f"witness_ladder_{args.tag}", ROOT)
    write_json(run / "config.json", {"tag": args.tag, "seed": SEED, "de_grid": DE_GRID,
                                     "lgb_params": LGB_PARAMS, "pca_components": 30, "folds": 5})
    write_json(run / "provenance.json", provenance(ROOT))
    rows, store = [], {"names": np.array(names), "tf_mu": tf.mu, "tf_sd": tf.sd,
                       "split": split, "groups": groups}
    for rung, F in W.items():
        t0 = time.time()
        Ztr = Z[tr]
        oof = np.zeros_like(Ztr)
        mu_all = np.zeros_like(Z)
        for k in range(len(names)):
            if F is None:
                oof[:, k] = 0.0          # latent is standardised on train: mean 0
                mu_all[:, k] = 0.0
                continue
            Ftr = F[tr]
            for a, b in folds:
                oof[b, k] = fit_predict(Ftr[a], Ztr[a, k], Ftr[b], SEED)
            mu_all[:, k] = fit_predict(Ftr, Ztr[:, k], F, SEED)
        mu_all[tr] = oof                 # train rows get honest out-of-fold means
        E = Ztr - oof
        S = np.cov(E, rowvar=False)
        sd = np.sqrt(np.diag(S))
        store[f"{rung}__mu"] = mu_all
        store[f"{rung}__S"] = S
        if F is not None:
            store[f"{rung}__F"] = F

        Xnat_hat = tf.to_natural(mu_all)
        for k, n in enumerate(names):
            zt, mt = Z[te, k], mu_all[te, k]
            r2_latent = 1 - np.mean((zt - mt) ** 2) / np.var(zt)
            xt, xh = X[te, k], Xnat_hat[te, k]
            rmse_nat = float(np.sqrt(np.mean((xt - xh) ** 2)))
            iqr = np.subtract(*np.percentile(xt, [75, 25]))
            cov90 = float(np.mean(np.abs(zt - mt) <= 1.6449 * sd[k]))
            # split-conformal 90% interval from calibration residuals
            qc = np.quantile(np.abs(Z[ca, k] - mu_all[ca, k]), 0.9 * (1 + 1 / ca.sum()))
            rows.append({"rung": rung, "property": n, "r2_latent_test": float(r2_latent),
                         "r2_latent_oof_train": float(1 - np.mean(E[:, k] ** 2) / np.var(Ztr[:, k])),
                         "rmse_natural_test": rmse_nat, "rpiq_test": float(iqr / rmse_nat),
                         "gauss90_coverage_test": cov90,
                         "conformal90_coverage_test": float(np.mean(np.abs(zt - mt) <= qc))})
        print(f"{rung:9s} done ({time.time() - t0:.0f}s)", flush=True)

    res = pd.DataFrame(rows)
    res.to_csv(run / "witness_ladder_metrics.csv", index=False)
    np.savez_compressed(ROOT / "data" / "processed" / f"witness_{args.tag}.npz", **store)
    write_json(run / "metrics.json", {"evidence_tag": "REAL DATA (ICRAF-ISRIC spectra; colour "
                                      "derived from lab spectra = best-case phone proxy)",
                                      "unit_of_analysis": "sample; profile-grouped splits"})
    pd.set_option("display.width", 200)
    print("\nR2 (latent, test split)\n", res.pivot(index="rung", columns="property",
                                                    values="r2_latent_test").round(2).to_string())
    print("\nConformal 90% coverage (test)\n", res.pivot(index="rung", columns="property",
                                                          values="conformal90_coverage_test").round(2).to_string())
    print("\nGaussian 90% coverage (test)\n", res.pivot(index="rung", columns="property",
                                                         values="gauss90_coverage_test").round(2).to_string())
    print("\nrun:", run)


if __name__ == "__main__":
    main()
