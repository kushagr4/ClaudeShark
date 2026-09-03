# ClaudeShark

An AI Chessathon entry: an iterative-deepening alpha-beta engine written against
`python-chess`, with a transposition table, quiescence search and a tapered
piece-square evaluation.

Current version: **v0.5.2-correctness**, frozen at
`champions/v0_5_2_correctness`. It is the release target. The working tree
matches it in *behaviour* -- depth-6 node counts are identical -- and adds one
dormant, flag-gated experiment (`cs_king.py`, `CS_EVAL_KING_SAFETY`, default
off) that was measured and rejected; see
`benchmarks/current/2026-09-02-king-safety-v1.md`.

### Version status, stated precisely

| version | what it is | strength evidence |
|---|---|---|
| v0.2 | first search bundle | superseded |
| **v0.3** | correctness fixes + faster evaluator | the strongest *evidence* the project has, but see the reclassification in `BENCHMARKS.md` — the "+30 Elo proven" claim does not survive the corpus and clustering corrections |
| v0.4 | v0.3 + static exchange evaluation | **experimental.** Efficiency gain is solid; playing strength measured +1 Elo, i.e. neutral |
| v0.5-correctness | v0.4 + the 2026-09-02 repairs | **not a strength claim.** It fixes bugs that silently corrupted results and play; it is not asserted to be stronger |
| v0.5.1-correctness | residual rules and benchmark-integrity repair | **not a strength claim** |
| **v0.5.2-correctness** | v0.5.1 + the PV transposition-cutoff fix | **not a strength claim**, but it removes an oracle-confirmed 560 cp tactical error for +0.41% nodes. See `benchmarks/current/2026-09-02-tt-pv-cutoff.md` |
| v0.6-material-scale | v0.5.2 with material scaled x1.47 | **rejected.** Passed every deterministic gate and then lost 40 Elo over 200 games (bootstrap CI -67..-14). See `benchmarks/current/2026-09-03-v0.6-material-scale.md` |
| v0.7-mopup | v0.5.2 + a mating gradient for bare-king endings, `CS_EVAL_MOPUP` | **keep for confirmation; default off.** Fixes its class outright (18/19 bare-king endings converted in play, 12/12 on the bench, 0/240 root moves changed, identical node counts) and moves the paired-game score by +3 Elo, bootstrap -0..+9. Not yet arena-tested. See `benchmarks/current/2026-09-03-mop-up-v1.md` |
| v0.8-passed | v0.5.2 + a rank-indexed passed-pawn bonus, `CS_EVAL_PASSED` | **inconclusive; default off.** Deterministic gates positive (blind-win suite robust loss 124->89 diagnostic, 149->123 validation read once; conversion diagnostic 226->181; root suite 35.3->34.0 with 29/240 moves changed; both adversarial flagship controls improved, none worsened) but the paired-game score is +2 Elo with a bootstrap of -26..+30. Not arena-tested. Failure audit: the term is a push incentive with no notion of consequence; no single corrective feature dominates, v2 deferred. See `benchmarks/current/2026-09-03-passed-pawn-v1.md` and `-failure-audit.md` |

**`submission.zip` is a build artefact, never authoritative.** It is
gitignored and is rebuilt from source by `tools/release_check.py` into a
temporary directory, which then validates *that* copy rather than anything on
disk. A stale archive in the working directory cannot be uploaded by mistake
because nothing reads it.

## Competition constraints

