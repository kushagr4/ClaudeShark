# RC-A live deployment, rounds 16–19: mechanisms, and what RC-B does at the same positions

**Date:** 2026-09-05 12:00 (Mac). **Build in play:** RC-A / exact rated-v1
(`3a89bf3e…ff9b`) for all four games, per the user. Sources: Rated 16 from
the public game page; rounds 17–19 from the user's downloaded PGNs
(`aichessathon-round-1{7,8,9}-*.pgn`, sha256 `25c6a2c7…`, `4eef257e…`,
`dc5c0d70…`), copied to `corpus/daily/rca/`, ingested with
`tools.daily.ingest`, annotated with `tools.postmortem.annotate` (Stockfish
18, 200k/1M nodes). Targeted engine-vs-oracle comparisons by the new
`tools/daily/targeted.py` (`targeted_r17.txt`, `targeted_r18_r19.txt`,
`targeted_deeper.txt`), each engine in its own process at a 2,500 ms budget
(the games' own mean spend is about 2 s), oracle at 1M nodes per child.

**These four games are not an Elo test.** Different opponents, different
starts, one game each. They are used for mechanism discovery, failure
classification and a regression check of RC-B on the causal positions. The
controlled 226-game paired screen remains the strength evidence.

| round | colour | result | termination | classification |
|---|---|---|---|---|
| 16 | White | **win** | checkmate | conversion wobble (+529 → +22 after 34.Qxe4), re-won on opponent errors |
| 17 | White | **draw** | threefold | **conversion failure by tactical horizon (perpetual check)**: 47.Re1 |
| 18 | Black | **loss** | checkmate | **tactical horizon failure**: 15…g6 loses a piece to a trap one ply past depth 6 |
| 19 | White | **win** | checkmate | positive control: 8…Bh6? 9.Bxh6, 12.Qxg5+ 13.Qg7#; mate found at depth 3 |

## Round 17 (pwn), draw by repetition — was the draw legitimate?

No. The peak objective evaluation was **+518 for White after 46…Qxd5**
(White to play move 47). The trajectory: +290 at move 32, +351 at 33, then
33.g4 / 34.hxg4 (−117) / 35.Qxa6 (−169) / 39.Re3 (−256) each gave back
ground while Black returned it (38…Nf7 −294, 41…Rb3 −317, 43…Rb3 −325,
45…dxc5 −148, 46…Qxd5 −132). First ≥100 cp RC-A loss: 13.a3 (−114, opening).
Largest loss and the **first winning → drawn transition: 47.Re1, −516**, from
+518 to +2. 47.Qc2 (oracle, +435) or 47.a6 (+300) keep the win. After 47.Re1
Rb4, **48.Qxe5 does enter a forced perpetual** (48…Rg4+ 49.Kf2 Qg2+ 50.Ke3
Rg3+ 51.Qxg3 Qxg3+ and the king cannot escape the g4/g3 checks), but by
then the position is already 0: the oracle's best at move 48 (Qf2, Qf1) is
also 0.0, so 48.Qxe5 cost 17 cp, not the win.

The 42–44 shuffle (42.Rcf1 Rbb8 43.Ra1 Rb3 44.Raf1 Rbb8) repeated a
position once at +280..+325 and 43.Ra1 (−280) allowed a drawing resource
Black missed; the cold engine at 2.5 s plays 43.c5 and 45.c5 (loss 0, the
oracle's move), so the in-game choice came from game state (table, history),
not from the repetition heuristic scoring a draw; the game did not end
there. This is **not** a repetition-policy failure: the repetition was the
consequence of 47.Re1, a move the search scores +354 (RC-A) / +320 at depth
8–9 while the truth is 0. Static is +80; the root is far above static, so the
search *believes* it is winning and cannot see the perpetual that starts five
plies later and needs another six to prove. **Depth 9 does not repair it**
(both builds, `targeted_deeper.txt`). RC-B chooses the same move at the same
score: no repair, no regression. Classification: **CONVERSION FAILURE via
TACTICAL HORIZON (perpetual check)**, the same mechanism as round 7 yesterday.

## Round 18 (sillycats), loss as Black — the highest-value failure

First ≥100 cp RC-A error: **14…Ng4 (−122, −65 → +57)**; the cold engine at
2.5 s plays the oracle's 14…Nd7 (loss 0), so the in-game choice again came
from game state. Largest loss and the **first level → lost transition:
15…g6 (−314, +48 → +362)**. The knight on g4 and the bishop on b6 are both
loose; after 15…g6 16.a4! (a5 traps the bishop, h3 the knight) White wins a
piece. The oracle wants 15…a4 (−29) or 15…f6 (−35).

| 15…, Black to move | move | root | static | depth | oracle after | loss |
|---|---|---|---|---|---|---|
| **RC-A, 2,500 ms** | **g6** | +27 | +86 | **6** | −362 | **+319** |
| **RC-B, 2,500 ms** | **f6** | +29 | +86 | **7** | −28 | **−15** (better than the oracle's first line) |
| RC-A, 8,000 ms | f6 | +29 | +86 | 8 | −28 | −15 |
| either, fixed depth 9 | f6 | +33 | +86 | 9 | −28 | −15 |

So the error is one ply past RC-A's horizon at the game budget, and **RC-B's
speed puts depth 7 inside the same budget and repairs it**. That is the
mechanism the timed screen measured, seen on a real deployment mistake.

After 15…g6 the game is lost (+300..+530 throughout). 17…Kg7 (−108; 17…f6
holds better) is the only later ≥100 loss before the ending; the
19…f6 / 20…Rxf6 / 21…Nxg4 / 22…Bxg4 / 23…Bxd4 sequence is **sound** (losses
0–21, the oracle's own moves) — it is the best practical try in a lost
position. The rook-and-pawns ending was not drawable: at 41…Kxf4 the oracle
reads +605 for White; 40…Bf4 (−91/−116 in the targeted run; 40…Be1 keeps it
at −561) changed nothing. The a-pawn could not be stopped from move 44 on
(+609 before 44…g5; after 45…g4 +891; 46…g3 walks into mate in the counting
race, the alternative being lost anyway). Classification: **TACTICAL HORIZON
FAILURE** at 15…g6, repaired by one more ply.

## Round 19 (trojanknight), win — positive control

8…Bh6?? 9.Bxh6 (loss 0) and after 11…b6?? 12.Qxg5+ Kh8 13.Qg7#. Both builds
find 12.Qxg5+ at depth 3 with a mate score (+29997) and the same 4,301
nodes; at 11.Qd2 both are within 1 cp of the oracle. No protocol or search
anomaly; RC-B identical.

## RC-B regression check on the causal live positions (the point of this file)

| position | RC-A | RC-B | oracle | verdict |
|---|---|---|---|---|
| R17 39.Re3 | Re3 (−291) | Re3 (−291) | Rcf1 | identical, both wrong |
| R17 42–46 | 4 of 5 at the oracle's move | identical | | identical |
| R17 47.Re1 | Re1 (−440) | Re1 (−440) | Qc2 | identical, both wrong; not fixed by depth 9 |
| R17 48.Qxe5 | Qxe5 (−17) | Qxe5 (−17) | Qf2 (0) | identical; already drawn |
| R18 14…Ng4 | Nd7 (0) | Nd7 (0) | Nd7 | identical, correct cold |
| **R18 15…g6** | **g6 (+319 loss)** | **f6 (−15)** | a4 / f6 | **RC-B repairs the decisive error** |
| R18 17…Kg7 | Kg7 (−107) | Kg7 (−107) | f6 | identical |
| R18 19…f6, 21…Nxg4 | oracle's moves | identical | | identical, sound |
| R18 40…Bf4 | Bf4 (−116) | Bf4 (−116) | Be1 | identical; lost either way |
| R19 11.Qd2, 12.Qxg5+ | oracle-equal, mate | identical | | identical |

RC-B is identical to RC-A at 15 of 16 positions and oracle-better at the
one where it differs. No regression; one repair of a real losing decision.
No code was changed because of these games.
