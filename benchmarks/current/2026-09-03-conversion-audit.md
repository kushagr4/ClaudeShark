# Winning-position conversion audit

Date: 2026-09-03. Analysis and tooling only; **production engine unchanged**
(verified: depth-6 node count 1,712,405 on both production and
`champions/v0_5_2_correctness`; the only source difference is the dormant
`CS_EVAL_KING_SAFETY` hook).

## The short answer

Production converts a +200 position into a win 44% of the time and *loses* it
only 3%. The failures are draws, and they come in two kinds that need
different fixes:

1. **Blind wins (the majority).** The advantage usually arrives because the
   opponent blundered -- 39 of 42 crossings -- and the engine then has to
   *find* the refutation. In the positions where it fails, its own root score
   is tiny (+7, +9, +3 against Stockfish +400..+700): it does not know there
   is anything to convert. Serious errors run at **31%** in +300..+599
   positions where the root score is under 100, and **1.8%** where the root
   sees 300 or more. The root is blind almost only when the static is blind
   (317 of 320 cases). These wins are dynamic -- promotion races, mating nets,
   tactics with advanced pawns -- in positions where the engine is *not* ahead
   in material (97 of 136 blind positions).

2. **Seen-but-stuck wins (12 of 49 failures).** K+Q v K, K+R v K, K+R+N v K,
   K+Q v K+pawns: root score +900 to +1000 for twenty plies, every move looks
   equally good, the engine shuffles into a threefold. The evaluator has no
   mop-up knowledge; its only mating incentive is the defending king's
   edge-penalty in the PeSTO endgame king table.

Simplification is not the problem (the engine takes Stockfish's preferred
trades *more* often when ahead, 77% vs 58% level). Material is not
over-valued: production's static is flat at about 105 cp per pawn-unit of
advantage where Stockfish is flat at about 150, and its search score recovers
much of the gap. The endgame is where advantages arise in this corpus, not
where an earlier error converts.

## 1. Repository verification

HEAD `c7e999a` on `main`, equal to `origin/main` (fetched), 0 unpushed
commits, working tree clean except an untracked `tatus` (4 KB of `git log`
output from a mistyped redirect; left in place). The amended repetition-audit
commit is authored and committed by `kushagr4 <ratrakushagra@gmail.com>`;
its message carries an empty trailer-label residue on line 2 from the
amend, already pushed and left alone.

## 2. Authorship / unpushed-commit audit

Nothing is unpushed. Of the commits already on `origin/main`, the following
carry a co-author trailer of the kind removed from `c7e999a`: `d6d8696`, `dbcbbd7`,
`af30518`, `a832ce7`, `27e7f8c`, `8ca6d66`; `d6d8696` and earlier are
authored `kushgrr <kushagraratra31@gmail.com>`. Pushed history was not
rewritten. Repository-local identity is `kushagr4 <ratrakushagra@gmail.com>`
(set by the user; a display-name change made earlier in this session was
reverted).

## 3. Evidence provenance

| conclusion | status |
|---|---|
| production == v0.5.2 snapshot | independently reproduced (node count) |
| conversion 44%/33%, defence 67%/56%, recovery 27%/17% | recomputed from `annotated.jsonl` -- exact |
| repetition categories B 82 / C 44 / D 1, 0/127 true threefolds, 44 cut short | recomputed from `classified.jsonl` -- exact |
| strict adjudication 125 repetition / 67 mate / 45.8%, 2 of 44 convert | recomputed from `fixed_depth_strict.jsonl` -- exact |
| the time-controlled arena +23 =131 -46 | inherited; moves not retained |
| instrumented scratch engines search identically to the originals | independently re-verified |

`corpus/conversion/00_provenance.txt`.

## 4. Dataset construction

`tools/conversion/episodes.py` over the 200 retained fixed-depth games
(10,625 moves, every move Stockfish-annotated). An *episode* is one (game,
side, threshold, sign): the first ply at which that side's Stockfish standing
crosses the threshold, followed to the end. First crossing only, so adjacent
positions are never counted twice; 1,194 episodes. Each record carries FEN,
Stockfish cp and WDL, material balance and imbalance kind, phase, pieces,
structural tags, result, peak, the standing 5/10/20 plies later, the first
serious error after crossing, whether the advantage was recovered, and the
largest-loss move with its trajectory. `corpus/conversion/episodes.jsonl`.

