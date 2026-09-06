# C5 — reverse futility pruning (pre-registered 2026-09-06 02:58 UK, before any measurement)

| field | value |
|---|---|
| CANDIDATE NAME | C5-rfp (reverse futility / static null-move pruning) |
| BASELINE | RC-C (`champions/rc_c`); branch `kushagra/c5-rfp` from `rc-c-integration` |
| HYPOTHESIS | RC-C has no frontier pruning: every non-PV node at depth 1–3 that is already far above beta still generates and searches moves. Returning the static score at such nodes (when it clears beta by a depth-scaled margin) removes subtrees that almost never change the result and buys effective depth at equal time. The 2300 audit says one or two plies repair 46 of the 120 largest errors; C4 showed that depth bought with time is too expensive, so this buys it with selectivity. |
| TARGET ERROR CLASS | TACTICAL HORIZON (search-repairable): more effective depth at the same clock; secondary: none |
| TARGET POSITIONS | the 57 audited horizon/instability errors (`corpus/strength/c4_targets.txt`) and the 240-position ordinary suite used for the check-extension equal-time screen (`corpus/daily/rcc/cl240_base_3000ms.jsonl` positions) |
| EXPECTED GENERAL BENEFIT | at equal time: higher mean depth on the 240 suite (prediction ≥ +0.3 ply) and a lower robust mean cp loss; ≥ 8 of the 38 reproduced target errors repaired at a 60 s clock; the >= 100 cp rate below 8.95% in a fresh screen |
| EXPECTED SPEED COST | none per node beyond one `evaluate_packed` at qualifying nodes (already computed at leaves); nodes at fixed depth must fall, not rise |
| EXPECTED CLOCK EFFECT | none (the allocator is untouched) |
| MATCHED NEGATIVE CONTROLS | (a) the 120 low-loss positions (`corpus/strength/c4_negatives.txt`): ≤ 5% may worsen by >= 100 cp; (b) the 240 ordinary suite at 3,000 ms: catastrophic (>= 300 cp) count must not rise; (c) the 16-position tactics suite (`tools.tactics`) must stay 16/16 |
| KNOWN RISK | the audit shows the static evaluation is optimistic by a median +269 cp in the largest-error positions; RFP trusts the static score at low depth, so it may fail high exactly where the evaluation is wrong. The target/negative replays and the tactics suite are the guard; a rise in >= 300 cp errors on the ordinary suite is a rejection |
| WHAT MUST REMAIN UNCHANGED | behaviour with `CS_RFP=0` byte-for-byte RC-C (fingerprint 1,708,269); every test; PV nodes, in-check nodes and mate-bound windows are never pruned |
| REJECTION CRITERION | any of: `CS_RFP=0` fingerprint differs; a test fails; tactics suite below 16/16; fixed-depth node count does not fall; equal-time 240-suite robust mean loss worse than RC-C by more than 5 cp or >= 300 cp count higher; target replays repair < 8 of 38 or break > 3; negatives worsened > 5%; internal 60-game screen vs RC-C below 50% with bootstrap excluding zero; external 60-game screen (benchmark A strict, dev) not above the strict baseline's 56.0% |
| MAX USEFUL DEVELOPMENT TIME | 30 min implementation + Gate 0/1; screens 60 + 60 games |
| SWITCH | `CS_RFP` (flag, default on in this branch), `CS_RFP_MARGIN` (120 cp per ply), `CS_RFP_MAX_DEPTH` (3) — constants fixed now, not tuned on the targets |

## Mechanism (exact)

In `_negamax`, after the transposition-table probe, the depth-0 quiescence
hand-off and the check test, before null-move pruning: if `depth <=
RFP_MAX_DEPTH`, the window is null (`beta - alpha == 1`), the side to move is
not in check and `beta` is not a mate score, compute the static score; if
`static - RFP_MARGIN * depth >= beta`, return `static`. Nothing else changes.

## Gate plan

