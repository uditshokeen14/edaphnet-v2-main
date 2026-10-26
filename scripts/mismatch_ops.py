"""Exploratory: value errors that are NOT in the method's corruption library (doc 11 ablation 10,
"library mismatch"). Used only by configs/real_kssl3_mismatch.yaml; the registered runs use the
library operators in src/edaphnet2/operators.py.

  x100       a value multiplied or divided by 100 (two decimal places slipped)
  gross_big  a multiplicative analytical error of x4-8 or /4-8 (outside the library's 1/3-3 grid)
  neighbour  a value copied from the neighbouring report in the tray (copy-paste slip)
  dropdigit  one non-leading digit deleted from the printed value
"""
import numpy as np

KINDS = ("x100", "gross_big", "neighbour", "dropdigit")


def drop_digit(value, decimals, rng):
    s = f"{value:.{decimals}f}"
    pos = [i for i, ch in enumerate(s) if ch.isdigit()]
    pos = [i for i in pos if not (i == 0 and len(pos) > 1 and s[0] != "0")] or pos   # keep the leading digit
    for _ in range(10):
        i = int(rng.choice(pos))
        t = s[:i] + s[i + 1:]
        changed = t not in ("", ".") and not t.endswith(".") and float(t.strip(".") or 0) > 0
        if changed and not np.isclose(float(t), value):
            return float(t)
    return None


def apply(r_batch, j, rng, space):
    """Corrupt one cell of report j in a batch (array of printed reports). Returns (new_row, info)."""
    row = r_batch[j].copy()
    n, P = r_batch.shape
    for _ in range(50):
        kind = KINDS[rng.integers(len(KINDS))]
        k = int(rng.integers(P))
        name = space.names[k]
        if kind == "x100":
            f = 100.0 if rng.random() < 0.5 else 0.01
            row[k] = row[k] * f
        elif kind == "gross_big":
            f = rng.uniform(4, 8)
            row[k] = row[k] * (f if rng.random() < 0.5 else 1 / f)
        elif kind == "neighbour":
            nb = j + 1 if j + 1 < n else j - 1
            if nb < 0 or np.isclose(r_batch[nb, k], row[k]):
                continue
            row[k] = r_batch[nb, k]
        else:
            v = drop_digit(row[k], space.decimals[k], rng)
            if v is None:
                continue
            row[k] = v
        return row, {"group": f"mm_{kind}", "op": f"{kind}@{name}", "cells": (k,)}
    raise RuntimeError("could not inject a mismatch error")
