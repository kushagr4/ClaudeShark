# RC-E UPLOAD CARD — prepared 2026-09-06 18:58 UK (Windows PC)

**STATUS:** READY FOR THE USER'S UPLOAD DECISION. **Not uploaded by the agent.**

**BUILD:** RC-E = C9 = the C5 search (RC-C + reverse futility pruning) executed by a Numba-compiled core: bitboard move generation, make/unmake, PeSTO evaluation, SEE, ordering, transposition table, quiescence and negamax in `cs_core.py`, driven by `cs_fast.py`; python-chess parses the FEN and emits UCI. Same evaluation, same search algorithm, 26× the node rate.

**REPLACES:** SUBMITTED RC-C (`corpus/release/claudeshark_rc_c.zip`, sha256 `1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`, user-confirmed upload 2026-09-05 23:14 UK). RC-D (C5) was never submitted and is superseded.

**EXACT COMMIT:** engine files at `8131214` on `kushagra/c9-numba-core` (snapshot `champions/c9_numba`); the archive was built from an LF export of those git blobs and every extracted file hashes to its blob.

**ZIP PATH:** `corpus/release/claudeshark_rc_e.zip`

**SHA-256:** `fb8f860944751e3b86afae1a11660b5903799041fee99605733c397d16ac58aa`

**COMPRESSED BYTES:** 64,789. **UNCOMPRESSED BYTES:** 195,293 in 16 files (`agent.py`, `cs_constants.py`, `cs_core.py`, `cs_drawish.py`, `cs_eval.py`, `cs_fast.py`, `cs_king.py`, `cs_kingpawn.py`, `cs_mopup.py`, `cs_ordering.py`, `cs_passed.py`, `cs_search.py`, `cs_see.py`, `cs_terms.py`, `cs_time.py`, `cs_tt.py`; all text, all at the zip root; every registry term off, as in RC-C).

**COMPLIANCE:** imports only the standard library plus python-chess, numpy and numba (all preinstalled at the platform's pinned versions); no native binary, no compile cache, no requirements.txt, no filesystem write, no network. The official docs (read 2026-09-06 17:38 UK) state "Compiled speed comes from numba, which JIT compiles your Python in process" and a 90 s init budget "covers importing your agent and runs before the clock starts". Compilation happens at import (27 s on this PC; the platform's EPYC 9V74 core at 2.6 GHz may take longer — still well inside 90 s). The local harness's stricter 60 s init budget was met in all 60 arena games.

**STRENGTH:** vs C5 (the previous development champion, itself +17 Elo over RC-C): **+55 =5 −0, 95.8%, +545 Elo** over 60 games at 120 s + 0.5 s, strict draw claims, organiser start positions, 30/30 informative families, paired bootstrap +436..+800, White 96.7% / Black 95.0%, 0 failures. External calibration vs Stockfish UCI_Elo 2800 running at card time (`corpus/strength/c9/c9_vs_sf2800_dev2400_60_strict.*`).

**SPEED / DEPTH:** `tools.bench --ms 2000 --positions 8`: depth 11.62 at 2,332,412 nps (C5 6.38 at 89,711 nps). Fingerprint `--depth 6`: 1,391,318 nodes (C5 1,409,912 — the same tree within 1.3%). Tactics suite 16/16 at 1 s (average depth 12.7).

**CLOCK SAFETY:** `tools.clockladder` PASS from 1 ms to 120 s, nothing over its hard deadline (worst 3.6 s at 120 s). Arena: lowest clock ever held 9.8 s, largest single think 13.5 s, mean think 2.09 s, median final clock 43.6 s; no flag, no crash, no illegal move.

**RELEASE CHECK:** 16 of 16 PASS, READY TO UPLOAD (18:49 UK): contents, size, no native binaries, imports resolve, no requirements.txt, no dev-only or network imports, no absolute paths, no filesystem writes, 60 probes legal and inside every clock, smoke game from the extracted zip, full test suite (1,260 passed). Fresh-extraction smoke under Python 3.12.13 / numba 0.67.0 / numpy 2.5.2 / chess 1.11.2 (the platform's stack): 10/10 probes legal (start position, in check, checkmated → `0000`, one legal move, mate in one, promotion, en passant, a 700 ms clock, fifty-move counter at 99, a round-20 middlegame); import + compile 27.15 s; longest think 2.8 s (`corpus/release/rc_e_smoke_py312.json`).

**KNOWN RISKS:** (1) the first import compiles for ~27–45 s depending on the core; if the platform's init budget were shorter than documented the agent would fail its smoke games — the docs say 90 s. (2) Memory: the transposition table is two 4M-entry int64 arrays (64 MB) plus Numba's LLVM runtime; well inside 2 GB. (3) No rated game has yet been played by this build; every rated result after an upload is C9 evidence and belongs in the live loss corpus.

**FALLBACK:** RC-C stays the submitted build until the user uploads; if RC-E misbehaves in its smoke games, re-upload `corpus/release/claudeshark_rc_c.zip`.

**UPLOAD:** not performed by the agent. **If you upload, upload this exact file: `corpus/release/claudeshark_rc_e.zip`, SHA-256 `fb8f860944751e3b86afae1a11660b5903799041fee99605733c397d16ac58aa`.** Verify with `certutil -hashfile corpus\release\claudeshark_rc_e.zip SHA256`. On confirmation, record the time and hash in `V2_ACTIVE_STATE.md` §1 and `spec.md` §2; every rated game after that is RC-E.