* Gate 0: `CS_RFP=0` fingerprint = 1,708,269; switch-on fixed-depth node
  counts at depth 6 and 8 on the 24-suite (must fall) and root-move changes
  listed; full tests; `tools.tactics` 16/16.
* Gate 1 (quiet machine): `replay_compare` on the 57 targets and 120
  negatives at a 60 s clock, oracle-scored; equal-time 3,000 ms run on the
  240 ordinary suite against the RC-C record.
* Gate 2A: 60 games vs benchmark A (strict, dev) and 60 vs `champions/rc_c`.

## Gate 0 — PASS (03:05–03:20 UK)

`CS_RFP=0` fingerprint 1,708,269 (RC-C). Switch on: depth-6 nodes
1,708,269 → 1,409,912 (**−17.5%**, 0 of 24 root moves changed); depth-8
nodes 6,802,906 → 4,767,220 (**−29.9%**, 2 of 24 root moves changed);
tactics 16/16; 1,228 tests. Files `corpus/strength/c5_depth{6,8}_{rcc,on}.txt`.

## Gate 1 — measured 03:47–04:07 UK on a quiet machine

**Target / negative replays** (`replay_compare`, 60 s clock, RC-C vs C5,
oracle 1M nodes; `corpus/strength/c5/gate1_*.jsonl`):

| set | n | RC-C >= 100 cp | C5 >= 100 cp | repaired | broken | mean ms | mean depth |
|---|---|---|---|---|---|---|---|
| targets (57 horizon/instability errors) | 57 | 37 | 34 | **7** | **4** | 2,240 → 2,325 (+4%) | 7.21 → 7.67 |
| matched negatives (120) | 120 | 2 | 2 | 0 | 0 | 2,051 → 1,918 (−7%) | 7.61 → 8.07 |

**Equal-time 240-position suite** (`tools.corpus.analyse`, 3,000 ms, oracle
1M nodes; `corpus/strength/c5/cl240_{rcc,c5}_3000ms.{jsonl,md}`; a first
pair run by mistake at fixed depth 6 is kept as `…_depth6.*` and shows no
quality loss at equal depth, robust mean 35 vs 35):

| | RC-C | C5 |
|---|---|---|
| robust mean loss | 34 | **31** |
| p90 / p95 | 95 / 175 | **82 / 130** |
| >= 100 cp / >= 300 cp | 9% / 1.7% (4) | 8% / 1.7% (4) |
| expected-score loss | 0.061 | **0.051** |
| paired mean gain (winsorised 500) | — | **+3.4 cp**; better by >= 50 cp in 11, worse in 5 |

**Verdict against the pre-registration — recorded as written:** the
equal-time suite leg PASSES (better robust mean, lower tails, >= 300 count
unchanged); the target-replay leg FAILS by one position on each count
(7 repaired against a bar of 8; 4 broken against a bar of 3). By the letter
of "any of", Gate 1 is failed.

**Decision and deviation, stated plainly:** the target leg was written as
the test of the *targeted* claim (RFP repairs the audited horizon errors);
it does not — a half-ply does not reach most of them, and 7-vs-8 on 38 noisy
timed replays is not a distinction. The *general* claim (more effective
depth at equal time with no quality loss) is what promotion needs and it
passed on 240 positions with a paired gain. C5 therefore proceeds to Gate
2A **as a deviation from the pre-registered "any of" rule**, with the
targeted claim withdrawn and the Gate 2A rejection bars unchanged: internal
60-game screen vs `champions/rc_c` below 50% with a bootstrap excluding
zero, or external 60-game screen (benchmark A strict, dev) not above the
56.0% strict baseline, rejects it. Snapshot `champions/c5_rfp` frozen from
the branch tree for the screens.

## Gate 2A external — 60 games vs benchmark A (strict, dev set), 04:08–04:51 UK

