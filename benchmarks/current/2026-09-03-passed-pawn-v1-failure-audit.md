# Passed pawns v1 failure audit: why more seventh-rank passers, and worse — DEFER

**Date:** 2026-09-03, audit phase 22:29-22:45. **Games audited:**
`corpus/passed/games/gate2_annotated.jsonl` (200 fixed-depth paired games,
`champions/v0_8_passed` vs `champions/v0_5_2_correctness`). **Production:**
unchanged, v1 remains flag-gated and off.

**Decision: DEFER. No single compact mechanism dominates.** The candidate's
excess of seventh-rank passers comes from pushes made in positions that were
already level or lost, and its extra errors once the passer exists are
general endgame technique errors that do not involve the passer at all. Neither
is a blocked-passer discount, a promotion-square discount, or a king-proximity
correction. Nothing was implemented.

## 1. Erratum first

The Gate 2 summary tool (`tools/passed/gate2.py`) counted the baseline's
draws as wins in the "who held the better passer at ply 60" block. Corrected:

| holder of the better passer at ply 60 | games | won / drew / lost |
|---|---|---|
| candidate | 26 | 13 / 8 / 5 |
| baseline | 21 | 9 / 11 / 1 (previously printed as 20 / 0 / 1) |

Stockfish at ply 60 from the holder's side: candidate mean +1276 with 11 of
26 under +100; baseline mean +2371 with 6 of 21 under +100. The candidate
holds "the better passer" more often in positions where it is worth nothing.
The v1 record is corrected in place and this note is the authority.

## 2. Episodes

`tools/passed/audit7.py` scans every annotated move for a passed pawn of the
side to move on its seventh rank; one pawn, one side, one game is an episode
from entry until promotion, capture or the end; episodes are deduplicated by
entry position and pawn (155 raw -> 141).

| | candidate | baseline |
|---|---|---|
| episodes | 81 | 60 |
| Stockfish at entry < +100 (not winning) | 27 (33%) | 16 (27%) |
| Stockfish at entry >= +300 | 51 (63%) | 43 (72%) |
| fate: promoted / captured / stuck | 50 / 19 / 12 | 39 / 14 / 7 |
| mean plies on the seventh | 3.8 | 2.9 |
| game result for the mover | 74.1% | 76.7% |
| created by the mover's own push | 78 | 55 |
| push made from a position already < +100 | **24 (31%)** | 9 (16%) |
| push that turned >= +100 into < +100 | 1 | 3 |
| push made in a decided position (abs >= 1000) | 23 | 27 |
| creating-move loss >= 100 (winsorised mean) | 13 (51) | 6 (29) |

