# C9 — Numba search core (pre-registered 2026-09-06 17:50 UK, before implementation)

| field | value |
|---|---|
| CANDIDATE | C9-numba-core: the board, move generation, make/unmake, evaluation, SEE, ordering, transposition table, quiescence and negamax reimplemented as one Numba-compiled region (`cs_core.py`), driven by a thin Python layer that keeps the C5 iterative-deepening, aspiration and time policy (`cs_fast.py`). python-chess is used only to parse the FEN and to emit UCI |
| CURRENT CHAMPION | C5 (`champions/c5_rfp`, engine `f6c0d30`) |
| ONE-SENTENCE CHANGE | Same search algorithm and evaluation as C5, executed by compiled code instead of python-chess and CPython |
| HYPOTHESIS | Profiling C5 (17:40 UK, `tools.profile_search`, 6 positions × 3 s): python-chess `push`/`pop`, pseudo-legal generation, attack masks and check detection take about 55% of runtime, the engine's own Python (negamax, quiescence, ordering, SEE, evaluate) the rest; C5 runs at 88.8 knps and depth 6.25 at 2 s. RC-C (+16.5% knps) and C5 (−30% nodes) both gained strength through effective depth alone. A compiled core at ≥10× the node rate buys 2–3 plies at the competition clock, which is the largest strength lever available and the only one that can reach top-3 calibre |
| TARGET FAILURE CLASS | every depth-repairable class: TACTICAL HORIZON and ROOT INSTABILITY (46 of 102 flips in the 2400 audit were repaired by one or two more plies) |
| EXPECTED STRENGTH BENEFIT | ≥ +150 Elo vs C5 at 120 s + 0.5 s if ≥10× nps is reached; the first screen must show ≥ 55% |
| EXPECTED NPS EFFECT | ≥ 10× (target ≥ 1,000 knps on this PC); measured by `tools.bench` |
| EXPECTED CLOCK EFFECT | none in policy (C5 allocator unchanged); JIT compilation happens at import inside the 90 s init budget and must be measured (< 45 s on this PC) |
| EXPECTED ACTIVATION RATE | 100% of nodes (it is the engine) |
| MATCHED NEGATIVES | perft must equal python-chess on standard perft positions and 300 random game positions (exact); evaluation must equal `cs_eval.evaluate` on 2,000 random positions (exact); the tactics suite 16/16; `tools.clockladder` PASS; the 240-suite equal-time move quality must not be worse than C5 |
| REJECTION CRITERION | any of: perft or evaluation mismatch not fixed within the time box; compile time > 60 s; tactics < 16/16; clock ladder failure or any flag; internal 60-game screen vs `champions/c5_rfp` below 55%; any crash or illegal move in the screen |
| MAX DEVELOPMENT TIME | 2 h to a perft-verified core with measured speed (go/no-go at 19:50 UK); 6 h to a screened candidate (reassess at 23:50 UK). Milestones: M1 perft-exact movegen + speed (2 h); M2 eval/SEE/search port, tactics 16/16, bench (4 h); M3 agent integration, Gate 0, 60-game screen (6 h) |
| COMPLIANCE | numba 0.67.0 is preinstalled in the competition container and JIT compilation is explicitly described in the official docs (fetched 2026-09-06 17:38 UK: "Compiled speed comes from numba, which JIT compiles your Python in process"); no native binary enters the zip; `/tmp` starts empty each game, so no compile cache is shipped or relied on |

## Baseline (C5, this PC, 17:45 UK)

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
