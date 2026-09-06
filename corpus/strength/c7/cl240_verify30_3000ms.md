# Move quality: competition_like_v1 at 3000 ms

Engine: working tree, 3000 ms. Suite: corpus\competition_like_v1.jsonl (competition_like v1, hash `6a8111f22f9ea393`, 240 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 240 | 40% | 71% | 0 | 29 | 79 | 134 | 7% | 1.7% | 0.048 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 60 | 43% | 87% | 0 | 17 | 32 | 76 | 3% | 1.7% | 0.020 |
| middlegame | 144 | 38% | 62% | 6 | 39 | 102 | 191 | 10% | 2.1% | 0.069 |
| opening | 36 | 44% | 83% | 0 | 12 | 36 | 46 | 0% | 0.0% | 0.011 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| unusual_king_placement | 15 | 13% | 40% | 32 | 61 | 134 | 134 | 20% | 6.7% | 0.108 |
| king_attack | 9 | 44% | 67% | 0 | 49 | 52 | 334 | 11% | 11.1% | 0.065 |
| rook_on_open_file | 91 | 42% | 68% | 0 | 42 | 134 | 195 | 13% | 3.3% | 0.076 |
| queenside_majority | 46 | 46% | 70% | 0 | 42 | 118 | 195 | 13% | 2.2% | 0.082 |
| queenless_middlegame | 41 | 37% | 59% | 16 | 41 | 113 | 191 | 12% | 2.4% | 0.082 |
| exposed_king | 54 | 46% | 63% | 0 | 41 | 102 | 165 | 11% | 1.9% | 0.069 |
| space_advantage | 30 | 37% | 63% | 8 | 40 | 85 | 165 | 7% | 3.3% | 0.050 |
| maroczy_bind | 12 | 25% | 50% | 31 | 39 | 95 | 95 | 8% | 0.0% | 0.069 |
| advanced_passer | 33 | 52% | 76% | 0 | 39 | 79 | 134 | 9% | 6.1% | 0.061 |
| passed_pawn | 98 | 49% | 72% | 0 | 39 | 116 | 225 | 11% | 4.1% | 0.065 |
| hanging_piece | 45 | 42% | 60% | 0 | 38 | 134 | 175 | 13% | 0.0% | 0.082 |
| connected_passers | 26 | 46% | 73% | 0 | 37 | 76 | 134 | 8% | 3.8% | 0.053 |
| material_imbalance | 127 | 43% | 69% | 0 | 37 | 85 | 195 | 9% | 3.1% | 0.064 |
| rook_and_minor_ending | 21 | 48% | 81% | 0 | 36 | 76 | 83 | 5% | 4.8% | 0.037 |
| bad_bishop | 65 | 37% | 71% | 2 | 36 | 74 | 195 | 8% | 3.1% | 0.046 |
| same_side_castling | 92 | 38% | 65% | 2 | 36 | 102 | 165 | 11% | 2.2% | 0.068 |
| opposite_side_castling | 21 | 48% | 76% | 0 | 35 | 62 | 72 | 5% | 4.8% | 0.035 |
| closed_centre | 24 | 29% | 58% | 18 | 34 | 95 | 96 | 4% | 0.0% | 0.043 |
| weak_colour_complex | 47 | 34% | 68% | 4 | 34 | 74 | 165 | 6% | 2.1% | 0.051 |
| rook_on_semi_open_file | 104 | 36% | 65% | 6 | 33 | 84 | 161 | 8% | 1.9% | 0.059 |
| protected_passer | 41 | 44% | 73% | 0 | 32 | 76 | 134 | 7% | 2.4% | 0.048 |
| open_centre | 91 | 45% | 68% | 0 | 32 | 79 | 191 | 9% | 2.2% | 0.057 |
| exchange_imbalance | 18 | 56% | 78% | 0 | 32 | 72 | 83 | 6% | 5.6% | 0.046 |
| open_file | 167 | 43% | 72% | 0 | 32 | 79 | 175 | 9% | 2.4% | 0.054 |
| isolated_pawn | 172 | 38% | 69% | 0 | 31 | 84 | 161 | 9% | 1.7% | 0.054 |
| semi_open_file | 227 | 41% | 71% | 0 | 29 | 79 | 134 | 7% | 1.8% | 0.048 |
| locked_pawn_chain | 31 | 35% | 65% | 2 | 29 | 84 | 95 | 3% | 0.0% | 0.042 |
| backward_pawn | 96 | 35% | 73% | 2 | 25 | 74 | 95 | 3% | 1.0% | 0.033 |
| doubled_pawns | 94 | 46% | 73% | 0 | 25 | 74 | 96 | 5% | 2.1% | 0.039 |
| bishop_pair | 76 | 47% | 70% | 0 | 24 | 78 | 85 | 5% | 0.0% | 0.046 |
| opposite_coloured_bishops | 27 | 41% | 78% | 0 | 23 | 46 | 74 | 4% | 3.7% | 0.026 |
| knight_outpost | 45 | 44% | 71% | 0 | 22 | 95 | 102 | 7% | 0.0% | 0.042 |
| king_in_centre | 48 | 42% | 73% | 1 | 21 | 53 | 74 | 2% | 0.0% | 0.029 |
| carlsbad | 22 | 32% | 77% | 2 | 18 | 44 | 82 | 5% | 0.0% | 0.036 |
| minority_attack | 10 | 40% | 80% | 1 | 15 | 44 | 82 | 0% | 0.0% | 0.031 |
| isolated_queen_pawn | 30 | 40% | 80% | 0 | 12 | 33 | 78 | 0% | 0.0% | 0.012 |
| complex_ending | 10 | 70% | 80% | 0 | 9 | 26 | 52 | 0% | 0.0% | 0.002 |
| minor_piece_ending | 11 | 18% | 91% | 0 | 5 | 11 | 32 | 0% | 0.0% | 0.002 |
| rook_ending | 9 | 67% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| albin | 4 | 25% | 25% | 51 | 150 | 10000 | 10000 | 25% | 25.0% | 0.170 |
| ruy_lopez | 5 | 40% | 40% | 28 | 129 | 484 | 484 | 40% | 20.0% | 0.194 |
| dutch | 6 | 0% | 17% | 64 | 99 | 102 | 334 | 33% | 16.7% | 0.156 |
| vienna | 6 | 0% | 50% | 24 | 98 | 195 | 331 | 33% | 16.7% | 0.169 |
| trompowsky | 5 | 20% | 60% | 19 | 56 | 165 | 165 | 20% | 0.0% | 0.121 |
| scandinavian | 5 | 40% | 80% | 0 | 53 | 243 | 243 | 20% | 0.0% | 0.104 |
| nimzo_indian | 5 | 20% | 60% | 2 | 49 | 161 | 161 | 20% | 0.0% | 0.120 |
| philidor | 5 | 40% | 60% | 11 | 49 | 204 | 204 | 20% | 0.0% | 0.101 |
| london | 5 | 0% | 20% | 57 | 49 | 78 | 78 | 0% | 0.0% | 0.084 |
| centre_game | 4 | 50% | 75% | 2 | 48 | 191 | 191 | 25% | 0.0% | 0.125 |
| modern | 5 | 60% | 80% | 0 | 48 | 225 | 225 | 20% | 0.0% | 0.101 |
| queens_gambit_declined | 6 | 17% | 50% | 22 | 40 | 82 | 113 | 17% | 0.0% | 0.121 |
| italian | 5 | 20% | 60% | 25 | 39 | 95 | 95 | 0% | 0.0% | 0.059 |
| colle | 5 | 20% | 60% | 22 | 33 | 118 | 118 | 20% | 0.0% | 0.084 |
| benoni | 4 | 50% | 50% | 16 | 32 | 96 | 96 | 0% | 0.0% | 0.025 |
| kings_indian | 6 | 50% | 50% | 19 | 26 | 42 | 74 | 0% | 0.0% | 0.018 |
| kings_gambit | 4 | 50% | 75% | 6 | 24 | 83 | 83 | 0% | 0.0% | 0.046 |
| grunfeld | 5 | 80% | 80% | 0 | 23 | 116 | 116 | 20% | 0.0% | 0.073 |
| pirc | 4 | 50% | 75% | 8 | 22 | 72 | 72 | 0% | 0.0% | 0.034 |
| french | 5 | 40% | 80% | 0 | 21 | 85 | 85 | 0% | 0.0% | 0.034 |
| sicilian_closed | 4 | 25% | 75% | 4 | 20 | 74 | 74 | 0% | 0.0% | 0.054 |
| queens_gambit_accepted | 4 | 50% | 75% | 0 | 20 | 79 | 79 | 0% | 0.0% | 0.096 |
| bird | 4 | 25% | 75% | 6 | 18 | 62 | 62 | 0% | 0.0% | 0.009 |
| nimzo_larsen | 4 | 50% | 50% | 16 | 18 | 40 | 40 | 0% | 0.0% | 0.023 |
| old_indian | 4 | 50% | 75% | 10 | 18 | 53 | 53 | 0% | 0.0% | 0.008 |
| sicilian_alapin | 5 | 40% | 80% | 1 | 15 | 52 | 52 | 0% | 0.0% | 0.003 |
| bogo_indian | 5 | 20% | 80% | 0 | 14 | 44 | 44 | 0% | 0.0% | 0.003 |
| smith_morra | 4 | 25% | 50% | 13 | 14 | 28 | 28 | 0% | 0.0% | 0.009 |
| owens | 5 | 40% | 80% | 0 | 13 | 50 | 50 | 0% | 0.0% | 0.005 |
| caro_kann | 5 | 40% | 80% | 0 | 13 | 47 | 47 | 0% | 0.0% | 0.014 |
| queens_indian | 5 | 20% | 80% | 8 | 12 | 39 | 39 | 0% | 0.0% | 0.017 |
| four_knights | 5 | 40% | 80% | 11 | 12 | 37 | 37 | 0% | 0.0% | 0.003 |
| benko | 4 | 50% | 75% | 1 | 12 | 46 | 46 | 0% | 0.0% | 0.011 |
| catalan | 6 | 33% | 83% | 4 | 12 | 19 | 46 | 0% | 0.0% | 0.006 |
| chigorin | 4 | 0% | 75% | 0 | 12 | 46 | 46 | 0% | 0.0% | 0.005 |
| other | 5 | 40% | 80% | 12 | 11 | 26 | 26 | 0% | 0.0% | 0.003 |
| torre | 5 | 60% | 80% | 0 | 9 | 41 | 41 | 0% | 0.0% | 0.002 |
| petrov | 4 | 75% | 75% | 0 | 8 | 33 | 33 | 0% | 0.0% | 0.002 |
| reti | 5 | 20% | 80% | 0 | 8 | 29 | 29 | 0% | 0.0% | 0.003 |
| bishops_opening | 5 | 60% | 80% | 0 | 7 | 36 | 36 | 0% | 0.0% | 0.007 |
| semi_slav | 7 | 43% | 86% | 2 | 7 | 9 | 30 | 0% | 0.0% | 0.004 |
| slav | 5 | 40% | 100% | 0 | 4 | 14 | 14 | 0% | 0.0% | 0.001 |
| scotch | 5 | 80% | 100% | 0 | 4 | 18 | 18 | 0% | 0.0% | 0.000 |
| english | 5 | 60% | 100% | 0 | 3 | 11 | 11 | 0% | 0.0% | 0.002 |
| sicilian | 5 | 60% | 100% | 0 | 2 | 12 | 12 | 0% | 0.0% | 0.000 |
| alekhine | 4 | 100% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |
| budapest | 4 | 100% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |
| polish | 5 | 60% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| cl-000 | 10000 | g2f3 | e7e8 | 13 | albin | bad_bishop, isolated_pawn, material_imbalance, passed_pawn, queenside_majority, rook_and_minor_ending, rook_on_open_file, weak_colour_complex | `2k5/1pp1rp1p/8/1NP5/P6n/2N5/1P4bP/2KR4 b - - 0 27` |
| cl-170 | 484 | h3e6 | b2c3 | 113 | ruy_lopez | advanced_passer, backward_pawn, bad_bishop, connected_passers, exposed_king, material_imbalance, opposite_side_castling, passed_pawn, protected_passer, rook_on_open_file, space_advantage | `3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 4 41` |
| cl-097 | 334 | c1b3 | g2g4 | 26 | dutch | advanced_passer, doubled_pawns, isolated_pawn, king_attack, material_imbalance, open_centre, opposite_coloured_bishops, passed_pawn, queenless_middlegame, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `r2r4/4R3/2k1p2p/2p1Bbp1/8/2N1p3/1PP3PP/1KN5 w - - 0 25` |
| cl-201 | 331 | f8d8 | c8d8 | 143 | vienna | doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_semi_open_file, same_side_castling | `2r2rk1/pp3p1p/4P1p1/8/1p2B2R/3Q2PP/2P2PK1/2q5 b - - 1 25` |
| cl-174 | 243 | b7c7 | b7b2 | -124 | scandinavian | bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `Q7/1r3ppk/2q1p2p/5b2/2P1n3/P2B1N2/1R3PPP/2n1B1K1 b - - 3 29` |
| cl-125 | 225 | c4e3 | c4a3 | -31 | modern | backward_pawn, bad_bishop, closed_centre, king_in_centre, locked_pawn_chain, passed_pawn, protected_passer, rook_on_semi_open_file | `r3k2r/4npbp/1qp1p1p1/3pP2P/2nP1P2/PpQ1B3/1P1N2P1/1KR2N1R b kq - 4 20` |
| cl-144 | 204 | c4e4 | c4e2 | 32 | philidor | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, queenside_majority, rook_on_semi_open_file | `r7/pp1kNpQ1/3p4/8/2q1P3/2P3R1/PP3r2/2KR4 b - - 0 24` |
| cl-202 | 195 | e3a7 | e2d4 | -14 | vienna | bad_bishop, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, passed_pawn, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, weak_colour_complex | `3rkb1r/ppp2pp1/2b5/4P2p/4p3/2P1B1P1/PPP1N2P/R3KR2 w Qk - 2 14` |
| cl-087 | 191 | e5e6 | f1e1 | 14 | centre_game | isolated_pawn, open_centre, queenless_middlegame, rook_on_open_file, same_side_castling | `r2r3k/ppp1b1pp/2n2p2/4P3/2B2P2/2P2N2/P1b3PP/R1B2RK1 w - - 0 15` |
| cl-094 | 175 | b5h5 | b5b4 | -64 | danish_gambit | hanging_piece, isolated_pawn, rook_on_open_file, same_side_castling | `r4rk1/pp1b1ppp/2np4/1q6/P2PB3/5N1P/1P1Q1PP1/R3R1K1 b - - 0 19` |
| cl-198 | 165 | a2a1 | b8a7 | -87 | trompowsky | exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, space_advantage, weak_colour_complex | `1k1r4/1p3p1R/5N2/p1pPPQ2/b7/2P5/qP3Pr1/2K4R b - - 1 29` |
| cl-128 | 161 | d3d8 | d3a3 | 100 | nimzo_indian | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `4r1k1/pp3pnn/8/8/4PN2/P2q1P2/5Q1P/6RK b - - 1 32` |
| cl-169 | 134 | g6h6 | g8h7 | -125 | ruy_lopez | advanced_passer, bishop_pair, connected_passers, doubled_pawns, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, protected_passer, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `1r4k1/2b3n1/p1P3r1/5pR1/BP2p3/2P1B2K/8/R7 b - - 1 39` |
| cl-014 | 118 | a3a4 | e5f6 | 20 | colle | isolated_pawn, pawn_ending, queenside_majority | `8/pp2k1p1/4p2p/4Pp2/8/PPK3P1/2P4P/8 w - f6 0 32` |
| cl-110 | 116 | f4g4 | f4f8 | 28 | grunfeld | bad_bishop, hanging_piece, isolated_pawn, maroczy_bind, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `r4rk1/7p/6p1/p1q5/BpPnPR2/8/PQ4PP/2R4K w - - 1 28` |
| cl-158 | 113 | e8c8 | e7d6 | 5 | queens_gambit_declined | backward_pawn, bishop_pair, carlsbad, doubled_pawns, isolated_pawn, knight_outpost, material_imbalance, queenless_middlegame, rook_on_semi_open_file | `r3k2r/1p2bp2/2p3b1/p2pNp1p/N2PnP2/P2BP1P1/1P5P/2R1K1R1 b kq - 1 20` |
| cl-096 | 102 | e7e6 | f5f4 | -40 | dutch | exposed_king, isolated_pawn, knight_outpost, rook_on_open_file, same_side_castling, unusual_king_placement | `4r3/R2bp2p/3p1qpk/2nB1p2/2PN3P/4P1P1/5P2/1Q4K1 b - - 2 32` |
| cl-069 | 96 | b7b5 | f8d7 | 32 | benoni | backward_pawn, closed_centre, doubled_pawns, locked_pawn_chain, material_imbalance, queenless_middlegame | `r3kn1r/1p2bpp1/p2p3p/2pPp3/N1P1P2P/4PN2/PP4P1/R3K2R b KQkq - 0 15` |
| cl-112 | 95 | d1d4 | f3e5 | -36 | italian | backward_pawn, exposed_king, isolated_pawn, knight_outpost, open_centre, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `5rk1/1pp2rp1/3p3p/2q1n3/p3P3/P1P2NQP/1P3RPK/3R4 w - - 2 25` |
| cl-200 | 95 | b5b4 | d8a5 | 22 | trompowsky | backward_pawn, closed_centre, exposed_king, king_in_centre, knight_outpost, locked_pawn_chain, maroczy_bind, queenside_majority, rook_on_semi_open_file, space_advantage | `1rbqk2r/3nbp2/p2p2p1/1ppPp1Pn/4P2P/2N2P2/PP1QBBN1/2KR2R1 b k - 3 24` |
| cl-106 | 85 | f7f8 | a8f8 | -81 | french | backward_pawn, bad_bishop, bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, same_side_castling, space_advantage, weak_colour_complex | `r4Bk1/ppqb1r1p/4p1n1/nP1pPp2/8/2PB1NP1/P2NQP2/R4RK1 b - - 0 20` |
| cl-129 | 84 | d1d2 | f2f4 | 78 | nimzo_indian | backward_pawn, bishop_pair, closed_centre, doubled_pawns, exposed_king, isolated_pawn, locked_pawn_chain, material_imbalance, rook_on_semi_open_file, same_side_castling | `r1bq1r2/p3np1k/1p1p1n1p/2pPp3/2P1P2p/P1PB4/5PP1/1RBQ1RKN w - - 2 16` |
| cl-024 | 83 | g7a7 | g7d7 | -26 | kings_gambit | connected_passers, exchange_imbalance, hanging_piece, isolated_pawn, isolated_queen_pawn, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_and_minor_ending, rook_on_semi_open_file | `5k2/p5R1/2p5/8/1K1PN2P/P2r2P1/2r5/8 w - - 5 42` |
| cl-157 | 82 | f6e4 | a7a5 | -24 | queens_gambit_declined | bishop_pair, carlsbad, material_imbalance, minority_attack, rook_on_semi_open_file, same_side_castling | `r2qr1k1/pp2bpp1/2p2n1p/3p2n1/1P1P4/2NBP1BP/P3QPP1/1R3RK1 b - - 2 16` |
| cl-153 | 79 | c5c7 | d1d4 | -50 | queens_gambit_accepted | advanced_passer, isolated_pawn, material_imbalance, open_centre, passed_pawn, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, weak_colour_complex | `8/1b1r1k2/p2P1n2/1pR4p/2n5/2N2PP1/1P3K2/3R4 w - - 1 34` |
