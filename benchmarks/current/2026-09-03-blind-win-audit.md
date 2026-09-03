# Blind-win audit: why the root search says 0 where Stockfish says +400

Date: 2026-09-03. Analysis only; production unchanged (verified against the
v0.5.2 snapshot: identical engine files apart from the two dormant hooks,
`CS_EVAL_KING_SAFETY` and `CS_EVAL_MOPUP`, both default off).

## The short answer

It is **static evaluation blindness in the endgame, to passed pawns and to
king activity**, and it is not a search problem. In 110 of 129 blind episodes
the static evaluation still does not see the win at the *end* of Stockfish's
own principal variation -- a quiet position where the win is supposed to be
visible. In pawn endings the static there averages **+4** where Stockfish
says **+616**. Quiescence recovers the missing score in 12 of 129 episodes
and depth-6 search in 7; the pruning counters show nothing a search change
could fix. The gap grows with the rank of the winner's most advanced passer
(+324 at ranks 1-3, +453 at rank 4, +665 at ranks 6-7) and is largest with
the fewest pieces on the board.

## 1. Repository verification

HEAD `360dd4d` = `origin/main`, tree clean, identity `kushagr4
<ratrakushagra@gmail.com>`, mop-up v1 left flag-gated and off as instructed.

## 2. Dataset

`tools/blindwin/dataset.py` over the two retained annotated self-play sets
(the conversion-audit games and the mop-up Gate 2 games; production is the
`base` side in both, 400 games, 20,000+ moves). A *blind episode* is the
first ply of a run of positions on production's turn where Stockfish's
standing is +300 or better and production's root score is under +100.
**129 episodes.** For each, the oracle was re-queried at 1M nodes for the PV,
WDL and mate distance; the PV was walked to its end (up to 10 plies) and
production's static evaluation recorded there; the PV was classified by what
it does. `corpus/blindwin/episodes.jsonl`, `01_dataset.txt`.

* 88 of 129 arise directly from an opponent blunder on the previous ply.
* The engine's move at the episode start loses >= 100 cp in **49** ("failed
  to punish"); in the other 80 it plays acceptably without knowing why.
* Outcomes of those games: 59 won, 64 drawn, 6 lost.
* Phase: 93 endgame, 36 middlegame. Material from production's side: level
  in 64, a pawn down in 27, a pawn up in 25. Own passers present in 76.

## 3. Horizon or blindness -- the discriminator

Production's static at the end of Stockfish's PV:

| verdict | n | share |
|---|---|---|
| **blind** -- static still under +100 at the PV end | 66 | 51% |
| partly -- static +100..+299 at the PV end | 44 | 34% |
| horizon -- static >= +300 at the PV end | 19 | 15% |

Mean static at the episode -4, at the PV end +141, Stockfish +429. If depth
were the problem the PV-end static would be high; it is not.

## 4. Mechanism, read off the PV

| mechanism | n | horizon / partly / blind | failed to punish | SF at PV end | static at PV end | gap |
|---|---|---|---|---|---|---|
| quiet / unresolved | 44 | 0 / 8 / 36 | 21 | +454 | +17 | **+437** |
| wins pawn(s) | 37 | 0 / 28 / 9 | 13 | +474 | +131 | +342 |
| wins a piece | 18 | 11 / 6 / 1 | 3 | +732 | +416 | +316 |
| king activity | 15 | 0 / 0 / 15 | 5 | +546 | -14 | **+560** |
| promotion race | 12 | 8 / 1 / 3 | 7 | +764 | +419 | +345 |
| rook activity | 3 | 0 / 1 / 2 | 0 | +536 | +106 | +430 |

Two clean groups. **Tactical wins -- a piece, a promotion -- are horizon**:
the static sees +400..+1300 once the line is played out, the search just
did not get there at depth 6. **Everything else is evaluation**: quiet
endgame wins, king activity and pawn-up endings stay at a static of 0..130
on positions Stockfish scores +450..+550. `03_gap.txt`.

## 5. What the missing knowledge is