Production plays 100 games as each colour against the v0.6 candidate; both
sides are reported, production is the subject.

## 5. Conversion curves (production)

| threshold | n | won | drew | lost | first serious error within 10 plies | mean standing +20 plies |
|---|---|---|---|---|---|---|
| +100 | 105 | 37.1% | 56.2% | 6.7% | 75.2% | +1642 |
| +200 | 88 | **44.3%** | 52.3% | 3.4% | 69.3% | +2229 |
| +300 | 83 | 47.0% | 50.6% | 2.4% | 71.1% | +2743 |
| +500 | 58 | 63.8% | 34.5% | 1.7% | 69.0% | +5171 |

The weakness is **general across advantage sizes and conversion-specific**:
losses from ahead are rare, draws are the failure. The candidate (v0.6) is
worse at every threshold (32.0% from +200), which is the post-mortem's
finding, reproduced.

## 6. Defence curves (production)

| threshold | n | held | won | lost |
|---|---|---|---|---|
| -100 | 83 | 71.1% | 9.6% | 28.9% |
| -200 | 75 | **68.0%** | 8.0% | 32.0% |
| -300 | 63 | 61.9% | 7.9% | 38.1% |
| -500 | 42 | 42.9% | 0.0% | 57.1% |

In self-play the two curves mirror each other -- production's failed
conversions are the opponent's successful defences -- so "symmetric" here
means the same weakness seen from both chairs.

## 7. First collapse

49 failed conversions from +200. The first serious error (>= 100 cp) by
production after crossing comes within **4 plies in 29 of them**, and in 28 of
those 29 the crossing itself was the *opponent's* serious error. The engine
is not losing an advantage it built; it is failing to cash one it was handed.
Its root score at those moments is typically under +50 while Stockfish is at
+300..+750.

`corpus/conversion/01_dataset_and_curves.txt` (collapse table),
`08_trajectories.txt` (ply-by-ply for five games).

## 8. Failure classification (first serious error, 49 failed conversions)

| category | n | note |
|---|---|---|
| quiet positional | 14 | residual, not a diagnosis |
| king exposure | 8 | heuristic is weak: mostly rook-ending checks |
| no serious error at all | 7 | drawn without any move losing 100 cp |
| passed pawn | 6 | best move pushes or wins a passer |
| missed tactic | 6 | best is a capture or check, loss >= 300 |
| material grab | 4 | captured and lost >= 100, best was quiet |
| refused trade | 3 | |
| bad trade | 1 | |
| missed mate | 0 | at the first error; mates were missed later (see 13) |

The heuristics are conservative and the residual is large; the depth ladder
(section 9) is the attribution that matters.

## 9. Depth-scaling: search/horizon or evaluation?

`tools/conversion/depth.py`: 63 positions -- the first serious error of every
failed conversion from +200 (42) plus the largest-loss move where it differed
and lost 300 or more (21) -- searched by production at depths 6, 7, 8, 9 and
10, every chosen move scored by Stockfish at 1M nodes
(`03_depth_ladder.txt`, `03b_depth_summary.txt`). Seven were not errors at
depth 6 by the 50 cp bar (the loss came from a later move); of the 56 that
were:

| verdict | n | share |
|---|---|---|
| A fixed by +1 ply | 10 | 18% |
| B fixed by +2 plies | 4 | 7% |
| C needs 3-4 more plies | 13 | 23% |
| **D persists at depth 10** | **27** | **48%** |
| E unstable | 2 | 4% |

Mean loss of the chosen move falls from 349 cp at depth 6 to 155 at depth 10,
and the number still losing 100 or more from 55 to 26. So roughly a quarter
of conversion errors are cheap horizon (one or two plies), a quarter are
expensive horizon, and **half are evaluation**: the engine's choice does not
change with depth because nothing in its evaluation distinguishes the
winning move from the one it plays.

