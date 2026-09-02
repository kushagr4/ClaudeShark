# Benchmark record

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

### The measurement at the competition's own operating point

Rated games are 120 s + 0.5 s, which the time manager turns into roughly 4.5 s
per move. Benchmarking both engines at exactly that budget is deterministic and
cheap, and it is the least ambiguous evidence available:

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
* per-feature A/B of PVS, null-move pruning and LMR separately, at a correct
  time control — the bundle was validated, the individual parts were not.
