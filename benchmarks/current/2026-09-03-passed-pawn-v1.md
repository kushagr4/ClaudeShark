# Passed pawns v1: one rank-indexed bonus, chosen once, inconclusive in play

**Date:** 2026-09-03. **Baseline:** `champions/v0_5_2_correctness`
(`6eee6bd9b5e58e29`). **Candidate:** `champions/v0_8_passed`
(`074f6f20d4d157a1`), the working tree with `CS_EVAL_PASSED` defaulting on.
**Production default:** off.

**Decision: INCONCLUSIVE at Gate 2, kept flag-gated, default off.** Every
deterministic gate moved the right way and no control worsened, but 200 paired
fixed-depth games score +2 Elo with a cluster bootstrap of -26..+30. The
deterministic evidence is what the audit predicted; the game evidence neither
confirms nor refutes it. Not promoted, not arena-tested.

**The one hypothesis tested.** Adding the single fact "this pawn is passed",
weighted by relative rank and phased through the existing taper, improves
endgame evaluation and playing strength. Nothing else was added: no defender
or attacker king distance, no square rule, no connected, protected, blocked or
candidate passers, no king activity, no breakthrough or race logic, no search
change. The design was narrowed to this after an independent red-team review
of the wider proposal in the blind-win audit.

## 1. Repository verification

Started at `f20a4088f8a5877cb39e4159a4e5ca7060fbbc5f` = `origin/main`, working
tree clean, repository-local identity `kushagr4 <ratrakushagra@gmail.com>`.
Production evaluator identical to v0.5.2 except the two dormant hooks (king
safety, mop-up), both default off; mop-up left exactly as it was.

## 2. Evidence re-verified before implementation

Recomputed from `corpus/blindwin/03_gap.jsonl`, by row and by unique FEN, as
the red-team asked (129 rows, 115 unique positions, 57 source-game clusters):

| statistic | by row (129) | by unique FEN (115) |
|---|---|---|
| production static at the episode | -4 | +4 |
| depth-6 root | +31 | +35 |
| Stockfish (1M nodes) | +429 | +427 |
| passer on rank 6-7 at the PV end: n / gap | 13 / +665 | 11 / +664 |
| pawn ending at the PV end: n / SF / static | 18 / +616 / +4 | (feature table below) |

The root quiescence mean (+30) is from `04_search_probe.txt` and was not
recomputed. The duplicate rows are the same position reached in both colours'
games of a pair, so the unique-FEN figures barely move; the row count is still
the wrong headline and is not used as one below.

## 3. Flagship expectations, stated up front

| cluster | FEN | role for v1 | why |
|---|---|---|---|
| 31 | `8/5k2/7p/5p2/3K1P2/4P3/8/8 b - - 1 62` | **target** | Black already has a passed h-pawn; `h6h5` advances it |
| 45 | `8/8/p4pp1/1p1p1k1p/1P3P1P/2P2K2/1P4P1/8 w - - 0 38` | adversarial control | no passer at the root; the win is breakthrough and opposition timing |
| 14 | `8/4k3/K3p1p1/1p2Pp1p/1P5P/P1P3P1/8/8 b - - 0 38` | adversarial control | no passer at the root; breakthrough and a mutual race |

A material worsening on either control would be a warning; an unchanged
result there is not a failure.

## 4. Detector

Definition: a pawn is passed when no enemy pawn stands ahead of it on its own
file or either adjacent file, "ahead" being colour-correct. Enemy pawns level
or behind do not disqualify it; pieces in the path are ignored.

`cs_passed.py` has three layers:

* `is_passed` / `passed_pawns_reference` -- the definition written out over
  `scan_forward`, per square, with the doubled rule as a second explicit test.
  Not used in search.
* `passed_pawn_mask` / `passed_pawns_packed` -- bitboard fills: the enemy pawn
  set is filled toward the pawn's own back rank (three shifts), widened one
  file each way, and complemented; the same fill of the side's own pawns gives
  the doubled test. No per-pawn loop until the passer set, which is usually
  empty, is read against the rank table.