The persisting half is endgame technique, almost without exception: pawn
endings (cluster 45 `b2b3` for `g2g4` at every depth, root +9; cluster 14;
cluster 36), bishop endings (cluster 29, twice; cluster 12), rook endings
(clusters 34, 56, 63, 75, 77), and the stuck K+R v K of cluster 77 where
`e4f4` throws a forced mate at every depth from 6 to 10 with the root score
frozen at +539. The horizon cases are the tactical ones -- cluster 4's `d8e7`
(+742) appears at depth 7, cluster 99's `g6h4` at depth 7, cluster 61's
queen manoeuvre at depth 8.

Awareness moves with depth but not enough: among errors in positions
Stockfish scores +300 or better, the root score was under +100 in 17 of 37
at depth 6 and still in 11 of 37 at depth 10.

## 10. Search instrumentation: does the engine search less carefully when ahead?

`tools/conversion/search_bins.py`: 80 positions per bin, binned by the
engine's *own* static evaluation, matched on phase, production at depth 6
(`04_search_bins.txt`). Endgame rows:

| own static | nodes | null tries / node | null cut rate | LMR / node | delta prunes / q-node | SEE prunes / q-node | aspiration re-searches |
|---|---|---|---|---|---|---|---|
| level | 21,266 | 0.0044 | 47.6% | 0.035 | 0.049 | 0.048 | 0.31 |
| +100..+299 | 21,363 | 0.0042 | 45.3% | 0.036 | 0.046 | 0.040 | 0.55 |
| +300..+599 | 25,246 | 0.0028 | 34.8% | 0.035 | 0.034 | 0.018 | 0.76 |
| >= +600 | 41,250 | **0.0013** | 38.7% | 0.029 | 0.043 | **0.009** | 0.78 |
| <= -300 | 11,257 | 0.0052 | 51.0% | 0.037 | 0.038 | 0.023 | 0.71 |

The middlegame rows show the same shape. **The hypothesis is not supported:
the search becomes *less* aggressive when ahead, not more.** Null-move
attempts per node fall by two thirds from level to +600 (fewer non-PV nodes
qualify once the score is far from the window), null cuts succeed less often,
SEE pruning in quiescence nearly vanishes, LMR is flat, and the engine spends
almost twice the nodes at +600 as at level. Aspiration re-searches rise with
the advantage, which means scores are moving between iterations -- the search
is working harder, not coasting. Principal-variation length was not measured:
`SearchInfo.pv` exists as a field but nothing in the search ever fills it, so
the worker reported an empty list for every position. Effective PV depth
remains an open instrumentation gap, noted rather than guessed at.

There is no pruning mechanism to tune here. Whatever the conversion failures
are, they are not the search cutting corners because the evaluation already
looks good.

## 11. Simplification analysis

Ahead by 200 or more (1,106 production moves): Stockfish's best move is an
equal non-pawn exchange in 35 (3.2%); the engine played it **27/35 (77%)**.
Level (2,439 moves): 96 (3.9%), played 56/96 (58%). When the engine traded
while ahead, the mean loss was 55 cp with 4 serious; when level, 10 cp with 1
serious. Trades into a pawn ending while ahead: 4, mean loss 26 cp.

Verdict: **C, simplification is handled normally**, and if anything the
engine simplifies *more* willingly when ahead. There is no simplification
signal and no case for a simplification term.

## 12. Material / compensation calibration

Production as the mover, static and search score against Stockfish
(`02_simplification_calibration_phase.txt`):

| mover ahead by k units | n | Stockfish/unit | static/unit | search/unit |
|---|---|---|---|---|
| +1 | 769 | +157 | +105 | +108 |
| +2 | 169 | +155 | +115 | +139 |
| +3 | 163 | +137 | +107 | +127 |
| +4 | 48 | +152 | +105 | +133 |
| +5 | 33 | +127 | +102 | +117 |
| +6 | 28 | +155 | +104 | +117 |

Stockfish's value per unit is essentially **flat** across the range; the
concavity the post-mortem inferred from mean-by-bucket tables does not
appear per unit. Production's static is also flat, at about two-thirds of
Stockfish's slope: it **under**-values material advantages uniformly, and
the search recovers part of the gap. This is the opposite of the v0.6 scale's
failure mode (right at +1, far too high at +4), and it argues against a
concave material term: the shape is right, only the scale is low, and the
scale is exactly what v0.6 tried and lost 40 Elo with.

