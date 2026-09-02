# Corpus calibration and move-quality diagnosis (Fable session 1)

Date: 2026-09-02. Base: `6449ad2`. Candidate: `champions/v0_5_1_correctness`,
which the working tree matches byte for byte. **No production engine file was
modified in this session.** Everything here is tooling, corpora, analysis and
tests.

## 1. Repository verification

| check | result |
|---|---|
| root `agent.py`, `cs_*.py` vs `champions/v0_5_1_correctness` | identical, all 8 files |
| root vs `champions/v0_5_correctness` | differs only in `cs_search.py`, `cs_time.py` (the v0.5.1 repair) |
| `uv run python -m pytest -q` | 691 passed in 105 s |
| `uv run python -m tools.release_check` | all 16 checks PASS, READY TO UPLOAD, zip 27,846 bytes |
| corpus v2 (`c269c63bb74391f0`) | 42 positions legal, non-terminal, unique; `unsuitable()` empty |
| `git status` at start | clean |

Nothing looked wrong, so no further correctness audit was performed.

## 2. The oracle

Stockfish 18 (official `stockfish-windows-x86-64-avx2` release build), run
outside the repository as tooling only. Single thread, 256 MB hash cleared
before every position, **fixed nodes**. Provenance and settings are recorded
in the header of every label file; see `corpus/README.md`.

Reproducibility was checked directly: the same position labelled twice at the
same node count gives an identical record, and labelling in parallel (one
engine per thread) gives records identical to the sequential run.

## 3. Calibration of the existing corpus (RECORD THIS)

`corpus/legacy_v2_calibration.md`, 4,000,000 nodes, multipv 3.

`BALANCED_OPENINGS` was a name. Of 24 positions:

| reference verdict | count | indices |
|---|---|---|
| near-equal (abs cp <= 50) | 12 | 0, 1, 5, 7, 10, 11, 16, 17, 19, 20, 21, 23 |
| moderate edge (50..150) | 6 | 2, 3, 4, 6, 9, 13 |
| clear advantage / decisive | 3 | 8 (+2.29), 14 (**+7.31**), 22 (+5.58) |
| tactically forced (best move >= 150 cp better than second) | 3 | 12 (+4.92, Bxc5 wins a piece), 15 (0.00 but Rb7 is the only move), 18 (+6.34, Bxc5 wins a piece) |

Band sensitivity for the 24: inside +/-25: 10; +/-50: 13; +/-75: 16;
+/-100: 17.

Two of the "balanced" positions (12 and 18) simply hang a bishop to the side
to move, which no arena result to date has flagged because both engines take
it. Position 14 is a rook up. Position 22, documented in the source as
"material imbalance, roughly level", is two rooks and a bishop against two
rooks: a clean piece up, +5.58, WDL 1000/0/0.

The 18 `SHARP_POSITIONS` are what their name says: 9 moderate edges, 6
near-equal, 2 forced, 1 clear advantage, plus the en-passant mate puzzle.

Consequence: the arena's 24 clusters contain 6 that carry almost no
information about relative strength, and a further 6 with a real edge for one
side. Colour pairing cancels the bias but not the waste.

The old suite is also too easy to be informative about move quality:
`corpus/analysis_legacy_v2_d6.md` (depth 6, oracle-judged) finds **0 of 42**
positions with a loss of 100 cp or more, robust mean loss 13 cp. The same
engine on the near-level suite below has a 10% serious-error rate. A suite
where every position is either trivially winning or trivially quiet cannot
show what the engine gets wrong.

## 4. Building a trustworthy distribution

### Source

61,459 master games from eight TWIC issues (2023 to 2026), filtered to both
players 2300+ (2100+ for niche openings), at least 24 plies, standard chess.
One transitional position (plies 16..40) and, in long games, one later
position (plies 44..100) sampled per game with a fixed seed; positions in
check, with a high halfmove clock or fewer than four legal moves are skipped.
Opening family from the first twelve plies with ECO as fallback, capped per
family (160 mainstream, 120 niche). Result: **6,203 candidates from 5,318
games across 49 families**, every one carrying its structural tags and the
game it came from.

### Labels

Every candidate labelled at 1,000,000 nodes, multipv 2 (22 minutes on 8
threads). The pool's score distribution: 42% within +/-50, 18% in 50..99,
and 22% at 200 cp or more, so master-game positions are far from
automatically level.

### The near-level band (RECORD THIS: the sensitivity table)

`corpus/band_sensitivity.md`, over the labelled pool:

| band | max gap | admitted | opening | middlegame | endgame | families >= 8 |
|---|---|---|---|---|---|---|
| +/-25 | 100 | 1478 | 184 | 947 | 347 | 48 |
| **+/-50** | **100** | **2389** | 346 | 1609 | 434 | 50 |
| +/-75 | 100 | 2981 | 445 | 2048 | 488 | 50 |
| +/-100 | 100 | 3421 | 502 | 2390 | 529 | 50 |

The WDL view says what a centipawn band means in expected score. Positions
with |E[score] - 0.5| <= 0.05 have a maximum |cp| of 66 and a mean of 22;
<= 0.10 admits up to 78 cp. So +/-50 cp is, on this pool, essentially
"expected score within 0.05 of a half" -- the oracle itself does not regard a
+/-50 position as favouring anyone. +/-100 admits positions the oracle scores
at about 60/40, which is a real edge a strong engine converts. +/-25 is not
more level in any meaningful sense (see label stability below) and halves the
pool, which costs endgame and rare-structure coverage.

Chosen: **|cp| <= 50, best minus second line <= 100 cp, |E[score] - 0.5|
<= 0.10.** The gap condition removes positions with one dominating move,
which measure tactics rather than play. 2,384 candidates qualify after
de-duplication.

### Selection

Greedy coverage: each pick is the candidate that adds the rarest structural
tags, family and phase, with caps of 12 per family, one per source game, and
a 15/60/25 opening/middlegame/endgame split. Exact and near-duplicates (same
side to move, at most two squares differ) are dropped.

## 5. COMPETITION_LIKE v1

`corpus/competition_like_v1.jsonl`, hash `6a8111f22f9ea393`.

| | |
|---|---|
| positions | 240, from 240 distinct games |
| phase | 144 middlegame, 60 endgame, 36 opening |
| reference eval | mean +1.9 cp, median abs 6 cp, max abs 50 cp, max abs(E - 0.5) 0.056 |
| side to move | 113 white, 127 black |
| families | 49 (17 mainstream, 32 niche), 3 to 7 positions each |
| tags with >= 10 positions | 37 |

`tests/test_corpus_tools.py` asserts every position is legal, non-terminal,
unique, inside the declared band, from a distinct game, and that the side to
move is not lopsided. `tools/arena.py --corpus corpus/competition_like_v1.jsonl`
plays it with the same colour pairing and clustering as before, recording the
suite's hash in the match header.

## 6. STRESS_TEST v1

`corpus/stress_test_v1.jsonl`, hash `591ec2b339da3a42`: 138 positions -- 120
selected from the pool for compensation for material (58), only-moves (57),
locked centres, exchange and minor-versus-pawns imbalances, unusual kings,
promotion races, attack races, opposite bishops a pawn up -- plus 18
hand-picked classical themes (trebuchet zugzwang, Lucena, opposition,
fortress, stalemate trap, knight against pawns). Results from it are never a
headline Elo figure.

## 7. and 8. Opening coverage

Mainstream, in the competition suite: Ruy Lopez 5, Italian 5, Scotch 5, QGD
6, QGA 4, Slav 5, Semi-Slav 7, Sicilian 5, French 5, Caro-Kann 5, King's
Indian 6, Grunfeld 5, Nimzo-Indian 5, Queen's Indian 5, English 5, Reti 5,
Catalan 6.

Niche: Benoni 4, Benko 4, Dutch 6, Pirc 4, Modern 5, Alekhine 4, Scandinavian
5, King's Gambit 4, Evans 3, Danish 3, Smith-Morra 4, Budapest 4, Trompowsky
5, Bird 4, Owen's 5, Polish 5, London 5, Colle 5, plus Vienna, Petrov,
Philidor, Four Knights, Bogo-Indian, Old Indian, Chigorin, Albin, Alapin,
Closed Sicilian, Torre, Ponziani, Bishop's Opening, Centre Game, Nimzo-Larsen.

Openings are the sourcing device, not the labels: the structural tags are
what the analysis groups by.

## 9. Structural coverage

Top tags in the competition suite: isolated pawn 172, material imbalance
127, passed pawn 98, backward pawn 96, doubled pawns 94, rook on open file 91,
open centre 91, bishop pair 76, bad bishop 65, exposed king 54, king in
centre 48, weak colour complex 47, queenside majority 46, knight outpost 45,
protected passer 41, queenless middlegame 41, advanced passer 33, locked pawn
chain 31, space advantage 30, isolated queen's pawn 30, opposite-coloured
bishops 27, connected passers 26, closed centre 24, Carlsbad 22, opposite-side
castling 21, exchange imbalance 18, Maroczy bind 12, minority attack 10,
hanging pawns 7. Endgame classes: rook-and-minor 21, minor-piece 11, rook 9,
queen 5, pawn 4.

