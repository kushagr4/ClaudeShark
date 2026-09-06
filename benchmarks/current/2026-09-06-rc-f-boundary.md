# RC-E / C9 release boundary → RC-F (C9 + quiescence stalemate fix)

Date: 2026-09-06, 19:39–21:10 UK (Windows PC, 12 logical cores).
Branch: `kushagra/rc-f-correctness` (from `99afd81`, the C9 promotion commit).
Trigger: user brief 19:39 UK — stop C10, sweep, freeze RC-E, fast catastrophic
correctness boundary, clean 2800 calibration, release validation, then stop for
the user's upload decision.

## 1. Process sweep (19:39 UK)

| job | PID | purpose | start | output | status |
|---|---|---|---|---|---|
| C9 vs Stockfish 2800 arena (task `bvkywtdnw`) | uv → arena + 6 runners + 6 Stockfish | external calibration | 18:52:37 | `corpus/strength/c9/c9_vs_sf2800_dev2400_60_strict.*` | **stopped by the user at 47/60** (last game written 19:34:29); no process remained at 19:39 |
| C10 fixed-depth comparisons | (finished) | C10 Gate 1 evidence | 18:59–19:05 | scratch `c10_depth12.log`, `benchmarks/current/2026-09-06-c10-log-lmr-prereg.md` | COMPLETE — preserved on branch `kushagra/c10-log-lmr` (`a15ef48`) |
| C10 Gate 0/1 script (`c10_gates.sh`) | — | equal-time gates | never launched | — | NOT STARTED (paused) |

Process listing at 19:39 (`Get-Process`): no python, no Stockfish, no uv.
Active jobs after the sweep: 0. Stale jobs found: 0. Stale jobs terminated: 0.
C10 state: PAUSED, branch and evidence intact, may resume after the RC-F
upload decision, starting from the frozen RC-F champion.

## 2. The stopped 2800 run — PARTIAL / TIMING-CONTAMINATED

Contamination window. The C10 branch was created at 18:59:02 and its
fixed-depth comparisons ran single-threaded until 19:05:07 (depth 8/10 runs
≈ 18:59–19:01, two depth-12 runs of 69 s and 64 s ending 19:05:07). The
arena ran 12 processes (6 C9 + 6 Stockfish) on 12 logical cores, so one extra
compute-bound process contended for roughly six minutes of a 42-minute run.
The C10 commit at 19:20:44 and the gate script written at 19:21 used no CPU.

Separation. The arena records per-game `seconds` but no per-game start or
finish timestamps, and the log lines carry no clock; with six concurrent
workers the completion order does not identify which games overlapped
18:59–19:05. Clean separation is therefore **not reliable**, and the run is
labelled as a whole:

**PARTIAL / TIMING-CONTAMINATED — 47 of 60 games, +18 =18 −11, 57.4%,
nominal +52 Elo, bootstrap 46.8%..69.1%, White +8 =9 −7, Black +10 =9 −4,
0 failures, clock floor 3,525 ms, largest think 13,739 ms.** Kept as
evidence of playing strength (the result is not sensitive to a few per cent
of CPU for six minutes) but **not used for any clock, depth or timing
conclusion**. The two stalemates in it (games 24 and 45) were drawn
king-and-pawn endings, not the defect in §4. The calibration is re-run
cleanly on the fixed build (§7).

## 3. RC-E freeze verified (19:45 UK)

| item | value |
|---|---|
| Git commit (engine) | `8131214` (`kushagra/c9-numba-core`; promotion records at `99afd81`) |
| frozen snapshot | `champions/c9_numba` — all 16 engine files byte-identical (LF-normalised) to `8131214` |
| archive | `corpus/release/claudeshark_rc_e.zip`, 16 entries, 195,293 bytes unpacked, contents byte-identical to the snapshot |
| SHA-256 | `fb8f860944751e3b86afae1a11660b5903799041fee99605733c397d16ac58aa` |
| Python / stack (competition) | Python 3.12, numba 0.67.0, numpy 2.5.2, python-chess 1.11.2 (smoke 10/10 under that stack, import+compile 27.15 s, `corpus/release/rc_e_smoke_py312.json`) |
| local venv | Python 3.13.5, numba 0.67.0, numpy 2.5.2, python-chess 1.11.2 |
| native binaries | none (16 `.py` files) |

RC-E is not modified. It is superseded for upload by RC-F (§6) because of the
defect in §4; RC-E remains the frozen C9 reference and the C9 arena result
(+55 =5 −0 vs C5) stands.

## 4. Classification and the defect found

C9 is **a new high-performance implementation of the C5 architecture**, not
an identity-preserving port: fixed-depth node counts differ (fingerprint
1,391,318 vs 1,409,912, −1.3%), root moves agree but not always.

Catastrophic-correctness review (19:40–19:55) found one real divergence, via
`tools/review_c9_repro.py` (a reviewer's reproduction script present in the
tree, untracked, 18:50 UK):

    stalemate FEN 6Bk/5K2/8/8/8/8/8/R7 b - - 0 1
    quiescence  C9 −849   C5 0

Cause: the compiled quiescence generates *pseudo-legal* captures and rejects
illegal ones inside the move loop; when every capture is illegal (here Kxg8
into the protected bishop) the loop plays nothing and the function returned
the stand-pat score, so a stalemated side was scored as simply behind on
material. C5 filters captures through python-chess before the loop and
reaches its stalemate check. Negamax was not affected (it counts legal
moves). RFP at depth 1 returns the static score in both cores (inherited,
identical, not a divergence).

Fix (`cs_core.py`, 10 lines, commit `b7f42cf`): count the captures that
proved legal; a non-check node that found none asks `has_legal_move` and
returns 0 when there is no legal move. Cost: none measurable (§5).