* a pawn-structure cache keyed on the two pawn bitboards, because the fills
  cost as much as the loop they replaced (Python integer ops, not iteration,
  were the expense). The value is a pure function of the key, so the cache
  cannot change any result.

**Doubled passers:** only the most advanced passed pawn on a file is scored.
This is a counting rule, not a doubled-pawn feature.

## 5. The feature

`PASSED_MG[r]`, `PASSED_EG[r]` by relative rank, added to the evaluator's
packed mg/eg total before the taper, so it is phased exactly like the
piece-square tables with no cutoff. Shipped values (family member A, see §7):

| relative rank | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|
| MG | 0 | 2 | 4 | 8 | 16 | 28 |
| EG | 4 | 8 | 16 | 32 | 56 | 88 |

Double-counting discipline: the PeSTO endgame pawn table already climbs about
165 cp from the second rank to the seventh, so the term is a conditional
adjustment on top of that (88 cp at most in the endgame), not a replacement.

## 6. Tests

`tests/test_passed.py`, 25 tests: enemy pawn ahead on the same file, on
either adjacent file, level, behind, two files away; the mirrored definition
for Black; a-file and h-file; doubled passers scored once and as the front
pawn; connected passers as two; own-piece and enemy-piece blockers ignored;
multiple passers add; an en-passant target square does not change the
definition; no passers in a normal middlegame; both tables monotonic and zero
off the board; a further-advanced passer never scores less; colour mirroring
negates the term; fast and reference agree on 400 random-play positions and
about 2,600 random legal pawn placements; the full evaluators agree and stay
symmetric with the flag on; the flag adds exactly the tapered term (whole
endgame value at phase 0, interpolated with two queens on) and nothing to a
passer-free position; the shipped default is off; the seventh-rank value stays
under a pawn and a half. Every FEN passes the fixture-hygiene scan. Full
suite: 1,042 tests pass.

## 7. Coefficient selection: predefined family, diagnostic half only, chosen once

Family fixed before any of it was run (`tools/passed/sweep.py`), all monotonic:

| member | MG ranks 2..7 | EG ranks 2..7 |
|---|---|---|
| off | 0 | 0 |
| A_small | 0 2 4 8 16 28 | 4 8 16 32 56 88 |
| B_medium | 0 4 8 14 26 44 | 6 12 24 48 84 132 |
| C_large | 0 6 12 20 36 60 | 8 16 32 64 112 176 |
| L_linear | 0 5 10 15 20 25 | 15 30 45 60 75 90 |

Run at depth 6 on the 36 diagnostic rows (36 unique positions, 23 source-game
clusters) of `corpus/blindwin_regression_v1.jsonl` (`9caeda378f88ed58`).
The validation half was not read. `corpus/passed/02_sweep.txt`:

| member | robust (row) | robust (cluster-weighted) | serious | catastrophic | agree | rows still < +100 at the root | PV-end gap closed |
|---|---|---|---|---|---|---|---|
| off | 124.0 | 130.8 | 27.8% | 25.0% | 52.8% | 36/36 | 2% |
| **A_small** | **88.7** | **81.4** | 25.0% | **13.9%** | **61.1%** | 30/36 | 4% |
| B_medium | 117.8 | 116.1 | 30.6% | 22.2% | 55.6% | 25/36 | 5% |
| C_large | 118.1 | 106.0 | 30.6% | 22.2% | 55.6% | 25/36 | 7% |
| L_linear | 118.6 | 119.6 | 27.8% | 22.2% | 55.6% | 28/36 | 7% |

A_small is the best member and the smallest, so the fewer-degrees-of-freedom
rule and the numbers agree. Chosen once; frozen; only then was validation run.
Five rows separate the members (bw-018, bw-025, bw-055, bw-065, bw-031); the
larger tables lose two of them the small one keeps, which is the size of the
sample talking as much as the tables.

