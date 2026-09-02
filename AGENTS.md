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
* **Record raw game outcomes.** `tools/arena.py --jsonl` writes per-game
  records with snapshots, corpus hash, environment and terminations. A console
  aggregate is not a record.
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
