# Rated games 1–15: what the submitted build actually did

**Date:** 2026-09-05. **Subject:** SUBMITTED V2.1 KING-PAWN (`champions/v2_1_kingpawn`,
commit `10c9277`), which played every one of these games. **Oracle:** Stockfish
via `tools.postmortem.annotate` (200k nodes, refined to 1M where a move lost
50 cp or more). **Snapshot answers:** `tools.daily.report` at depth 6 for
rated-v1 and V2.1 on every position we moved in. Stockfish is research
instrumentation only; nothing here ships.

Raw: `corpus/daily/games/rated15.jsonl`, `rated15_annotated.jsonl`,
`corpus/daily/rated15_report.txt/.jsonl`, `corpus/daily/rated_games.json/.txt`
(the canonical per-game dataset with evidence sources), `corpus/daily/rated_classes.json`.

## 1. Record and identity

Every colour is confirmed from our public team page and cross-checked against
seven direct dashboard logs and the PGN results (fifteen of fifteen
consistent). **7 wins, 3 draws, 5 losses: 8.5/15.** As White 2W 2D 3L, as
Black 5W 1D 2L. Rating on the public board after round 11: 1598, rank 85 of
243 teams; opponents were rated 1467–1782 at the snapshot.

| R | colour | result | opponent | plies | our time used / left | first serious error | classification |
|---|---|---|---|---|---|---|---|
| 1 | W | **L** | The Castle Gambit | 59 | 77 s / 57 s | 22 Nxd4 (−114) | dynamic attack compensation |
| 2 | B | W | Trio Duo | 57 | 77 / 57 | 18 O-O (−157) | positive control |
| 3 | B | **D** | Baryon | 98 | 117 / 28 | 14 Bd7 (−182) | **blind win → repetition**, rook v bishop + pawns |
| 4 | B | W | Prophylaxis | 44 | 60 / 71 | 15 Re8 (−107) | positive control |
| 5 | W | **L** | Stonkfish | 67 | 81 / 56 | 17 bxc3 (−109) | tactical horizon after gradual erosion |
| 6 | W | W | e=π=2 | 104 | 125 / 21 | 19 Qd3 (−123) | positive control (conversion) |
| 7 | W | **D** | Desai | 92 | 103 / 40 | 33 Bb4 (−159) | **perpetual-check horizon from +521** |
| 8 | B | W | 404 Not Found | 35 | 59 / 70 | none | positive control |
| 9 | W | W | PawnStorm | 26 | 46 / 80 | none | positive control |
| 10 | B | **L** | Elbow Grease | 98 | 114 / 30 | 13 Bb7 (−150) | **collapse under a kingside attack, moves 13–18** |
| 11 | W | **L** | mangodogo | 83 | 95 / 45 | 13 a4 (−154) | gradual positional loss, then tactical |
| 12 | B | W | Rudra | 131 | 132 / 21 | 43 e3 (−324) | positive control (rook ending) |
| 13 | W | D | Tobias Carlsen | 31 | 46 / 82 | 10 Nxe5 (−117) | short repetition at −42; not a failure |
| 14 | B | W | does 4th place get a trophy | 99 | 117 / 28 | 16 Rde8 (−124) | positive control (survived −259) |
| 15 | B | **L** | Zagreus 5.0 | 134 | 126 / 27 | **5 d5 (−127)** | **opening error from the start position** |

## 2. The eight non-wins, one at a time

**Round 1 (White, loss).** Analysed in the previous session: the opponent gave
a pawn and then a piece for a sustained attack; the root stayed at +41..+61
while Stockfish read −190..−270 (moves 18–21), and the collapse followed.

**Round 3 (Black, draw).** Two distinct mechanisms, both already on record.
Moves 18–20: static −378 against oracle +438 (dynamic compensation, our own
attack unrecognised). Moves 37–56: rook versus bishop with pawns, Stockfish
+234..+462 throughout, our root +32..+193, and a threefold at **+443**. The
engine shuffled Rd2/Rg2/Rg3 because it believed the position was worth +180.

**Round 5 (White, loss).** +184 at move 12 (Bxa7). Four errors of 65–109 cp
(17 bxc3, 18 g4, 19 Bxe4) eroded it; **23 hxg4 (−338)** opened our own king
and the root still read −10 while Stockfish read −461 after the reply; 25 Rxb7
was mate-in-n. Tactical horizon in a position the engine thought level.

