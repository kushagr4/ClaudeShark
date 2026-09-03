# Working on ClaudeShark

A chess engine for the [AI Chessathon](https://aichessathon.com), written in
Python over `python-chess`. This file is the short version for coding agents.
Deeper detail lives in [`PROJECT.md`](PROJECT.md) (architecture, constraints,
testing), [`docs/SPEC.md`](docs/SPEC.md) (the competition rules, verbatim, with
retrieval dates), [`BENCHMARKS.md`](BENCHMARKS.md) (what has actually been
measured) and [`benchmarks/`](benchmarks/) (raw records).

## The one rule that matters

**Elo over novelty.** A change is worth keeping only if the evidence says it
plays better chess. This repository has three separate 400-game measurements
showing that more search does *not* automatically mean more strength, so
"deeper" and "faster" are not arguments on their own.

## Before you change anything

1. **Read the actual repository first.** Do not assume a file, flag or number
   exists because it would make sense. Several corrections in this project's
   history came from claims that a fresh read contradicted.
2. **Check `git status` and the frozen snapshots.** `champions/` holds every
   version that has been measured. Never modify or delete one; they are the
   opponents that make results comparable.
3. **Reproduce before you fix.** When handed a bug report — including from
   another agent — write the reproduction first and confirm it. Audit findings
   in this project have been confirmed, partly confirmed and outright wrong, and
   the only way to tell was to run them.

## Experiments

* **One variable at a time.** Bundled changes cannot be attributed. The v0.2
  bundle had to be re-measured from scratch a session later because of this.
* **Use the flags.** Every search feature is behind a `CS_*` environment flag
  defaulting to shipping behaviour, so variants come from one code base rather
  than diverging copies. `tools/make_time_variants.py` generates single-constant
  variants and refuses to write one that differs by more than that line.
* **Fixed depth for pruning changes, fixed time for reporting.**
  `tools/bench.py --depth N` is deterministic; `--ms N` measures the machine as
  much as the engine.
* **Match the arena's per-move budget to the competition's.** A fast local
  control produces a per-move budget an order of magnitude smaller and has
  already reversed the sign of one result.
* **Three gates, in order. Never skip to the last one.**
  1. *Root move quality* -- `tools/corpus/analyse.py` on
     `corpus/competition_like_v1.jsonl`, plus the conversion regression suite
     `corpus/conversion_regression_v1.jsonl` via `tools/conversion/suite.py run`
     and the blind-win regression suite `corpus/blindwin_regression_v1.jsonl`
     via `tools/blindwin/run.py` (report by row, by unique FEN and by
     source-game cluster; tune on the diagnostic half only, read validation
     once after freezing).
     Cheap screening **only**. It admits
     near-balanced positions by construction (239 of 240 under 50 cp) and
     cannot see a change that trades balanced-position quality for unbalanced,
     which is how v0.6 passed it and lost 40 Elo.
  2. *Fixed-depth paired self-play* -- `tools/postmortem/play.py`, then
     `annotate.py`, then `report.py`. 100-200 games, every move retained,
     deterministic. Report W/D/L, the cluster bootstrap, serious-error and
     first-error rates, conversion from +200, defence from -200, and
     repetition outcomes. This is the gate that reproduced the v0.6 loss.
  3. *Real time-controlled arena* -- only if gate 2 passes.
* **Never present the root suite alone as predictive Elo evidence.**
* **Record raw game outcomes, moves included.** `tools/arena.py --jsonl`
  writes per-game records with snapshots, corpus hash, environment and
  terminations, and the move history now defaults to the same path with a
  `.pgn` suffix. Discarding it takes an explicit `--no-pgn` and is warned
  about. The v0.6 arena ran without a PGN and the post-mortem could not
  reconstruct one trajectory out of 200 games.
* **Report both intervals.** The naive game-level CI and the paired bootstrap
  over starting positions. Repeated positions are clusters, not independent
  samples.
* **Never call depth or nodes/second an Elo gain.** Say what was measured.

## Correctness

* The corpus is validated: `tests/test_positions.py` fails on any invalid FEN.
  An `OPPOSITE_CHECK` position sat in it for the project's first several
  sessions and corrupted every arena.
* Draw handling is subtle and has produced three separate bugs — a forced mate
  scored as a draw, a stalemate scored statically, and fifty-move contamination
  through the transposition table. Treat anything touching draws as high risk
  and test the **score**, not just that a legal move comes back.
* Prefer a documented heuristic to a silent one. If the search forces 0 where
  the rules do not, say so in the code.

## Before proposing a release

Run the gate. All of it:

```bash
uv run python -m tools.release_check
```

That builds the real zip, extracts it, and checks everything against the
extracted copy — size, native binaries, imports, absolute paths, filesystem
writes, legal moves across clocks from 1 ms up, terminal positions, a smoke
game, and the test suite. `submission.zip` is never authoritative; it is a build
artefact and is not tracked.

## Etiquette

* **Do not push without explicit permission.** Committing locally is fine when
  asked; `git push` needs a direct instruction.
* **Do not rewrite history** or fabricate commits for tidiness.
* **Flag `RECORD THIS`** when something is worth capturing for the project's
  write-up: a surprising benchmark reversal, a real bug with a reproduction, a
  significant Elo result, a failed optimisation that sounded good.
* **Say what is not proven.** "Very likely better, not proven" is an acceptable
  conclusion; overstating one is not.
