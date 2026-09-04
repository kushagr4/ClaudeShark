# Benchmark record

> ## Every result below this line predates the 2026-09-02 correctness repair
>
> They were produced on **corpus v1**, which contained an illegal starting
> position (`BALANCED_OPENINGS[19]`, `OPPOSITE_CHECK`), at a **200-ply cap**
> rather than the competition's 300, with **no environment sanitisation**, and
> with **game-level intervals that ignored clustering** by starting position.
> They are kept verbatim — none has been altered — but they must be read with
> that in mind. See
> [`benchmarks/current/2026-09-02-correctness-repair.md`](benchmarks/current/2026-09-02-correctness-repair.md).
>
> ### Reclassification
>
> | result | previous claim | status now |
> |---|---|---|
> | v0.3 vs v0.2, 400 games, +30 Elo (CI +3..+58) | "statistically significant" | **Directionally encouraging, significance not established.** One position in 24 was illegal, and the interval assumed 400 independent games when they were 24 clustered positions. Both push the true interval wider than reported. **Stop quoting "+30 Elo proven."** |
> | v0.4 SEE, 240 games, +1 Elo | neutral on strength | **Efficiency result stands** — node and wall-clock measurements are deterministic and corpus-independent in kind, though the specific numbers were taken on v1. **Playing-strength result uncertain**, same caveats. |
> | Time policy sf60, 400 games, +9 Elo | inconclusive | **Still inconclusive**, and it remains a clean one-variable experiment. Same corpus and clustering caveats. |
>
> The qualitative conclusion that survives all of this is the one drawn from
> three experiments agreeing: **more search has not converted into measurable
> strength in this engine.** That pattern does not depend on a single position
> or on the width of an interval.


> Full records with exact commands live in [`benchmarks/`](benchmarks/). This
> file is the narrative summary. Results recorded before that directory existed
> are transcribed console output and are labelled as such.

## A correction that applies to everything below

Earlier revisions of this file described the competition as having roughly
"4.5 seconds per move". **That is wrong.** The competition plays a chess clock of
120 s + 0.5 s. 4.5 s is only what the allocator happens to spend on an opening
move with a full clock, and it falls through the game. Where 4.5 s appears
below it is a *fixed-budget benchmark point* used to compare engines at a
comparable amount of thinking, never a description of the time control.


Every entry is a measurement, not an impression. Arena games are played from the
balanced FEN suite in `tools/positions.py`, each position once with each colour.
Elo intervals are 95%.

Hardware for all runs below: 12-core x86-64 Windows laptop, arena at 5
concurrent games. Absolute node counts from the arena are therefore not
comparable to the single-threaded benchmark; the benchmark numbers are.

## v0.1 — first complete engine

Iterative deepening, negamax + alpha-beta, fixed-size TT, MVV-LVA + killers +
history ordering, quiescence with delta pruning, tapered PeSTO evaluation.

### Search benchmark

`uv run python -m tools.bench --ms 2000`, 24 positions, fixed 2 s budget each:

| metric | value |
|---|---|
| average depth | 6.21 |
| total nodes | 2,709,235 |
| quiescence share | 49% |
| nodes/second | 74,212 |
| TT hit rate | 14.4% |

### Arena, versus the provided baselines

10 s + 0.1 s, 24 games each.

| opponent | result | score | Elo |
|---|---|---|---|
| `baselines/minimax` | +24 =0 -0 | 100.0% | saturated |
| `baselines/numba` | see below | | |

No crashes, no flags, no illegal moves in any game.

The provided baselines are saturated and are no longer a useful measurement.
From here on the opponent that matters is the previous champion.

### Profile

`uv run python -m tools.profile_search --ms 3000 --positions 6`, 15.8 s total:

| area | share |
|---|---|
| legal move generation (`python-chess`) | ~32% |
| `cs_eval.evaluate` (including its bit scanning) | ~24% |
| `push` / `pop` | ~19% |
| move ordering | ~10% |
| search bookkeeping | ~5% |

