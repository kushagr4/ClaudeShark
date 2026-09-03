# Move quality: selfplay_positions_v1 at depth 6

Engine: champions\v0_6_material_scale, depth 6. Suite: corpus\selfplay_positions_v1.jsonl (selfplay_positions v1, hash `d3fb0a92c94191eb`, 318 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 318 | 44% | 78% | 0 | 31 | 89 | 146 | 9% | 3.1% | 0.030 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 215 | 47% | 86% | 0 | 25 | 49 | 101 | 6% | 3.3% | 0.018 |
| middlegame | 101 | 39% | 60% | 7 | 43 | 128 | 163 | 17% | 3.0% | 0.054 |
| opening | 2 | 0% | 50% | 26 | 26 | 51 | 51 | 0% | 0.0% | 0.060 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| isolated_queen_pawn | 9 | 33% | 56% | 15 | 67 | 76 | 405 | 11% | 11.1% | 0.125 |
| complex_ending | 9 | 22% | 78% | 5 | 65 | 59 | 8703 | 11% | 11.1% | 0.004 |
| king_attack | 8 | 50% | 50% | 18 | 61 | 146 | 230 | 25% | 0.0% | 0.064 |
| connected_passers | 31 | 42% | 74% | 0 | 54 | 215 | 227 | 16% | 6.5% | 0.034 |
| queenside_majority | 46 | 52% | 72% | 0 | 54 | 143 | 319 | 20% | 6.5% | 0.032 |
| exchange_imbalance | 28 | 36% | 64% | 2 | 53 | 137 | 319 | 18% | 7.1% | 0.018 |
| bishop_pair | 28 | 46% | 71% | 0 | 52 | 146 | 320 | 21% | 7.1% | 0.072 |
| protected_passer | 26 | 38% | 58% | 8 | 52 | 138 | 227 | 23% | 3.8% | 0.043 |
| advanced_passer | 54 | 44% | 76% | 0 | 52 | 138 | 572 | 17% | 7.4% | 0.014 |
| same_side_castling | 77 | 30% | 56% | 14 | 50 | 137 | 212 | 18% | 3.9% | 0.064 |
| weak_colour_complex | 36 | 36% | 61% | 6 | 44 | 146 | 212 | 22% | 0.0% | 0.027 |
| exposed_king | 20 | 60% | 60% | 0 | 42 | 112 | 155 | 15% | 5.0% | 0.024 |
| queenless_middlegame | 16 | 56% | 75% | 0 | 40 | 146 | 146 | 19% | 6.2% | 0.061 |
| bad_bishop | 37 | 46% | 70% | 0 | 39 | 112 | 212 | 19% | 0.0% | 0.040 |
| opposite_side_castling | 10 | 60% | 60% | 0 | 39 | 112 | 146 | 30% | 0.0% | 0.046 |
| passed_pawn | 150 | 47% | 77% | 0 | 39 | 105 | 227 | 12% | 4.7% | 0.029 |
| doubled_pawns | 60 | 52% | 72% | 0 | 37 | 138 | 163 | 18% | 1.7% | 0.026 |
| backward_pawn | 101 | 44% | 73% | 0 | 37 | 98 | 215 | 10% | 5.0% | 0.047 |
| rook_on_semi_open_file | 81 | 47% | 74% | 0 | 36 | 112 | 155 | 12% | 3.7% | 0.043 |
| semi_open_file | 263 | 48% | 77% | 0 | 34 | 104 | 212 | 11% | 3.8% | 0.031 |
| material_imbalance | 154 | 45% | 77% | 0 | 34 | 101 | 155 | 10% | 4.5% | 0.027 |
| isolated_pawn | 221 | 49% | 78% | 0 | 33 | 105 | 163 | 11% | 3.2% | 0.024 |
| hanging_piece | 51 | 57% | 75% | 0 | 33 | 98 | 163 | 8% | 3.9% | 0.045 |
| unusual_king_placement | 12 | 50% | 58% | 1 | 32 | 76 | 76 | 8% | 0.0% | 0.000 |
| open_centre | 45 | 47% | 67% | 0 | 31 | 79 | 120 | 9% | 2.2% | 0.035 |
| open_file | 277 | 45% | 81% | 0 | 30 | 89 | 146 | 9% | 3.2% | 0.025 |
| minor_piece_ending | 35 | 46% | 83% | 0 | 29 | 58 | 95 | 6% | 5.7% | 0.038 |
| space_advantage | 25 | 52% | 76% | 0 | 28 | 143 | 163 | 12% | 0.0% | 0.016 |
| opposite_coloured_bishops | 48 | 38% | 77% | 2 | 26 | 89 | 143 | 10% | 0.0% | 0.019 |
| rook_on_open_file | 161 | 47% | 81% | 0 | 25 | 89 | 137 | 9% | 1.9% | 0.026 |
| in_check | 29 | 52% | 86% | 0 | 24 | 26 | 95 | 3% | 3.4% | 0.012 |
| rook_ending | 57 | 46% | 91% | 0 | 23 | 20 | 89 | 5% | 3.5% | 0.018 |
| knight_outpost | 20 | 40% | 75% | 1 | 23 | 95 | 105 | 10% | 0.0% | 0.042 |
| closed_centre | 15 | 27% | 67% | 9 | 21 | 59 | 59 | 0% | 0.0% | 0.035 |
| rook_and_minor_ending | 106 | 51% | 86% | 0 | 17 | 37 | 98 | 5% | 0.9% | 0.014 |
| locked_pawn_chain | 22 | 45% | 82% | 1 | 14 | 51 | 66 | 5% | 0.0% | 0.023 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| selfplay | 318 | 44% | 78% | 0 | 31 | 89 | 146 | 9% | 3.1% | 0.030 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| sp-261 | 9351 | g5h6 | d2f4 | -575 | selfplay | advanced_passer, exchange_imbalance, isolated_pawn, material_imbalance, passed_pawn, rook_and_minor_ending | `7k/8/4p3/4P1K1/8/7p/3B4/7r w - - 0 67` |
| sp-037 | 9260 | e2e1 | e2f2 | -267 | selfplay | advanced_passer, backward_pawn, in_check, isolated_pawn, passed_pawn, pawn_ending | `8/p7/1p6/1P6/P3k3/5p2/4K3/8 w - - 0 49` |
| sp-058 | 8703 | h2g3 | h7h8q | -1733 | selfplay | advanced_passer, complex_ending, connected_passers, isolated_pawn, material_imbalance, passed_pawn, queenside_majority | `8/kp5P/3P2n1/8/8/8/6PK/3q4 w - - 1 59` |
| sp-120 | 698 | b5d4 | e5e6 | -157 | selfplay | backward_pawn, material_imbalance, minor_piece_ending | `8/8/6p1/1n2kpP1/7P/4BK2/5P2/8 b - - 0 46` |
| sp-158 | 572 | a4h4 | a4a8 | -35 | selfplay | advanced_passer, hanging_piece, isolated_pawn, passed_pawn, queenside_majority, rook_ending, rook_on_semi_open_file | `8/5K2/8/1k5p/R7/6P1/p4P2/r7 w - - 7 53` |
| sp-022 | 408 | a7d7 | e5f4 | -136 | selfplay | isolated_pawn, passed_pawn, rook_ending, rook_on_open_file | `8/R5p1/6k1/4K3/8/8/8/2r5 w - - 8 56` |
| sp-222 | 405 | b2f2 | b2c3 | 19 | selfplay | bishop_pair, connected_passers, hanging_piece, isolated_pawn, isolated_queen_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `4r1k1/ppp2ppp/8/8/3P1Bn1/1BR2N2/bq3PPP/3Q2K1 b - - 0 23` |
| sp-005 | 320 | d4e3 | e1a1 | 97 | selfplay | backward_pawn, bishop_pair, doubled_pawns, material_imbalance, passed_pawn, protected_passer, queenless_middlegame, rook_on_semi_open_file, same_side_castling | `3rr3/2p2kp1/1p1p1p1p/p4P2/b1PBP3/1nPP3P/2B2RP1/4R1K1 w - - 6 37` |
| sp-002 | 319 | g5d2 | e8d8 | 276 | selfplay | backward_pawn, exchange_imbalance, exposed_king, isolated_pawn, material_imbalance, queenside_majority, rook_on_open_file, same_side_castling | `4r1k1/5pp1/4p3/p3P1q1/1p1B4/1P3Q1P/2r2PPK/4R3 b - - 2 37` |
| sp-182 | 302 | e6e5 | b5c7 | -151 | selfplay | backward_pawn, material_imbalance, minor_piece_ending | `8/8/4k1p1/1nB2pP1/7P/5K2/5P2/8 b - - 2 47` |
| sp-045 | 230 | e5c6 | f1c1 | -19 | selfplay | bad_bishop, bishop_pair, isolated_pawn, king_attack, material_imbalance, rook_on_open_file, same_side_castling, weak_colour_complex | `2rqr1k1/5ppp/b1p1pb2/p1B1N3/3PQ3/P3P3/5PPP/1R3RK1 w - - 5 22` |
| sp-016 | 227 | f6h6 | d4d5 | 142 | selfplay | connected_passers, doubled_pawns, isolated_pawn, passed_pawn, protected_passer, rook_ending, rook_on_open_file | `8/8/5R2/1k1p1P1p/3KpP1P/8/r5P1/8 w - - 5 55` |
| sp-215 | 215 | h4h3 | g4g3 | 340 | selfplay | backward_pawn, bad_bishop, connected_passers, isolated_pawn, opposite_coloured_bishops, passed_pawn, rook_and_minor_ending, rook_on_open_file, space_advantage, weak_colour_complex | `8/8/p1p1k3/P2b4/1P1Bp1pp/4Pr2/1R6/6K1 b - - 5 56` |
| sp-094 | 212 | g2g3 | f2f3 | -179 | selfplay | bad_bishop, doubled_pawns, isolated_pawn, opposite_coloured_bishops, queenside_majority, rook_on_semi_open_file, same_side_castling, weak_colour_complex | `r3r1k1/1p3pp1/p1bBp1q1/4P3/2Q5/4p3/1P3PPP/R3R1K1 w - - 0 25` |
| sp-118 | 163 | b4c6 | b4d3 | -175 | selfplay | backward_pawn, doubled_pawns, hanging_piece, isolated_pawn, same_side_castling, space_advantage | `r1bq1rk1/1p2bpp1/p3p2p/2P1P3/Pn6/1BP2N2/3B1PPP/1Q2RRK1 b - - 0 18` |
| sp-187 | 155 | e6h6 | e6d6 | -171 | selfplay | doubled_pawns, exchange_imbalance, exposed_king, isolated_pawn, material_imbalance, passed_pawn, queenside_majority, rook_on_semi_open_file, same_side_castling | `4rr2/2p2p1k/2p1q3/p3N1Q1/P2PP2P/8/1P4P1/2R3K1 b - - 2 32` |
| sp-039 | 146 | b8c8 | f4g5 | 87 | selfplay | backward_pawn, bishop_pair, isolated_pawn, king_attack, knight_outpost, material_imbalance, opposite_side_castling, passed_pawn, queenless_middlegame, rook_on_open_file, unusual_king_placement, weak_colour_complex | `1r4k1/5p2/4b1p1/1N2p3/PK2Pb1p/3r1P1P/4R1P1/1R3N2 b - - 4 30` |
| sp-307 | 143 | a3f8 | e3d4 | -121 | selfplay | advanced_passer, doubled_pawns, isolated_pawn, opposite_coloured_bishops, passed_pawn, protected_passer, queenside_majority, rook_and_minor_ending, rook_on_open_file, space_advantage | `8/6p1/2b1p1k1/r7/3p2P1/Brp1P1K1/R4PP1/R7 w - - 0 48` |
| sp-207 | 138 | b2b3 | d1c1 | -139 | selfplay | advanced_passer, bad_bishop, doubled_pawns, isolated_pawn, opposite_coloured_bishops, passed_pawn, protected_passer, queenside_majority, rook_on_semi_open_file, same_side_castling, weak_colour_complex | `r2r2k1/1p3pp1/p1bBp1q1/4P3/2p1P3/3p1P2/1P1Q2PP/3RR1K1 w - - 0 25` |
| sp-265 | 137 | a1b2 | d3e3 | -163 | selfplay | bishop_pair, doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `3r2k1/ppq1p1bp/2r1p1p1/8/3PP1B1/3Q3P/P4PP1/BR4K1 w - - 7 21` |
| sp-108 | 128 | d7f5 | a3a4 | 176 | selfplay | backward_pawn, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `2n1r1k1/3Q2p1/3p2qp/2p5/4PB2/P1P4P/6P1/5RK1 w - - 1 42` |
| sp-144 | 122 | a4b5 | g1f1 | -613 | selfplay | exchange_imbalance, isolated_pawn, material_imbalance, rook_and_minor_ending, rook_on_open_file | `6k1/5ppp/8/6P1/B4P2/1p1r4/1P6/6K1 w - - 1 47` |
| sp-268 | 120 | f2d4 | e2c1 | -1674 | selfplay | advanced_passer, bishop_pair, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling, weak_colour_complex | `5rk1/5p1p/5Pp1/q7/P3P3/7P/1rpbNQP1/3b1RK1 w - - 0 32` |
| sp-199 | 112 | g7g6 | h8d8 | -62 | selfplay | bad_bishop, doubled_pawns, exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, opposite_side_castling, rook_on_semi_open_file | `rkb4q/1pn3pp/1pnQ4/1B6/8/5P2/PPP3PP/R4RK1 b - - 6 21` |
| sp-208 | 112 | c5e5 | c5c1 | 258 | selfplay | doubled_pawns, isolated_pawn, locked_pawn_chain, same_side_castling | `4r1k1/1R3pp1/4p2p/1pq1P2P/p3p1Q1/4P3/1P3PP1/6K1 b - - 5 32` |