Compensation (production as mover): up >= 2 units but Stockfish says not
better, n=60: static +234, search +84, Stockfish -134. Down >= 2 units but
Stockfish says not worse, n=164: static -321, search +84, Stockfish +169. The
static is badly wrong in both directions, the search halves the error, and
the serious-error rate in these positions (6.7%, 4.9%) is *below* average.
Compensation blindness exists but does not drive the conversion failures.

Verdict on the concave-material hypothesis: **not supported by the per-unit
data; deferred indefinitely.**

## 13. Endgame / phase analysis

Of 49 failed conversions, 38 were already endgames at the crossing and 34
have their first serious error in the endgame; 7 are middlegame-to-middlegame
and one crosses phases. Conversion by pieces on the board at the crossing:
26/50 with 15 or more, 11/31 with 9-14, 2/7 with 8 or fewer.

The endgame is **where the advantage arises**, because the corpus starts are
middlegame and endgame positions and 83% of moves are endgame moves. Errors
do not begin in the middlegame and convert later; they begin where they are
seen. The endgame is the cause, in the specific sense that the evaluation
lacks endgame knowledge (sections 14 and 15), not in the sense of a phase
transition being mishandled.

## 14. Structural breakdown (conversion from +200, production)

| tag | n | won |
|---|---|---|
| rook_ending | 13 | **15.4%** |
| rook_and_minor_ending | 23 | 26.1% |
| exchange_imbalance | 11 | 27.3% |
| passed_pawn | 63 | 44.4% |
| advanced_passer | 24 | 54.2% |
| opposite_coloured_bishops | 20 | 55.0% |
| locked_pawn_chain | 13 | 69.2% |
| queenless_middlegame | 8 | 75.0% |

By imbalance at the crossing: level material 39.5% won (n=38), +1 pawn 46.7%,
exchange up 37.5%. By phase: middlegame 60.7%, endgame 36.7%. Rook endings
dominate the failures; closed and queenless middlegames, the v0.6 candidate's
weak spots, are production's strong ones.

Blind winning positions (`07_blind.txt`): Stockfish >= +300 and root < 100,
n=136 against 774 seen. Blind positions are level or down in material (42%
at +0, 22% at -1; **97 of 136 not ahead in material**), enriched for rook
endings (27.9% vs 12.8%) and depleted for material imbalance (43% vs 67%)
and advanced passers (21% vs 38%). The largest gaps are promotion races and
mating nets where the static counts the material the wrong way:
`3K3k/4r1bP/4R1P1/8/8/8/P1p5/2n5 w` is Stockfish +742, root +7, static -299.

## 15. Seen-but-stuck: the elementary endgames

`09_seen_but_stuck.txt`. Of the 49 failed conversions, in **12** the root
score over the last ten own moves is +300 or more and Stockfish agrees; all
twelve end by threefold repetition. Final positions include:

| cluster | position | root | Stockfish |
|---|---|---|---|
| 4 | `8/8/6K1/8/6Q1/8/8/7k w` -- K+Q v K | +1036 | mate |
| 28 | `8/4Q3/8/5K2/2k5/8/8/8 w` -- K+Q v K | +1006 | mate |
| 87 | `8/8/6K1/8/6Q1/4k3/8/8 w` -- K+Q v K | +939 | mate |
| 98 | `1k6/3R4/5K2/4N3/8/8/8/8 w` -- K+R+N v K | +902 | mate |
| 48 | `8/5K2/8/8/k7/8/8/1R6 w` -- K+R v K | +547 | mate |
| 77 | `8/7K/5r2/8/8/6k1/8/8 b` -- K+R v K | +543 | mate |
| 45 | `5Q2/8/p5K1/1p6/kP6/8/8/8 w` -- K+Q v K+2P | +818 | mate |

Cluster 45 is the clearest: the root score is +937 for twenty consecutive
plies while the engine plays `f8c5`, `c5f8`, `f8c5`. The evaluator has no
mop-up term -- nothing that rewards the attacking king approaching the
defending king or the defending king being driven to an edge beyond the
PeSTO endgame king table's own-square values -- so every queen move scores
the same and the search has no gradient to follow.

