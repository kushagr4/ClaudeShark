# Move quality: competition_like_v1 at 3000 ms

Engine: working tree, 3000 ms. Suite: corpus\competition_like_v1.jsonl (competition_like v1, hash `6a8111f22f9ea393`, 240 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 240 | 39% | 70% | 0 | 30 | 82 | 116 | 8% | 1.7% | 0.052 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 60 | 42% | 90% | 0 | 16 | 24 | 48 | 3% | 1.7% | 0.020 |
| middlegame | 144 | 38% | 61% | 9 | 40 | 105 | 191 | 11% | 2.1% | 0.073 |
| opening | 36 | 39% | 75% | 12 | 17 | 57 | 61 | 0% | 0.0% | 0.018 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| king_attack | 9 | 44% | 56% | 0 | 59 | 105 | 334 | 22% | 11.1% | 0.097 |
| unusual_king_placement | 15 | 27% | 47% | 31 | 51 | 102 | 102 | 13% | 6.7% | 0.077 |
| exposed_king | 54 | 37% | 56% | 10 | 48 | 116 | 165 | 13% | 1.9% | 0.085 |
| rook_on_open_file | 91 | 38% | 67% | 0 | 44 | 116 | 195 | 14% | 3.3% | 0.083 |
| exchange_imbalance | 18 | 44% | 67% | 6 | 42 | 83 | 111 | 11% | 5.6% | 0.078 |
| passed_pawn | 98 | 43% | 69% | 0 | 42 | 116 | 225 | 13% | 4.1% | 0.076 |
| queenside_majority | 46 | 46% | 70% | 0 | 40 | 105 | 195 | 13% | 2.2% | 0.079 |
| advanced_passer | 33 | 52% | 73% | 0 | 40 | 105 | 116 | 12% | 6.1% | 0.067 |
| material_imbalance | 127 | 41% | 65% | 0 | 40 | 105 | 195 | 11% | 3.1% | 0.071 |
| connected_passers | 26 | 38% | 65% | 0 | 39 | 74 | 111 | 8% | 3.8% | 0.055 |
| same_side_castling | 92 | 35% | 62% | 11 | 39 | 105 | 161 | 12% | 2.2% | 0.076 |
| bad_bishop | 65 | 40% | 69% | 0 | 39 | 99 | 195 | 9% | 3.1% | 0.055 |
| space_advantage | 30 | 50% | 70% | 0 | 38 | 95 | 165 | 10% | 3.3% | 0.057 |
| maroczy_bind | 12 | 33% | 50% | 27 | 38 | 95 | 95 | 8% | 0.0% | 0.075 |
| queenless_middlegame | 41 | 46% | 63% | 3 | 36 | 79 | 191 | 10% | 2.4% | 0.068 |
| rook_on_semi_open_file | 104 | 34% | 63% | 9 | 35 | 95 | 161 | 9% | 1.9% | 0.064 |
| closed_centre | 24 | 33% | 58% | 18 | 34 | 95 | 99 | 4% | 0.0% | 0.049 |
| rook_and_minor_ending | 21 | 52% | 81% | 0 | 34 | 48 | 83 | 5% | 4.8% | 0.034 |
| protected_passer | 41 | 39% | 68% | 0 | 34 | 74 | 105 | 7% | 2.4% | 0.046 |
| weak_colour_complex | 47 | 38% | 70% | 0 | 34 | 74 | 165 | 6% | 2.1% | 0.052 |
| locked_pawn_chain | 31 | 32% | 61% | 2 | 33 | 95 | 99 | 6% | 0.0% | 0.062 |
| open_file | 167 | 41% | 72% | 0 | 33 | 95 | 165 | 10% | 2.4% | 0.058 |
| hanging_piece | 45 | 47% | 67% | 0 | 32 | 112 | 161 | 11% | 0.0% | 0.071 |
| opposite_side_castling | 21 | 62% | 81% | 0 | 32 | 62 | 72 | 5% | 4.8% | 0.032 |
| semi_open_file | 227 | 38% | 70% | 2 | 31 | 82 | 130 | 7% | 1.8% | 0.052 |
| open_centre | 91 | 47% | 71% | 0 | 31 | 78 | 191 | 8% | 2.2% | 0.052 |
| isolated_pawn | 172 | 39% | 71% | 0 | 30 | 83 | 130 | 8% | 1.7% | 0.051 |
| backward_pawn | 96 | 30% | 70% | 8 | 29 | 85 | 105 | 6% | 1.0% | 0.047 |
| knight_outpost | 45 | 38% | 67% | 7 | 27 | 95 | 113 | 9% | 0.0% | 0.053 |
| doubled_pawns | 94 | 46% | 72% | 0 | 26 | 74 | 84 | 5% | 2.1% | 0.040 |
| bishop_pair | 76 | 47% | 68% | 0 | 25 | 74 | 84 | 4% | 0.0% | 0.043 |
| king_in_centre | 48 | 38% | 69% | 12 | 24 | 61 | 82 | 2% | 0.0% | 0.034 |
| opposite_coloured_bishops | 27 | 37% | 81% | 0 | 23 | 46 | 74 | 4% | 3.7% | 0.026 |
| carlsbad | 22 | 27% | 73% | 8 | 20 | 47 | 82 | 5% | 0.0% | 0.038 |
| minority_attack | 10 | 30% | 80% | 7 | 17 | 44 | 82 | 0% | 0.0% | 0.031 |
| complex_ending | 10 | 60% | 80% | 0 | 15 | 26 | 111 | 10% | 0.0% | 0.045 |
| isolated_queen_pawn | 30 | 40% | 80% | 0 | 14 | 33 | 78 | 0% | 0.0% | 0.013 |
| minor_piece_ending | 11 | 18% | 100% | 0 | 3 | 11 | 16 | 0% | 0.0% | 0.002 |
| rook_ending | 9 | 44% | 100% | 0 | 3 | 7 | 19 | 0% | 0.0% | 0.000 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| albin | 4 | 50% | 50% | 28 | 139 | 10000 | 10000 | 25% | 25.0% | 0.157 |
| ruy_lopez | 5 | 60% | 60% | 0 | 106 | 484 | 484 | 20% | 20.0% | 0.103 |
| vienna | 6 | 0% | 50% | 24 | 98 | 195 | 331 | 33% | 16.7% | 0.169 |
| dutch | 6 | 0% | 17% | 50 | 94 | 102 | 334 | 33% | 16.7% | 0.145 |
| philidor | 5 | 20% | 40% | 32 | 66 | 204 | 204 | 20% | 0.0% | 0.126 |
| scandinavian | 5 | 40% | 80% | 14 | 56 | 243 | 243 | 20% | 0.0% | 0.103 |
| trompowsky | 5 | 20% | 60% | 19 | 56 | 165 | 165 | 20% | 0.0% | 0.121 |
| benoni | 4 | 25% | 25% | 46 | 52 | 116 | 116 | 25% | 0.0% | 0.120 |
| nimzo_indian | 5 | 20% | 60% | 2 | 49 | 161 | 161 | 20% | 0.0% | 0.120 |
| london | 5 | 0% | 20% | 57 | 49 | 78 | 78 | 0% | 0.0% | 0.084 |
| centre_game | 4 | 50% | 75% | 2 | 48 | 191 | 191 | 25% | 0.0% | 0.125 |
| modern | 5 | 60% | 80% | 0 | 48 | 225 | 225 | 20% | 0.0% | 0.101 |
| italian | 5 | 20% | 60% | 25 | 39 | 95 | 95 | 0% | 0.0% | 0.059 |
| french | 5 | 20% | 60% | 18 | 35 | 85 | 85 | 0% | 0.0% | 0.062 |
| queens_gambit_declined | 6 | 17% | 67% | 8 | 35 | 82 | 113 | 17% | 0.0% | 0.118 |
| queens_indian | 5 | 20% | 60% | 15 | 34 | 105 | 105 | 20% | 0.0% | 0.079 |
| bishops_opening | 5 | 40% | 60% | 0 | 29 | 111 | 111 | 20% | 0.0% | 0.096 |
| bogo_indian | 5 | 20% | 60% | 0 | 29 | 99 | 99 | 0% | 0.0% | 0.052 |
| grunfeld | 5 | 80% | 80% | 0 | 26 | 130 | 130 | 20% | 0.0% | 0.086 |
| kings_indian | 6 | 50% | 50% | 19 | 26 | 42 | 74 | 0% | 0.0% | 0.018 |
| caro_kann | 5 | 20% | 60% | 16 | 25 | 61 | 61 | 0% | 0.0% | 0.020 |
| kings_gambit | 4 | 50% | 75% | 6 | 24 | 83 | 83 | 0% | 0.0% | 0.046 |
| old_indian | 4 | 25% | 75% | 20 | 23 | 53 | 53 | 0% | 0.0% | 0.009 |
| pirc | 4 | 50% | 75% | 8 | 22 | 72 | 72 | 0% | 0.0% | 0.034 |
| sicilian_closed | 4 | 25% | 75% | 4 | 20 | 74 | 74 | 0% | 0.0% | 0.054 |
| queens_gambit_accepted | 4 | 50% | 75% | 0 | 20 | 79 | 79 | 0% | 0.0% | 0.096 |
| bird | 4 | 25% | 75% | 6 | 18 | 62 | 62 | 0% | 0.0% | 0.009 |
| torre | 5 | 20% | 60% | 7 | 16 | 41 | 41 | 0% | 0.0% | 0.003 |
| colle | 5 | 20% | 60% | 22 | 16 | 27 | 27 | 0% | 0.0% | 0.010 |
| slav | 5 | 40% | 80% | 0 | 15 | 62 | 62 | 0% | 0.0% | 0.024 |
| smith_morra | 4 | 50% | 50% | 13 | 14 | 28 | 28 | 0% | 0.0% | 0.009 |
| owens | 5 | 40% | 80% | 0 | 13 | 50 | 50 | 0% | 0.0% | 0.005 |
| chigorin | 4 | 25% | 75% | 0 | 12 | 46 | 46 | 0% | 0.0% | 0.005 |
| other | 5 | 40% | 80% | 12 | 11 | 26 | 26 | 0% | 0.0% | 0.003 |
| catalan | 6 | 50% | 83% | 0 | 11 | 19 | 46 | 0% | 0.0% | 0.005 |
| nimzo_larsen | 4 | 75% | 75% | 0 | 10 | 40 | 40 | 0% | 0.0% | 0.020 |
| petrov | 4 | 75% | 75% | 0 | 8 | 33 | 33 | 0% | 0.0% | 0.002 |
| sicilian_alapin | 5 | 60% | 100% | 0 | 8 | 21 | 21 | 0% | 0.0% | 0.003 |
| four_knights | 5 | 40% | 100% | 11 | 8 | 16 | 16 | 0% | 0.0% | 0.001 |
| semi_slav | 7 | 43% | 86% | 2 | 7 | 9 | 30 | 0% | 0.0% | 0.004 |
| alekhine | 4 | 50% | 100% | 1 | 6 | 23 | 23 | 0% | 0.0% | 0.003 |
| reti | 5 | 40% | 80% | 0 | 6 | 29 | 29 | 0% | 0.0% | 0.001 |
| budapest | 4 | 75% | 100% | 0 | 4 | 16 | 16 | 0% | 0.0% | 0.004 |
| scotch | 5 | 80% | 100% | 0 | 4 | 18 | 18 | 0% | 0.0% | 0.000 |
| sicilian | 5 | 40% | 100% | 0 | 3 | 8 | 8 | 0% | 0.0% | 0.000 |
| english | 5 | 60% | 100% | 0 | 3 | 11 | 11 | 0% | 0.0% | 0.002 |
| benko | 4 | 75% | 100% | 0 | 0 | 2 | 2 | 0% | 0.0% | 0.000 |
| polish | 5 | 60% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| cl-000 | 10000 | g2f3 | e7e8 | 13 | albin | bad_bishop, isolated_pawn, material_imbalance, passed_pawn, queenside_majority, rook_and_minor_ending, rook_on_open_file, weak_colour_complex | `2k5/1pp1rp1p/8/1NP5/P6n/2N5/1P4bP/2KR4 b - - 0 27` |
| cl-170 | 484 | h3e6 | b2c3 | 113 | ruy_lopez | advanced_passer, backward_pawn, bad_bishop, connected_passers, exposed_king, material_imbalance, opposite_side_castling, passed_pawn, protected_passer, rook_on_open_file, space_advantage | `3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 4 41` |
| cl-097 | 334 | c1b3 | g2g4 | 26 | dutch | advanced_passer, doubled_pawns, isolated_pawn, king_attack, material_imbalance, open_centre, opposite_coloured_bishops, passed_pawn, queenless_middlegame, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `r2r4/4R3/2k1p2p/2p1Bbp1/8/2N1p3/1PP3PP/1KN5 w - - 0 25` |
| cl-201 | 331 | f8d8 | c8d8 | 143 | vienna | doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_semi_open_file, same_side_castling | `2r2rk1/pp3p1p/4P1p1/8/1p2B2R/3Q2PP/2P2PK1/2q5 b - - 1 25` |
| cl-174 | 243 | b7c7 | b7b2 | -115 | scandinavian | bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `Q7/1r3ppk/2q1p2p/5b2/2P1n3/P2B1N2/1R3PPP/2n1B1K1 b - - 3 29` |
| cl-125 | 225 | c4e3 | c4a3 | -24 | modern | backward_pawn, bad_bishop, closed_centre, king_in_centre, locked_pawn_chain, passed_pawn, protected_passer, rook_on_semi_open_file | `r3k2r/4npbp/1qp1p1p1/3pP2P/2nP1P2/PpQ1B3/1P1N2P1/1KR2N1R b kq - 4 20` |
| cl-144 | 204 | c4e4 | c4e2 | 32 | philidor | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, queenside_majority, rook_on_semi_open_file | `r7/pp1kNpQ1/3p4/8/2q1P3/2P3R1/PP3r2/2KR4 b - - 0 24` |
| cl-202 | 195 | e3a7 | e2d4 | -14 | vienna | bad_bishop, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, passed_pawn, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, weak_colour_complex | `3rkb1r/ppp2pp1/2b5/4P2p/4p3/2P1B1P1/PPP1N2P/R3KR2 w Qk - 2 14` |
| cl-087 | 191 | e5e6 | f1e1 | 14 | centre_game | isolated_pawn, open_centre, queenless_middlegame, rook_on_open_file, same_side_castling | `r2r3k/ppp1b1pp/2n2p2/4P3/2B2P2/2P2N2/P1b3PP/R1B2RK1 w - - 0 15` |
| cl-198 | 165 | a2a1 | b8a7 | -87 | trompowsky | exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, space_advantage, weak_colour_complex | `1k1r4/1p3p1R/5N2/p1pPPQ2/b7/2P5/qP3Pr1/2K4R b - - 1 29` |
| cl-128 | 161 | d3d8 | d3a3 | 100 | nimzo_indian | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `4r1k1/pp3pnn/8/8/4PN2/P2q1P2/5Q1P/6RK b - - 1 32` |
| cl-110 | 130 | f4f2 | f4f8 | 19 | grunfeld | bad_bishop, hanging_piece, isolated_pawn, maroczy_bind, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `r4rk1/7p/6p1/p1q5/BpPnPR2/8/PQ4PP/2R4K w - - 1 28` |
| cl-066 | 116 | c8d8 | c8e8 | -88 | benoni | advanced_passer, backward_pawn, exposed_king, knight_outpost, locked_pawn_chain, material_imbalance, passed_pawn, queenside_majority, rook_on_open_file, same_side_castling | `2r3k1/3q3p/3p1P1n/1p1Pr1p1/2p3P1/1nP4P/2B2Q1K/3NRR2 b - - 2 30` |
| cl-158 | 113 | e8c8 | e7d6 | 5 | queens_gambit_declined | backward_pawn, bishop_pair, carlsbad, doubled_pawns, isolated_pawn, knight_outpost, material_imbalance, queenless_middlegame, rook_on_semi_open_file | `r3k2r/1p2bp2/2p3b1/p2pNp1p/N2PnP2/P2BP1P1/1P5P/2R1K1R1 b kq - 1 20` |
| cl-094 | 112 | b5a5 | b5b4 | -55 | danish_gambit | hanging_piece, isolated_pawn, rook_on_open_file, same_side_castling | `r4rk1/pp1b1ppp/2np4/1q6/P2PB3/5N1P/1P1Q1PP1/R3R1K1 b - - 0 19` |
| cl-007 | 111 | g4g6 | d6d5 | -24 | bishops_opening | backward_pawn, complex_ending, connected_passers, doubled_pawns, exchange_imbalance, material_imbalance, passed_pawn, rook_on_semi_open_file | `6k1/1p6/3p4/p1p4r/P2pPBq1/3P4/1PP3PP/5QK1 b - - 4 29` |
| cl-162 | 105 | g1h1 | h2h3 | 17 | queens_indian | advanced_passer, backward_pawn, bad_bishop, king_attack, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, space_advantage | `5rk1/3PQ1pp/1q6/1p6/2p5/2Pp4/3NbPPP/4R1K1 w - - 3 26` |
| cl-096 | 102 | e7e6 | f5f4 | -44 | dutch | exposed_king, isolated_pawn, knight_outpost, rook_on_open_file, same_side_castling, unusual_king_placement | `4r3/R2bp2p/3p1qpk/2nB1p2/2PN3P/4P1P1/5P2/1Q4K1 b - - 2 32` |
| cl-073 | 99 | b6b4 | g1f2 | -35 | bogo_indian | backward_pawn, bad_bishop, closed_centre, exposed_king, isolated_pawn, locked_pawn_chain, passed_pawn, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `1rb5/Rpq2kpp/1Q1p4/2rPp3/4Pp2/3B1P1P/6P1/1R4K1 w - - 7 30` |
| cl-112 | 95 | d1d4 | f3e5 | -26 | italian | backward_pawn, exposed_king, isolated_pawn, knight_outpost, open_centre, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `5rk1/1pp2rp1/3p3p/2q1n3/p3P3/P1P2NQP/1P3RPK/3R4 w - - 2 25` |
| cl-200 | 95 | b5b4 | d8a5 | 22 | trompowsky | backward_pawn, closed_centre, exposed_king, king_in_centre, knight_outpost, locked_pawn_chain, maroczy_bind, queenside_majority, rook_on_semi_open_file, space_advantage | `1rbqk2r/3nbp2/p2p2p1/1ppPp1Pn/4P2P/2N2P2/PP1QBBN1/2KR2R1 b k - 3 24` |
| cl-106 | 85 | f7f8 | a8f8 | -81 | french | backward_pawn, bad_bishop, bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, same_side_castling, space_advantage, weak_colour_complex | `r4Bk1/ppqb1r1p/4p1n1/nP1pPp2/8/2PB1NP1/P2NQP2/R4RK1 b - - 0 20` |
| cl-129 | 84 | d1d2 | f2f4 | 84 | nimzo_indian | backward_pawn, bishop_pair, closed_centre, doubled_pawns, exposed_king, isolated_pawn, locked_pawn_chain, material_imbalance, rook_on_semi_open_file, same_side_castling | `r1bq1r2/p3np1k/1p1p1n1p/2pPp3/2P1P2p/P1PB4/5PP1/1RBQ1RKN w - - 2 16` |
| cl-024 | 83 | g7a7 | g7d7 | -20 | kings_gambit | connected_passers, exchange_imbalance, hanging_piece, isolated_pawn, isolated_queen_pawn, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_and_minor_ending, rook_on_semi_open_file | `5k2/p5R1/2p5/8/1K1PN2P/P2r2P1/2r5/8 w - - 5 42` |
| cl-157 | 82 | f6e4 | a7a5 | -24 | queens_gambit_declined | bishop_pair, carlsbad, material_imbalance, minority_attack, rook_on_semi_open_file, same_side_castling | `r2qr1k1/pp2bpp1/2p2n1p/3p2n1/1P1P4/2NBP1BP/P3QPP1/1R3RK1 b - - 2 16` |
