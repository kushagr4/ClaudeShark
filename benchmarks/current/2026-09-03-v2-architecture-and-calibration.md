# V2 start: evaluation architecture, the endgame calibration set, and the root-cause map

**Date:** 2026-09-03/04. **Branch:** `v2-development` from `98c48c8` (tag
`rated-v1`, which is untouched). **No engine behaviour changed:** the
depth-6 fingerprint is 1,712,405 nodes before and after, every shipped
default is off, and the rated V1 build is the fallback.

**Recommendation in one line:** the first V2 feature should be *endgame
king-to-pawn proximity* -- one endgame-weighted table by the king's distance
to the nearest pawn, both kings, symmetric -- because it is the only cheap
single feature whose sign agrees with both failure directions on the new
calibration set, and because the root-cause map puts "where the kings stand
relative to the pawns" at the centre of the largest coherent static
deficiency in both blind wins and false wins. Its expected static effect is
small (it closes about 4% of the blind-win gap and 12% of the false-win
excess on validation); the case for it is direction and reach, not
magnitude, and the experiment design below is built to catch the V1 failure
mode (a gradient the engine follows into positions it cannot play).

## 1. Current evaluator anatomy (rated V1)

`cs_eval.evaluate` is one flat function: twelve unrolled bitboard scans over
packed PeSTO tables (material folded in, `(mg << 16) + eg` per square), a
bishop-pair pair, one split of the packed total, a linear taper on the 0..24
phase with truncation toward zero, tempo. About 3.85 us per call, 52-58k
NPS at depth 6. Beside it, three optional terms existed as three `if FLAG:`
branches at three different places in the function: king safety added to
the middlegame half after the split, mop-up added after the taper in whole
centipawns, passed pawns added to the packed total before the split. Each
had its own environment variable read at import, its own test file, and its
own way of being toggled by tools (`cs_eval.USE_*` assignments and source
patches of the flag line). Nothing shared a test for antisymmetry,
fast/reference agreement or non-interaction.

## 2. V2 evaluator architecture (implemented; trivial and required)

`cs_terms.py` is a registry: `Term(name, flag, stage, fast, reference)` plus a
`DEFAULTS` table that is the only place a term is shipped. Two stages,
because the three existing terms needed exactly two: `packed` (an mg/eg pair
added before the taper, phased like the tables; a middlegame-only term packs
`mg << 16`, numerically identical to the old post-split addition) and `post`
(whole centipawns after the taper, for the mop-up, whose gradient must not
be diluted and which is *not* equivalent to `packed` with mg = eg because
of the truncating division). `cs_eval` keeps two tuples of active fast
functions and two of reference functions; the fast path is

    if _PACKED_TERMS:
        for term in _PACKED_TERMS: packed += term(board)
    ...
    if _POST_TERMS:
        for term in _POST_TERMS: score += term(board)

so an empty registry costs two falsy checks and the node count is
unchanged. `cs_eval.set_terms(names)` / `set_term(name, on)` change the
active set at runtime for tests and tools; the three `USE_*` names survive
as read-only mirrors. The environment selects terms per flag
(`CS_EVAL_PASSED=1`) or as a list (`CS_EVAL_TERMS=passed,mopup`), read once.

What a new term gets for free: `tests/test_terms.py` (antisymmetry under
mirroring, fast = reference on random positions, "on adds exactly this term
at its stage", non-interaction, full-evaluator symmetry with everything on,
default off), `tests/conftest.py` (no test can leak an active term), and
`tools/v2/termbench.py` (evaluator cost, depth-6 NPS in a fresh process,
activation frequency and contribution size on the calibration set and on
every position of a retained game file, and the static-vs-Stockfish table
by class with the term off and on). Not built, on purpose: no per-term
weights table, no fitting harness, no term composition language. One term
is a module with two functions and two registry lines.

Verification: `ruff` clean; 1,062 tests (20 new); release check READY with
the registry module packaged; `tools.bench --depth 6` = 1,712,405 nodes;
`profile_eval` 3.97 us with the registry empty against 3.84-3.86 before
(inside run-to-run noise on this machine).