Mini-ladder on the fifteen stuck final positions at depths 6, 8, 10, 12
(`10_stuck_ladder.txt`) makes the mechanism precise. By centipawn loss the
engine's move is *not wrong* in thirteen of fifteen -- in K+Q v K every queen
move keeps the mate, so the one-ply metric reports 0 -- yet the game was
drawn. The root score stays frozen at about +1026 in K+Q v K (clusters 28,
87) and +570 in K+R v K (cluster 48) all the way to depth 12, with no mate
score and no reason to prefer one shuffle over another. Depth helps only when
the mate is already short: cluster 4 and cluster 98 find it at depth 8,
clusters 67 and 77 at depth 12. This is not a horizon problem that more
depth solves in general; it is the absence of an evaluation gradient toward
mate. Two positions also show depth *hurting*: cluster 45 chooses a
stalemate-adjacent `f8d6` at depths 8 and 10 (loss 8,758) before recovering
at 12, and cluster 21 plays a 515-cp inaccuracy from depth 8 upward.

The gradient itself was measured (`11_mopup_gradient.txt`): in K+Q v K with
the white king on e2 and queen on d1, production's static rises only from
+914 with the black king on e5 to +975 with it on a8 -- a 61 cp spread on a
936 cp queen -- and moving the white king from e1 toward a cornered black king
adds about 40 cp, then *falls* from b6 to c7. The evaluator's entire mating
incentive is the PeSTO endgame king table, and it is too small and too flat
for a depth-6 search to assemble into a plan.

## 16. Conversion regression suite

`corpus/conversion_regression_v1.jsonl`, hash `9c7a29b0bbdde64c`, **90
positions**, every one from a retained self-play game with cluster, colour,
ply, Stockfish score/WDL/best at 1M nodes, the engine's move and loss at
build time, a failure category and the depth-ladder verdict where the
position was on the ladder. Built by `tools/conversion/suite.py build`.

| source | n | what it is |
|---|---|---|
| first_error | 42 | first serious error of a failed conversion from +200 |
| defence | 24 | first serious error of a failed defence from -200 |
| blind | 13 | Stockfish >= +300, root < +100, largest gaps |
| missed_mate | 3 | a mate on the board, thrown away |
| control | 8 | +300 crossings that *were* converted |

Split by cluster parity into **diagnostic (43, even clusters)** and
**validation (47, odd clusters)**, so the halves come from different games and
the validation half is never tuned against. Production at depth 6 scores
robust loss 226 / serious 81% on diagnostic and 205 / 64% on validation
(`12_suite_production_d6.txt`); the control rows score 119 and 4.5. It is a
regression tool, not an Elo instrument: a candidate that fixes the stuck
endgames should move the missed_mate and blind rows and leave the controls
alone, and the fixed-depth game set still decides.

## 17. Ranked root causes

Evidence-weighted, without invented percentages.

1. **Endgame evaluation knowledge -- the dominant cause.** Half of all
   conversion errors persist at depth 10 and nearly all of those are endgame
   technique; 12 of 49 failed conversions are elementary won endgames
   shuffled into repetition at a frozen root score; rook endings convert at
   15%; the static's mating gradient is 61 cp on a 936 cp queen. Strong,
   specific, reproduced from several directions.
2. **Horizon.** A quarter of errors are fixed by one or two plies and another
   quarter by three or four; the tactical first errors (missed tactic, material
   grab) live here. Real, but the engine already spends its depth where it
   can and Python buys no more.
3. **Blindness to dynamic wins** -- promotion races and mating nets in
   positions where the winner is not ahead in material; overlaps with 1 and 2;
   two of the largest gaps (clusters 76, 86) persist at depth 10.
4. **Tactical blindness** as such: 6 of 49 first errors, mostly the horizon
   cases above.
5. **Material / compensation calibration**: production under-values material
   uniformly (static ~105 cp/unit vs Stockfish ~150) and is wrong in both
   directions on compensation, but the search corrects much of it and the
   serious-error rate in those positions is *below* average. Not driving the
   failures. Concave material is **not supported**: Stockfish's per-unit value
   is flat from +1 to +6.
