# RC-B upload card — 2026-09-05 12:05 local (Mac), final for the 1 PM decision

**RC-B 1PM DECISION: GO**

**RECOMMENDATION:** **SUBMIT** (replaces RC-A; RC-A stays the fallback archive)

**BUILD NAME:** RC-B / C1 staged move picker + fast stalemate probe

**REPLACES:** SUBMITTED RC-A / exact rated-v1 (`corpus/release/claudeshark_rated_v1_rc_a.zip`, 39,125 bytes, SHA-256 `3a89bf3e2fbfab0b7e07baf2fff7e0edf2288fc2a4d372e8eda823db1767ff9b`, commit `98c48c8`)

**EXACT COMMIT:** `3d918a5db6233e9f0c7a4dcbee6713b83f758c11` on `mac-full-development` (the commit that flipped the picker default and froze `champions/rc_b`); the 14 shipped files are byte-identical to `champions/rc_b/` and to the working tree at every later commit on the branch (only tools, records and data changed afterwards). Verified 12:00 from the frozen files: zip sha256 `f7b94b65…c9c1a`, 48,167 bytes, 14 files, 131,795 uncompressed; `unzip` → `diff -rq` against `champions/rc_b` and `cmp` against the working tree: no differences; no network, subprocess or file-write imports in the shipped modules; the only `print` is inside the `CLAUDESHARK_DEBUG` telemetry block, which defaults off; no data files shipped.

**ZIP PATH:** `corpus/release/claudeshark_rc_b.zip`

**ZIP BYTES:** 48,167

**UNCOMPRESSED BYTES:** 131,795 in 14 files (`agent.py`, `cs_constants.py`, `cs_drawish.py`, `cs_eval.py`, `cs_king.py`, `cs_kingpawn.py`, `cs_mopup.py`, `cs_ordering.py`, `cs_passed.py`, `cs_search.py`, `cs_see.py`, `cs_terms.py`, `cs_time.py`, `cs_tt.py`; all text, all at the zip root; the three V2 term modules ship with every term off, exactly as the C1 snapshot that played the match)

**FULL SHA-256:** `f7b94b6507c39f32c6ba40f453e302812ba0bfbce1c8be16d2129ecb458c9c1a`

**STARTUP:** 1.62 s on CPython 3.12.14 with python-chess 1.11.2 (fresh extraction, import including warm-up); budget 90 s