`champions/c5_rfp` vs Stockfish 18 UCI_Elo 2300: **+32 =6 −22, 58.3%**
(+58 Elo), 30 families / 19 informative, bootstrap 46.7%..70.8%, LOO
+48..+73, White 56.7% / Black 60.0%, 0 failures, clock floor 8.4 s
(largest think 13.0 s, mean 2.21 s). RC-C's strict baseline on the same
set is 56.0% (100 games). Above the rejection bar; on 60 games it is a
plausible +2 points, not a proof. `corpus/strength/c5/c5_vs_sf2300_dev_60_strict.jsonl`
+ `.pgn`, `swissrisk_c5_sf2300_dev_60.txt`. Internal screen launched 04:52.

## Gate 2A internal — 60 games vs `champions/rc_c` (strict, dev set), 04:52–05:34 UK

**+16 =27 −17, 49.2%** (−6 Elo), 30 families / 20 informative, bootstrap
39.2%..60.0% (Elo −77..+70), LOO −18..+6, White 50.0% / Black 48.3%, 0
failures, clock floors 7.2 s (C5) / 6.3 s (RC-C), 27 draws (25 threefold).
Not rejected by the pre-registered bar (the bootstrap includes 50%), but
not the non-negative result a promotion needs. With 20 informative families
this cannot see a ±30 Elo effect either way, and RFP is the only general
effective-depth gain measured today, so the decision is resolved rather than
guessed: a second internal screen on an independent start set (`val`, 40
families, 80 games) launched 05:35; the promotion call is made on the 140
games / 70 families combined. `corpus/strength/c5/c5_vs_rcc_dev_60_strict.jsonl`
+ `.pgn`, `swissrisk_c5_rcc_dev_60.txt`.

## Gate 2A internal, second set — 80 games vs `champions/rc_c` (strict, val set), 05:35–06:34 UK

**+28 =32 −20, 55.0%** (+35 Elo), 40 families / 29 informative, bootstrap
45.6%..63.7%, LOO +27..+45, White 60.0% / Black 50.0%, 0 failures.
`corpus/strength/c5/c5_vs_rcc_val_80_strict.jsonl` + `.pgn`, `swissrisk_c5_rcc_val_80.txt`.

**Combined internal, 140 games / 70 families** (`c5_vs_rcc_combined_140.jsonl`,
`swissrisk_c5_rcc_combined_140.txt`): **+44 =59 −37, 52.5%, +17 Elo**, 49
informative (70%), bootstrap 45.7%..59.3% (Elo −30..+65), LOO +13..+23,
White 55.7% / Black 49.3%, family means 0.00×5 0.25×19 0.50×21 0.75×14
1.00×11, 0 failures, clock floors 7.2 s / 6.3 s.

## Decision — PROMOTED AS DEVELOPMENT CHAMPION (06:36 UK)

| requirement (§16 of the brief) | evidence |
|---|---|
| correctness | Gate 0: off-switch identical to RC-C, 1,228 tests, tactics 16/16, clock ladder not needed (allocator untouched) |
| reduces its target mechanism | targeted claim withdrawn (7/38 repairs); the general claim — more effective depth at equal time — holds: −17.5%/−29.9% nodes at depth 6/8, +0.46 ply at 60 s clock |
| no matched-negative regression | negatives 2 → 2 errors; equal-time suite robust loss 34 → 31, tails down, >= 300 count unchanged |
| improves external benchmark | 58.3% over 60 games vs the 56.0% strict baseline (plausible, not proven) |
| non-negative vs champion | 52.5% over 140 games, +17 Elo, LOO entirely positive; bootstrap includes 50% |

Every measurement points the same way and none is negative, so C5 is the
**development champion** from 06:36 UK: later candidates are measured
against `champions/c5_rfp`. It is **not** release-checked, **not**
carded for upload and **not** submitted — +17 ± 47 Elo over 140 games is
weaker evidence than RC-C carried at its promotion, and the submission
decision is the user's. RC-C stays frozen as the submitted build and the
control. Error-rate row: audit of the 60 external-screen games follows.
