# Amendment v3 — DRAFT (not registered)

**Date:** 2026-10-02 · **Status:** DRAFT. To be finalised after the KSSL verdict (doc 18) and
supervisor review, and **registered by commit before any LUCAS or step-6 evaluation**.
**Motivation:** doc 19 (exploratory): the joint model is strong on swaps and weak on single
wrong values; simple checks are better on decimal/column-swap errors.

## 1. Combined re-test policy (candidate method)

Two pre-specified variants. The choice between them is made on the **dev split only**, never on
the test data:

| Variant | Rule |
|---|---|
| **P1 rank fusion** | reciprocal-rank fusion of (a) Full's swap posterior P(report moved) and (b) a value-error score; score = 1/(60 + rank_a) + 1/(60 + rank_b) |
| **P2 budget split** | half of the re-test budget goes to the top swap posteriors, half to the top value-error scores (duplicates passed to the next in line) |

Value-error score: the best of {B2 lab-only density, B7 cleanlab} **on the dev split**, plus a
heavy-tailed variant of B2 (Student-t marginals instead of Gaussian) as a third candidate.

Code needed (after the KSSL run ends): save Full's `p_moved` and `p_value_err` per report; implement
P1 and P2; Student-t B2.

## 2. Hypotheses (draft)

| ID | Hypothesis | Pass rule (draft) |
|---|---|---|
| C1 | Combined policy beats both Full and the best single baseline in recall at 5% budget | ≥ +0.03 over the better of the two, CI > 0, colour witness (W1 ΔE0, ΔE2), random batches |
| C2 | It keeps Full's swap advantage | swap recall ≥ Full's − 0.02 |
| C3 | It removes Full's value-error deficit | value recall ≥ best baseline's − 0.02 |

## 3. LUCAS confirmation (rules fixed before access)

- Property set: the largest set with ≥ 90% completeness among {pH, OC, N, P, K, CaCO₃, EC, clay,
  silt, sand}, decided by an audit script **before** fitting any model; recorded as an amendment.
- Split: by LUCAS point ID, 50 / 15 / 35, seed 20261101.
- Same witness ladder; same settings as doc 18 §7; A1–A4 re-tested as **confirmation**; C1–C3
  tested for the first time.
- Calibration: one score per distinct sample (doc 18, Amendment 1).

## 4. Open questions for supervisor review

1. Is a 5% re-test budget realistic for Indian soil-testing labs, or should the budget be 2% / 10%?
2. Which value-error baseline should be the reference for C3?
3. Should step-6 real-photo data be the primary test of C1 instead of LUCAS?
