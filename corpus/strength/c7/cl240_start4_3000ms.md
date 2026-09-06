# Move quality: competition_like_v1 at 3000 ms

Engine: working tree, 3000 ms. Suite: corpus\competition_like_v1.jsonl (competition_like v1, hash `6a8111f22f9ea393`, 240 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 240 | 39% | 68% | 2 | 34 | 99 | 175 | 10% | 1.7% | 0.062 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 60 | 43% | 85% | 0 | 22 | 41 | 111 | 7% | 1.7% | 0.035 |
| middlegame | 144 | 36% | 58% | 12 | 44 | 116 | 195 | 13% | 2.1% | 0.084 |
| opening | 36 | 42% | 75% | 6 | 17 | 55 | 61 | 3% | 0.0% | 0.020 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| king_attack | 9 | 44% | 56% | 0 | 59 | 105 | 334 | 22% | 11.1% | 0.097 |
| exposed_king | 54 | 43% | 59% | 4 | 49 | 161 | 204 | 15% | 1.9% | 0.093 |
| rook_on_open_file | 91 | 40% | 66% | 1 | 48 | 161 | 195 | 16% | 3.3% | 0.091 |
| space_advantage | 30 | 40% | 63% | 6 | 45 | 105 | 165 | 13% | 3.3% | 0.071 |
| opposite_side_castling | 21 | 48% | 67% | 2 | 45 | 72 | 184 | 10% | 4.8% | 0.059 |
| unusual_king_placement | 15 | 33% | 53% | 16 | 44 | 74 | 74 | 7% | 6.7% | 0.059 |
| closed_centre | 24 | 25% | 50% | 25 | 44 | 99 | 212 | 8% | 0.0% | 0.071 |
| material_imbalance | 127 | 39% | 63% | 7 | 44 | 113 | 204 | 13% | 3.1% | 0.082 |
| queenside_majority | 46 | 46% | 67% | 0 | 44 | 116 | 195 | 15% | 2.2% | 0.087 |
| queenless_middlegame | 41 | 39% | 59% | 16 | 42 | 113 | 191 | 12% | 2.4% | 0.081 |
| passed_pawn | 98 | 47% | 70% | 0 | 41 | 116 | 225 | 13% | 4.1% | 0.074 |
| locked_pawn_chain | 31 | 26% | 58% | 15 | 41 | 99 | 116 | 10% | 0.0% | 0.078 |
| same_side_castling | 92 | 37% | 62% | 10 | 40 | 116 | 165 | 13% | 2.2% | 0.081 |
| bad_bishop | 65 | 38% | 66% | 2 | 40 | 99 | 195 | 9% | 3.1% | 0.054 |
| advanced_passer | 33 | 58% | 76% | 0 | 39 | 105 | 116 | 12% | 6.1% | 0.067 |
| maroczy_bind | 12 | 25% | 50% | 31 | 39 | 95 | 95 | 8% | 0.0% | 0.070 |
| rook_on_semi_open_file | 104 | 33% | 62% | 12 | 38 | 105 | 195 | 11% | 1.9% | 0.074 |
| exchange_imbalance | 18 | 50% | 72% | 0 | 38 | 83 | 111 | 11% | 5.6% | 0.071 |
| open_file | 167 | 41% | 69% | 0 | 37 | 111 | 191 | 12% | 2.4% | 0.068 |
| backward_pawn | 96 | 30% | 65% | 11 | 36 | 100 | 116 | 10% | 1.0% | 0.065 |
| open_centre | 91 | 43% | 65% | 3 | 36 | 95 | 191 | 10% | 2.2% | 0.065 |
| isolated_pawn | 172 | 37% | 66% | 2 | 36 | 100 | 175 | 10% | 1.7% | 0.064 |
| hanging_piece | 45 | 42% | 64% | 0 | 35 | 116 | 175 | 11% | 0.0% | 0.077 |
| semi_open_file | 227 | 38% | 67% | 2 | 35 | 99 | 184 | 10% | 1.8% | 0.063 |
| rook_and_minor_ending | 21 | 48% | 81% | 0 | 35 | 48 | 83 | 5% | 4.8% | 0.034 |
| weak_colour_complex | 47 | 38% | 68% | 0 | 35 | 74 | 165 | 6% | 2.1% | 0.052 |
| connected_passers | 26 | 54% | 77% | 0 | 34 | 74 | 111 | 8% | 3.8% | 0.049 |
| doubled_pawns | 94 | 44% | 67% | 0 | 34 | 106 | 184 | 12% | 2.1% | 0.063 |
| bishop_pair | 76 | 43% | 64% | 2 | 31 | 84 | 113 | 8% | 0.0% | 0.058 |
| protected_passer | 41 | 49% | 76% | 0 | 31 | 74 | 105 | 7% | 2.4% | 0.042 |
| king_in_centre | 48 | 38% | 67% | 12 | 28 | 62 | 106 | 6% | 0.0% | 0.046 |
| knight_outpost | 45 | 42% | 69% | 7 | 27 | 95 | 113 | 9% | 0.0% | 0.053 |
| opposite_coloured_bishops | 27 | 37% | 78% | 0 | 23 | 46 | 74 | 4% | 3.7% | 0.026 |
| carlsbad | 22 | 32% | 73% | 8 | 20 | 47 | 82 | 5% | 0.0% | 0.038 |
| isolated_queen_pawn | 30 | 37% | 77% | 0 | 18 | 61 | 83 | 3% | 0.0% | 0.026 |
| minority_attack | 10 | 40% | 80% | 4 | 16 | 44 | 82 | 0% | 0.0% | 0.031 |
| complex_ending | 10 | 60% | 80% | 0 | 15 | 26 | 111 | 10% | 0.0% | 0.045 |
| minor_piece_ending | 11 | 18% | 91% | 0 | 6 | 11 | 32 | 0% | 0.0% | 0.002 |
| rook_ending | 9 | 56% | 100% | 0 | 2 | 0 | 19 | 0% | 0.0% | 0.000 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| albin | 4 | 25% | 25% | 51 | 150 | 10000 | 10000 | 25% | 25.0% | 0.170 |
| scandinavian | 5 | 20% | 40% | 184 | 134 | 243 | 243 | 60% | 0.0% | 0.303 |
| ruy_lopez | 5 | 60% | 60% | 0 | 106 | 484 | 484 | 20% | 20.0% | 0.103 |
| vienna | 6 | 0% | 50% | 24 | 98 | 195 | 331 | 33% | 16.7% | 0.169 |
| dutch | 6 | 17% | 33% | 40 | 78 | 52 | 334 | 17% | 16.7% | 0.100 |
| nimzo_indian | 5 | 0% | 40% | 75 | 64 | 161 | 161 | 20% | 0.0% | 0.175 |
| kings_indian | 6 | 33% | 33% | 40 | 61 | 74 | 212 | 17% | 0.0% | 0.100 |
| london | 5 | 0% | 20% | 58 | 59 | 106 | 106 | 20% | 0.0% | 0.118 |
| trompowsky | 5 | 20% | 60% | 19 | 56 | 165 | 165 | 20% | 0.0% | 0.121 |
| benoni | 4 | 25% | 25% | 46 | 52 | 116 | 116 | 25% | 0.0% | 0.120 |
| philidor | 5 | 40% | 60% | 11 | 49 | 204 | 204 | 20% | 0.0% | 0.101 |
| centre_game | 4 | 25% | 75% | 3 | 49 | 191 | 191 | 25% | 0.0% | 0.125 |
| modern | 5 | 60% | 80% | 0 | 48 | 225 | 225 | 20% | 0.0% | 0.101 |
| sicilian_closed | 4 | 25% | 50% | 40 | 45 | 100 | 100 | 25% | 0.0% | 0.115 |
| queens_gambit_declined | 6 | 33% | 50% | 20 | 39 | 82 | 113 | 17% | 0.0% | 0.121 |
| italian | 5 | 20% | 60% | 25 | 39 | 95 | 95 | 0% | 0.0% | 0.059 |
| queens_indian | 5 | 20% | 60% | 15 | 34 | 105 | 105 | 20% | 0.0% | 0.079 |
| bogo_indian | 5 | 0% | 60% | 24 | 33 | 99 | 99 | 0% | 0.0% | 0.052 |
| colle | 5 | 40% | 60% | 22 | 33 | 118 | 118 | 20% | 0.0% | 0.084 |
| kings_gambit | 4 | 25% | 50% | 21 | 31 | 83 | 83 | 0% | 0.0% | 0.048 |
| bishops_opening | 5 | 40% | 60% | 0 | 29 | 111 | 111 | 20% | 0.0% | 0.096 |
| old_indian | 4 | 25% | 50% | 28 | 27 | 53 | 53 | 0% | 0.0% | 0.012 |
| polish | 5 | 40% | 80% | 0 | 25 | 125 | 125 | 20% | 0.0% | 0.077 |
| caro_kann | 5 | 40% | 60% | 16 | 25 | 61 | 61 | 0% | 0.0% | 0.020 |
| grunfeld | 5 | 80% | 80% | 0 | 23 | 116 | 116 | 20% | 0.0% | 0.073 |
| pirc | 4 | 50% | 75% | 8 | 22 | 72 | 72 | 0% | 0.0% | 0.034 |
| french | 5 | 40% | 80% | 0 | 21 | 85 | 85 | 0% | 0.0% | 0.034 |
| queens_gambit_accepted | 4 | 50% | 75% | 0 | 20 | 79 | 79 | 0% | 0.0% | 0.096 |
| bird | 4 | 25% | 75% | 6 | 18 | 62 | 62 | 0% | 0.0% | 0.009 |
| nimzo_larsen | 4 | 50% | 50% | 16 | 18 | 40 | 40 | 0% | 0.0% | 0.023 |
| slav | 5 | 40% | 80% | 0 | 15 | 62 | 62 | 0% | 0.0% | 0.024 |
| smith_morra | 4 | 50% | 50% | 13 | 14 | 28 | 28 | 0% | 0.0% | 0.009 |
| owens | 5 | 40% | 80% | 0 | 13 | 50 | 50 | 0% | 0.0% | 0.005 |
| chigorin | 4 | 0% | 75% | 0 | 12 | 46 | 46 | 0% | 0.0% | 0.005 |
| other | 5 | 40% | 80% | 12 | 11 | 26 | 26 | 0% | 0.0% | 0.003 |
| catalan | 6 | 67% | 83% | 0 | 11 | 19 | 46 | 0% | 0.0% | 0.005 |
| torre | 5 | 60% | 80% | 0 | 10 | 41 | 41 | 0% | 0.0% | 0.002 |
| petrov | 4 | 75% | 75% | 0 | 8 | 33 | 33 | 0% | 0.0% | 0.002 |
| sicilian_alapin | 5 | 60% | 100% | 0 | 8 | 21 | 21 | 0% | 0.0% | 0.003 |
| reti | 5 | 40% | 80% | 0 | 8 | 29 | 29 | 0% | 0.0% | 0.003 |
| four_knights | 5 | 40% | 100% | 11 | 8 | 16 | 16 | 0% | 0.0% | 0.001 |
| semi_slav | 7 | 43% | 86% | 2 | 7 | 9 | 30 | 0% | 0.0% | 0.004 |
| alekhine | 4 | 50% | 100% | 1 | 6 | 23 | 23 | 0% | 0.0% | 0.003 |
| scotch | 5 | 80% | 100% | 0 | 4 | 18 | 18 | 0% | 0.0% | 0.000 |
| sicilian | 5 | 40% | 100% | 0 | 3 | 8 | 8 | 0% | 0.0% | 0.000 |
| english | 5 | 60% | 100% | 0 | 3 | 11 | 11 | 0% | 0.0% | 0.002 |
| benko | 4 | 75% | 100% | 0 | 0 | 2 | 2 | 0% | 0.0% | 0.000 |
| budapest | 4 | 100% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| cl-000 | 10000 | g2f3 | e7e8 | 17 | albin | bad_bishop, isolated_pawn, material_imbalance, passed_pawn, queenside_majority, rook_and_minor_ending, rook_on_open_file, weak_colour_complex | `2k5/1pp1rp1p/8/1NP5/P6n/2N5/1P4bP/2KR4 b - - 0 27` |
| cl-170 | 484 | h3e6 | b2c3 | 113 | ruy_lopez | advanced_passer, backward_pawn, bad_bishop, connected_passers, exposed_king, material_imbalance, opposite_side_castling, passed_pawn, protected_passer, rook_on_open_file, space_advantage | `3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 4 41` |
| cl-097 | 334 | c1b3 | g2g4 | 26 | dutch | advanced_passer, doubled_pawns, isolated_pawn, king_attack, material_imbalance, open_centre, opposite_coloured_bishops, passed_pawn, queenless_middlegame, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `r2r4/4R3/2k1p2p/2p1Bbp1/8/2N1p3/1PP3PP/1KN5 w - - 0 25` |
| cl-201 | 331 | f8d8 | c8d8 | 143 | vienna | doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_semi_open_file, same_side_castling | `2r2rk1/pp3p1p/4P1p1/8/1p2B2R/3Q2PP/2P2PK1/2q5 b - - 1 25` |
| cl-174 | 243 | b7c7 | b7b2 | -124 | scandinavian | bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `Q7/1r3ppk/2q1p2p/5b2/2P1n3/P2B1N2/1R3PPP/2n1B1K1 b - - 3 29` |
| cl-125 | 225 | c4e3 | c4a3 | -31 | modern | backward_pawn, bad_bishop, closed_centre, king_in_centre, locked_pawn_chain, passed_pawn, protected_passer, rook_on_semi_open_file | `r3k2r/4npbp/1qp1p1p1/3pP2P/2nP1P2/PpQ1B3/1P1N2P1/1KR2N1R b kq - 4 20` |
| cl-045 | 220 | f6g7 | d6d2 | 4 | scandinavian | backward_pawn, doubled_pawns, queen_ending | `8/5p2/p2qpkp1/1p5p/1P2QP1P/2P5/1P4PK/8 b - - 6 34` |
| cl-117 | 212 | e1g1 | e3h6 | 145 | kings_indian | backward_pawn, bishop_pair, closed_centre, doubled_pawns, exposed_king, isolated_pawn, king_in_centre, locked_pawn_chain, material_imbalance, rook_on_semi_open_file | `2kr3r/pp1bn1q1/3p1npp/2pPp3/2P1P2Q/2P1B3/P2NBPP1/R3K2R w KQ - 12 16` |
| cl-144 | 204 | c4e4 | c4e2 | 32 | philidor | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, queenside_majority, rook_on_semi_open_file | `r7/pp1kNpQ1/3p4/8/2q1P3/2P3R1/PP3r2/2KR4 b - - 0 24` |
| cl-202 | 195 | e3a7 | e2d4 | -8 | vienna | bad_bishop, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, passed_pawn, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, weak_colour_complex | `3rkb1r/ppp2pp1/2b5/4P2p/4p3/2P1B1P1/PPP1N2P/R3KR2 w Qk - 2 14` |
| cl-087 | 191 | e5e6 | f1e1 | 14 | centre_game | isolated_pawn, open_centre, queenless_middlegame, rook_on_open_file, same_side_castling | `r2r3k/ppp1b1pp/2n2p2/4P3/2B2P2/2P2N2/P1b3PP/R1B2RK1 w - - 0 15` |
| cl-173 | 184 | e4d2 | h2h4 | -57 | scandinavian | backward_pawn, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, open_centre, opposite_side_castling, queenless_middlegame, rook_on_open_file | `2kr3r/1p1np2p/p1p3pb/P3pb2/4N3/1P1N2P1/2P2PBP/3RR1K1 w - - 0 21` |
| cl-094 | 175 | b5h5 | b5b4 | -67 | danish_gambit | hanging_piece, isolated_pawn, rook_on_open_file, same_side_castling | `r4rk1/pp1b1ppp/2np4/1q6/P2PB3/5N1P/1P1Q1PP1/R3R1K1 b - - 0 19` |
| cl-198 | 165 | a2a1 | b8a7 | -87 | trompowsky | exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, space_advantage, weak_colour_complex | `1k1r4/1p3p1R/5N2/p1pPPQ2/b7/2P5/qP3Pr1/2K4R b - - 1 29` |
| cl-128 | 161 | d3d8 | d3a3 | 100 | nimzo_indian | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `4r1k1/pp3pnn/8/8/4PN2/P2q1P2/5Q1P/6RK b - - 1 32` |
| cl-149 | 125 | c5e3 | e2f3 | 49 | polish | doubled_pawns, exposed_king, isolated_pawn, isolated_queen_pawn, open_centre, rook_on_open_file, same_side_castling, space_advantage | `r2qr1k1/pp1bnpp1/5b1p/2Bp1P1P/6P1/2PB4/PP1NQP2/R4RK1 w - - 7 17` |
| cl-014 | 118 | a3a4 | e5f6 | 13 | colle | isolated_pawn, pawn_ending, queenside_majority | `8/pp2k1p1/4p2p/4Pp2/8/PPK3P1/2P4P/8 w - f6 0 32` |
| cl-066 | 116 | c8d8 | c8e8 | -88 | benoni | advanced_passer, backward_pawn, exposed_king, knight_outpost, locked_pawn_chain, material_imbalance, passed_pawn, queenside_majority, rook_on_open_file, same_side_castling | `2r3k1/3q3p/3p1P1n/1p1Pr1p1/2p3P1/1nP4P/2B2Q1K/3NRR2 b - - 2 30` |
| cl-110 | 116 | f4g4 | f4f8 | 34 | grunfeld | bad_bishop, hanging_piece, isolated_pawn, maroczy_bind, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `r4rk1/7p/6p1/p1q5/BpPnPR2/8/PQ4PP/2R4K w - - 1 28` |
| cl-158 | 113 | e8c8 | e7d6 | 5 | queens_gambit_declined | backward_pawn, bishop_pair, carlsbad, doubled_pawns, isolated_pawn, knight_outpost, material_imbalance, queenless_middlegame, rook_on_semi_open_file | `r3k2r/1p2bp2/2p3b1/p2pNp1p/N2PnP2/P2BP1P1/1P5P/2R1K1R1 b kq - 1 20` |
| cl-007 | 111 | g4g6 | d6d5 | -24 | bishops_opening | backward_pawn, complex_ending, connected_passers, doubled_pawns, exchange_imbalance, material_imbalance, passed_pawn, rook_on_semi_open_file | `6k1/1p6/3p4/p1p4r/P2pPBq1/3P4/1PP3PP/5QK1 b - - 4 29` |
| cl-222 | 106 | a7a6 | c8d7 | 30 | london | doubled_pawns, isolated_pawn, king_in_centre, rook_on_semi_open_file | `r1b1kb1r/pp3ppp/2n1pn2/1BPpN3/5B2/2q1P3/P1PN1PPP/1R1QK2R b Kkq - 1 9` |
| cl-162 | 105 | g1h1 | h2h3 | 17 | queens_indian | advanced_passer, backward_pawn, bad_bishop, king_attack, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, space_advantage | `5rk1/3PQ1pp/1q6/1p6/2p5/2Pp4/3NbPPP/4R1K1 w - - 3 26` |
| cl-188 | 100 | f1d1 | f2f3 | -86 | sicilian_closed | backward_pawn, bishop_pair, doubled_pawns, isolated_pawn, knight_outpost, material_imbalance, rook_on_open_file, same_side_castling | `6k1/p1q2p2/2pbr1p1/2pn1b1p/N1Np1P2/1P1P3P/P1PB1QP1/5R1K w - - 1 21` |
| cl-073 | 99 | b6b4 | g1f2 | -35 | bogo_indian | backward_pawn, bad_bishop, closed_centre, exposed_king, isolated_pawn, locked_pawn_chain, passed_pawn, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `1rb5/Rpq2kpp/1Q1p4/2rPp3/4Pp2/3B1P1P/6P1/1R4K1 w - - 7 30` |