## 5. Fast catastrophic-correctness boundary — PASS

| item | evidence |
|---|---|
| move generation, make/unmake, pins, double check, evasions, castling, en passant (incl. rank-pinned EP and EP discovered check), promotions, underpromotions, corner-square sliders (int64 sign bit) | perft exact vs python-chess: 6 standard + 40 random positions (`tests/test_core.py`), 33 targeted positions with the full root legal-move *set* compared (`tests/test_core_rules.py`) |
| stalemate | 3 stalemates with only illegal captures score 0 in quiescence and negamax; a root whose only "progress" stalemates scores 0 (fails on the unpatched core: 3 of 5 new tests) |
| checkmate, mate-distance | mate in 1 (MATE−1), mate in 2 (MATE−3), same distance when re-read through the table |
| repetition | path repetition at stride two scores 0; path scan bounded by the halfmove clock; root keys enter the game record (mirrors `tests/test_repetition.py`) |
| fifty-move | `rules_outcome` equal to the C5 function on 300+ random positions at clocks 98/99/100; claim at 100 beats material |
| insufficient material | equal to the C5 function on 12 targeted endings + 300 random positions |
| TT bounds and mate normalisation | store/probe round trip of depth, score (incl. mate), bound, move on 500 random entries; `score_to_tt`/`score_from_tt` round trip for 60 plies; stored mate read deeper is closer |
| null move / LMR re-search / RFP | fixed-depth agreement with C5 (§6); legacy suite on the compiled core |
| quiescence | 200 random positions vs C5 `_quiescence`: ≥ 90% identical, never a draw on one side and a material verdict on the other |
| timeout propagation | 150 ms budget returns in < 0.6 s; ladder PASS (§5b); 60 clock probes in the release check |
| illegal-move path | random play from varied positions (6 games × 30 moves) and 80-ply random play, every move legal |
| legacy suite on the compiled core (`CS_CORE=numba`) | 1,299 passed; 72 failed, all of them tests that reach interpreted-core internals (`_quiescence`, `_negamax`, `_path`, `_game_counts`, table `store`/`probe`), a monkeypatch of the interpreted evaluator, or the deliberately-broken table policy that the compiled core does not implement — none a behavioural failure |
| full suite (default interpreted core + compiled-core tests) | 1,270 passed at `b7f42cf`; 1,372 in the release check |

Gate 0 on the fix (19:55–19:59, quiet machine, `corpus/strength/rcf/`):

| build | nodes/s at 2 s × 24 | tactics 1 s | ladder |
|---|---|---|---|
| frozen C9 (`champions/c9_numba`) | 2,496,684 | — | — |
| tree with fix (= RC-F) | 2,553,201 | 16/16, avg depth 12.69 | PASS (10 s: 7.3% used, floor 733 ms; 120 s: 3.0%) |

## 6. Root / search semantic check — PASS

`corpus/strength/rcf/cmp_c5_vs_c9_fixed_depth.md` (competition-like suite,
random sample, C5 interpreted vs RC-F compiled, fixed depth):

| depth | positions | root agreement | identical scores | max score diff | nodes C9/C5 |
|---|---|---|---|---|---|
| 5 | 40 | 38/40 | 38/40 | 3 cp | 0.963 |
| 6 | 16 | 15/16 | 11/16 | 27 cp | 0.979 |

Every root disagreement is a same-score alternative (d8c7 vs d8e7 at −5/−5;
h4g3 vs g5g4 at 113/116; g4g6 vs g4h5 at −49/−55). No divergence with a
different move and a score gap above 100 cp. Node counts differ per position
by up to ±40% (tie-break order among equal-score captures, table replacement)
but sum to within 4%. Nothing suspicious.

## 7. Clean 2800 calibration (RC-F, launched 20:06 UK)

`champions/rc_f` vs Stockfish 18 UCI_Elo 2800 (Hash 16, one thread), 60
games, dev2400 set, 120 s + 0.5 s, strict claims, 6 workers, **no competing
CPU work** (`corpus/strength/rcf/rcf_vs_sf2800_dev2400_60_strict.*`).

RESULT: see §7a (filled when the run ends).

## 8. Release validation — RC-F

| check | result |
|---|---|
| frozen snapshot | `champions/rc_f` (16 files) = tree at `b7f42cf`; differs from `champions/c9_numba` by the 10-line fix only |
| archive | `corpus/release/claudeshark_rc_f.zip` — 64,984 bytes, 16 files, 195,818 unpacked, all `.py` at the root |
| SHA-256 | `4ee4033e509bf8709d7d1090037d0aeb6b146da375c88f9986cb1a67789df13d` |
| release gate | 16/16 PASS, READY TO UPLOAD (20:05 UK): contents, size, no native binaries, imports resolve, no requirements.txt, no dev-only/network imports, no absolute paths, no filesystem writes, 60 probes legal and inside every clock, smoke game, 1,372 tests |
| fresh extraction, competition stack | Python 3.12.13 / numba 0.67.0 / numpy 2.5.2 / chess 1.11.2: 10/10 probes legal (`corpus/release/rc_f_smoke_py312.json`) |
| init / JIT | import + warm-up 27.05 s (budget 90 s); ordinary moves after that do not compile (in-check, one-move, mate-in-one probes answer in 0.00 s; 700 ms clock answered in 0.09 s) |
| clock ladder | PASS |
| rules compliance | pure Python + numba JIT (docs 2026-09-06 17:38: "Compiled speed comes from numba"); no third-party engine code; no native binaries; nothing written to disk |
| working tree | clean after the records commit (§9) |
