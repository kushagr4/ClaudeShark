# Benchmark records

Every result that a decision was based on, with the command that produced it.

```
benchmarks/
  README.md      this file: the recording rules
  historical/    results from before this directory existed
  current/       results recorded with their exact command and conditions
```

## Corpus versions

Results are only comparable within a corpus version. Every arena record states
the version and hash it ran on.

| version | balanced | sharp | combined hash | note |
|---|---|---|---|---|
| v1 | 24 | 18 | `0c1fd866a32163e5` | **contained an illegal position** (`BALANCED_OPENINGS[19]`, `OPPOSITE_CHECK`) used as a game start in every arena |
| v2 | 24 | 18 | `c269c63bb74391f0` | index 19 replaced; validated by `tests/test_positions.py` |

Ply cap also changed: everything before 2026-09-02 used **200**, the competition
uses **300**, and 300 is now the default. Pass `--ply-cap 200` to reproduce an
older run.

## The rules

**Record the command, not just the number.** A benchmark without its exact
invocation is an anecdote. Every file in `current/` starts with the command that
produced it.

**Never edit a recorded result.** If a run was wrong, add a new record saying so
and why. `historical/` in particular is a transcription of results that were
produced before this structure existed; it says so explicitly rather than
pretending logs were kept.

**Say what kind of measurement it is.** Three kinds are used here and they are
not interchangeable:

| kind | tool | deterministic? | what it is good for |
|---|---|---|---|
| fixed depth | `tools/bench.py --depth N` | yes | comparing pruning: same nominal work, so node counts are directly comparable |
| fixed time | `tools/bench.py --ms N` | no | what the engine achieves in a given budget; varies with machine load |
| arena | `tools/arena.py` | no | actual playing strength, the only thing that settles a promotion |

**Depth is not strength.** A selective search that reduces the wrong moves
reaches a bigger depth number and plays worse. Any claim about strength needs
`tools/tactics.py`, `tools/movequality.py` or an arena behind it.

**Match the arena's per-move budget to the competition's.** The competition
clock is 120 s + 0.5 s. A fast local control produces a per-move budget an order
of magnitude smaller, and features that need depth to pay measure as neutral or
negative there. This has already produced one reversed result; see
`historical/2026-09-02-v0.2-time-control-lesson.md`.

## What to record for an arena run

Use `--jsonl`. It writes all of this automatically: match id, timestamp, git
commit, a content hash of each agent directory, corpus version and hash, clock,
increment, ply cap, worker count, the effective and stripped `CS_*` environment,
platform — then one line per game with the starting FEN and cluster, colours,
result, termination, ply count, final FEN, duration and failure flag, and a
closing summary with both intervals.

Add any caveat that would change how the number should be read.

**Report both intervals, labelled.** The naive game-level CI treats every game
as independent, which they are not: each starting position is played twice and
the corpus is cycled, so a 400-game match is ~24 clusters. The paired bootstrap
over positions is the honest one. Do not quote the naive figure alone.
