# N1 learned evaluation (100K): report

Preregistration: `DESIGN_N1.md`, committed as `3cc9e9b` before any N1 label was
read. RC-J runtime files unchanged; every N1 engine is a scratch copy. No
arena, no upload, no push, `START_FRACTION` 0.45.

## Data and labels

| | |
|---|---|
| pool | 100,000 positions, 25,823 games, SHA-256 `f016e26a…9560`; leakage (UUID, position, start family, move sequence, cross-split groups) zero |
| near-duplicate rule | 241 validation/test positions one piece displacement from a train position dropped (226 at ply <= 30) |
| splits | train 79,673 / validation 9,870 / test 10,216 (sealed until the freeze) |
| train labels | Stockfish 18 at 50k nodes, 79,673 positions in 973 s (81.9 positions/s, 10 workers) |
| validation labels | 1M nodes |
| test labels | 1M nodes, after the freeze |
| validation labelling | 9,870 positions at 1M nodes in 28.8 min (5.7 positions/s) |
| noise subset (300 validation, report only) | 1M against 4M: mean \|dE\| 0.0125 (median 0.001), 7.3% of positions differ by >= 0.05, WDL-category agreement 98.0%, best-move agreement 85.0%, balanced-band membership agreement 97.7%. 50k against 1M: band agreement 93.0%, signed shift 50k→1M −0.0013 overall and −0.0033 in the band (below the 0.01 caveat threshold) |

## Engine plumbing (before training; random weights)

| check | result |
|---|---|
| zero-weight control, depth 10, 24 openings | 16,818,635 nodes and moves identical to RC-J |
| random-walk accumulator test | 18,950 transitions, 10,018 evaluations, 0 failures (captures 4,603; castles 131 across all four kinds; en passant 42; promotions 144 across all four pieces, 13 capturing; king moves 3,428; null moves 983; unmakes 2,798; multi-ply catch-ups 3,505) |
| shadow-verify in real search | 0 mismatches over 9.66M evaluations (depth 10), 3.59M (1,000 ms), 2.02M (80-ply self-play without `new_game`) |
| root seeding | rebuilds = root searches exactly (246, 224, 500); 1.05 catch-up steps per evaluation |

## Calibration, training and selection (validation only; test and holdout sealed)

* **Frozen phase link** (E0, train ∩ quiet, 50k labels): K_mg 209.4, K_eg
  96.0. The E0 × 1.5 control reproduces E0's validation BCE exactly (0.581389).
* **Shrinkage control:** s* = 0.5, the smallest scale in the grid. On
  near-balanced positions, halving E0 already brings the band E-MSE down from
  0.0178 to 0.0068.
* **Training:** train ∩ quiet 60,958 positions; validation ∩ quiet 7,583
  (3,527 in the band). U and B both early-stopped at epoch 14 (21 epochs run).

| validation, quiet, link (a) | E0 | U | B |
|---|---|---|---|
| BCE | 0.5814 | 0.5692 (−2.1%) | 0.5693 (−2.1%) |
| band E-MSE | 0.0178 | 0.0239 | 0.0195 |
| band E-MSE, shrink control E0·0.5 | 0.0068 | | |
| band BCE change | | +2.0% | +0.1% |
| 0.10-0.30 band BCE change | | −0.2% | −1.0% |
| band Spearman with Stockfish cp | 0.242 | 0.317 | 0.315 |
| band magnitude ratio (median \|N1\| / median \|E0\|) | 1.00 | 1.42 | 1.17 |
| quiescence-resolved pair accuracy (1,820 pairs) | 80.05% | 78.6% | 80.2% |
| eligible (section 7) | | no | no |

**Neither run is eligible: VALIDATION FAIL.** By the frozen rule U is frozen
and the stage continues. Both networks rank near-balanced positions better
than E0 (Spearman +0.07) but inflate the evaluation there (U by 42%), so their
calibrated band error is worse than E0's. It is far worse than the shrink
control's, which shows how much of the band error is magnitude, not order.

**N1q acceptance (validation): PASS.**
* band E-MSE 0.35% from float;
* maximum |cp| difference from float 9.3 (mean 2.1);
* quiescence pair agreement with float 99.45%;
* no clipped parameter (W1 0, W2 0).

Weights SHA-256 `b1b809b79d84238ef292096334d598d2a6327e96df690ade182dcf4e871da201`.

## Frozen-weight engine checks: PASS

| check | result |
|---|---|
| zero-weight control (depth 10, 24 openings) | 16,818,635 nodes and moves identical to RC-J |
| random-walk accumulator test, frozen weights | 18,950 transitions, 10,018 evaluations, 0 failures (captures 4,603; castles 131 in all four kinds; en passant 42; promotions 144 in all four pieces; king moves 3,428; null moves 983; unmakes 2,798) |
| shadow-verify inside real search | 0 mismatches at depth 10, at 1,000 ms and over 80 plies of self-play without `new_game`; depth-10 nodes identical to RC-J; rebuilds = root searches |

## Magnitude audit: FAIL (MAGNITUDE-INCOMPATIBLE)

| criterion | result | verdict |
|---|---|---|
| A: p99 \|f\| at sampled call sites, per phase band (14,201 samples from 58.2M evaluate calls) | 245.2 / **252.6** / 236.0 cp (phase >= 16 / 8-15 / < 8); mean f +27.3 / +20.6 / +1.3 cp | **fail** (limit 250) |
| B: mean f on the validation balanced band | +9.99 cp | pass (limit 10) |
| C: slope of N1q on E0 per phase band | 1.011 / 1.029 / 1.020 | pass |
| D: N1q's own phase link against the frozen link | K_mg 150.5 against 209.4 (**−28%**); K_eg 95.5 against 96.0 (−0.5%) | **fail** (limit ±10%) |
| E: analytic range of f; clipped W1 | f in [−109, +374] cp; 0 clipped | pass |
| F: bare-king mates (10 KQK + 10 KRK, self-play at 200 ms) | RC-J 20/20; N1 **17/20**, and slower where it mates (47 plies against 11, 73 against 23) | **fail** |

At the call sites, 64% of corrections exceed the 30 cp aspiration window, 11.8%
exceed the 120 cp reverse-futility margin, and 3.0% exceed 200 cp. The
network's middlegame evaluation is about 40% hotter than the frozen link, the
same inflation validation showed on the balanced band (magnitude ratio 1.42).
In bare-king endings, where it was never trained, the correction drowns the
mop-up gradient.

**By the frozen rules this verdict is REJECTED.** The search replay (§11) is
not run, and f is not rescaled, clamped or otherwise rescued. The static test
record, the speed measurement and the descriptive holdout are still produced.

Disclosed deviation: the call-site sampling stride was changed from 64 to
4,096 before the test opened. At 64 the fixed 20,000-row buffer filled inside
the first few openings and held no endgame call site, and the first audit run
crashed on that empty band. The criteria are unchanged.

RESULTS_TBD
