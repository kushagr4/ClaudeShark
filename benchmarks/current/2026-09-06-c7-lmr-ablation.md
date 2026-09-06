# Pruning ablation on the 2400-audit search errors — 2026-09-06 12:15–12:47 UK

Question: which pruning mechanism makes C5's deeper search choose a worse
move than a shallow one? Input: the 114 errors the 2400 audit classified
ROOT INSTABILITY (65: a fresh depth-6 search avoids the move the timed
depth-7–9 search played) or UNKNOWN (49: nothing up to 8 s repaired it).
Method: `tools.strength.ablate`, `champions/c5_rfp`, fixed depth 8, one
switch off per configuration, moves oracle-scored at 1M nodes
(`corpus/strength/c7/ablation_depth8.jsonl`).

| configuration | >= 100 cp at depth 8 | repaired (of base's 74) | broken | move differs from base | nodes vs base |
|---|---|---|---|---|---|
| base (C5 as shipped) | 74 | — | — | — | 22.0M |
| `CS_RFP=0` | 71 | 6 | 3 | 12 | +68% |
| `CS_NMP=0` | 74 | 4 | 4 | 11 | +21% |
| **`CS_LMR=0`** | **60** | **20** | 6 | 38 | **+236%** |
| all three off | 60 | 22 | 8 | 39 | +1518% |

Repaired by one switch only: RFP 3, null move 1, **LMR 15**; any single
switch 24. Forty of the 114 positions are not errors at a fresh depth 8 at
all (they were timing/table-state effects in the game), so the base of the
question is 74.

Reading the 20 LMR repairs: the move LMR-off finds is the oracle's best in 9
and within 100 cp in all 20; in 13 it is a quiet (reducible) move; in most
of the 20 the shipped search's root score is **higher** than the LMR-off
score (e.g. +496 vs +468, +141 vs +127, +153 vs +138) — the reductions make
lines look better than they are by cutting the opponent's quiet resources
short at reduced depth, and a reduced search that fails low is never
re-searched. RFP and null-move are minor contributors and are left alone.

Conclusion: **late-move reductions are the dominant search-side cause of
the instability/unknown errors at equal depth** (20 of 74), at a cost that
rules out simply switching them off (3.4× nodes ≈ −1.5 ply at the clock; the
2026-09-05 LMR-schedule screen was flat at equal time). The candidate lane
is a *narrower* reduction — a later start, later 2-ply reductions, or an
exemption for a measurable class of moves — chosen by the follow-up
ablation of milder schedules on the same positions
(`corpus/strength/c7/ablation_lmr_depth8.jsonl`).

## Milder schedules, same 114 positions, depth 8 (12:50–12:56 UK; `ablation_lmr_depth8.jsonl`)

| configuration | >= 100 cp | repaired | broken | nodes vs base |
|---|---|---|---|---|
| base | 74 | — | — | — |
| `CS_LMR_START=4` (reduce from the 5th move) | 70 | 6 | 2 | **+4%** |
| `CS_LMR_START=5` | 73 | 5 | 4 | +6% |
| 2-ply reductions from index 10 and depth 8 | 71 | 6 | 3 | +40% |
| both | 69 | 9 | 4 | +43% |
| (LMR off, from above) | 60 | 20 | 6 | +236% |

Where reductions *start* is not the lever: pushing the start index or the
2-ply threshold buys at most a net +4 to +5 of 74 for the cheap variants.
The damage comes from reductions throughout the tree: a reduced search that
fails low is never re-searched, so a quiet resource for the side to move at
that node is missed. The candidate is therefore a **verification margin**
— re-search at full depth when the reduced search fails low by less than a
margin — and, separately, an exemption for moves that take an attacked
piece out of attack; both are measured next at the same depth on the same
positions before anything is pre-registered.

## Safeguards, same 114 positions, depth 8 (12:58–13:13 UK; `ablation_safeguards_depth8.jsonl`; engine = C7 tree with the switches)

| configuration | >= 100 cp | repaired | broken | net | nodes vs base |
|---|---|---|---|---|---|
| base (C5) | 74 | — | — | — | — |
| verification margin 30 cp (`CS_LMR_VERIFY=30`) | 63 | 19 | 8 | +11 | +100% |
| verification margin 60 | 62 | 19 | 7 | +12 | +133% |
| verification margin 100 | 61 | 20 | 7 | +13 | +170% |
| no-escape exemption (`CS_LMR_NO_ESCAPE=1`) | 67 | 10 | 3 | +7 | **+37%** |
| verify 60 + no-escape | 62 | 19 | 7 | +12 | +165% |
| (LMR off) | 60 | 20 | 6 | +14 | +236% |
| (`CS_LMR_START=4`, from above) | 70 | 6 | 2 | +4 | +4% |

A verification margin recovers nearly the whole LMR-off benefit at 40% of
its node cost, but +100% nodes is about −0.7 ply at the clock; the no-escape
exemption is the most efficient absolute repairer (+7 for +37%); the start
index is the cheapest per node but tiny. None is free, so the arbiter is
equal time: the 240-position suite at 3,000 ms for each of the three
(`corpus/strength/c7/cl240_{noescape,start4,verify30}_3000ms.*`) against
C5's record (robust mean 31, E-loss 0.051, >= 300 count 4).

## Equal time, 240 ordinary positions at 3,000 ms (13:15–13:26 UK; `cl240_{noescape,start4,verify30}_3000ms.*` vs C5's record)

| variant | robust mean (winsorised 500) | paired gain vs C5 | better / worse by >= 50 | >= 100 cp | >= 300 cp | E-loss |
|---|---|---|---|---|---|---|
| C5 | 31.0 | — | — | 19 | 4 | 0.051 |
| no-escape exemption | 30.4 | +0.5 | 6 / 7 | 18 | 4 | 0.052 |
| `CS_LMR_START=4` | 34.5 | **−3.5** | 3 / 9 | 24 | 4 | 0.062 |
| **verification margin 30** | **29.4** | **+1.6** | 8 / 6 | **17** | 4 | **0.048** |

The start-index change costs quality at equal time and is closed. The
verification margin is the candidate (C7): the largest depth-8 repair at a
node cost the clock absorbs. Pre-registration: `2026-09-06-c7-lmr-verify-prereg.md`.
