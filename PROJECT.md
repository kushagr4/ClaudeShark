# ClaudeShark

An AI Chessathon entry: an iterative-deepening alpha-beta engine written against
`python-chess`, with a transposition table, quiescence search and a tapered
piece-square evaluation.

Current version: **v0.2**. Previous versions are frozen under `champions/` and
kept as arena opponents.

## Competition constraints

Taken from [aichessathon.com/docs](https://aichessathon.com/docs), which is
canonical and changes. Re-read it before every upload.

| | |
|---|---|
| Entry point | `agent.py` at the zip root, exposing `get_move(fen: str, time_left_ms: int) -> str` returning UCI |
| Submission | zip, 50 MB unzipped maximum |
| Dependencies | `torch` 2.13.0+cpu, `numpy` 2.5.2, `python-chess` 1.11.2, `onnxruntime` 1.29.0, `numba` 0.67.0, Python 3.12 stdlib. Nothing installs at runtime |
| CPU | 1 dedicated core |
| Memory | 2 GB |
| Filesystem | read-only, 256 MB scratch at `/tmp` |
| Network | none |
| Time control | 120 s + 0.5 s increment; 60 s initialisation budget before the clock starts |
| Output | 4096 bytes per move maximum |
| Validation | build check, then two smoke games (one as each colour) |
| Prohibited | third-party engines (Stockfish, Lc0, Maia) or wrappers around them; obfuscated code |
| Allowed | labelling training positions with an existing engine offline — the ban covers what ships in the zip, not what we learn from. Any model shipped must be one we trained |

Two things the docs make clear that shape the design:

* **Rated games start from curated positions, not the initial position.** An
  opening book is close to worthless. Broad positional strength is what counts,
  which is why the benchmark suite in `tools/positions.py` spans open, closed,
  queenless and endgame families rather than opening theory.
* **The process stays alive between moves.** The transposition table, the
  killer/history tables and the repetition history all persist across a game.

Compliance status: the submission is pure Python over `python-chess` and the
standard library. No third-party engine ships or is invoked, no network access
occurs, nothing is written outside the process, and no code is obfuscated.

## Architecture

```
agent.py           entry point: legal-move fallback, new-game detection, warm-up
cs_search.py       iterative deepening, negamax + alpha-beta, quiescence
cs_eval.py         tapered material + piece-square evaluation
cs_ordering.py     MVV-LVA, killers, history
cs_tt.py           fixed-size transposition table, mate-score encoding
cs_time.py         soft/hard deadlines, increment inference
cs_constants.py    score bounds, piece values, PeSTO piece-square tables
```

Modules live at the repository root with a `cs_` prefix on purpose. The official
packager (`harness/package.py`) zips `*.py` from the root, so a flat layout is
packaged correctly with no extra flags; the prefix guarantees nothing shadows a
standard-library module when the submission directory goes first on `sys.path`.

Supporting code, none of which ships:

```
harness/           the official harness, vendored unchanged (MIT, see THIRD_PARTY_LICENSE)
baselines/         the official random / greedy / minimax / numba opponents
tools/arena.py     many games from a FEN suite, in parallel, with an Elo interval
tools/bench.py     fixed-budget search benchmark: depth, nps, TT hit rate
tools/positions.py the balanced FEN suite
tests/             correctness tests
champions/         frozen previous versions, kept as arena opponents
```

### Search

Iterative deepening from depth 1. A legal fallback move is chosen before any
expensive work starts, and a position with one legal move returns immediately.
Timeouts are signalled by raising `SearchAbort` from wherever the search is; the
aborted board is discarded rather than unwound, which keeps `try`/`finally` out
of the hot loop entirely.

A root move that has been *fully* searched at the current depth and improved
alpha is committed even when the iteration is later aborted, because its score
came from a complete search with a valid window.

Three Phase-10 techniques are in (added in v0.2, benchmarked one at a time):

* **Principal variation search** — every move after the first gets a null-window
  probe and is only re-searched with the full window if it beats alpha.
* **Null-move pruning** — at non-PV nodes, depth ≥ 3, not in check, and only
  when the side to move has non-pawn material, so zugzwang positions are
  excluded. A mate score proved by a null move is not returned as a mate.
* **Late move reductions** — quiet, non-killer, non-promotion moves from index 3
  onward are searched shallower, then re-searched at full depth if they beat
  alpha.

Mate scores count from the root (`-MATE_SCORE + ply`), so shorter mates score
higher and unavoidable ones are delayed. They are re-based on the way into and
out of the transposition table, since a mate distance is only meaningful
relative to where it was found.

Draws are detected three ways: the fifty-move counter, a cheap insufficient
material test, and repetition. Repetition uses the search path (checked at a
stride of two plies, bounded by the halfmove clock) plus a record of every root
position the engine has been handed this game — the referee claims threefold
automatically, so an engine that cannot see a repetition can draw a won game.

### Time management

Explicit, and pessimistic, because a flag is a whole point. Everything runs off
`time.perf_counter()`.

* **soft deadline** — whether to start another iteration. Checked between
  iterations only. An iteration is also skipped when more than 45% of the soft
  budget is already gone, since the next ply costs 2–4× the last.
* **hard deadline** — aborts mid-search, checked every 1024 nodes.
* **margins** — 40 ms for IPC overhead the referee attributes to us but we
  cannot measure, plus a 200 ms reserve, plus a cap of one third of the
  remaining clock on any single move.

The API never tells us the increment. It is inferred: we know what we spent and
what the clock said, so the difference between the next clock and that
prediction is the increment. The estimate is deliberately biased low.

### Transposition table

A preallocated list of 2^19 slots, indexed by `hash(board._transposition_key())`
masked to size, holding `(key, depth, score, bound, move)`. Fixed-size by
construction so a long game cannot grow it without bound. Storing the full key
alongside means an index collision is detected rather than silently returning a
wrong score. Replacement is depth-preferred within a position and
always-replace across positions.

### Move ordering

`TT move > queen promotions > captures (MVV-LVA) > killers > history > quiet`.
Two killers per ply; history indexed by colour, from-square and to-square, and
rescaled when it saturates so bands never overlap. History is halved between
moves.

### Evaluation

Tapered PeSTO material and piece-square tables interpolated on a 0–24 game
phase, plus a bishop pair term and a tempo bonus. Written as one flat function
with locals bound up front and no allocation, scanning piece bitboards directly.
Nothing else is in there yet, on purpose: every extra term has to pay for its
runtime cost in measured Elo.

## Testing methodology

Three layers, all runnable from the Makefile.

1. **Correctness** (`make test`) — legality across the whole position suite,
   terminal positions, promotion and en-passant paths, mate finding, mate-score
   round trips through the TT, evaluation colour symmetry, budget adherence
   under clocks from 1 ms to 3 s, and a full self-play game to flush out rare
   paths.
2. **Search benchmark** (`make bench`) — fixed budget per position across the
   suite, reporting depth, nodes, nodes per second, quiescence share and TT hit
   rate. This attributes a change to speed or to ordering.
3. **Arena** (`make suite`) — many games from the balanced FEN suite, every
   position played once with each colour, run concurrently, reporting the score
   and an Elo difference with a 95% interval.

Rules of engagement: **candidate vs champion**, always. A change is only an
improvement when it beats the previous champion over enough games that the
interval excludes zero. Two games mean nothing; a 3% edge needs hundreds. The
current champion is frozen under `champions/` and used as the arena opponent.

**Match the arena's per-move budget to the competition's.** This cost us a whole
run and is the single most important lesson so far. The obvious way to get games
quickly is a fast time control, but 5 s + 0.05 s gives about 180 ms per move
while rated games give about 4.5 s. Reductions and null-move pruning need depth
before they pay: the same change measured −26 Elo at 180 ms per move and +26 Elo
at 900 ms, and its depth advantage over v0.1 grows from +0.17 ply to +1.29 ply
across that range. A result measured at the wrong operating point does not
transfer. `tools/bench.py --engine champions/<name> --ms 4500` compares two
engines at the real budget deterministically, and is the cheap sanity check to
run before committing an arena to hours of games.

Instrumentation is a plain dataclass filled once per move. Setting
`CLAUDESHARK_DEBUG=1` prints one line per move to stderr; nothing is logged from
inside the search loop.

## Benchmarks

See `BENCHMARKS.md` for the running record.

## Future optimisation ideas

Ordered by expected Elo per unit of risk. Each is a separate change, A/B tested
against the champion, and reverted if it does not measure.

**Search** — aspiration windows; check extensions (currently a checking move can
be reduced, which is the most likely weakness in the LMR scheme); futility
pruning and razoring; static exchange evaluation for capture ordering and
quiescence pruning; mate-distance pruning; a history-aware reduction table
rather than the current fixed 1–2 ply. Principal variation search, null-move
pruning and late move reductions are already in as of v0.2.

**Speed** — this is where most of the strength is, because at ~74k nodes/second
we reach depth 6–7 where a C engine reaches 12+. Profile first. Candidates:
avoiding `list(board.legal_moves)` allocation, staged move generation (try the
TT move before generating anything), incremental evaluation maintained through
push/pop, and a Numba-jitted movegen and evaluation over a bitboard
representation of our own. The last is a large, risky project and must be gated
on a measured win.

**Evaluation** — passed pawns, rook on open file, king safety, mobility, doubled
and isolated pawns. Cheap terms only, one at a time, each justified by Elo.

**Learned evaluation** — deliberately deferred. Once the classical engine is
strong: a small NNUE-style net trained by us, exported to ONNX, sized so it can
be evaluated thousands of times per move rather than fifty.
