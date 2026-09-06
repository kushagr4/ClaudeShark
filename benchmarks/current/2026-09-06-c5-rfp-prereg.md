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
