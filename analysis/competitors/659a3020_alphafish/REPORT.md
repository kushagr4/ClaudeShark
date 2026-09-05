# Competitor study: AlphaFish (team `659a3020-8af7-4934-b753-3b7c5fd11184`, "Emile Andrieu")

**Date:** 2026-09-05 22:30–23:00 UK (Mac), branch `kushagra/competitor-659a3020-study`,
baseline `origin/rc-c-integration` (exact RC-B). Analysis only; no engine change.

## 1. Sources (all public, no auth, fetched 22:32–22:36 UK)

* `https://aichessathon.com/leaderboard` (ratings after Round 29; Round 30 in
  progress, 138 of 149 games finished; 295 teams) → `leaderboard_*.json`.
* `https://aichessathon.com/team/659a3020-…` → `team_page.html`, `team_games.json`
  (22 games, Rated 9 – Rated 30; the team joined at Round 9).
* `https://aichessathon.com/game/<id>` for all 22 games → `game_<id>.html`,
  `games.jsonl` (PGN with `%clk`, platform Stockfish 16 depth-16 review,
  ladder context). PGNs under `pgn/`, ingested (`alphafish_games.jsonl`) and
  annotated with our oracle (Stockfish 18, 200k / 1M nodes, both sides,
  3,241 labelled moves) → `alphafish_games_annotated.jsonl`.
* ClaudeShark's own 30 public games for the like-for-like numbers →
  `../claudeshark_public/`.
* Earlier snapshot of the same team at 00:12 UTC (rank 20, 1867, 5-1-1) in
  `analysis/refresh_2026-09-05/top50_*`.

## 2. Who they are on the ladder

| | AlphaFish | ClaudeShark v2 |
|---|---|---|
| rank / rating after R29 | **1 / 2216** (was 20 / 1867 at 00:12 UTC) | 109 / 1589 |
| record | 15W 5D 1L through R29, +1W in R30 → **16W 5D 1L, 84.1%** | 12W 7D 10L |
| mean opponent rating (ladder now) | 1936 | ~1590 |
| performance rating vs those opponents | **≈ 2290** | — |
| vs opponents rated ≥ 1970 (n = 14) | **10W 4D 0L (85.7%)**: beat Anchoa (4), Mate in One (3), SoberJackson (6), ms (9), Patzer 1.2 (5), checkers (10), test_bot (8), Loss Preventer (15), lyra (12), make_no_mistakes (13); drew Capablanca (2), AI Fellow (11), Blank Shooter (14), Danya's Disciple (7) | — |
| as White / as Black | 10.5/12 / 8.0/10 | — |
| wins | **16 of 16 by checkmate** (none by opponent flag or crash) | — |
| only loss | Rated 10, as Black, to Oyinda (1639, rank 87) | — |

They have not played ClaudeShark. At a 630-point ladder gap a Swiss
pairing is unlikely before the final rounds.

## 3. Move quality — the gap in one table

Our oracle, both sides of every AlphaFish game, positions with |eval| < 800
(decided positions excluded), losses capped at 1000 cp
(`move_quality_comparison.txt`):

| player | moves | mean loss | median | p90 | ≥ 50 cp | **≥ 100 cp** | ≥ 300 cp | plays the oracle's top move |
|---|---|---|---|---|---|---|---|---|
| **AlphaFish** | 1,407 | **6.5** | 0 | 18 | 1.9% | **0.6%** | **0.0%** | 55% |
| its opponents (mostly top-15 teams) | 1,403 | 15.2 | 1 | 35 | 5.6% | 2.6% | 0.6% | 49% |
| ClaudeShark RC-A/RC-B (R16–R20) | 179 | 41.7 | 11 | 117 | 24.0% | **14.5%** | 1.7% | 44% |
| ClaudeShark V2.1 (R1–R15) | 465 | 31.8 | 8 | 83 | 15.7% | 7.7% | 1.1% | 49% |

