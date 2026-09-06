# C7 — LMR verification margin (pre-registered 2026-09-06 13:30 UK, before Gate 1)

| field | value |
|---|---|
| CANDIDATE | C7-lmr-verify: `CS_LMR_VERIFY=30` — a late-move reduction whose reduced null-window search fails low by **less than 30 cp** is re-searched at full depth (branch `kushagra/c7-lmr-safeguard`, on top of C5) |
| BASELINE | C5 (`champions/c5_rfp`, development champion) |
| HYPOTHESIS | Reductions throughout the tree make the search choose worse moves than a shallower search would (65 ROOT-INSTABILITY + 49 UNKNOWN errors in the 2400 audit): a reduced search that fails low is never verified, so the opponent's quiet resource is cut short. Verifying the near-misses recovers most of what switching LMR off recovers (19 of 74 depth-8 errors vs 20) at 40% of its node cost, and at equal time the 240-suite is not worse (+1.6 cp). Fewer such errors means fewer result flips and a higher accuracy floor without buying time |
| TARGET ERROR CLASS | ROOT INSTABILITY and UNKNOWN / MIXED (53 of the 102 result-flipping errors in the 2400 audit) |
| TARGET LOW-ACCURACY GAMES | the 20 worst 2400 games (83.6–92.0 on V1) — 20 of their 42 flips are in those two classes |
| TARGET RESULT-FLIPPING POSITIONS | the 114 ablation positions (`corpus/strength/c7_ablation_targets.txt`); at a 60 s clock C5 is expected to reproduce a >= 100 cp loss on roughly half |
| EXPECTED GENERAL BENEFIT | lower >= 100 cp rate and fewer flips in games; internal strength non-negative |
| EXPECTED ACCURACY BENEFIT | on a 60-game internal screen: fewer games below 98 and a higher minimum than C5's paired set; on the 2400 external screen: minimum above C5's 83.6 and fewer than 89 games below 98 |
| EXPECTED SPEED COST | +100% nodes at fixed depth 8 on the error positions (fewer on ordinary positions); equal-time suite already measured at +1.6 cp, so the net at the clock is expected to be near zero in depth and positive in reliability |
| EXPECTED CLOCK COST | none (allocator untouched) |
| MATCHED NEGATIVE CONTROLS | the 120 low-loss positions (`c4_negatives.txt`) at a 60 s clock: <= 5% worsened by >= 100 cp; the 240-suite (done): >= 300 count not higher (4 → 4 ✓); tactics 16/16 |
| REJECTION CRITERION | any of: `CS_LMR_VERIFY=0` fingerprint differs from C5's 1,409,912; a test fails; tactics below 16/16; Gate 1 net repairs (repaired − broken) fewer than 8 among the targets C5 reproduces, or > 5% of negatives worsened; internal 60-game screen vs `champions/c5_rfp` below 48% or with more games below 98 accuracy than C5's side; external 60 games vs benchmark 2400 (dev2400, strict) with a minimum accuracy below 83.6 or a >= 100 cp rate above C5's 6.54% |
| MAX USEFUL TIME | Gate 1 15 min; screens 60 + 60 games (~110 min) |
| SWITCH | `CS_LMR_VERIFY` (integer knob; 0 = C5). Value 30 fixed now; 60/100 were measured at depth 8 (19–20 repairs, +133–170% nodes) and not chosen |

## Gate plan

* Gate 0: off-switch fingerprint = 1,409,912 (done, 12:58); full suite; tactics.
* Gate 1: `replay_compare` C5 vs C7 (`--set-env CS_LMR_VERIFY=30`) on the 114 targets and 120 negatives at a 60 s clock, oracle 1M.
* Gate 2A internal: 60 games vs `champions/c5_rfp`, strict, dev set, with per-game accuracy for **both** sides (the opponent's games are C5's accuracy control on the same positions).
* Gate 2A external: 60 games vs Stockfish UCI_Elo 2400 strict on dev2400 with the accuracy distribution.

## Result — REJECTED at Gate 1 (13:33 UK)

Tactics 16/16 with and without the switch. `replay_compare`, 60 s clock,
C5 vs C7 (`CS_LMR_VERIFY=30`), oracle 1M (`corpus/strength/c7/gate1_*.jsonl`):

| set | n | C5 >= 100 cp | C7 >= 100 cp | repaired | broken | net | mean ms | mean depth |
|---|---|---|---|---|---|---|---|---|
| targets (114 instability/unknown errors) | 114 | 74 | 73 | 11 | 10 | **+1** (bar 8) | 2,044 → 2,232 (+9%) | 7.84 → 7.32 |
| negatives (120) | 120 | 2 | 3 | 0 | 1 | −1 | 1,929 → 2,062 | 8.19 → 7.62 |

At the game clock the verification costs about half a ply, and the half
ply costs as many errors as the verification repairs. The fixed-depth
picture (19 of 74 repaired) was real but not transferable: with this engine
depth is worth more than the reductions cost, exactly as the 2026-09-05 LMR
screen found. **Verdict: REJECTED.** Switch stays off. The branch is the
record. Closed with it: LMR start index (negative at equal time), no-escape
exemption (neutral), verification margin (neutral at best).
