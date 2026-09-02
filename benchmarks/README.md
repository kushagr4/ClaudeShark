# Benchmark records

Every result that a decision was based on, with the command that produced it.

```
benchmarks/
  README.md      this file: the recording rules
  historical/    results from before this directory existed
  current/       results recorded with their exact command and conditions
```

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

Date, candidate and opponent version, git commit, exact command, FEN set, game
count, time control, W/D/L, score, Elo with interval, crashes, illegal moves,
timeouts, average depth, NPS, and any caveat that would change how the number
should be read.