6. **Structural evaluation**: rook endings are the weak family, which is
   cause 1 again; closed centres and queenless middlegames, the v0.6
   candidate's weak spots, are production's strong ones.
7. **Aggressive pruning while ahead: ruled out.** The search prunes less and
   searches more when its evaluation is high.
8. **Poor simplification: ruled out.** The engine takes Stockfish's preferred
   trades more often when ahead than when level.

## 18. Exactly one proposed next experiment: mop-up evaluation for won endgames

**What:** an endgame term, active only when the opponent has no pawns and
the side to move has mating material (queen, rook, two bishops, or bishop and
knight -- the same material test `is_material_draw` already performs from the
other side), that adds to the stronger side's score a bonus for the defending
king's distance from the centre and for the attacking king's proximity to it.
The classic KXK "mop-up" term. Tapered off when the defender still has a
piece, zero in every other position, so the hot path pays one cheap gate.

**Why this one:** it has the tightest causal link in the audit. Twelve of the
49 failed conversions are exactly these positions, with WDL 1000/0/0, a root
score of +900 to +1000 and a repetition draw; the gradient measurement shows
the evaluator offers 61 cp of incentive where it needs several hundred; the
mini-ladder shows depth up to 12 does not substitute for it; and the search
instrumentation shows the search is already working hard there, so the
missing ingredient is direction, not effort. Nothing else in the ranking is
both specific enough to implement as one term and free of the v0.6 trap of
being invisible to the root suite -- the stuck endgames are exactly the
positions the regression suite now holds.

## 19. Expected upside and downside

Upside: 12 of 200 fixed-depth games were draws that a working mop-up term
converts, six of them K+Q v K or K+R v K outright. If every one converts,
that is +6 points on the 200-game score, of the order of +20 to +40 Elo
against an opponent without the term -- an upper bound; in self-play both
sides gain and the paired score moves less. It also removes a class of draw a
competition opponent would never concede.

Downside: a mis-scaled term can (a) fire in positions that are not won --
guarded by reusing the exact insufficient-material logic; (b) drive the king
toward stalemate traps -- the search handles those, and cluster 45 shows the
present engine already brushes against one; (c) cost time -- it must not,
and the gate is the usual one, depth-6 node count within noise and NPS
within noise. There is no risk to middlegame play because the term is zero
there by construction.

## 20. Gating plan

* **Gate 1**, the 240-position root suite plus the new 90-position
  conversion regression suite: the term must not change a single move on the
  240 (it is zero there) and must fix the missed_mate and blind rows without
  touching the controls. Screening only.
* **Gate 2**, 200 fixed-depth paired games with `--draw-claim auto`, moves
  retained, reported with the cluster bootstrap, conversion from +200/+500,
  defence, and repetition outcomes. The specific prediction: conversion from
  +500 rises from 64% and the repetition count falls. This decides.
* **Gate 3**, the time-controlled arena, only if gate 2 is positive, with PGN
  retained (now the default).

## 21. Performance considerations

The candidate must report depth-6 nodes and NPS against 1,712,405 and about
60,000, eval/s, and the number of positions the term fires in. A term gated
on "opponent has no pawns" is evaluated in a small fraction of nodes; the
gate itself is a bitboard test.

## 22. RECORD THIS

1. **Reaching +300 and drawing:** cluster 45, production White, Stockfish
   mate for twenty plies, root +937, `f8c5` / `c5f8` / `f8c5` into a
   threefold. Show `08_trajectories.txt`, plies 25-42, then the final position
   `5Q2/8/p5K1/1p6/kP6/8/8/8 w - - 6 55` on a board.
2. **The exact collapse move:** cluster 4, `3K3k/4r1bP/4R1P1/8/8/8/P1p5/2n5 w`,
   Stockfish +742, static -299, root +7, engine plays `e6e7` and the score is
   0 next ply; Stockfish's `d8e7` wins. Trajectory in `08_trajectories.txt`.
3. **Depth fixing a failure:** the same position at depth 7 plays `d8e7`
   (`03_depth_ladder.txt`, cluster 4). Command:
   `uv run python -m tools.conversion.depth --engine %TEMP%\cs_pm\baseline --cases corpus\conversion\cases.json --depths 6,7,8,9,10 --out out.txt`