## 8. Validation, read once, and the limitation

`corpus/passed/01_baseline_blindwin.txt` (baseline, an independent rerun that
reproduces the sweep's "off" row exactly) and `04_candidate_blindwin.txt`:

| half | rows / clusters | robust row: base -> cand | robust cluster: base -> cand | serious | catastrophic | agree | moves changed (better / worse) |
|---|---|---|---|---|---|---|---|
| diagnostic | 36 / 23 | 124.0 -> 88.7 | 130.8 -> 81.4 | 27.8% -> 25.0% | 25.0% -> 13.9% | 52.8% -> 61.1% | 10 (6 / 3) |
| validation | 32 / 24 | 148.5 -> 123.3 | 142.0 -> 115.3 | 34.4% -> 28.1% | 28.1% -> 21.9% | 62.5% -> 65.6% | 6 (3 / 2) |

By verdict, validation: blind 150 -> 174 (one row, bw-024, `d7e8` 0 -> `b3c2`
334), partly 143 -> 48, horizon unchanged. By mechanism, validation: wins
pawn(s) 194 -> 52, quiet 84 -> 126, king activity and promotion race unchanged.

**The validation half is not independent evidence that passed-pawn evaluation
helps.** It comes from the same 400 self-play games, the same engine's
failures, the same episode-selection rule (Stockfish >= +300, root < +100) and
the same oracle budget as the diagnostic half; the split is by source-game
parity, which removes position overlap but not the shared selection bias.
Three of the six validation changes are the same positions as conversion-suite
rows (cv-007, cv-027, cv-080). It says the tables did not overfit the 36 rows
they were chosen on; it does not say the feature is strong. Only Gate 2 can.

## 9. What the term actually does: the static gap barely closes

`corpus/passed/09_static_gap_all_episodes.txt`, all 129 episodes, static at
the end of Stockfish's line, descriptive and after freezing:

| set | static at PV end: base -> cand | gap (SF - static): base -> cand | gap by cluster | PV-end static < +100 |
|---|---|---|---|---|
| rows (129) | +148 -> +160 | +392 -> +380 | +412 -> +398 | 65 -> 57 |
| unique FEN (115) | +147 -> +159 | +386 -> +374 | +412 -> +398 | 59 -> 53 |
| passer on rank 6-7 (13) | +77 -> +135 | +657 -> +600 | | |
| pawn endings (18) | +12 -> +24 | +604 -> +592 | | |

The term supplies about 3% of the missing evaluation, 9% where a passer stands
on the sixth or seventh. The move improvements in §8 and §10 are therefore not
the static "seeing the win"; they are the search following a gradient that
now prefers to keep, create and advance a passer. Cluster 14 is the clearest
case: the candidate plays the winning `g6g5` at every depth while its root
still says -271. That is the honest reading of v1, and it bounds what any
rank-only term can do.

## 10. Gate 1

**A. Conversion regression suite** (`corpus/conversion_regression_v1.jsonl`,
`1a3de886a87db970`; `corpus/mopup/06_regression_baseline.txt` vs
`corpus/passed/05_regression_candidate.txt`): 21 of 90 moves changed, 16
better, 5 worse, net -1,752 cp.

| role | source | n | base robust / serious / catast | cand robust / serious / catast |
|---|---|---|---|---|
| diagnostic | ALL | 43 | 226.2 / 81.4% / 27.9% | **180.6 / 69.8% / 18.6%** |
| diagnostic | blind | 6 | 114.7 / 33.3% / 16.7% | 32.0 / 16.7% / 0% |
| diagnostic | first_error | 19 | 290.8 / 94.7% / 42.1% | 225.0 / 78.9% / 26.3% |
| diagnostic | defence | 12 | 233.3 / 100% / 16.7% | 216.0 / 91.7% / 16.7% |
| validation | ALL | 47 | 205.4 / 63.8% / 29.8% | 209.8 / 68.1% / 29.8% |
| validation | blind | 7 | 94.7 / 14.3% / 14.3% | 23.3 / 0% / 0% |
| validation | first_error | 23 | 224.3 / 73.9% / 34.8% | 224.2 / 78.3% / 34.8% |
| validation | defence | 12 | 235.2 / 83.3% / 25.0% | 252.8 / 91.7% / 25.0% |
| validation | missed_mate | 3 | 333.3 / 66.7% / 66.7% | 500.0 / 100% / 100% |

The diagnostic half shares three positions with the blind-win diagnostic half
(cv-021, cv-026, cv-074), so its gain is partly the same gain. Validation is
flat: the blind rows improve, defence and first-error rows give some back. The
missed-mate row is cv-038, `5Q2/8/p5K1/1p6/kP6/8/8/8 w`: both engines score
+937, the baseline keeps the oracle's forced mate, the candidate's `f8d6`
drops it to +1242, still trivially won, counted as a 500 cp loss by the
winsorised metric. No passer exists at that root; the term acted inside the
tree.

**B. 240-position root suite** (`corpus/passed/analysis_cl_v1_d6_baseline.jsonl`,
a fresh baseline run that matches the retained one to 0.06 cp, vs
`analysis_cl_v1_d6_passed.jsonl`; `10_root_suite_comparison.txt`):

| | agree | within 25 | robust | serious | catastrophic | nodes |
|---|---|---|---|---|---|---|
| base | 37.1% | 65.8% | 35.3 | 10.0% | 1.7% | 20,047,682 |
| cand | 39.2% | 65.8% | 34.0 | 10.0% | 1.7% | 20,116,598 |

29 of 240 moves changed: 14 better, 10 worse, 5 same, net -302 cp. By bucket
the endgame rows without a mover's passer got slightly worse (13.4 -> 19.3 and
11.6 -> 23.5, on 19 and 14 rows) and the middlegame rows where the opponent
has a passer got better (106.5 -> 81.1 on 22). Screening only; it cannot see
what v0.6 did.

