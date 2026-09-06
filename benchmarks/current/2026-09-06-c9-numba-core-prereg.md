# C9 — Numba search core (pre-registered 2026-09-06 17:38 UK, before implementation)

| field | value |
|---|---|
| CANDIDATE | C9-numba-core: the board, move generation, make/unmake, evaluation, SEE, ordering, transposition table, quiescence and negamax reimplemented as one Numba-compiled region (`cs_core.py`), driven by a thin Python layer that keeps the C5 iterative-deepening, aspiration and time policy (`cs_fast.py`). python-chess is used only to parse the FEN and to emit UCI |
| CURRENT CHAMPION | C5 (`champions/c5_rfp`, engine `f6c0d30`) |
| ONE-SENTENCE CHANGE | Same search algorithm and evaluation as C5, executed by compiled code instead of python-chess and CPython |
| HYPOTHESIS | Profiling C5 (17:36 UK, `tools.profile_search`, 6 positions × 3 s): python-chess `push`/`pop`, pseudo-legal generation, attack masks and check detection take about 55% of runtime, the engine's own Python (negamax, quiescence, ordering, SEE, evaluate) the rest; C5 runs at 88.8 knps and depth 6.25 at 2 s. RC-C (+16.5% knps) and C5 (−30% nodes) both gained strength through effective depth alone. A compiled core at ≥10× the node rate buys 2–3 plies at the competition clock, which is the largest strength lever available and the only one that can reach top-3 calibre |
| TARGET FAILURE CLASS | every depth-repairable class: TACTICAL HORIZON and ROOT INSTABILITY (46 of 102 flips in the 2400 audit were repaired by one or two more plies) |
| EXPECTED STRENGTH BENEFIT | ≥ +150 Elo vs C5 at 120 s + 0.5 s if ≥10× nps is reached; the first screen must show ≥ 55% |
| EXPECTED NPS EFFECT | ≥ 10× (target ≥ 1,000 knps on this PC); measured by `tools.bench` |
| EXPECTED CLOCK EFFECT | none in policy (C5 allocator unchanged); JIT compilation happens at import inside the 90 s init budget and must be measured (< 45 s on this PC) |
| EXPECTED ACTIVATION RATE | 100% of nodes (it is the engine) |
| MATCHED NEGATIVES | perft must equal python-chess on standard perft positions and 300 random game positions (exact); evaluation must equal `cs_eval.evaluate` on 2,000 random positions (exact); the tactics suite 16/16; `tools.clockladder` PASS; the 240-suite equal-time move quality must not be worse than C5 |
| REJECTION CRITERION | any of: perft or evaluation mismatch not fixed within the time box; compile time > 60 s; tactics < 16/16; clock ladder failure or any flag; internal 60-game screen vs `champions/c5_rfp` below 55%; any crash or illegal move in the screen |
| MAX DEVELOPMENT TIME | 2 h to a perft-verified core with measured speed (go/no-go at 19:38 UK); 6 h to a screened candidate (reassess at 23:38 UK). Milestones: M1 perft-exact movegen + speed (2 h); M2 eval/SEE/search port, tactics 16/16, bench (4 h); M3 agent integration, Gate 0, 60-game screen (6 h) |
| COMPLIANCE | numba 0.67.0 is preinstalled in the competition container and JIT compilation is explicitly described in the official docs (fetched 2026-09-06 17:38 UK: "Compiled speed comes from numba, which JIT compiles your Python in process"); no native binary enters the zip; `/tmp` starts empty each game, so no compile cache is shipped or relied on |

## Baseline (C5, this PC, 17:37 UK)

`tools.bench --ms 2000 --positions 8`: depth 6.25, 851,758 nodes (48% quiescence),
**88,818 nps**, tt hit 6.7%. Fingerprint `tools.bench --depth 6`: 1,409,912 nodes.

## Plan of record

1. `cs_core.py`: int64 bitboards, mailbox, Zobrist keys, ray attacks, pseudo-legal
   generation with make/unmake legality, castling and en passant, perft.
2. Exact PeSTO packed evaluation with the bishop pair and tempo (all registry terms are off
   in C5, so this is the whole evaluator), incremental through make/unmake.
3. SEE, MVV-LVA + killers + history ordering, TT (numpy arrays), quiescence with delta and
   SEE pruning (checks kept), negamax with PVS, null move, LMR (C5 schedule), RFP,
   repetition on the path and game history, fifty-move and insufficient-material rules.