Two thirds of the time is inside `python-chess`. Our own evaluation is the
largest single function, which is why incremental evaluation and a cheaper bit
scan are on the list — but at depth 6 a ply of search is worth more than a 25%
speedup, so search technique came first.

## v0.2 — Phase 10 search techniques

Added one at a time, each benchmarked before the next went in. Same command,
same 24 positions, same 2 s budget, so the rows are comparable.

| engine | avg depth | nodes | nps | TT hit |
|---|---|---|---|---|
| v0.1 baseline | 6.21 | 2,709,235 | 74,212 | 14.4% |
| + principal variation search | 6.21 | 2,674,502 | 75,516 | 13.7% |
| + null-move pruning | 6.62 | 3,063,171 | 78,824 | 12.2% |
| + late move reductions | **7.33** | 2,406,081 | 66,458 | 17.7% |

Notes on each:

* **PVS** bought almost nothing on its own (1.3% fewer nodes, no extra depth).
  The reason is visible in the profile: about half of all nodes are in
  quiescence, which PVS does not touch, and at depth 6 the interior tree is
  small. It is kept because it is free and it compounds with LMR, which depends
  on a null-window probe being cheap.
* **Null-move pruning** was worth +0.41 ply.
* **Late move reductions** were worth a further +0.71 ply *and* reduced total
  nodes, which is the signature of a reduction scheme that is pruning the right
  moves. Note the nps drop: re-searches make each node more expensive, so depth
  went up while raw throughput went down. Depth is the number that matters.

Cumulative: **+1.12 ply** at a fixed 2 s budget.

### The first A/B, and why it was measured wrong

`tools.arena --opponent champions/v0_1 --games 200 --base-ms 5000 --increment-ms 50`:

```
+56 =73 -71, score 46.2%
elo -26  (95% CI -65 .. +12)
terminations: checkmate 127, threefold_repetition 63, insufficient_material 8,
              fifty_moves 1, stalemate 1
```

No crashes, no flags, no illegal moves. But no improvement either — despite
+1.12 ply on the benchmark.

The explanation is a time-control mismatch, and it is worth writing down because
it invalidates the obvious way to run these tests. A 5 s + 0.05 s game gives the
engine roughly 180 ms per move. The benchmark was run at 2 s per move. Measuring
the same two engines at both budgets:

| budget/move | v0.1 depth | candidate depth | gain |
|---|---|---|---|
| 200 ms | 4.54 | 4.71 | **+0.17 ply** |
| 2000 ms | 6.17 | 7.38 | **+1.21 ply** |

Reductions and null-move pruning need depth before they pay. At 180 ms per move
the candidate gains almost nothing, while the tactical risk of reducing moves is
present in full, and its nodes-per-second is *lower* (58.7k vs 67.2k) because of
the re-searches. So the fast arena measured the change at an operating point the
competition never uses.

Rated games are 120 s + 0.5 s, which is roughly 4.5 s per move. **A/B time
controls have to produce a per-move budget in the same range as the
competition's, or the result does not transfer.** The corrected run below uses
20 s + 0.2 s, about 0.9 s per move, which is the slowest control that still
fits a useful number of games in reasonable wall-clock time.

### The corrected A/B

`tools.arena --opponent champions/v0_1 --games 120 --base-ms 20000
--increment-ms 200 --ply-cap 200`, about 0.9 s per move:

```
+44 =41 -35, score 53.8%
elo +26  (95% CI -24 .. +78)
terminations: checkmate 78, threefold_repetition 33, insufficient_material 8,
              adjudication 1
```

No crashes, no flags, no illegal moves. The point estimate flipped from -26 to
+26 exactly as the depth analysis predicted, but 120 games is not enough to
exclude zero, so **this is not on its own proof of an improvement**.

### The measurement at a competition-scale budget

With a full 120 s clock the allocator spends roughly 4.5 s on a move, so
benchmarking both engines at that fixed budget compares them at a realistic
amount of thinking. It is deterministic and cheap:

