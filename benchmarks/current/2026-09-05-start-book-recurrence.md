# Public start-FEN recurrence, and whether a book is worth shipping

**Date:** 2026-09-05. Data: the refreshed public collector run at 00:12 UTC
(`analysis/refresh_2026-09-05/top50_games.jsonl`, 447 unique completed games
of the top-50 teams, rounds 1–15, 239 distinct start positions) and our own
fifteen rated starts.

## Measurement

For each round, the fraction of that round's distinct start positions that
had already appeared in an earlier round of the public corpus:

| round | distinct starts | seen earlier | share |
|---|---|---|---|
| 1 | 29 | 0 | 0% |
| 2 | 27 | 3 | 11% |
| 3 | 30 | 4 | 13% |
| 4 | 27 | 4 | 15% |
| 5 | 27 | 10 | 37% |
| 6 | 27 | 13 | 48% |
| 7 | 27 | 10 | 37% |
| 8 | 26 | 13 | 50% |
| 9 | 30 | 15 | 50% |
| 10 | 30 | 12 | 40% |
| 11 | 29 | 19 | 66% |
| 12 | 30 | 19 | 63% |
| 13 | 28 | 15 | 54% |
| **14** | 31 | 27 | **87%** |
| **15** | 31 | 26 | **84%** |

The curated pool is finite and the collector has seen most of it: 239
distinct positions after 447 games, with new ones arriving at a few per
round. Within a round a position is used at most twice (two boards share it).

Our own rounds 6–15: **four of ten** (R7, R10, R12, R13) began from a
position already public before that round; R7's start had appeared in round
4, R10's in round 9, R12's in round 2, R13's in round 5.

## What a legal book could and could not contain

The current docs permit opening books as shipped data but state that "a
database of engine moves or evaluations shipped for lookup at runtime is an
engine, not training data." A book of Stockfish choices for these positions
is therefore **prohibited**. A book is legal only if its moves come from our
own code, i.e. ClaudeShark's own offline search at greater depth than it
reaches in a game, or from non-engine data.

## Value, estimated rather than guessed

* Coverage: if the final Swiss draws from the same pool, roughly 80–90% of
  our thirteen starts would be in a book built from the public corpus.
* Benefit per hit: one move (the first) chosen at, say, depth 11–12 offline
  instead of depth 8–9 in play, plus about 3–5 s of clock. The opponent's
  reply is not ours to choose, so a tree deeper than one or two plies
  buys little. Round 15 is the one rated game decided at the first moves,
  and its first error (5…d5) is repaired by our own engine at depth 8 in the
  depth-repair test, so a book entry would have helped there.
* Cost: a new module, a data file a judge must be able to read, a
  fallback path, and the risk that the Swiss uses a fresh draw.

## Decision

**Measured; not shipped tonight.** The recurrence is material, but the legal
form of the book is our own engine's deeper answers to the first move of
each known start, which is a small gain that a single evening cannot also
test properly under the locked-build Swiss lens. It is the best-supported
*next* idea after the time policy, and it is entirely mechanical:
`tools.corpus.oracle` is not involved; the generator would call
`Searcher.search` with a long fixed budget on each public start and record
the move and score in a plain JSON file with a comment block explaining its
provenance. Pre-registered acceptance: the book move must be stable across
two adjacent depths, and the out-of-book engine must be byte-identical.
