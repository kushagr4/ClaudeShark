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

**Method C — public metadata.** The public top-50 scrape carries team names,
colours, ratings and starting positions for 143 games. Where our game appears
there, it settles the question outright.

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

The public scrape contains our round-1 game outright:

```
dd7b41da-4334-4d22-9636-e8a02bce4bad   Rated 1
  White  ClaudeShark v2 (1467)
  Black  The Castle Gambit (1638)
  0-1, checkmate
  start rnbqk2r/p3nppp/1p2p3/2ppP3/P2P4/2P2N2/2P2PPP/R1BQKB1R b KQkq - 0 8
```

Three consequences.

**Our team is `ClaudeShark v2`, rated 1467 at that point, against an opponent
rated 1638.** We were the lower-rated side.

**Round 1 is confirmed by all three methods**: move agreement 86.2% against
46.7%, the clock fingerprint, and now the platform record. We played **White**
and lost.

**The PGN filenames name the opponent, and that convention is now tested rather
than assumed.** `aichessathon-round-1-the-castle-gambit.pgn` was played against
The Castle Gambit, who is rank 46 on the leaderboard. Of the other four
filename tokens, `stonkfish` matches **Minimaxnus / "Stonkfish"** at rank 44,
while `trio-duo`, `baryon` and `prophylaxis` match nothing — consistent with
those opponents sitting outside the top 50, which is the only part of the
ladder the scrape covers.

Only one of our games is in the scrape, because it collects the games of top-50
teams and our other four opponents are either outside the top 50 or, in
Minimaxnus's case, played us after the 10:27 UTC snapshot: their four scraped
games are rounds 1 to 4 and ours is round 5.

## Status

| round | opponent | result | our colour | confidence |
|---|---|---|---|---|
| 1 | The Castle Gambit (1638) | **loss** | **White** | **confirmed** — methods A, B and C agree |
| 2 | trio duo | **win** | **Black** | **confirmed** — A and B agree (B was 29/29) |
| 3 | baryon | **draw** | **Black** | **confirmed** — A and B agree |
| 4 | prophylaxis | 0-1 | leans **Black** | **provisional, method A only** |
| 5 | Minimaxnus / Stonkfish | 0-1 | leans **White** | **provisional, method A only** |

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

## Settled on 2026-09-05: every colour through Round 15, from official metadata

Our public team page (`https://aichessathon.com/team/6532bc56-58ba-48b5-977d-0c039fe3fd7b`,
fetched 2026-09-05 01:20 local with the unauthenticated collector, saved as
`analysis/refresh_2026-09-05/claudeshark_team_page.html` and parsed into
`claudeshark_team_games.json`) lists all fifteen rated games with our colour,
the opponent, the opening and the match id. That is **Method C for every
round**, and it is cross-checked in `corpus/daily/rated_games.txt` against the
seven direct match logs the dashboard offers (`corpus/daily/logs/`) and the PGN
results: fifteen of fifteen consistent.

| round | opponent | our colour | result | sources agreeing |
|---|---|---|---|---|
| 1 | The Castle Gambit | White | loss | team page, log-free; earlier A+B+C |
| 2 | Trio Duo | Black | win | team page; earlier A+B |
| 3 | Baryon | Black | draw | team page, direct log; earlier A+B |
| 4 | Prophylaxis | Black | win | team page, direct log (clock had leaned Black) |
| 5 | Stonkfish | White | loss | team page (clock had leaned White) |
| 6 | e=π=2 | White | win | team page, direct log |
| 7 | Desai | White | draw | team page |
| 8 | 404 Not Found | Black | win | team page, direct log |
| 9 | PawnStorm | White | win | team page |
| 10 | Elbow Grease | Black | loss | team page |
| 11 | mangodogo | White | loss | team page, direct log |
| 12 | Rudra | Black | win | team page |
| 13 | Tobias Carlsen | White | draw | team page |
| 14 | does 4th place get a trophy | Black | win | team page, direct log |
| 15 | Zagreus 5.0 | Black | loss | team page, direct log |

Both provisional clock-fingerprint calls (round 4 Black, round 5 White) were
right, which is mild validation of Method A; it is still never used alone.
The move-fingerprint replay (Method B) was not run for rounds 4–15 because
Method C made it unnecessary. Round 5 is therefore a **submitted-build loss as
White**, and its analysis proceeds on that basis.