**C. Blind-win suite**: §8.

**D. Depth ladders, candidate** (`06_flagship_ladder.txt`,
`07_persisting_ladder.txt`, `11_persisting_ladder_summary.txt`):

| cluster | role | baseline d6..10 (loss) | candidate d6..10 (loss) | candidate root d6 / d10 |
|---|---|---|---|---|
| 31 | target | f7e6 519, then h6h5 2 (A +1 ply) | **unchanged**: f7e6 519, then h6h5 2 (A +1 ply) | +15 / +262 (was +15 / +47) |
| 45 | control | b2b3 442 at every depth (D persists) | b2b3 to depth 9, **g2g4 0 at depth 10** (C deeper) | +9 / +14 |
| 14 | control | e7d7 933, e7f7 889 (D persists) | **g6g5 4 at every depth** | -271 / -298 |

The target is not fixed at depth 6; the candidate believes the win more
deeply once it finds `h6h5`, and finds it one ply later exactly as before.
Neither control worsened; both improved, which was not required and is
noted, not claimed. Of the 18 unique positions that persisted at depth 10 in
the audit: 1 now fixed at every depth, 2 fixed deeper, 2 unstable, 13 still
persist; the depth-6 loss improved by more than 20 cp in 4 and worsened in 0;
13 of 18 still have a root under +100 at depth 10.

**E. Runtime** (`03_cost.txt`): evaluator micro-benchmark 3.84 -> 3.99 us per
call cache-hot (+4%); depth-6 search on the 42 bench positions 56,246 NPS
off, 56,310 on, 24,940 pawn structures cached over 3.56M nodes: no measurable
search cost. The first fill-based version without the cache cost +53% per
evaluation, the per-pawn loop the same; the cost is Python integer
arithmetic, and the cache is what makes the term affordable.

## 11. Gate 2: 200 fixed-depth paired games

