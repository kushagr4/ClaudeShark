# RC-F upload card — C9 Numba core + quiescence stalemate fix

Prepared 2026-09-06 20:10 UK. **Not uploaded by the agent. The user decides.**

**BUILD:** RC-F = C9 (the C5 search algorithm executed by a Numba-compiled
core, `cs_core.py` + `cs_fast.py`) plus one correctness fix: the compiled
quiescence now scores a stalemate 0 when every pseudo-legal capture is illegal
(it returned the stand-pat material score). Everything else is byte-identical
to RC-E.

**REPLACES:** SUBMITTED RC-C (`corpus/release/claudeshark_rc_c.zip`, sha256
`1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`,
user-confirmed upload 2026-09-05 23:14 UK). RC-E (`claudeshark_rc_e.zip`,
sha256 `fb8f8609…58aa`) was never submitted and is superseded by RC-F; do not
upload RC-E.

**EXACT COMMIT:** `b7f42cf` on `kushagra/rc-f-correctness` (engine files;
records commit follows). Parent C9 engine commit `8131214`.

**FROZEN SNAPSHOT:** `champions/rc_f` (16 files, blob-identical to the archive
contents after LF normalisation).

**ZIP PATH:** `corpus/release/claudeshark_rc_f.zip`

**SHA-256:** `4ee4033e509bf8709d7d1090037d0aeb6b146da375c88f9986cb1a67789df13d`

**COMPRESSED BYTES:** 64,984. **UNCOMPRESSED BYTES:** 195,818 in 16 files
(`agent.py`, `cs_constants.py`, `cs_core.py`, `cs_drawish.py`, `cs_eval.py`,
`cs_fast.py`, `cs_king.py`, `cs_kingpawn.py`, `cs_mopup.py`, `cs_ordering.py`,
`cs_passed.py`, `cs_search.py`, `cs_see.py`, `cs_terms.py`, `cs_time.py`,
`cs_tt.py`; all text, all at the zip root).

**COMPLIANCE:** pure Python; the speed comes from numba 0.67.0 JIT, which the
official docs (fetched 2026-09-06 17:38 UK) name as the supported route; no
native binaries, no third-party engine code, no network, no filesystem writes,
no requirements file. Init: import + kernel compile 27.05 s under the
competition stack (Python 3.12.13, numba 0.67.0, numpy 2.5.2, chess 1.11.2),
inside the 90 s init budget; ordinary moves do not recompile.

**STRENGTH (C9 vs the previous champion C5, unchanged by the fix):** +55 =5 −0
over 60 games at 120 s + 0.5 s strict, 95.8%, +545 Elo, paired bootstrap
+436..+800, 0 failures. Against Stockfish 18 UCI_Elo 2800 the stopped C9 run
scored +18 =18 −11 (57.4%, PARTIAL / TIMING-CONTAMINATED); the clean RC-F
result is in `2026-09-06-rc-f-boundary.md` §7a.

**SPEED / DEPTH:** 2.55 Mnps at 2 s (C5 88.8 knps, ×28); average depth at 2 s
about 11.8 plies (C5 6.25); tactics 16/16 at 1 s.

**CLOCK SAFETY:** ladder PASS (10 s clock: 7.3% used, floor 733 ms; 120 s:
3.0%); release-check probes all inside their clocks; arena floor ≥ 3.5 s.

**RELEASE CHECK:** 16 of 16 PASS, READY TO UPLOAD (20:05 UK), 1,372 tests.
Fresh-extraction smoke under Python 3.12: 10/10 probes legal
(`corpus/release/rc_f_smoke_py312.json`).

**RISKS:** the compiled core is a new implementation (about 1,700 lines) of
the C5 algorithm; it has passed perft, 33 targeted rule positions, the
legacy behavioural suite, fixed-depth agreement with C5 and 60 + 47 timed
games without a failure, but it has fewer rated games behind it than RC-C.

**FALLBACK:** RC-C stays the submitted build until the user uploads; if RC-F
misbehaves in its first rated games, re-upload
`corpus/release/claudeshark_rc_c.zip`.

**UPLOAD:** not performed by the agent. **If you upload, upload this exact
file: `corpus/release/claudeshark_rc_f.zip`, SHA-256
`4ee4033e509bf8709d7d1090037d0aeb6b146da375c88f9986cb1a67789df13d`.** Verify
with `certutil -hashfile corpus\release\claudeshark_rc_f.zip SHA256`. On
confirmation, record the time and hash in `V2_ACTIVE_STATE.md` §1 and
`spec.md` §2; every rated game after that is RC-F.
