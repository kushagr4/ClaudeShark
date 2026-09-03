# Repetition and win-conversion audit: 127 draws, one real mistake

Date: 2026-09-03. Analysis and benchmark tooling only. **Production engine
behaviour is unchanged.**

The post-mortem observed that 116 of 200 arena games and 127 of 200 fixed-depth
games ended by repetition, and guessed that around 10% of games might contain
wins thrown away that way. This audit tests the guess. It does not survive.

## Headline

Of 127 repetition draws with full move history, **one** is a winning side
declining a better continuation. The rest are correct chess: 82 level positions
repeating naturally and 44 in which the *losing* side successfully saved the
draw. The engine's repetition handling is sound, and relaxing it makes the
engine repeat **more**, not less.

The by-product is more interesting than the hypothesis: the engine already has
correct practical win/loss awareness with no draw-contempt term anywhere in the
code, and it takes an available repetition 74% of the time when losing and
**0%** of the time when winning by 300 cp or more.

## 1. Repetition termination counts

| set | games | repetition | checkmate | other | repetition share |
|---|---|---|---|---|---|
| time-controlled arena (v0.6 vs v0.5.2) | 200 | 116 | 69 | 11 insufficient, 4 fifty-move | 58.0% |
| fixed-depth diagnostic set | 200 | 127 | 65 | 8 insufficient | 63.5% |

These are two different game sets, not a repeated measurement of one. All 127
fixed-depth repetition draws replay to a position the referee legitimately
called: `can_claim_threefold_repetition()` is true in every one. Candidate
colour is balanced (57 white / 59 black in the arena). Repetition games are
shorter than decisive ones (46 vs 66 plies at fixed depth).

**The arena's move history was not retained** -- the v0.6 run was made without
`--pgn` -- so everything below that needs moves uses the fixed-depth set, where
every move was recorded. Section 12 fixes the tooling so this cannot recur.

## 2. Category A/B/C/D breakdown

Judged at the decision point: the position one ply before the end, whose mover
chose a move that left the opponent a claimable draw. Stockfish scores that
position from a fresh board at 1M nodes, so the number is the position's
objective value rather than a verdict contaminated by the repetition about to
be claimed.

| | category | n | share |
|---|---|---|---|
| A | ahead, but no non-repeating move keeps the advantage | 0 | 0.0% |
| B | equal position repeating naturally | 82 | 64.6% |
| C | losing side successfully forcing the draw | 44 | 34.6% |
| D | **winning side repeating despite a stronger continuation** | **1** | **0.8%** |

Category C is a *success*, not a defect: in 37 of those 44 the saving side was
worse than -300, i.e. the draw rescued a lost game.

## 3. Genuine avoidable winning repetitions

**One, and it is marginal.** Cluster 43,
`1Q6/5pk1/1p2p1p1/1P5p/4P2P/6P1/4qPK1/8 w - - 9 51`, White to move at +120
(WDL 789/211/0). The engine played `b8e5`, handing over the draw. The best
non-repeating move, `b8b6`, holds +135. So the loss is about 135 cp of a
position Stockfish already scores as only 79% likely to be won -- and every
other non-repeating move is far worse (`b8e8` -25, `b8c7` -247). The engine
gave up a slim advantage, not a win.

Against 200 games, that is 0.5% of games and one twentieth of the 10% the
post-mortem guessed at.

## 4. Evaluation distribution before the repetition

Mover's point of view at the decision point:

| band | n | share | categories |
|---|---|---|---|
| <= -300 | 37 | 29.1% | C 37 |
| -299..-100 | 7 | 5.5% | C 7 |
| -99..+99 | 82 | 64.6% | B 82 |
| +100..+299 | 1 | 0.8% | D 1 |
| >= +300 | 0 | 0.0% | -- |

Nothing at all above +300. Fourteen of the decisions already had a mate on the
board for the opponent.

## 6. Ahead / behind asymmetry

The strongest form of the question, and the best result in the audit. Every ply
of all 200 games was replayed with real move history; at each ply, did the
mover *have* a move handing over a claimable threefold, and did they take it?

| mover's Stockfish eval | had the option | took the draw | rate |
|---|---|---|---|
| <= -300 | 31 | 23 | **74.2%** |
| -299..-100 | 12 | 7 | 58.3% |
| -99..+99 | 111 | 82 | 73.9% |
| +100..+299 | 5 | 1 | **20.0%** |
| >= +300 | 5 | 0 | **0.0%** |
| all | 164 | 113 | 68.9% |

Both engines show the same gradient (v0.5.2: 64% when losing, 0% when winning).

