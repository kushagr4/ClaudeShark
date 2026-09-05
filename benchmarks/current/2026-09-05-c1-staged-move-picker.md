# C1-search-staged: lazy move picker at interior nodes

**Date:** 2026-09-05 (Mac, Apple M4, Python 3.12.14, python-chess 1.11.2).
**Base:** RC-A / exact rated-v1 (`champions/rated_v1`, commit `98c48c8`).
**Change:** `cs_search._negamax` takes its moves from `cs_ordering.staged_moves`
behind `CS_STAGED_MOVES` (shipping default **off** until promoted). The picker
yields the table move, then the captures that are not losing (MVV-LVA), then
the killers, all from masked generation, and only builds and sorts the full
legal list if the search asks for more. A side with a pawn on its seventh
rank (promotions available) falls back to `order_moves`. Nothing else in the
search changed; the flag off is byte-for-byte RC-A behaviour (fingerprint
1,712,405 reproduced on this machine, all 1,204 tests + 1 skip pass).

## Gate 0

The handoff asked for an *identical* tree. It is not identical, and the
reason is structural, not a bug: `order_moves` reads history for the quiet
tail once, at node entry; the picker reads it when the tail is reached, after
the head moves' subtrees have run, and grandchild cutoffs update this side's
history in between. A diagnostic that wrapped the picker with an entry-time
snapshot over the 24-position depth-6 suite found

| staged nodes | tails that diverged from the entry-time order | explained by refreshed history | unexplained |
|---|---|---|---|
| 133,487 | 93 (0.07%) | 93 | **0** |

so the picker reproduces the sort exactly and the only difference is fresher
history at the tail. Making it identical would need a per-node copy of the
4,096-entry history half, which costs about what the picker saves; not worth
it for 0.07% of nodes. C1 is therefore a near-identical-tree speedup and was
gated as a search change: root moves and tactics as well as node counts.

| measurement | flag off (RC-A) | flag on (C1) |
|---|---|---|
| 24-position suite, depth 6, nodes | 1,712,405 | 1,708,269 (−0.24%) |
| root moves changed | — | **0 / 24** |
| knps, two alternated runs each | 118,487 / 118,942 | 138,501 / 139,684 (**+17%**) |
| wall at depth 6 | 14.5 s / 14.4 s | 12.3 s / 12.2 s (−15%) |
| sharp suite (18), depth 6, nodes | 1,850,917 | 1,852,716 (+0.10%) |
| sharp suite root moves changed | — | **0 / 18** |
| tactics, 1,000 ms per puzzle | 16/16, avg depth 8.00, 695,782 nodes | 16/16, avg depth 8.12, 717,719 nodes |
| full test suite | 1,204 passed, 1 skipped | 1,204 passed, 1 skipped |
| `tests/test_staged_moves.py` | 300+ random positions, random killers/history/table moves, with and without SEE: identical sequences | |
| ruff / mypy on `cs_search.py`, `cs_ordering.py` | clean (the 5 mypy errors in `cs_eval.py` pre-date this change) | |

Raw: `corpus/daily/time/gate0_c1staged.txt` (bench, sharp, tactics outputs).

The Windows opportunity map expected 10–20% NPS from this mechanism, on the
measurement that 79% of interior nodes cut on their first move and only 22%
have a table move; +17% on the M4 is inside that band.

## Timed screen (Gate 2 at the competition clock)

Launched 2026-09-05 (time in the log): `tools.arena --agent champions/c1_staged
--opponent champions/rated_v1 --games 226 --base-ms 120000 --increment-ms 500
--ply-cap 300 --workers 8 --corpus corpus/daily/pool/competition_actual_suite.jsonl
--set-env CS_STAGED_MOVES=1`. `champions/c1_staged` is the working tree frozen
at this commit. Against `champions/rated_v1` it carries the V2 term registry
(`cs_terms.py`, `cs_drawish.py`, `cs_kingpawn.py`, the registry hook in
`cs_eval.py`) with every term off, which is RC-A behaviour to the node
(fingerprint 1,712,405 with the flag off), plus the picker in `cs_search.py`
and `cs_ordering.py`. Only the candidate declares `CS_STAGED_MOVES`;
`rated_v1` ignores it, so the environment reaches one side. Output
`corpus/daily/time/games/c1staged_vs_ratedv1_120s.jsonl` + `.pgn`, risk report
by `tools.daily.swissrisk` to `corpus/daily/time/swissrisk_c1staged.txt`.