| engine | avg depth | nodes | nps | TT hit | wall time |
|---|---|---|---|---|---|
| v0.1 | 7.04 | 6,372,399 | 66,286 | 17.5% | 96.1 s |
| v0.2 | **8.33** | 4,833,655 | 66,862 | 19.3% | 72.3 s |

**+1.29 ply on 24% fewer nodes**, and it finishes the suite in 25% less wall
time because iterations complete sooner. The depth advantage grows with the
budget (+0.17 ply at 200 ms, +1.21 at 2 s, +1.29 at 4.5 s), so at the real time
control it is larger than anywhere it has been arena-tested.

### Verdict on v0.2

Promoted to champion, on the combination of a large deterministic depth gain at
the competition's operating point and an arena result that is positive and never
negative there. The Elo interval still spans zero, so the honest statement is
*"very likely better, not yet proven"*. Outstanding work:

* a longer run (400+ games) at 20 s + 0.2 s to tighten the interval;
* per-feature A/B of PVS, null-move pruning and LMR separately — done in v0.3,
  see below.

## v0.3 — attribution, correctness, evaluator speed

Full record: [`benchmarks/current/2026-09-02-v0.3-feature-attribution.md`](benchmarks/current/2026-09-02-v0.3-feature-attribution.md).

### Feature attribution (fixed depth 6, deterministic)

| variant | nodes | vs v0.1 search |
|---|---|---|
| baseline (v0.1 search) | 5,870,410 | — |
| PVS only | 5,471,327 | −6.8% |
| null-move only | 5,846,694 | **−0.4%** |
| LMR only | 2,195,691 | −62.6% |
| PVS + null-move | 3,478,706 | −40.7% |
| all three (v0.2) | 1,990,684 | −66.1% |

**Null-move pruning does nothing without PVS.** It is gated on
`beta - alpha == 1`, and with PVS off no null-window nodes exist for it to fire
at. This corrects the v0.2 note suggesting PVS might be droppable for saving
"only 1.3% of nodes": removing PVS from the full combination costs 9.4% of nodes
*and* silently disables null-move entirely. All three are kept.

### Move quality (centipawn loss against an unpruned reference)

| suite | v0.2 | safe LMR | no LMR |
|---|---|---|---|
| 24 quiet, depth 6 | 0.3 avg / 7 worst | 0.3 / 7 | 0.0 / 0 |
| 16 sharp, depth 7 | 0.7 avg / 8 worst | 0.7 / 8 | 0.0 / 0 |

LMR never blundered, and safe LMR chose an identical move in all 40 positions.
It is enabled for robustness at a measured cost of 0.6% nodes, **not** as an Elo
claim.

### Evaluator

| metric | v0.2 | v0.3 | change |
|---|---|---|---|
| evaluations/second | 196,378 | 264,053 | **+34%** |
| search NPS at depth 6 | 64,833 | 68,808 | **+6.1%** |
| depth-6 node count | 2,001,875 | 2,001,875 | identical |

Identical node counts prove the packing and unrolling are behaviour-neutral, so
the speed carries no strength risk. Guarded by an equivalence test against a
transparent reference over every suite position plus 400 randomly-played ones.

### Aspiration windows

−2.8% nodes at depth 7, −2.4% at depth 8, 23 of 24 root moves unchanged. Kept.

### Correctness fix worth its own line

With `halfmove_clock` at 99, v0.2 scored a **forced mate as a draw** and played
a random pawn move, because the fifty-move test ran before checkmate detection:

```
v0.2 (old):   move=f2f3  score=518
v0.3 (fixed): move=a1a8  score=29999
```

Rare, but it only becomes possible in long endgames, which is exactly where a
won game gets thrown away. Regression test in `tests/test_search_correctness.py`.

### Arena, and the regression a fixed-depth benchmark could not see

Full record: [`benchmarks/current/2026-09-02-v0.3-arena.md`](benchmarks/current/2026-09-02-v0.3-arena.md).

Aspiration windows were validated at fixed depth, where they are unambiguously
good. Fixed-depth runs never run out of time — and that is precisely what hid a
regression. v0.2 committed a root move that had been fully searched and improved
alpha even when the iteration was later aborted. The first aspiration
implementation refused every partial result from a narrow-window iteration, and
since aspiration applies from depth 4 up, that removed the behaviour from
essentially every real iteration under a clock.

