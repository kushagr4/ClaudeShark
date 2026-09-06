# C4 — instability-triggered time extension (pre-registered 2026-09-06 01:55 UK, before any measurement)

| field | value |
|---|---|
| CANDIDATE NAME | C4-instability-extension |
| BASELINE | RC-C (`champions/rc_c`, submitted champion); branch `kushagra/c4-instability-extension` from `rc-c-integration` |
| HYPOTHESIS | A large share of RC-C's result-flipping errors are one or two plies short of repair (min repair depth 7–8 in 30 of 120 audited errors) or come from a root that was still flip-flopping when the clock stopped it (16 of 120 avoided by a settled depth-6 search). When the last completed iteration changed the root move or moved the root score by >= 50 cp, one more iteration is worth more than the average iteration, so spending extra time only then buys depth exactly where the errors are, at a small average clock cost. |
| TARGET ERROR CLASS | TACTICAL HORIZON (search-repairable) and SEARCH INSTABILITY, together 29 of the 52 result-flipping errors from live positions in `2026-09-06-rcc-2300-error-audit.md` |
| TARGET POSITIONS | the 57 audited errors in those two classes (`corpus/strength/games/rcc_vs_sf2300_dev_100.errors.jsonl`, mechanisms in `…mechanisms.json`) |
| EXPECTED GENERAL BENEFIT | fewer >= 100 cp errors per game at the competition clock (prediction: at least 10 of the 57 targets repaired at the game budget; the >= 100 cp rate in a fresh screen below the 8.95% baseline) |
| EXPECTED SPEED COST | none per node (no search-tree change; fixed-depth fingerprint must be identical with the switch on or off) |
| EXPECTED CLOCK EFFECT | more time on unstable moves only; the extension raises the soft budget once per move by a fixed factor, never the hard budget, and is disabled below a clock floor. Prediction: mean think up by under 20%, clock floor not below RC-C's 3.8–5.6 s in the same match, zero flags |
| MATCHED NEGATIVE CONTROLS | 120 positions from the same games where RC-C's move lost < 30 cp (`tools.strength.instability_probe`): (a) instability must be rarer there than at the errors, else the trigger is not selective; (b) with the extension on, the move must stay within 30 cp of the oracle in >= 95% of them |
| WHAT MUST REMAIN UNCHANGED | every fixed-depth node count (`tools.bench --depth 6` = 1,708,269 with the switch on and off); every test; behaviour when the switch is off byte-for-byte RC-C; panic/low-clock behaviour; the hard budget |
| REJECTION CRITERION | any of: fingerprint changes; a test fails; Gate 1 repairs < 10 of the 57 targets at the game budget; > 5% of negatives worsened by >= 100 cp; clock floor below 4 s or any flag in a 60-game screen; internal screen vs RC-C below 50% with a family bootstrap excluding zero; external screen (benchmark A, strict, dev set) not above the strict baseline's score |
| MAX USEFUL DEVELOPMENT TIME | 60 minutes of implementation + Gate 0/1 before any arena; screens 60 games external + 60 games internal |
| SWITCH | `CS_TIME_EXTEND` (declared time variable; `0` = RC-C behaviour). The candidate snapshot ships it on |

## Mechanism (exact)

`cs_time.TimeManager.extend(factor)`: once per move, if not panicking and the
clock at `begin` was above `EXTEND_MIN_CLOCK_MS`, `soft = min(hard, soft *
factor)`. `cs_search.Searcher.search`: after a completed iteration at depth
>= `EXTEND_MIN_DEPTH`, if the best move differs from the previous iteration's
or the score moved by >= `EXTEND_JUMP`, call `timer.extend(EXTEND_FACTOR)`.
`should_start_iteration` is unchanged (`elapsed < soft * START_FRACTION`), so
the extension only lets one more iteration start; the hard deadline still
aborts it. Fixed-depth and fixed-budget benchmark paths never call `extend`.

Initial constants (pre-registered, to be fixed before Gate 1 and not tuned on
the target set afterwards): `EXTEND_FACTOR = 1.6`, `EXTEND_JUMP = 50`,
`EXTEND_MIN_DEPTH = 4`, `EXTEND_MIN_CLOCK_MS = 20_000`.

## Gate plan

* Gate 0: fingerprint on/off; full test suite; clock ladder with the switch on.
* Gate 1: `instability_probe` on 120 errors + 120 negatives (selectivity);
  replay of the 57 targets and the 120 negatives at the game budget with the
  switch on and off, oracle-scored (repairs, regressions, time used).
* Gate 2A external: 60 games vs benchmark A (strict) on the dev set.
* Gate 2A internal: 60 games vs `champions/rc_c`.
* Promotion only with both non-negative and the error rate below baseline.

## Result — REJECTED at Gate 1 (2026-09-06 02:35 UK)

Gate 0 passed (fingerprint 1,708,269 with `CS_TIME_EXTEND` on and off; 1,228
tests). Gate 1 (`tools.strength.replay_compare`, 60 s clock, RC-C vs the
candidate, oracle 1M nodes; `corpus/strength/c4/gate1_*.jsonl`, `gate1.log`):

| set | n | baseline >= 100 cp | candidate >= 100 cp | repaired | broken | extended | mean ms | mean depth |
|---|---|---|---|---|---|---|---|---|
| targets (horizon + instability errors) | 57 | 38 | 34 | **7** | 3 | 47 (82%) | 2,183 → 3,145 (+44%) | 7.21 → 7.63 |
| matched negatives (< 30 cp moves, same games) | 120 | 2 | 2 | 0 | 0 | **77 (64%)** | 2,062 → 2,779 (+35%) | 7.61 → 8.07 |

* Repairs 7 < the pre-registered 10; net +4 of 38 reproduced errors.
* The trigger is not selective: it fires on 64% of ordinary moves (82% of
  the targets). RC-C's root moves or scores change between iterations on
  most moves at depths 4–8 (baseline unstable-iteration count >= 1 in 98 of
  120 negatives and 51 of 57 targets), so "instability" does not mark the
  error positions — it marks nearly everything, and the candidate is a
  +35–44% uniform time increase, which the sf60 and early16 experiments
  already showed to be flat at the competition clock.
* The 7 repairs are one-ply repairs bought with time (depth +1 in every
  case); they say depth pays, not that instability finds where it pays.

**Verdict: REJECTED. The switch stays off (`CS_TIME_EXTEND=0` is RC-C);
the branch is kept as the record.** What survives: depth repairs a real
share of the largest errors, so the lane that buys depth without buying
time — identity-preserving speed — is next, profile-driven.
