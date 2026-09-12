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

## Test gates: FAIL

Opened once, 2026-09-11 23:50, after the freeze manifest. Test split 10,216
positions (7,792 quiet, 3,640 in the band, 2,387 groups); 4,995 pair roots and
12,524 root-restricted 1M-node searches giving 7,590 test pairs.

| gate | result | verdict |
|---|---|---|
| **G1** aggregate BCE, link (a) | **−1.62%** [−2.24, −0.97] | **pass** |
| G1 under the richer link (b) | −1.77% [−2.42, −1.14] | pass |
| **G2 (i)** band E-MSE difference, link (a) | **+0.0061** [+0.0054, +0.0069] (worse) | **fail** |
| G2 (i) under link (b) | +0.0042 [+0.0035, +0.0050] (worse) | fail |
| G2 (ii) against the shrinkage control E0·0.5 | +0.0170 [+0.0156, +0.0189] (worse) | fail |
| G2 (iii) within-band Spearman with Stockfish cp | **+0.0526** [+0.0275, +0.0804] (better) | pass |
| G2 (iv) band magnitude ratio | **1.40** | fail (limit 1.25) |
| G2 (v) band BCE / 0.10-0.30 band BCE | **+2.13%** / −0.87% | fail / pass |
| **G3 (i)** quiescence-resolved pair accuracy | E0 79.57% → N1q **79.47%**, difference −0.09 points [−0.94, +0.76] | **fail**, not underpowered |
| G3 (ii) balanced-root pairs (3,091) | +0.13 points [−1.27, +1.41] | pass (non-inferiority) |
| G3 (iii) quiescence-resolved root score, band E-MSE | +0.0061 [+0.0054, +0.0070] (worse) | fail |
| **G4** non-quiet positions (2,424) | −3.70% | **pass** |

Band E-MSE: E0 0.01771, N1q 0.02384, shrink control 0.00681.

**Static label: FAIL.** N1 is a better *ranker* of near-balanced positions
(Spearman +0.05) and a better aggregate predictor (−1.6%), while being a worse
*calibrated* judge of exactly the positions the stage was built to improve,
because it inflates the evaluation there by 40%. After RC-J's own quiescence
resolution the ranking gain disappears entirely.

By pair kind (quiescence-resolved, E0 → N1q): best vs random 87.52% → 87.06%;
game vs random 84.08% → 83.72%; **best vs game 46.69% → 48.21%** (both at
chance, as in the pilot); quiet pairs 76.38% → 76.48%.

Sensitivity (flags, not gates): on the TWIC-only subset (2,350 of 2,387 groups)
G1 stays negative (−1.23% [−1.89, −0.57]) and G2 (i) stays positive (+0.0064),
so the conclusion is not cluster-driven; on the subset excluding every group the
pilot had seen in its validation or test split (7,497 positions, 2,306 groups)
the numbers are unchanged (G1 −1.63%, G2 (i) +0.0061). Test groups by family:
TWIC 2,350, PUBLIC 31, VS_SF 25, SELFPLAY 12.

## Runtime speed: gate INVALID / NON-DECISIVE; descriptive evidence of ~57% overhead

*Wording corrected after the stage closed (see the correction note at the end
of this section). The raw measurements and the verdict are unchanged.*

**Formal result: the speed gate is INVALID / NON-DECISIVE.** The design (§10)
makes a speed block valid only if its null control — RC-J against a second
RC-J process — stays within ±2% by median per-round ratio. The null control
missed that condition on both attempts (median 1.022 each time), so under the
frozen protocol no NPS band, including the >30% "automatic rejection" band, was
formally measured. The numbers below are descriptive engineering evidence, not
a gate outcome.

Idle machine, each engine its own process, 5 ABBA rounds per block, completed
depth excluding partial iterations.

| | RC-J | N1 |
|---|---|---|
| shadow cost at depth 10 (identical 16,818,635-node tree) | 1.00 | **0.427 min / 0.433 median** |
| real N1q at 1,000 ms per position | 1.00 | 0.424 min / 0.427 median |
| mean completed depth at 1,000 ms | 12.06 | **10.55 (−1.51 ply)** |
| aspiration re-searches / unstable iterations (5 rounds) | 60 / 589 | 90 / 732 |
| compile + warm-up | 27.3-28.1 s | 29.8-30.5 s |