AlphaFish makes a ≥ 100 cp error about once every 170 moves and has never
made a ≥ 300 cp one in 22 games; RC-B makes one ≥ 100 cp error every 7
moves. Its worst move all tournament cost 250 cp (R21 78.Nxh4, a won
position that stayed won). By phase its loss is flat: opening 5.5,
middlegame 8.6, plies 60–119 7.8, long endings 4.0. The platform's own
Stockfish 16 depth-16 review agrees: AlphaFish accuracy 99.4% mean, acpl 2.8
mean / 2 median / 21 max; its opponents 15.5; ClaudeShark 97.9% / 16.2 mean
(median 3.0 — our mean is made by nine games of 24–104 acpl, AlphaFish has
none above 21).

**Not just tactics.** Its only loss (`loss_r10_trajectory.txt`) contains no
blunder: Oyinda (acpl 6 that game) outplayed it positionally from −81 at
move 9 to −300 by move 20 with AlphaFish's largest single errors 70, 54 and
45 cp. Its opening play has no book: every first move is searched at the
full ~4.4 s, and its first three moves agree with the oracle's top choice 43
of 66 times with losses mostly 0–10 cp (`first_moves.txt`).

## 4. Time policy (from `%clk`, 1,624 own moves, `clock_profile.txt`, `time_policy_fit.txt`)

* **spend ≈ 0.033 × clock-before + 0.19 s** (least squares, 89% of the
  variance; adding the ply number adds nothing). Equivalent to "remaining
  time divided by about 30, plus the increment's worth". Median ratio
  spend/clock 0.040, rising to 0.06–0.09 below 15 s (the additive term).
* Cap **4.4 s** (never exceeded in 1,624 moves; 3.9 s median at 100–120 s),
  2.75 s at 60–100 s, 1.65 s at 30–60 s, 0.98 s at 15–30 s, 0.67 s at 8–15 s,
  0.53 s under 8 s. Lowest clock ever held: 4.9 s (the 525-ply game); it
  spends nearly everything but never flags.
* **Instant moves** (< 0.3 s, 137 of 1,624): a found mate is played out
  instantly (R9 35…Ba6+ Bxc4+ Qc7+ Qc2# at 0.001–0.013 s each), forced
  single legal moves, and decided endings; ordinary positions always get the
  formula time.
* Compared with ClaudeShark R16–R30 (`../claudeshark_public/time_policy_curve.txt`):
  ours is spend ≈ 0.025 × clock + 0.51 s but explains only 40% of the
  variance (sd 0.96 s vs their 0.38 s), with 5–10 s outliers (aborted
  iterations) and a 3.0 s median at 100–120 s against their 3.9 s. They
  spend ~30% more in the first 20 moves and keep a smoother curve.

## 5. Draw behaviour (`draws_analysis.txt`)

* **Contempt zero, immediately**: R28 as Black vs Danya's Disciple (2057,
  ranked below it) it repeated from move 9 in a 0.00 position (Nf5 Na4 Qa5+
  Nc3 Qb6 Na4 Qa5+ Nc3), spending the full 4 s per move; the oracle agrees
  every move is best. It takes 0 when 0 is what it sees.
* **Conversion is its weakest visible skill**: R22 vs Capablanca reached
  +203 at ply 54, gave 166 cp back with 38.Qd6, and shuffled to a fifty-move
  draw; R24 vs AI Fellow was never above +35 and ran 525 plies (262 own
  moves at 0.9 s mean) to insufficient material — it does not force
  progress in equal endings. R15 and R26 were equal throughout; in R26 it
  held a worse position with a perpetual after the opponent promoted.
* No draw by agreement/repetition from a winning position appeared; its
  five draws cost it at most the R22 half point.

## 6. What it is likely built from (inference, public data only)

