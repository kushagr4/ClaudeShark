# Move quality: competition_like_v1 at depth 6

Engine: champions\v2_2a_low_material, depth 6. Suite: corpus\competition_like_v1.jsonl (competition_like v1, hash `6a8111f22f9ea393`, 240 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 240 | 38% | 67% | 0 | 33 | 95 | 159 | 10% | 1.2% | 0.062 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 60 | 43% | 83% | 0 | 21 | 52 | 101 | 7% | 1.7% | 0.034 |
| middlegame | 144 | 36% | 59% | 11 | 42 | 116 | 191 | 13% | 1.4% | 0.084 |
| opening | 36 | 39% | 69% | 12 | 18 | 55 | 57 | 0% | 0.0% | 0.025 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| exposed_king | 54 | 37% | 54% | 12 | 53 | 161 | 204 | 19% | 1.9% | 0.103 |
| queenside_majority | 46 | 43% | 63% | 0 | 48 | 134 | 195 | 17% | 2.2% | 0.100 |
| space_advantage | 30 | 37% | 60% | 6 | 46 | 105 | 165 | 13% | 3.3% | 0.072 |
| connected_passers | 26 | 31% | 65% | 0 | 46 | 101 | 134 | 15% | 3.8% | 0.080 |
| closed_centre | 24 | 25% | 50% | 24 | 45 | 96 | 212 | 8% | 0.0% | 0.073 |
| exchange_imbalance | 18 | 44% | 61% | 6 | 45 | 101 | 111 | 17% | 5.6% | 0.087 |
| unusual_king_placement | 15 | 27% | 47% | 31 | 44 | 109 | 109 | 20% | 0.0% | 0.096 |
| rook_on_open_file | 91 | 43% | 67% | 0 | 44 | 125 | 191 | 16% | 2.2% | 0.088 |
| material_imbalance | 127 | 39% | 61% | 2 | 43 | 111 | 195 | 13% | 2.4% | 0.085 |
| locked_pawn_chain | 31 | 23% | 58% | 11 | 41 | 96 | 116 | 10% | 0.0% | 0.080 |
| passed_pawn | 98 | 45% | 69% | 0 | 41 | 116 | 195 | 15% | 3.1% | 0.079 |
| bad_bishop | 65 | 45% | 66% | 0 | 40 | 105 | 195 | 11% | 3.1% | 0.062 |
| rook_and_minor_ending | 21 | 57% | 76% | 0 | 39 | 83 | 101 | 10% | 4.8% | 0.050 |
| same_side_castling | 92 | 34% | 60% | 12 | 39 | 116 | 161 | 14% | 1.1% | 0.082 |
| hanging_piece | 45 | 44% | 62% | 0 | 38 | 134 | 175 | 13% | 0.0% | 0.086 |
| protected_passer | 41 | 37% | 68% | 0 | 38 | 95 | 134 | 10% | 2.4% | 0.059 |
| maroczy_bind | 12 | 33% | 50% | 27 | 37 | 95 | 95 | 8% | 0.0% | 0.070 |
| weak_colour_complex | 47 | 43% | 64% | 0 | 37 | 79 | 165 | 9% | 2.1% | 0.064 |
| rook_on_semi_open_file | 104 | 34% | 61% | 10 | 37 | 101 | 161 | 11% | 1.0% | 0.074 |
| open_file | 167 | 42% | 70% | 0 | 34 | 105 | 165 | 12% | 1.8% | 0.067 |
| advanced_passer | 33 | 48% | 76% | 0 | 34 | 105 | 116 | 12% | 3.0% | 0.067 |
| isolated_pawn | 172 | 38% | 67% | 0 | 33 | 101 | 161 | 10% | 1.2% | 0.065 |
| semi_open_file | 227 | 38% | 67% | 0 | 33 | 95 | 159 | 10% | 1.3% | 0.062 |
| opposite_side_castling | 21 | 62% | 81% | 0 | 32 | 62 | 72 | 5% | 4.8% | 0.033 |
| queenless_middlegame | 41 | 44% | 63% | 4 | 32 | 96 | 134 | 10% | 0.0% | 0.069 |
| king_in_centre | 48 | 33% | 60% | 16 | 32 | 76 | 95 | 4% | 0.0% | 0.057 |
| backward_pawn | 96 | 34% | 67% | 2 | 31 | 95 | 111 | 8% | 1.0% | 0.054 |
| open_centre | 91 | 47% | 68% | 0 | 31 | 79 | 161 | 9% | 1.1% | 0.061 |
| bishop_pair | 76 | 45% | 66% | 0 | 29 | 84 | 113 | 7% | 0.0% | 0.060 |
| knight_outpost | 45 | 42% | 64% | 0 | 29 | 102 | 113 | 13% | 0.0% | 0.066 |
| doubled_pawns | 94 | 46% | 71% | 0 | 27 | 84 | 113 | 7% | 1.1% | 0.052 |
| king_attack | 9 | 44% | 67% | 0 | 25 | 52 | 105 | 11% | 0.0% | 0.042 |
| isolated_queen_pawn | 30 | 40% | 77% | 0 | 20 | 78 | 101 | 7% | 0.0% | 0.042 |
| complex_ending | 10 | 60% | 70% | 0 | 20 | 52 | 111 | 10% | 0.0% | 0.046 |
| carlsbad | 22 | 36% | 77% | 4 | 17 | 44 | 82 | 5% | 0.0% | 0.037 |
| minority_attack | 10 | 40% | 80% | 4 | 16 | 44 | 82 | 0% | 0.0% | 0.031 |
| opposite_coloured_bishops | 27 | 41% | 78% | 0 | 15 | 46 | 74 | 4% | 0.0% | 0.019 |
| minor_piece_ending | 11 | 9% | 91% | 0 | 6 | 16 | 30 | 0% | 0.0% | 0.002 |
| rook_ending | 9 | 44% | 100% | 0 | 2 | 0 | 19 | 0% | 0.0% | 0.000 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| albin | 4 | 50% | 50% | 28 | 139 | 10000 | 10000 | 25% | 25.0% | 0.157 |
| ruy_lopez | 5 | 40% | 40% | 28 | 129 | 484 | 484 | 40% | 20.0% | 0.194 |
| vienna | 6 | 0% | 50% | 24 | 98 | 195 | 331 | 33% | 16.7% | 0.169 |
| philidor | 5 | 20% | 40% | 32 | 65 | 204 | 204 | 20% | 0.0% | 0.124 |
| nimzo_indian | 5 | 0% | 40% | 75 | 64 | 161 | 161 | 20% | 0.0% | 0.175 |
| kings_indian | 6 | 33% | 33% | 40 | 61 | 74 | 212 | 17% | 0.0% | 0.100 |
| benoni | 4 | 25% | 25% | 64 | 61 | 116 | 116 | 25% | 0.0% | 0.140 |
| centre_game | 4 | 25% | 50% | 18 | 56 | 191 | 191 | 25% | 0.0% | 0.126 |
| scandinavian | 5 | 40% | 80% | 0 | 53 | 243 | 243 | 20% | 0.0% | 0.104 |
| trompowsky | 5 | 0% | 60% | 4 | 53 | 165 | 165 | 20% | 0.0% | 0.120 |
| london | 5 | 20% | 20% | 57 | 49 | 78 | 78 | 0% | 0.0% | 0.084 |
| modern | 5 | 60% | 80% | 0 | 48 | 225 | 225 | 20% | 0.0% | 0.101 |
| dutch | 6 | 0% | 33% | 42 | 46 | 72 | 102 | 17% | 0.0% | 0.072 |
| sicilian_closed | 4 | 25% | 50% | 37 | 46 | 109 | 109 | 25% | 0.0% | 0.134 |
| polish | 5 | 40% | 60% | 0 | 45 | 125 | 125 | 40% | 0.0% | 0.136 |
| grunfeld | 5 | 60% | 60% | 0 | 42 | 116 | 116 | 20% | 0.0% | 0.110 |
| colle | 5 | 40% | 60% | 22 | 42 | 159 | 159 | 20% | 0.0% | 0.105 |
| queens_gambit_declined | 6 | 33% | 50% | 20 | 39 | 82 | 113 | 17% | 0.0% | 0.121 |
| italian | 5 | 20% | 60% | 25 | 39 | 95 | 95 | 0% | 0.0% | 0.059 |
| queens_indian | 5 | 20% | 60% | 15 | 34 | 105 | 105 | 20% | 0.0% | 0.079 |
| bishops_opening | 5 | 40% | 60% | 0 | 29 | 111 | 111 | 20% | 0.0% | 0.096 |
| sicilian_alapin | 5 | 20% | 60% | 21 | 29 | 52 | 52 | 0% | 0.0% | 0.056 |
| old_indian | 4 | 25% | 50% | 25 | 26 | 53 | 53 | 0% | 0.0% | 0.011 |
| kings_gambit | 4 | 25% | 75% | 6 | 24 | 83 | 83 | 0% | 0.0% | 0.046 |
| pirc | 4 | 50% | 75% | 8 | 22 | 72 | 72 | 0% | 0.0% | 0.034 |
| french | 5 | 20% | 80% | 0 | 21 | 85 | 85 | 0% | 0.0% | 0.034 |
| queens_gambit_accepted | 4 | 50% | 75% | 1 | 20 | 79 | 79 | 0% | 0.0% | 0.096 |
| nimzo_larsen | 4 | 75% | 75% | 0 | 19 | 76 | 76 | 0% | 0.0% | 0.064 |
| owens | 5 | 40% | 60% | 0 | 19 | 50 | 50 | 0% | 0.0% | 0.011 |
| bird | 4 | 25% | 75% | 6 | 18 | 62 | 62 | 0% | 0.0% | 0.009 |
| slav | 5 | 40% | 80% | 0 | 15 | 62 | 62 | 0% | 0.0% | 0.024 |
| caro_kann | 5 | 60% | 80% | 0 | 14 | 56 | 56 | 0% | 0.0% | 0.021 |
| smith_morra | 4 | 25% | 50% | 13 | 14 | 28 | 28 | 0% | 0.0% | 0.009 |
| chigorin | 4 | 0% | 75% | 0 | 12 | 46 | 46 | 0% | 0.0% | 0.005 |
| other | 5 | 40% | 80% | 12 | 11 | 26 | 26 | 0% | 0.0% | 0.003 |
| catalan | 6 | 50% | 83% | 0 | 11 | 19 | 46 | 0% | 0.0% | 0.005 |
| bogo_indian | 5 | 60% | 80% | 0 | 9 | 44 | 44 | 0% | 0.0% | 0.003 |
| reti | 5 | 40% | 80% | 0 | 8 | 29 | 29 | 0% | 0.0% | 0.003 |
| scotch | 5 | 80% | 80% | 0 | 8 | 40 | 40 | 0% | 0.0% | 0.001 |
| alekhine | 4 | 75% | 75% | 0 | 8 | 30 | 30 | 0% | 0.0% | 0.001 |
| semi_slav | 7 | 43% | 86% | 2 | 7 | 9 | 30 | 0% | 0.0% | 0.004 |
| torre | 5 | 60% | 80% | 0 | 7 | 32 | 32 | 0% | 0.0% | 0.001 |
| four_knights | 5 | 40% | 100% | 0 | 6 | 16 | 16 | 0% | 0.0% | 0.001 |
| budapest | 4 | 50% | 100% | 0 | 4 | 16 | 16 | 0% | 0.0% | 0.004 |
| english | 5 | 60% | 100% | 0 | 3 | 11 | 11 | 0% | 0.0% | 0.002 |
| sicilian | 5 | 60% | 100% | 0 | 2 | 8 | 8 | 0% | 0.0% | 0.000 |
| benko | 4 | 75% | 100% | 0 | 0 | 2 | 2 | 0% | 0.0% | 0.000 |
| petrov | 4 | 100% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| cl-000 | 10000 | e7e5 | e7e8 | 41 | albin | bad_bishop, isolated_pawn, material_imbalance, passed_pawn, queenside_majority, rook_and_minor_ending, rook_on_open_file, weak_colour_complex | `2k5/1pp1rp1p/8/1NP5/P6n/2N5/1P4bP/2KR4 b - - 0 27` |
| cl-170 | 484 | h3e6 | b2c3 | 113 | ruy_lopez | advanced_passer, backward_pawn, bad_bishop, connected_passers, exposed_king, material_imbalance, opposite_side_castling, passed_pawn, protected_passer, rook_on_open_file, space_advantage | `3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 4 41` |
| cl-201 | 331 | f8d8 | c8d8 | 143 | vienna | doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_semi_open_file, same_side_castling | `2r2rk1/pp3p1p/4P1p1/8/1p2B2R/3Q2PP/2P2PK1/2q5 b - - 1 25` |
| cl-174 | 243 | b7c7 | b7b2 | -101 | scandinavian | bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `Q7/1r3ppk/2q1p2p/5b2/2P1n3/P2B1N2/1R3PPP/2n1B1K1 b - - 3 29` |
| cl-125 | 225 | c4e3 | c4a3 | -24 | modern | backward_pawn, bad_bishop, closed_centre, king_in_centre, locked_pawn_chain, passed_pawn, protected_passer, rook_on_semi_open_file | `r3k2r/4npbp/1qp1p1p1/3pP2P/2nP1P2/PpQ1B3/1P1N2P1/1KR2N1R b kq - 4 20` |
| cl-117 | 212 | e1g1 | e3h6 | 140 | kings_indian | backward_pawn, bishop_pair, closed_centre, doubled_pawns, exposed_king, isolated_pawn, king_in_centre, locked_pawn_chain, material_imbalance, rook_on_semi_open_file | `2kr3r/pp1bn1q1/3p1npp/2pPp3/2P1P2Q/2P1B3/P2NBPP1/R3K2R w KQ - 12 16` |
| cl-144 | 204 | c4e4 | c4e2 | 24 | philidor | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, queenside_majority, rook_on_semi_open_file | `r7/pp1kNpQ1/3p4/8/2q1P3/2P3R1/PP3r2/2KR4 b - - 0 24` |
| cl-202 | 195 | e3a7 | e2d4 | -20 | vienna | bad_bishop, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, passed_pawn, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, weak_colour_complex | `3rkb1r/ppp2pp1/2b5/4P2p/4p3/2P1B1P1/PPP1N2P/R3KR2 w Qk - 2 14` |
| cl-087 | 191 | e5e6 | f1e1 | 12 | centre_game | isolated_pawn, open_centre, queenless_middlegame, rook_on_open_file, same_side_castling | `r2r3k/ppp1b1pp/2n2p2/4P3/2B2P2/2P2N2/P1b3PP/R1B2RK1 w - - 0 15` |
| cl-094 | 175 | b5h5 | b5b4 | -61 | danish_gambit | hanging_piece, isolated_pawn, rook_on_open_file, same_side_castling | `r4rk1/pp1b1ppp/2np4/1q6/P2PB3/5N1P/1P1Q1PP1/R3R1K1 b - - 0 19` |
| cl-198 | 165 | a2a1 | b8a7 | -105 | trompowsky | exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, space_advantage, weak_colour_complex | `1k1r4/1p3p1R/5N2/p1pPPQ2/b7/2P5/qP3Pr1/2K4R b - - 1 29` |
| cl-128 | 161 | d3d8 | d3a3 | 74 | nimzo_indian | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `4r1k1/pp3pnn/8/8/4PN2/P2q1P2/5Q1P/6RK b - - 1 32` |
| cl-014 | 159 | h2h4 | e5f6 | 22 | colle | isolated_pawn, pawn_ending, queenside_majority | `8/pp2k1p1/4p2p/4Pp2/8/PPK3P1/2P4P/8 w - f6 0 32` |
| cl-169 | 134 | g6h6 | g8h7 | -97 | ruy_lopez | advanced_passer, bishop_pair, connected_passers, doubled_pawns, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, protected_passer, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `1r4k1/2b3n1/p1P3r1/5pR1/BP2p3/2P1B2K/8/R7 b - - 1 39` |
| cl-149 | 125 | c5e3 | e2f3 | 49 | polish | doubled_pawns, exposed_king, isolated_pawn, isolated_queen_pawn, open_centre, rook_on_open_file, same_side_castling, space_advantage | `r2qr1k1/pp1bnpp1/5b1p/2Bp1P1P/6P1/2PB4/PP1NQP2/R4RK1 w - - 7 17` |
| cl-066 | 116 | c8d8 | c8e8 | -86 | benoni | advanced_passer, backward_pawn, exposed_king, knight_outpost, locked_pawn_chain, material_imbalance, passed_pawn, queenside_majority, rook_on_open_file, same_side_castling | `2r3k1/3q3p/3p1P1n/1p1Pr1p1/2p3P1/1nP4P/2B2Q1K/3NRR2 b - - 2 30` |
| cl-110 | 116 | f4g4 | f4f8 | 29 | grunfeld | bad_bishop, hanging_piece, isolated_pawn, maroczy_bind, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `r4rk1/7p/6p1/p1q5/BpPnPR2/8/PQ4PP/2R4K w - - 1 28` |
| cl-158 | 113 | e8c8 | e7d6 | 25 | queens_gambit_declined | backward_pawn, bishop_pair, carlsbad, doubled_pawns, isolated_pawn, knight_outpost, material_imbalance, queenless_middlegame, rook_on_semi_open_file | `r3k2r/1p2bp2/2p3b1/p2pNp1p/N2PnP2/P2BP1P1/1P5P/2R1K1R1 b kq - 1 20` |
| cl-007 | 111 | g4g6 | d6d5 | -41 | bishops_opening | backward_pawn, complex_ending, connected_passers, doubled_pawns, exchange_imbalance, material_imbalance, passed_pawn, rook_on_semi_open_file | `6k1/1p6/3p4/p1p4r/P2pPBq1/3P4/1PP3PP/5QK1 b - - 4 29` |
| cl-189 | 109 | e3g5 | d4d5 | 32 | sicilian_closed | backward_pawn, bad_bishop, exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, unusual_king_placement, weak_colour_complex | `8/5pkp/4p1p1/1q1nP3/3R4/P3BQPK/5P1P/6r1 w - - 17 44` |
| cl-162 | 105 | g1h1 | h2h3 | 17 | queens_indian | advanced_passer, backward_pawn, bad_bishop, king_attack, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, space_advantage | `5rk1/3PQ1pp/1q6/1p6/2p5/2Pp4/3NbPPP/4R1K1 w - - 3 26` |
| cl-096 | 102 | e7e6 | f5f4 | -39 | dutch | exposed_king, isolated_pawn, knight_outpost, rook_on_open_file, same_side_castling, unusual_king_placement | `4r3/R2bp2p/3p1qpk/2nB1p2/2PN3P/4P1P1/5P2/1Q4K1 b - - 2 32` |
| cl-038 | 101 | h5e2 | g8b8 | -76 | polish | connected_passers, exchange_imbalance, isolated_pawn, isolated_queen_pawn, knight_outpost, material_imbalance, opposite_coloured_bishops, passed_pawn, rook_and_minor_ending, rook_on_semi_open_file | `6R1/8/3k4/pp1p2pB/1n5b/4K2P/8/8 w - - 0 40` |
| cl-069 | 96 | b7b5 | f8d7 | 19 | benoni | backward_pawn, closed_centre, doubled_pawns, locked_pawn_chain, material_imbalance, queenless_middlegame | `r3kn1r/1p2bpp1/p2p3p/2pPp3/N1P1P2P/4PN2/PP4P1/R3K2R b KQkq - 0 15` |
| cl-107 | 95 | g7f6 | g7e5 | 128 | grunfeld | bishop_pair, doubled_pawns, exposed_king, isolated_pawn, king_in_centre, material_imbalance, passed_pawn, protected_passer, rook_on_open_file, rook_on_semi_open_file | `3q1rk1/1p3pbp/8/3P4/2PNp1P1/1P2B3/3R1PP1/r2BK2R b K - 4 24` |