**ClaudeShark does not lack practical win/loss awareness.** It gets this for
free and the mechanism is worth stating, because it is the reason no contempt
term is needed: a repetition is scored `DRAW_SCORE`, which is zero, and
alpha-beta compares that against the position's real score. Zero is worse than
a winning score, so a winning engine avoids the repetition; zero is better than
a losing score, so a losing engine steers into it. One unsigned constant
produces the entire asymmetry. Candidate B from the brief -- root-relative
repetition contempt -- is already implemented, implicitly and correctly.

## 5 & 6. Concrete reproductions, and what they actually show

The brief asked for a `Qf8`-class reproduction. Four candidates were found and
instrumented. **None of them is caused by the repetition policy.**

The search-level suspects are positions where the engine, replaying its own
game-level repetition record, would itself choose a repeating move while
winning:

| cluster | FEN | Stockfish | engine plays |
|---|---|---|---|
| 38 | `1k1n2R1/8/1b6/3B4/p2pK2P/1p6/8/8 w - - 7 64` | +367, WDL 1000/0/0 | `g8g2` (repeats), score -8 |
| 91 | `3N4/3b4/2p1pBkb/2PpP1p1/3Pp1P1/2K1P3/8/8 w - - 28 58` | +511, WDL 1000/0/0 | `d8b7` (repeats), score 0 |
| 96 | `1r6/R6p/3p1qpk/1P2p3/1Q2Pp1P/3n2P1/5PB1/6K1 w - - 7 42` | +149, WDL 959/41/0 | `b4d2` (repeats), score 0 |

Two of these are 100% wins by WDL that the engine scores at zero. That looks
damning until the policy is varied. At depth 10:

* cluster 91 -- **depth fixes it.** Every policy plays `c3b4` at +108, no
  repetition.
* cluster 43 (the category-D case) -- **depth fixes it.** The current policy
  and the threefold-aware variant both play Stockfish's `b8b6`; only the
  variant with repetition scoring *disabled* still plays the drawing `b8e5`.
* clusters 38 and 96 -- still repeat at depth 10, under every policy. The
  engine's score stays at 0 and 78 against Stockfish's +367 and +149.

So the failures are horizon and evaluation failures, not repetition failures.
The engine does not know it is winning; it is not choosing a draw over a win it
can see.

## 6b. Search-level second-occurrence diagnosis

The mechanism under suspicion is one line in `cs_search.py`:

    if key in self._game_counts:
        return DRAW_SCORE

`_game_counts` is a counter but only its keys are read, so a single earlier
occurrence scores as a draw. FIDE requires three. Three policies were built as
scratch copies, differing only in that line, with the path scan that prevents
the search looping inside one line untouched in all of them.

Swept over all 127 final positions at depth 6, with each engine's true
game-level record replayed:

| policy | moves differing from current | chooses a repeating move |
|---|---|---|
| D current (`key in _game_counts`) | -- | 24 |
| A threefold-aware (`get(key, 0) >= 2`) | 23 | **29** |
| C game-level check removed | 76 | **81** |

**Cases where a relaxed policy avoids a repetition the current policy takes
while winning: zero.** Relaxing the rule makes the engine repeat more, because
without the draw penalty the search no longer has a reason to steer away from
positions it has already visited. Disabling the check moved the search score by
only +8.7 cp on average (+5.0 cp restricted to winning positions).

One structural note that matters for the pipeline: with no game history,
`_game_counts` is empty and all three policies are **bit-identical**. The
240-position root suite therefore cannot see a repetition change at all. It is
not merely insensitive here; it is blind by construction.

## 7. Candidate policies tested

| candidate | result |
|---|---|
| A -- exact threefold-aware history | Rejected. 23 moves change, repeats *more* (29 vs 24), fixes nothing while winning. |
| B -- root-relative repetition contempt | Not needed. Already implemented implicitly; section 6 shows the full ahead/behind gradient with no contempt term. |
| C -- allow the second occurrence, forbid the immediate cycle only | Rejected. 76 moves change, repeats far more (81 vs 24), and at depth 10 it *loses* the one category-D case the current policy gets right. |
| D -- current heuristic (control) | **Kept.** |

## 8. Safety tests

`tests/test_repetition_safety.py` (10 tests) and `tests/test_draw_claim.py`
(11 tests) pin the properties any future change must preserve:

* the losing side takes a repetition draw (score -515 becomes 0, same move);
* the winning side declines one (avoids the repeating move, stays above +300);
* a forced perpetual is accepted when losing -- real audited position,
  `6k1/6pp/1p1p1p2/1P1P1P2/2P1K3/R7/7P/5r2 b - - 9 46`, Stockfish -316, the
  engine holds with checks;
* a genuinely equal repeated position scores near zero;
* the search terminates when every move only shuffles;
* a claimable fifty-move draw scores zero *inside* the search, and checkmate
  still outranks it;
* the repetition record survives across the moves of one game, is cleared by
  `new_game`, and does not write a drawn score into the table under a plain
  position key;
