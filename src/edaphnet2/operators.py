"""Corruption library C (doc 11 §2.4).

A value-error hypothesis for a report says which cell(s) were corrupted and how. For
inference we need, for a reported vector r, every candidate "original" vector y = T^-1(r),
with the log-Jacobian log|dy/dr| of the inverse map and the hypothesis' prior mass.

Groups (equal prior mass per group, uniform within group):
  decimal        x10 / /10 on any cell
  unit           property-specific unit confusions
  transposition  adjacent-digit swap of the printed value
  column_swap    two cells interchanged
  gross          multiplicative analytical error, factor log-uniform on [1/3,0.8] U [1.25,3],
                 integrated numerically on a fixed grid
"""
from dataclasses import dataclass

import numpy as np

from .space import ALL_UNIT_OPS, T0

GROUPS = ("decimal", "unit", "transposition", "column_swap", "gross")

# (property, op name, forward factor): reported = factor * true
UNIT_OPS = ALL_UNIT_OPS
DECIMAL_OPS = (("x10", 10.0), ("/10", 0.1))


def gross_grid(n_side=20):
    lo = np.exp(np.linspace(np.log(1 / 3), np.log(0.8), n_side))
    hi = np.exp(np.linspace(np.log(1.25), np.log(3.0), n_side))
    return np.concatenate([lo, hi])


GROSS_GRID = gross_grid()


@dataclass
class HypSet:
    """All value-error hypotheses for one report, as arrays (row 0 is always "none")."""
    y: np.ndarray          # (H, P) candidate original vectors, natural units
    log_jac: np.ndarray    # (H,) log|d y / d r| of the inverse map
    log_prior: np.ndarray  # (H,) normalised log prior
    group: list            # (H,) group name ("none" for row 0)
    op: list               # (H,) operator label


def transpose_candidates(value, decimals):
    """All values obtained by swapping two adjacent, different digits of the printed value.

    Transposition is its own inverse, so this serves both for injection and inference.
    Candidates that would create a leading zero (e.g. "05.3") are excluded.
    """
    s = f"{value:.{decimals}f}"
    out = []
    for a in range(len(s) - 1):
        c1, c2 = s[a], s[a + 1]
        if c1.isdigit() and c2.isdigit() and c1 != c2:
            t = s[:a] + c2 + c1 + s[a + 2:]
            body = t.lstrip("-")
            if len(body) > 1 and body[0] == "0" and body[1].isdigit():
                continue
            out.append(float(t))
    return out


def _scaled(r, cells, factors):
    """Rows of r with r[cell] divided by factor (the inverse of a multiplicative op)."""
    Y = np.repeat(r[None, :], len(cells), axis=0)
    Y[np.arange(len(cells)), cells] = r[cells] / factors
    return Y


def enumerate_hypotheses(r, value_error_rate, groups=GROUPS, space=T0):
    """Enumerate value-error hypotheses for report vector r (natural units).

    Priors: log P(none) = log(1 - eps); the remaining eps is split equally across enabled
    groups that have at least one candidate, then uniformly within a group.
    """
    r = np.asarray(r, float)
    P, NAMES, IDX = space.P, space.names, space.idx
    parts = {}  # group -> (Y, log_jac, ops)

    if "decimal" in groups:
        cells = np.repeat(np.arange(P), len(DECIMAL_OPS))
        f = np.tile([f for _, f in DECIMAL_OPS], P)
        ops = [f"{n}@{NAMES[k]}" for k in range(P) for n, _ in DECIMAL_OPS]
        parts["decimal"] = (_scaled(r, cells, f), -np.log(f), ops)
    if "unit" in groups and space.unit_ops:
        uops = space.unit_ops
        cells = np.array([IDX[p] for p, _, _ in uops])
        f = np.array([f for _, _, f in uops])
        parts["unit"] = (_scaled(r, cells, f), -np.log(f), [f"{n}@{p}" for p, n, _ in uops])
    if "transposition" in groups:
        rows, ops = [], []
        for k, (name, dec) in enumerate(zip(NAMES, space.decimals)):
            for v in transpose_candidates(r[k], dec):
                y = r.copy(); y[k] = v
                rows.append(y); ops.append(f"TR@{name}")
        if rows:
            parts["transposition"] = (np.array(rows), np.zeros(len(rows)), ops)
    if "column_swap" in groups:
        a, b = np.triu_indices(P, 1)
        Y = np.repeat(r[None, :], len(a), axis=0)
        Y[np.arange(len(a)), a] = r[b]
        Y[np.arange(len(a)), b] = r[a]
        parts["column_swap"] = (Y, np.zeros(len(a)),
                                [f"CS@{NAMES[i]}<->{NAMES[j]}" for i, j in zip(a, b)])
    if "gross" in groups:
        cells = np.repeat(np.arange(P), len(GROSS_GRID))
        f = np.tile(GROSS_GRID, P)
        parts["gross"] = (_scaled(r, cells, f), -np.log(f), [f"G@{NAMES[k]}" for k in cells])

    Ys, ljs, lps, grp, ops = [r[None, :]], [np.zeros(1)], [], ["none"], ["none"]
    if parts and value_error_rate > 0:
        lps.append(np.array([np.log1p(-value_error_rate)]))
        lg = np.log(value_error_rate) - np.log(len(parts))
        for g, (Y, lj, o) in parts.items():
            Ys.append(Y); ljs.append(lj)
            lps.append(np.full(len(Y), lg - np.log(len(Y))))
            grp += [g] * len(Y); ops += o
    else:
        lps.append(np.zeros(1))
    return HypSet(np.vstack(Ys), np.concatenate(ljs), np.concatenate(lps), grp, ops)


# ---------------------------------------------------------------- forward (injection)

def apply_random_corruption(y, rng, groups=GROUPS, space=T0):
    """Corrupt one cell (or one pair for column_swap) of a correct report y.

    Returns (r, info) with info = {group, op, cells, factor}.
    Group uniform, then operator uniform within the group.
    """
    y = np.asarray(y, float)
    r = y.copy()
    P, NAMES, IDX = space.P, space.names, space.idx
    groups = tuple(g for g in groups if g != "unit" or space.unit_ops)
    for _ in range(100):
        g = groups[rng.integers(len(groups))]
        if g == "decimal":
            k = rng.integers(P); name, f = DECIMAL_OPS[rng.integers(2)]
            r[k] = y[k] * f
            return r, {"group": g, "op": f"{name}@{NAMES[k]}", "cells": (k,)}
        if g == "unit":
            prop, name, f = space.unit_ops[rng.integers(len(space.unit_ops))]
            k = IDX[prop]; r[k] = y[k] * f
            return r, {"group": g, "op": f"{name}@{prop}", "cells": (k,)}
        if g == "transposition":
            k = rng.integers(P)
            c = transpose_candidates(y[k], space.decimals[k])
            if not c:
                continue
            r[k] = c[rng.integers(len(c))]
            return r, {"group": g, "op": f"TR@{NAMES[k]}", "cells": (k,)}
        if g == "column_swap":
            a, b = sorted(rng.choice(P, 2, replace=False))
            r[a], r[b] = y[b], y[a]
            return r, {"group": g, "op": f"CS@{NAMES[a]}<->{NAMES[b]}", "cells": (int(a), int(b))}
        if g == "gross":
            k = rng.integers(P); f = GROSS_GRID[rng.integers(len(GROSS_GRID))]
            r[k] = y[k] * f
            return r, {"group": g, "op": f"G@{NAMES[k]}", "cells": (k,), "factor": float(f)}
    raise RuntimeError("could not inject a corruption")
