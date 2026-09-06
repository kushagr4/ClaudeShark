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

### Task 4 results — RC-F, 60 clean games vs Stockfish 18 UCI_Elo 2800 (dev2400, strict)

Pipeline: `tools.strength.convert` → `tools.postmortem.annotate` (Stockfish
18, cheap/deep node budgets) → `tools.strength.accuracy` → `tools.strength.audit`
(replay at the recorded think time, 10 s deep replay, fixed-depth ladder
9–14) → `review/rcf_error_classify.py`. Files: `review/rcf_2800_accuracy.md`,
`review/rcf_2800_error_audit.md`, `review/rcf_2800_errors.jsonl`,
`review/rcf_2800_error_classes.md`, `review/notrepro_replay_losses.json`.

| measure | RC-F vs 2800 (60 games, 3,332 own moves) | C5 vs 2400 (100 games, 4,100 moves, 2026-09-06 morning) |
|---|---|---|
| ≥ 100 cp self-inflicted errors | **3.33%** (111) | 6.54% (268) |
| ≥ 300 cp | **0.57%** (19) | 1.44% (59) |
| average cp loss per error | 34.7 | 69.6 |
| result-flipping errors | 41 in 60 games | 102 in 100 games |
| accuracy (CLAUDESHARK_ACCURACY_V1) | mean 96.02, median 96.34, min 87.67; games ≥ 99.5: 4 of 60 | — |

**Extra-depth repair rate** (errors reproduced at the game budget with a
ladder point at replay depth D + k; ladder capped at depth 14, so +2/+3 are
available for fewer errors): **+1: 18/73 = 25%, +2: 20/56 = 36%, +3: 17/38 =
45%.** Depth alone is no longer the main lever: more than half of the errors
survive three extra plies.

**Mechanism classes** (heuristic, stated in the script):

| class | errors | result flips | notes |
|---|---|---|---|
| no repair by +3 plies nor by a 10 s replay ("EVALUATION / knowledge") | 52 | 17 | queens on the board in 39 of 52; late middlegame 23, endgame 11, opening/middlegame 18; the mover was already lost by the oracle in 30 (collapse of a lost position), drawn in 17, winning in 5 |
| not reproduced by a fresh-table replay at the same budget ("state / instability") | 45 | 20 | the replay chose a different move; see below |
| tactical horizon (repaired at +1/+2/+3) | 8 | 3 | small: the 12-ply engine has largely removed this class |
| search shape (10 s replay repairs, +3 plies do not) | 6 | 1 | LMR / ordering candidates |
| endgame knowledge (≤ 8 pieces, nothing repairs) | 4 | 1 | K+P and rook endings |
| conversion (winning by ≥ 300, no repair) | 2 | 0 | |
| time (moved in < 0.8 s with > 20 s on the clock) | 2 | 0 | |

**The "not reproduced" class, examined.** Scoring the fresh-table replay
move with the oracle: better than the game move in 32 of 45, similar in 8,
worse in 5; the replay move loses under 100 cp in 26 of 45; median loss 163
cp (game) vs 62 cp (replay); 10 of the class's 20 result flips avoided.
Matched control: 45 random *good* moves (loss < 50 cp) replayed with a fresh
table at their recorded budgets — the same move 33 times, **0 new ≥ 100 cp
errors** (base rate 3.33%, expected about 1.5), mean loss 8.6 cp. So a fresh
table is not worse on average, and at the error positions it is much
better — but the error positions were *selected* for the in-game state
having gone wrong, and a re-roll of any kind regresses toward the mean, so
"carried-over table/killer/history state hurts" is a hypothesis with a real
signal, not a demonstrated cause. It is cheap to test properly (paired
60-game screen: RC-F vs RC-F with table, killers and history reset per
move, game keys kept). Not implemented tonight: the brief's bar for a
same-night candidate is exceptional confidence, and this has a selection
bias it cannot remove without the screen.

**Ranking of what limits RC-F now** (by result flips, frequency, fixability):

1. **Evaluation / positional knowledge** (52 errors, 17 flips): nothing in
   the search fixes them; RC-F evaluates with PeSTO tables, bishop pair and
   tempo only. Fixable but not cheaply (every earlier single-term attempt was
   rejected on the 6-ply engine; at 12 plies the trade-off may differ), and
   it is the last lane in the sprint priority.
2. **Carried-over search state / marginal decisions** (45 errors, 20 flips):
   cheap to test (one-line reset per move), unproven cause.
3. **Search shape and horizon** (14 errors, 4 flips): LMR/ordering and
   +2/+3-ply tactics; speed work (staged ordering, +10–20% NPS ≈ +0.3 ply)
   helps this class only, and +1 ply repairs just 25% of errors.

## Optional candidate

**NOT created.** No change reached the "exceptionally high-confidence" bar by
23:00: the state-reset hypothesis has an unremovable selection bias without a
game screen, and staged ordering is a 2–3 h change. Both are pre-registered
below for tomorrow, after the independent reviews.

Pre-registration for tomorrow (first in line, ≤ 30 min implementation):
CANDIDATE: RC-F + per-move reset of table, killers and history (game keys
kept). CURRENT CHAMPION: RC-F. HYPOTHESIS: carried-over state from previous
searches biases marginal decisions; a fresh state per move removes 20–50% of
the "not reproduced" error class. TARGET FAILURE CLASS: errors not
reproduced by a fresh replay (45 of 111). EXPECTED NPS EFFECT: none. EXPECTED
CLOCK EFFECT: none (same allocator). EXPECTED ACTIVATION: every move.
MATCHED NEGATIVE: random good-move replays (done tonight: 0 of 45 harmed).
REJECTION: < 52% over 60 paired games vs RC-F, or any failure. MAX TIME: 30
min + one 60-game screen.

## Final state (22:40 UK)

Active jobs 0; sweep clean (no python, Stockfish or uv processes); C10 still
paused; no upload performed. Evidence committed on `kushagra/rc-f-correctness`.
