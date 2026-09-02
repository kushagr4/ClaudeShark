# Move quality: competition_like_v1 at depth 6

Engine: working tree, depth 6. Suite: corpus\competition_like_v1.jsonl (competition_like v1, hash `6a8111f22f9ea393`, 240 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 240 | 37% | 65% | 0 | 36 | 101 | 165 | 10% | 1.7% | 0.065 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 60 | 38% | 83% | 0 | 22 | 48 | 101 | 7% | 1.7% | 0.034 |
| middlegame | 144 | 35% | 58% | 11 | 45 | 130 | 195 | 14% | 2.1% | 0.088 |
| opening | 36 | 39% | 67% | 6 | 21 | 73 | 80 | 3% | 0.0% | 0.029 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| king_attack | 9 | 44% | 56% | 0 | 67 | 116 | 334 | 33% | 11.1% | 0.137 |
| unusual_king_placement | 15 | 13% | 40% | 33 | 64 | 134 | 134 | 27% | 6.7% | 0.125 |
| closed_centre | 24 | 17% | 42% | 31 | 54 | 149 | 212 | 12% | 0.0% | 0.095 |
| exposed_king | 54 | 39% | 57% | 0 | 48 | 161 | 204 | 15% | 1.9% | 0.085 |
| rook_on_open_file | 91 | 41% | 64% | 0 | 47 | 161 | 195 | 16% | 3.3% | 0.091 |
| queenside_majority | 46 | 39% | 61% | 0 | 46 | 134 | 195 | 15% | 2.2% | 0.089 |
| material_imbalance | 127 | 39% | 61% | 2 | 45 | 116 | 204 | 14% | 3.1% | 0.087 |
| queenless_middlegame | 41 | 39% | 59% | 18 | 45 | 134 | 191 | 15% | 2.4% | 0.093 |
| passed_pawn | 98 | 42% | 68% | 0 | 44 | 134 | 225 | 15% | 4.1% | 0.080 |
| locked_pawn_chain | 31 | 16% | 55% | 19 | 44 | 96 | 149 | 10% | 0.0% | 0.082 |
| exchange_imbalance | 18 | 50% | 61% | 0 | 43 | 94 | 101 | 11% | 5.6% | 0.074 |
| maroczy_bind | 12 | 17% | 50% | 25 | 43 | 95 | 95 | 8% | 0.0% | 0.075 |
| bad_bishop | 65 | 40% | 66% | 0 | 42 | 105 | 195 | 11% | 3.1% | 0.065 |
| same_side_castling | 92 | 34% | 59% | 11 | 41 | 116 | 165 | 14% | 2.2% | 0.085 |
| space_advantage | 30 | 40% | 67% | 0 | 41 | 95 | 165 | 10% | 3.3% | 0.059 |
| opposite_side_castling | 21 | 57% | 76% | 0 | 40 | 72 | 167 | 10% | 4.8% | 0.056 |
| connected_passers | 26 | 35% | 65% | 0 | 40 | 83 | 134 | 12% | 3.8% | 0.059 |
| hanging_piece | 45 | 47% | 62% | 0 | 39 | 161 | 175 | 16% | 0.0% | 0.093 |
| advanced_passer | 33 | 48% | 76% | 0 | 39 | 105 | 134 | 12% | 6.1% | 0.067 |
| rook_on_semi_open_file | 104 | 32% | 61% | 12 | 39 | 106 | 195 | 12% | 1.9% | 0.075 |
| rook_and_minor_ending | 21 | 52% | 76% | 0 | 39 | 83 | 101 | 10% | 4.8% | 0.048 |
| weak_colour_complex | 47 | 40% | 68% | 0 | 38 | 85 | 165 | 9% | 2.1% | 0.065 |
| open_file | 167 | 41% | 68% | 0 | 36 | 105 | 175 | 12% | 2.4% | 0.069 |
| isolated_pawn | 172 | 35% | 66% | 0 | 36 | 109 | 167 | 12% | 1.7% | 0.069 |
| protected_passer | 41 | 37% | 71% | 0 | 36 | 94 | 134 | 10% | 2.4% | 0.056 |
| semi_open_file | 227 | 37% | 66% | 0 | 35 | 96 | 165 | 10% | 1.8% | 0.063 |
| open_centre | 91 | 49% | 67% | 0 | 35 | 116 | 191 | 11% | 2.2% | 0.069 |
| backward_pawn | 96 | 28% | 64% | 11 | 33 | 95 | 109 | 7% | 1.0% | 0.054 |
| bishop_pair | 76 | 42% | 64% | 0 | 32 | 85 | 134 | 9% | 0.0% | 0.068 |
| king_in_centre | 48 | 38% | 60% | 12 | 32 | 80 | 106 | 6% | 0.0% | 0.057 |
| doubled_pawns | 94 | 45% | 68% | 0 | 32 | 96 | 134 | 10% | 2.1% | 0.058 |
| knight_outpost | 45 | 40% | 64% | 0 | 28 | 101 | 109 | 11% | 0.0% | 0.055 |
| minority_attack | 10 | 30% | 50% | 19 | 27 | 59 | 82 | 0% | 0.0% | 0.064 |
| opposite_coloured_bishops | 27 | 37% | 78% | 0 | 25 | 46 | 101 | 7% | 3.7% | 0.034 |
| complex_ending | 10 | 50% | 70% | 0 | 24 | 52 | 149 | 10% | 0.0% | 0.050 |
| carlsbad | 22 | 32% | 68% | 6 | 22 | 59 | 82 | 5% | 0.0% | 0.051 |
| isolated_queen_pawn | 30 | 37% | 67% | 0 | 21 | 78 | 83 | 3% | 0.0% | 0.032 |
| minor_piece_ending | 11 | 9% | 91% | 0 | 6 | 16 | 30 | 0% | 0.0% | 0.002 |
| rook_ending | 9 | 44% | 100% | 0 | 2 | 0 | 19 | 0% | 0.0% | 0.000 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| albin | 4 | 25% | 25% | 110 | 180 | 10000 | 10000 | 50% | 25.0% | 0.280 |
| ruy_lopez | 5 | 20% | 20% | 116 | 156 | 484 | 484 | 60% | 20.0% | 0.270 |
| vienna | 6 | 0% | 33% | 60 | 111 | 195 | 331 | 33% | 16.7% | 0.203 |
| dutch | 6 | 0% | 17% | 50 | 94 | 102 | 334 | 33% | 16.7% | 0.145 |
| philidor | 5 | 20% | 60% | 20 | 63 | 204 | 204 | 20% | 0.0% | 0.123 |
| london | 5 | 0% | 20% | 58 | 59 | 106 | 106 | 20% | 0.0% | 0.118 |
| trompowsky | 5 | 0% | 60% | 19 | 56 | 165 | 165 | 20% | 0.0% | 0.121 |
| kings_indian | 6 | 33% | 33% | 31 | 53 | 42 | 212 | 17% | 0.0% | 0.088 |
| nimzo_indian | 5 | 20% | 60% | 2 | 49 | 161 | 161 | 20% | 0.0% | 0.120 |
| scandinavian | 5 | 60% | 80% | 0 | 49 | 243 | 243 | 20% | 0.0% | 0.100 |
| modern | 5 | 60% | 80% | 0 | 48 | 225 | 225 | 20% | 0.0% | 0.101 |
| centre_game | 4 | 75% | 75% | 0 | 48 | 191 | 191 | 25% | 0.0% | 0.125 |
| sicilian_closed | 4 | 25% | 50% | 37 | 46 | 109 | 109 | 25% | 0.0% | 0.134 |
| queens_gambit_declined | 6 | 17% | 50% | 35 | 44 | 82 | 113 | 17% | 0.0% | 0.145 |
| four_knights | 5 | 20% | 60% | 12 | 42 | 149 | 149 | 20% | 0.0% | 0.100 |
| italian | 5 | 20% | 60% | 25 | 39 | 95 | 95 | 0% | 0.0% | 0.059 |
| colle | 5 | 40% | 60% | 0 | 37 | 159 | 159 | 20% | 0.0% | 0.102 |
| french | 5 | 0% | 60% | 18 | 37 | 85 | 85 | 0% | 0.0% | 0.045 |
| queens_indian | 5 | 0% | 40% | 29 | 36 | 105 | 105 | 20% | 0.0% | 0.067 |
| benoni | 4 | 25% | 50% | 16 | 32 | 96 | 96 | 0% | 0.0% | 0.025 |
| sicilian_alapin | 5 | 20% | 60% | 21 | 29 | 52 | 52 | 0% | 0.0% | 0.056 |
| smith_morra | 4 | 0% | 25% | 33 | 26 | 39 | 39 | 0% | 0.0% | 0.019 |
| grunfeld | 5 | 80% | 80% | 0 | 26 | 130 | 130 | 20% | 0.0% | 0.086 |
| catalan | 6 | 33% | 67% | 10 | 23 | 46 | 73 | 0% | 0.0% | 0.019 |
| pirc | 4 | 50% | 75% | 8 | 22 | 72 | 72 | 0% | 0.0% | 0.034 |
| kings_gambit | 4 | 50% | 75% | 0 | 21 | 83 | 83 | 0% | 0.0% | 0.045 |
| queens_gambit_accepted | 4 | 50% | 75% | 1 | 20 | 79 | 79 | 0% | 0.0% | 0.096 |
| polish | 5 | 60% | 80% | 0 | 20 | 101 | 101 | 20% | 0.0% | 0.059 |
| nimzo_larsen | 4 | 75% | 75% | 0 | 19 | 76 | 76 | 0% | 0.0% | 0.064 |
| owens | 5 | 20% | 60% | 0 | 19 | 50 | 50 | 0% | 0.0% | 0.011 |
| bird | 4 | 25% | 75% | 6 | 18 | 62 | 62 | 0% | 0.0% | 0.009 |
| bogo_indian | 5 | 20% | 80% | 0 | 18 | 64 | 64 | 0% | 0.0% | 0.011 |
| caro_kann | 5 | 60% | 80% | 0 | 14 | 56 | 56 | 0% | 0.0% | 0.021 |
| english | 5 | 60% | 80% | 0 | 14 | 58 | 58 | 0% | 0.0% | 0.035 |
| old_indian | 4 | 50% | 75% | 10 | 12 | 31 | 31 | 0% | 0.0% | 0.005 |
| chigorin | 4 | 25% | 75% | 0 | 12 | 46 | 46 | 0% | 0.0% | 0.005 |
| other | 5 | 40% | 80% | 12 | 11 | 26 | 26 | 0% | 0.0% | 0.003 |
| petrov | 4 | 75% | 75% | 0 | 8 | 33 | 33 | 0% | 0.0% | 0.002 |
| reti | 5 | 40% | 80% | 0 | 8 | 29 | 29 | 0% | 0.0% | 0.003 |
| scotch | 5 | 80% | 80% | 0 | 8 | 40 | 40 | 0% | 0.0% | 0.001 |
| alekhine | 4 | 75% | 75% | 0 | 8 | 30 | 30 | 0% | 0.0% | 0.001 |
| bishops_opening | 5 | 60% | 80% | 0 | 7 | 36 | 36 | 0% | 0.0% | 0.007 |
| semi_slav | 7 | 43% | 86% | 2 | 7 | 9 | 30 | 0% | 0.0% | 0.004 |
| torre | 5 | 60% | 80% | 0 | 6 | 32 | 32 | 0% | 0.0% | 0.001 |
| benko | 4 | 50% | 100% | 1 | 6 | 21 | 21 | 0% | 0.0% | 0.001 |
| budapest | 4 | 50% | 100% | 0 | 4 | 16 | 16 | 0% | 0.0% | 0.004 |
| slav | 5 | 40% | 100% | 0 | 4 | 14 | 14 | 0% | 0.0% | 0.001 |
| sicilian | 5 | 60% | 100% | 0 | 2 | 8 | 8 | 0% | 0.0% | 0.000 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| cl-000 | 10000 | e7e5 | e7e8 | 29 | albin | bad_bishop, isolated_pawn, material_imbalance, passed_pawn, queenside_majority, rook_and_minor_ending, rook_on_open_file, weak_colour_complex | `2k5/1pp1rp1p/8/1NP5/P6n/2N5/1P4bP/2KR4 b - - 0 27` |
| cl-170 | 484 | h3e6 | b2c3 | 99 | ruy_lopez | advanced_passer, backward_pawn, bad_bishop, connected_passers, exposed_king, material_imbalance, opposite_side_castling, passed_pawn, protected_passer, rook_on_open_file, space_advantage | `3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 4 41` |
| cl-097 | 334 | c1b3 | g2g4 | 33 | dutch | advanced_passer, doubled_pawns, isolated_pawn, king_attack, material_imbalance, open_centre, opposite_coloured_bishops, passed_pawn, queenless_middlegame, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `r2r4/4R3/2k1p2p/2p1Bbp1/8/2N1p3/1PP3PP/1KN5 w - - 0 25` |
| cl-201 | 331 | f8d8 | c8d8 | 131 | vienna | doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_semi_open_file, same_side_castling | `2r2rk1/pp3p1p/4P1p1/8/1p2B2R/3Q2PP/2P2PK1/2q5 b - - 1 25` |
| cl-174 | 243 | b7c7 | b7b2 | -101 | scandinavian | bishop_pair, exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `Q7/1r3ppk/2q1p2p/5b2/2P1n3/P2B1N2/1R3PPP/2n1B1K1 b - - 3 29` |
| cl-125 | 225 | c4e3 | c4a3 | -14 | modern | backward_pawn, bad_bishop, closed_centre, king_in_centre, locked_pawn_chain, passed_pawn, protected_passer, rook_on_semi_open_file | `r3k2r/4npbp/1qp1p1p1/3pP2P/2nP1P2/PpQ1B3/1P1N2P1/1KR2N1R b kq - 4 20` |
| cl-117 | 212 | e1g1 | e3h6 | 139 | kings_indian | backward_pawn, bishop_pair, closed_centre, doubled_pawns, exposed_king, isolated_pawn, king_in_centre, locked_pawn_chain, material_imbalance, rook_on_semi_open_file | `2kr3r/pp1bn1q1/3p1npp/2pPp3/2P1P2Q/2P1B3/P2NBPP1/R3K2R w KQ - 12 16` |
| cl-144 | 204 | c4e4 | c4e2 | 18 | philidor | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, queenside_majority, rook_on_semi_open_file | `r7/pp1kNpQ1/3p4/8/2q1P3/2P3R1/PP3r2/2KR4 b - - 0 24` |
| cl-202 | 195 | e3a7 | e2d4 | 5 | vienna | bad_bishop, bishop_pair, doubled_pawns, isolated_pawn, material_imbalance, passed_pawn, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, weak_colour_complex | `3rkb1r/ppp2pp1/2b5/4P2p/4p3/2P1B1P1/PPP1N2P/R3KR2 w Qk - 2 14` |
| cl-087 | 191 | e5e6 | f1e1 | 8 | centre_game | isolated_pawn, open_centre, queenless_middlegame, rook_on_open_file, same_side_castling | `r2r3k/ppp1b1pp/2n2p2/4P3/2B2P2/2P2N2/P1b3PP/R1B2RK1 w - - 0 15` |
| cl-094 | 175 | b5h5 | b5b4 | -70 | danish_gambit | hanging_piece, isolated_pawn, rook_on_open_file, same_side_castling | `r4rk1/pp1b1ppp/2np4/1q6/P2PB3/5N1P/1P1Q1PP1/R3R1K1 b - - 0 19` |
| cl-060 | 167 | g3e5 | f7e6 | -42 | albin | bishop_pair, hanging_piece, isolated_pawn, material_imbalance, open_centre, opposite_side_castling, passed_pawn, queenless_middlegame, rook_on_open_file | `2kr1b1r/ppp2Bpp/8/4n3/4P3/N4nB1/PP3P1P/R4K1R w - - 0 15` |
| cl-198 | 165 | a2a1 | b8a7 | -101 | trompowsky | exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, space_advantage, weak_colour_complex | `1k1r4/1p3p1R/5N2/p1pPPQ2/b7/2P5/qP3Pr1/2K4R b - - 1 29` |
| cl-128 | 161 | d3d8 | d3a3 | 90 | nimzo_indian | exposed_king, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling | `4r1k1/pp3pnn/8/8/4PN2/P2q1P2/5Q1P/6RK b - - 1 32` |
| cl-014 | 159 | h2h4 | e5f6 | 22 | colle | isolated_pawn, pawn_ending, queenside_majority | `8/pp2k1p1/4p2p/4Pp2/8/PPK3P1/2P4P/8 w - f6 0 32` |
| cl-020 | 149 | b7e7 | e6d5 | 8 | four_knights | backward_pawn, closed_centre, complex_ending, doubled_pawns, locked_pawn_chain | `8/1q4pk/3ppn1p/1p1Pp3/p1p1P3/P1N1P2P/1PP2QP1/6K1 b - - 0 30` |
| cl-169 | 134 | g6h6 | g8h7 | -100 | ruy_lopez | advanced_passer, bishop_pair, connected_passers, doubled_pawns, hanging_piece, isolated_pawn, material_imbalance, open_centre, passed_pawn, protected_passer, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, unusual_king_placement | `1r4k1/2b3n1/p1P3r1/5pR1/BP2p3/2P1B2K/8/R7 b - - 1 39` |
| cl-110 | 130 | f4f2 | f4f8 | 28 | grunfeld | bad_bishop, hanging_piece, isolated_pawn, maroczy_bind, material_imbalance, open_centre, passed_pawn, rook_on_open_file, same_side_castling | `r4rk1/7p/6p1/p1q5/BpPnPR2/8/PQ4PP/2R4K w - - 1 28` |
| cl-172 | 116 | a8d8 | a6d3 | -68 | ruy_lopez | bishop_pair, doubled_pawns, isolated_pawn, king_attack, material_imbalance, open_centre, rook_on_semi_open_file, same_side_castling | `r3qrk1/p1pp2pp/bbp5/4P3/6n1/3N2B1/PPP1NPPP/R2Q1RK1 b - - 4 14` |
| cl-158 | 113 | e8c8 | e7d6 | 18 | queens_gambit_declined | backward_pawn, bishop_pair, carlsbad, doubled_pawns, isolated_pawn, knight_outpost, material_imbalance, queenless_middlegame, rook_on_semi_open_file | `r3k2r/1p2bp2/2p3b1/p2pNp1p/N2PnP2/P2BP1P1/1P5P/2R1K1R1 b kq - 1 20` |
| cl-189 | 109 | e3g5 | d4d5 | 20 | sicilian_closed | backward_pawn, bad_bishop, exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, rook_on_open_file, same_side_castling, unusual_king_placement, weak_colour_complex | `8/5pkp/4p1p1/1q1nP3/3R4/P3BQPK/5P1P/6r1 w - - 17 44` |
| cl-222 | 106 | a7a6 | c8d7 | 14 | london | doubled_pawns, isolated_pawn, king_in_centre, rook_on_semi_open_file | `r1b1kb1r/pp3ppp/2n1pn2/1BPpN3/5B2/2q1P3/P1PN1PPP/1R1QK2R b Kkq - 1 9` |
| cl-162 | 105 | g1h1 | h2h3 | 19 | queens_indian | advanced_passer, backward_pawn, bad_bishop, king_attack, material_imbalance, passed_pawn, protected_passer, queenside_majority, rook_on_open_file, rook_on_semi_open_file, same_side_castling, space_advantage | `5rk1/3PQ1pp/1q6/1p6/2p5/2Pp4/3NbPPP/4R1K1 w - - 3 26` |
| cl-096 | 102 | e7e6 | f5f4 | -43 | dutch | exposed_king, isolated_pawn, knight_outpost, rook_on_open_file, same_side_castling, unusual_king_placement | `4r3/R2bp2p/3p1qpk/2nB1p2/2PN3P/4P1P1/5P2/1Q4K1 b - - 2 32` |
| cl-038 | 101 | h5e2 | g8b8 | -72 | polish | connected_passers, exchange_imbalance, isolated_pawn, isolated_queen_pawn, knight_outpost, material_imbalance, opposite_coloured_bishops, passed_pawn, rook_and_minor_ending, rook_on_semi_open_file | `6R1/8/3k4/pp1p2pB/1n5b/4K2P/8/8 w - - 0 40` |
