# RC-F evening self-review — 2026-09-06, 21:10–midnight UK

Submitted build: **RC-F** (`corpus/release/claudeshark_rc_f.zip`, sha256
`4ee4033e509bf8709d7d1090037d0aeb6b146da375c88f9986cb1a67789df13d`, engine
`b7f42cf`, snapshot `champions/rc_f`, user-confirmed activation 21:07 UK).

This is a SELF-AUDIT by the developer who wrote the compiled core. It is not
independent verification; a friend and Astra review RC-F independently
tomorrow. Evidence files: `corpus/strength/rcf/review/`.

## Task 1 — the RFP stalemate path

**Code path.** `cs_core.negamax`, after the TT probe and before null move:
`if not checked and depth <= 3 and beta - alpha == 1 and -MATE_BOUND < beta <
MATE_BOUND: static = evaluate(); if static - 120*depth >= beta: return static`.
No legal-move test precedes it, so a stalemated side whose static score is
at least `beta + 120*depth` is scored on material instead of 0. C5 has the
identical test (`cs_search._negamax`), so this is inherited, not a port
divergence.

**Reproducible FEN.** `6Bk/5K2/8/8/8/8/8/R7 b - - 0 1` (Black stalemated, a
rook and bishop down). `negamax(depth 1, window (−1001, −1000))` returns −849
in both cores (`tools/review_c9_repro.py`).

**Can it change a decision?** The window it needs makes it harmless. The
child (stalemated side) is searched with `beta_child = −alpha_parent`; RFP
fires only when `static_child ≥ −alpha_parent + 120·depth`, i.e. when the
parent's static view of the stalemating move is already at least `120·depth`
*worse* than the alpha it holds. The move then fails low with the static
score; its true value 0 also fails low. The root choice is the same either
way, and a TT upper bound of −static instead of 0 cannot cut later (any
re-probe with a lower alpha re-searches, RFP no longer fires, and the exact
0 is found). The mirror case (a stalemated side that is statically ahead)
needs the *weak* side to stalemate the *strong* side, which requires the
strong side to have no legal move at all — essentially never with more than
a king and a blocked pawn.

**Measured activation** (`review/rfp_stalemate_probe.txt`, instrumented copy,
guard = return 0 when RFP would fire on a node with no legal move):

| set | positions | depth | RFP hits | hits on a stalemated node | root move or score changed by the guard |
|---|---|---|---|---|---|
| competition_like_v1 | 240 | 7 | 2,282,257 | **0** | 0 |
| ≤ 7-piece endings from the 2800 games | 300 | 9 | 987,526 | 1,753 (0.18%) | **0** (4 positions differ by < 0.4% in node count only) |

**≥ 100 cp / result flips:** none possible by the argument above and none
observed. **Smallest correct fix:** `has_legal_move` before the RFP return
(cost: one cheap pin-aware scan per RFP hit, about +1% nodes/s risk in
endings, 0 elsewhere). **Recommendation: document, deprioritise, no
candidate branch.** It is not a bug that affects play.

## Task 2 — high-severity self-audit of the compiled core

Read: `make_move`/`unmake_move`, `gen_moves` (pawns, EP, castling
through-check tests, promotions), `is_legal_after_make`, `pinned_pieces`,
`has_legal_move`, `rules_outcome`, `tt_probe/tt_store` and the packed entry,
`score_to_tt/score_from_tt`, `_check_time`, `quiescence`, `negamax` (RFP,
null move, LMR and its two re-searches, killers/history, terminal and bound
handling), `search_root`, and `cs_fast.search` (root policy, partial commit,
game keys). Findings:

| area | finding | severity |
|---|---|---|
| quiescence stalemate with only illegal captures | real, fixed in RC-F (`b7f42cf`), regression tests added | fixed |
| RFP on a stalemated node | inherited from C5, provably decision-neutral, 0 activations in 240 middlegames, 0 root changes in 300 endings | none in practice |
| quiescence at the ply cap in check | returns static eval without a legal-move test; C5 does the same; a checkmated side at ply ≥ 126 or qply 10 in check is scored by material for one node | theoretical (needs 126 plies of search) |
| TT entry packing | score+32768 fits 16 bits for ±32,000; depth 8 bits (≤ 64); move 18 bits at bit 26: 44 bits total, sign bit clear; replacement keeps the deeper entry and never ages within a game | no defect; a possible efficiency loss late in long games (deep stale entries block shallower fresh ones) |
| Zobrist keys | int64 with sign bit used; index `key & mask` on a negative key works because Numba masks the two's-complement pattern; EP term only when a capture exists (matches `compute_key`, tested) | none |
| castling | squares between king and rook tested empty via bitboards, king path tested for attack with the current occupancy, rights updated through `CASTLE_MASK[from] & CASTLE_MASK[to]` (rook captures included); perft-exact | none |
| en passant | capture square, discovered check along the rank and EP-pinned cases perft-exact (targeted fixtures) | none |
| promotions | queen-only in the quiescence set (C5's `_tactical_moves` policy, fixed-depth agreement holds); all four in the main set | none |
| mate distance | `score_to_tt/score_from_tt` round trip tested; mate-in-2 reported MATE−3 through the table on re-search | none |
| null move | non-PV, not in check, depth ≥ 3, needs non-pawn material; fail-high returns beta when the null score is a mate | none |
| LMR | quiet, non-killer, index ≥ 3, capped at child depth − 1, cancelled when the move gives check; reduced null-window → full-depth null-window → full-window re-search chain matches C5 | none |
| time | `objmode` `perf_counter` every 1,024 nodes (0.0074 µs per node), abort flag propagates as 0 through every return; root keeps a fully searched move; 150 ms budget returns in < 0.6 s; ladder PASS | none |
| Numba typing / JIT | every kernel is compiled by `warm_up()` on five positions before the clock; signatures are fixed (int64 arrays, float64 clock); the smoke shows no compile on later moves (0.00 s answers) | none |
| bitboards | `shr8` is sign-aware, msb via byte table, `DARK_SQUARES` written as its negative int64; corner-square sliders and h-file pawns covered by perft fixtures | none |

No new high-severity defect found. Two theoretical items recorded above; neither
has a realistic activation.

## Task 3 — RC-F profile (2 s × 24 bench positions, 70.3 M nodes, 2.24 Mnps under instrumentation)

Method (`review/prof_rcf.py`, `review/profile_rcf.txt`): call counters in an
instrumented copy of RC-F during a real search, multiplied by per-call
microbenchmarks of each component over 200 competition-like positions.
Search counts: make/unmake 57.3 M, gen_moves 17.7 M, evaluate 39.1 M, SEE
12.0 M, scored move lists 14.9 M, TT probes 40.9 M; time inside the compiled
root loop 100.0% (Python↔Numba transitions are not a cost).

| rank | component | share of runtime | possible optimisation | expected NPS gain | semantic risk | time |
|---|---|---|---|---|---|---|
| 1 | move ordering: `score_moves` (0.31 µs/list of 33, SEE on losing captures inside) + `pick_next` selection (O(n) per pick, 0.33 µs for a full 27-move selection) | ~19% measured (38% upper bound if every list were fully selected) | staged generation and scoring: try the TT move before generating, score captures first, score quiets only when the node survives; keeps the same order for the same scores | 10–20% | low if scores and tie-breaks are preserved (fixed-depth fingerprint must stay identical); medium if the order changes | 2–3 h + Gate 0 |
| 2 | search control flow and recursion: 70 M kernel calls each passing 16 array arguments (Numba reference-count traffic per argument), pruning tests, history/killer updates | ~28% (the unexplained remainder; the per-call cost could not be isolated because LLVM inlines the probe callee) | bundle the 16 arrays into fewer buffers (one int64 workspace + offsets) or pass a jitclass; reduces per-call incref/decref | 5–15% (unmeasured) | none semantically, but a large mechanical refactor | 3–4 h |
| 3 | make/unmake + legality (`is_legal_after_make` = one attack query per move) | ~14% (0.075 µs per make+legal+unmake) | skip the legality query for moves of unpinned non-king pieces when not in check (pins already computed cheaply in `has_legal_move`) | 5–8% | low (perft-testable) | 1–2 h |
| 4 | `in_check` after make for reduced moves and at every node | ~9% | compute "gives check" from the moving piece's attacks instead of a full king-attack query; reuse the node's check status | 3–5% | low | 1 h |
| 5 | move generation | ~6% (0.12 µs full list, 0.08 µs captures) | captures-first staged generation (shared with item 1) | 2–3% | low | with item 1 |
| — | SEE 2.3%, time checks 1.7%, TT 1.0%, evaluation 0.4% (incremental packed PST) | — | nothing worth doing | — | — | — |

**Best safe speed opportunity:** staged move ordering (item 1), flagged HIGH
PRIORITY at an expected 10–20% NPS if implemented order-preserving (the
fixed-depth fingerprint 4,852,987 at depth 8 is the identity check). Not
implemented tonight: it is a 2–3 h change and the brief caps a candidate at
30 minutes.

## Task 4 — what limits RC-F now

See the section appended after the error audit of the 60 clean RC-F games
against Stockfish 18 UCI_Elo 2800 (`corpus/strength/rcf/rcf_vs_sf2800_dev2400_60_strict.annotated.jsonl`,
audit `review/rcf_2800_errors.jsonl`, report `review/rcf_2800_error_audit.md`).
