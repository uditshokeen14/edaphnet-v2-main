"""Property space: everything the method needs to know about a set of soil properties.

T0Space wraps the synthetic properties (properties.py); RealSpace wraps a fitted
LatentTransform for a real property set. Operators, inference and baselines take a space,
so the same code runs on synthetic and real data.
"""
import numpy as np

# reporting precision for real properties (decimals as printed on typical soil reports)
REAL_DECIMALS = {"pH": 1, "OC": 2, "N": 3, "clay": 1, "sand": 1, "CEC": 1, "K": 2, "Ca": 1, "Mg": 1,
                 "Ctot": 2, "CaCO3": 1}

# unit confusions (property, label, factor: reported = factor * true); only those whose
# property is present in the space are used (doc 11 §2.4)
ALL_UNIT_OPS = (
    ("P", "P->P2O5", 2.29), ("P", "P2O5->P", 1 / 2.29),
    ("K", "K->K2O", 1.205), ("K", "K2O->K", 1 / 1.205),
    ("K", "cmol->mg/kg", 391.0), ("K", "mg/kg->cmol", 1 / 391.0),
    ("P", "mg/kg->kg/ha", 2.24), ("P", "kg/ha->mg/kg", 1 / 2.24),
)


class Space:
    names: tuple
    decimals: tuple
    positive: np.ndarray   # bool per property: value must be > 0

    @property
    def P(self):
        return len(self.names)

    @property
    def idx(self):
        return {n: i for i, n in enumerate(self.names)}

    @property
    def unit_ops(self):
        return tuple(op for op in ALL_UNIT_OPS if op[0] in self.names)

    def to_latent(self, X):
        raise NotImplementedError

    def print_values(self, X):
        """Round to reporting precision; positive properties never print as 0."""
        X = np.array(X, float)
        for k, d in enumerate(self.decimals):
            X[..., k] = np.round(X[..., k], d)
            if self.positive[k]:
                X[..., k] = np.maximum(X[..., k], 10.0 ** -d)
        return X


class T0Space(Space):
    def __init__(self):
        from . import properties as pr
        self._pr = pr
        self.names = pr.NAMES
        self.decimals = tuple(p.decimals for p in pr.PROPS)
        self.positive = np.array([p.kind == "lognormal" for p in pr.PROPS])

    def to_latent(self, X):
        return self._pr.to_latent(X)


class RealSpace(Space):
    def __init__(self, transform):
        self.tf = transform
        self.names = transform.names
        self.decimals = tuple(REAL_DECIMALS[n] for n in self.names)
        self.positive = np.array([k != "identity" for k in transform.kinds])

    def to_latent(self, X):
        X = np.asarray(X, float)
        shp = X.shape
        Z, LJ = self.tf.to_latent(X.reshape(-1, shp[-1]))
        return Z.reshape(shp), LJ.reshape(shp)


T0 = T0Space()