Gap at the PV end by feature of that position (`05_gap_by_feature.txt`):

| feature at the PV end | n | gap | Stockfish | static |
|---|---|---|---|---|
| pawn ending | 18 | **+612** | +616 | **+4** |
| 1-2 non-pawn pieces | 47 | +418 | +535 | +117 |
| 3-4 pieces | 36 | +358 | +527 | +170 |
| 5+ pieces | 28 | +280 | +515 | +235 |
| own passer rank 1-3 | 48 | +324 | +511 | +187 |
| own passer rank 4 | 24 | +453 | +542 | +89 |
| own passer rank 5 | 18 | +423 | +509 | +86 |
| own passer rank 6-7 | 13 | **+665** | +735 | +69 |
| no own passer | 26 | +336 | +515 | +180 |

Tags enriched in large-gap positions: advanced_passer 43% vs 12%,
pawn_ending 20% vs 0%, minor_piece_ending 23% vs 0%, own passer on rank >= 5
33% vs 6%, on rank >= 6 16% vs 0%. An own passer exists at the PV end in
103 of 129 episodes; the position is a pawn or minor-piece ending in 65.

The pattern is exact: the fewer the pieces and the further the passer, the
larger the gap. PeSTO's pawn table gives a 7th-rank pawn +178 in the endgame
and nothing for being *passed*, nothing for the enemy king being outside the
square, nothing for the attacking king escorting it, and nothing for king
activity in a pawn ending beyond centralisation. Every one of those is what
Stockfish is counting.

## 6. Search probe

`tools/blindwin/probe.py`, 129 blind episodes against 129 seen winning
positions (same Stockfish band, root >= +300), production at depth 6:

| stage | blind episodes |
|---|---|
| static | -4 |
| root quiescence | +30 |
| depth-6 root | +31 |
| Stockfish | +429 |

Quiescence lifts the static by >= 100 in 12 episodes, the search lifts
quiescence by >= 100 in 7. Static is *negative* in 52 of 129. Pruning per
node, blind against seen: null-move 1.20x tries and 1.08x cut rate, LMR
1.03x, delta prunes 1.42x, SEE prunes 2.80x, TT hits 0.83x, nodes 1.36x --
the endgame signature (more losing captures to prune, fewer transpositions),
not a search that is cutting corners; the engine searches *more* in these
positions and finds nothing because its leaves score them level.

## 7. Depth ladder: the 49 failed-to-punish episodes at depths 6-10

`tools/conversion/depth.py`, production, `02_depth_ladder.txt`,
`06_ladder_summary.txt`. Eight were not errors at depth 6 by the 50 cp bar;
of the 41 that were:

| verdict | n | share |
|---|---|---|
| A fixed by +1 ply | 9 | 22% |
| B fixed by +2 plies | 2 | 5% |
| C needs 3-4 more plies | 5 | 12% |
| **D persists at depth 10** | **20** | **49%** |
| E unstable | 5 | 12% |

Mean loss of the chosen move 350 cp at depth 6, 175 at depth 10; 19 still
lose 100 or more at depth 10.

Against the PV-end discriminator:

| static at PV end | A +1 | B +2 | C deeper | D persists | E |
|---|---|---|---|---|---|
| horizon | 1 | 2 | 1 | 2 | 0 |
| partly | 0 | 0 | 3 | 6 | 3 |
| blind | **8** | 0 | 1 | **12** | 2 |

The eight "blind but fixed by one ply" cases need reading carefully: one
more ply stops the engine *blundering* -- the loss goes to 0 -- while its
root score stays at +16..+50 (clusters 48, 36, 75). It avoids the bad move
without ever seeing the win, which is why those games were still drawn. The
twelve blind cases that persist are the pure form: pawn endings (cluster 45,
`b2b3` for `g2g4` at every depth with the root between -4 and +10; cluster
14, `e7d7`/`e7f7` for `g6g5`, root -230 at every depth against Stockfish
+380), rook-and-pawn endings (63, 36 twice, 75) and a minor ending (38).
In 18 of the 20 persisting cases the root is still under +100 at depth 10.

