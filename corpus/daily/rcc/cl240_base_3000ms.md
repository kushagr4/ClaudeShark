# Move quality: competition_like_v1 at 3000 ms

Engine: working tree, 3000 ms. Suite: corpus/competition_like_v1.jsonl (competition_like v1, hash `6a8111f22f9ea393`, 240 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 240 | 37% | 70% | 0 | 29 | 82 | 130 | 8% | 1.2% | 0.051 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 60 | 37% | 82% | 0 | 13 | 41 | 56 | 3% | 0.0% | 0.021 |
| middlegame | 144 | 35% | 62% | 8 | 40 | 105 | 195 | 12% | 2.1% | 0.073 |
| opening | 36 | 44% | 81% | 0 | 12 | 36 | 55 | 0% | 0.0% | 0.011 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| king_attack | 9 | 44% | 56% | 0 | 59 | 105 | 334 | 22% | 11.1% | 0.097 |
| space_advantage | 30 | 37% | 57% | 6 | 52 | 125 | 251 | 17% | 3.3% | 0.088 |
| unusual_king_placement | 15 | 20% | 53% | 16 | 48 | 102 | 102 | 13% | 6.7% | 0.072 |
| exposed_king | 54 | 39% | 59% | 4 | 45 | 125 | 204 | 13% | 1.9% | 0.076 |
| exchange_imbalance | 18 | 44% | 61% | 0 | 44 | 100 | 111 | 17% | 5.6% | 0.085 |
| opposite_side_castling | 21 | 48% | 76% | 0 | 42 | 72 | 184 | 10% | 4.8% | 0.056 |
| closed_centre | 24 | 21% | 50% | 22 | 41 | 95 | 212 | 8% | 0.0% | 0.061 |
| material_imbalance | 127 | 37% | 65% | 2 | 38 | 100 | 195 | 11% | 2.4% | 0.070 |
| maroczy_bind | 12 | 33% | 50% | 21 | 37 | 95 | 95 | 8% | 0.0% | 0.075 |
| queenless_middlegame | 41 | 41% | 61% | 9 | 37 | 79 | 184 | 10% | 2.4% | 0.068 |
| advanced_passer | 33 | 55% | 76% | 0 | 37 | 79 | 105 | 9% | 6.1% | 0.053 |
| rook_on_open_file | 91 | 42% | 70% | 0 | 36 | 105 | 184 | 13% | 2.2% | 0.069 |
| rook_on_semi_open_file | 104 | 32% | 62% | 8 | 35 | 95 | 195 | 9% | 1.9% | 0.064 |
| locked_pawn_chain | 31 | 23% | 61% | 11 | 35 | 84 | 95 | 6% | 0.0% | 0.056 |
| backward_pawn | 96 | 27% | 64% | 10 | 34 | 95 | 113 | 9% | 1.0% | 0.057 |
| passed_pawn | 98 | 45% | 70% | 0 | 34 | 100 | 195 | 11% | 3.1% | 0.059 |
| same_side_castling | 92 | 37% | 67% | 2 | 34 | 100 | 130 | 11% | 2.2% | 0.065 |
| connected_passers | 26 | 42% | 77% | 0 | 33 | 71 | 111 | 8% | 3.8% | 0.046 |
| protected_passer | 41 | 39% | 73% | 0 | 32 | 83 | 105 | 10% | 2.4% | 0.047 |
| doubled_pawns | 94 | 41% | 70% | 0 | 31 | 84 | 184 | 10% | 2.1% | 0.056 |
| open_centre | 91 | 44% | 70% | 0 | 31 | 78 | 184 | 8% | 2.2% | 0.054 |
| open_file | 167 | 40% | 71% | 0 | 31 | 83 | 175 | 10% | 1.8% | 0.054 |
| bad_bishop | 65 | 38% | 68% | 0 | 31 | 62 | 130 | 8% | 1.5% | 0.043 |
| semi_open_file | 227 | 37% | 69% | 0 | 30 | 82 | 130 | 8% | 1.3% | 0.051 |
| bishop_pair | 76 | 39% | 67% | 1 | 29 | 82 | 113 | 7% | 0.0% | 0.053 |
| isolated_pawn | 172 | 36% | 68% | 0 | 29 | 79 | 130 | 8% | 1.2% | 0.050 |
| hanging_piece | 45 | 49% | 69% | 0 | 26 | 83 | 130 | 7% | 0.0% | 0.055 |
| king_in_centre | 48 | 40% | 69% | 1 | 25 | 57 | 95 | 4% | 0.0% | 0.039 |
| weak_colour_complex | 47 | 40% | 68% | 0 | 25 | 62 | 100 | 6% | 0.0% | 0.045 |
| knight_outpost | 45 | 42% | 69% | 0 | 24 | 95 | 102 | 7% | 0.0% | 0.043 |
| opposite_coloured_bishops | 27 | 37% | 74% | 0 | 23 | 46 | 56 | 4% | 3.7% | 0.024 |
| queenside_majority | 46 | 52% | 74% | 0 | 23 | 79 | 105 | 7% | 0.0% | 0.045 |
| minority_attack | 10 | 20% | 70% | 8 | 20 | 44 | 82 | 0% | 0.0% | 0.032 |
| carlsbad | 22 | 27% | 77% | 4 | 18 | 44 | 82 | 5% | 0.0% | 0.036 |
| isolated_queen_pawn | 30 | 40% | 77% | 0 | 17 | 61 | 83 | 3% | 0.0% | 0.025 |
| complex_ending | 10 | 40% | 80% | 0 | 15 | 26 | 111 | 10% | 0.0% | 0.045 |
| minor_piece_ending | 11 | 0% | 73% | 2 | 13 | 32 | 56 | 0% | 0.0% | 0.004 |
| rook_and_minor_ending | 21 | 57% | 81% | 0 | 11 | 41 | 48 | 0% | 0.0% | 0.010 |
| rook_ending | 9 | 44% | 100% | 0 | 2 | 1 | 13 | 0% | 0.0% | 0.000 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| vienna | 6 | 0% | 33% | 63 | 112 | 195 | 331 | 50% | 16.7% | 0.210 |
| ruy_lopez | 5 | 80% | 80% | 0 | 97 | 484 | 484 | 20% | 20.0% | 0.100 |
| dutch | 6 | 0% | 17% | 50 | 94 | 102 | 334 | 33% | 16.7% | 0.145 |
| scandinavian | 5 | 20% | 40% | 36 | 91 | 220 | 220 | 40% | 0.0% | 0.204 |
| trompowsky | 5 | 20% | 60% | 19 | 56 | 165 | 165 | 20% | 0.0% | 0.121 |
| philidor | 5 | 40% | 60% | 11 | 49 | 204 | 204 | 20% | 0.0% | 0.101 |
| london | 5 | 0% | 20% | 57 | 49 | 78 | 78 | 0% | 0.0% | 0.084 |
| kings_indian | 6 | 33% | 50% | 20 | 49 | 42 | 212 | 17% | 0.0% | 0.086 |
| modern | 5 | 60% | 80% | 0 | 47 | 225 | 225 | 20% | 0.0% | 0.101 |
| queens_indian | 5 | 0% | 40% | 35 | 41 | 105 | 105 | 20% | 0.0% | 0.081 |
| italian | 5 | 20% | 60% | 25 | 39 | 95 | 95 | 0% | 0.0% | 0.059 |
| queens_gambit_declined | 6 | 33% | 67% | 6 | 34 | 82 | 113 | 17% | 0.0% | 0.118 |
| nimzo_indian | 5 | 20% | 60% | 2 | 32 | 84 | 84 | 0% | 0.0% | 0.077 |
| bishops_opening | 5 | 40% | 60% | 0 | 29 | 111 | 111 | 20% | 0.0% | 0.096 |
| grunfeld | 5 | 80% | 80% | 0 | 26 | 130 | 130 | 20% | 0.0% | 0.086 |
| polish | 5 | 40% | 80% | 0 | 25 | 125 | 125 | 20% | 0.0% | 0.077 |
| caro_kann | 5 | 20% | 60% | 16 | 25 | 61 | 61 | 0% | 0.0% | 0.020 |
| old_indian | 4 | 25% | 50% | 22 | 24 | 53 | 53 | 0% | 0.0% | 0.010 |
| benoni | 4 | 50% | 50% | 16 | 23 | 60 | 60 | 0% | 0.0% | 0.005 |
| pirc | 4 | 50% | 75% | 8 | 22 | 72 | 72 | 0% | 0.0% | 0.034 |
| kings_gambit | 4 | 50% | 75% | 0 | 21 | 83 | 83 | 0% | 0.0% | 0.045 |
| sicilian_closed | 4 | 25% | 75% | 4 | 20 | 74 | 74 | 0% | 0.0% | 0.054 |
| queens_gambit_accepted | 4 | 50% | 75% | 0 | 20 | 79 | 79 | 0% | 0.0% | 0.096 |
| bird | 4 | 25% | 75% | 6 | 18 | 62 | 62 | 0% | 0.0% | 0.009 |
| nimzo_larsen | 4 | 50% | 50% | 16 | 18 | 40 | 40 | 0% | 0.0% | 0.023 |
| french | 5 | 40% | 80% | 0 | 17 | 85 | 85 | 0% | 0.0% | 0.034 |
| bogo_indian | 5 | 20% | 60% | 0 | 16 | 44 | 44 | 0% | 0.0% | 0.005 |
| torre | 5 | 20% | 60% | 2 | 15 | 41 | 41 | 0% | 0.0% | 0.004 |
| budapest | 4 | 75% | 75% | 0 | 14 | 56 | 56 | 0% | 0.0% | 0.007 |
| albin | 4 | 75% | 75% | 0 | 14 | 55 | 55 | 0% | 0.0% | 0.032 |
| smith_morra | 4 | 50% | 50% | 13 | 14 | 28 | 28 | 0% | 0.0% | 0.009 |
| colle | 5 | 40% | 80% | 0 | 13 | 44 | 44 | 0% | 0.0% | 0.005 |
| chigorin | 4 | 0% | 75% | 0 | 12 | 46 | 46 | 0% | 0.0% | 0.005 |
| other | 5 | 40% | 80% | 12 | 11 | 26 | 26 | 0% | 0.0% | 0.003 |
| owens | 5 | 40% | 80% | 0 | 10 | 50 | 50 | 0% | 0.0% | 0.003 |
| petrov | 4 | 75% | 75% | 0 | 8 | 33 | 33 | 0% | 0.0% | 0.002 |
| sicilian_alapin | 5 | 60% | 100% | 0 | 8 | 21 | 21 | 0% | 0.0% | 0.003 |
| alekhine | 4 | 50% | 75% | 1 | 8 | 30 | 30 | 0% | 0.0% | 0.001 |
| reti | 5 | 20% | 80% | 0 | 8 | 29 | 29 | 0% | 0.0% | 0.003 |
| scotch | 5 | 80% | 80% | 0 | 8 | 40 | 40 | 0% | 0.0% | 0.001 |
| four_knights | 5 | 20% | 100% | 11 | 8 | 16 | 16 | 0% | 0.0% | 0.001 |
| semi_slav | 7 | 43% | 86% | 2 | 7 | 9 | 30 | 0% | 0.0% | 0.004 |
| slav | 5 | 20% | 100% | 0 | 6 | 16 | 16 | 0% | 0.0% | 0.001 |
| benko | 4 | 50% | 100% | 1 | 6 | 21 | 21 | 0% | 0.0% | 0.001 |
| catalan | 6 | 50% | 100% | 0 | 4 | 2 | 19 | 0% | 0.0% | 0.002 |
| sicilian | 5 | 40% | 100% | 0 | 3 | 8 | 8 | 0% | 0.0% | 0.000 |
| english | 5 | 60% | 100% | 0 | 3 | 11 | 11 | 0% | 0.0% | 0.002 |
| centre_game | 4 | 50% | 100% | 2 | 2 | 3 | 3 | 0% | 0.0% | 0.000 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| cl-170 | 484 | h3e6 | b2c3 | 113 | ruy_lopez | advanced_passer, backward_pawn, bad_bishop, connected_passers, exposed_king, material_imbalance, opposite_side_castling, passed_pawn, protected_passer, rook_on_open_file, space_advantage | `3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 4 41` |
| cl-097 | 334 | c1b3 | g2g4 | 26 | dutch | advanced_passer, doubled_pawns, isolated_pawn, king_attack, material_imbalance, open_centre, opposite_coloured_bishops, passed_pawn, queenless_middlegame, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `r2r4/4R3/2k1p2p/2p1Bbp1/8/2N1p3/1PP3PP/1KN5 w - - 0 25` |
| cl-201 | 331 | f8d8 | c8d8 | 143 | vienna | doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_semi_open_file, same_side_castling | `2r2rk1/pp3p1p/4P1p1/8/1p2B2R/3Q2PP/2P2PK1/2q5 b - - 1 25` |
| cl-151 | 251 | f1f5 | d8f8 | -157 | ponziani | bishop_pair, exposed_king, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling, space_advantage | `3r3k/p2q2p1/P1p1R2p/1pb1P3/8/1BP1n1BP/1P2Q1PK/4Rr2 b - - 4 33` |
| cl-125 | 225 | c4e3 | c4a3 | -31 | modern | backward_pawn, bad_bishop, closed_centre, king_in_centre, locked_pawn_chain, passed_pawn, protected_passer, rook_on_semi_open_file | `r3k2r/4npbp/1qp1p1p1/3pP2P/2nP1P2/PpQ1B3/1P1N2P1/1KR2N1R b kq - 4 20` |
| cl-045 | 220 | f6g7 | d6d2 | 10 | scandinavian | backward_pawn, doubled_pawns, queen_ending | `8/5p2/p2qpkp1/1p5p/1P2QP1P/2P5/1P4PK/8 b - - 6 34` |
| cl-117 | 212 | e1g1 | e3h6 | 145 | kings_indian | backward_pawn, bishop_pair, closed_centre, doubled_pawns, exposed_king, isolated_pawn, king_in_centre, locked_pawn_chain, material_imbalance, rook_on_semi_open_file | `2kr3r/pp1bn1q1/3p1npp/2pPp3/2P1P2Q/2P1B3/P2NBPP1/R3K2R w KQ - 12 16` |
| cl-144 | 204 | c4e4 | c4e2 | 32 | philidor | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, queenside_majority, rook_on_semi_open_file | `r7/pp1kNpQ1/3p4/8/2q1P3/2P3R1/PP3r2/2KR4 b - - 0 24` |
| cl-202 | 195 | e3a7 | e2d4 | -8 | vienna | bad_bishop, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, passed_pawn, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, weak_colour_complex | `3rkb1r/ppp2pp1/2b5/4P2p/4p3/2P1B1P1/PPP1N2P/R3KR2 w Qk - 2 14` |
| cl-173 | 184 | e4d2 | h2h4 | -57 | scandinavian | backward_pawn, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, open_centre, opposite_side_castling, queenless_middlegame, rook_on_open_file | `2kr3r/1p1np2p/p1p3pb/P3pb2/4N3/1P1N2P1/2P2PBP/3RR1K1 w - - 0 21` |
| cl-094 | 175 | b5h5 | b5b4 | -67 | danish_gambit | hanging_piece, isolated_pawn, rook_on_open_file, same_side_castling | `r4rk1/pp1b1ppp/2np4/1q6/P2PB3/5N1P/1P1Q1PP1/R3R1K1 b - - 0 19` |
| cl-198 | 165 | a2a1 | b8a7 | -87 | trompowsky | exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, space_advantage, weak_colour_complex | `1k1r4/1p3p1R/5N2/p1pPPQ2/b7/2P5/qP3Pr1/2K4R b - - 1 29` |
| cl-110 | 130 | f4f2 | f4f8 | 22 | grunfeld | bad_bishop, hanging_piece, isolated_pawn, maroczy_bind, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `r4rk1/7p/6p1/p1q5/BpPnPR2/8/PQ4PP/2R4K w - - 1 28` |
| cl-149 | 125 | c5e3 | e2f3 | 49 | polish | doubled_pawns, exposed_king, isolated_pawn, isolated_queen_pawn, open_centre, rook_on_open_file, same_side_castling, space_advantage | `r2qr1k1/pp1bnpp1/5b1p/2Bp1P1P/6P1/2PB4/PP1NQP2/R4RK1 w - - 7 17` |
| cl-158 | 113 | e8c8 | e7d6 | 5 | queens_gambit_declined | backward_pawn, bishop_pair, carlsbad, doubled_pawns, isolated_pawn, knight_outpost, material_imbalance, queenless_middlegame, rook_on_semi_open_file | `r3k2r/1p2bp2/2p3b1/p2pNp1p/N2PnP2/P2BP1P1/1P5P/2R1K1R1 b kq - 1 20` |
| cl-007 | 111 | g4g6 | d6d5 | -24 | bishops_opening | backward_pawn, complex_ending, connected_passers, doubled_pawns, exchange_imbalance, material_imbalance, passed_pawn, rook_on_semi_open_file | `6k1/1p6/3p4/p1p4r/P2pPBq1/3P4/1PP3PP/5QK1 b - - 4 29` |
| cl-162 | 105 | g1h1 | h2h3 | 22 | queens_indian | advanced_passer, backward_pawn, bad_bishop, king_attack, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, space_advantage | `5rk1/3PQ1pp/1q6/1p6/2p5/2Pp4/3NbPPP/4R1K1 w - - 3 26` |
| cl-096 | 102 | e7e6 | f5f4 | -44 | dutch | exposed_king, isolated_pawn, knight_outpost, rook_on_open_file, same_side_castling, unusual_king_placement | `4r3/R2bp2p/3p1qpk/2nB1p2/2PN3P/4P1P1/5P2/1Q4K1 b - - 2 32` |
| cl-203 | 100 | e2g3 | d1b1 | 8 | vienna | backward_pawn, exchange_imbalance, material_imbalance, passed_pawn, protected_passer, rook_on_open_file, same_side_castling, weak_colour_complex | `5rk1/3n1p1p/2pp1np1/1pb1p3/4P3/3PNQ1P/1q2NPP1/R2R2K1 w - - 0 21` |
| cl-112 | 95 | d1d4 | f3e5 | -17 | italian | backward_pawn, exposed_king, isolated_pawn, knight_outpost, open_centre, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `5rk1/1pp2rp1/3p3p/2q1n3/p3P3/P1P2NQP/1P3RPK/3R4 w - - 2 25` |
| cl-200 | 95 | b5b4 | d8a5 | 10 | trompowsky | backward_pawn, closed_centre, exposed_king, king_in_centre, knight_outpost, locked_pawn_chain, maroczy_bind, queenside_majority, rook_on_semi_open_file, space_advantage | `1rbqk2r/3nbp2/p2p2p1/1ppPp1Pn/4P2P/2N2P2/PP1QBBN1/2KR2R1 b k - 3 24` |
| cl-106 | 85 | f7f8 | a8f8 | -81 | french | backward_pawn, bad_bishop, bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, same_side_castling, space_advantage, weak_colour_complex | `r4Bk1/ppqb1r1p/4p1n1/nP1pPp2/8/2PB1NP1/P2NQP2/R4RK1 b - - 0 20` |
| cl-129 | 84 | d1d2 | f2f4 | 80 | nimzo_indian | backward_pawn, bishop_pair, closed_centre, doubled_pawns, exposed_king, isolated_pawn, locked_pawn_chain, material_imbalance, rook_on_semi_open_file, same_side_castling | `r1bq1r2/p3np1k/1p1p1n1p/2pPp3/2P1P2p/P1PB4/5PP1/1RBQ1RKN w - - 2 16` |
| cl-024 | 83 | g7a7 | g7d7 | -26 | kings_gambit | connected_passers, exchange_imbalance, hanging_piece, isolated_pawn, isolated_queen_pawn, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_and_minor_ending, rook_on_semi_open_file | `5k2/p5R1/2p5/8/1K1PN2P/P2r2P1/2r5/8 w - - 5 42` |
| cl-157 | 82 | f6e4 | a7a5 | -24 | queens_gambit_declined | bishop_pair, carlsbad, material_imbalance, minority_attack, rook_on_semi_open_file, same_side_castling | `r2qr1k1/pp2bpp1/2p2n1p/3p2n1/1P1P4/2NBP1BP/P3QPP1/1R3RK1 b - - 2 16` |