* a real threefold ends the game in both adjudication modes; a claim that is
  merely available does not, under `strict`.

The two synthetic tests are the same rook endgame from either side, so the
asymmetry is visible in one file.

## 9. Deterministic move-quality effects

None: production is unchanged. `cs_constants.py`, `cs_search.py`, `cs_tt.py`,
`cs_ordering.py`, `cs_see.py`, `cs_time.py` and `agent.py` are byte-identical
to `champions/v0_5_2_correctness`; `cs_eval.py` differs only by the dormant
`CS_EVAL_KING_SAFETY` hook, default off, which the king-safety session showed
leaves the depth-6 node count identical at 1,712,405.

The audit variants were deliberately *not* scored on the 240-position suite,
because as section 6b establishes they are identical to production on it.

## 10. Fixed-depth paired self-play

The referee ends a game on `board.outcome(claim_draw=True)`, and python-chess
reports a claimable threefold either when a position has occurred three times
**or** when the side to move merely has a legal move reaching a third. Not one
of the 127 draws had actually occurred three times on the board; every one
ended on the earlier clause. Under FIDE the claim is the player's option, and
in 44 of them the side it was claimed for was winning by 100 cp or more and,
asked directly, would have played a different move.

That looked like a benchmark bug worth 22% of games, so it was measured rather
than asserted. A `--draw-claim strict` mode was added, ending the game only on
a genuine third occurrence, and the whole 200-game set was replayed:

| adjudication | W | D | L | score | Elo | bootstrap 95% CI | mean plies |
|---|---|---|---|---|---|---|---|
| auto (historical) | 25 | 135 | 40 | 46.2% | -26 | -49 .. -3 | 53 |
| strict | 25 | 133 | 42 | 45.8% | -30 | -53 .. -7 | 55 |

| terminations | auto | strict |
|---|---|---|
| threefold repetition | 127 | 125 |
| checkmate | 65 | 67 |

**The correction is mine to make: it changes almost nothing.** Of the 44 games
called "cut short", 42 reach a real threefold a few plies later anyway and only
2 become wins. The winning side plays on, as predicted, and then cannot make
progress. The referee's early claim is technically wrong and empirically
irrelevant; what the 44 games actually demonstrate is the conversion failure
the post-mortem already established, seen from another angle.

`auto` therefore stays the default, so every historical result remains
comparable, and `strict` exists for anyone who wants the stricter reading. The
choice is now explicit and tested rather than implicit.

## 11. Performance impact

None. No production code changed, so no measurement is owed. The scratch policy
variants cost within noise of the control at equal depth (cluster 38 at depth
10: 171,910 nodes for both the current and the threefold-aware policy, 219,055
for the disabled variant -- the disabled variant searches *more* because it no
longer prunes cycles by scoring them).

## 12. Decision: NO CHANGE to the engine; two tooling fixes

**Engine: no change.** The brief's rule was "no reproduction, no production
change." Four candidate reproductions were built and all four turned out to be
depth or evaluation failures; every alternative policy is worse. There is
nothing to fix here.

**Tooling, two fixes:**

1. **Move history is retained by default.** `tools/arena.py` now derives the
   PGN path from `--jsonl` unless `--pgn` names another or `--no-pgn` refuses
   it explicitly, with a loud warning in the refusing and the
   nothing-recorded-at-all cases. Every PGN carries `MatchId`, `GameIndex`,
   `PgnIndex`, `Cluster`, `White` and `Black`, and each JSONL game row carries
   `pgn_file` and `pgn_index`, so a game and its record find each other in
   either direction. `tests/test_move_history_retention.py`, 9 tests.
2. **Draw adjudication is explicit.** `harness.referee.game_outcome(board,
   draw_claim)` with modes `auto` (unchanged, and tested to be bit-identical to
   `board.outcome(claim_draw=True)`) and `strict`. Exposed as `--draw-claim` on
   both `tools/arena.py` and `tools/postmortem/play.py`, and recorded in the
   arena JSONL header. The fifty-move rule is deliberately left claimable in
   both modes: the engine's own `rules_outcome` mirrors
   `can_claim_fifty_moves`, and desyncing them is exactly the class of bug that
   cost this project a benchmark before.

## 13. Updated experiment pipeline

Documented in `AGENTS.md` and `PROJECT.md`:

| gate | instrument | cost | role |
|---|---|---|---|
| 1 | `tools/corpus/analyse.py` on `corpus/competition_like_v1.jsonl` | minutes | Screening only. 239 of its 240 positions are under 50 cp, and it is *bit-blind* to repetition policy. |
| 2 | `tools/postmortem/play.py` + `annotate.py` + `report.py` | ~50 min / 200 games | Decides. Fixed-depth paired self-play, every move retained, cluster bootstrap, error rates, conversion from +200, defence from -200, repetition outcomes. |
| 3 | `tools/arena.py` | hours | Confirms, on a real clock. Only if gate 2 passes. |