**DEPTH-6 FINGERPRINT:** 1,708,269 nodes over the 24-position suite from the extracted zip (RC-A: 1,712,405; the 0.24% difference is the picker's fresher history at the quiet tail, 0 of 42 root moves changed)

**SPEED:** 154 knps on the Mac against RC-A's 119 knps on the same machine (+30%): +17% from the picker, +11% from the probe, both measured alternated on a quiet machine

**TESTS:** 1,213 passed, 1 skipped (`pytest -q`, 1 min 25 s, 2026-09-05 11:39)

**RELEASE CHECK:** 15 of 15 PASS, READY TO UPLOAD (11:41): contents, size, no native binaries, imports resolve, no requirements.txt, no dev-only or network imports, no absolute paths, no filesystem writes, 60 probes legal and inside every clock, smoke game from the extracted zip (white by checkmate); plus the fresh-extraction smoke under Python 3.12.14 (seven positions including in-check, one-legal-move and a 700 ms clock: all legal, max 2.54 s) and `tools.clockladder` PASS from 1 ms to 120 s with nothing over its hard deadline (worst think 6.3 s at 120 s)

**FAMILY-LEVEL EVIDENCE (required alongside the game count):** 113 start families, **80 informative (71%)**; family-mean histogram 0.00×6, 0.25×18, 0.50×33, 0.75×44, 1.00×12; family bootstrap 95% Elo +25..+95 (score 53.5%..63.3%); leave-one-informative-family-out Elo **+56..+63** (no single-family dependence); as White 55.8% (+40), as Black 61.1% (+78); no flag, crash, illegal move, false win or abnormal timeout on either side (`corpus/daily/time/c1staged_family_sensitivity.txt`).

**SLEEP SENSITIVITY: PASS.** The Mac slept 10:20:46–11:31:35 during the match. The 8 games in flight (wall time 3,690–4,517 s against a 254 s median; families 105–109) had ordinary per-move spends (largest 7.4 s; the referee's per-move clock is monotonic). Excluding those 8 games and their 5 families entirely: **+79 =93 −44, 58.1%, +57 Elo, family bootstrap +21..+92, 77 informative families, leave-one-out +54..+61**. Excluding only the 8 games: 58.0%, +56 Elo, bootstrap +22..+91. The conclusion does not depend on the affected games. The original artifact was not altered.

**LIVE-GAME REGRESSION CHECK (RC-A rounds 16–19, not an Elo test):** at 16 causal positions from the four games RC-B is identical to RC-A at 15 and oracle-better at the one where it differs: R18 15…g6 (RC-A, depth 6 at 2.5 s, loses a piece, −319) becomes 15…f6 (RC-B, depth 7 at 2.5 s, −15 against the oracle's own line). R17's 47.Re1 (the move that threw away +518 into a perpetual) is played by both and not repaired by depth 9; R19's mate is found identically. Record: `2026-09-05-rca-live-games-r16-r19.md`.

**STRENGTH EVIDENCE (the reason to submit):** `champions/c1_staged` with the picker on, against `champions/rated_v1` (= RC-A), 226 paired games on the organiser's own 113 start positions at the competition clock (120 s + 0.5 s, 300-ply cap): **+83 =98 −45, 58.4%, +59 Elo, cluster bootstrap +25..+93**, 80 informative families, leave-one-family-out +56..+63, as White +40 / as Black +78. Zero flags, crashes or illegal moves on either side; lowest clock held 5.7 s against RC-A's 4.7 s; largest think 10.3 s. Record: `2026-09-05-c1-staged-move-picker.md`, raw `corpus/daily/time/games/c1staged_vs_ratedv1_120s.jsonl` + `.pgn`, risk report `corpus/daily/time/swissrisk_c1staged.txt`. The stalemate probe added afterwards changes no node (fingerprints identical in every flag state, agreement test on thousands of positions) and only adds speed.

**RULE COMPATIBILITY:** Python 3.12 (runs on 3.12.14); stdlib + python-chess only; no torch/numpy/numba needed; no native binary; no network, subprocess or file writes; no book, no tablebase, no engine data; readable source; one thread; 120 s + 0.5 s allocator unchanged from RC-A; 131,795 bytes against the 50 MB limit

**WHY:** RC-B is RC-A's search made 30% faster with the tree left essentially alone, and it is the first candidate in the project to beat rated-v1 on the competition distribution at the competition clock with a bootstrap that excludes zero. Every evaluation-side candidate today (Lane B static attack signals) and every search-tuning candidate (LMR schedule) was measured and closed; nothing else is stacked on this build.

**KNOWN RISKS:**
* RC-B has not itself played a rated game; RC-A's one rated game today (Rated 16, win) is inherited evidence for everything except the two speed changes.
* The match ran while the Mac slept for about 70 minutes; per-move clocks are monotonic and the six games in flight resumed normally (no flags, largest think 7.4 s), so nothing was discarded, but it is on record.
* The engine's real weaknesses (attack blindness, conversion of won endings: Rated 16 fell from +529 to +22 before winning) are unchanged; this upload buys depth, it does not fix them.
* Eligibility for the final Swiss still needs written organiser clarification.

**UPLOAD:** not performed by the agent. **Upload this exact file: `corpus/release/claudeshark_rc_b.zip`, SHA-256 `f7b94b6507c39f32c6ba40f453e302812ba0bfbce1c8be16d2129ecb458c9c1a`.** Verify the hash after download/upload with `shasum -a 256 corpus/release/claudeshark_rc_b.zip`. If the user uploads, record the time and confirm the SHA-256 in `V2_ACTIVE_STATE.md` section 1; every rated game after that is RC-B.
