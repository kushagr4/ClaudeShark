# Learned evaluation: pilot preregistration

Date: 2026-09-11, written before any position was labelled. Engine: RC-J
(runtime files byte-identical to `2bf6885`; `main` at `3b9addd`). Nothing in
this lane changes the runtime engine; every measurement below runs offline or
in a scratch copy.

Status note: the Chessathon upload window closed on 11 September at 11:00
(London), so this is post-deadline research. Nothing is uploaded, no arena is
played, `START_FRACTION` stays 0.45.

## 1. Question

Does a Stockfish-supervised learned correction to RC-J's leaf evaluation carry
held-out signal large enough to justify scaling the dataset and building a small
NNUE-style evaluator? The pilot answers that for a cheap linear model (E1)
against RC-J's evaluator (E0); the neural model is designed, not trained, here.

## 2. Evaluators

**E0** is RC-J's live evaluator, `cs_core.evaluate(B, S)` (`cs_core.py:840-864`):
tapered PeSTO material + piece-square tables (phase 0..24), bishop pair 22/40,
bare-king mop-up, tempo +8 for the side to move. It is called directly from the
compiled core on each position, not re-implemented.

**E1** = E0 + a learned linear correction:

    E1_stm = E0_stm + sum_j ( w_mg[j] * phase/24 + w_eg[j] * (24 - phase)/24 ) * x_j

Every feature `x_j` is computed relative to the side to move (a count for the
side to move minus the same count for the opponent, or a side-to-move-specific
threat count), so E1 is colour-symmetric by construction. The E0 term keeps
coefficient 1 and the probability scale K is fixed to E0's fitted K0, so E1
stays in E0's centipawn units and search margins keep their meaning (the v0.6
material-scale lesson: a scale change must never be scored as a quality gain).

Preregistered feature set (each with a middlegame and an endgame weight, plus a
tapered intercept that acts as a tempo correction):

| family | features |
|---|---|
| material correction | pawn, knight, bishop, rook, queen counts |
| mobility | knight, bishop, rook, queen attacks on squares not own-occupied and not attacked by enemy pawns |
| pawn structure | doubled, isolated, backward, passed, passed advancement (ranks beyond the second), protected passed, connected passed, pawn chain links |
| rooks | open file, semi-open file, seventh rank |
| king | shelter pawns, open/semi-open files at the king, enemy pieces attacking the king zone, king-zone squares attacked |
| space | own pawns on the fifth/sixth (relative) ranks |
| minor pieces | knights/bishops on outposts, bishop pair correction |
| threats | side-to-move pieces hanging (attacked, undefended); opponent pieces hanging; side-to-move pieces attacked by a lower-valued piece; opponent pieces attacked by a lower-valued piece |

These follow `tools/corpus/eval_residuals.py` so the result can be read against
the earlier in-sample residual study (`corpus/eval_residuals.md`), with the
threat features split by side to move because a hanging piece means different
things for the mover and the opponent.

## 3. Data

Sources (all local; nothing is downloaded):

| family | source | group key |
|---|---|---|
| TWIC | master games in `C:\Users\epick\engines\twic\*.pgn`, both players 2300+, at least 24 plies, standard start; game ids as `tools.corpus.extract._game_id`; games already in `corpus/candidates.jsonl` (the source of cl240) excluded | game id |
| PUBLIC | Chessathon public games: `analysis/top50_games.jsonl`, `analysis/refresh_2026-09-05/top50_games.jsonl`, `analysis/competitors/*/…games.jsonl` | organiser start FEN |
| VS_SF | ClaudeShark builds vs Stockfish UCI_Elo arenas under `corpus/strength/` | start FEN |
| SELFPLAY | timed ClaudeShark self-play: `corpus/daily/rcc`, `corpus/daily/time`, `corpus/strength` c5/c8/c9 | start FEN |

Excluded outright: fixed-depth Gate-2 arenas (heavy duplication, old builds),
files marked CORRUPT-DISCARDED, the v0.5 regression PGNs, and everything under
`benchmarks/current/rcj_loss_autopsy/`.

**Split.** By group, never by position: `sha1("20260911|" + group) mod 10`,
0-7 train, 8 validation, 9 test. Games that share an organiser start FEN share a
group, so an opening family never straddles two splits. The split is frozen in
`pool.jsonl` before any label is read.

**Sampling.** Positions at least 10 plies apart within a game; TWIC from ply 16
(1 per game), PUBLIC 4, VS_SF 2, SELFPLAY 2 per game from ply 2 after the
start. Positions in check or already over are not sampled (the evaluator is
never asked about them). Positions are deduplicated on the four-field FEN
across the whole pool; a duplicate is kept in the highest-priority split
(test > validation > train) and dropped elsewhere.

