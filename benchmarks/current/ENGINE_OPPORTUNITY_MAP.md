# Engine opportunity map — 2026-09-05 07:25

Baseline: RC-A / exact rated-v1 (`champions/rated_v1`, working tree with every
term off; depth-6 fingerprint 1,712,405 nodes, 61 knps on this machine).
Audited from the code, the profile (`tools.profile_search`, 6 positions,
3 s each) and an instrumented depth-6 run over the 24-position suite.

## Where the time goes (profiled shares, depth 6)

| cost centre | share | note |
|---|---|---|
| python-chess legal-move generation in negamax (`list(board.legal_moves)`) | ~35% | 30 µs per interior node; unavoidable per node unless generation is staged |
| `push`/`pop` | ~14% | python-chess bookkeeping; not ours to change |
| `evaluate` | ~15% | 4.4 µs per call, 346k calls; already packed and unrolled |
| `order_moves` | ~11% | scores and sorts every legal move at every interior node; 5.3M `Move.__eq__` calls |
| quiescence stalemate probes (`any(generate_legal_moves())`) | ~5% | 667k probes at 2.3 µs; already cheap |
| tactical move generation, evasions, `is_check` | ~15% | |

Instrumented facts: 133,779 interior nodes reached generation; **79% cut off
on their first move**; only **22%** had a table move (17.5% of nodes cut on it).
So most first-move cutoffs come from a capture or a killer, after the full
list was generated and sorted.

## Opportunities, ranked

| # | mechanism | expected upside | implementation risk | runtime risk | test cost | existing evidence | priority |
|---|---|---|---|---|---|---|---|
| A1 | **Staged move picker**: table move → winning captures/queen promotions (MVV-LVA) → killers → losing captures → history-ordered quiets → under-promotions, generated lazily with python-chess masks; identical order to today's sort | 10–15% NPS with **identical search tree** (fingerprint must not change) | medium: tie order within stages must match the stable sort; TT-move legality via `is_legal`; LMR index preserved | none if identical | Gate 0 = fingerprint + root move/score identity on suites and random positions + tests; short timed screen | 79% first-move cutoffs measured today | **1** |
| A2 | Cheaper `Move` equality in ordering (integer keys) | 2–3% NPS | low | none | fingerprint | 5.3M `__eq__` calls | 3 (fold into A1 if free) |
| A3 | Evaluation cache keyed by transposition key | ≤3% | low | memory | fingerprint | eval is 15% and the key costs 1.2 µs | 5 |
| A4 | Check extension / singular extension | unknown, could help tactics (R5 23 hxg4, R11 31 Nxe4) | medium: interacts with LMR/NMP/mate distances | node growth | Gate 1 on rated errors, Gate 2 | depth 7–8 repairs 6/27 key errors; no extension exists today | 4 |
| A5 | LMR/NMP retuning | small either way | low | search instability | Gate 2 | ablation 2026-09-04: null −2, LMR removal +367 cp at 1.9× nodes | 6 (closed unless A4 opens it) |
| B1 | **Attack-blindness signal**: smallest feature separating genuine attacks from fake ones (safe checks, escape squares, attacker/defender counts, pinned defenders) with matched negatives | the largest deployment loss source (R1, R3, R5, R10, R11; 104 correct-move/wrong-score) | high: broad king safety already failed globally; must be narrow and phase-aware | eval cost per node | Gate 1 on the rated positions with matched negatives; short Gate 2 | strong deployment evidence; depth fixes only 1 in 4 | **2** |
| C1 | Conversion: blind wins in rook/minor + pawns, perpetual-check horizon | two half-points yesterday | high; prior mop-up/passed/V2.2a not strength-proven | | Gate 1/2 | R3, R7 | 7 (only with time) |
| D | Time policy | none | — | floor | — | five nulls | closed |
| E | Book (own-engine moves only) / tablebases | small / negligible | rules-bound | size | coverage measured (84–87% start recurrence; ≤5-piece hit rate 1/15 games) | measured | 8 / closed |

## Plan

C1-search-staged (A1) first: identical-tree speedup, Gate 0 by fingerprint,
one short timed screen. Then B1 with a pre-registered positive/negative set
drawn from the rated positions. Nothing else unless those two settle early.