Taken from [aichessathon.com/docs](https://aichessathon.com/docs), which is
canonical and changes. Re-read it before every upload.

| | |
|---|---|
| Entry point | `agent.py` at the zip root, exposing `get_move(fen: str, time_left_ms: int) -> str` returning UCI |
| Submission | zip, **200 MB expanded** (sources disagree — the automated fetch reports 50 MB; see the provenance table in `docs/SPEC.md`. Our zip is ~58 KB, so nothing depends on it) |
| Dependencies | `torch` 2.13.0+cpu, `numpy` 2.5.2, `python-chess` 1.11.2, `onnxruntime` 1.29.0, `numba` 0.67.0, Python 3.12 stdlib. Nothing installs at runtime |
| CPU | 1 dedicated core |
| Memory | 2 GB |
| Filesystem | read-only, 256 MB scratch at `/tmp` |
| Network | none |
| Time control | 120 s + 0.5 s increment; 60 s initialisation budget before the clock starts |
| Output | 4096 bytes per move maximum |
| Validation | build check, then two smoke games (one as each colour) |
| Prohibited | third-party engines (Stockfish, Lc0, Maia) or wrappers around them; **native binaries inside the zip** ("what you ship has to be source a judge can read"); obfuscated code |
| Dependencies | the five preinstalled packages, plus — per the participant reading — anything declared in a `requirements.txt`, including compiled PyPI wheels. The automated fetch says such a file is ignored and an extra import crashes the agent; confirm with the organisers before relying on one. We ship none and import nothing extra |
| Process | **one process serves one game, started fresh for each**; in-memory state carries across our own moves within a game |
| Pondering | **awaiting organiser clarification — not implemented** (see `docs/SPEC.md`) |
| Adjudication | 300 plies without a result is adjudicated on material, else drawn; threefold and fifty-move draws are claimed automatically |
| Failure | illegal move, crash, timeout, init failure or malformed output all lose the game |
| Allowed | labelling training positions with an existing engine offline — the ban covers what ships in the zip, not what we learn from. Any model shipped must be one we trained |

Four things the docs make clear that shape the design:

* **Rated games start from curated positions, not the initial position.** An
  opening book is close to worthless. Broad positional strength is what counts,
  which is why the benchmark suite in `tools/positions.py` spans open, closed,
  queenless and endgame families rather than opening theory.
* **The process stays alive between moves.** The transposition table, the
  killer/history tables and the repetition history all persist across a game.
  It is also started fresh for each game, so cross-game state cannot leak.
* **Native binaries in the zip are rejected.** This is the one packaging rule
  both sources agree on: a hand-built `.so` or a Cython-compiled extension
  shipped inside the submission is an automatic rejection. Whether a compiled
  *PyPI wheel* can be pulled in through a `requirements.txt` is disputed — see
  `docs/SPEC.md`. Either way Numba is the safe route to compiled speed: it is
  preinstalled and ships as source compiled at runtime, so nothing compiled
  enters the zip.
* **Pondering status is unresolved.** The documentation read on 2026-09-02 does
  say pondering is allowed, but we are treating that as pending organiser
  confirmation and the production agent does no work between `get_move` calls.
  Design analysis only, in `docs/PONDERING.md`.

### The time control is a clock, not a per-move budget

The competition plays **120 s per side plus a 500 ms increment**. Earlier notes
in this repository described it as roughly "4.5 s per move"; that was wrong.
4.5 s is only what the allocator happens to spend on an opening move with a full
clock, and it falls as the game goes on. It survives here solely as a
*fixed-budget benchmark point*. Actual allocation depends on the remaining
clock, the known increment and the game phase — see `cs_time.py`.

Because the increment is published, it is a constant. v0.2 inferred it from
successive clocks; that machinery has been removed. `CS_INCREMENT_MS` overrides
it only so local arenas, which must use faster controls to fit games into an
afternoon, can state their real increment rather than have the engine guess.

Compliance status: the submission is pure Python over `python-chess` and the
standard library. No third-party engine ships or is invoked, no network access
occurs, nothing is written outside the process, and no code is obfuscated.

## Architecture

```
agent.py           entry point: legal-move fallback, new-game detection, warm-up
AGENTS.md          the short version of this file, for coding agents
cs_search.py       iterative deepening, negamax + alpha-beta, quiescence
cs_eval.py         tapered material + piece-square evaluation
cs_king.py         king safety, flag-gated OFF (measured and rejected, kept for v2)
cs_ordering.py     MVV-LVA, killers, history
cs_see.py          static exchange evaluation
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
harness/                the official harness, vendored unchanged (MIT, see THIRD_PARTY_LICENSE)
baselines/              the official random / greedy / minimax / numba opponents
tools/arena.py          many games from a FEN suite, in parallel, with an Elo interval
tools/bench.py          search benchmark: --depth N is deterministic, --ms N is not
tools/attribute.py      which of PVS / null-move / LMR is actually paying
tools/movequality.py    centipawn loss of a variant against a less-selective reference
tools/tactics.py        puzzles with objectively correct moves; --verify proves the mates
tools/clocksim.py       how much of its allocated clock an engine actually spends
tools/profile_search.py where search time goes
tools/profile_eval.py   evaluator throughput, and cProfile of it
tools/positions.py      the legacy FEN suites (corpus v2; see corpus/ for the calibrated ones)
tools/tune/             offline evaluator tuning: decomposition, audit, material fit, simulation
                        (see benchmarks/current/2026-09-02-material-tuning-audit.md)
tools/corpus/           reference-oracle labelling, structural tags, suite building, move-quality analysis
corpus/                 calibrated suites: competition_like_v1 (strength), stress_test_v1 (failure hunting)
tools/freeze.py         snapshot the engine as a champion
tests/                  correctness tests
champions/              frozen previous versions, kept as arena opponents
benchmarks/             recorded results with the exact command that produced them
docs/MOVEGEN.md         investigation: where future speed could come from
```

The `CS_*` environment flags (`CS_PVS`, `CS_NMP`, `CS_LMR`, `CS_LMR_SAFE`,
`CS_ASPIRATION`, `CS_TT_PV_CUTOFF`, `CS_INCREMENT_MS`) let any variant be run
from one code base. Every default is the shipping behaviour, so an agent started
with no environment set is the production engine.

### Search

Iterative deepening from depth 1. A legal fallback move is chosen before any
expensive work starts, and a position with one legal move returns immediately.
Timeouts are signalled by raising `SearchAbort` from wherever the search is; the
aborted board is discarded rather than unwound, which keeps `try`/`finally` out
of the hot loop entirely.

A root move that has been *fully* searched at the current depth and improved
alpha is committed even when the iteration is later aborted, because its score
came from a complete search with a valid window.

Four selective-search techniques are in, each benchmarked separately:

* **Principal variation search** — every move after the first gets a null-window
  probe and is only re-searched with the full window if it beats alpha.
* **Null-move pruning** — at non-PV nodes, depth ≥ 3, not in check, and only
  when the side to move has non-pawn material, so zugzwang positions are
  excluded. A mate score proved by a null move is not returned as a mate.
* **Late move reductions** — quiet, non-killer, non-promotion moves from index 3
  onward are searched shallower, then re-searched at full depth if they beat
  alpha. Moves that give check and en-passant captures are exempt.
* **Aspiration windows** — each iteration from depth 4 searches a ±30cp window
  around the previous score, widening geometrically on a fail and falling back
  to a full window rather than creeping outward.

Attribution matters here and is easy to get wrong: **null-move pruning is worth
nothing without PVS**, because it only fires at null-window nodes and PVS is
what creates them. The measurements are in `BENCHMARKS.md`.

Every one of these is behind a `CS_*` environment flag, defaulting to the
shipping behaviour, so any variant can be measured without maintaining a second
copy of the code that would drift.

Mate scores count from the root (`-MATE_SCORE + ply`), so shorter mates score
higher and unavoidable ones are delayed. They are re-based on the way into and
out of the transposition table, since a mate distance is only meaningful
relative to where it was found.

Draws are detected three ways.

* **Fifty-move counter** — rule-exact, and checkmate outranks it.
* **Insufficient material** — rule-exact, matching `is_insufficient_material()`
  exactly. It deliberately does *not* fire on merely drawish endings such as
  K+N vs K+N; those are not dead positions and the search has no business
  forcing 0 on them.
* **Repetition** — a **documented heuristic, not the rule**. FIDE draws on the
  third occurrence; this scores a draw on the second, either on the current
  search line or against the positions the engine has been asked about this
  game. That is the usual engine convention, but it can make a winning line
  whose only path revisits an earlier position look drawn.
  `tests/test_repetition.py` documents the actual behaviour.

The transposition key does not include the fifty-move counter, so the table is
bypassed for scores once the counter passes `TT_HALFMOVE_LIMIT`. Without that,
a near-fifty-move search poisons the same position at a fresh clock — measured
at 0 instead of +542 in a won rook endgame.

### Time management

Explicit, and pessimistic, because a flag is a whole point. Everything runs off
`time.perf_counter()`.

* **soft deadline** — whether to *start* another iteration, checked between
  iterations only, where stopping is free. The threshold is 45% of the soft
  budget by default, since the next ply costs 2–4× the last; it relaxes to 70%
  when the root move keeps changing and tightens to 35% once the root has been
  stable for three iterations.
* **hard deadline** — aborts mid-search, checked every 1024 nodes.
* **margins** — 40 ms for IPC overhead the referee attributes to us but we
  cannot measure, a 200 ms reserve, a cap of one third of the usable clock on
  any single move, and a panic mode below 120 ms that returns the depth-1 move
  or the legal fallback.
* **increment** — the published 500 ms constant, credited each move at 75%, and
  never credited beyond what is actually left on the clock.

Validated by `tests/test_time.py`: an allocation ladder from 50 ms to 120 s, real
searches at each, panic clocks down to 1 ms, and a whole self-played game run
with the referee's own clock arithmetic asserting the clock never reaches zero.

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
Everything positional beyond that is a *term* in the registry
`cs_terms.py`: a fast function of the board returning White's-point-of-view
centipawns, a transparently written reference twin, and a stage -- `packed`
(a middlegame/endgame pair added before the taper, phased like the tables)
or `post` (whole centipawns after the taper, for the bare-king mop-up whose
gradient must not be diluted). The active set is fixed once at import from
the `DEFAULTS` table and the environment (`CS_EVAL_PASSED=1` or
`CS_EVAL_TERMS=passed,mopup`) and can be changed by tests and tools with
`cs_eval.set_terms`; with nothing active the evaluator is exactly the tapered
tables (two falsy checks, depth-6 node count unchanged at 1,712,405). Three
terms are registered, all default off: king safety (`cs_king.py`), the
bare-king mop-up (`cs_mopup.py`), and the rank-indexed passed-pawn bonus
(`cs_passed.py`, cached by pawn structure). Nothing is switched on by
default, on purpose: every extra term has to pay for its runtime cost in
measured Elo, and one term is added, measured and gated at a time. The 2026-09-02 corpus calibration ranks the
missing terms by evidence (king safety first); see
`benchmarks/current/2026-09-02-corpus-calibration.md`.

**The material values are not under-scaled, and the 240-position suite cannot
be used as a strength gate.** A one-parameter material scale of x1.47, fitted
with the sigmoid scale K refitted per candidate and selected on validation,
improved the leakage-free external suite, the stress suite and every error
band, cost nothing at runtime, and then lost 40 Elo in a 200-game match. Two
things follow. Material scale is a dead end and should not be retried. More
importantly, oracle-agreement over single moves is a *screening* tool: it can
rank candidates for further work, but a candidate must win games before any
strength claim is made. See `benchmarks/current/2026-09-03-v0.6-material-scale.md`.

The post-mortem (`benchmarks/current/2026-09-03-v0.6-postmortem.md`) found
why: the 240-position suite admits only near-balanced positions (239 of 240
at |Stockfish cp| < 50) while 40% of a game's moves are played at |cp| >= 200,
and the candidate's extra errors are exactly there -- ten points worse at both
converting an advantage and holding a deficit, from an evaluator that is
over-confident about large material edges and blind to compensation. The
metric was sound; the sample was not. **The pre-arena gate is now a
fixed-depth paired self-play set** (`tools/postmortem/play.py` +
`annotate.py` + `report.py`, ~50 minutes for 200 games), which reproduced the
loss at -26 Elo with a bootstrap excluding zero. The suite remains a
tactical and diagnostic screen only.

## The candidate pipeline

Three gates, in order, adopted after the v0.6 post-mortem. Gate 1 is screening,
gate 2 decides, gate 3 confirms.

| gate | instrument | cost | what it can and cannot see |
|---|---|---|---|
| 1 | `tools/corpus/analyse.py` on `corpus/competition_like_v1.jsonl` | minutes | Root move quality against Stockfish on 240 near-balanced positions. Tactical and catastrophic-error screening. **Cannot** see a change that trades balanced-position quality for unbalanced: 239 of its 240 positions sit under 50 cp, while 40% of the moves in a real game are played at 200 cp or more. |
| 2 | `tools/postmortem/play.py` + `annotate.py` + `report.py` | ~50 min for 200 games at depth 6 | Fixed-depth paired self-play, deterministic, every move retained. W/D/L with a cluster bootstrap, serious-error and first-error rates, conversion from +200, defence from -200, repetition outcomes. Reproduced the v0.6 loss at -26 Elo with a bootstrap excluding zero. |
| 3 | `tools/arena.py` | hours | Real clock, real time management. Run only if gate 2 passes. Retains move history by default. |

The rule that produced this: **the root suite alone is not predictive Elo
evidence.** A candidate must not reach gate 3 on gate 1 alone.

Gate 1 also includes `corpus/blindwin_regression_v1.jsonl` (68 blind-win
positions, `tools/blindwin/suite.py`) and `corpus/conversion_regression_v1.jsonl`: 90 real
self-play positions from failed conversions and defences, split into a
diagnostic and a validation half by game, built by
`tools/conversion/suite.py`. It is a regression tool for the conversion
weakness, never an Elo instrument.

**The blind wins are endgame evaluation, and the next experiment is passed
pawns.** The blind-win audit (`benchmarks/current/2026-09-03-blind-win-audit.md`)
took the 129 positions in retained self-play where Stockfish scores
production +300 or better while its own root says under +100, and walked
Stockfish's principal variation to its end: in 110 of them the static
evaluation *still* does not see the win on that quiet position. Pawn endings
score +4 where Stockfish says +616; the gap climbs with the winner's most
advanced passer, +324 at ranks 1-3 to +665 at ranks 6-7. Quiescence recovers
the score in 12 episodes and depth-6 search in 7; the search is not the
problem. The single next experiment is an endgame-weighted passed-pawn term
with king-distance components, gated on the 240 suite, the conversion and
blind-win regression suites, then fixed-depth paired self-play. Passers were
deferred twice before for lack of a causal signal; the audit supplies it.

**Mop-up v1** (`cs_mopup.py`, flag `CS_EVAL_MOPUP`, default off) is the
first experiment to come out of that audit: two geometric terms -- drive the
defending king to an edge, bring the attacking king closer -- active only when
one side is a bare king and the other has a rook or queen, zero everywhere
else. It finishes every stuck ending the audit found and changes nothing
outside its domain; the paired-game gain is +3 Elo with a bootstrap of -0..+9,
because the class it fixes cost the baseline only two to six half-points per
200 games. Kept flag-gated pending a time-controlled arena.

**Passed pawns v1** (`cs_passed.py`, flag `CS_EVAL_PASSED`, default off) is
the second: one bonus indexed by relative rank, separate middlegame and
endgame tables, both monotonic, tapered with everything else, the front pawn
of a doubled file only. Deliberately nothing else -- no king distances, no
square rule, no connected or protected or blocked adjustments -- so the
result is attributable to the single fact "this pawn cannot be stopped by a
pawn". The tables were chosen once from a five-member family on the
diagnostic half of the blind-win suite (the smallest member won outright)
and frozen. It moves the deterministic gates the right way and leaves the
adversarial controls no worse, but the term supplies only about 3% of the
missing evaluation at the end of Stockfish's lines: the moves improve
because the search now has a gradient toward keeping and advancing passers,
not because the static sees the win. 200 paired games: +2 Elo, bootstrap
-26..+30. Inconclusive; kept flag-gated.

**The conversion weakness is endgame knowledge, not search.** The 2026-09-03
conversion audit (`benchmarks/current/2026-09-03-conversion-audit.md`) found
production converts +200 into a win 44% of the time and loses only 3%; half
of its conversion errors persist at depth 10 and are endgame technique;
twelve of forty-nine failed conversions are K+Q v K, K+R v K and the like,
shuffled into repetition at a root score of +1000 because the evaluator's
whole mating incentive is a 61 cp spread in the PeSTO king table. Ruled out
with evidence: aggressive pruning while ahead (the search prunes *less* when
ahead), simplification, and concave material (Stockfish's value per unit is
flat). The next experiment is a mop-up term for won endgames, gated as
above.

## Testing methodology

Five layers, all runnable from the Makefile.

1. **Correctness** (`make test`) — legality across the position suites, terminal
   positions, promotion and en-passant paths, mate finding, mate-score round
   trips through the TT, evaluator equivalence against a transparent reference
   over 400 randomly-played positions, a clock ladder from 50 ms to 120 s, a
   whole self-played game run on the referee's own clock arithmetic, and a game
   played out of the extracted submission zip.
2. **Deterministic search benchmark** (`tools/bench.py --depth N`) — fixed
   *depth*, so node counts reproduce exactly and are machine-independent. This
   is the right instrument for comparing pruning changes; a time-limited run
   measures the laptop as much as the engine.
3. **Fixed-budget benchmark** (`make bench`) — what the engine achieves in a
   given amount of thinking. Use for reporting, not for A/B.
4. **Tactics and move quality** (`tools/tactics.py`, `tools/movequality.py`) —
   whether the moves are any *good*. `movequality` scores a variant's chosen
   moves against a less-selective reference in centipawns, which is how a
   pruning change that buys speed with blunders gets caught.
5. **Arena** (`make suite`) — many games from the FEN suite, every position
   played once with each colour, run concurrently, reporting the score and an
   Elo difference with a 95% interval.

**Depth is not strength.** A selective search that reduces the wrong moves
reaches a bigger depth number and plays worse. No promotion is justified by
depth alone; layers 4 and 5 exist to say whether the moves improved.

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

**Pondering** — potentially the largest non-rewrite gain, and **blocked pending
organiser clarification**. Not implemented, not scheduled. Analysis only, in
`docs/PONDERING.md`.

**Time management** — the engine finishes a 120 s game with about a fifth of its
clock unspent and uses 67.9% of its soft budget on an average move. The fix is a
single parameter (`START_FRACTION`, or `DEFAULT_MOVES_TO_GO` from 26 to ~22) and
is worth perhaps 0.2 ply. Deliberately not bundled with anything else; it is the
next isolated A/B.

**Search** — check extensions; futility pruning and razoring; mate-distance
pruning; a history-aware reduction table rather than the current fixed 1–2 ply.
PVS, null-move pruning, LMR and aspiration windows arrived in v0.3; static
exchange evaluation for quiescence pruning and capture ordering in v0.4.

**Speed** — at ~69k nodes/second we reach depth 8 where a C engine reaches 14+.
About half the remaining time is inside python-chess, which bounds what
optimising our own code can do. Candidates: staged move generation (try the TT
move before generating anything), incremental evaluation through push/pop, and
cheaper ordering. A custom or Numba-jitted move generator is the only route to
an order of magnitude and is analysed in `docs/MOVEGEN.md` — **not recommended
yet**, and gated on a perft spike proving 5x before any rewrite is authorised.
Note that native binaries in the zip are rejected, so Cython and C are off the
table; Numba is compliant because it is preinstalled and ships as source.

**Evaluation** — passed pawns, rook on open file, king safety, mobility, doubled
and isolated pawns. Cheap terms only, one at a time, each justified by Elo.

**Learned evaluation** — deliberately deferred. Once the classical engine is
strong: a small NNUE-style net trained by us, exported to ONNX, sized so it can
be evaluated thousands of times per move rather than fifty.