### Label stability (why 1,000,000 nodes is enough for the band)

240 pool positions with |cp| <= 100 relabelled at 4,000,000 nodes
(`corpus/label_stability.txt`, sample in `corpus/label_stability_sample.json`):

| | |
|---|---|
| shift, mean signed / mean abs / median abs / p90 / max | -0.9 / 8.1 / 6 / 19 / 44 cp |
| +/-25 at 1M still inside +/-25 at 4M | 93 of 102 (91%), none beyond 50 |
| **+/-50 at 1M still inside +/-50 at 4M** | **157 of 163 (96%), none beyond 75** |
| +/-75 at 1M still inside at 4M | 207 of 209 (99%) |
| best move unchanged | 195 of 240 |
| gap > 100 at 1M still > 100 at 4M | 24 of 25 |

The label noise is about 8 cp, so a +/-25 band is narrower than its own
measurement error while +/-50 is not. That is the other half of the argument
for +/-50.

## 10. ClaudeShark's move quality on the near-level suite (RECORD THIS)

`corpus/analysis_cl_v1_d6.md` (fixed depth 6, deterministic) and
`corpus/analysis_cl_v1_4500ms.md` (4.5 s per move, three concurrent
searches, mean depth reached 7.3). Loss is the oracle's score after its best
move minus its score after the engine's move, both children at 1,000,000
nodes, from the side to move.

| run | agree | <= 25 cp | median | robust mean | p90 | p95 | >= 100 cp | >= 300 cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|
| legacy suite, depth 6 (42) | 45% | 74% | 0 | 13 | 39 | 41 | **0%** | 0.0% | 0.023 |
| competition-like, depth 6 (240) | 37% | 66% | 2 | 35 | 95 | 165 | **10%** | 1.7% | 0.064 |
| competition-like, 4.5 s (240) | 37% | 67% | 2 | 34 | 95 | 175 | **9%** | 1.2% | 0.062 |

By phase (depth 6): endgame robust mean 20, 5% serious; opening 18, 0%;
**middlegame 46, 15% serious, 2.1% catastrophic.**

The second RECORD THIS in this table: **3.4 times the search effort changed
almost nothing.** 200 of 240 moves are identical at depth 6 and at 4.5 s. Of
the 24 serious errors at depth 6, 19 are still serious at 4.5 s; time cured
5 and introduced 3. Every one of the 7 evaluation-cause errors survives.

## 11. Weaknesses by structure

Tags with n >= 8, ranked by robust mean loss at depth 6 (4.5 s in brackets):

| tag | n | robust mean | >= 100 cp | E-loss |
|---|---|---|---|---|
| unusual_king_placement | 15 | 65 (51) | 27% (13%) | 0.129 |
| king_attack | 9 | 59 (59) | 22% (22%) | 0.097 |
| exposed_king | 54 | 58 (57) | 20% (19%) | 0.112 |
| space_advantage | 30 | 56 (53) | 17% (17%) | 0.090 |
| rook_on_open_file | 91 | 50 (46) | 19% (16%) | 0.098 |
| queenside_majority | 46 | 49 | 17% | 0.100 |
| passed_pawn | 98 | 46 (41) | 16% (13%) | 0.085 |
| material_imbalance | 127 | 46 (42) | 14% (13%) | 0.088 |
| closed_centre | 24 | 44 (46) | 8% (8%) | 0.070 |
| ... | | | | |
| isolated_queen_pawn | 30 | 20 | 7% | 0.042 |
| carlsbad | 22 | 16 | 5% | 0.036 |
| minority_attack | 10 | 16 | 0% | 0.031 |
| minor_piece_ending | 11 | 10 | 0% | 0.003 |
| rook_ending | 9 | 2 | 0% | 0.000 |

The pattern is stable across the two budgets: **king-related tags lead, at
about three times the loss of the classical pawn-structure tags.** Isolated
queen's pawn, Carlsbad and minority attack, the structures a pawn-structure
term would target, are among the best handled. Rook and minor-piece endings
are near-perfect, which is consistent with PeSTO endgame tables doing their
job once material is simple.