So depth buys about a quarter of the *punishing* errors and none of the
*recognition*: the class is evaluation, with a tactical fringe.

## 8. Classification

| class | episodes | evidence |
|---|---|---|
| **2. static evaluation blindness** (endgame passers, king activity) | ~95 | blind + partly, minus the tactical mechanisms |
| 1. search / horizon | 19 | horizon verdicts; wins-a-piece and promotion races |
| 5. passed-pawn / race evaluation | inside 2 | gap rises with passer rank; race cases that are blind are the pawn-ending ones |
| 6. king activity | inside 2 | 15 episodes, all blind, gap +560 |
| 4. endgame technique | overlaps 2 | the mop-up class was the extreme case; here the material is still on the board |
| 3. tactical blindness | ~6 | failed-to-punish among the horizon cases |
| 7. rook activity | 3 | too few to say |
| 8. other / unresolved | small | the residual "quiet" cases are endgame evaluation, not unresolved |

**Largest common causal class: endgame static evaluation without passed-pawn
and king-activity knowledge.** Not king safety, not global material, not
repetition, not more mop-up, and not search.

## 9. Blind-win regression suite

`corpus/blindwin_regression_v1.jsonl`, built by `tools/blindwin/suite.py`:
the largest-gap episodes, at most 14 per mechanism, each with FEN, source
game, Stockfish score / WDL / mate / best / PV at 1M nodes, production's
root, static and PV-end static at build time, the mechanism, the
horizon-or-blind verdict and the depth-ladder verdict where present; split by
cluster parity into diagnostic (even) and validation (odd) halves from
different games. A regression tool for the next candidate, not an Elo
instrument.

## 10. Exactly one next experiment: passed-pawn evaluation v1 (endgame-weighted, with king distance)

**What:** a passed-pawn term in the endgame component of the evaluation:
a bonus rising with the passer's rank, increased when the defending king is
far from the promotion square and when the attacking king is close to the
pawn, and a large bonus for a passer the defending king cannot catch ("outside
the square") when the defender has no pieces. Zero for non-passed pawns;
tapered by phase so the middlegame is nearly untouched in v1.

**Why this one:** it is the feature the gap table points at from every
direction -- 103 of 129 PV-end positions have an own passer, the gap climbs
with the passer's rank from +324 to +665, and the pawn-ending row (static +4
vs +616) is the purest case of an evaluator that cannot tell a won pawn
ending from a drawn one. King activity, the other blind mechanism, enters
through the king-distance terms: in every one of the 15 king-activity
episodes the king is walking toward or escorting a pawn. Earlier sessions
deferred passers for lack of a causal signal; this audit supplies it.

**Not chosen:** generic king safety (middlegame, no link here), global
material (rejected twice), repetition (exonerated), more mop-up (its class
is done), a learned evaluator (the distribution lesson from v0.6 still
stands), search changes (section 6).

**Gating:** Gate 1 -- the 240 root suite, the conversion regression suite,
the blind-win regression suite (the blind and partly rows should move, the
horizon rows and controls should not), tactics; Gate 2 -- 200 fixed-depth
paired games with PGN, cluster bootstrap, conversion from +200/+500,
blind-episode count as the targeted metric; Gate 3 only on a clear Gate 2.
Fit nothing against Gate 2; choose weights on the diagnostic half and check
on the validation half.

## 11. RECORD THIS

1. **Stockfish +500 while the engine says near 0**: cluster 31,
   `8/5k2/7p/5p2/3K1P2/4P3/8/8 b - - 1 62` -- a pawn ending, Stockfish +519,
   root +15, static -20; the engine plays `f7e6` and loses 519 cp. The
   winning move is the quiet `h6h5`. `03_gap.txt`, king-activity block.
2. **The exact missed winning move**: cluster 45,
   `8/8/p4pp1/1p1p1k1p/1P3P1P/2P2K2/1P4P1/8 w - - 0 38`, `g2g4` wins
   (+442); production plays `b2b3` at depths 6, 7, 8, 9 and 10 with a root of
   -4..+10. `02_depth_ladder.txt`.