The per-move profile (median loss 0, p90 18 cp, zero ≥ 300 cp errors at
~1.7 s per move) is not reachable by a python-chess alpha-beta at depth
7–8 with a hand-tuned evaluator: RC-B's median is 8–11 cp at the same
budget. Within the rules (Python 3.12, python-chess, numpy, torch,
onnxruntime, numba, one thread, no runtime lookup tables of engine moves)
the two routes to this profile are a **numba-compiled bitboard search** (an
order of magnitude more nodes per second than python-chess) and/or an
**NNUE-style evaluation run in numpy/torch/onnxruntime**. The flat
phase-independent error rate, the accurate quiet play, and the fact that it
lost a positional grind rather than a tactic point at a strong evaluator
rather than raw depth; the instant mate playouts point at a conventional
iterative-deepening search with a PV. Nothing public distinguishes the two
further, and the name "AlphaFish" is not evidence.

## 7. Implications for ClaudeShark (findings, not instructions)

1. **The strength gap is error rate, not opening or endgame knowledge.**
   RC-B's ≥ 100 cp error rate (14.5%) is 24× AlphaFish's (0.6%). Every lane
   that reduces our blunder rate at equal time (speed, horizon) attacks the
   right variable; nothing in this study argues for a book, tablebases or
   new evaluation terms.
2. **Time policy is a cheap, measurable difference.** AlphaFish spends
   ~4 s per move for the first 20 moves and decays smoothly; RC-B spends
   ~3 s early with a much noisier curve and occasional 5–10 s aborted
   iterations. A proportional policy (clock/30 + increment, hard cap ~4.4 s,
   no early-iteration gamble) is worth a controlled test *after* the speed
   lane settles — the earlier sf60/early16 tests changed different
   variables and were flat, so this is not a re-run of a closed lane.
3. **Contempt zero is what the field's best does.** No evidence that
   draw-avoidance helps; our repetition heuristic is not the problem.
4. **Conversion of +200 is where even AlphaFish leaks** (R22), and it is
   our R17 failure too; a conversion lane has cross-engine evidence.
5. **Pairing**: we are 630 points below; a head-to-head is improbable. The
   useful comparison set is their *opponents* (2.6% ≥ 100 cp errors, top-15
   teams) — that is the bar for the standings we could reach.

(Section 8 appended below after the punishment test.)

## 8. Would RC-B punish what AlphaFish punished? (`punish_rcb.txt`, `punish_summary.txt`)

At the 29 positions where an AlphaFish opponent had just erred by ≥ 100 cp
(|eval| < 600 before the error), RC-B was put in AlphaFish's seat at 2,500 ms
(`champions/rc_b`, `tools.daily.targeted`, oracle 1M nodes on both moves):

| | kept the gain (loss < 50 cp) | mean loss | ≥ 100 cp |
|---|---|---|---|
| AlphaFish's actual move | 20 / 29 | — | 3 |
| **RC-B, 2.5 s** | **24 / 29** | 36 cp | 5 |

RC-B finds the punishing move as often as AlphaFish does; the five it misses
are the same kind of miss as its own games (R11 32…Qd6: RC-B plays Kg2 and
loses 233 cp; R16 27…Na7: Ne4 instead of f6, −262). **The gap is not
tactical exploitation; it is the 14.5% of ordinary moves where RC-B gives
100 cp away unprovoked, against AlphaFish's 0.6%.** That is the number to
move.

## 9. Files

`analysis/competitors/659a3020_alphafish/`: `REPORT.md` (this), `games.jsonl`,
`team_games.json`, `leaderboard_*.json`, `team_page.html`, `game_*.html`,
`pgn/rated09..30.pgn`, `alphafish_games.jsonl`, `alphafish_games_annotated.jsonl`,
`results_and_review.txt` (note: its score column is wrong; use
`performance_rating.txt`), `clock_profile.txt`, `time_policy_fit.txt`,
`instant_moves.txt`, `move_quality_comparison.txt`, `loss_r10_trajectory.txt`,
`draws_analysis.txt`, `first_moves.txt`, `punish_*.{json,jsonl,txt}`.
`analysis/competitors/claudeshark_public/`: our 30 public games, review and
clock numbers. No engine file was touched; no Chessathon upload; the Windows
candidate-3 screen was not interacted with.