**Round 7 (White, draw).** Queen, two rooks and a bishop against queen, rook
and bishop: +521 by Stockfish at move 33. 33 Bb4 (−159) and 34 Bxa5 (−211)
grabbed pawns and let the queen in; the root scored those moves **+575 and
+606**, higher than the oracle, a rare case of the engine being the optimist.
From move 40 the black queen checked continuously. **48 Ke2 (root +501, oracle
+272 → 0)** walked into a forced perpetual the six-ply search could not see;
at move 50 the engine deviated once (root +134) and then accepted the
repetition at 0. This is a **perpetual-check horizon** failure, not "king
safety": the king was never in danger of being mated, only of being checked
forever.

**Round 10 (Black, loss).** The sharpest single collapse. From +34 at move 13
to −375 at move 18 in five moves (13…Bb7 −150, 16…Qf5 −106, 17…Rfe8 −156,
18…hxg6 −142) under a kingside pawn storm. **Throughout those five moves the
root read +77..+99** while Stockfish went −114, −168, −180, −241, −375. Every
one of those decisions was made with over 100 s on the clock in about 2 s.
This is the defensive mirror of the round-1 and round-3 attack blindness.

**Round 11 (White, loss).** Gradual, then tactical. 13 a4 (−154, root +85 v
oracle −18) after a 5.7 s think; the position drifted to −352 by move 27 while
the root never went below −66; then 31 Nxe4 (−237) and 32 Bd3 (−122) lost to a
queen-and-rook attack and 37 fxg3 allowed mate. The opponent made no error of
100 cp in the whole game. Evaluation blindness preceded every move error: at
moves 16–27 the root was +41..−66 against −169..−354.

**Round 13 (White, draw).** 10 Nxe5 (−117) then a bishop shuffle from −42.
Fifteen moves, 46 s used. Not a failure of the engine; a short draw from a
slightly worse position.

**Round 15 (Black, loss).** The start position has a white knight on b5
hitting c7 and d6. **5…d5 (−127) is the first causal failure**, a move the
fixed-depth snapshot also chooses (root +21 against oracle −23; d6 is best);
7…Qe7+ (−151) follows and the position is −324 by move 8 and −354 by move 10,
with the root at −110, −12 and 0 over those three moves. The 11.2 s think at
move 20 (axb6) produced a move the oracle scores as losing by force. The king
walk from move 25 onward, and the endgame that follows, are consequences of a
position already lost by move 10. Tested hypotheses: opening/search error
**yes** (two errors before move 8); material valuation no (no material was
misjudged); king safety no (the king walk begins at −580); conversion no;
repetition no; endgame evaluation no; time management no (127 s used of 153);
opponent resource no (the opponent made two errors of 100+, both after the
position was decided).

## 3. What recurs

| mechanism | games | points lost against the oracle's read |
|---|---|---|
| **evaluation blind to a dynamic attack** (ours or theirs) | R1, R3 (moves 18–20), R5, R10, R11 | three losses and half of a draw |
| **conversion of a won position** | R3 (blind win → repetition), R7 (perpetual horizon) | two half-points |
| opening error from a sharp curated start | R15 | one loss |

The first row is one mechanism seen from both sides: the same evaluator that
did not believe its own attack in round 3 did not believe the opponent's in
rounds 1, 10 and 11. Depth 8 repaired 1 of 7 round-3 positions in the previous
session; the depth-repair test on this session's key positions is in section
6.

## 4. Cross-game classification of every decision we made

491 positions where we moved and the oracle score was not a mate score.
"Wrong score" means the depth-6 root differs from Stockfish by 200 cp or more.

| class | count | share |
|---|---|---|
| correct move, correct score | 339 | 69% |
| **correct move, wrong score** | **104** | **21%** |
| wrong move (≥100 loss), wrong score | 18 | 4% |
| wrong move, correct score | 30 | 6% |
| blind wins (SF ≥ +300, root < +100) | 4 | R3 ×2, R2, R7 |
| false wins (|SF| ≤ 60, root ≥ +150) | **0** | |

One position in five is played correctly while being scored hundreds of
centipawns wrong. The slope of the root against Stockfish where |SF| ≥ 100 is
**0.84 over 341 positions**, but it is much lower exactly where it matters:
0.36 in round 3, 0.44 in round 1, 0.62 in round 11. Zero false wins across 491
positions is the calibration finding of the previous session confirmed on
deployment data: the engine is not optimistic, it is **blind in both
directions**.

## 5. Was the submitted feature involved?

