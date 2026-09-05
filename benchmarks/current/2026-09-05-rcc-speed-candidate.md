# RC-C candidate 3: identity-preserving speed (incremental piece-square sum + inline capture generation)

**Date:** 2026-09-05 14:15 (Mac). **Champion:** RC-B. **Snapshot:**
`champions/rcc_speed` (working tree at commit `f2543bd`; no flags, nothing
to switch on). Chosen after the check-extension lane closed: the evidence
that speed converts to strength in this engine is RC-B itself (+17% knps →
+59 Elo at the clock), and R18's 15…g6 / R20's 12…Nxd5 were both repaired by
exactly one more ply.

## Preregistration

* **HYPOTHESIS.** The search tree is left byte-identical and the engine
  reaches more depth per second, so every timed result moves in RC-B's
  favour direction or not at all.
* **MECHANISM.** (a) `cs_eval.pst_packed` computes the white-positive packed
  piece-square sum once at the root; `pst_delta(board, move)` updates it
  before every push (moving piece, captured piece, en passant, promotion,
  castling rook); `evaluate_packed(board, packed)` does everything
  `evaluate` did except the 30-piece scan. The sum is threaded through
  `_negamax` and `_quiescence` as a parameter (direct callers may pass none
  and get the full sum). (b) `cs_ordering.legal_captures(board, in_check)`
  reproduces `generate_legal_captures()` out of check without the checkers
  scan and without a Python safety call per move.
* **WHAT MUST REMAIN UNCHANGED.** Node counts (fingerprints 1,708,269 and
  1,852,716), every root move, every evaluation value (the sum is asserted
  equal to the full recomputation at every leaf in
  `tests/test_pst_incremental.py`; the capture sequence is asserted equal to
  python-chess's on 3,000+ positions in `tests/test_legal_captures.py`).
* **REJECTION.** Any fingerprint change; any test failure; knps gain under
  5%; the 100-game timed screen against RC-B below 50% with a bootstrap that
  excludes zero, or a clock floor below RC-B's in the same match.
* **What the timed screen can and cannot show.** An identical tree cannot
  be *weaker*; the screen is a non-regression check (clock, protocol,
  nothing pathological) and an estimate of how much the depth buys. A
  100-game screen cannot resolve ±20 Elo, so promotion rests on Gate 0
  identity plus a non-negative screen, the same standard the stalemate probe
  met inside RC-B.

## Gate 0

| | RC-B snapshot | candidate |
|---|---|---|
| depth-6 suite nodes | 1,708,269 | **1,708,269** |
| sharp suite nodes | 1,852,716 | **1,852,716** |
| root moves | — | identical (implied by identical trees) |
| tests | 1,213 | **1,227** pass, 1 skip (two new agreement tests) |
| knps, alternated twice, quiet machine | 152,764 / 152,190 | **180,973 / 181,142 (+18.7%)** |
| of which the capture generator alone | | +1.7% (measured separately, `276780f`) |

Against RC-A (118.7 knps on this machine) the chain is now +53% nodes per
second at a near-identical tree.

## Gate 2a — launched 14:12

`tools.arena --agent champions/rcc_speed --opponent champions/rc_b --games 100
--base-ms 120000 --increment-ms 500 --ply-cap 300 --workers 8
--corpus corpus/daily/pool/competition_actual_suite.jsonl`, output
`corpus/daily/rcc/speed_vs_rcb_120s_100.jsonl` + `.pgn`. Result appended when
complete.

### Gate 2a — STOPPED FOR PC HANDOFF at 14:42 (59 of 100 games), NON-DECISIVE

The user moved development to the PC while the screen was running. The
process tree (arena, 16 runners, caffeinate) was terminated cleanly at
14:42:40 and verified gone; the 59 completed game rows were preserved and
the artifact renamed
`corpus/daily/rcc/speed_vs_rcb_120s_100.PARTIAL-NON-DECISIVE-STOPPED-FOR-PC-HANDOFF.jsonl`
(+ `.txt` summary). The arena writes its PGN only at the end, so no PGN
exists for this run; the games in flight were lost.

Partial read, **not strength evidence**: +18 =25 −16, 51.7%, +12 Elo, 30
families / 19 informative, family bootstrap −47..+73, no failures. It is
consistent with "identical tree, more depth" and proves nothing; the screen
must be rerun in full (100 games, then 226 if positive) on the PC before
this candidate can be called RC-C.

**Status at handoff: candidate 3 has passed Gate 0 (identity + 1,227 tests
+ +18.7% knps) and awaits Gate 2.** It is not champion; RC-B is.