3. **Fixed by one extra ply**: cluster 4,
   `3K3k/4r1bP/4R1P1/8/8/8/P1p5/2n5 w - - 2 56`: depth 6 `e6e7` (loss 742,
   root +7), depth 7 `d8e7` (loss 0, root +267). And the subtler version,
   cluster 48 `8/1k6/2p2p2/3p1P1p/3P4/4PK2/R4P1r/8 w - - 2 40`: depth 7 stops
   the 322-cp blunder while the root stays at +16.
4. **Persisting at depth 10**: cluster 14,
   `8/4k3/K3p1p1/1p2Pp1p/1P5P/P1P3P1/8/8 b - - 0 38`, Stockfish +380 with
   `g6g5`; production plays `e7d7`/`e7f7` at every depth, root -230 -- it
   thinks it is losing a pawn ending it is winning.
5. **The dominant mechanism**: the feature table in section 5 -- pawn endings
   static +4 vs Stockfish +616; passer rank 6-7 gap +665. `05_gap_by_feature.txt`.
6. **The single chosen experiment**: section 10 -- passed-pawn evaluation
   v1, endgame-weighted, with king distance.

## 12. Reproduction (Windows CMD, from the repository root)

    uv run python -m tools.blindwin.dataset --games corpus\postmortem\games\annotated.jsonl corpus\mopup\games\gate2_annotated.jsonl --sf 300 --root 100 --out corpus\blindwin
    uv run python -m tools.blindwin.gap --episodes corpus\blindwin\episodes.jsonl --out corpus\blindwin\03_gap.txt
    uv run python -m tools.blindwin.probe --engine %TEMP%\cs_pm\baseline --episodes corpus\blindwin\episodes.jsonl --games corpus\postmortem\games\annotated.jsonl corpus\mopup\games\gate2_annotated.jsonl --out corpus\blindwin\04_search_probe.txt
    uv run python -m tools.conversion.depth --engine champions\v0_5_2_correctness --cases corpus\blindwin\ladder_cases.json --depths 6,7,8,9,10 --out corpus\blindwin\02_depth_ladder.txt
    uv run python -m tools.blindwin.suite --episodes corpus\blindwin\03_gap.jsonl --ladder corpus\blindwin\02_depth_ladder.json --out corpus\blindwin_regression_v1.jsonl

(`%TEMP%\cs_pm` is the instrumented copy from `tools.postmortem.instrument`;
the `qs` command on the analysis worker is new in this session.)

## 13. Artefacts

`corpus/blindwin/{01_dataset,03_gap,04_search_probe,05_gap_by_feature,
06_ladder_summary}.txt`, `02_depth_ladder.{txt,json}`, `03_gap.jsonl`,
`04_search_probe.json`, `episodes.jsonl`, `ladder_cases.json`;
`corpus/blindwin_regression_v1.jsonl` (68 positions, hash
`9caeda378f88ed58`, diagnostic 36 / validation 32);
`tools/blindwin/{dataset,gap,probe,suite}.py`; `tests/test_blindwin_tools.py`;
the `qs` command in `tools/postmortem/worker.py`.

## 14. Classification summary, one line each

1. Search/horizon -- 19 episodes, the tactical wins; depth 7-10 finds them.
2. Static evaluation blindness -- the bulk, ~95 episodes; endgame passers and
   king activity; depth does not help.
3. Tactical blindness -- a handful inside 1.
4. Endgame technique -- the same knowledge gap as 2, seen after the win is
   already on the board; mop-up v1 covered its bare-king corner.
5. Passed-pawn / race evaluation -- inside 2; the gap climbs with passer rank.
6. King activity -- inside 2; 15 episodes, every one blind.
7. Rook activity -- 3, too few.
8. Other / unresolved -- none that the PV-end test could not place.

## 15. Tests, lint, release, commit

`ruff check .` clean; 995 tests pass (10 new); release gate run at commit
time. Production untouched.