At the 90 positions where we lost 50 cp or more, **V2.1 king-pawn and
rated-v1 choose different moves at 5** (three in round 15's lost ending, one
each in rounds 1 and 10), and none of those five changed the assessment. The
king-to-pawn term fired materially only in the round-3 and round-12 endings.
The feature that separates the submitted build from rated-v1 was, in the
fifteen rated games, effectively **inert**: every failure above belongs to
rated-v1's evaluator and search equally. Combined with the 226-game result
(section 5 of `V2_ACTIVE_STATE.md`), there is no deployment evidence for it
and fixed-depth evidence against it.

## 6. Does depth repair the key decisions?

`corpus/daily/rated15_key_deeper.txt` — 27 positions from the seven non-wins,
each snapshot at depths 6, 7 and 8, the chosen move scored by the oracle at
2M nodes. A "repair" is a chosen move the oracle rates at least 100 cp better
than the move actually played.

| snapshot | depth 6 | depth 7 | depth 8 |
|---|---|---|---|
| rated-v1 | 2 of 27 | **6 of 27** | **6 of 27** |
| V2.1 king-pawn | 2 | 5 | 6 |
| V2.2a low-material | 2 | 5 | 6 |

The two depth-6 "repairs" are positions the fixed-depth snapshot happens to
play differently from the game (round 3 move 55, round 7 move 44); the game
engine had more time and chose worse, which is search instability, not
strength. Depth 7 repairs round 1 move 17, round 3 move 14, round 7 move 33,
round 10 move 16 (partly), round 11 moves 13 and 27; depth 8 additionally
repairs round 10 move 13, round 15 moves 5 and 20 and round 5 move 25 (the
mate-in-n blunder) while losing round 10 move 16 and round 15 move 10. Neither
depth touches the perpetual at round 7 move 48, the attack blindness at round
3 move 20, round 5 move 23, round 11 move 31 or round 15 move 7: those need a
different evaluator, not a deeper one.

**About one serious error in four is a depth error; the rest are evaluation
errors that depth does not reach.** The three snapshots are almost
interchangeable on these positions, which is the fixed-depth face of section
5: nothing in V2.1 or V2.2a addresses what lost these games.

## 7. Time management

Errors were not made in time trouble. At the first serious error of each game
the clock stood between **45 and 113 s**; the mean think on the 47 moves that
lost 100 cp or more was **2.52 s**, against 2.63 s on the 388 moves that lost
under 50. Every game ended with 21–82 s unused; the five losses ended with
27–57 s unused. The allocator behaves exactly as written (`START_FRACTION =
0.45` declines a new iteration once 45% of a ~5 s soft budget has elapsed), so
the engine spends about half of what it budgets and never approaches the
clock. The direct logs confirm it: slowest think 5.2–11.2 s, fastest 0.0 s,
average 1.9–2.4 s, 20–71 s left at the end.

Search-signal complexity was not available from these logs; the finding is
narrower and does not need it: **no decision in fifteen games was constrained
by the clock, and the search ablation values one ply at hundreds of
centipawns on exactly the positions that lost these games.** That is the case
for V2.4, pre-registered on 2026-09-04 and run in this session.

## 8. RECORD THIS

* **Round 10, moves 13–18.** Show `corpus/daily/rated15_report.txt`, the
  round-10 block: five consecutive Black moves at root +77..+99 while the
  Stockfish column reads −114 → −375. Board:
  `1rbq1rk1/p4pbp/1p1p2p1/n1pPp2P/8/3P2P1/1PPQNPB1/R1B1K2R b KQ - 0 13`
  is the position in which 13…Bb7 was played (White has just pushed h5;
  Stockfish wants Re8). One command:
  `uv run python -m tools.daily.report --games corpus/daily/games/rated15_annotated.jsonl --colours corpus/daily/colours.json --snapshots "rated-v1,V2.1 king-pawn" --out corpus/daily/rated15_report.txt`.
* **Round 7, move 48.** The engine at +501 walks into a perpetual: final
  position `6rk/4R1pp/1B1Q4/3b4/5P2/8/P2R3P/6Kq w - - 24 54`, White a queen
  and a rook up, drawn. Show the last twenty plies of `corpus/daily/round7-desai.pgn`.
* **Round 15, move 5.** The start FEN
  `r1bqkbnr/pp1p1ppp/2n1p3/1N6/4P3/8/PPP2PPP/RNBQKB1R b KQkq - 2 5` and the
  engine's 5…d5 against d6; the whole game was decided before move 10.
* **The cross-game table in section 4**: 104 correct-move/wrong-score
  decisions and zero false wins — the engine plays better than it understands.
