# The PV transposition-cutoff defect

Date: 2026-09-02. Base: `8fb67f8`. Result: `champions/v0_5_2_correctness`.

Reported by Fable during corpus analysis, reproduced independently here, and
confirmed against the offline oracle. This is the largest single tactical error
the project has found.

## The position

```
1r4k1/5p1p/5PpQ/3Bp3/2Pb4/qP3R2/7P/7K b - - 0 1
```

Stockfish 18, 4,000,000 nodes, multipv 5, black to move:

| rank | move | score | WDL | line |
|---|---|---|---|---|
| 1 | **Qf8** | **-26** | 6 / 945 / 49 | 1...Qf8 2.Qxf8+ Kxf8 3.h4 e4 4.Bxe4 |
| 2 | Qc1+ | -586 | 0 / 0 / 1000 | |
| 3 | Qa1+ | -962 | 0 / 0 / 1000 | 1...Qa1+ 2.Kg2 Qg1+ 3.Kh3 Qf1+ 4.Rxf1 |
| 4 | Qa8 | mate in 1 against | | 2.Qg7# |

`Qf8` is the only move that holds. The gap to the second best is **560 cp**.

## What the engine did

Production played **Qa1+** — the third-best move, dead lost — at every depth
tested:

| depth | production | `CS_TT_PV_POLICY=none` |
|---|---|---|
| 6 | `a3a1` **-939** | `a3f8` -36 |
| 7 | `a3a1` -917 | `a3f8` -48 |
| 8 | `a3a1` -917 | `a3f8` -44 |
| 9 | `a3a1` -915 | `a3f8` -38 |
| 10 | `a3a1` **-964** | `a3f8` -41 |

Note the engine's own score for `Qa1+`, -964, agrees with Stockfish's -962. The
evaluation was fine. The search simply never accepted `Qf8`.

## Root cause: a fail-high cascade between aspiration and the table

Instrumenting the `Qf8` subtree at depth 6 shows the mechanism directly. These
are the values returned for the `Qf8` child as the root's aspiration window
widened:

```
depth=5 window=(   -65,    -5)  entry LOWER score   7 >= beta  -5  -> returns   7
depth=5 window=(   -35,    25)  entry LOWER score  31 >= beta  25  -> returns  31
depth=5 window=(    -5,    91)                                    -> returns 100
depth=5 window=(    43,   211)                                    -> returns 212
depth=5 window=(   127,   452)                                    -> returns 464
depth=5 window=(-32000,   939)                                    -> returns 939
```

Each aspiration re-search widens the root window. The child fails high against
its own beta, a LOWER bound is stored at that value, and the next re-search
reads it back and returns a larger number still. The score chases the window
upward -- 7, 31, 100, 212, 464, 939 -- so the root sees `Qf8` as -7, then -31,
then -100, and finally -939, and concludes its only saving move is its worst.

The EXACT entries in the same subtree (depths 1-4, score -35) were correct
throughout. **Only the bound entries lied.**

The unsoundness is not in the table. A LOWER bound is a true statement about the
window it was proved in; using it at a PV node with a different window is what
is wrong, and re-storing the result compounds it across iterations.

## The fix

`TT_PV_POLICY`, replacing the `TT_CUTOFF_AT_PV` boolean:

| policy | behaviour at PV nodes |
|---|---|
| `all` | every bound cuts -- what v0.2 through v0.5.1 shipped |
| **`exact`** | **only an EXACT score cuts; LOWER and UPPER order moves only** |
| `none` | no score cutoff at all; the stored move still orders |

Non-PV nodes are untouched: the window is null, every bound is actionable, and
all three kinds still cut.

`CS_TT_PV_CUTOFF=0` still forces `none`, since existing records refer to it.

## Why `exact` rather than `none`

`none` was the workaround that first revealed the defect. `exact` fixes the same
position using less work, because it keeps the proven scores:

| policy | depth 10 on the target | nodes |
|---|---|---|
| `all` | `a3a1` -964 | 117,146 |
| **`exact`** | **`a3f8` -41** | **179,126** |
| `none` | `a3f8` -41 | 236,216 |

`exact` reaches the right move with **24% fewer nodes than `none`**.

On the position itself at depth 6 the fix is outright cheaper than the bug:

```
all    a3a1  -939   34,078 nodes
exact  a3f8   -36   19,440 nodes   <-- oracle best
none   a3f8   -36   21,033 nodes   <-- oracle best
```

## Cost

Across all 240 positions of `corpus/competition_like_v1.jsonl` at fixed depth 6:

| | nodes | nps | TT hit |
|---|---|---|---|
| `all` | 1,705,479 | 61,926 | 9.8% |
| `exact` | 1,712,405 | 62,080 | 9.9% |

**+0.41% nodes, nodes/second unchanged.**

## Red team

`tools/ttpv_redteam.py`, fixed depth 6, comparing all three policies.

**Competition-like suite, 240 positions: `exact` chose the same move as `all` in
240 of 240.** The fix is behaviourally invisible on near-level play. The only
two divergences were `none` against the other two, and both were score-neutral:

| index | all / exact | none |
|---|---|---|
| 51 | `c2c8` 67 | `c2c5` 67 |
| 168 | `e8b8` 7 | `e8a8` 15 |

Fable reported 3/240 for `none`; this run found 2. Close enough to be the same
observation under slightly different conditions, and immaterial either way.

**Stress-test suite, 138 positions: 1 divergence — the bug itself.**

```
[98] 1r4k1/5p1p/5PpQ/3Bp3/2Pb4/qP3R2/7P/7K b - - 6 36
   all    a3a1  -939   34,078 nodes
   exact  a3f8   -36   19,440 nodes  <-- oracle best
   none   a3f8   -36   21,033 nodes  <-- oracle best
   oracle: a3f8 at 22 cp
   structures: connected_passers, exposed_king, isolated_pawn, open_centre,
               open_file, opposite_coloured_bishops
```

That the near-level suite shows nothing while the stress suite shows exactly one
case is the point of keeping the two separate: this defect needs a sharp
position with a forced-looking king attack to fire at all.

## Fable's corpus, verified

Checked before relying on any of it:

| claim | result |
|---|---|
| hash `6a8111f22f9ea393` | **matches** |
| 240 positions | yes |
| all legal | yes |
| all non-terminal | yes |
| all unique | yes |
| max abs reference eval <= 50 cp | 50, yes |
| one position per source game | yes |
| Stockfish binary outside the repository | yes, absolute path outside the tree, SHA-256 recorded |
| oracle provenance | Stockfish 18, 1,000,000 nodes, Threads 1, Hash 256, hash cleared per position |

## Verdict

**Keep.** A concrete, oracle-confirmed 560 cp error is removed for +0.41% nodes,
with zero move changes across 240 near-level positions. Regression tests are in
`tests/test_tt_pv_policy.py`, including one that keeps the defect reproducible
under `TT_PV_POLICY="all"` so the fix cannot be quietly reverted.

## Regression match

Not an Elo test -- the deterministic evidence already showed identical moves on
240 of 240 near-level positions. This is insurance against a catastrophic
regression under a real clock, where games diverge by timing rather than at a
fixed depth.

```
CS_INCREMENT_MS=200, 20 s + 0.2 s, 300-ply cap, corpus competition_like_v1
champions/v0_5_2_correctness vs champions/v0_5_1_correctness over 96 games

+16 =63 -17, score 49.5%
elo -4
  Wilson score 95% CI        -73 .. +65
  paired bootstrap 95% CI    -33 .. +22   (48 position clusters)
terminations: threefold_repetition 51, checkmate 33, insufficient_material 9,
              fifty_moves 3
```

No crashes, no flags, no illegal moves. 63 of 96 games drawn, which is what two
engines differing in one rarely-reached search rule should produce. The
bootstrap interval spans zero and is centred on it: **no regression, and no
strength claim either.**