**The registry measured on the term V1 already has**
(`corpus/v2/termbench_passed.txt`, `tools/v2/termbench.py --term passed`):
evaluator 3.96 -> 4.34 us cache-hot (+8.7%), depth-6 NPS 55,452 -> 54,352
(+2.0%), active on 68.5% of calibration positions and 68.7% of all 9,641
positions of the passed-pawn Gate 2 games, mean contribution 32 cp when
active, maximum 176. Static against Stockfish by class, off -> on: blind
wins MAE 526 -> 528, **false wins 266 -> 293**, recognised draws 91 -> 99,
controls 50 -> 57. The one term V1 tried moves the false-win class the
wrong way and the blind-win class not at all, which is the failure audit's
conclusion measured on the new set, and the reason the brief's "do not
simply increase passed-pawn bonuses" is now a number. (This tool reports
static without the tempo term; the suite runner reports the engine's own
static, tempo included, so the two differ by a constant.)

## 3. The V2 endgame calibration set

`tools/v2/calibration.py` -> `corpus/v2/endgame_calibration_v1.jsonl`
(`a473da0823abf75c`). Sources: every retained annotated fixed-depth game in
which rated V1 was to move (the v0.6 post-mortem set, the mop-up Gate 2, the
passed-pawn Gate 2: 600 games), the blind-win episode file, the labelled
competition-like suite for middlegame controls, the tactics fixtures for
tactical controls. Classes from the side to move, endgame and its
approaches (phase <= 12 of 24) for the five game-derived classes:

| class | definition |
|---|---|
| blind_win | Stockfish >= +300, V1 root < +100 |
| false_win | V1 root >= +200, Stockfish within +-50 at the position and after the move actually played |
| recognised_win | both >= +300 |
| recognised_draw | both within +-50, phase <= 8 |
| losing | Stockfish <= -300 |
| control_middle | level middlegame positions, 240 suite |
| control_tactic | the 16 tactics fixtures |

Exact FENs deduplicated (1,433 harvested rows -> 1,162 unique). A trajectory
is one game; at most two positions per class per game, at least six plies
apart, largest disagreement first. The failure classes are kept whole; the
three recognised/losing classes are capped at one position per trajectory
and a deterministic sample of 100, so the easy cases do not outnumber the
hard ones four to one. Split by source and cluster parity, so both games of
a pair land on one side. Every position relabelled by the oracle at 1M
nodes and rescored by rated V1 from a fresh searcher: static, root
quiescence, depth-6 root, move and PV.

## 4. Dataset statistics

550 unique FENs, 387 independent trajectories, hash `a473da0823abf75c`.

| class | rows | traj | diag / valid | SF | V1 static | V1 qs | V1 root | endgame | pawn end | rook end | own passer | their passer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| blind_win | 170 | 135 | 73 / 97 | +540 | +28 | +63 | +36 | 78% | 12% | 18% | 61% | 45% |
| false_win | 40 | 24 | 24 / 16 | +1 | +266 | +295 | +301 | 98% | 10% | 35% | 60% | 45% |
| recognised_win | 100 | 100 | 48 / 52 | +1837 | +1131 | | | 98% | 3% | 12% | 52% | 32% |
| recognised_draw | 100 | 100 | 45 / 55 | +4 | -50 | -18 | -2 | 100% | 8% | 25% | 49% | 53% |
| losing | 100 | 100 | 42 / 58 | -1521 | -934 | | | 92% | 1% | 6% | 38% | 51% |
| control_middle | 24 | 24 | 10 / 14 | +3 | +6 | +26 | +16 | 0% | | | | |
| control_tactic | 16 | 16 | 8 / 8 | +1243 | +287 | +2332 | | | | | | |

Material signatures, blind wins: KNPPP-KBPPPP, KPPPP-KPPPP, KRBPPPP-KRBPPPP,
KPPP-KPPP, KRP-KRPP; false wins: KBPP-KBPPP (5), KRPPP-KRP (4), KRP-KRP (3),
KR-KRB, KPP-KR, K-KP, KP-K, KP-KQ. King geometry: in blind wins *our* king
is nearer the pawns than theirs (1.21 vs 1.52); in false wins *their* king
is nearer (1.02 vs 1.40); in recognised draws the two are equal (1.33 vs
1.37). Full table: `corpus/v2/endgame_calibration_v1.txt`. Rated V1 on the suite
(`corpus/v2/04_suite_v1_static.txt`, static only): blind wins sit +511
below Stockfish (152 of 170 rows under +100), false wins +265 above (30 of
40 rows at or above +200); diagnostic half +537 / +302, validation half
+492 / +209.

