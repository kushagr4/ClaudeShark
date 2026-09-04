# Which side is ours: identifying the submitted build in the rated games

The rated PGNs are anonymised — `White "?"`, `Black "?"` — so every claim about
what ClaudeShark did in a rated game depends on first establishing which colour
it played. Three independent methods are used, and nothing is called confirmed
on one alone.

**Method A — clock fingerprint.** `cs_time.py` opens a soft budget and stops
starting new iterations part way through it, which produces a spend that varies
move to move with occasional long thinks. An opponent on a fixed per-move
budget produces an almost constant spend. This reads the clock, not the moves.

**Method B — move fingerprint.** Replay the game and ask the submitted build at
fixed depth what it would play in every position, feeding it the earlier root
positions first so its repetition record matches.

**Method C — public metadata.** The platform's public game records carry
colours and starting positions. Where our game appears there, it settles the
question outright.

## The clock profiles, measured

| game | side | moves | mean | sd | max | ≤0.1 s | identity |
|---|---|---|---|---|---|---|---|
| round 1 | White | 28 | 2.67 | **1.59** | **7.58** | 2 | **ours** |
| round 1 | Black | 29 | 3.74 | 2.65 | 13.30 | 5 | opponent |
| round 2 | White | 27 | 2.41 | 0.47 | 2.51 | 1 | opponent |
| round 2 | Black | 28 | 2.68 | **1.44** | **6.40** | 3 | **ours** |
| round 3 | White | 48 | 2.08 | 0.52 | 2.95 | 0 | opponent |
| round 3 | Black | 48 | 2.34 | **1.33** | **7.58** | 0 | **ours** |
| round 4 | White | 21 | 3.32 | 0.78 | 4.67 | 0 | — |
| round 4 | Black | 21 | 2.66 | **1.19** | **6.02** | 2 | leans ours |
| round 5 | White | 32 | 2.40 | **1.54** | **6.94** | 4 | leans ours |
| round 5 | Black | 33 | 1.87 | 1.05 | 4.19 | 4 | — |

Established profile over the three settled games: **sd 1.33–1.59, max
6.40–7.58**. The opponents span sd 0.47–2.65 and max 2.51–13.30, which is wide
because the round-1 opponent is itself a variable-time engine — so "inside our
range" is suggestive, never exclusive. That is exactly why a second method is
required.

## Method C settles round 1, and validates the file naming

The platform's public record contains our round-1 game outright:

```
game-001   Rated 1
  White  ClaudeShark v2 (1467)
  Black  Opponent A
  0-1, checkmate
  start rnbqk2r/p3nppp/1p2p3/2ppP3/P2P4/2P2N2/2P2PPP/R1BQKB1R b KQkq - 0 8
```

Three consequences.

**Our team is `ClaudeShark v2`, rated 1467 at that point, against a
higher-rated opponent.** We were the lower-rated side.

**Round 1 is confirmed by all three methods**: move agreement 86.2% against
46.7%, the clock fingerprint, and now the platform record. We played **White**
and lost.

**The downloaded PGN filenames named the opponent, and that convention is now
tested rather than assumed.** The round-1 file was played against Opponent A,
as the platform record confirms; the round-5 filename token matches Opponent E,
while the round-2, round-3 and round-4 tokens matched no public record
available at the time. (The files have since been renamed to `roundN.pgn`.)

Only one of our games was in the public records available at the time; the
round-5 game was played after the 10:27 UTC snapshot.

## Status

| round | opponent | result | our colour | confidence |
|---|---|---|---|---|
| 1 | Opponent A | **loss** | **White** | **confirmed** — methods A, B and C agree |
| 2 | Opponent B | **win** | **Black** | **confirmed** — A and B agree (B was 29/29) |
| 3 | Opponent C | **draw** | **Black** | **confirmed** — A and B agree |
| 4 | Opponent D | 0-1 | leans **Black** | **provisional, method A only** |
| 5 | Opponent E | 0-1 | leans **White** | **provisional, method A only** |

Rounds 4 and 5 wait on the move fingerprint, which is CPU-heavy and queued
behind the 226-game match. Method C cannot reach either of them.

**The round-5 answer changes its meaning entirely.** If we were White it is a
submitted-build **loss** in which Black gave up material for a sustained king
attack and mated on move 41 — the defensive mirror of the round-3 dynamic
compensation failure, and independent support for that mechanism. If we were
Black it is a submitted-build **win** in which the same engine that mis-scored
a winning attack in round 3 executed one correctly here, which would be a
positive control isolating what made round 3 different. No causal conclusion is
drawn until the identity is settled by a second method.