Two 120-game runs under identical conditions, differing only in that fix:

| | score | Elo | 95% CI |
|---|---|---|---|
| before the fix | 47.9% | −14 | −61 .. +32 |
| after the fix | **53.3%** | **+23** | −23 .. +71 |

Neither result is individually significant, and the difference between them is
not either (p ≈ 0.26). What the pair does establish is a direction, and the
lesson generalises:

> **A change validated only at fixed depth has not been validated for
> time-limited play.** Anything touching the iterative-deepening loop, the abort
> path or move commitment needs an arena or a clock simulation, because the
> deterministic instruments structurally cannot reach it.

### The 400-game result — settled

```
champions/v0_3 vs champions/v0_2 over 400 games
+144 =147 -109, score 54.4%
elo +30  (95% CI +3 .. +58)
```

**The interval excludes zero.** This is the first statistically significant
strength measurement in the project. No crashes, flags or illegal moves.

It is also a lesson in sample size. The same comparison, same conditions:

| games | score | Elo | 95% CI |
|---|---|---|---|
| 120 (pre-fix) | 47.9% | −14 | −61 .. +32 |
| 120 (post-fix) | 53.3% | +23 | −23 .. +71 |
| **400** | **54.4%** | **+30** | **+3 .. +58** |

120 games could not tell −14 from +23. Reading either of the smaller runs as
evidence of anything was reading noise.

## v0.4 — static exchange evaluation

Full record: [`benchmarks/current/2026-09-02-see-experiment.md`](benchmarks/current/2026-09-02-see-experiment.md).

MVV-LVA cannot tell a real capture from one that loses material, so losing
captures sorted above every quiet move and dragged their recapture subtrees
through quiescence. SEE fixes both, behind separate flags so each was measured
on its own.

| variant (fixed depth 6) | nodes | vs v0.3 |
|---|---|---|
| v0.3 | 1,957,695 | — |
| + SEE in quiescence | 1,756,212 | −10.3% |
| + SEE in ordering | 1,848,730 | −5.6% |
| + both | 1,666,590 | **−14.9%** |

On an idle machine that is **16.8% less wall clock at identical depth**, so SEE
repays its per-call cost several times over. Depth gain: **+0.41 ply at 900 ms,
+0.34 ply at 4500 ms**. Move quality unchanged (1.5 → 1.9 cp average loss
against an unpruned reference, zero blunders, tactical suite 16/16).

SEE ignores pins — the standard limitation — and that is measured rather than
assumed: agreement with an independent brute-force swap-off over 250 random
capture positions is held above 98%, with the one disagreement kept as a named
regression test.

### And the arena said +1

```
champions/v0_4 vs champions/v0_3 over 240 games
+68 =105 -67, score 50.2%
elo +1  (95% CI -32 .. +35)
```

Full record: [`benchmarks/current/2026-09-02-v0.4-arena.md`](benchmarks/current/2026-09-02-v0.4-arena.md).

Every deterministic instrument said SEE was a clear win. The arena says nothing
happened. For contrast, v0.3 over v0.2 was a comparable depth gain and measured
+30 Elo over 400 games, so this is not simply an effect too small to see.

The likely explanation is *where* the depth comes from. SEE buys nodes by
refusing to look at losing captures — subtrees that are cheap to skip and mostly
irrelevant — and spends the savings on quiet positions the engine already
understood. **A ply bought by pruning better is not worth the same as a ply
bought by searching deeper into what matters.**

This is recorded prominently because it undermines a habit the project had been
forming: treating "+0.4 ply at a realistic budget" as a proxy for strength. That
proxy was good for v0.3 and poor here, and nothing in the deterministic
measurements distinguished the two cases beforehand.

### Current status