**Descriptive engineering evidence.** The shadow build repeatedly searched the
bit-identical 16,818,635-node tree at approximately 0.43× RC-J's throughput
(0.427-0.433 in every round of both sets), implying approximately 56-57%
overhead (57.6% from the pessimistic end, 57.3% from medians), and real N1 was
approximately 1.5 completed plies shallower at equal time. The shadow-cost
build reproduces RC-J's node count exactly, so this is per-node cost, not a
tree-shape artefact: the incremental accumulator removes the first layer's
cost but the 256→32→1 head still runs at every leaf. This is very strong
evidence that the implementation is too expensive, but it is not a formally
valid timing gate.

**Why the gate is invalid, disclosed:** the null control failed both times, at
a median ratio of 1.022 against the ±2% rule, so the first set was voided and
repeated as the design requires, and the repeat also missed. The per-run
spread between identical processes reached 20% at a 1,000 ms budget. The
margin between the observed overhead and the 30% band boundary is an order of
magnitude larger than that instability, which is why the evidence is reported
as strong; it does not make the block valid.

**Correction note (2026-09-12).** This section, the verdict table and
requirement 17 originally described the speed result as a measured "automatic
rejection (>30%)". That overstated the protocol: a block whose null control
fails twice has no valid band. The wording was corrected to "INVALID /
NON-DECISIVE" with the same measurements retained as descriptive evidence. N1
remains REJECTED independently of speed, on the magnitude audit (A, D, F) and
the sealed test gates G2 and G3.

## RC-J real-loss holdout (opened last, descriptive only)

Opened after the freeze manifest, the test gates, the magnitude audit and the
speed measurement were all on file; their hashes are recorded in
`holdout/preconditions.json`. Ground truth is the autopsy's 10M-node values;
7 replay moves not already scored there were labelled at 10M nodes. This
section can neither promote nor rescue N1, and nothing was retrained after it.

| | E0 | N1q |
|---|---|---|
| 14 first decisive errors, static ranking | 3/14 | **8/14** |
| 14, quiescence-resolved ranking | 1/14 | **7/14** |
| 19 confirmed serious errors, static | 6/19 | 12/19 |
| 19, quiescence-resolved | 4/19 | 10/19 |

Cold search replay (fresh table; RC-J against the N1q engine):

| replay | RC-J good | N1 good | repaired | worsened | flips repaired / introduced | >= 100 cp repaired / introduced |
|---|---|---|---|---|---|---|
| 14 at the recorded clock | 1 | **6** | 5 | 0 | 5 / 1 | 2 / 2 |
| 14 at the autopsy's depth | 1 | 4 | 3 | 0 | 3 / 1 | 1 / 1 |
| 19 at the recorded clock | 2 | 9 | 7 | 0 | 7 / 1 | 4 / 2 |
| 19 at the autopsy's depth | 2 | 7 | 5 | 0 | 5 / 1 | 3 / 1 |

N1 finds Stockfish's move where RC-J did not in R103-25w (Qf4), R81-10b (d5),
R94-44w (Rh1), R95-20b, R81-8bs and R94-35ws, and worsens none outright.

**How much of this is evaluation?** Not clearly any of it. Three caveats, and
they are the reason the design made this section descriptive:
* the clocked replay is non-deterministic, and N1 searches about 1.5 ply
  shallower at equal time, so it explores a different tree rather than
  judging the same leaves better;
* the fixed-depth replay, which removes the clock, repairs less (3/14 against
  5/14), which is what a tree-shape effect looks like;
* on the test split the same network showed no quiescence-resolved ranking gain
  at all (79.47% against 79.57%), and 14 items cannot outweigh 7,590 pairs.

Four of the 19 are the autopsy's state-dependent cases, where a cold search
already fails to reproduce the live move.

## Verdict: N1 REJECTED

| gate | outcome |
|---|---|
| validation selection (§7) | **VALIDATION FAIL** — neither U nor B eligible; U frozen by rule |
| N1q acceptance (§8) | pass |
| magnitude audit (§10) | **FAIL** — A (call-site p99 252.6 cp), D (own middlegame link 28% hot), F (17/20 bare-king mates) |
| static test gates (§9) | **FAIL** — G1 and G4 pass; G2 and G3 fail |
| speed (§10) | **INVALID / NON-DECISIVE** — null control missed ±2% on both attempts; descriptive evidence only: ~0.43× throughput on the identical tree (~56-57% overhead), ~1.5 ply shallower at equal time |
| regression corpus (§11) | not run: barred by the magnitude-audit failure |
| holdout (§12) | descriptive: 5/14 repaired at the clock, 3/14 at fixed depth, 0 worsened |

