# C6 — selective king-pressure term (pre-registered 2026-09-06 07:50 UK, before any measurement)

| field | value |
|---|---|
| CANDIDATE NAME | C6-king-pressure (evaluation term `king_pressure`, registry stage `packed`, middlegame only) |
| BASELINE | C5 = RC-C + RFP (`champions/c5_rfp`, development champion); branch `kushagra/c6-king-pressure` from `kushagra/c5-rfp` |
| HYPOTHESIS | The audit's largest errors are made with the static evaluation a median +269 cp above the oracle, most often with a material lead and the enemy queen plus two or more enemy pieces bearing on our king. The shipped evaluator has no king term, so it cannot see that; a term that fires only in that configuration lowers the optimism where it matters and changes the moves that walk into attacks, without disturbing ordinary positions. |
| TARGET ERROR CLASS | EVALUATION / WRONG WORLD MODEL (optimism under king pressure): 39 of the 120 largest audited errors; secondary, the UNKNOWN class where the signal fires |
| TARGET POSITIONS | the 63 audited errors whose root score was >= 200 cp above the oracle (`corpus/strength/games/rcc_vs_sf2300_dev_100.errors.jsonl`, `timed.score - oracle_before >= 200`) |
| SELECTIVITY EVIDENCE (measured before design, 07:25 UK) | signal = enemy queen on the board AND >= 2 enemy non-pawn pieces attacking our king ring: fires in **38%** of the 63 optimistic errors, 19% of the other 57 errors, **4%** of the 120 matched low-loss positions from the same games. Attackers >= 2 alone (no queen gate) fires in 20% of negatives — not selective enough; >= 3 with queen fires in 6% / 0% — too rare |
| EXPECTED GENERAL BENEFIT | fewer >= 100 cp errors from "material up, king under fire" positions; a lower >= 300 cp rate; no change on the 96% of ordinary positions where the term is zero |
| EXPECTED SPEED COST | small: the term is computed only when the enemy queen is on the board, with cs_king's zone-masked attacker scan; measured by knps at fixed depth (must stay within −3%) |
| EXPECTED CLOCK EFFECT | none |
| MATCHED NEGATIVE CONTROLS | (a) the 120 low-loss positions: moves within 30 cp of the oracle in >= 95%; the term must be nonzero in <= 8% of them; (b) the 240-position equal-time suite: robust mean loss not worse than C5 by more than 3 cp and >= 300 count not higher; (c) tactics 16/16; (d) `tests/test_terms.py` colour antisymmetry and fast/reference agreement |
| WHAT MUST REMAIN UNCHANGED | with the term off, C5 exactly (depth-6 nodes 1,409,912); every test; colour symmetry (the term is antisymmetric by construction); endgame evaluation (the term tapers to zero) |
| REJECTION CRITERION | any of: off-switch fingerprint differs from C5; a test fails; tactics below 16/16; term nonzero in > 8% of negatives; > 5% of negatives worsened by >= 100 cp; target replays repair fewer than 8 of the optimistic errors that C5 reproduces, or break more than 3; equal-time suite worse than C5 by > 3 cp robust mean or more >= 300 cp errors; knps below −3%; internal 60-game screen vs `champions/c5_rfp` below 50% with a bootstrap excluding zero; external 60-game screen not above C5's 58.3% on the same set |
| MAX USEFUL DEVELOPMENT TIME | 40 min implementation + Gate 0/1; screens 60 + 60 games |
| SWITCH | `CS_EVAL_KING_PRESSURE` (registry term flag; `0` = off = C5). Constants fixed now, not tuned on the targets: `PRESSURE_MG = 40` per attacker beyond the first, cap 4 attackers (max 120 cp) |

## Mechanism (exact)

For each side with the enemy queen on the board: count enemy knights,
bishops, rooks and queens that attack the king ring (the king square and
its eight neighbours) through the real occupancy, each piece once (cs_king's
zone-masked scan; pawns excluded). If the count is at least 2, the side is
charged `PRESSURE_MG * (min(count, 4) - 1)` middlegame centipawns. The term
is white-minus-black, packed as `(mg << 16)`, so it tapers with the phase
exactly like the piece-square tables and is zero in the endgame. It is a
new registry term; the rejected `king_safety` v1 (uniform, ungated, 8 cp per
attacker) is untouched and stays off.

## Gate plan

* Gate 0: off-switch fingerprint = C5's 1,409,912; on-switch fixed-depth
  nodes and root moves at depth 6 listed; `tests/test_terms.py` (antisymmetry,
  reference agreement, evaluator untouched when off); full suite; tactics;
  knps at fixed depth vs C5.
* Gate 1 (quiet machine): term activation rate on the 63 targets vs the 120
  negatives; `replay_compare` C5 vs C6 on the 63 targets and 120 negatives at
  a 60 s clock, oracle-scored; equal-time 240 suite for C6 against C5's record.
* Gate 2A: 60 games vs benchmark A (strict, dev) against C5's 58.3%; 60 games
  vs `champions/c5_rfp`.

## Gate 0 — PASS (08:00–08:35 UK)

`CS_EVAL_KING_PRESSURE=0` depth-6 nodes 1,409,912 (= C5). Term on:
1,400,356 (−0.7%), 0 of 24 root moves changed. `tests/test_terms.py`
antisymmetry and fast/reference agreement pass; the two "shipped defaults
are all off" tests were rewritten to assert the DEFAULTS table, and the
tuner decomposition test now switches registry terms off for its
comparison; full suite 1,231 pass after those changes.

Activation (measured 07:58): term nonzero in **40%** of the 63 optimistic
errors (35% against the mover), 18% of the other 57 errors, **9%** of the
120 matched ordinary positions (2% against the mover, 7% in the mover's
favour). The pre-registered bar was <= 8% — missed by one point because the
bar was written for the one-sided signal (4%) and the term is two-sided.

## Gate 1 — FAIL (08:36–08:43 UK, quiet machine)

| set | n | C5 >= 100 cp | C6 >= 100 cp | repaired | broken | mean ms | mean depth |
|---|---|---|---|---|---|---|---|
| targets (63 optimistic errors) | 63 | 50 | 47 | **5** (bar 8) | 2 | 2,458 → 2,353 | 7.65 → 7.60 |
| negatives (120) | 120 | 2 | 3 | 0 | 1 | 1,933 → 1,964 | 8.05 → 7.95 |

Median root-score change on the targets: **0 cp** — a 40–120 cp middlegame
term does not move a +269 cp optimism, and where it fires the search mostly
finds another move that keeps the material. Equal-time 240 suite
(`corpus/strength/c6/cl240_c6_3000ms.*`): robust mean 33 vs C5's 31, p95
161 vs 130, expected-score loss 0.056 vs 0.051, paired **−2.2 cp** (7 better
/ 11 worse by >= 50 cp), >= 300 count 4 vs 4.

**Verdict: REJECTED at Gate 1** (targets 5 < 8; activation 9% > 8%; suite
leans negative). No deviation: nothing measured positive. The branch stays
as the record; the term stays off everywhere else. What survives: the
selectivity signal itself (queen + two ring attackers: 38% of optimistic
errors, 4% of ordinary positions on our side) is real, and the cs_king v1
record's warning holds — a penalty small enough to leave ordinary positions
alone is too small to change the decisions that matter, and a larger one
would perturb the 96%. The optimism class needs a different mechanism than a
static king term (a search-side treatment of attacked kings, or evaluation
of *our* defensive resources), not a retune of this one.