The root suite is never again presented alone as predictive Elo evidence.

## 14. Remaining evaluation candidates

Unchanged in order by this audit, which removed one candidate rather than
adding any:

1. **Conversion from a winning position.** Now supported by two independent
   lines of evidence: the post-mortem's 33%-vs-44% conversion from +200, and
   this audit's finding that 42 of 44 games where a side was winning at the
   claim point still failed to win when allowed to continue. This is the
   biggest measured weakness in the engine and it is not a repetition problem.
2. **Non-linear (concave) material**, per the post-mortem's calibration table.
3. Passed pawns -- still the top corpus-ranked missing term, still without a
   causal signal.
4. Mobility, rook files -- no evidence either way.
5. Search-margin calibration -- real interaction, neutral on unbiased test.

Repetition policy is removed from the list.

## 15. RECORD THIS

1. **The headline, and it is a negative.** "Half the games ended by repetition
   -- but how many were actually mistakes?" **One in 127.** Show
   `corpus/repetition/02_categories.txt`: B 82, C 44, D 1, and nothing at all
   above +300. Then the guess it replaces: the post-mortem's "approximately 10%
   of games may contain wins thrown away through repetition".
2. **The engine repeating from a clearly winning position.** Cluster 91,
   `3N4/3b4/2p1pBkb/2PpP1p1/3Pp1P1/2K1P3/8/8 w - - 28 58`, Stockfish +511 and
   WDL 1000/0/0, engine plays `d8b7` and scores it **0**. Then the twist: at
   depth 10 it plays `c3b4` at +108 instead. It was never a repetition bug --
   it could not see the win. Command:
   `uv run python -m tools.repetition.policies --out %TEMP%\cs_rep --cases corpus\repetition\cases.json --depth 10`
3. **The policy comparison that kills the hypothesis.**
   `corpus/repetition/04_policy_sweep.txt`: relaxing the rule makes the engine
   repeat *more* (24 -> 29 -> 81), and "cases where a variant avoids a
   repetition the current policy takes while winning: **0**".
4. **The asymmetry table.** `corpus/repetition/06_asymmetry.txt`: 74.2% when
   losing, 0.0% when winning by 300+, from a single unsigned zero and no
   contempt term. Good visual: the five-row gradient.
5. **The referee finding, and my own correction to it.** Not one of the 127
   positions had actually occurred three times; the referee claims an option
   that belongs to the player, and in 44 games it claimed it for a *winning*
   side. That is a 22%-of-games headline -- and then `--draw-claim strict`
   showed only 2 of the 44 convert (`corpus/repetition/05_strict_vs_auto.txt`).
   Worth recording precisely because the dramatic version was wrong.
6. **The gate predicting the arena.** `corpus/repetition/05_strict_vs_auto.txt`
   beside the v0.6 arena: fixed-depth -26 Elo (bootstrap -49..-3), real arena
   -40 Elo (bootstrap -67..-14). Same sign, same conclusion, 50 minutes
   instead of hours.

## 16. Reproduction (Windows CMD, from the repository root)

    uv run python -m tools.postmortem.instrument --out %TEMP%\cs_pm
    uv run python -m tools.repetition.audit --games corpus\postmortem\games\annotated.jsonl --cand %TEMP%\cs_pm\scale --base %TEMP%\cs_pm\baseline --out corpus\repetition\classified.jsonl
    uv run python -m tools.repetition.policies --out %TEMP%\cs_rep --cases corpus\repetition\cases.json --depth 6
    uv run python -m tools.repetition.policies --out %TEMP%\cs_rep --cases corpus\repetition\cases.json --depth 10
    uv run python -m tools.postmortem.play --cand %TEMP%\cs_pm\scale --base %TEMP%\cs_pm\baseline --depth 6 --workers 5 --draw-claim strict --out corpus\repetition\fixed_depth_strict.jsonl
    uv run python -m pytest tests\test_repetition_safety.py tests\test_draw_claim.py tests\test_move_history_retention.py -q

The count, category, asymmetry and strict-versus-auto tables are inline scripts
whose outputs are kept as `corpus/repetition/0*.txt`.

## 17. Generated artefacts

`corpus/repetition/01_counts.txt`, `02_categories.txt`,
`03_policies_d6.txt`, `03_policies_d10.txt`, `04_policy_sweep.txt`,
`05_strict_vs_auto.txt`, `06_asymmetry.txt`, `classified.jsonl`,
`policy_sweep.json`, `cases.json`, `fixed_depth_strict.jsonl`;
`tools/repetition/{audit,policies}.py`; a `seen` command added to
`tools/postmortem/worker.py`; `tests/test_repetition_safety.py`,
`tests/test_draw_claim.py`, `tests/test_move_history_retention.py`.
