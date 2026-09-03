# Move quality: selfplay_positions_v1 at depth 6

Engine: champions\v0_5_2_correctness, depth 6. Suite: corpus\selfplay_positions_v1.jsonl (selfplay_positions v1, hash `d3fb0a92c94191eb`, 318 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 318 | 42% | 77% | 0 | 29 | 98 | 146 | 10% | 2.5% | 0.032 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 215 | 46% | 85% | 0 | 25 | 58 | 143 | 7% | 2.8% | 0.021 |
| middlegame | 101 | 35% | 60% | 9 | 39 | 112 | 146 | 15% | 2.0% | 0.054 |
| opening | 2 | 0% | 50% | 72 | 72 | 123 | 123 | 50% | 0.0% | 0.102 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| opposite_side_castling | 10 | 30% | 30% | 72 | 74 | 146 | 170 | 50% | 0.0% | 0.100 |
| complex_ending | 9 | 22% | 78% | 5 | 71 | 110 | 8703 | 22% | 11.1% | 0.039 |
| connected_passers | 31 | 39% | 71% | 0 | 68 | 215 | 343 | 23% | 9.7% | 0.035 |
| protected_passer | 26 | 38% | 62% | 5 | 60 | 143 | 320 | 27% | 7.7% | 0.043 |
| isolated_queen_pawn | 9 | 44% | 67% | 0 | 56 | 44 | 405 | 11% | 11.1% | 0.113 |
| queenside_majority | 46 | 50% | 72% | 0 | 52 | 138 | 343 | 17% | 6.5% | 0.027 |
| queenless_middlegame | 16 | 38% | 62% | 6 | 51 | 146 | 146 | 25% | 6.2% | 0.092 |
| bishop_pair | 28 | 43% | 71% | 2 | 47 | 137 | 320 | 18% | 7.1% | 0.054 |
| space_advantage | 25 | 40% | 68% | 2 | 45 | 182 | 215 | 16% | 4.0% | 0.030 |
| advanced_passer | 54 | 41% | 78% | 0 | 43 | 138 | 182 | 17% | 5.6% | 0.014 |
| open_centre | 45 | 38% | 60% | 5 | 40 | 123 | 166 | 16% | 2.2% | 0.052 |
| same_side_castling | 77 | 31% | 61% | 9 | 40 | 112 | 138 | 13% | 2.6% | 0.058 |
| weak_colour_complex | 36 | 36% | 64% | 4 | 40 | 138 | 146 | 19% | 0.0% | 0.019 |
| minor_piece_ending | 35 | 40% | 83% | 0 | 39 | 174 | 246 | 11% | 5.7% | 0.038 |
| rook_on_semi_open_file | 81 | 41% | 73% | 0 | 37 | 112 | 182 | 12% | 3.7% | 0.049 |
| king_attack | 8 | 38% | 50% | 26 | 36 | 50 | 146 | 12% | 0.0% | 0.001 |
| doubled_pawns | 60 | 47% | 68% | 0 | 36 | 137 | 160 | 17% | 1.7% | 0.036 |
| passed_pawn | 150 | 43% | 77% | 0 | 36 | 120 | 182 | 13% | 4.0% | 0.031 |
| bad_bishop | 37 | 41% | 73% | 5 | 34 | 105 | 138 | 16% | 0.0% | 0.033 |
| knight_outpost | 20 | 30% | 60% | 4 | 32 | 105 | 110 | 15% | 0.0% | 0.073 |
| semi_open_file | 263 | 44% | 76% | 0 | 32 | 105 | 170 | 11% | 3.0% | 0.031 |
| backward_pawn | 101 | 41% | 72% | 0 | 32 | 95 | 166 | 9% | 3.0% | 0.052 |
| hanging_piece | 51 | 57% | 75% | 0 | 31 | 47 | 112 | 6% | 3.9% | 0.051 |
| material_imbalance | 154 | 44% | 77% | 0 | 31 | 98 | 166 | 10% | 3.2% | 0.023 |
| isolated_pawn | 221 | 46% | 78% | 0 | 30 | 105 | 166 | 11% | 2.3% | 0.025 |
| unusual_king_placement | 12 | 42% | 58% | 4 | 28 | 64 | 64 | 8% | 0.0% | 0.000 |
| open_file | 277 | 43% | 80% | 0 | 28 | 98 | 160 | 10% | 2.5% | 0.026 |
| opposite_coloured_bishops | 48 | 33% | 75% | 2 | 27 | 89 | 143 | 10% | 0.0% | 0.023 |
| rook_ending | 57 | 42% | 86% | 0 | 26 | 34 | 160 | 7% | 3.5% | 0.018 |
| exposed_king | 20 | 60% | 65% | 0 | 26 | 64 | 112 | 10% | 0.0% | 0.003 |
| rook_on_open_file | 161 | 44% | 80% | 0 | 25 | 98 | 143 | 9% | 1.2% | 0.027 |
| closed_centre | 15 | 27% | 60% | 6 | 24 | 95 | 95 | 7% | 0.0% | 0.055 |
| exchange_imbalance | 28 | 43% | 75% | 0 | 19 | 40 | 122 | 7% | 0.0% | 0.001 |
| locked_pawn_chain | 22 | 41% | 77% | 2 | 16 | 51 | 78 | 5% | 0.0% | 0.025 |
| rook_and_minor_ending | 106 | 52% | 86% | 0 | 13 | 37 | 98 | 4% | 0.0% | 0.017 |
| in_check | 29 | 52% | 86% | 0 | 8 | 26 | 50 | 0% | 0.0% | 0.012 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| selfplay | 318 | 42% | 77% | 0 | 29 | 98 | 146 | 10% | 2.5% | 0.032 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| sp-058 | 8703 | h2g3 | h7h8q | -1167 | selfplay | advanced_passer, complex_ending, connected_passers, isolated_pawn, material_imbalance, passed_pawn, queenside_majority | `8/kp5P/3P2n1/8/8/8/6PK/3q4 w - - 1 59` |
| sp-120 | 633 | b5d6 | e5e6 | -113 | selfplay | backward_pawn, material_imbalance, minor_piece_ending | `8/8/6p1/1n2kpP1/7P/4BK2/5P2/8 b - - 0 46` |
| sp-158 | 572 | a4h4 | a4a8 | -78 | selfplay | advanced_passer, hanging_piece, isolated_pawn, passed_pawn, queenside_majority, rook_ending, rook_on_semi_open_file | `8/5K2/8/1k5p/R7/6P1/p4P2/r7 w - - 7 53` |
| sp-022 | 408 | a7d7 | e5f4 | -93 | selfplay | isolated_pawn, passed_pawn, rook_ending, rook_on_open_file | `8/R5p1/6k1/4K3/8/8/8/2r5 w - - 8 56` |
| sp-222 | 405 | b2f2 | b2c3 | 57 | selfplay | bishop_pair, connected_passers, hanging_piece, isolated_pawn, isolated_queen_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `4r1k1/ppp2ppp/8/8/3P1Bn1/1BR2N2/bq3PPP/3Q2K1 b - - 0 23` |
| sp-062 | 343 | d2e3 | c4c5 | -256 | selfplay | advanced_passer, connected_passers, isolated_pawn, passed_pawn, protected_passer, queen_ending, queenside_majority, space_advantage | `8/6pk/7p/8/2PKp1q1/3p4/3Q4/8 w - - 2 60` |
| sp-005 | 320 | d4e3 | e1a1 | 63 | selfplay | backward_pawn, bishop_pair, doubled_pawns, material_imbalance, passed_pawn, protected_passer, queenless_middlegame, rook_on_semi_open_file, same_side_castling | `3rr3/2p2kp1/1p1p1p1p/p4P2/b1PBP3/1nPP3P/2B2RP1/4R1K1 w - - 6 37` |
| sp-182 | 302 | e6e5 | b5c7 | -107 | selfplay | backward_pawn, material_imbalance, minor_piece_ending | `8/8/4k1p1/1nB2pP1/7P/5K2/5P2/8 b - - 2 47` |
| sp-090 | 246 | e7f7 | e7d7 | -253 | selfplay | backward_pawn, isolated_pawn, material_imbalance, minor_piece_ending | `8/2p1k3/1p1p4/p2P1K2/P1PB4/8/8/8 b - - 12 65` |
| sp-215 | 215 | h4h3 | g4g3 | 255 | selfplay | backward_pawn, bad_bishop, connected_passers, isolated_pawn, opposite_coloured_bishops, passed_pawn, rook_and_minor_ending, rook_on_open_file, space_advantage, weak_colour_complex | `8/8/p1p1k3/P2b4/1P1Bp1pp/4Pr2/1R6/6K1 b - - 5 56` |
| sp-094 | 212 | g2g3 | f2f3 | -138 | selfplay | bad_bishop, doubled_pawns, isolated_pawn, opposite_coloured_bishops, queenside_majority, rook_on_semi_open_file, same_side_castling, weak_colour_complex | `r3r1k1/1p3pp1/p1bBp1q1/4P3/2Q5/4p3/1P3PPP/R3R1K1 w - - 0 25` |
| sp-290 | 182 | h6h5 | a1c1 | -280 | selfplay | advanced_passer, isolated_pawn, passed_pawn, rook_ending, rook_on_open_file, rook_on_semi_open_file, space_advantage | `8/5pp1/2P1p1kp/PR6/7P/6P1/5PK1/r7 b - - 0 48` |
| sp-223 | 174 | e6d5 | e6f7 | -110 | selfplay | isolated_pawn, material_imbalance, minor_piece_ending, passed_pawn | `8/8/4k3/5p2/1n1B3P/5K2/5P2/8 b - - 1 47` |
| sp-067 | 170 | e8d8 | e8a4 | 109 | selfplay | connected_passers, doubled_pawns, exposed_king, isolated_pawn, material_imbalance, open_centre, opposite_side_castling, passed_pawn, rook_on_open_file | `4Q3/kp2n3/1p6/3n2q1/8/2P5/PP4PP/5R1K w - - 6 38` |
| sp-108 | 166 | f1e1 | a3a4 | 154 | selfplay | backward_pawn, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `2n1r1k1/3Q2p1/3p2qp/2p5/4PB2/P1P4P/6P1/5RK1 w - - 1 42` |
| sp-016 | 160 | f6d6 | d4d5 | 98 | selfplay | connected_passers, doubled_pawns, isolated_pawn, passed_pawn, protected_passer, rook_ending, rook_on_open_file | `8/8/5R2/1k1p1P1p/3KpP1P/8/r5P1/8 w - - 5 55` |
| sp-039 | 146 | b8c8 | f4g5 | 106 | selfplay | backward_pawn, bishop_pair, isolated_pawn, king_attack, knight_outpost, material_imbalance, opposite_side_castling, passed_pawn, queenless_middlegame, rook_on_open_file, unusual_king_placement, weak_colour_complex | `1r4k1/5p2/4b1p1/1N2p3/PK2Pb1p/3r1P1P/4R1P1/1R3N2 b - - 4 30` |
| sp-072 | 143 | h2h3 | f3e5 | -3 | selfplay | open_centre, opposite_side_castling, queenless_middlegame, rook_on_open_file | `2krr3/ppp2ppp/8/3Nn3/4n3/5N2/PPP2PPP/3R1RK1 w - - 0 13` |
| sp-307 | 143 | a3f8 | e3d4 | -121 | selfplay | advanced_passer, doubled_pawns, isolated_pawn, opposite_coloured_bishops, passed_pawn, protected_passer, queenside_majority, rook_and_minor_ending, rook_on_open_file, space_advantage | `8/6p1/2b1p1k1/r7/3p2P1/Brp1P1K1/R4PP1/R7 w - - 0 48` |
| sp-207 | 138 | b2b3 | d1c1 | -94 | selfplay | advanced_passer, bad_bishop, doubled_pawns, isolated_pawn, opposite_coloured_bishops, passed_pawn, protected_passer, queenside_majority, rook_on_semi_open_file, same_side_castling, weak_colour_complex | `r2r2k1/1p3pp1/p1bBp1q1/4P3/2p1P3/3p1P2/1P1Q2PP/3RR1K1 w - - 0 25` |
| sp-265 | 137 | a1b2 | d3e3 | -119 | selfplay | bishop_pair, doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `3r2k1/ppq1p1bp/2r1p1p1/8/3PP1B1/3Q3P/P4PP1/BR4K1 w - - 7 21` |
| sp-277 | 123 | c1g5 | f1e1 | 16 | selfplay | king_in_centre, open_centre | `r1bqk2r/ppp2ppp/2n5/2bnp3/2B5/3P1N2/PPP2PPP/RNBQ1RK1 w kq - 0 8` |
| sp-144 | 122 | a4b5 | g1f1 | -431 | selfplay | exchange_imbalance, isolated_pawn, material_imbalance, rook_and_minor_ending, rook_on_open_file | `6k1/5ppp/8/6P1/B4P2/1p1r4/1P6/6K1 w - - 1 47` |
| sp-268 | 120 | f2d4 | e2c1 | -1162 | selfplay | advanced_passer, bishop_pair, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling, weak_colour_complex | `5rk1/5p1p/5Pp1/q7/P3P3/7P/1rpbNQP1/3b1RK1 w - - 0 32` |
| sp-199 | 112 | g7g6 | h8d8 | -62 | selfplay | bad_bishop, doubled_pawns, exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, opposite_side_castling, rook_on_semi_open_file | `rkb4q/1pn3pp/1pnQ4/1B6/8/5P2/PPP3PP/R4RK1 b - - 6 21` |
