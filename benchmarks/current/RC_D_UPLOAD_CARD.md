# RC-D upload card — 2026-09-06 08:45 UK (Windows PC)

**RECOMMENDATION:** **SUBMIT, with the evidence weighed below** — RC-D is RC-C plus one search change that measured non-negative against RC-C over 140 internal games and cleared the ~2300 benchmark stage on a fresh holdout with a lower bound above 50%; nothing measured negative. The evidence is weaker than RC-C carried (its +56 Elo came with an identical tree); if you prefer a stronger internal margin before replacing a live build, the honest alternative is to keep RC-C and let RC-D accumulate the ~2400-stage games first.

**BUILD NAME:** RC-D / RC-C + reverse futility pruning (candidate C5)

**REPLACES:** SUBMITTED RC-C (`corpus/release/claudeshark_rc_c.zip`, 50,258 bytes, SHA-256 `1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`, user-confirmed upload 2026-09-05 23:14 UK)

**EXACT COMMIT:** engine files at `f6c0d30` on `kushagra/c5-rfp` (snapshot `champions/c5_rfp`; the archive was built from an LF export of those git blobs and every extracted file hashes to its blob). Differs from RC-C in exactly one file, `cs_search.py`: reverse futility pruning (`CS_RFP`, default on; `CS_RFP=0` reproduces RC-C's tree exactly, depth-6 fingerprint 1,708,269).

**ZIP PATH:** `corpus/release/claudeshark_rc_d.zip`

**ZIP BYTES:** 50,597

**UNCOMPRESSED BYTES:** 140,569 in 14 files (`agent.py`, `cs_constants.py`, `cs_drawish.py`, `cs_eval.py`, `cs_king.py`, `cs_kingpawn.py`, `cs_mopup.py`, `cs_ordering.py`, `cs_passed.py`, `cs_search.py`, `cs_see.py`, `cs_terms.py`, `cs_time.py`, `cs_tt.py`; all text, all at the zip root; the same set as RC-C; every registry term off, as in RC-C)

**FULL SHA-256:** `3dab7d89fee56a84ddb18540f52fb388f65ebb73f258de585f3a73f3329951e7`

**STARTUP:** 1.37 s on CPython 3.12.13 with python-chess 1.11.2 (fresh extraction, import including warm-up); budget 90 s

**DEPTH-6 FINGERPRINT:** 1,409,912 nodes over the 24-position suite from the extracted zip (RC-C 1,708,269: −17.5% nodes at depth 6 with 0 of 24 root moves changed; −29.9% at depth 8 with 2 of 24 changed)

**SPEED:** nodes per second unchanged (85.8 knps from the zip on this PC; the gain is fewer nodes per depth, +0.46 ply at a 60 s clock on 177 replayed positions)

**TESTS:** 1,228 passed on the C5 branch (`pytest -q`, 2 min 40 s, 03:20); tactics suite 16/16

**RELEASE CHECK:** 15 of 15 PASS, READY TO UPLOAD (08:33): contents, size, no native binaries, imports resolve, no requirements.txt, no dev-only or network imports, no absolute paths, no filesystem writes, 60 probes legal and inside every clock, smoke game from the extracted zip; fresh-extraction smoke under Python 3.12.13 (eight positions including in-check, one-legal-move, a round-20 game position and a 700 ms clock: all legal, longest think 4.8 s; `corpus/release/rc_d_smoke_py312.json`); `tools.clockladder` PASS from 1 ms to 120 s with nothing over its hard deadline (worst 4.1 s at 120 s)

**STRENGTH EVIDENCE:**
* **Internal vs RC-C** (`champions/rc_c`), competition clock, strict draw claim, organiser starts: 140 paired games on two independent start sets — **+44 =59 −37, 52.5%, +17 Elo**, 70 families / 49 informative, family bootstrap 45.7%..59.3% (Elo −30..+65), leave-one-family-out +13..+23, White 55.7% / Black 49.3%. Dev set 60: 49.2%; val set 80: 55.0%. Zero failures, clock floors 7.2 s / 6.3 s. Records `corpus/strength/c5/c5_vs_rcc_*`.
* **External, ~2300 BENCHMARK-A** (Stockfish 18 `UCI_Elo 2300`, strict; `STRENGTH_BENCHMARK_2300.md` — a proxy, not Chess.com): dev-set screen 60 games **58.3%** (RC-C: 56.0% over 100 on the same set); **qualification on the untouched `holdout_b`, 100 games: +53 =16 −31, 61.0%, +78 Elo, bootstrap 53.0%..69.0%**, 30 informative families, LOO +72..+87, White 61.0% / Black 61.0%, 0 failures, clock floor 5.1 s (RC-C on `holdout_a`: 55.5%, bootstrap 47%..64%).
* **Equal-time move quality**, 240 ordinary positions at 3,000 ms, oracle 1M nodes: robust mean loss 34 → 31, p90 95 → 82, p95 175 → 130, expected-score loss 0.061 → 0.051, paired +3.4 cp (11 better / 5 worse by >= 50 cp); >= 300 cp count 4 → 4.
* **Error rate** (like-for-like, strict games vs benchmark A): >= 100 cp 8.30% (RC-C 8.36%); >= 300 cp 2.14% (RC-C 1.69%; 50 vs 79 events, within noise). RFP buys depth, it does not by itself cut the large-error tail.

**THE STANDARD MET, STATED PLAINLY:** promotion to development champion rested on "non-negative against the champion and better externally" (`2026-09-06-c5-rfp-prereg.md`, including one recorded deviation from its own Gate 1 bar). The internal bootstrap includes 50%; the external qualification's does not. This is a smaller, less certain step than RC-B→RC-C. It is not a regression by any measurement taken.

**CLOCK SAFETY:** `cs_time.py` byte-identical to RC-C's; no game under 5 s in 300 timed games; largest think 13.2 s; ladder PASS.

**RULE COMPATIBILITY:** Python 3.12 (runs on 3.12.13); stdlib + python-chess only; no torch/numpy/numba; no native binary; no network, subprocess or file writes; no book, no tablebase, no engine data; readable source; one thread; 140,569 bytes against the 50 MB limit.

**KNOWN RISKS:**
* Reverse futility pruning trusts the static evaluation at low depth, and the audit shows that evaluation is optimistic by a median +269 cp in the largest-error positions; the >= 300 cp rate ticked up (2.14% vs 1.69%) within noise. A candidate that corrects that optimism (C6, in test) would pair naturally with it.
* Internal margin is +17 ± 47 Elo: RC-D may be no stronger than RC-C against engines like itself; it has not lost to it.
* RC-D has not played a rated game.
* Eligibility for the final Swiss still needs written organiser clarification.

**UPLOAD:** not performed by the agent. **If you upload, upload this exact file: `corpus/release/claudeshark_rc_d.zip`, SHA-256 `3dab7d89fee56a84ddb18540f52fb388f65ebb73f258de585f3a73f3329951e7`.** Verify with `certutil -hashfile corpus\release\claudeshark_rc_d.zip SHA256`. On confirmation, record the time and hash in `V2_ACTIVE_STATE.md` §1 and `spec.md` §2; every rated game after that is RC-D.
