# Correctness and benchmark-integrity repair

Date: 2026-09-02. Base: v0.4 (`a12e340`). Result: `champions/v0_5_correctness`.

Prompted by an independent audit from a second AI (Codex). Every finding was
treated as a hypothesis and reproduced before anything was changed. Two turned
out to be wrong or overstated, which is why reproducing first mattered.

## Findings, as reproduced

| # | finding | verdict | evidence |
|---|---|---|---|
| 1 | illegal FEN in the corpus at index 19 | **confirmed** | `BALANCED_OPENINGS[19]` = `Status.OPPOSITE_CHECK` |
| 2 | quiescence scores a stalemate statically | **confirmed** | `_quiescence` returned **-990** for a stalemate |
| 3 | `is_material_draw` over-declares draws | **confirmed** | 3 of 10 configurations disagreed with python-chess |
| 4 | null-move search can null again | **confirmed** (only at depth) | 1125 consecutive-null lines at depth 10; **0 at depth 7** |
| 5 | repetition documented too strongly | **confirmed** | scores a draw on the 2nd occurrence, not the 3rd |
| 6 | TT keys lack draw context | **confirmed, and demonstrably harmful** | won endgame scored **0 instead of +542** |
| 7 | SEE prunes forcing moves | **confirmed, quantified** | **20.7%** of negative-SEE captures give check |
| 8 | arena stores only aggregates | **confirmed** | no per-game record existed |
| 9 | arena uses 200 plies, competition 300 | **confirmed** | default now 300 |
| 10 | parent `CS_*` leaks into both engines | **confirmed** | inherited environment, unrecorded |
| 11 | `submission.zip` is stale | **partly** | stale on disk, but **not tracked** — it is gitignored |
| 12 | root is v0.4 while v0.3 is champion | **confirmed** | resolved by v0.5 |
| 13 | `AGENTS.md` missing | **confirmed** | created |

### Where the audit was not quite right

**Finding 4 needed a deeper search than the obvious one.** A first probe at
depth 7 found *zero* consecutive nulls and would have justified rejecting the
finding. It was too shallow: null-move needs depth >= 3 and reduces the child by
three or four plies, so a second null requires a non-PV node at depth >= 6.
Re-run at depth 10 the count was 1125. Recorded because "I tested it and found
nothing" was very nearly the wrong conclusion.

**Finding 11 was half right.** `submission.zip` was stale on disk, but it is in
`.gitignore` and has never been tracked, so it was not a checked-in artefact
masquerading as authoritative. It is now deleted, and `tools/release_check.py`
builds a fresh zip into a temporary directory and validates *that*, so no
on-disk archive is ever trusted.

## Fixes

### 1. Corpus (v1 → v2)

`BALANCED_OPENINGS[19]` was `8/2n2pk1/6p1/8/8/2B3P1/5P1P/6K1 w - - 0 40`: the
bishop on c3 attacked the black king on g7 with White to move. python-chess
builds such a board and generates moves from it without complaint, so nothing
ever failed — **every arena this project ran used it as a starting position.**
Replaced with the same material and structure, bishop on e3.

| | balanced | sharp | combined hash |
|---|---|---|---|
| v1 | 24 | 18 | `0c1fd866a32163e5` |
| **v2** | 24 | 18 | **`c269c63bb74391f0`** |

`tests/test_positions.py` now fails the suite on any invalid FEN, any terminal
position, any position where the side not to move is in check, and duplicates.
`tools/arena.py` refuses to start on an invalid corpus.

### 2. Quiescence terminals

Returned a static evaluation for stalemate. Now handles checkmate, stalemate,
the fifty-move rule and insufficient material.

The cheapest correct form took two attempts, both measured. Hoisting the full
capture list above the stand-pat cutoff was correct but cost **30%** of
nodes/second. Using `any(board.generate_legal_moves())` — which stops at the
first legal move — at the two points that return a static score costs **13.5%**
(74,811 → 64,721 nps) with **identical node counts**, so no search decision
changed. That is the version shipped.