**v0.4 is the shipping version, and its advantage over v0.3 is unproven.** v0.3
over v0.2 is settled at +30 Elo (95% CI +3 .. +58) over 400 games. SEE is kept
because it is not a regression, because "less work for the same depth" is a
proven property, and because futility pruning and further quiescence work both
need an exchange evaluator — **not** because it was shown to gain Elo. It was
not.

## 2026-09-02 — corpus calibration and move-quality diagnosis (corpus-calibration session)

Record: [`benchmarks/current/2026-09-02-corpus-calibration.md`](benchmarks/current/2026-09-02-corpus-calibration.md).
No engine change. What was measured, against an offline reference engine
(Stockfish 18, fixed nodes, tooling only, never shipped):

* **`BALANCED_OPENINGS` is not balanced.** 12 of 24 are within +/-50 cp; two
  hang a piece to the side to move; one is a rook up; one is a piece up. The
  legacy suite also produces **zero** serious errors from the engine at depth
  6, so it cannot show what the engine gets wrong.
* **New suites** in `corpus/`: `competition_like_v1` (240 near-level,
  diverse, one-per-game positions from master games; band +/-50 cp, best
  minus second <= 100 cp) and `stress_test_v1` (138 failure-hunting
  positions). `tools/arena.py --corpus` plays them.
* **Move quality on the near-level suite**: 10% of moves lose >= 100 cp at
  depth 6 and **9% at 4.5 s per move** — 3.4x the effort changes almost
  nothing. King-related structures lead the loss table by about 3x over pawn
  structures.
* **Diagnosis of the 24 serious errors**: 12 search-depth (fixed by depth 8),
  7 evaluation (never fixed; five are pawn grabs or attacks with the engine's
  own king exposed), 3 pruning (LMR twice, delta once), 1 horizon.
* **Recommended next experiment: a bounded king-safety term**, constants
  seeded from the regression in `corpus/eval_residuals.md`. Not implemented.

## 2026-09-03 — mop-up v1: bare-king mating gradient, keep for confirmation

Record: [`benchmarks/current/2026-09-03-mop-up-v1.md`](benchmarks/current/2026-09-03-mop-up-v1.md).
Flag-gated (`CS_EVAL_MOPUP`), production default off. Gate 1: 0 of 240 root
moves changed, regression suite identical except the missed-mate rows, tactics
16/16, node counts identical. Gate 2 (200 fixed-depth paired games, moves and
PGN retained): +35 =132 -33, 50.5%, Elo +3, cluster bootstrap -0..+9;
bare-king endings converted 18/19 with the term against 14/16 without. Gate 3
not run: the signal is positive but not decisive.

## 2026-09-03 — blind-win audit: the root says 0 where Stockfish says +400

Record: [`benchmarks/current/2026-09-03-blind-win-audit.md`](benchmarks/current/2026-09-03-blind-win-audit.md).
No engine change. 129 blind episodes from 400 retained self-play games; in
110 the static still misses the win at the end of Stockfish's own line (pawn
endings: static +4 vs +616), the gap rises with passer rank to +665, and
neither quiescence nor depth-6 search recovers it. Dominant class: endgame
static blindness to passed pawns and king activity. Adds a 68-position
blind-win regression suite. Next experiment: passed-pawn evaluation v1.

## 2026-09-03 — passed pawns v1: rank-indexed bonus, inconclusive

Record: [`benchmarks/current/2026-09-03-passed-pawn-v1.md`](benchmarks/current/2026-09-03-passed-pawn-v1.md).
Flag-gated (`CS_EVAL_PASSED`), production default off. One feature: a
passed-pawn bonus by relative rank with middlegame and endgame tables
(0,0,2,4,8,16,28 / 0,4,8,16,32,56,88), chosen once from a five-member family
on the diagnostic half of the blind-win suite. Gate 1: blind-win suite robust
loss 124.0 -> 88.7 (diagnostic), 148.5 -> 123.3 (validation, read once);
conversion suite diagnostic 226 -> 181, validation 205 -> 210; root suite
35.3 -> 34.0 with 29 of 240 moves changed; flagship cluster 31 unchanged,
both adversarial controls improved. Gate 2 (200 fixed-depth paired games,
moves and PGN retained): +35 =131 -34, 50.2%, Elo +2, cluster bootstrap
-26..+30; converts +200 47.9% vs 41.0% and holds -200 59.0% vs 52.1%, but
reaches seventh-rank passers twice as often and errs there more. No search
cost (56.2k vs 56.3k NPS). Gate 3 not run.

