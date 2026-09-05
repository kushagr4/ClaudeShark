# RC-C upload card — 2026-09-05 23:10 UK (Windows PC)

**RECOMMENDATION:** **SUBMIT** (replaces RC-B; RC-B stays the fallback archive, RC-A the second fallback)

**BUILD NAME:** RC-C / RC-B + identity-preserving speed (incremental piece-square sum, inline out-of-check capture generation)

**REPLACES:** SUBMITTED RC-B (`corpus/release/claudeshark_rc_b.zip`, 48,167 bytes, SHA-256 `f7b94b6507c39f32c6ba40f453e302812ba0bfbce1c8be16d2129ecb458c9c1a`, commit `3d918a5`, uploaded 2026-09-05 12:01 UK)

**EXACT COMMIT:** engine files at `f2543bd` on `kushagra/rcc-speed-validation` (unchanged through the branch head `6f37820`; snapshot `champions/rcc_speed`). The archive was built from an LF export of the `champions/rcc_speed` git blobs and every extracted file hashes to its blob (`git hash-object` = `HEAD:champions/rcc_speed/<file>` for all 14). Differs from RC-B in exactly three files: `cs_eval.py`, `cs_ordering.py`, `cs_search.py`; `cs_time.py` and the other ten are byte-identical to RC-B.

**ZIP PATH:** `corpus/release/claudeshark_rc_c.zip`

**ZIP BYTES:** 50,258

**UNCOMPRESSED BYTES:** 139,381 in 14 files (`agent.py`, `cs_constants.py`, `cs_drawish.py`, `cs_eval.py`, `cs_king.py`, `cs_kingpawn.py`, `cs_mopup.py`, `cs_ordering.py`, `cs_passed.py`, `cs_search.py`, `cs_see.py`, `cs_terms.py`, `cs_time.py`, `cs_tt.py`; all text, all at the zip root, the same set as RC-B)

**FULL SHA-256:** `1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`

**STARTUP:** 1.25 s on CPython 3.12.13 with python-chess 1.11.2 (fresh extraction, import including warm-up); budget 90 s

**DEPTH-6 FINGERPRINT:** 1,708,269 nodes over the 24-position suite from the extracted zip — identical to RC-B's 1,708,269 (the search tree is unchanged; this is the whole point of the candidate)

**SPEED:** +16.5% nodes per second over RC-B on this PC (88.1 / 89.1 knps against 75.8 / 76.2 knps, alternated twice on a quiet machine); +18.7% on the Mac

**TESTS:** 1,228 passed on the PC (`pytest -q`, 2 min 9 s, 21:40); 1,227 passed + 1 skipped on the Mac

**RELEASE CHECK:** 15 of 15 PASS, READY TO UPLOAD (23:02): contents, size, no native binaries, imports resolve, no requirements.txt, no dev-only or network imports, no absolute paths, no filesystem writes, 60 probes legal and inside every clock, smoke game from the extracted zip (white by checkmate); plus the fresh-extraction smoke under Python 3.12.13 (eight positions including in-check, one-legal-move, a round-20 game position and a 700 ms clock: all legal, longest think 4.6 s; `corpus/release/rc_c_smoke_py312.json`) and `tools.clockladder` PASS from 1 ms to 120 s with nothing over its hard deadline (worst think 4.6 s at 120 s)

**STRENGTH EVIDENCE (the reason to submit):** `champions/rcc_speed` against `champions/rc_b`, 100 paired games on the organiser's own start positions at the competition clock (120 s + 0.5 s, 300-ply cap), fresh run on the PC 21:42–22:56 with no other CPU work: **+39 =38 −23, 58.0%, +56 Elo**. Zero flags, crashes or illegal moves on either side. Record: `2026-09-05-rcc-speed-candidate.md`; raw `corpus/daily/rcc/speed_vs_rcb_120s_100_pc.jsonl` + `.pgn`; risk report `corpus/daily/rcc/swissrisk_speed_pc_100.txt`. The interrupted Mac run (59 games) was not used.

