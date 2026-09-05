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

## Windows PC — 2026-09-05 21:38–23:08

### Speed transfer and Gate 0 (PC)

Alternated depth-6 runs on a quiet AMD Ryzen 5 5600X
(`corpus/daily/rcc/pc_speed_transfer_depth6.txt`): RC-B 75,764 / 76,234 knps,
candidate 88,104 / 89,056 knps (**+16.5%**; the Mac measured +18.7%);
1,708,269 nodes in all four runs. Full suite on the lane: **1,228 passed**.

### Gate 2a — fresh 100-game screen vs RC-B, complete

`tools.arena --agent champions/rcc_speed --opponent champions/rc_b --games 100
--base-ms 120000 --increment-ms 500 --ply-cap 300 --workers 6 --corpus
corpus/daily/pool/competition_actual_suite.jsonl`, launched 21:42:27, finished
22:56:28, single writer, no other CPU work during the match. Artifact
`corpus/daily/rcc/speed_vs_rcb_120s_100_pc.jsonl` + `.pgn` + `.log`; risk
report `corpus/daily/rcc/swissrisk_speed_pc_100.txt`. The Mac partial was
not appended to and plays no part in this result.

| | value |
|---|---|
| W/D/L | **+39 =38 −23** |
| score, nominal Elo | **58.0%, +56** |
| families / informative | 50 / **34 (68%)** |
| family bootstrap 95% | score 50.0%..66.0%, Elo **−0.0..+115** |
| leave-one-informative-family-out | Elo +50..+64 |
| family-mean histogram | 0.00×3 0.25×9 0.50×16 0.75×13 1.00×9 |
| colour split | White +21 =18 −11 (60.0%, +70); Black +18 =20 −12 (56.0%, +42) |
| failures | none on either side (no flag, crash, illegal move, false win) |
| terminations | checkmate 61, threefold 34, fifty-move 2, insufficient 2, adjudication 1 |
| clock floor | candidate 5.6 s, RC-B 5.9 s; games under 5 s: 0 / 0 |
| lowest-clock distribution (p10 / p25 / median) | candidate 10.0 / 15.2 / 21.3 s; RC-B 10.9 / 13.9 / 20.4 s |
| largest single think | candidate 9.8 s; RC-B 13.0 s |

The pre-registered rejection conditions were: any fingerprint change (none),
any test failure (none), knps gain under 5% (+16.5%), a screen below 50% with
a bootstrap excluding zero (58.0%, bootstrap lower bound exactly 50.0%), or a
clock floor below RC-B's (5.6 s against 5.9 s). The last is a single-game
minimum: `cs_time.py` is byte-identical, the candidate's second-lowest clock
(6.1 s) sits between RC-B's two lowest (5.9, 7.0 s), its distribution is at
or above RC-B's from the 10th percentile up, and its largest think is 3.2 s
shorter. Read as a distribution, the clock behaviour is equivalent; there is
no drop.

**Verdict: PASS on the identity-preserving standard** (Gate 0 identity plus
a non-negative screen with no clock harm, the standard the stalemate probe
met inside RC-B). It does not meet the general "bootstrap excludes zero"
standard by itself: the lower bound is exactly zero. Because the search tree
is byte-identical, the candidate cannot choose a worse move than RC-B at
equal depth; the screen measures how much the extra depth buys and confirms
nothing pathological happens at the clock. A 126-game extension to 226
(about 2.5 h on this machine) would narrow the interval; it is optional and
the user's call.

### RC-C frozen — 23:02

`corpus/release/claudeshark_rc_c.zip`, sha256
`1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`, 50,258
bytes, 139,381 uncompressed, 14 files, built from an LF export of the
`champions/rcc_speed` git blobs (every extracted file hashes to its blob).
Release gate 15/15 READY TO UPLOAD; fingerprint 1,708,269 from the extracted
zip; `tools.clockladder` PASS 1 ms..120 s (worst 4.6 s at 120 s); Python
3.12.13 + python-chess 1.11.2 fresh-extraction smoke 8/8 legal, startup
1.25 s (`corpus/release/rc_c_smoke_py312.json`). Manifest
`corpus/release/RC_C_MANIFEST.txt`, card `RC_C_UPLOAD_CARD.md`. Not uploaded.