`champions/v0_8_passed` vs `champions/v0_5_2_correctness`, the 100 starting
positions of `corpus/postmortem/pairs.json` both colours, depth 6, 300-ply
cap, `--draw-claim auto`, no `CS_*` variable in the environment. Raw games
with every move: `corpus/passed/games/gate2_fixed_depth.jsonl`, the same
games as `gate2_fixed_depth.pgn`; Stockfish annotation `gate2_annotated.jsonl`;
`12_gate2_report.txt`, `13_gate2_summary.txt`.

    +35 =131 -34   score 50.2%   Elo +2
    naive 95% CI -46 .. +50   paired cluster bootstrap -26 .. +30 (100 clusters)
    terminations: threefold 129, checkmate 69, insufficient material 2
    failures: 0

**Annotated move quality** (`12_gate2_report.txt`): candidate robust loss
39.9 on 4,827 moves against the baseline's 39.4 on 4,814; games with a
serious error 137 vs 140; first serious error by the candidate in 70 games,
by the baseline in 62, neither in 55. Static calibration against Stockfish:
Pearson r 0.682 vs 0.671.

**Conversion and defence** (first time a threshold is reached, from the
engine's side):

| | cand won / drew / lost | base won / drew / lost | cand held | base held |
|---|---|---|---|---|
| ahead >= +200 | 47.9% / 42.5% / 9.6% (n 73) | 41.0% / 50.6% / 8.4% (n 83) | | |
| ahead >= +300 | 52.2% / 40.3% / 7.5% (n 67) | 43.6% / 48.7% / 7.7% (n 78) | | |
| behind <= -200 | | | 59.0% (n 83) | 52.1% (n 73) |
| behind <= -300 | | | 56.4% (n 78) | 47.8% (n 67) |

Both directions favour the candidate, on samples of 70-80 games each, and
the match still lands at 50.2%: the candidate reaches +200 less often (73
games against 83) and falls to -200 more often, so it converts and holds
better from positions it enters less favourably. Recovery after the
opponent's first serious error: won 25.0% vs 24.8%.

**Targeted metric** (`13_gate2_summary.txt`): Stockfish loss of every
annotated move, by the mover's most advanced passer.

| bucket | cand n / loss / serious | base n / loss / serious |
|---|---|---|
| no own passer | 2,578 / 37.0 / 10.0% | 2,582 / 37.1 / 10.5% |
| passer rank 2-4 | 849 / 38.8 / 10.1% | 1,089 / 41.3 / 11.2% |
| passer rank 5-6 | 1,021 / 47.2 / 13.6% | 950 / 44.7 / 12.1% |
| passer rank 7 | **379** / 42.9 / 13.5% | **193** / 33.1 / 8.8% |
| middlegame, passer rank 7 | 70 / 66.1 / 20.0% | 41 / 44.6 / 7.3% |

The bucket the term cannot reach is unchanged, as it should be. The
candidate plays in seventh-rank-passer positions twice as often and plays
worse in them; in the middlegame the serious-error rate there nearly
triples on a small sample. At ply 60 the candidate held the more advanced
passer in 26 games and scored 13 wins, 8 draws, 5 losses; the baseline held
it in 21 and scored 9 wins, 11 draws, 1 loss (an earlier version of this
record and of the summary tool counted the baseline's draws as wins and
printed 20/0/1; corrected in the failure audit). **The term makes the engine
create and push passers it does not know how to use.** A rank bonus with no
notion of whether the pawn can be stopped by a king or a piece rewards the
advance itself, and the search obliges. This is the mechanism by which the
deterministic gains and the neutral match coexist, and it is exactly the
information the red-team removed from v1: it belongs in a v2 measured
against this record.

## 12. Decision: INCONCLUSIVE, keep flag-gated, default off

Classification rule: KEEP requires the bootstrap to exclude zero on the
right side or a targeted metric to move decisively with the match at least
neutral; REVERT requires a deterministic regression or a bootstrap excluding
zero on the wrong side; anything else is INCONCLUSIVE. Here the deterministic
gates are positive on the targeted suite, neutral-to-positive on the root
suite, flat on conversion validation, the controls are no worse, and the
match is +2 with -26..+30. Inconclusive.

What would settle it: another 200 paired games from fresh starting positions
(the bootstrap width halves at 400 games only if the effect is real), or the
arena, which the rules reserve for a clear Gate 2. Not run.

What was learned regardless: a rank-only passer bonus is a *gradient*, not
*knowledge*, and in play the gradient cuts both ways: the candidate converts
+200 into a win 47.9% of the time against 41.0% and holds -200 59.0% against
52.1%, yet reaches seventh-rank passers twice as often and errs there more
(§11). It advances pawns it cannot use. It closes 3% of the static gap and still changes a quarter of the
suite's moves for the better, because the endgame search had nothing to steer
by. The remaining 97% of the gap -- the pawn endings at +12, the persisting
13 of 18 -- is where the king-distance and square-rule terms the red-team
removed from v1 would act, and they should be proposed as v2 only with this
record as their baseline, one at a time.

## 13. RECORD THIS

1. **The sweep table** (`corpus/passed/02_sweep.txt`, first table): the
   smallest member wins, the others barely beat off. Show the "off" row and
   the "A_small" row side by side: 124.0 -> 88.7, catastrophic 25% -> 14%.
2. **The static gap that does not close** (`09_static_gap_all_episodes.txt`):
   +392 -> +380 by row. Then the diff (`08_blindwin_diff.txt`): 16 moves
   changed anyway. The feature works as a gradient, not as understanding.
3. **Cluster 14, the control that got fixed while believing it is losing**:
   `8/4k3/K3p1p1/1p2Pp1p/1P5P/P1P3P1/8/8 b - - 0 38`. Run
   `uv run python -m tools.conversion.depth --engine champions\v0_8_passed --cases corpus\passed\flagship_cases.json --depths 6,7,8,9,10 --out %TEMP%\l.txt`
   and show the cluster 14 block: `g6g5` at every depth, root -271..-298.
4. **The target that is not fixed**: cluster 31,
   `8/5k2/7p/5p2/3K1P2/4P3/8/8 b - - 1 62`, same command, same block: `f7e6`
   at depth 6 with or without the term. A passed-pawn bonus that does not
   push the passed pawn.
5. **Gate 2 at +2 with -26..+30** (`13_gate2_summary.txt` header): the
   deterministic gates said yes, the games said nothing. Contrast with v0.6
   (deterministic yes, games -40).
6. **The evaluator cost story** (`03_cost.txt`): loop version +53%, fill
   version +53%, cached version +4%. Python bit arithmetic is the cost, not
   iteration.
7. **Passers it cannot use** (`13_gate2_summary.txt`, last two blocks): the
   candidate holds the better passer at ply 60 in 26 games and scores
   13/8/5; the baseline holds it in 21 and scores 9/11/1 (loses less, wins
   less). The sharper shot is the rank-7 row of the table above them: 379
   moves at 42.9 vs 193 at 33.1, and the failure audit's 27% vs 14.5%
   serious-error rate when ahead with a passer on the seventh.

## 14. Reproduction (Windows CMD, from the repository root)

    uv run python -m pytest tests\test_passed.py -q
    uv run python -m tools.profile_eval --repeats 300
    set CS_EVAL_PASSED=1 && uv run python -m tools.profile_eval --repeats 300 && set CS_EVAL_PASSED=
    uv run python -m tools.passed.cost --depth 6 --out corpus\passed\03_cost.txt
    uv run python -m tools.blindwin.run --suite corpus\blindwin_regression_v1.jsonl --engine champions\v0_5_2_correctness --depth 6 --role all --out corpus\passed\01_baseline_blindwin.txt
    uv run python -m tools.passed.sweep --scratch %TEMP%\cs_passed --depth 6 --workers 5 --out corpus\passed\02_sweep.txt
    uv run python -m tools.blindwin.run --suite corpus\blindwin_regression_v1.jsonl --engine champions\v0_8_passed --depth 6 --role all --out corpus\passed\04_candidate_blindwin.txt
    uv run python -m tools.conversion.suite run --suite corpus\conversion_regression_v1.jsonl --engine champions\v0_8_passed --depth 6 --out corpus\passed\05_regression_candidate.txt
    uv run python -m tools.conversion.depth --engine champions\v0_8_passed --cases corpus\passed\flagship_cases.json --depths 6,7,8,9,10 --out corpus\passed\06_flagship_ladder.txt
    uv run python -m tools.conversion.depth --engine champions\v0_8_passed --cases corpus\passed\persisting_cases.json --depths 6,7,8,9,10 --out corpus\passed\07_persisting_ladder.txt
    uv run python -m tools.corpus.analyse --suite corpus\competition_like_v1.jsonl --depth 6 --workers 3 --engine champions\v0_5_2_correctness --out corpus\passed\analysis_cl_v1_d6_baseline.jsonl
    uv run python -m tools.corpus.analyse --suite corpus\competition_like_v1.jsonl --depth 6 --workers 3 --engine champions\v0_8_passed --out corpus\passed\analysis_cl_v1_d6_passed.jsonl
    uv run python -m tools.passed.compare_root --base corpus\passed\analysis_cl_v1_d6_baseline.jsonl --cand corpus\passed\analysis_cl_v1_d6_passed.jsonl --out corpus\passed\10_root_suite_comparison.txt
    uv run python -m tools.postmortem.play --cand champions\v0_8_passed --base champions\v0_5_2_correctness --pairs corpus\postmortem\pairs.json --depth 6 --workers 4 --out corpus\passed\games\gate2_fixed_depth.jsonl
    uv run python -m tools.postmortem.annotate --games corpus\passed\games\gate2_fixed_depth.jsonl --out corpus\passed\games\gate2_annotated.jsonl --workers 8
    uv run python -m tools.postmortem.report --games corpus\passed\games\gate2_annotated.jsonl --out corpus\passed\12_gate2_report.txt
    uv run python -m tools.passed.gate2 --games corpus\passed\games\gate2_annotated.jsonl --out corpus\passed\13_gate2_summary.txt
    uv run python -m tools.postmortem.to_pgn --games corpus\passed\games\gate2_fixed_depth.jsonl --out corpus\passed\games\gate2_fixed_depth.pgn --cand-name v0_8_passed --base-name v0_5_2_correctness

To play with the term on from the working tree: set `CS_EVAL_PASSED=1`.

## 15. Artefacts

`cs_passed.py` (production module, flag-gated off); `cs_eval.py` (hook, both
evaluators); `tests/test_passed.py`; `tools/blindwin/run.py`;
`tools/passed/{sweep,compare_root,gate2,cost}.py`;
`champions/v0_8_passed/` (`074f6f20d4d157a1`);
`corpus/passed/01_baseline_blindwin.{txt,jsonl}`, `02_sweep.{txt,json}` and
`sweep_*.{txt,jsonl}`, `sweep_*_gap.json`, `03_cost.txt`,
`04_candidate_blindwin.{txt,jsonl}`, `05_regression_candidate.{txt,jsonl}`,
`06_flagship_ladder.{txt,json}`, `07_persisting_ladder.{txt,json}`,
`08_blindwin_diff.txt`, `09_static_gap_all_episodes.txt`,
`10_root_suite_comparison.txt`, `11_persisting_ladder_summary.txt`,
`12_gate2_report.txt`, `13_gate2_summary.txt`,
`analysis_cl_v1_d6_{baseline,passed}.jsonl`, `flagship_cases.json`,
`persisting_cases.json`, `games/gate2_fixed_depth.{jsonl,pgn}`,
`games/gate2_annotated.jsonl`.