**FAMILY-LEVEL EVIDENCE (required alongside the game count):** 50 start families, **34 informative (68%)**; family-mean histogram 0.00×3, 0.25×9, 0.50×16, 0.75×13, 1.00×9; family bootstrap 95% Elo **−0.0..+115** (score 50.0%..66.0%); leave-one-informative-family-out Elo **+50..+64** (no single-family dependence); as White 60.0% (+70), as Black 56.0% (+42).

**THE STANDARD MET, STATED PLAINLY:** this is the identity-preserving standard (Gate 0 identity + a non-negative screen with no clock harm), the same standard the stalemate probe met inside RC-B — not the general "bootstrap excludes zero" standard, whose lower bound here is exactly zero. The justification is structural: the tree is byte-identical, so at equal depth RC-C makes RC-B's decisions; the only behavioural difference is more depth per second, and the screen confirms that this converts to points rather than to anything pathological. A 126-game extension to 226 (about 2.5 h on this machine) would tighten the interval and is optional.

**CLOCK SAFETY:** `cs_time.py` is byte-identical to RC-B's. In the match: no game under 5 s on either side; lowest clock 5.6 s (RC-B 5.9 s; the candidate's second-lowest, 6.1 s, lies between RC-B's two lowest); lowest-clock distribution p10 / p25 / median 10.0 / 15.2 / 21.3 s against RC-B's 10.9 / 13.9 / 20.4 s; largest single think 9.8 s against RC-B's 13.0 s; median final clock 22.0 s against 21.9 s. Equivalent, no drop.

**RULE COMPATIBILITY:** Python 3.12 (runs on 3.12.13); stdlib + python-chess only; no torch/numpy/numba needed; no native binary; no network, subprocess or file writes; no book, no tablebase, no engine data; readable source; one thread; 120 s + 0.5 s allocator unchanged from RC-A/RC-B; 139,381 bytes against the 50 MB limit

**WHY:** RC-C is RC-B searching the same tree 16–19% faster. RC-B's own promotion showed that speed converts to points in this engine (+17% knps → +59 Elo over RC-A), and the two live tactical failures analysed today (R18 15…g6, R20 12…Nxd5) were each repaired by exactly one more ply. Nothing else is stacked on this build: the check-extension lane was rejected and its code path ships default-off.

**KNOWN RISKS:**
* The screen is 100 games, not 226; the bootstrap lower bound touches zero. The structural argument (identical tree) carries the promotion; the optional extension would carry it statistically.
* `cs_search.py` contains the rejected check-extension code path behind `CS_CHECK_EXT`, default off; it was off in every test and game above and changes no node when off (fingerprint identical). It is dead weight, not a behaviour.
* RC-C has not itself played a rated game; RC-B's nine rated games today (rounds 21–29, 3W 3D 3L) are inherited evidence for everything except speed.
* The engine's known weaknesses (tactical horizon at the capture-only quiescence, conversion of won endings) are unchanged; this upload buys depth, it does not fix them.
* Eligibility for the final Swiss still needs written organiser clarification.

**UPLOAD:** not performed by the agent. **Upload this exact file: `corpus/release/claudeshark_rc_c.zip`, SHA-256 `1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`.** Verify the hash before uploading with `certutil -hashfile corpus\release\claudeshark_rc_c.zip SHA256` (Windows) or `shasum -a 256 corpus/release/claudeshark_rc_c.zip` (Mac). If the user uploads, record the time and confirm the SHA-256 in `V2_ACTIVE_STATE.md` section 1 and `spec.md` section 2; every rated game after that is RC-C.

**UPLOADED: user-confirmed 2026-09-05 23:14 UK.** RC-C is SUBMITTED and CHAMPION; `rc-c-integration` carries its engine from spec revision 6; RC-B is the frozen fallback. The optional 126-game extension was not run (user instruction; Daily Five imminent).