## 2026-09-03 — passed pawns v1 failure audit: DEFER

Record: [`benchmarks/current/2026-09-03-passed-pawn-v1-failure-audit.md`](benchmarks/current/2026-09-03-passed-pawn-v1-failure-audit.md).
No engine change. 141 deduplicated seventh-rank passer episodes from the v1
Gate 2 games: the candidate's extra passers are pushed in positions already
level (24 of 78 pushes vs 9 of 55), its not-winning passers fail for the same
spread of reasons as the baseline's (no label above 22%), and 32 of its 34
extra serious errors while ahead do not touch the passer. Erratum: the
"better passer at ply 60" baseline line was 9/11/1, not 20/0/1 (tool bug,
fixed). No single compact mechanism; nothing implemented.

## 2026-09-03 — V2 start: term registry, endgame calibration set, root-cause map

Record: [`benchmarks/current/2026-09-03-v2-architecture-and-calibration.md`](benchmarks/current/2026-09-03-v2-architecture-and-calibration.md).
Branch `v2-development`; rated V1 tagged `rated-v1`, untouched. Evaluator
terms now go through `cs_terms.py` (fingerprint unchanged at 1,712,405
nodes; 1,062 tests). A 550-position, 387-trajectory calibration set with
both failure directions: blind wins sit +511 below Stockfish, false wins
+265 above. Root-cause map by trajectory: tactical/horizon 26%, passed pawn
22%, king-to-pawn coordination 15%, king activity 13% of blind wins;
drawn-material and blocked-passer configurations dominate the 24 false-win
trajectories. Single-feature scan: no linear feature explains the residual;
only king-to-pawn proximity points the right way in both classes.
Recommended V2.1 feature: endgame king-to-pawn proximity. Nothing implemented.

## 2026-09-04 — V2.1 king-to-pawn proximity: keep for Daily confirmation

Record: [`benchmarks/current/2026-09-04-v2.1-king-pawn-proximity.md`](benchmarks/current/2026-09-04-v2.1-king-pawn-proximity.md).
Branch `v2-development`; term `king_pawn`, default off; candidate frozen as
`champions/v2_1_kingpawn` (`6af9dea9c9041358`). Gate 1: validation blind-win
depth-6 loss 123 -> 106, false-win root overestimate 266 -> 251, draws and
wins flat, blind-win suite validation 148.5 -> 128.5, 240 suite 35.3 -> 33.2,
tactics 16/16, NPS +2.2%. Gate 2 vs rated V1 (200 fixed-depth paired games,
PGN and JSONL retained): +41 =129 -30, 52.8%, Elo +19, cluster bootstrap
-7..+45; +200 conversion 41% -> 48%, -200 defence 42% -> 51% held, pawn
endings 33% -> 56%, rook endings 30% -> 55%. Gate 3 not run.

## 2026-09-04 — V2.2 false-win audit: DEFER / SPLIT

Record: [`benchmarks/current/2026-09-04-v2.2-false-win-audit.md`](benchmarks/current/2026-09-04-v2.2-false-win-audit.md).
Branch `v2.2-development`; audit only, no engine change. 82-row, 52-trajectory
false-win corpus (V2.1 root >= +150, Stockfish level): 32 trajectories are
static false wins that depth 10 does not cure. Two carriers: the material
term for a piece that cannot convert in pawnless or near-pawnless endings
(~14 trajectories; KRB v KR is +372 on the bishop's price alone), and the
endgame pawn table's credit for a blockaded advanced passer (12). Fuzzy
"pawn up" scalings reach 109 genuine-win trajectories and are rejected.
Proposed V2.2a exact drawn-material recognition first, V2.2b blockaded-passer
discount second; a 21-position gallery is the V2.2 regression set.
