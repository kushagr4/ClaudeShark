# Move quality: competition_like_v1 at depth 6

Engine: champions\v0_7_mopup, depth 6. Suite: corpus\competition_like_v1.jsonl (competition_like v1, hash `6a8111f22f9ea393`, 240 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 240 | 37% | 66% | 2 | 35 | 95 | 165 | 10% | 1.7% | 0.064 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 60 | 40% | 83% | 0 | 20 | 48 | 83 | 5% | 1.7% | 0.026 |
| middlegame | 144 | 35% | 58% | 12 | 46 | 125 | 204 | 15% | 2.1% | 0.090 |
| opening | 36 | 39% | 69% | 12 | 18 | 55 | 57 | 0% | 0.0% | 0.025 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| unusual_king_placement | 15 | 27% | 40% | 32 | 65 | 134 | 134 | 27% | 6.7% | 0.129 |
| king_attack | 9 | 44% | 56% | 0 | 59 | 105 | 334 | 22% | 11.1% | 0.097 |
| exposed_king | 54 | 37% | 52% | 15 | 58 | 165 | 212 | 20% | 1.9% | 0.112 |
| space_advantage | 30 | 30% | 57% | 16 | 55 | 125 | 251 | 17% | 3.3% | 0.089 |
| rook_on_open_file | 91 | 41% | 65% | 0 | 50 | 161 | 243 | 19% | 3.3% | 0.098 |
| queenside_majority | 46 | 39% | 61% | 0 | 48 | 134 | 195 | 17% | 2.2% | 0.100 |
| passed_pawn | 98 | 42% | 66% | 0 | 46 | 134 | 243 | 16% | 4.1% | 0.085 |
| material_imbalance | 127 | 39% | 61% | 2 | 46 | 116 | 212 | 14% | 3.1% | 0.088 |
| same_side_castling | 92 | 34% | 58% | 14 | 45 | 125 | 175 | 16% | 2.2% | 0.093 |
| closed_centre | 24 | 25% | 50% | 25 | 44 | 95 | 212 | 8% | 0.0% | 0.070 |
| advanced_passer | 33 | 45% | 73% | 0 | 43 | 116 | 134 | 15% | 6.1% | 0.081 |
| connected_passers | 26 | 31% | 65% | 0 | 41 | 83 | 134 | 12% | 3.8% | 0.061 |
| bad_bishop | 65 | 40% | 65% | 2 | 41 | 105 | 195 | 11% | 3.1% | 0.062 |
| locked_pawn_chain | 31 | 26% | 58% | 15 | 41 | 95 | 116 | 10% | 0.0% | 0.077 |
| queenless_middlegame | 41 | 41% | 61% | 9 | 39 | 113 | 191 | 12% | 2.4% | 0.079 |
| rook_on_semi_open_file | 104 | 33% | 61% | 12 | 39 | 101 | 195 | 11% | 1.9% | 0.075 |
| maroczy_bind | 12 | 25% | 50% | 31 | 39 | 95 | 95 | 8% | 0.0% | 0.070 |
| rook_and_minor_ending | 21 | 48% | 76% | 0 | 39 | 83 | 101 | 10% | 4.8% | 0.048 |
| exchange_imbalance | 18 | 50% | 67% | 0 | 39 | 83 | 101 | 11% | 5.6% | 0.062 |
| hanging_piece | 45 | 42% | 60% | 0 | 38 | 134 | 175 | 13% | 0.0% | 0.087 |
| weak_colour_complex | 47 | 38% | 64% | 6 | 38 | 79 | 165 | 9% | 2.1% | 0.064 |
| protected_passer | 41 | 34% | 66% | 0 | 38 | 95 | 134 | 10% | 2.4% | 0.059 |
| open_file | 167 | 40% | 69% | 0 | 37 | 109 | 191 | 13% | 2.4% | 0.070 |
| isolated_pawn | 172 | 37% | 66% | 0 | 37 | 109 | 175 | 12% | 1.7% | 0.070 |
| open_centre | 91 | 46% | 66% | 0 | 37 | 116 | 204 | 11% | 2.2% | 0.072 |
| semi_open_file | 227 | 37% | 66% | 2 | 35 | 95 | 165 | 10% | 1.8% | 0.064 |
| opposite_side_castling | 21 | 62% | 81% | 0 | 32 | 62 | 72 | 5% | 4.8% | 0.033 |
| bishop_pair | 76 | 45% | 66% | 0 | 32 | 85 | 134 | 8% | 0.0% | 0.065 |
| king_in_centre | 48 | 33% | 60% | 16 | 32 | 76 | 95 | 4% | 0.0% | 0.057 |
| backward_pawn | 96 | 34% | 67% | 6 | 31 | 85 | 109 | 7% | 1.0% | 0.049 |
| opposite_coloured_bishops | 27 | 33% | 70% | 0 | 29 | 56 | 101 | 7% | 3.7% | 0.037 |
| doubled_pawns | 94 | 46% | 70% | 0 | 29 | 80 | 125 | 7% | 2.1% | 0.051 |
| knight_outpost | 45 | 42% | 67% | 0 | 29 | 102 | 113 | 13% | 0.0% | 0.066 |
| isolated_queen_pawn | 30 | 37% | 77% | 0 | 20 | 78 | 101 | 7% | 0.0% | 0.042 |
| carlsbad | 22 | 41% | 82% | 2 | 16 | 44 | 82 | 5% | 0.0% | 0.036 |
| minority_attack | 10 | 40% | 80% | 4 | 16 | 44 | 82 | 0% | 0.0% | 0.031 |
| minor_piece_ending | 11 | 9% | 82% | 0 | 10 | 30 | 56 | 0% | 0.0% | 0.003 |
| complex_ending | 10 | 70% | 80% | 0 | 9 | 26 | 52 | 0% | 0.0% | 0.002 |
| rook_ending | 9 | 44% | 100% | 0 | 2 | 0 | 19 | 0% | 0.0% | 0.000 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| albin | 4 | 50% | 50% | 28 | 139 | 10000 | 10000 | 25% | 25.0% | 0.157 |
| ruy_lopez | 5 | 60% | 60% | 0 | 124 | 484 | 484 | 40% | 20.0% | 0.193 |
| vienna | 6 | 0% | 50% | 24 | 98 | 195 | 331 | 33% | 16.7% | 0.169 |
| dutch | 6 | 0% | 17% | 50 | 94 | 102 | 334 | 33% | 16.7% | 0.145 |
| philidor | 5 | 20% | 40% | 32 | 65 | 204 | 204 | 20% | 0.0% | 0.124 |
| nimzo_indian | 5 | 0% | 40% | 75 | 64 | 161 | 161 | 20% | 0.0% | 0.175 |
| kings_indian | 6 | 33% | 33% | 40 | 61 | 74 | 212 | 17% | 0.0% | 0.100 |
| centre_game | 4 | 25% | 50% | 18 | 56 | 191 | 191 | 25% | 0.0% | 0.126 |
| trompowsky | 5 | 0% | 60% | 19 | 56 | 165 | 165 | 20% | 0.0% | 0.121 |
| scandinavian | 5 | 40% | 80% | 0 | 53 | 243 | 243 | 20% | 0.0% | 0.104 |
| benoni | 4 | 25% | 25% | 46 | 52 | 116 | 116 | 25% | 0.0% | 0.120 |
| london | 5 | 0% | 20% | 57 | 49 | 78 | 78 | 0% | 0.0% | 0.084 |
| modern | 5 | 60% | 80% | 0 | 48 | 225 | 225 | 20% | 0.0% | 0.101 |
| colle | 5 | 20% | 40% | 27 | 47 | 159 | 159 | 20% | 0.0% | 0.108 |
| sicilian_closed | 4 | 25% | 50% | 37 | 46 | 109 | 109 | 25% | 0.0% | 0.134 |
| polish | 5 | 40% | 60% | 0 | 45 | 125 | 125 | 40% | 0.0% | 0.136 |
| grunfeld | 5 | 60% | 60% | 0 | 42 | 116 | 116 | 20% | 0.0% | 0.110 |
| queens_gambit_declined | 6 | 33% | 50% | 20 | 39 | 82 | 113 | 17% | 0.0% | 0.121 |
| italian | 5 | 20% | 60% | 25 | 39 | 95 | 95 | 0% | 0.0% | 0.059 |
| queens_indian | 5 | 20% | 60% | 15 | 34 | 105 | 105 | 20% | 0.0% | 0.079 |
| sicilian_alapin | 5 | 20% | 60% | 21 | 29 | 52 | 52 | 0% | 0.0% | 0.056 |
| old_indian | 4 | 25% | 50% | 25 | 26 | 53 | 53 | 0% | 0.0% | 0.011 |
| kings_gambit | 4 | 25% | 75% | 6 | 24 | 83 | 83 | 0% | 0.0% | 0.046 |
| pirc | 4 | 50% | 75% | 8 | 22 | 72 | 72 | 0% | 0.0% | 0.034 |
| french | 5 | 20% | 80% | 0 | 21 | 85 | 85 | 0% | 0.0% | 0.034 |
| queens_gambit_accepted | 4 | 50% | 75% | 1 | 20 | 79 | 79 | 0% | 0.0% | 0.096 |
| nimzo_larsen | 4 | 75% | 75% | 0 | 19 | 76 | 76 | 0% | 0.0% | 0.064 |
| owens | 5 | 40% | 60% | 0 | 19 | 50 | 50 | 0% | 0.0% | 0.011 |
| bird | 4 | 25% | 75% | 6 | 18 | 62 | 62 | 0% | 0.0% | 0.009 |
| slav | 5 | 20% | 80% | 6 | 16 | 62 | 62 | 0% | 0.0% | 0.024 |
| caro_kann | 5 | 60% | 80% | 0 | 14 | 56 | 56 | 0% | 0.0% | 0.021 |
| budapest | 4 | 75% | 75% | 0 | 14 | 56 | 56 | 0% | 0.0% | 0.007 |
| bogo_indian | 5 | 20% | 80% | 0 | 14 | 44 | 44 | 0% | 0.0% | 0.003 |
| smith_morra | 4 | 25% | 50% | 13 | 14 | 28 | 28 | 0% | 0.0% | 0.009 |
| chigorin | 4 | 0% | 75% | 0 | 12 | 46 | 46 | 0% | 0.0% | 0.005 |
| other | 5 | 40% | 80% | 12 | 11 | 26 | 26 | 0% | 0.0% | 0.003 |
| catalan | 6 | 50% | 83% | 0 | 11 | 19 | 46 | 0% | 0.0% | 0.005 |
| reti | 5 | 40% | 80% | 0 | 8 | 29 | 29 | 0% | 0.0% | 0.003 |
| scotch | 5 | 80% | 80% | 0 | 8 | 40 | 40 | 0% | 0.0% | 0.001 |
| four_knights | 5 | 40% | 100% | 11 | 8 | 16 | 16 | 0% | 0.0% | 0.001 |
| alekhine | 4 | 75% | 75% | 0 | 8 | 30 | 30 | 0% | 0.0% | 0.001 |
| bishops_opening | 5 | 60% | 80% | 0 | 7 | 36 | 36 | 0% | 0.0% | 0.007 |
| semi_slav | 7 | 43% | 86% | 2 | 7 | 9 | 30 | 0% | 0.0% | 0.004 |
| torre | 5 | 60% | 80% | 0 | 6 | 32 | 32 | 0% | 0.0% | 0.001 |
| english | 5 | 60% | 100% | 0 | 3 | 11 | 11 | 0% | 0.0% | 0.002 |
| sicilian | 5 | 60% | 100% | 0 | 2 | 8 | 8 | 0% | 0.0% | 0.000 |
| benko | 4 | 75% | 100% | 0 | 0 | 2 | 2 | 0% | 0.0% | 0.000 |
| petrov | 4 | 100% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| cl-000 | 10000 | e7e5 | e7e8 | 26 | albin | bad_bishop, isolated_pawn, material_imbalance, passed_pawn, queenside_majority, rook_and_minor_ending, rook_on_open_file, weak_colour_complex | `2k5/1pp1rp1p/8/1NP5/P6n/2N5/1P4bP/2KR4 b - - 0 27` |
| cl-170 | 484 | h3e6 | b2c3 | 113 | ruy_lopez | advanced_passer, backward_pawn, bad_bishop, connected_passers, exposed_king, material_imbalance, opposite_side_castling, passed_pawn, protected_passer, rook_on_open_file, space_advantage | `3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 4 41` |
| cl-097 | 334 | c1b3 | g2g4 | 25 | dutch | advanced_passer, doubled_pawns, isolated_pawn, king_attack, material_imbalance, open_centre, opposite_coloured_bishops, passed_pawn, queenless_middlegame, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `r2r4/4R3/2k1p2p/2p1Bbp1/8/2N1p3/1PP3PP/1KN5 w - - 0 25` |
| cl-201 | 331 | f8d8 | c8d8 | 143 | vienna | doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_semi_open_file, same_side_castling | `2r2rk1/pp3p1p/4P1p1/8/1p2B2R/3Q2PP/2P2PK1/2q5 b - - 1 25` |
| cl-151 | 251 | f1f5 | d8f8 | -157 | ponziani | bishop_pair, exposed_king, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling, space_advantage | `3r3k/p2q2p1/P1p1R2p/1pb1P3/8/1BP1n1BP/1P2Q1PK/4Rr2 b - - 4 33` |
| cl-174 | 243 | b7c7 | b7b2 | -101 | scandinavian | bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `Q7/1r3ppk/2q1p2p/5b2/2P1n3/P2B1N2/1R3PPP/2n1B1K1 b - - 3 29` |
| cl-125 | 225 | c4e3 | c4a3 | -24 | modern | backward_pawn, bad_bishop, closed_centre, king_in_centre, locked_pawn_chain, passed_pawn, protected_passer, rook_on_semi_open_file | `r3k2r/4npbp/1qp1p1p1/3pP2P/2nP1P2/PpQ1B3/1P1N2P1/1KR2N1R b kq - 4 20` |
| cl-117 | 212 | e1g1 | e3h6 | 145 | kings_indian | backward_pawn, bishop_pair, closed_centre, doubled_pawns, exposed_king, isolated_pawn, king_in_centre, locked_pawn_chain, material_imbalance, rook_on_semi_open_file | `2kr3r/pp1bn1q1/3p1npp/2pPp3/2P1P2Q/2P1B3/P2NBPP1/R3K2R w KQ - 12 16` |
| cl-144 | 204 | c4e4 | c4e2 | 32 | philidor | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, queenside_majority, rook_on_semi_open_file | `r7/pp1kNpQ1/3p4/8/2q1P3/2P3R1/PP3r2/2KR4 b - - 0 24` |
| cl-202 | 195 | e3a7 | e2d4 | -14 | vienna | bad_bishop, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, passed_pawn, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, weak_colour_complex | `3rkb1r/ppp2pp1/2b5/4P2p/4p3/2P1B1P1/PPP1N2P/R3KR2 w Qk - 2 14` |
| cl-087 | 191 | e5e6 | f1e1 | 12 | centre_game | isolated_pawn, open_centre, queenless_middlegame, rook_on_open_file, same_side_castling | `r2r3k/ppp1b1pp/2n2p2/4P3/2B2P2/2P2N2/P1b3PP/R1B2RK1 w - - 0 15` |
| cl-094 | 175 | b5h5 | b5b4 | -61 | danish_gambit | hanging_piece, isolated_pawn, rook_on_open_file, same_side_castling | `r4rk1/pp1b1ppp/2np4/1q6/P2PB3/5N1P/1P1Q1PP1/R3R1K1 b - - 0 19` |
| cl-198 | 165 | a2a1 | b8a7 | -105 | trompowsky | exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, space_advantage, weak_colour_complex | `1k1r4/1p3p1R/5N2/p1pPPQ2/b7/2P5/qP3Pr1/2K4R b - - 1 29` |
| cl-128 | 161 | d3d8 | d3a3 | 100 | nimzo_indian | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `4r1k1/pp3pnn/8/8/4PN2/P2q1P2/5Q1P/6RK b - - 1 32` |
| cl-014 | 159 | h2h4 | e5f6 | 22 | colle | isolated_pawn, pawn_ending, queenside_majority | `8/pp2k1p1/4p2p/4Pp2/8/PPK3P1/2P4P/8 w - f6 0 32` |
| cl-169 | 134 | g6h6 | g8h7 | -103 | ruy_lopez | advanced_passer, bishop_pair, connected_passers, doubled_pawns, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, protected_passer, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `1r4k1/2b3n1/p1P3r1/5pR1/BP2p3/2P1B2K/8/R7 b - - 1 39` |
| cl-149 | 125 | c5e3 | e2f3 | 49 | polish | doubled_pawns, exposed_king, isolated_pawn, isolated_queen_pawn, open_centre, rook_on_open_file, same_side_castling, space_advantage | `r2qr1k1/pp1bnpp1/5b1p/2Bp1P1P/6P1/2PB4/PP1NQP2/R4RK1 w - - 7 17` |
| cl-066 | 116 | c8d8 | c8e8 | -88 | benoni | advanced_passer, backward_pawn, exposed_king, knight_outpost, locked_pawn_chain, material_imbalance, passed_pawn, queenside_majority, rook_on_open_file, same_side_castling | `2r3k1/3q3p/3p1P1n/1p1Pr1p1/2p3P1/1nP4P/2B2Q1K/3NRR2 b - - 2 30` |
| cl-110 | 116 | f4g4 | f4f8 | 29 | grunfeld | bad_bishop, hanging_piece, isolated_pawn, maroczy_bind, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `r4rk1/7p/6p1/p1q5/BpPnPR2/8/PQ4PP/2R4K w - - 1 28` |
| cl-158 | 113 | e8c8 | e7d6 | 19 | queens_gambit_declined | backward_pawn, bishop_pair, carlsbad, doubled_pawns, isolated_pawn, knight_outpost, material_imbalance, queenless_middlegame, rook_on_semi_open_file | `r3k2r/1p2bp2/2p3b1/p2pNp1p/N2PnP2/P2BP1P1/1P5P/2R1K1R1 b kq - 1 20` |
| cl-189 | 109 | e3g5 | d4d5 | 32 | sicilian_closed | backward_pawn, bad_bishop, exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, unusual_king_placement, weak_colour_complex | `8/5pkp/4p1p1/1q1nP3/3R4/P3BQPK/5P1P/6r1 w - - 17 44` |
| cl-162 | 105 | g1h1 | h2h3 | 17 | queens_indian | advanced_passer, backward_pawn, bad_bishop, king_attack, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, space_advantage | `5rk1/3PQ1pp/1q6/1p6/2p5/2Pp4/3NbPPP/4R1K1 w - - 3 26` |
| cl-096 | 102 | e7e6 | f5f4 | -39 | dutch | exposed_king, isolated_pawn, knight_outpost, rook_on_open_file, same_side_castling, unusual_king_placement | `4r3/R2bp2p/3p1qpk/2nB1p2/2PN3P/4P1P1/5P2/1Q4K1 b - - 2 32` |
| cl-038 | 101 | h5e2 | g8b8 | -73 | polish | connected_passers, exchange_imbalance, isolated_pawn, isolated_queen_pawn, knight_outpost, material_imbalance, opposite_coloured_bishops, passed_pawn, rook_and_minor_ending, rook_on_semi_open_file | `6R1/8/3k4/pp1p2pB/1n5b/4K2P/8/8 w - - 0 40` |
| cl-107 | 95 | g7f6 | g7e5 | 128 | grunfeld | bishop_pair, doubled_pawns, exposed_king, isolated_pawn, king_in_centre, material_imbalance, passed_pawn, protected_passer, rook_on_open_file, rook_on_semi_open_file | `3q1rk1/1p3pbp/8/3P4/2PNp1P1/1P2B3/3R1PP1/r2BK2R b K - 4 24` |