**What N1 learned, and why it still fails.** The network is a genuinely better
*ranker* of near-balanced positions than RC-J's evaluator: within-band Spearman
with Stockfish's centipawns rises from 0.242 to 0.295 on test (+0.053
[+0.028, +0.080]), and aggregate loss improves 1.6%. But it expresses that
knowledge as a 40% larger evaluation in exactly those positions, so its
*calibrated* judgement of near-balanced positions is worse than E0's, and worse
still than simply halving E0. After RC-J's own quiescence resolution the
ranking advantage disappears. Those three findings — the magnitude audit and
gates G2 and G3 — are each sufficient for rejection. The speed block, formally
invalid because its null control failed twice, adds descriptive evidence that
the implementation costs about 57% of the search speed, because incremental
accumulators remove only the first layer's cost while the 256 → 32 → 1 head
runs at every leaf.

**Not attempted, deliberately:** rescaling or clamping f, changing any search
margin, retraining after the test or the holdout, or running an arena. The
design forbids each of them, and each would have turned a clean negative into
an unfalsifiable one.

## What this says about the next step (for the human; nothing is started)

1. **The balanced-band metric is dominated by magnitude, not order.** Halving
   E0 cuts band E-MSE from 0.0178 to 0.0068 without knowing any more chess. Any
   future candidate should be trained with the magnitude penalty built into the
   objective (a calibrated-per-band loss, or an explicit scale constraint), not
   left to discover it.
2. **The ranking gain is real but small and does not survive quiescence.** A
   leaf evaluator that only reorders positions RC-J's quiescence already
   resolves correctly buys nothing.
3. **A 128-unit accumulator with a 256 → 32 head is too expensive at RC-J's
   node rate**, even done incrementally and in integers. A useful candidate
   needs either a much cheaper head or an evaluator consulted at a fraction of
   the leaves, and the latter is a search change, which is out of scope.
4. **Bare-king endings need protection.** Training data contains almost none,
   and the correction drowned the mop-up gradient, costing three mates in
   twenty.

## Requirement compliance

| # | requirement | evidence |
|---|---|---|
| 1 | 100K positions only; no 500K, N2, N3 | pool exactly 100,000; nothing else started |
| 2 | the 19 RC-J positions fully held out | excluded from every split with the 30 games and their start families; leakage audit zero; holdout opened only in the last step |
| 3 | near-balanced performance a primary gate | G2 with a shrinkage control, within-band discrimination and a band magnitude check; selection required the same on validation |
| 4 | train labels at 50k | 79,673 train positions; `train_n1.py` asserts the file holds no validation or test pid |
| 5 | validation / test / ranking labels at 1M | 9,870 validation, 10,216 test, 2,999 validation pair moves (1,198 roots), 12,524 test pair moves (4,995 roots) |
| 6 | small deterministic 4M subset for label noise | 300 validation positions at 4M and 50k; report only |
| 7 | phase-aware calibration frozen first; calibration never counted as chess | frozen link fitted on train ∩ quiet; richer 3x3 family fitted for E0 and N1q on validation; the E0 x 1.5 control reproduces E0 |
| 8 | only the preregistered N1 architecture | one architecture, 106,689 parameters |
| 9 | only U and B, validation chooses | both trained identically; neither eligible; U frozen by rule |
| 10 | centipawn-compatible latent; audit every magnitude consumer | audit A-F; **failed** (A, D, F) |
| 11 | incremental accumulators, never full recompute in search | lazy key-validated accumulator with root seeding; rebuilds = root searches in every measured run |
| 12 | exact make/unmake across thousands of transitions | 18,950 transitions and 10,018 evaluations with zero failures, plus zero shadow-verify mismatches inside real search |
| 13 | float first, freeze on validation, then quantise; test last | selection and acceptance on validation only; the freeze manifest precedes every test step |
| 14 | holdout last, no retraining after | holdout script refuses to run without the other result files and records their hashes |
| 15 | balanced improvement and quiescence-resolved evidence required | G2 and G3 |
| 16 | search replay and regression corpus if static gates pass | barred: the magnitude audit failed |
| 17 | NPS bands | **gate INVALID / NON-DECISIVE**: the null control missed the ±2% validity condition on both attempts, so no band was formally measured; descriptive evidence of ~56-57% overhead on a bit-identical tree and ~1.5 ply lost at equal time; rejection rests on the magnitude audit, G2 and G3 |
| 18 | START_FRACTION 0.45, no search change, no arena | zero-weight control reproduces RC-J's tree; no arena run |
| 19 | main only, zero tags, no push | `main` the only branch, 0 tags, 0 stashes, one worktree, clean tree; local commits only (3 ahead of `origin/main`, unpushed); RC-J runtime files identical to `2bf6885` and the release ZIP `c8226c03…22fb5` unchanged |
| 20 | stop and report | this report |