Pre-registered decision rule: freeze RC-B from this build only if the timed
screen is not negative (nominal Elo ≥ 0 or the bootstrap comfortably covering
0 with a clock floor no worse than rated-v1's) and there are no failures. A
same-strength result still promotes it as the new development base, because
the mechanism buys depth at zero evaluation change; a negative result closes
the lane and the flag stays off.

### Result (completed 11:37 local; 3 h 07 min wall, of which about 1 h 10 min the Mac was asleep)

Raw: `corpus/daily/time/games/c1staged_vs_ratedv1_120s.jsonl` + `.pgn`; risk
report `corpus/daily/time/swissrisk_c1staged.txt`.

| | C1-staged vs rated-v1 |
|---|---|
| games / families / **informative families** | 226 / 113 / **80 (71%)** |
| W/D/L, score | **+83 =98 −45, 58.4%** |
| nominal Elo | **+59** |
| cluster bootstrap 95% | **+25 .. +93** (score 53.5%..63.1%) |
| leave-one-family-out | +56 .. +63 |
| family-mean histogram | 0.00×6 0.25×18 0.50×33 0.75×44 1.00×12 |
| as White / as Black | 55.8% (+40) / 61.1% (+78) |
| flags, crashes, illegal moves | **0 / 0 / 0** either side |
| terminations | checkmate 128, threefold 86, insufficient 10, fifty-move 2; none at the 300-ply cap |
| lowest clock held | **C1 5.7 s** (0 games under 5 s, 12 under 10 s) v rated-v1 4.7 s (1 under 5 s, 13 under 10 s) |
| largest single think | C1 10.3 s, rated-v1 8.8 s |
| mean think / median final clock | 2.07 s / 24.8 s v 2.09 s / 24.2 s |

**Decision by the pre-registered rule: promote.** The bootstrap excludes zero
by a wide margin, the clock floor is higher than the base's, and there were no
failures. This is the first candidate in the project's history to beat
rated-v1 on the organiser's distribution at the competition clock.

*Sleep caveat, on record:* the machine slept (lid closed, on battery) from
10:20:46 to 11:31:35 with brief dark wakes (`pmset -g log`). The referee's
per-move clock is monotonic and stops during sleep, so the six games in
flight resumed with ordinary spends (largest 7.4 s, no flags); only their
wall-time field shows the gap (3,700–4,480 s against a 300–1,200 s norm).
No game was discarded.

## Stacked on the same day: the fast stalemate probe (identical tree)

Commit `0216486`: the two out-of-check stand-pat exits in quiescence ask
`_has_legal_move` instead of `any(board.generate_legal_moves())`. An unpinned
knight, pawn or slider with any target is a legal move; only a position with
none pays for the full generator, so the answer is identical
(`tests/test_has_legal_move.py`: random game and sparse positions, known
stalemates, pinned-only positions). Fingerprints unchanged in every state
(1,712,405 / 1,708,269 / sharp 1,852,716).

| quiet machine, depth 6, alternated twice | `champions/c1_staged` (no probe) | working tree (probe) |
|---|---|---|
| nodes | 1,708,269 | 1,708,269 |
| knps | 138,632 / 138,922 | **154,167 / 154,493 (+11%)** |
| wall | 12.3 s / 12.3 s | 11.1 s / 11.1 s |

Against RC-A (118.7 knps on this machine) the two together are **+30%
nodes per second** at an unchanged or near-identical tree.

## RC-B

`CS_STAGED_MOVES` now defaults to on; the no-environment fingerprint is
1,708,269. Frozen as `champions/rc_b` (picker on by default, probe, LMR
knobs at their shipped values). Release check and card: `RC_B_UPLOAD_CARD.md`.

