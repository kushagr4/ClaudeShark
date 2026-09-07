# C12 — a mate score may only end the search when the search could prove it

Baseline: RC-F (`champions/rc_f`, engine commit `b7f42cf`, archive
`corpus/release/claudeshark_rc_f.zip` sha256
`4ee4033e509bf8709d7d1090037d0aeb6b146da375c88f9986cb1a67789df13d`).
Lane: `kushagra/c12-verified-mate-score`, rooted at `dd6a9d2` on
`origin/rc-c-integration`, engine byte-identical to the RC-F archive, 16 of 16
files checked before any edit. SPEC_REVISION 12. C11 is untouched and is not an
ancestor of this lane.

## The defect

`cs_fast.Searcher.search` left the iterative-deepening loop the moment
`abs(best_score) > MATE_BOUND`, whatever depth had actually completed.

At depth 1 the root score is decided entirely by transposition-table reads: each
root move is made and `negamax` is entered at depth 0, where the probe accepts
any entry with `entry_depth >= 0` and returns immediately. Those entries were
written by earlier, deeper searches of **other roots**, carried across real
moves. So a single table read can hand the root a mate score, and RC-F would
stop and play on it having searched a few dozen nodes.

The mate-distance encoding itself is correct. `score_to_tt` adds the ply and
`score_from_tt` subtracts it, so a mate stored at one ply reads back with the
right distance at another; this is now held by tests at every ply from 0 to 63
and for all three bound types. The defect is not normalisation. It is trusting a
distance the current search never verified.

The consequence is that the claimed distance need not improve as moves are
played. Traced from round 54 move 93, RC-F at fixed depth 10:

| ply | move | score | mate in | completed depth | nodes |
|---|---|---|---|---|---|
| 6 | Rb6 | +29987 | 13 | 9 | 58,698 |
| 8 | Ke8 | +29989 | 11 | 1 | 44 |
| 10 | Kd7 | +29987 | 13 | 1 | 39 |
| 12 | Ke8 | +29989 | 11 | 1 | 44 |

At ply 10 the engine played Kd7 for a mate in 13 while it had just held a mate
in 11, on 39 nodes at completed depth 1, and the position cycled to a threefold.
Each individual line was a genuine mate; the engine simply never searched deeply
enough to notice it was going backwards.

## The change

One file, `cs_fast.py`, ten lines added and one changed.

```
if abs(best_score) > core.MATE_BOUND:
    if core.MATE_SCORE - abs(best_score) <= depth:
        break
```

Proving a mate in n plies takes n plies, so the loop may stop only when the
completed depth covers the distance being claimed. Otherwise the score and the
move are kept and used exactly as before and the search simply carries on.

It does not disable table mates, does not clear the table between moves, does
not touch the table layout, normalisation, bounds or replacement, and does not
change negamax, quiescence, ordering, pruning, time management or the agent. It
is symmetric: a losing mate score is held to the same rule. Legitimate early
exits survive, and a proved mate in one still stops at depth one.

## Round 54 move 103, live carried state

Both builds replay the real game move by move, so the table, killers, history
and 95 game-history keys are the live ones. Clock 21.1 seconds.

| | RC-F | C12 |
|---|---|---|
| move | Rc6 | Rc6 |
| score | +29985, mate in 15 | +29993, mate in 7 |
| completed depth | **3** | **7** |
| nodes | 563 | 4,848 |
| time | 0.3 ms | 1.7 ms |
| claim verifiable at that depth | **no** | **yes** |
| table line | 30 plies, never mates | `Rc6 Kg8 Kf6 Kh8 Kg6 Kg8 Rc8#` |

RC-F stops on a mate in 15 it has not seen, and the line it holds does not mate.
C12 stops on a mate in 7 it has proved, and the line mates in exactly 7.

## Conversion, deterministic fixed depth, same fixed defender

| position | RC-F | C12 |
|---|---|---|
| round 54, entry at move 91 | 2/4 | 3/4 |
| round 54, move 93 | 2/4 | **4/4** |
| KQK-2, a C11 residual | 1/4 | **4/4** |
| KQK-3, a C11 residual | 3/4 | **4/4** |
| total cells | 8/16 | **15/16** |

C12 also mates faster where both convert, for example 11 plies against 15 at
depth 14 from move 93. Both of C11's residual failures are repaired here with no
evaluation change at all, which confirms the C11 report's diagnosis that those
two positions were lost to this defect and not to a missing gradient.

Traced from move 93 at depth 10, the claimed distance now falls monotonically,
13 then 9 then 3 then 1, and the game ends in checkmate after 13 plies where
RC-F drew by threefold after 14.

## Everything else held still

240 competition-like positions at fixed depth 8: **0 root move changes, 0 root
score changes, 0 node-count differences**, total nodes identical at 51,854,481.
The 24-position bench fingerprint at depth 8 is identical too, 4,852,987 nodes on
both builds. That is expected: the rule changes only when the root loop stops,
never what the tree computes.

Tactics 16 of 16 at 1,000 ms. Clock ladder PASS at all fourteen clocks, worst
usage 21.4% at a 2-second clock, floor 428 ms, zero overruns, which matters
because the candidate deliberately keeps thinking where RC-F used to stop.

Transposition-table health is unchanged: hit rate 18.6% and 18.7% against RC-F's
18.5% and 19.0%.

| run | RC-F | C12 |
|---|---|---|
| 1 | 2,439,457 nps | 2,402,539 nps |
| 2 | 2,363,783 nps | 2,324,387 nps |
| mean | 2,401,620 | 2,363,463 |

Delta −1.59%, inside the 3% target.

Full test suite 1,417 passed, including 21 new cases in
`tests/test_verified_mate.py` covering mate-distance normalisation at every ply,
table round trips for exact, lower and upper bounds, eleven mate positions whose
distances were verified with Stockfish rather than assumed, the rule itself, the
stale-deep-entry reproduction, and the preservation of the mate-in-one early
exit.

## 60-game screen against frozen RC-F

Candidate working tree against `champions/rc_f`, 60 games, 120 s + 0.5 s,
strict claims, 6 workers, organiser start set, quiet machine, one CPU-heavy job.

| measure | value |
|---|---|
| result | +16 =33 −11 |
| score | 54.2% |
| nominal Elo | +29 |
| Wilson 95% | −58 .. +116 |
| paired bootstrap 95%, 30 clusters | −29 .. +89 |
| White / Black | 58.3% / 50.0% |
| failures | 0 |
| clock floor | 4,689 ms |
| largest think | 13,239 ms |

Terminations: 26 checkmate, 26 threefold, 6 insufficient material, 1 fifty-move,
1 adjudication.

The class the candidate exists for: **six games reached a position where the
opponent was reduced to a bare king, and all six were converted to checkmate.
None was drawn by repetition or by the fifty-move rule.**

The interval spans zero, so this is not on its own a proof of Elo. It is a
narrowly activating correctness fix, and the strength evidence is consistent
with a small gain rather than establishing one.

## Verdict

Gate 0 PASS on all ten criteria. Causal gate PASS. Strength screen positive but
not significant. Recommendation: PROMOTE, on the primary evidence hierarchy the
brief set out, a proven live causal repair with no correctness regression, an
unchanged fixed-depth tree, and a 1.6% speed cost.