The candidate does not push winning passers into bad ones (1 case against the
baseline's 3). It pushes pawns to the seventh in level positions where the
push achieves nothing: the bonus is collected, Stockfish's score does not
move, and the pawn then sits on the seventh for four plies instead of three.

## 3. Mechanism at entry, not-winning episodes (Stockfish < +100)

Priority-ordered single label per episode:

| mechanism | candidate (27) | baseline (16) |
|---|---|---|
| pawn immediately capturable | 3 | 5 |
| blocked by enemy king | 1 | 0 |
| piece blockade | 5 | 2 |
| promotion square controlled | 6 | 4 |
| enemy rook/queen behind or beside | 6 | 0 |
| losing mutual pawn race | 1 | 1 |
| wrong rook pawn / corner draw | 0 | 0 |
| defending king close enough | 0 | 0 |
| supporting king too far away | 0 | 0 |
| advancement abandons another obligation | 0 | 1 |
| search/horizon | 0 | 1 |
| other | 5 | 2 |

The largest single label is 22% of the candidate's failures. Any promotion
square rule (king or piece on it, or enemy-controlled) covers 12 of 27 (44%),
and 6 of 16 (38%) of the baseline's: it is what a failing seventh-rank passer
looks like for either engine, not what the candidate does differently. The
one label the baseline never shows, an enemy rook or queen on the pawn's file
or rank (6 of 27), is a rook-ending fact the "rook-ending bundle" exclusion
covers, and 6 episodes is not a feature.

Feature rates at entry, multi-label: pawn attacked 63% of the candidate's
not-winning episodes against 24% of its winning ones, but 56% for the
baseline's not-winning ones too; enemy heavy piece on the file or rank 41% vs
16%, baseline 50%. Same shape both engines.

## 4. The errors once the passer exists

Rank-7 moves with the mover between +100 and +999 (decided positions
excluded so mate-score annotation artefacts do not count):

| | candidate | baseline |
|---|---|---|
| moves | 126 | 55 |
| serious errors (loss >= 100) | **34 (27.0%)** | 8 (14.5%) |
| errors that moved the passer itself | 2 | 1 |
| errors where Stockfish wanted the passer moved | 3 | 2 |
| kind played (candidate errors) | king 11, rook 8, pawn 8, bishop 3, knight 3, queen 1 | |
| kind Stockfish wanted | rook 10, pawn 9, bishop 6, king 4, knight 4, queen 1 | |

Thirty-two of the candidate's thirty-four errors do not touch the passer, and
Stockfish's answer is a rook move or a piece move more often than a pawn move.
Representative: cluster 28 `8/8/8/3r4/k4K2/6P1/2p2P2/4R3 b`, played `a4b3`
(king), wanted `d5d1` (rook behind the passer); cluster 31
`1R6/1P3k2/6p1/7p/5P1P/1r2p3/4K3/8 w`, played `e2f3`, wanted `b8h8`; cluster
56 `1R6/1P2Kp2/8/5p2/7P/5k2/8/1r6 w`, played `e7f7` taking a pawn, wanted
`h4h5`. These are rook-ending technique -- rook placement, tempo, which pawn
to run -- in positions the candidate reaches more often because the term
walked it there. Excluding decided positions the rank-7 loss is 42.4 vs 25.4;
level positions 19.6 vs 6.1; ahead 73.7 vs 39.3.

**Causal replay** (`corpus/passed/15_error_replay.txt`): the 34 error
positions given to both engines from a fresh searcher at depth 6, moves
scored by the oracle at 1M nodes.

| | baseline | candidate |
|---|---|---|
| same move as the other engine | 24 of 34 | |
| serious error (loss >= 100) | **20 of 34** | 24 of 34 |
| mean winsorised loss | 167 | 199 |

The baseline makes the same mistakes in the same positions. The term does not
cause the technique errors; it causes the engine to arrive in the positions
that provoke them. Removing or discounting the bonus would change where the
engine goes, not what it does when it gets there.

## 5. Why DEFER

The brief's bar was one simple missing piece of information explaining a
large fraction of the candidate's bad advanced passers. What the games show:

1. The bad passers are bad for the same spread of reasons as the baseline's,
   with no label above a quarter of them.
2. The candidate's extra passers are created in positions that were already
   level (24 of 78 pushes), not by ruining winning ones (1 of 78).
3. The extra errors after the passer exists are not about the passer; they
   are rook-ending technique, and the baseline errs in 20 of the same 34
   positions when given them. The term walks the engine into hard endings;
   it does not make it play them worse.

A blocked-passer or promotion-square discount would remove the bonus in
about 12 of 27 not-winning episodes and none of the 34 technique errors.
That is not a compelling single feature, and the rule for that case is to
stop.

## 6. What this says about v1

The rank-only term is a push incentive with no notion of consequence: it pays
for the seventh rank whether or not the pawn can ever promote, so the search
spends tempi reaching it in level positions and then must play endgames it
handles worse than the baseline handles its own. The deterministic gains in
the v1 record are real on the suites they were measured on; the games show
the price. Any v2 needs the *consequence* side (can the pawn be stopped, is
the promotion square available) and that is more than one feature; it is not
on this session's clock.

## 7. Artefacts

`tools/passed/audit7.py`; `corpus/passed/14_seventh_rank_audit.{txt,jsonl}`
(episode table, mechanism tables, feature rates, every not-winning episode
with its FEN); `corpus/passed/15_error_replay.txt` (both engines on the 34 error
positions); `corpus/passed/13_gate2_summary.txt` regenerated with the
corrected holder block; `tools/passed/gate2.py` fixed.

## 8. Reproduction (Windows CMD, from the repository root)

    uv run python -m tools.passed.audit7 --games corpus\passed\games\gate2_annotated.jsonl --out corpus\passed\14_seventh_rank_audit.txt
    uv run python -m tools.passed.gate2 --games corpus\passed\games\gate2_annotated.jsonl --out corpus\passed\13_gate2_summary.txt

## 9. RECORD THIS

1. **The erratum**: the old and new holder lines side by side (20/0/1 vs
   9/11/1). A tool bug flattered the baseline; the correction changes the
   story from "the baseline converts passers" to "the baseline avoids
   losing with them".
2. **Pushes from level positions**: 24 of 78 vs 9 of 55, with 1 vs 3 pushes
   that actually spoiled a winning position. Show cluster 63
   `3r2k1/5pp1/P1R4p/8/1p6/1P1r4/5PPP/5RK1 w`, the one candidate push that
   did spoil one: `a6a7` from +162 to -11, Stockfish wanted `h2h3`.
3. **The errors are not passer moves**: 32 of 34. Cluster 28
   `8/8/8/3r4/k4K2/6P1/2p2P2/4R3 b` on the board: king to b3 played, rook to
   d1 behind the pawn wanted.
4. **The DEFER table** (§3): no row above 22%.