By opening family the worst are Albin, Ruy Lopez, Vienna, Dutch, Philidor,
Nimzo-Indian and King's Indian; the best are Petrov, Benko, Sicilian,
English, Torre, Semi-Slav. With 4 to 7 positions per family these are
suggestive only. No niche family stands out beyond what its structures
predict: the Dutch and Vienna positions that failed are exposed-king
positions.

## 12. Search failure or evaluation failure?

`corpus/diagnosis_cl_v1.md`: for each of the 24 serious errors, a depth
ladder 4..9 with every move oracle-scored, six feature-off variants at depth
6 (null move, LMR, quiescence SEE, aspiration, TT cutoff at PV, delta
pruning), a 4.5 s search, and whether the static evaluator itself prefers the
child after the engine's move to the child after the oracle's.

| cause | count | meaning |
|---|---|---|
| search_depth | 12 | the right move appears by depth 8 (nine of them exactly at 8) |
| **evaluation** | **7** | never fixed through depth 9, and the static evaluator prefers the wrong child |
| pruning | 3 | a feature-off variant fixes it at the same depth: LMR twice (cl-117, cl-149), delta pruning once (cl-162); LMR also fixes two of the search_depth cases |
| horizon | 1 | fixed only at depth 9 |
| unresolved | 1 | never fixed, evaluator not obviously to blame |

The 4.5 s column of the diagnosis was run under six-way CPU contention and
is not trusted; the clean timed run in section 10 is: at competition-scale
budget 8 of the 12 search_depth errors are still there, because 4.5 s
reaches depth 7, not 8.

The seven evaluation errors, read by hand (PVs in the diagnosis file):

| id | engine | oracle | what the engine misjudged |
|---|---|---|---|
| cl-170 | Qxe6 (+1.13) | Bc3 | grabs a pawn; ...h3 opens its own king (opposite-side castling) |
| cl-097 | Nb3 | g4 | ignores the attack on its b1 king and the e3 passer |
| cl-125 | Nxe3 (+4.70 static) | Nxa3 | takes a bishop into a mating attack; the oracle's line is a perpetual |
| cl-144 | Qxe4 | Qe2 | grabs a pawn with its own king on d7 exposed to queen and knight |
| cl-202 | Bxa7 | Nd4 | wing pawn grab; ...h4 and the h-file attack follow |
| cl-094 | Qh5 | Qb4 | attacks instead of consolidating a pinned knight |
| cl-198 | Qa1+ | Ka7 | checks instead of stepping the king out of a mating net |

**Five of the seven are the same mistake: material taken or an attack begun
while the engine's own king is exposed.** The evaluator has no term for king
exposure, so the search sees a pawn and no cost. This is what the tag table
in section 11 shows statistically and the regression in section 13 shows
numerically, from three independent directions.

## 13. Current evaluator audit

`cs_eval.py`, confirmed from source: tapered PeSTO material and piece-square
tables (0..24 phase), a bishop-pair bonus, a tempo bonus. Nothing else. No
pawn-structure, king, mobility, rook-file, outpost, space or threat term.

`corpus/eval_residuals.md` measures what that costs, over all 6,203 labelled
positions: the static evaluator's correlation with the oracle is 0.485; after
a depth-1 search with quiescence (so pending captures are resolved) it is
0.710, R^2 0.502. Regressing the remaining residual on 28 cheap features,
tapered by phase, raises R^2 to 0.561. The well-determined terms (|t| >= 3),
in centipawns per unit of white-minus-black:

| feature | MG | EG | t | note |
|---|---|---|---|---|
| king_open_files (files near the king with no own pawn) | **-24** | +18 | -5.0 | king safety |
| king_zone_attackers (enemy pieces hitting the king's ring) | **-16** | -5 | -4.9 | king safety |
| passed_advance (per rank a passer has advanced) | +20 | +3 | +4.9 | with `passed` at -46 MG: a passer on the 3rd is a liability, on the 6th an asset |
| rook_open_file | +25 | +17 | +4.3 | |
| connected_passed | +40 | -29 | +3.6 | |
| doubled | -5 | -23 | -3.8 | endgame only |
| isolated | 0 | -16 | -3.2 | endgame only |
| mobility_bishop / mobility_knight (per safe square) | +2.7 / +3.1 | +4.7 / +6.1 | +3.4 / +2.8 | |
| bishop_pair | -11 | +59 | +3.1 | PeSTO's pair bonus is too small in the endgame |
| rook_seventh | +53 | -18 | +2.9 | |

Mean absolute error of the engine's quiet score by tag confirms the same
ordering: king_attack 179 cp, advanced_passer 172, connected_passers 169,
protected_passer 151, exchange_imbalance 151, unusual_king 148, exposed_king
143, against isolated_queen_pawn 95 and Maroczy 93.

Ranked list of absent concepts, by evidence:

1. **King safety** (shelter, open files near the king, attackers on the king
   zone): top of the move-quality tag table, five of seven evaluation-cause
   errors, two of the three strongest regression coefficients.
2. **Passed pawns by rank** (with connected and protected bonuses): largest
   quiet-score errors by tag; strong coefficient; but the move-quality loss on
   passed-pawn tags is only moderately elevated and the errors there were
   mostly search-depth.
3. **Rook on open or semi-open file**: clear coefficient, cheap; move-quality
   loss on the tag is elevated but that tag co-occurs with exposed kings.
4. **Mobility**: consistent small coefficients; expensive per node.
5. **Doubled and isolated pawns**: endgame-only effect, and the corresponding
   structures are already handled well. Lowest priority despite being the
   textbook first term.

## 14. Top five next improvement candidates

Runtime costs from a micro-benchmark of each term written in the style of
`evaluate()` (bitboard scans, no allocation), against `evaluate()` itself at
3.7 us per call on the suite; a node costs about 14.5 us at 69k nps.

| candidate | evidence | expected value | runtime cost | risk |
|---|---|---|---|---|
| **king safety** (shelter + open files + zone attackers) | sections 11, 12, 13 agree | highest: the only concept implicated by all three analyses, and the one the search cannot compensate for | +3.8 us per eval, about +26% per node, roughly -0.25 ply | medium: attack counting is the classic over-tuned term; must be phase-tapered and bounded |
| passed pawns by rank | regression t 4.9; largest quiet-score errors | medium-high | +3.7 us for the whole pawn term set, cacheable by pawn hash to near zero | low |
| rook open / semi-open file | regression t 4.3; cheap | medium-low | +0.7 us | very low |
| LMR refinement (history-aware, or not reducing moves that gain material or attack the king) | 4 of 24 serious errors fixed by turning LMR off | medium; but the v0.2 and v0.3 history says search changes have not converted | none | medium: benchmarked by depth, must be judged by move quality |
| mobility | consistent small coefficients | low-medium | +2.7 us | low, but the cheapest version double-counts PeSTO centralisation |

## 15. Recommended first strength experiment

**King safety, as one bounded evaluation term, nothing else in the same
change.**

Shape: for each king, a middlegame-weighted penalty of the form
`a * (files near the king without an own pawn) + b * (enemy non-pawn pieces
attacking the king's ring)` subtracted from that side, plus a small shelter
bonus, tapered to zero in the endgame, with the initial constants taken from
the regression (a about 24, b about 16, shelter about 8) and then tuned on
the labelled corpus, not by hand. Gate it behind a `CS_*` flag like every
other feature.

Why this and not passed pawns: expected Elo times confidence over complexity
times risk. The confidence is the point. Passed pawns have the bigger
regression coefficient in places, but the errors on passed-pawn positions
were mostly cured by two more plies, which the search will get from any speed
work. King-exposure errors were cured by nothing: not depth 9, not 4.5 s, not
any pruning switch. They are the ones that lose games outright (three of the
four catastrophic errors at depth 6 are in this group). The complexity is
higher than a pawn term and the tuning risk is real, which is why the
acceptance test must be the labelled corpus first and the arena second.

Acceptance sequence (section 19 discipline): (1) the regression and the
per-tag quiet-score error improve on `candidates_labelled.jsonl`; (2)
`analyse.py` at depth 6 on `competition_like_v1` shows the exposed_king and
king_attack rows improving without the others regressing, and the seven
evaluation-cause positions move; (3) `tactics.py` 16/16 and `bench.py --depth 6`
node cost within budget; (4) a 200-game arena on `competition_like_v1` with
`--corpus`; (5) only then 400+ games.

## 16. Offline tuning and a learned evaluator

The regression in section 13 is offline weight fitting: linear features,
MG and EG weights, fitted to an external engine's labels, shipping only
numbers. It already says which handcrafted terms are worth having and roughly
what they are worth. The honest limit: 28 linear features raise the quiet
score's R^2 from 0.50 to 0.56. The evaluator is missing interactions, not
just terms.

| | handcrafted terms | linear weights fitted offline | small NN (ONNX) evaluator |
|---|---|---|---|
| expected strength | modest, term by term | same terms, better constants | potentially large, but only if evaluated thousands of times per move, which python-chess plus Python cannot afford today |
| inference cost | 1..4 us per term | identical | 50..500 us per call in onnxruntime for anything tiny, i.e. 4..30x the current node cost |
| engineering risk | low per term | low; the tooling exists as of this session | high: feature extraction in Python is the bottleneck, and the 60 s init only helps loading, not per-node cost |
| interpretability | full | full | none |
| release restrictions | none | none | allowed (our own model, onnxruntime preinstalled) but every byte is a judge's question |

Recommendation: handcrafted terms with regression-derived constants, one term
at a time. A learned evaluator becomes compelling only after a faster move
generator (`docs/MOVEGEN.md`), because its cost per call is irrelevant until
the rest of the node is cheap. Keep the labelled pool: it is the training set
either route needs, and it should grow.

## 17. The 60-second initialisation budget

Current use 1.47 s of 60. Nothing in the recommended experiment needs it.
What would: Numba compilation of a bitboard evaluator (tens of seconds, and
the reason Numba is viable at all under this rule), onnxruntime session
creation and warm-up for a learned evaluator. The economics change only for
architectures whose per-move cost is small and whose setup is large; a Python
evaluator is the opposite shape.

## 18. Benchmark methodology

* Strength comparisons: `tools/arena.py --corpus corpus/competition_like_v1.jsonl`,
  even game counts, `--jsonl`, 300-ply cap, both intervals. 240 clusters
  instead of 24 changes the bootstrap materially: a 480-game match has 240
  independent starting positions.
* Never quote a result on the legacy suite as a strength figure again; it
  remains the regression-match suite for comparability with the records that
  used it.
* Move quality before games: `analyse.py` at depth 6 is deterministic and
  takes six minutes; a change that does not move the tag table there does
  not need an arena.
* The stress suite is for failure hunting and for the RECORD THIS reel.

## 18b. The stress suite

`corpus/analysis_st_v1_d6.md` (120 oracle-labelled stress positions; the 18
hand-picked themes carry no reference and are skipped by the analyser):
agree 76%, robust mean 31, **10% serious, 3.3% catastrophic**. Worst tags:
locked_pawn_chain (robust mean 76, 10.5% catastrophic), exposed_king 63,
connected_passers 62, exchange_imbalance 51.

`corpus/diagnosis_st_v1.md` on its 12 serious errors: 6 search-depth, 3
pruning, 2 unresolved, 1 evaluation. Two are worth a closer look.

**st-098 (RECORD THIS: a concrete search defect, reproduced).**
`1r4k1/5p1p/5PpQ/3Bp3/2Pb4/qP3R2/7P/7K b - - 6 36`, Black to move. The only
move is Qf8, which the oracle scores about -0.1. ClaudeShark plays Qa1+ and
walks into mate, at every depth from 4 to 9, scoring itself -9.39 at depth 6
while still refusing Qf8. Turn off `CS_TT_PV_CUTOFF` and it finds Qf8 at
depth 6 (-0.36) on fewer nodes (21,025 against 34,069). Reproduction:

```
set CS_TT_PV_CUTOFF=0
uv run python -c "import chess; from cs_search import Searcher; m,i=Searcher().search(chess.Board('1r4k1/5p1p/5PpQ/3Bp3/2Pb4/qP3R2/7P/7K b - - 6 36'),0,max_depth=6); print(m,i.score)"
```

(default: `a3a1 -939`; with the flag off: `a3f8 -36`). A transposition-table
score from a null-window or reduced search is cutting a PV node and hiding
the only defence. `PROJECT.md` notes the flag is on "because that is what
v0.2 shipped". This is not touched in this session, per the brief, but it is
the one search finding that looks like a defect rather than a shortfall and
it should be red-teamed next: the run in section 18c is the first step.

**st-024 (RECORD THIS: a rare structure breaks the engine).**
`8/2p5/3p3p/pp1Pk1p1/2P3P1/PP2K2P/8/8 w - - 0 40`, a pure pawn ending. The
oracle holds with Kd3; ClaudeShark plays cxb5 at every depth through 9 and
loses 4.2 pawns of evaluation: the evaluator sees a capture and nothing about
the resulting outside passed pawn and king race. Classified as evaluation:
never fixed by depth, static evaluator prefers the wrong child.

**st-028**, a bishop ending, is the opposite kind: Bxf6?? loses 9.75 at depth
6 and is fixed at depth 7. That one is a search-depth shortfall in a position
with few pieces, exactly where the engine should be deepest.

## 19. RECORD THIS moments

| # | what | command / artefact | show |
|---|---|---|---|
| 1 | `BALANCED_OPENINGS` was a name: 12 of 24 level, two hang a piece, one is a rook up | `uv run python -m tools.corpus.calibrate_legacy --nodes 4000000 --workers 8` | `corpus/legacy_v2_calibration.md`, the table; the boards for index 14 (`8/5pk1/6p1/8/8/1R6/5PPP/6K1 w`) and index 12 (`r3k2r/pp3ppp/2n1bn2/2bp4/8/2N1BN2/PPP2PPP/R3KB1R w`, Bxc5 wins a piece) |
| 2 | the old suite produces zero serious errors; the near-level suite produces 10% | `corpus/analysis_legacy_v2_d6.md` against `corpus/analysis_cl_v1_d6.md` | the two "Overall" rows side by side |
| 3 | band sensitivity: what +/-25, 50, 75, 100 admit, and label noise of 8 cp | `uv run python -m tools.corpus.build --labelled corpus\candidates_labelled.jsonl --sensitivity`; `corpus/label_stability.txt` | the sensitivity table and the stability lines |
| 4 | 3.4x the search effort changes almost nothing: 24 serious errors at depth 6, 22 at 4.5 s, 19 in common | `corpus/analysis_cl_v1_d6.md` and `corpus/analysis_cl_v1_4500ms.md` | the two "Overall" rows; the sentence "200 of 240 moves identical" |
| 5 | one weakness across unrelated openings: king exposure leads the loss table in a Ruy Lopez, a Dutch, a Modern, a Philidor, a Vienna, a Trompowsky and a Danish | `corpus/diagnosis_cl_v1.md`, the seven evaluation rows | the board for cl-170 (`3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w`): ClaudeShark plays Qxe6 for a pawn, Stockfish says Bc3 and after Qxe6 ...h3 the white king is lost |
| 6 | evaluation and search disagree on the root cause, and the split is measured: 12 depth, 7 evaluation, 3 pruning, 1 horizon | `uv run python -m tools.corpus.diagnose ...` | the cause table and the ladder column for cl-125 (`d4..d9: 225 225 225 225 225 225`) against cl-000 (`10000 x4, then 0 0`) |
| 7 | the regression says the same thing in numbers: king_open_files -24, king_zone_attackers -16, t about -5 | `corpus/eval_residuals.md` | the quiet-score coefficient table, top six rows |
| 8 | a concrete search defect: the engine sees -9.39 and still refuses the only defence; one flag fixes it | section 18b, st-098 | the terminal output of the two one-liners, then the board |
| 9 | a rare structure breaks the engine: a pure pawn ending mis-evaluated by 4 pawns at every depth | section 18b, st-024 | the board and the ladder line `422 x6` |
| 10 | Fable disagrees with the standing plan: PROJECT.md lists "passed pawns, rook on open file, king safety, mobility, doubled and isolated pawns" in that order; the evidence puts king safety first and doubled/isolated last | section 13 ranking against `PROJECT.md` "Evaluation" bullet | the two lists side by side |

## 20. Reproduction commands (Windows CMD, from the repository root)

```
uv run python -m pytest -q
uv run python -m tools.release_check
uv run python -m tools.corpus.calibrate_legacy --nodes 4000000 --workers 8
uv run python -m tools.corpus.extract --pgn-dir C:\Users\epick\engines\twic --out corpus\candidates.jsonl --min-elo 2300 --niche-min-elo 2100
uv run python -m tools.corpus.label --in corpus\candidates.jsonl --out corpus\candidates_labelled.jsonl --nodes 1000000 --multipv 2 --workers 8
uv run python -m tools.corpus.build --labelled corpus\candidates_labelled.jsonl --sensitivity
uv run python -m tools.corpus.build --labelled corpus\candidates_labelled.jsonl --band 50 --max-gap 100 --max-dev 0.10 --size 240 --per-family 12 --stress-size 120 --seed 1 --out-dir corpus
uv run python -m tools.corpus.analyse --suite corpus\competition_like_v1.jsonl --depth 6 --nodes 1000000 --workers 8 --out corpus\analysis_cl_v1_d6.jsonl
uv run python -m tools.corpus.analyse --suite corpus\competition_like_v1.jsonl --depth 0 --ms 4500 --nodes 1000000 --workers 3 --out corpus\analysis_cl_v1_4500ms.jsonl
uv run python -m tools.corpus.analyse --suite corpus\legacy_v2_calibration.jsonl --depth 6 --nodes 1000000 --workers 2 --out corpus\analysis_legacy_v2_d6.jsonl
uv run python -m tools.corpus.analyse --suite corpus\stress_test_v1.jsonl --depth 6 --nodes 1000000 --workers 6 --out corpus\analysis_st_v1_d6.jsonl
uv run python -m tools.corpus.diagnose --analysis corpus\analysis_cl_v1_d6.jsonl --min-loss 100 --max-depth 9 --ms 4500 --workers 6 --out corpus\diagnosis_cl_v1.jsonl
uv run python -m tools.corpus.diagnose --analysis corpus\analysis_st_v1_d6.jsonl --min-loss 100 --max-depth 9 --ms 0 --workers 6 --out corpus\diagnosis_st_v1.jsonl
uv run python -m tools.corpus.eval_residuals --labelled corpus\candidates_labelled.jsonl --out corpus\eval_residuals.md
uv run python -m pytest -q tests\test_corpus_tools.py
```

The oracle binary: `C:\Users\epick\engines\stockfish\stockfish-windows-x86-64-avx2.exe`
(override with `set ORACLE_ENGINE_PATH=...`). The PGNs:
`C:\Users\epick\engines\twic\twic{1500,1520,1540,1560,1580,1600,1620,1640}.pgn`.
Neither is in the repository. Everything from `label` onward is reproducible
from the tracked JSONL alone; `extract` needs the PGNs; anything that scores
a move needs the binary. Fixed-depth engine runs and fixed-node oracle runs
are deterministic; the 4.5 s run is not.

## 21. Generated artefacts

| path | what |
|---|---|
| `tools/corpus/{oracle,structure,extract,label,build,analyse,diagnose,eval_residuals,suite,calibrate_legacy}.py` | the tooling (nothing ships) |
| `tools/arena.py` | `--corpus` option, suite hash recorded in the match header |
| `tests/test_corpus_tools.py` | 100 tests: tags, opening recognition, dedupe, band filter, selection caps, hand-picked stress legality, shipped-suite invariants, legacy calibration coverage |
| `corpus/README.md` | provenance and the pipeline |
| `corpus/legacy_v2_calibration.{jsonl,md}` | the old suite, labelled |
| `corpus/candidates_labelled.jsonl` | 6,203 labelled master-game positions (the training/validation pool) |
| `corpus/band_sensitivity.md`, `corpus/label_stability.{txt,json}` | the band evidence |
| `corpus/competition_like_v1.{jsonl,md}` | the strength suite, hash `6a8111f22f9ea393` |
| `corpus/stress_test_v1.{jsonl,md}` | the failure suite, hash `591ec2b339da3a42` |
| `corpus/analysis_{legacy_v2_d6,cl_v1_d6,cl_v1_4500ms,st_v1_d6}.{jsonl,md}` | move quality |
| `corpus/diagnosis_{cl_v1,st_v1}.{jsonl,md}` | causes |
| `corpus/eval_residuals.md` | the evaluator regression |
| `benchmarks/current/2026-09-02-fable-corpus-calibration.md` | this record |
| `BENCHMARKS.md`, `PROJECT.md`, `.gitignore` | pointers; `corpus/candidates.jsonl` ignored as regenerable |

## 22. Git state

Nothing pushed, nothing committed. Production engine files untouched
(`git diff --stat` shows only `.gitignore`, `BENCHMARKS.md`, `PROJECT.md`,
`tools/arena.py`; everything else is new). `ruff check .`, `mypy` and the
full suite (791 tests) pass; `tools.release_check` passed at the start on the
unchanged engine and nothing it packages has changed since.

## 18c. How often does the PV cutoff matter? (addendum)

`corpus/analysis_cl_v1_d6_ttpv_off.jsonl`: the whole competition-like suite
at depth 6 with `CS_TT_PV_CUTOFF=0`. Moves change on 3 of 240 positions (one
clearly better, one clearly worse, one neutral), serious errors 24 both ways,
nodes +0.7%. So the st-098 defect is real but rare on level positions; it
surfaces when the side to move is in trouble and a stale table bound hides
the only defence. Worth a targeted red team on lost-but-holdable positions
(the stress suite's `only_move` reason is the right pool), not a blanket
flag flip on this evidence.
