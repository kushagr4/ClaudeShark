# Move quality: search_audit_positions at 3000 ms

Engine: working tree, 3000 ms. Suite: corpus/daily/search_audit_positions.jsonl (search_audit_positions 2026-09-05, hash `None`, 80 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 80 | 45% | 54% | 0 | 138 | 436 | 570 | 41% | 22.5% | 0.174 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| ? | 80 | 45% | 54% | 0 | 138 | 436 | 570 | 41% | 22.5% | 0.174 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| ? | 80 | 45% | 54% | 0 | 138 | 436 | 570 | 41% | 22.5% | 0.174 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| sa-011 | 9252 | b2e5 | h8h7 | 1 | None |  | `4k2r/p1q5/2p2p2/1pQ2Np1/4Pn1p/1B6/PbP3PP/3R3K b - - 1 31` |
| sa-068 | 8868 | c4c1 | h6e3 | -788 | None |  | `8/4kr2/7Q/P1pq1p2/2Rn3P/6P1/1p5K/8 w - - 7 55` |
| sa-057 | 840 | e6f7 | g1h2 | -95 | None |  | `5k2/5n2/1q1pPP2/1p5p/2p3r1/1nP1NRQ1/8/4R1K1 w - - 2 41` |
| sa-042 | 595 | e7d7 | g7g5 | -74 | None |  | `8/p3k1p1/1p2p3/4Pp1p/PK5P/1P4P1/2P5/8 b - - 1 34` |
| sa-014 | 570 | c1c2 | b4b5 | 31 | None |  | `R7/2r4k/5qp1/3p1r1p/1P2pP1P/P1p1P1Q1/6PK/2R5 w - - 0 43` |
| sa-064 | 540 | d4d5 | g1f1 | -49 | None |  | `1R6/8/8/7p/2rP3P/2k1p3/6P1/6K1 w - - 0 69` |
| sa-008 | 481 | b5c6 | b1d1 | 3 | None |  | `8/8/8/1k2B2R/8/1p1K3P/p5P1/1r6 b - - 1 51` |
| sa-031 | 440 | h2g2 | c3c4 | 242 | None |  | `8/8/8/6KP/5P2/2k5/7r/8 b - - 4 54` |
| sa-071 | 436 | e7d7 | d8c8 | -45 | None |  | `3k4/1p2r1p1/p2R1p1p/P2p1P2/1P1P2P1/2P5/3K4/8 b - - 6 47` |
| sa-002 | 410 | f5g6 | f5e5 | -107 | None |  | `8/8/1N6/p4K2/P7/1kn5/8/8 w - - 5 61` |
| sa-041 | 367 | g3h5 | d2e3 | -147 | None |  | `6k1/5pp1/2pq3p/1p1p1Prn/rP1P4/3B2NK/3QN3/1R6 w - - 8 36` |
| sa-067 | 348 | d4f2 | f8g7 | 91 | None |  | `5k2/3K1p2/5p2/2p5/1p1bB3/pP1P4/P1P5/8 b - - 23 44` |
| sa-069 | 344 | e8e3 | e8e1 | -22 | None |  | `2k1r3/1p1q1p2/p5p1/2P5/PP1p2QP/1R5P/6P1/7K b - - 1 31` |
| sa-077 | 332 | c5b4 | h2g1 | -275 | None |  | `8/8/6k1/2Bp2P1/4bP2/4P2p/6pK/8 w - - 1 44` |
| sa-049 | 320 | b1b3 | c6a8 | 13 | None |  | `r2q4/p1p3kp/2B1P1p1/3p4/3NpPPn/P2b3P/8/1R1Q2K1 w - - 2 30` |
| sa-070 | 317 | a4d4 | f4f3 | 104 | None |  | `8/1p5p/p4k2/P7/R2p1K2/4p2N/2r1P1rP/4R3 w - - 4 46` |
| sa-023 | 304 | a7a6 | g7g5 | -82 | None |  | `8/p3k1p1/4p3/1p2Pp1p/1P1K3P/P5P1/2P5/8 b - - 1 34` |
| sa-055 | 301 | e4h4 | c3d2 | 96 | None |  | `8/8/8/3P3p/4r2P/2k1p3/6P1/1R4K1 b - - 2 70` |
| sa-000 | 297 | a1d1 | g3f3 | 8 | None |  | `r1b3k1/ppp2ppp/6q1/8/6r1/2B1P1Q1/PP3PPP/R4RK1 w - - 2 16` |
| sa-044 | 297 | f3c3 | e1a1 | -160 | None |  | `2r5/6pk/2pB1p1p/P2p4/3P2P1/1p3RKP/1rb2P2/4R3 w - - 0 42` |
| sa-058 | 297 | e2f3 | e3g4 | 30 | None |  | `3r2r1/5p2/1k1p2p1/2pPp2p/P1R1P1nP/4N3/1P2K1P1/4R3 w - - 2 37` |
| sa-029 | 251 | d5c3 | d8a8 | -152 | None |  | `3r2k1/2p2pp1/2N4p/2Pn4/3P4/6PP/3q1PK1/1Q2R3 b - - 5 30` |
| sa-047 | 250 | d1c1 | g3f1 | -133 | None |  | `4r1k1/5pp1/2pq1n1p/1p1p1P2/1P1P2r1/3B2NK/3QN3/3R4 w - - 4 34` |
| sa-040 | 246 | h2d2 | h2g2 | -606 | None |  | `8/5k2/2p4P/5r1r/8/8/7R/4K3 w - - 1 64` |
| sa-072 | 230 | b5d6 | f3e1 | -20 | None |  | `8/3kb2p/2n2pp1/1NP1p3/1PKpP3/5N1P/r4PP1/1R6 w - - 6 30` |
