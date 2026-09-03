# Move quality: competition_like_v1 at depth 6

Engine: C:\Users\epick\AppData\Local\Temp\claude\C--Users-epick-Documents-ClaudeShark\e3813b42-0a37-4aea-86be-348b96190e38\scratchpad\engines\scale_margins, depth 6. Suite: corpus\competition_like_v1.jsonl (competition_like v1, hash `6a8111f22f9ea393`, 240 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 240 | 35% | 65% | 7 | 34 | 95 | 159 | 10% | 1.2% | 0.063 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 60 | 38% | 85% | 0 | 20 | 40 | 83 | 5% | 1.7% | 0.030 |
| middlegame | 144 | 35% | 58% | 14 | 43 | 116 | 191 | 15% | 1.4% | 0.085 |
| opening | 36 | 31% | 61% | 20 | 23 | 57 | 61 | 0% | 0.0% | 0.028 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| space_advantage | 30 | 37% | 57% | 10 | 54 | 125 | 251 | 17% | 3.3% | 0.089 |
| exposed_king | 54 | 39% | 56% | 12 | 52 | 161 | 204 | 19% | 1.9% | 0.099 |
| queenside_majority | 46 | 39% | 63% | 0 | 49 | 134 | 195 | 20% | 2.2% | 0.102 |
| rook_on_open_file | 91 | 38% | 63% | 0 | 49 | 134 | 195 | 19% | 2.2% | 0.098 |
| unusual_king_placement | 15 | 20% | 47% | 31 | 45 | 109 | 109 | 20% | 0.0% | 0.096 |
| connected_passers | 26 | 35% | 69% | 0 | 44 | 107 | 135 | 15% | 3.8% | 0.072 |
| material_imbalance | 127 | 35% | 61% | 12 | 44 | 113 | 195 | 13% | 2.4% | 0.085 |
| passed_pawn | 98 | 43% | 68% | 0 | 44 | 134 | 225 | 16% | 3.1% | 0.082 |
| same_side_castling | 92 | 33% | 58% | 19 | 43 | 116 | 165 | 16% | 1.1% | 0.091 |
| bad_bishop | 65 | 34% | 62% | 11 | 43 | 105 | 195 | 11% | 3.1% | 0.062 |
| rook_and_minor_ending | 21 | 43% | 76% | 0 | 42 | 83 | 135 | 10% | 4.8% | 0.059 |
| exchange_imbalance | 18 | 44% | 67% | 0 | 39 | 83 | 135 | 11% | 5.6% | 0.066 |
| hanging_piece | 45 | 40% | 62% | 1 | 38 | 134 | 175 | 13% | 0.0% | 0.086 |
| protected_passer | 41 | 37% | 68% | 0 | 38 | 105 | 134 | 12% | 2.4% | 0.061 |
| maroczy_bind | 12 | 25% | 50% | 26 | 38 | 95 | 95 | 8% | 0.0% | 0.068 |
| open_file | 167 | 37% | 68% | 0 | 37 | 109 | 175 | 13% | 1.8% | 0.071 |
| weak_colour_complex | 47 | 40% | 66% | 0 | 37 | 79 | 165 | 9% | 2.1% | 0.063 |
| opposite_side_castling | 21 | 52% | 76% | 0 | 36 | 62 | 109 | 10% | 4.8% | 0.045 |
| open_centre | 91 | 40% | 65% | 11 | 36 | 109 | 191 | 11% | 1.1% | 0.070 |
| isolated_pawn | 172 | 34% | 65% | 6 | 36 | 109 | 161 | 12% | 1.2% | 0.068 |
| advanced_passer | 33 | 48% | 76% | 0 | 35 | 107 | 116 | 15% | 3.0% | 0.070 |
| semi_open_file | 227 | 35% | 65% | 7 | 35 | 95 | 159 | 10% | 1.3% | 0.063 |
| queenless_middlegame | 41 | 39% | 63% | 14 | 34 | 109 | 134 | 12% | 0.0% | 0.076 |
| rook_on_semi_open_file | 104 | 34% | 62% | 9 | 34 | 95 | 135 | 10% | 1.0% | 0.065 |
| bishop_pair | 76 | 42% | 64% | 4 | 32 | 85 | 113 | 8% | 0.0% | 0.065 |
| closed_centre | 24 | 29% | 54% | 18 | 31 | 60 | 95 | 4% | 0.0% | 0.037 |
| knight_outpost | 45 | 40% | 62% | 9 | 31 | 109 | 116 | 13% | 0.0% | 0.068 |
| locked_pawn_chain | 31 | 29% | 61% | 2 | 30 | 73 | 95 | 6% | 0.0% | 0.052 |
| king_in_centre | 48 | 31% | 56% | 21 | 30 | 62 | 95 | 2% | 0.0% | 0.045 |
| backward_pawn | 96 | 34% | 67% | 4 | 29 | 85 | 109 | 7% | 1.0% | 0.048 |
| minority_attack | 10 | 30% | 60% | 12 | 27 | 59 | 82 | 0% | 0.0% | 0.064 |
| doubled_pawns | 94 | 44% | 71% | 0 | 26 | 76 | 109 | 6% | 1.1% | 0.046 |
| king_attack | 9 | 44% | 67% | 0 | 25 | 52 | 105 | 11% | 0.0% | 0.042 |
| isolated_queen_pawn | 30 | 30% | 70% | 6 | 25 | 78 | 125 | 7% | 0.0% | 0.050 |
| carlsbad | 22 | 36% | 68% | 9 | 23 | 59 | 82 | 5% | 0.0% | 0.053 |
| opposite_coloured_bishops | 27 | 37% | 78% | 0 | 17 | 46 | 74 | 4% | 0.0% | 0.025 |
| complex_ending | 10 | 50% | 80% | 0 | 9 | 26 | 52 | 0% | 0.0% | 0.002 |
| minor_piece_ending | 11 | 9% | 91% | 0 | 6 | 16 | 30 | 0% | 0.0% | 0.002 |
| rook_ending | 9 | 56% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| albin | 4 | 50% | 50% | 28 | 139 | 10000 | 10000 | 25% | 25.0% | 0.157 |
| ruy_lopez | 5 | 60% | 60% | 0 | 124 | 484 | 484 | 40% | 20.0% | 0.193 |
| vienna | 6 | 17% | 50% | 24 | 96 | 195 | 331 | 33% | 16.7% | 0.169 |
| scandinavian | 5 | 20% | 60% | 21 | 75 | 243 | 243 | 40% | 0.0% | 0.176 |
| philidor | 5 | 20% | 40% | 32 | 65 | 204 | 204 | 20% | 0.0% | 0.124 |
| trompowsky | 5 | 0% | 60% | 19 | 56 | 165 | 165 | 20% | 0.0% | 0.121 |
| queens_gambit_declined | 6 | 0% | 33% | 49 | 53 | 82 | 113 | 17% | 0.0% | 0.149 |
| polish | 5 | 20% | 60% | 0 | 52 | 135 | 135 | 40% | 0.0% | 0.170 |
| centre_game | 4 | 25% | 75% | 8 | 52 | 191 | 191 | 25% | 0.0% | 0.125 |
| sicilian_closed | 4 | 25% | 50% | 50 | 52 | 109 | 109 | 25% | 0.0% | 0.135 |
| benoni | 4 | 25% | 25% | 46 | 52 | 116 | 116 | 25% | 0.0% | 0.120 |
| london | 5 | 0% | 20% | 57 | 49 | 78 | 78 | 0% | 0.0% | 0.084 |
| modern | 5 | 60% | 80% | 0 | 48 | 225 | 225 | 20% | 0.0% | 0.101 |
| nimzo_indian | 5 | 20% | 60% | 2 | 48 | 161 | 161 | 20% | 0.0% | 0.153 |
| dutch | 6 | 0% | 33% | 42 | 47 | 76 | 102 | 17% | 0.0% | 0.074 |
| italian | 5 | 20% | 40% | 31 | 45 | 95 | 95 | 0% | 0.0% | 0.066 |
| grunfeld | 5 | 60% | 60% | 0 | 42 | 116 | 116 | 20% | 0.0% | 0.110 |
| colle | 5 | 40% | 60% | 22 | 42 | 159 | 159 | 20% | 0.0% | 0.105 |
| queens_indian | 5 | 20% | 60% | 15 | 33 | 105 | 105 | 20% | 0.0% | 0.075 |
| sicilian_alapin | 5 | 20% | 60% | 21 | 29 | 52 | 52 | 0% | 0.0% | 0.056 |
| caro_kann | 5 | 40% | 60% | 16 | 27 | 61 | 61 | 0% | 0.0% | 0.027 |
| kings_indian | 6 | 50% | 50% | 14 | 24 | 42 | 74 | 0% | 0.0% | 0.017 |
| kings_gambit | 4 | 25% | 75% | 6 | 24 | 83 | 83 | 0% | 0.0% | 0.046 |
| bogo_indian | 5 | 20% | 60% | 24 | 21 | 44 | 44 | 0% | 0.0% | 0.005 |
| old_indian | 4 | 50% | 50% | 16 | 21 | 53 | 53 | 0% | 0.0% | 0.010 |
| queens_gambit_accepted | 4 | 50% | 75% | 1 | 20 | 79 | 79 | 0% | 0.0% | 0.096 |
| owens | 5 | 20% | 60% | 0 | 19 | 50 | 50 | 0% | 0.0% | 0.011 |
| slav | 5 | 20% | 80% | 14 | 18 | 62 | 62 | 0% | 0.0% | 0.024 |
| bird | 4 | 25% | 75% | 6 | 18 | 62 | 62 | 0% | 0.0% | 0.009 |
| french | 5 | 40% | 80% | 0 | 17 | 85 | 85 | 0% | 0.0% | 0.034 |
| four_knights | 5 | 20% | 80% | 12 | 16 | 37 | 37 | 0% | 0.0% | 0.005 |
| pirc | 4 | 50% | 75% | 8 | 14 | 39 | 39 | 0% | 0.0% | 0.008 |
| alekhine | 4 | 50% | 75% | 12 | 14 | 30 | 30 | 0% | 0.0% | 0.002 |
| smith_morra | 4 | 25% | 50% | 13 | 14 | 28 | 28 | 0% | 0.0% | 0.009 |
| semi_slav | 7 | 43% | 71% | 9 | 12 | 30 | 39 | 0% | 0.0% | 0.008 |
| catalan | 6 | 33% | 83% | 4 | 12 | 19 | 46 | 0% | 0.0% | 0.006 |
| english | 5 | 80% | 80% | 0 | 12 | 58 | 58 | 0% | 0.0% | 0.034 |
| chigorin | 4 | 0% | 75% | 0 | 12 | 46 | 46 | 0% | 0.0% | 0.005 |
| nimzo_larsen | 4 | 50% | 75% | 2 | 11 | 40 | 40 | 0% | 0.0% | 0.020 |
| other | 5 | 40% | 80% | 12 | 11 | 26 | 26 | 0% | 0.0% | 0.003 |
| reti | 5 | 40% | 80% | 0 | 8 | 29 | 29 | 0% | 0.0% | 0.003 |
| scotch | 5 | 80% | 80% | 0 | 8 | 40 | 40 | 0% | 0.0% | 0.001 |
| bishops_opening | 5 | 60% | 80% | 0 | 7 | 36 | 36 | 0% | 0.0% | 0.007 |
| torre | 5 | 60% | 80% | 0 | 6 | 32 | 32 | 0% | 0.0% | 0.001 |
| budapest | 4 | 75% | 100% | 0 | 4 | 16 | 16 | 0% | 0.0% | 0.004 |
| sicilian | 5 | 60% | 100% | 0 | 2 | 8 | 8 | 0% | 0.0% | 0.000 |
| benko | 4 | 75% | 100% | 0 | 0 | 2 | 2 | 0% | 0.0% | 0.000 |
| petrov | 4 | 100% | 100% | 0 | 0 | 0 | 0 | 0% | 0.0% | 0.000 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| cl-000 | 10000 | e7e5 | e7e8 | 36 | albin | bad_bishop, isolated_pawn, material_imbalance, passed_pawn, queenside_majority, rook_and_minor_ending, rook_on_open_file, weak_colour_complex | `2k5/1pp1rp1p/8/1NP5/P6n/2N5/1P4bP/2KR4 b - - 0 27` |
| cl-170 | 484 | h3e6 | b2c3 | 194 | ruy_lopez | advanced_passer, backward_pawn, bad_bishop, connected_passers, exposed_king, material_imbalance, opposite_side_castling, passed_pawn, protected_passer, rook_on_open_file, space_advantage | `3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 4 41` |
| cl-201 | 331 | f8d8 | c8d8 | 213 | vienna | doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_semi_open_file, same_side_castling | `2r2rk1/pp3p1p/4P1p1/8/1p2B2R/3Q2PP/2P2PK1/2q5 b - - 1 25` |
| cl-151 | 251 | f1f5 | d8f8 | -212 | ponziani | bishop_pair, exposed_king, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling, space_advantage | `3r3k/p2q2p1/P1p1R2p/1pb1P3/8/1BP1n1BP/1P2Q1PK/4Rr2 b - - 4 33` |
| cl-174 | 243 | b7c7 | b7b2 | -154 | scandinavian | bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `Q7/1r3ppk/2q1p2p/5b2/2P1n3/P2B1N2/1R3PPP/2n1B1K1 b - - 3 29` |
| cl-125 | 225 | c4e3 | c4a3 | -11 | modern | backward_pawn, bad_bishop, closed_centre, king_in_centre, locked_pawn_chain, passed_pawn, protected_passer, rook_on_semi_open_file | `r3k2r/4npbp/1qp1p1p1/3pP2P/2nP1P2/PpQ1B3/1P1N2P1/1KR2N1R b kq - 4 20` |
| cl-144 | 204 | c4e4 | c4e2 | 49 | philidor | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, queenside_majority, rook_on_semi_open_file | `r7/pp1kNpQ1/3p4/8/2q1P3/2P3R1/PP3r2/2KR4 b - - 0 24` |
| cl-202 | 195 | e3a7 | e2d4 | 16 | vienna | bad_bishop, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, passed_pawn, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, weak_colour_complex | `3rkb1r/ppp2pp1/2b5/4P2p/4p3/2P1B1P1/PPP1N2P/R3KR2 w Qk - 2 14` |
| cl-087 | 191 | e5e6 | f1e1 | 12 | centre_game | isolated_pawn, open_centre, queenless_middlegame, rook_on_open_file, same_side_castling | `r2r3k/ppp1b1pp/2n2p2/4P3/2B2P2/2P2N2/P1b3PP/R1B2RK1 w - - 0 15` |
| cl-094 | 175 | b5h5 | b5b4 | -64 | danish_gambit | hanging_piece, isolated_pawn, rook_on_open_file, same_side_castling | `r4rk1/pp1b1ppp/2np4/1q6/P2PB3/5N1P/1P1Q1PP1/R3R1K1 b - - 0 19` |
| cl-198 | 165 | a2a1 | b8a7 | -136 | trompowsky | exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, space_advantage, weak_colour_complex | `1k1r4/1p3p1R/5N2/p1pPPQ2/b7/2P5/qP3Pr1/2K4R b - - 1 29` |
| cl-128 | 161 | d3d8 | d3a3 | 154 | nimzo_indian | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `4r1k1/pp3pnn/8/8/4PN2/P2q1P2/5Q1P/6RK b - - 1 32` |
| cl-014 | 159 | h2h4 | e5f6 | 22 | colle | isolated_pawn, pawn_ending, queenside_majority | `8/pp2k1p1/4p2p/4Pp2/8/PPK3P1/2P4P/8 w - f6 0 32` |
| cl-038 | 135 | g8c8 | g8b8 | -100 | polish | connected_passers, exchange_imbalance, isolated_pawn, isolated_queen_pawn, knight_outpost, material_imbalance, opposite_coloured_bishops, passed_pawn, rook_and_minor_ending, rook_on_semi_open_file | `6R1/8/3k4/pp1p2pB/1n5b/4K2P/8/8 w - - 0 40` |
| cl-169 | 134 | g6h6 | g8h7 | -114 | ruy_lopez | advanced_passer, bishop_pair, connected_passers, doubled_pawns, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, protected_passer, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `1r4k1/2b3n1/p1P3r1/5pR1/BP2p3/2P1B2K/8/R7 b - - 1 39` |
| cl-149 | 125 | c5e3 | e2f3 | 93 | polish | doubled_pawns, exposed_king, isolated_pawn, isolated_queen_pawn, open_centre, rook_on_open_file, same_side_castling, space_advantage | `r2qr1k1/pp1bnpp1/5b1p/2Bp1P1P/6P1/2PB4/PP1NQP2/R4RK1 w - - 7 17` |
| cl-066 | 116 | c8d8 | c8e8 | -101 | benoni | advanced_passer, backward_pawn, exposed_king, knight_outpost, locked_pawn_chain, material_imbalance, passed_pawn, queenside_majority, rook_on_open_file, same_side_castling | `2r3k1/3q3p/3p1P1n/1p1Pr1p1/2p3P1/1nP4P/2B2Q1K/3NRR2 b - - 2 30` |
| cl-110 | 116 | f4g4 | f4f8 | 82 | grunfeld | bad_bishop, hanging_piece, isolated_pawn, maroczy_bind, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `r4rk1/7p/6p1/p1q5/BpPnPR2/8/PQ4PP/2R4K w - - 1 28` |
| cl-158 | 113 | e8c8 | e7d6 | 19 | queens_gambit_declined | backward_pawn, bishop_pair, carlsbad, doubled_pawns, isolated_pawn, knight_outpost, material_imbalance, queenless_middlegame, rook_on_semi_open_file | `r3k2r/1p2bp2/2p3b1/p2pNp1p/N2PnP2/P2BP1P1/1P5P/2R1K1R1 b kq - 1 20` |
| cl-173 | 109 | c2c4 | h2h4 | -120 | scandinavian | backward_pawn, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, open_centre, opposite_side_castling, queenless_middlegame, rook_on_open_file | `2kr3r/1p1np2p/p1p3pb/P3pb2/4N3/1P1N2P1/2P2PBP/3RR1K1 w - - 0 21` |
| cl-189 | 109 | e3g5 | d4d5 | 85 | sicilian_closed | backward_pawn, bad_bishop, exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, unusual_king_placement, weak_colour_complex | `8/5pkp/4p1p1/1q1nP3/3R4/P3BQPK/5P1P/6r1 w - - 17 44` |
| cl-092 | 107 | d1b3 | e2g3 | -31 | danish_gambit | advanced_passer, connected_passers, isolated_pawn, passed_pawn, protected_passer, queenside_majority, rook_on_semi_open_file, same_side_castling | `r2qr2k/pbp1n1bp/3pP1p1/8/2B1pP2/P3B2P/4N1P1/2RQ1RK1 w - - 1 21` |
| cl-162 | 105 | g1h1 | h2h3 | 8 | queens_indian | advanced_passer, backward_pawn, bad_bishop, king_attack, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, space_advantage | `5rk1/3PQ1pp/1q6/1p6/2p5/2Pp4/3NbPPP/4R1K1 w - - 3 26` |
| cl-096 | 102 | e7e6 | f5f4 | -41 | dutch | exposed_king, isolated_pawn, knight_outpost, rook_on_open_file, same_side_castling, unusual_king_placement | `4r3/R2bp2p/3p1qpk/2nB1p2/2PN3P/4P1P1/5P2/1Q4K1 b - - 2 32` |
| cl-107 | 95 | g7f6 | g7e5 | 205 | grunfeld | bishop_pair, doubled_pawns, exposed_king, isolated_pawn, king_in_centre, material_imbalance, passed_pawn, protected_passer, rook_on_open_file, rook_on_semi_open_file | `3q1rk1/1p3pbp/8/3P4/2PNp1P1/1P2B3/3R1PP1/r2BK2R b K - 4 24` |
