# Move quality: search_audit_positions at 3000 ms

Engine: working tree, 3000 ms. Suite: corpus/daily/search_audit_positions.jsonl (search_audit_positions 2026-09-05, hash `None`, 80 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 80 | 40% | 50% | 21 | 152 | 477 | 570 | 45% | 23.8% | 0.182 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| ? | 80 | 40% | 50% | 21 | 152 | 477 | 570 | 45% | 23.8% | 0.182 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| ? | 80 | 40% | 50% | 21 | 152 | 477 | 570 | 45% | 23.8% | 0.182 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| sa-011 | 9252 | b2e5 | h8h7 | 1 | None |  | `4k2r/p1q5/2p2p2/1pQ2Np1/4Pn1p/1B6/PbP3PP/3R3K b - - 1 31` |
| sa-068 | 8868 | h6b6 | h6e3 | -788 | None |  | `8/4kr2/7Q/P1pq1p2/2Rn3P/6P1/1p5K/8 w - - 7 55` |
| sa-057 | 840 | e6f7 | g1h2 | -102 | None |  | `5k2/5n2/1q1pPP2/1p5p/2p3r1/1nP1NRQ1/8/4R1K1 w - - 2 41` |
| sa-042 | 595 | e7d7 | g7g5 | -78 | None |  | `8/p3k1p1/1p2p3/4Pp1p/PK5P/1P4P1/2P5/8 b - - 1 34` |
| sa-014 | 570 | c1c2 | b4b5 | 52 | None |  | `R7/2r4k/5qp1/3p1r1p/1P2pP1P/P1p1P1Q1/6PK/2R5 w - - 0 43` |
| sa-064 | 540 | d4d5 | g1f1 | -51 | None |  | `1R6/8/8/7p/2rP3P/2k1p3/6P1/6K1 w - - 0 69` |
| sa-075 | 487 | g1f1 | a8f8 | -126 | None |  | `R7/P7/8/6p1/7p/6k1/r5P1/6K1 w - - 2 68` |
| sa-008 | 481 | b5c6 | b1d1 | 3 | None |  | `8/8/8/1k2B2R/8/1p1K3P/p5P1/1r6 b - - 1 51` |
| sa-034 | 477 | b5b8 | b3b1 | -66 | None |  | `5rk1/6p1/2r1p2p/1R6/4RN2/PQ3P2/4KP1n/q7 w - - 20 44` |
| sa-071 | 436 | e7d7 | d8c8 | -44 | None |  | `3k4/1p2r1p1/p2R1p1p/P2p1P2/1P1P2P1/2P5/3K4/8 b - - 6 47` |
| sa-015 | 416 | f8d6 | f8c5 | -22 | None |  | `5Bk1/2r5/q4ppQ/2p5/P1bnP2P/1p4P1/6BK/2R5 w - - 3 46` |
| sa-078 | 392 | e3f1 | e3d5 | -61 | None |  | `8/8/1p6/p5k1/P1P5/1P2Nn2/6Kp/8 w - - 1 56` |
| sa-041 | 367 | g3h5 | d2e3 | -141 | None |  | `6k1/5pp1/2pq3p/1p1p1Prn/rP1P4/3B2NK/3QN3/1R6 w - - 8 36` |
| sa-067 | 348 | d4f2 | f8g7 | 91 | None |  | `5k2/3K1p2/5p2/2p5/1p1bB3/pP1P4/P1P5/8 b - - 23 44` |
| sa-069 | 344 | e8e3 | e8e1 | -22 | None |  | `2k1r3/1p1q1p2/p5p1/2P5/PP1p2QP/1R5P/6P1/7K b - - 1 31` |
| sa-056 | 341 | f1g1 | f1e1 | 41 | None |  | `2Rr1k2/1p4p1/q2P3p/4Q1p1/1p6/8/5PPP/5K2 w - - 1 42` |
| sa-077 | 332 | c5b4 | h2g1 | -291 | None |  | `8/8/6k1/2Bp2P1/4bP2/4P2p/6pK/8 w - - 1 44` |
| sa-049 | 320 | b1b3 | c6a8 | 13 | None |  | `r2q4/p1p3kp/2B1P1p1/3p4/3NpPPn/P2b3P/8/1R1Q2K1 w - - 2 30` |
| sa-070 | 317 | a4d4 | f4f3 | 104 | None |  | `8/1p5p/p4k2/P7/R2p1K2/4p2N/2r1P1rP/4R3 w - - 4 46` |
| sa-044 | 297 | f3c3 | e1a1 | -160 | None |  | `2r5/6pk/2pB1p1p/P2p4/3P2P1/1p3RKP/1rb2P2/4R3 w - - 0 42` |
| sa-058 | 297 | e2f3 | e3g4 | 30 | None |  | `3r2r1/5p2/1k1p2p1/2pPp2p/P1R1P1nP/4N3/1P2K1P1/4R3 w - - 2 37` |
| sa-076 | 280 | f5f3 | f5h5 | 37 | None |  | `6k1/5n1p/5P2/1ppP1R2/2p3PN/1nP1r3/2B5/6K1 w - - 1 39` |
| sa-029 | 251 | d5c3 | d8a8 | -132 | None |  | `3r2k1/2p2pp1/2N4p/2Pn4/3P4/6PP/3q1PK1/1Q2R3 b - - 5 30` |
| sa-047 | 250 | d1c1 | g3f1 | -133 | None |  | `4r1k1/5pp1/2pq1n1p/1p1p1P2/1P1P2r1/3B2NK/3QN3/3R4 w - - 4 34` |
| sa-001 | 246 | c3e2 | d2f1 | 69 | None |  | `r3r1k1/5ppp/2pq1n2/1p1p1P1b/1P1P2Pn/2NBP2P/2QN4/1R2R1K1 w - - 1 23` |
