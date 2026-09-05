# Move quality: search_audit_positions at 3000 ms

Engine: working tree, 3000 ms. Suite: corpus/daily/search_audit_positions.jsonl (search_audit_positions 2026-09-05, hash `None`, 80 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 80 | 46% | 57% | 0 | 116 | 344 | 440 | 39% | 16.2% | 0.146 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| ? | 80 | 46% | 57% | 0 | 116 | 344 | 440 | 39% | 16.2% | 0.146 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| ? | 80 | 46% | 57% | 0 | 116 | 344 | 440 | 39% | 16.2% | 0.146 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| sa-068 | 8868 | c4c1 | h6e3 | -782 | None |  | `8/4kr2/7Q/P1pq1p2/2Rn3P/6P1/1p5K/8 w - - 7 55` |
| sa-064 | 540 | d4d5 | g1f1 | -96 | None |  | `1R6/8/8/7p/2rP3P/2k1p3/6P1/6K1 w - - 0 69` |
| sa-042 | 514 | e7d8 | g7g5 | -74 | None |  | `8/p3k1p1/1p2p3/4Pp1p/PK5P/1P4P1/2P5/8 b - - 1 34` |
| sa-008 | 481 | b5c6 | b1d1 | 2 | None |  | `8/8/8/1k2B2R/8/1p1K3P/p5P1/1r6 b - - 1 51` |
| sa-031 | 440 | h2g2 | c3c4 | 242 | None |  | `8/8/8/6KP/5P2/2k5/7r/8 b - - 4 54` |
| sa-071 | 436 | e7d7 | d8c8 | -54 | None |  | `3k4/1p2r1p1/p2R1p1p/P2p1P2/1P1P2P1/2P5/3K4/8 b - - 6 47` |
| sa-015 | 416 | f8d6 | f8c5 | -49 | None |  | `5Bk1/2r5/q4ppQ/2p5/P1bnP2P/1p4P1/6BK/2R5 w - - 3 46` |
| sa-067 | 348 | d4f2 | f8g7 | 89 | None |  | `5k2/3K1p2/5p2/2p5/1p1bB3/pP1P4/P1P5/8 b - - 23 44` |
| sa-069 | 344 | e8e3 | e8e1 | -22 | None |  | `2k1r3/1p1q1p2/p5p1/2P5/PP1p2QP/1R5P/6P1/7K b - - 1 31` |
| sa-077 | 332 | c5b4 | h2g1 | -270 | None |  | `8/8/6k1/2Bp2P1/4bP2/4P2p/6pK/8 w - - 1 44` |
| sa-070 | 317 | a4d4 | f4f3 | 116 | None |  | `8/1p5p/p4k2/P7/R2p1K2/4p2N/2r1P1rP/4R3 w - - 4 46` |
| sa-055 | 301 | e4h4 | c3d2 | 131 | None |  | `8/8/8/3P3p/4r2P/2k1p3/6P1/1R4K1 b - - 2 70` |
| sa-023 | 300 | e7f8 | g7g5 | -84 | None |  | `8/p3k1p1/4p3/1p2Pp1p/1P1K3P/P5P1/2P5/8 b - - 1 34` |
| sa-044 | 297 | f3c3 | e1a1 | -160 | None |  | `2r5/6pk/2pB1p1p/P2p4/3P2P1/1p3RKP/1rb2P2/4R3 w - - 0 42` |
| sa-058 | 297 | e2f3 | e3g4 | 27 | None |  | `3r2r1/5p2/1k1p2p1/2pPp2p/P1R1P1nP/4N3/1P2K1P1/4R3 w - - 2 37` |
| sa-004 | 281 | b6a6 | d8c8 | -37 | None |  | `2Rr1k2/1p4p1/1q1P3p/4Q1p1/1p6/8/5PPP/5K2 b - - 0 41` |
| sa-076 | 280 | f5f3 | f5h5 | 30 | None |  | `6k1/5n1p/5P2/1ppP1R2/2p3PN/1nP1r3/2B5/6K1 w - - 1 39` |
| sa-029 | 251 | d5c3 | d8a8 | -132 | None |  | `3r2k1/2p2pp1/2N4p/2Pn4/3P4/6PP/3q1PK1/1Q2R3 b - - 5 30` |
| sa-047 | 250 | d1c1 | g3f1 | -133 | None |  | `4r1k1/5pp1/2pq1n1p/1p1p1P2/1P1P2r1/3B2NK/3QN3/3R4 w - - 4 34` |
| sa-001 | 246 | c3e2 | d2f1 | 28 | None |  | `r3r1k1/5ppp/2pq1n2/1p1p1P1b/1P1P2Pn/2NBP2P/2QN4/1R2R1K1 w - - 1 23` |
| sa-040 | 246 | h2d2 | h2g2 | -604 | None |  | `8/5k2/2p4P/5r1r/8/8/7R/4K3 w - - 1 64` |
| sa-072 | 230 | b5d6 | f3e1 | -19 | None |  | `8/3kb2p/2n2pp1/1NP1p3/1PKpP3/5N1P/r4PP1/1R6 w - - 6 30` |
| sa-060 | 229 | b2b4 | a8e8 | -5 | None |  | `R7/2r4k/1q4p1/3p1r1p/4pP1P/P1p1P1Q1/1P4PK/1R6 w - - 0 42` |
| sa-045 | 225 | c8c7 | g4c4 | -76 | None |  | `2k1r3/8/1p1R2pp/p1pP4/P1P3r1/4P3/1P1K2P1/4R3 b - - 0 45` |
| sa-006 | 211 | e4d4 | e4e5 | 132 | None |  | `r5k1/ppp2ppp/6q1/3b4/4r3/P1B1PQ2/1P3PPP/R4RK1 b - - 4 17` |