4. **A failure persisting at depth 10:** cluster 45,
   `8/8/p4pp1/1p1p1k1p/1P3P1P/2P2K2/1P4P1/8 w - - 0 38`, pawn ending,
   Stockfish +442 with `g2g4`; production plays `b2b3` at every depth from 6
   to 10 with a root score between -4 and +10. It does not know it is
   winning at any depth it can reach.
5. **Pruning while ahead -- the negative:** `04_search_bins.txt`, null-move
   tries per node 0.0044 level to 0.0013 at +600, SEE prunes 0.048 to 0.009,
   nodes 21k to 41k. The search tries *harder* when ahead.
6. **A good simplification the engine refuses:** none worth filming; it
   accepts them 77% of the time when ahead. The honest shot is the
   simplification table in `02_simplification_calibration_phase.txt`.
7. **Internal eval dramatically wrong:** cluster 4 again (static -299 vs
   +742), and the compensation rows: up two units, Stockfish -134, static
   +234; down two units, Stockfish +169, static -321.
8. **The ranking:** section 17, and the three-line summary at the top.
9. **The evidence for the experiment:** `11_mopup_gradient.txt` -- a
   61-cp spread from centre to corner on a 936-cp queen -- beside
   `10_stuck_ladder.txt` cluster 28, root +1026 at every depth to 12.

## 23. Reproduction (Windows CMD, from the repository root)

    uv run python -m tools.postmortem.instrument --out %TEMP%\cs_pm
    uv run python -m tools.conversion.episodes --games corpus\postmortem\games\annotated.jsonl --out corpus\conversion
    uv run python -m tools.conversion.calibration --games corpus\postmortem\games\annotated.jsonl --episodes corpus\conversion\episodes.jsonl --out corpus\conversion\02_simplification_calibration_phase.txt
    uv run python -m tools.conversion.first_error --games corpus\postmortem\games\annotated.jsonl --episodes corpus\conversion\episodes.jsonl --out corpus\conversion\05_first_error.txt
    uv run python -m tools.conversion.awareness --games corpus\postmortem\games\annotated.jsonl --out corpus\conversion\06_awareness.txt
    uv run python -m tools.conversion.blind --games corpus\postmortem\games\annotated.jsonl --out corpus\conversion\07_blind.txt
    uv run python -m tools.conversion.depth --engine %TEMP%\cs_pm\baseline --cases corpus\conversion\cases.json --depths 6,7,8,9,10 --out corpus\conversion\03_depth_ladder.txt
    uv run python -m tools.conversion.depth --engine %TEMP%\cs_pm\baseline --cases corpus\conversion\stuck_cases.json --depths 6,8,10,12 --out corpus\conversion\10_stuck_ladder.txt
    uv run python -m tools.conversion.search_bins --engine %TEMP%\cs_pm\baseline --games corpus\postmortem\games\annotated.jsonl --out corpus\conversion\04_search_bins.txt
    uv run python -m tools.conversion.suite build --episodes corpus\conversion\episodes.jsonl --games corpus\postmortem\games\annotated.jsonl --ladder corpus\conversion\03_depth_ladder.json --out corpus\conversion_regression_v1.jsonl
    uv run python -m tools.conversion.suite run --suite corpus\conversion_regression_v1.jsonl --engine %TEMP%\cs_pm\baseline --depth 6

## 24. Artefacts

`corpus/conversion/00_provenance.txt`, `01_dataset_and_curves.txt`,
`02_simplification_calibration_phase.txt`, `03_depth_ladder.{txt,json}`,
`03b_depth_summary.txt`, `04_search_bins.txt`, `05_first_error.txt`,
`06_awareness.txt`, `07_blind.txt`, `08_trajectories.txt`,
`09_seen_but_stuck.txt`, `10_stuck_ladder.{txt,json}`,
`11_mopup_gradient.txt`, `12_suite_production_d6.{txt,jsonl}`,
`episodes.jsonl`, `cases.json`, `stuck_cases.json`;
`corpus/conversion_regression_v1.jsonl`; `tools/conversion/{episodes,
calibration, first_error, awareness, blind, depth, search_bins, suite}.py`;
`tests/test_conversion_tools.py`; a `pv` field on the analysis worker's reply.
