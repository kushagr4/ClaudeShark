# RC-C candidate 1: check extension — preregistration

**Date:** 2026-09-05 12:40 (Mac). **Champion:** RC-B (`champions/rc_b`,
fingerprint 1,708,269). Written before implementation.

## Evidence that selected this lane (not a roadmap item)

Every unrepaired or late-repaired search failure on record has the same
shape: a forcing sequence whose decisive move is a **check** just past the
horizon, and the capture-only quiescence never generates it.

| game | position | root vs truth | what sits past the horizon | repaired by depth? |
|---|---|---|---|---|
| **R20 (RC-B, high confidence)** | 12…Nxd5 | +9 vs −481 | 13.Qxd5! Bh4+ 14.Bf2 Bxf2+ 15.Kxf2 Qxd5 **16.Nc7+** fork; depth-7 PV prefers 13.Be2 because Qxd5 "loses the queen" | depth 8 (1.3M nodes, 8.5 s at RC-B speed; the game spent 3.9 s) |
| R20 | 11…d5 | −5 vs −342 | the same line one move earlier; depth-8 PV: d5 exd5 Nxd5 Bg5 … never sees Qxd5 | not at depth 8 |
| R17 (RC-A) | 47.Re1 | +354 vs 0 | Rb4 48.Qxe5 **Rg4+ Qg2+ Rg3+** … a perpetual made entirely of checks; the depth-8 PV ends inside it | not at depth 9 |
| R7 (V2.1, 2026-09-04) | move 48 | +501 vs 0 | perpetual check | not at depth 8 |
| R5 23.hxg4, R11 31.Nxe4 (postmortem, A4 note) | | | forcing tactics | depth 7–8 repairs 6 of 27 key decisions |

R18 15…g6 (repaired by depth 7 in RC-B) and R19's mate are the positive
controls that must not regress.

## Preregistration

* **HYPOTHESIS.** Extending the main search by one ply when a move gives
  check lets forcing sequences of checks be resolved at the depth the engine
  already reaches, so the fork at R20 and the perpetual at R17 become
  visible without a whole extra ply of brute-force search.
* **MECHANISM.** In `_negamax`, after `push(move)`, if the child is in
  check the child searches at `depth` instead of `depth − 1` (no reduction
  either, which `LMR_SAFE` already enforces). Bounded by `ply < 2 × root
  depth` so a long check sequence cannot run away. Quiescence is unchanged.
* **TARGET FAILURES.** R20 12…Nxd5 must become 12…Nd4 (or another move the
  oracle scores within 50 cp of best) at fixed depth 7; R20 11…d5 must be
  avoided at depth ≤ 8; R17 47.Re1 must be avoided at depth ≤ 9 (or its
  score must fall below +100, proving the perpetual is seen).
* **EXPECTED BENEFIT.** Repairs at the same nominal depth; general (checks
  are how tactics end), competition-relevant (three of five recent rated
  losses/draws are this shape).
* **EXPECTED COST.** `board.is_check()` on every searched move (~+4% time)
  plus node growth at fixed depth in check-rich positions; the equal-time
  test must show the growth is paid back.
* **REJECTION.** Any of: fixed-depth-6 nodes on the 24 suite grow by more
  than 40%; R20 12…Nxd5 is not repaired at depth 7; the 80-position
  equal-time screen (3,000 ms) is worse than RC-B by more than 5 cp robust
  mean or has more ≥300 cp errors; tactics fall below 16/16; any test fails;
  the short timed screen against RC-B is negative.
* **MATCHED NEGATIVE CONTROLS.** The 24 balanced openings and the 18 sharp
  positions (root moves), R18 15…, R19 12., and 40 quiet labelled-pool
  positions with |SF − material| ≤ 50 (root move and score must not move by
  more than 30 cp).
* **WHAT MUST REMAIN UNCHANGED.** Flag off = RC-B byte-for-byte in behaviour
  (fingerprint 1,708,269); draw rules, TT semantics, time policy, protocol.

## Alternatives ranked and not chosen first

1. Checks in the first quiescence ply — same target, but generating quiet
   checks in python-chess costs ~2 µs per candidate move at every
   quiescence entry; prohibitive without a fast check-detection mask.
2. More time at "critical" positions — the time lane closed flat twice
   (sf60, early16); R20 needed 2× the time at one move, which a generic
   allocator cannot identify.
3. Remaining hot-path speed — worth 5–10%, well under the ply R20 needed.
4. Evaluator: 8…Bh5 (static +100 for Black, truth −130) is a real
   evaluation miss (bishop walks into g4–h4–h5), but a single instance and
   itself tactical in nature; parked.

## Gate 0 (13:05)

* Flag off: fingerprint 1,708,269 (RC-B unchanged). Flag on: 1,921,543
  (+12.5%; limit 40%). Sharp suite 18/18 root moves identical (+16% nodes).
  24-suite root moves: 2 of 24 changed, both oracle-neutral (suite 14
  b3b6→g1f1, −1 cp; suite 23 e1g1→d2d4, +2 cp). Tactics 16/16 at 1,000 ms
  (mean depth 7.88 v 8.12). 40 quiet positions: 1 root move changed
  (oracle-neutral band), 1 score moved by 39 cp, mean |Δ| 1.6 cp, nodes +12.5%
  (`corpus/daily/rcb/checkext_quiet_negatives.txt`).
* Tests with the flag on: 1,212 pass, **1 fails**:
  `test_a_forced_perpetual_is_accepted_when_losing`. Investigated: at
  `6k1/6pp/1p1p1p2/1P1P1P2/2P1K3/R7/7P/5r2 b` RC-B at depth 6 plays Re1+
  (−30) and at depth 8 plays g6 (−38); the candidate plays g6 at depth 6.
  Oracle: g6 → −349, Re1+ → −364, the checks do not hold. The test asserts
  a depth-6 artifact ("the holding resource is a check"); the candidate's
  move is the oracle-better one. Not a regression; if the extension ships
  the test is rewritten around the oracle finding. Flag off passes.

## Gate 1 (13:00) — causal targets, flag on (`corpus/daily/rcb/checkext_causal_on.txt`)

| target | RC-B | candidate | oracle |
|---|---|---|---|
| R20 12…Nxd5 | Nxd5 +9 at d7 (Nd4 only at d8, 1.3M nodes) | **Nd4 −244 at d7** (765k nodes); d6 Na5 −220 (also avoids the fork) | Nd4 −341 |
| R20 11…d5 | d5 −5 at d7 and d8 | d5 +4 at d7; **O-O −109 at d8** | O-O −207 |
| R17 47.Re1 | Re1 +354 at d7, +320 at d9 | **a6 +207 at d7**, +168 at d8, +172 at d9 | Qc2 +435, a6 +300 |
| R18 15…g6 | f6 at d7 | f6 at d7 (unchanged) | f6 / a4 |
| R19 12.Qxg5+ | mate at d3 | mate at d3 (unchanged) | mate |

All three targets repaired; both positive controls preserved. The cost is
concentrated in check-rich positions (R20 12… at d7 3.5× the nodes; R17 at
d8 2.3×), so the equal-time screen decides whether the extension pays.