### 3. Material draw

Now matches `is_insufficient_material()` exactly. It previously declared
K+N vs K+N, K+B vs K+N and opposite-coloured K+B vs K+B to be draws. Those are
*drawish*, not *dead*: a helpmate exists in each, so the rule does not draw them
and the search had no business forcing 0. Kept as our own implementation
(168 ns against python-chess's 521 ns, at every node) with exhaustive
equivalence tests over every small configuration plus 400 random endgames.

### 4. Consecutive null moves

A null search receives a null window, which is exactly the condition null-move
pruning tests for, so the child passed again immediately. Fixed with
`allow_null`, threaded through `_negamax`. The guard is deliberately narrow: it
blocks the immediate child, not descendants reached by real moves, because two
nulls *in a line* are fine and only two *in a row* are meaningless.

### 5. Transposition table and the fifty-move counter

The key omits the halfmove clock, so a position at clock 5 and at clock 96 share
an entry. Demonstrated harmful:

```
near-50-move position (clock 96): score 0
fresh position via the SAME table: score 0
fresh position via a CLEAN table:  score 542
```

A won rook endgame read back as a dead draw. Putting the counter in the key
would make every clock value a separate entry and gut the hit rate; instead the
table is bypassed for *scores* once the clock passes `TT_HALFMOVE_LIMIT = 80`,
which leaves a 20-ply margin. The stored move is still used for ordering, which
cannot be unsound.

### 6. SEE and forcing moves

20.7% of negative-SEE captures give check (831 of 4011 sampled). Checking
captures are now exempt from SEE pruning in quiescence, at a measured cost of
**1.9% more nodes** (1,674,285 → 1,705,479), tactical suite unchanged at 16/16,
move quality 0.5–0.6 cp average loss with zero blunders. Like `LMR_SAFE` this is
a robustness argument rather than a measured Elo gain, and is labelled as such.

### 7. Repetition — documented, not changed

Confirmed to be a heuristic: a draw is scored on the **second** occurrence, not
the third as FIDE requires. That is the usual engine convention and it is left
in place, but the code and `PROJECT.md` no longer describe it as rule-exact.
`tests/test_repetition.py` documents the behaviour, including the real failure
mode — a winning line whose only path revisits an earlier position is avoided.

### 8. Benchmark infrastructure

* **Raw records.** `--jsonl` writes a header (match id, timestamp, git commit,
  both snapshot hashes, corpus version and hash, clock, ply cap, workers,
  effective and stripped environment, platform) plus one line per game (start
  FEN, cluster, colours, result, termination, ply count, final FEN, duration,
  failure flag) and a summary. `--pgn` optional.
* **Environment sanitisation.** Every `CS_*` variable is stripped from the
  parent and only explicitly requested ones are restored, with both lists
  recorded. Verified live: a planted `CS_LMR=0` was stripped and reported.
* **Cluster-aware statistics.** `tools/stats.py` reports the naive game-level
  interval *and* a paired bootstrap over starting positions, because repeated
  positions are clusters. Tested on synthetic data where clustered and spread
  outcomes have identical W/D/L but must produce different intervals.
* **300-ply cap** by default, matching the competition. `--ply-cap 200`
  reproduces historical runs.

## Cost of the repairs

Fixed depth 6 on corpus v2, so old and new are measured on the same positions:

| | nodes | nps |
|---|---|---|
| v0.4 (before) | 1,674,285 | 74,811 |
| v0.5 (after) | 1,705,479 | ~58,000 |

Node count rises 1.9%, entirely from the SEE check exemption; the other fixes
changed **no search decision at all** on this corpus. Throughput falls, mostly
from the quiescence legality check. That is the price of the repairs and it is
paid deliberately: the class of bug removed here converts won games into draws,
and this project has already measured that ~0.4 ply of extra search is worth
approximately nothing in Elo.