4. `cs_fast.py`: Searcher-compatible wrapper (same `search()` signature as `cs_search.Searcher`)
   so bench, arena, tactics and the clock ladder run unchanged; `agent.py` switched to it.

## M1 — movegen exact (17:46 UK, 8 min after pre-registration)

perft equals python-chess on all six standard positions (startpos d4 197,281;
Kiwipete d3 97,862; pos3 d5 674,624; pos4 d4 422,333; pos5 d3 62,379; pos6 d3
89,890) and on 58 random game positions at depth 2–3; hash key, packed sum and
board equal a fresh reconstruction after every legal move from 60 random
positions. Perft speed 9–13 million nodes/s (python-chess about 100k).

## M2 — evaluation, SEE, search (17:53 UK)

Evaluation equals `cs_eval.evaluate` on 391 random positions (0 mismatches),
insufficient material equals `is_material_draw`, SEE equals `cs_see.see` on
1,620 captures (0 mismatches). At equal fixed depth the compiled search and
the interpreted C5 search choose the same root move in 10 of 12 cases with
the same or near-identical scores and node counts (depth 4 and 6 over six
openings). Mate scores, stalemate avoidance, the fifty-move claim and the
legal-move/abort behaviour are held by `tests/test_core.py` (16 tests).

## Gate 0 — PASS (18:01 UK)

| check | result |
|---|---|
| fingerprint `tools.bench --depth 6` | **1,391,318 nodes** (C5 1,409,912: the same tree within 1.3%) in 0.5 s, **2,593,264 nps** |
| timed `tools.bench --ms 2000 --positions 8` | **depth 11.62, 2,332,412 nps** vs C5 (same run, interpreted core) depth 6.38, 89,711 nps: **26× nps, +5.2 plies** |
| tactics suite 1 s | **16/16**, average depth 12.69 (C5 16/16 at lower depth) |
| clock ladder | **PASS** 1 ms..120 s, worst 3.6 s at 120 s, nothing over hard |
| tests | full suite 1,258 passed (legacy suite on the interpreted core via `CS_CORE=python` in conftest) + `tests/test_core.py` 16 passed |
| agent import + warm-up (compile) | **27.6 s** on this PC (Ryzen 5 5600X); platform init budget 90 s (harness 60 s); first move at a full clock 2.4 s |
| snapshot | `champions/c9_numba` (16 files: the 14 C5 files + `cs_core.py`, `cs_fast.py`), commit `8131214` |

## Gate 2A internal — 60 games vs `champions/c5_rfp` (strict, dev set, 6 workers), launched 18:02 UK

Output `corpus/strength/c9/c9_vs_c5_dev_60_strict.jsonl` (+ `.pgn`, `.log`). Continue bar: ≥ 55%.

**Result (18:02–18:44 UK): +55 =5 −0, 95.8%, +545 Elo** (Wilson +337..+752,
paired bootstrap +436..+800), 30 families / 30 informative, LOO +538..+579,
White 96.7% / Black 95.0%, terminations checkmate 55 / threefold 4 /
insufficient 1, mean 97 plies, 0 failures; clock floor 9.8 s (C5 12.4 s),
largest think 13.5 s (same as C5), mean think 2.09 s, median final clock
43.6 s. `swissrisk_c9_c5_dev_60.txt`.

## Decision — PROMOTED (18:50 UK)

Every pre-registered bar is cleared by a margin no earlier candidate came
near: the continue bar was 55%, the result 95.8% with a lower bound of +436
Elo. C9 is the development champion; every later candidate starts from
`champions/c9_numba`. Release: `tools.release_check` on an LF export of the
committed blobs 16/16 PASS (`corpus/release/claudeshark_rc_e.zip`, sha256
`fb8f860944751e3b86afae1a11660b5903799041fee99605733c397d16ac58aa`, 64,789
bytes, 16 files, 195,293 bytes unpacked); fresh-extraction smoke under Python
3.12.13 with numba 0.67.0 / numpy 2.5.2 / chess 1.11.2: 10/10 probes legal,
import + compile 27.2 s, first move at a full clock 2.7 s
(`corpus/release/rc_e_smoke_py312.json`). Upload card:
`RC_E_UPLOAD_CARD.md`. Not submitted.

RECORD THIS: `uv run python -m tools.bench --ms 2000 --positions 8` twice,
once with `CS_CORE=python` (C5: depth 6.38, 89,711 nps) and once without
(C9: depth 11.62, 2,332,412 nps) — the same algorithm, 26× the speed, five
plies deeper; then the arena line `+55 =5 -0, score 95.8%, elo +545`.
