# Lane B: no narrow static king-attack signal separates the rated-game attacks

**Date:** 2026-09-05 (Mac). **Question, pre-registered in `V2_ACTIVE_STATE.md`
section 6 and `ENGINE_OPPORTUNITY_MAP.md` B1:** is there a *small* static
signal (safe checks, escape squares, attacker/defender counts on the king
ring, pinned defenders) that separates the attacks the engine did not see in
rounds 1, 3, 5, 10 and 11 from material balances that are what they look
like? Broad king safety was already rejected globally, so the test is for the
smallest separating signal, not a new king-safety term.

Tool: `tools/daily/laneb_signals.py`; output `corpus/daily/laneb_signals.txt`.

## Set construction

* Label, white view: Stockfish 18 (1M nodes, existing labels) minus bare
  material (100/320/330/500/900). Middlegame only: both queens on, at least
  16 pieces.
* **Positives** (1,068; 271 from the rated games): |label| ≥ 200, a dynamic
  factor worth two pawns that a material count cannot see.
* **Negatives** (2,974; 117 *hard* negatives with |material| ≥ 200): |label| ≤
  100, the material count is right.
* Sources: every ply of the 15 rated games (both sides to move) and the
  6,203-position labelled TWIC pool. The frozen competition holdout is in
  neither.
* Each signal is a white-view difference D = f(White attacking Black's king)
  − f(Black attacking White's king). A term built on D needs |D| large and
  sign-aligned with the label on positives and |D| small on negatives.

## Result: none of the five signals separates

| signal | AUC (|D| positives > negatives) | sign agrees with label on positives | positives where D = 0 | mean |D| positives / negatives / hard negatives |
|---|---|---|---|---|
| safe checks | 0.580 | 18% | 74% | 0.68 / 0.14 / 0.35 |
| escape squares | 0.580 | 34% | 26% | 1.29 / 0.94 / 1.18 |
| ring attackers | 0.610 | 36% | 39% | 0.83 / 0.49 / 0.84 |
| ring attackers − defenders | 0.532 | 39% | 22% | 1.40 / 1.26 / 1.21 |
| pinned defenders | 0.535 | 12% | 79% | 0.22 / 0.15 / 0.20 |

Restricted to the rated-game positives the picture is the same (best AUC
0.632, sign agreement 24–38%). On the hard negatives, where a material
deficit is genuinely a deficit, the signals are as large as on the positives,
so any weight on them would mis-score real material as often as it rescued
an attack.

## The five named sequences, position by position

The postmortem's attack sequences (round 1 plies 19–42, round 5 31–40, round
10 14–29, round 11 19–52, round 3 35–40) were printed with the Stockfish
score, material, the rated-v1 root and static score where we moved, and all
five signals. What the table shows:

* **Round 1, plies 19–28 and round 11, plies 19–41: every signal is exactly
  zero** while Stockfish already reads −200 to −350 against us and the root
  sits at +61..−66. The attack is not yet on the king ring; it is in piece
  placement and structure, and no king-zone count can see it.
* **Round 10, plies 14–29:** the escape-square signal has the wrong sign the
  whole way (the attacked side's king has *more* free squares), while
  Stockfish reads +114..+517 for the attacker.
* Where the signals do fire (round 1 from ply 29, round 5, round 11 from ply
  45) the root is already moving (−100..−470) and still under-reads by
  200–800; sign agreement there is good for safe checks (21/25) and ring
  attackers (32/42) but the size of the miss is not proportional to the
  counts.

## Decision

The static king-zone sub-lane of Lane B is **closed**: the early phase of
every named attack is invisible to king-zone counts, and the late phase is
partly seen by the search already. This is the same conclusion the global
king-safety term reached from the other side (coin-flip at 49 changed moves
over the 240 suite). What remains of Lane B is a *search* question: the
positions are "correct move, wrong score" and depth 7–8 repairs one in four,
so the lever is depth (lane 6, speed) and possibly a check extension (A4),
not a static evaluation term. Nothing was tuned; no coefficient was chosen;
the validation and holdout splits were not read.