**RC-J real-loss holdout.** The 30 R76-R105 games (platform UUIDs), every
position in them, the 852 scanned positions, and every game that starts from
one of their 28 organiser start FENs are excluded from all three splits. The 14
first-decisive-error positions and the 5 confirmed supplementary serious errors
(`rcj_loss_autopsy/data/verify*.json`) form the holdout and are never trained
or tuned on. The leakage audit checks UUIDs, exact move sequences, start
families and four-field FENs; zero overlap is required.

## 4. Labels

Stockfish 18, binary SHA-256 `c86215fa1977d53b…9118911`, one thread, Hash 32 MB,
`UCI_ShowWDL`, `ucinewgame` before every position, fixed nodes, last exact info
line (`scripts/sf_label.py`).

Target: `E = (W + D/2) / 1000` from Stockfish's WDL, side to move's expected
score in [0, 1]. Mates saturate to 1 or 0 through the WDL itself; mate
distances and centipawns are stored separately for diagnostics and never used
as a numeric regression target.

**Budget selection (frozen rule).** A stability sample of 300 pool positions is
labelled at 50k, 100k, 200k, 400k and 1M nodes and at a 4M-node reference. The
budget is the smallest one with mean |E - E_ref| <= 0.04, WDL-category
agreement with the reference >= 90% (win >= 0.75, loss <= 0.25), and Spearman
correlation with E_ref >= 0.95. If none qualifies, 1M. Determinism: 30 positions
labelled twice at the chosen budget must give identical records.

**Training subset.** Train split, and "quiet": Stockfish's best move is not a
capture or promotion (the side to move is never in check by construction).
Tactical positions are labelled and kept for diagnostics but not fitted, because
the evaluator is consulted at quiet leaves (quiescence stand-pat, reverse
futility) and a static function cannot see material in flight.

## 5. Training

K0: fitted on the train quiet subset so `sigmoid(E0_stm / K0)` minimises the
binary cross-entropy against E. E1: weights fitted by the same loss with K = K0
fixed, L2 penalty lambda chosen on the validation split from
{0, 1e-4, 1e-3, 1e-2, 1e-1} (in units of the mean loss per squared weight in
pawns). The test split is read once, after lambda is frozen.

## 6. Metrics (test split unless stated; train and validation also reported)

1. **Calibrated loss.** Binary cross-entropy and E-MSE with each evaluator's own
   K refitted on train (E0, E1, and a control E0 x 1.5 that must come out
   identical to E0: a uniform scale is decision-invariant).
2. Pearson and Spearman correlation of the evaluation with Stockfish's cp
   (clipped to +/-1000, mates excluded) and with logit(E).
3. Sign accuracy where |E - 0.5| >= 0.15.
4. **Pairwise move ranking.** For up to 800 test positions: Stockfish's best move,
   the game move (if different) and one seeded random legal move are each
   scored by a root-restricted Stockfish search (`searchmoves`) from the same
   root at the label budget. Every pair with |dE| >= 0.05 is a test item; an
   evaluator is correct if it orders the two moves the same way. Move value =
   minus the evaluation of the resulting position (static), and minus a
   captures-and-promotions quiescence search that uses the evaluator at its
   leaves (qsearch-resolved; the same quiescence code for every evaluator).
   Qsearch-resolved accuracy is the primary ranking metric; ties are errors.
5. Stratified by balance (|E - 0.5| < 0.1, 0.1-0.3, >= 0.3), phase (>= 16,
   8-15, < 8) and source family; the v0.6 post-mortem showed a near-balanced
   suite can hide a regression in unbalanced positions.
6. Uncertainty: 1,000 bootstrap resamples of test groups for every E1 - E0
   difference.

**Holdout.** For each of the 14 first-decisive positions: Stockfish's 10M-node
best move against RC-J's played move, ordered by the 10M-node E values from
`verify.json`. E0 and E1 are each correct when they value the Stockfish move
above the played move (static and qsearch-resolved). The 5 confirmed
supplementary errors are reported as an extended set of 19. With 14 items this
is descriptive; no pass threshold is set on it at the pilot stage.

## 7. Speed

E0 and E1 static-evaluation throughput in a compiled loop over the test
positions; then a scratch copy of RC-J whose `evaluate` adds the E1 correction
(weights compiled in as constants), searched to fixed depth 8 on the 24
`BALANCED_OPENINGS`: a zero-weight copy must reproduce RC-J's node count
exactly (plumbing control), and the E1 copy gives the nodes-per-second ratio.
Run only on an otherwise idle machine.

## 8. Pilot verdict (frozen rule)

* **STOP LEARNED EVAL** if the labels fail the stability rule at 1M nodes, or if
  E1 is significantly *worse* than E0 on test.
* **CHANGE REPRESENTATION** if the labels are stable but E1 does not improve the
  test calibrated loss with a bootstrap 95% interval excluding zero, or improves
  the loss while its qsearch-resolved pairwise accuracy falls below E0's.
* **SCALE DATASET** if E1 improves the test calibrated loss with the interval
  excluding zero and its qsearch-resolved pairwise accuracy is at least E0's.

Whatever the verdict, the pilot stops for human review. The 100k-500k main
labelling job is not launched without approval.