## 5. Blind wins versus false wins

Blind wins are common and large: 135 trajectories, V1 static +28 where
Stockfish says +540, quiescence and depth-6 search add almost nothing
(+63, +36). False wins, as strictly defined, are rare: 24 trajectories in
600 games, V1 root +301 where Stockfish says +1, and the static already
carries the whole excess (+266). The two classes are mirror images in the
king table above and share one structural fact: passed pawns are present in
60% of both. What differs is what the passer means. In the blind wins the
winning side's king is already among the pawns and the line goes on to use
it; in the false wins the *defending* king is among the pawns and holds
them (KRPPP-KRP with the b-pawn blockaded, KBPP-KBPPP with opposite bishops,
K-KP with the wrong rook pawn, KRB-KR, KP-KQ). A term that scores the passer
alone moves both classes the wrong way; a term that scores the king's
relation to the pawns moves both the right way.

## 6. Causal mechanism counts (independent trajectories)

`tools/v2/rootcause.py` -> `corpus/v2/02_rootcause.txt`.

Blind wins, 135 trajectories:

| mechanism | traj | share | SF | V1 root | V1 static |
|---|---|---|---|---|---|
| tactical/horizon | 35 | 26% | +476 | +34 | -29 |
| passed pawn | 30 | 22% | +492 | +32 | +49 |
| king-to-pawn coordination | 20 | 15% | +476 | +52 | +57 |
| other | 18 | 13% | +393 | +37 | +22 |
| king activity | 18 | 13% | +435 | +52 | +20 |
| rook activity | 9 | 7% | +430 | +59 | +14 |
| mating gradient | 9 | 7% | mate | -20 | +222 |
| pawn race / tempo | 7 | 5% | +484 | +32 | -36 |
| rook + passer coordination | 6 | 4% | +407 | +40 | +50 |
| extra-pawn conversion | 5 | 4% | +420 | +62 | -5 |
| pawn breakthrough | 3 | 2% | +455 | -96 | -12 |

False wins, 24 trajectories:

| mechanism | traj | share | V1 static |
|---|---|---|---|
| extra-pawn conversion (drawn material: KP-KQ fortress, KPP-KR, rook endings a pawn up) | 7 | 29% | +355 |
| blocked/stoppable passer | 5 | 21% | +304 |
| opposite bishops / fortress | 4 | 17% | +248 |
| king activity (defender's king among the pawns) | 4 | 17% | +57 |
| mating gradient (KRB-KR, KR-KRB) | 3 | 12% | +299 |
| wrong rook pawn | 1 | 4% | +227 |

## 7. The largest remaining static-evaluation weakness

Grouping the map by what a static term would have to know: *king geometry
relative to the pawns* (king-to-pawn coordination 20, king activity 18,
pawn race 7, breakthrough 3, and the stoppable half of the passer class)
is 38-48 of 135 blind-win trajectories and 9 of 24 false-win trajectories
(blocked passer 5, king activity 4). Tactical/horizon (35) is not static.
Passed pawns as such (30) were tested in V1: the rank bonus moved the
suites and the engine then pushed pawns it could not use, and the failure
audit found the remaining information is whether the pawn can be stopped,
which is again king geometry. Drawn material configurations (KRB-KR,
KP-KQ, wrong rook pawn, opposite bishops: 15 of 24 false-win trajectories)
are the other coherent group, but they touch no blind win.

The direct test, `tools/v2/featurescan.py` -> `corpus/v2/03_featurescan.txt`:
nine cheap single features, one least-squares scale each on the 242
diagnostic rows, read on the 300 validation rows.

| feature | scale (cp/unit, eg-weighted) | failure traj touched | blind below SF | false above SF | sign agreement blind / false |
|---|---|---|---|---|---|
| V1 as is | | | +436 | +209 | |
| **king_pawn_proximity** | +91.6 | 79 | **+420** | **+183** | 56+ / 24- ; 12- / 5+ |
| king_to_enemy_pawns | -0.8 | 114 | +435 | +209 | 56 / 63 ; 17 / 8 |
| king_vs_passer_geometry | +4.9 | 112 | +435 | +204 | 65 / 51 ; 16 / 12 |
| unstoppable_passer (square rule) | -1003 | 2 | +426 | +152 | fires on 2 rows |
| rook_activity | -65.6 | 80 | +441 | +172 | 44 / 32 ; 6 / 11 (wrong sign for blind wins) |
| opposite_bishops | +301 | 3 | +436 | +175 | 3 trajectories |
| king_centralisation (PST control) | +9.2 | 125 | +435 | +205 | 72 / 58 ; 16 / 18 |
| passer_count (V1 control) | +14.9 | 100 | +431 | +207 | 68 / 36 ; 9 / 16 (wrong sign for false wins) |
| pawn_ending_king_race | +33.7 | 15 | +437 | +209 | |

Every R2 is at or below zero: no single linear feature explains the
residual, and none should be expected to when the mean blind-win gap is
+436 cp. What the table does show is which features point the right way in
*both* classes: only king-pawn proximity (blind wins 56 for, 24 against;
false wins 12 for, 5 against). Passer count has the V1 failure written in
it (16 false wins where it says "more"), rook activity likewise for blind
wins, and the square rule, opposite bishops and the pawn-ending race fire
on too few rows to be a first feature.

## 8. Recommended ONE V2.1 feature

**Endgame king-to-pawn proximity.** For each side, an endgame-table bonus
indexed by the Chebyshev distance from that side's king to the nearest pawn
of either colour (distance 1..7; a board with no pawns scores 0), White
minus Black, middlegame value zero, entered as a `packed` term so the taper
phases it out of the middlegame. Interpretation: in the endgame the king is
a piece, and its job is to be where the pawns are, whether to escort its
own or to hold the opponent's. This is the one term the map and the scan
both point at, it rewards the *defending* king as much as the attacking one
(which is what the false wins need), and it is not a passer bonus, a
king-safety term, generic centralisation or aggression.

Not chosen, with the reason: king-versus-passer geometry (square rule)
fires on 2 of 550 rows; rook activity points the wrong way on blind wins;
drawn-material scaling helps 15 false-win trajectories and no blind win;
generic king centralisation is already in the PST and the scan shows it
adds nothing.

## 9. Expected affected population

Non-zero on 47% of blind-win rows and 42% of false-win rows in the
calibration set (79 of 159 failure trajectories); active on essentially
every endgame position in play (any position with pawns and a phase below
24 gets a non-zero value whenever the two kings differ in distance). On
validation, with the fitted scale, it moves the blind-win mean up 16 cp
and the false-win mean down 26 cp; the search will amplify whatever
gradient it supplies, exactly as it did for passed pawns, so the play
effect is the thing to measure, not the static one.

## 10. Likely computational cost

Inputs: two king squares and the pawn bitboard. Distance by ring expansion
of the king-attack mask against the pawn set (one shift-or set per ring,
usually one or two rings) or, cheaper, a cache keyed on (king squares,
pawns) like the passed-pawn cache, hit on almost every node because pawns
and kings move on a minority of plies. Estimate from the passed-pawn
experience: +50% per evaluation uncached, +4% cache-hot, no measurable NPS
change. To be measured with `termbench`, not assumed.

## 11. Exact experiment design (V2.1, not started)

1. Module `cs_kingpawn.py`: `king_pawn_reference(board) -> (mg, eg)` written
   out; `king_pawn_packed(board)` bitboard version with a pawn-structure
   cache; table `KING_PAWN_EG[d]` for d = 1..7, monotonic non-increasing in
   d, `KING_PAWN_MG` all zero. One `Term("king_pawn", "CS_EVAL_KING_PAWN",
   "packed", ...)` line and a `DEFAULTS` entry, off.
2. Gate 0: the registry tests, plus a fixture test that a king walking
   toward a pawn scores monotonically and that pawnless boards score 0.
3. Table family fixed in advance, three members by scale (e.g. peak 20, 40,
   60 cp at distance 1, falling to 0 at distance 5 or 7). Selection on the
   *diagnostic* halves of the calibration set and the blind-win suite,
   static-only first (`tools/v2/suite.py --static-only`, `termbench`), then
   depth-6 move quality on the diagnostic rows; choose once; freeze.
4. Gate 1, read once each: calibration validation half (blind wins up,
   false wins down, recognised draws and controls within noise), blind-win
   suite validation, conversion suite, 240 suite with `compare_root`,
   tactics 16/16, `termbench` cost lines.
5. The V1 failure check before any game: the passed-pawn failure audit's
   seventh-rank episode tool, run on whatever Gate 2 produces, must not
   show the engine reaching a class of positions it then plays worse than
   the baseline; and the false-win class must not have grown.
6. Gate 2: 200 fixed-depth paired games against rated V1, PGN and JSONL
   retained, W/D/L with the cluster bootstrap, conversion and defence
   rates, and the endgame-class targeted metric. Compare against rated V1
   and against v0_8_passed. Classification: keep for confirmation,
   inconclusive (off), revert.
7. Gate 3 only on a clear Gate 2.

## 12. Things explicitly deferred

Drawn-material scaling (KRB-KR, KP-KQ fortress, wrong rook pawn, opposite
bishops): the second-largest coherent false-win group, zero blind-win
reach; a V2.2 candidate with its own record. The square rule and any
passer-stoppability term: too few rows here, and it is the V1 v2 the failure
audit deferred. Rook activity: wrong sign on blind wins in this data.
Tactical/horizon blind wins (26%): search, not evaluation, and search is
not on the V2 agenda. Mating gradient beyond the bare-king mop-up.
Everything in the V1 negative list.

## 13. RECORD THIS

1. **The mirror-image king table** (`corpus/v2/02_rootcause.txt`, king
   geometry block): blind wins our king 1.21 / theirs 1.52; false wins ours
   1.40 / theirs 1.02; draws 1.33 / 1.37. One number tells both stories.
2. **The false-win gallery** (same file, examples): KRB-KR at +372, KP-KQ at
   +718, K-KP wrong rook pawn at +255, KRPPP-KRP blockaded at +458. Put
   `3k4/4R3/8/5K2/4B3/8/4r3/8 w` on the board with the +372.
3. **The scan table** (`corpus/v2/03_featurescan.txt`): every R2 at zero,
   and the two control rows (passer_count, king_centralisation) failing on
   sign exactly where V1 failed.
4. **The fingerprint line** before and after the registry: 1,712,405 both
   times, `uv run python -m tools.bench --depth 6`.

## 14. Artefacts

`cs_terms.py`, `cs_eval.py` (registry hook), `tests/test_terms.py`,
`tests/conftest.py`, `tools/v2/{calibration,rootcause,featurescan,suite,termbench}.py`,
`corpus/v2/endgame_calibration_v1.{jsonl,txt}`, `corpus/v2/02_rootcause.{txt,jsonl}`,
`corpus/v2/03_featurescan.{txt,json}`, `corpus/v2/termbench_passed.txt`;
updated `tests/test_king_safety.py`, `tests/test_mopup.py`,
`tests/test_passed.py`, `tools/mopup/{gradient,sweep}.py`,
`tools/passed/sweep.py`, `pyproject.toml`, `AGENTS.md`, `PROJECT.md`,
`BENCHMARKS.md`.

## 15. Reproduction (Windows CMD, from the repository root)

    uv run python -m pytest tests\test_terms.py -q
    uv run python -m tools.bench --depth 6
    uv run python -m tools.v2.calibration --out corpus\v2\endgame_calibration_v1.jsonl
    uv run python -m tools.v2.rootcause --suite corpus\v2\endgame_calibration_v1.jsonl --out corpus\v2\02_rootcause.txt
    uv run python -m tools.v2.featurescan --suite corpus\v2\endgame_calibration_v1.jsonl --out corpus\v2\03_featurescan.txt
    uv run python -m tools.v2.termbench --term passed --out corpus\v2\termbench_passed.txt
    uv run python -m tools.v2.suite --suite corpus\v2\endgame_calibration_v1.jsonl --engine champions\v0_5_2_correctness --static-only --out corpus\v2\04_suite_v1_static.txt
