# Move quality: legacy_v2_calibration at depth 6

Engine: working tree, depth 6. Suite: corpus\legacy_v2_calibration.jsonl (None None, hash `None`, 42 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 42 | 45% | 74% | 0 | 13 | 39 | 41 | 0% | 0.0% | 0.023 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 11 | 55% | 91% | 0 | 6 | 10 | 50 | 0% | 0.0% | 0.000 |
| middlegame | 3 | 33% | 33% | 40 | 41 | 84 | 84 | 0% | 0.0% | 0.053 |
| opening | 28 | 43% | 71% | 8 | 13 | 38 | 39 | 0% | 0.0% | 0.029 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| open_file | 14 | 57% | 86% | 0 | 7 | 39 | 39 | 0% | 0.0% | 0.002 |
| semi_open_file | 17 | 65% | 82% | 0 | 7 | 32 | 38 | 0% | 0.0% | 0.015 |
| king_in_centre | 9 | 56% | 89% | 0 | 6 | 15 | 32 | 0% | 0.0% | 0.019 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| ? | 42 | 45% | 74% | 0 | 13 | 39 | 41 | 0% | 0.0% | 0.023 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| None | 84 | d4e5 | f3e5 | 82 | None | closed_centre, queenless_middlegame | `r3k2r/ppp2ppp/2n2n2/3pp3/3PP3/2N2N2/PPP2PPP/R3K2R w KQkq - 0 9` |
| None | 50 | f1b5 | f1c4 | 384 | None | material_imbalance, rook_and_minor_ending, rook_on_open_file | `r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/2KR1B1R w kq - 0 15` |
| None | 41 | b1c3 | f3g5 | 5 | None |  | `r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4` |
| None | 40 | e4e5 | b3e6 | -67 | None | opposite_side_castling, rook_on_semi_open_file | `r2q1rk1/1b1nbppp/p2ppn2/1p6/3NPP2/1BN1B3/PPPQ2PP/2KR3R w - - 0 13` |
| None | 39 | f1d3 | f3e5 | 25 | None |  | `r2qkb1r/pp2pppp/2n2n2/3p1b2/3P4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 7` |
| None | 39 | c4d5 | c4c5 | 63 | None | same_side_castling | `r1b2rk1/pp1nqppp/2pbpn2/3p4/2PP4/2NBPN2/PPQ2PPP/R1B2RK1 w - - 0 10` |
| None | 38 | b1c3 | c4d5 | -53 | None |  | `r1bqkb1r/pppp1ppp/2n5/4p3/2B1n3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5` |
| None | 33 | e2e3 | d1b3 | 29 | None |  | `rn1qkb1r/pp2pppp/2p2n2/3p1b2/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5` |
| None | 33 | c3d5 | d3d4 | 25 | None |  | `r1bqk2r/ppp1bppp/2np1n2/4p3/2P5/2NPPN2/PP2BPPP/R1BQK2R w KQkq - 0 7` |
| None | 32 | f3g5 | f1b5 | 14 | None | carlsbad, king_in_centre | `r2qk2r/ppp1bppp/2n1bn2/3p4/3P1B2/2N1PN2/PPQ2PPP/R3KB1R w KQkq - 0 9` |
| None | 28 | e5d4 | c6d4 | 79 | None | hanging_piece | `r1bqk2r/pppp1ppp/2n2n2/2b1p3/2BPP3/5N2/PPP2PPP/RNBQK2R b KQkq - 0 5` |
| None | 21 | g1f3 | d2d4 | 54 | None |  | `rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 4` |
| None | 16 | a2a3 | d1a4 | 47 | None |  | `rnbqk2r/ppp2ppp/4pn2/3p4/1bPP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 6` |
| None | 15 | e1c1 | c4d5 | 30 | None | king_in_centre | `r1bqk2r/pp1nbppp/2p1pn2/3p2B1/2PP4/2N1PN2/PPQ2PPP/R3KB1R w KQkq - 0 8` |
| None | 12 | b1c3 | c2c3 | 8 | None |  | `r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6` |
| None | 12 | b1c3 | c2c3 | 30 | None |  | `r1bqkbnr/pp1p1ppp/2n5/2p1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4` |
| None | 11 | e1g1 | b2b3 | 38 | None | king_in_centre | `r1bqk2r/pp1nbppp/2p1pn2/3p4/2PP4/2N1PN2/PPQ1BPPP/R1B1K2R w KQkq - 0 8` |
| None | 10 | e1g1 | a2a4 | 12 | None | opposite_coloured_bishops, rook_and_minor_ending | `r1b1k2r/pppp1ppp/8/8/8/8/PPPP1PPP/R1B1K2R w KQkq - 0 12` |
| None | 5 | c3d5 | a2a4 | 0 | None | backward_pawn, same_side_castling | `r2q1rk1/pp1bbppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP1QPPP/R1B2RK1 w - - 0 10` |
| None | 2 | h2h4 | h2h3 | 73 | None | rook_ending, rook_on_open_file | `8/5ppk/8/8/8/1R6/r4PPP/6K1 w - - 0 38` |
| None | 0 | a2a3 | a2a3 | 16 | None | same_side_castling | `r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9` |
| None | 0 | a2a3 | a2a3 | -55 | None | same_side_castling | `r1bq1rk1/pp3ppp/2n1pn2/2pp4/1b1P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9` |
| None | 0 | d4d5 | d4d5 | 17 | None | king_in_centre | `r1bq1rk1/1pp1npbp/p1np2p1/4p3/2PPP3/2N1BP2/PP1QN1PP/R3KB1R w KQ - 0 10` |
| None | 0 | d4f5 | d4f5 | 168 | None | king_in_centre, open_centre | `r1b1k2r/ppppqppp/2n2n2/2b5/3NP3/2N5/PPP1BPPP/R1BQ1RK1 w kq - 0 8` |
| None | 0 | e1g1 | e1g1 | 33 | None | isolated_pawn, king_in_centre | `rnbq1rk1/pp2ppbp/6p1/2p5/3PP3/2P2N2/P3BPPP/R1BQK2R w KQ - 0 9` |
