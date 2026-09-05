# RC-A upload card — 2026-09-05 06:55 local

**RECOMMENDATION:** **SUBMIT**

**BUILD NAME:** RC-A / exact rated-v1 (RATED-V1 HISTORICAL BASELINE, unchanged)

**REPLACES:** SUBMITTED V2.1 KING-PAWN (`corpus/v2/kp/submission_v2_1_kingpawn.zip`, 43,489 bytes, SHA-256 `a8b95a5cab3e33aaac6e5d3e686eb7f292d3a600a115e18e077b9622f35bbd0a`, commit `10c9277`)

**EXACT COMMIT:** `98c48c89b3a8142e6567e5f46b2d2036df7297d1` (tag `rated-v1`, also `main`); every shipped file is byte-identical to `champions/rated_v1/` and identical to the tag's tree once line endings are normalised

**ZIP PATH:** `corpus/release/claudeshark_rated_v1_rc_a.zip`

**ZIP BYTES:** 39,125

**UNCOMPRESSED BYTES:** 106,863 in 11 files (`agent.py`, `cs_constants.py`, `cs_eval.py`, `cs_king.py`, `cs_mopup.py`, `cs_ordering.py`, `cs_passed.py`, `cs_search.py`, `cs_see.py`, `cs_time.py`, `cs_tt.py`; all text, all at the zip root)

**FULL SHA-256:** `3a89bf3e2fbfab0b7e07baf2fff7e0edf2288fc2a4d372e8eda823db1767ff9b`

**STARTUP:** 1.63 s on CPython 3.12.13 with python-chess 1.11.2 (fresh extraction, import including warm-up); 1.49 s on the 3.13 venv; budget 90 s

**DEPTH-6 FINGERPRINT:** 1,712,405 nodes over the 24-position suite (`tools.bench --depth 6 --engine champions/rated_v1`)

**TESTS:** 1,202 passed (`pytest -q`, 1 min 58 s, 2026-09-05 03:50)

**RELEASE CHECK:** 15 of 15 PASS, run twice (03:52 with `--keep`, 06:45 independently): contents, size, no native binaries, imports resolve on the platform, no requirements.txt, no dev-only or network imports, no absolute paths, no filesystem writes, 60 probes legal and inside every clock, smoke game from the extracted zip; plus the 06:47 fresh-extraction run under real Python 3.12.13 (six positions including in-check, one-legal-move and a 700 ms clock: all legal, max 3.75 s) and `tools.clockladder` PASS from 1 ms to 120 s with nothing over its hard deadline

**RULE COMPATIBILITY:** Python 3.12 (every file parses under the 3.12 grammar and runs on 3.12.13); stdlib + python-chess only; no torch/numpy/numba needed; no native binary; no network, subprocess or file writes; no book, no tablebase, no engine data; readable source (the only Stockfish mentions are docstrings about how terms were measured); one thread; 120 s + 0.5 s allocator with 0 flags, crashes or illegal moves in 521 timed games tonight and a lowest clock of 6.1 s; 106,863 bytes against the 50 MB limit

**WHY:** The submitted V2.1 king-pawn build adds one endgame term to this exact engine. On the organiser's own 113 start positions it scored 45.8% against rated-v1 over 226 paired fixed-depth games (−29 Elo, 54 informative families, cluster bootstrap −56..−5 excluding zero), and in the fifteen rated games it played, its distinguishing term changed the move at 5 of 90 critical positions without changing any outcome. RC-A is the same engine without that term: the only build that is not measurably weaker than anything on the competition distribution, with a validated release gate, a full test pass and a content match to an archive that was uploaded before. Every other candidate tested tonight (two time policies at the competition clock) measured flat or negative and lowered the clock floor.

**KNOWN RISKS:**
* RC-A has never itself played a rated game; its deployment evidence is inherited from V2.1, which made the same decisions at 85 of 90 critical rated positions.
* The engine's real weaknesses (attack blindness, conversion of won endings) are shared by RC-A and V2.1; this upload removes a regression, it does not fix them.
* Eligibility for the final Swiss depends on the UK-student rule; get written organiser clarification before relying on the seat.
