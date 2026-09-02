# Move quality: stress_test_v1 at depth 6

Engine: working tree, depth 6. Suite: corpus\stress_test_v1.jsonl (stress_test v1, hash `591ec2b339da3a42`, 120 positions). Oracle: Stockfish 18 at 1,000,000 nodes per child, single thread.

Loss is centipawns from the side to move, oracle score after the oracle's best move minus oracle score after the engine's move, both at the same node count. Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.

## Overall

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 120 | 76% | 82% | 0 | 31 | 80 | 178 | 10% | 3.3% | 0.052 |

## By phase

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| endgame | 36 | 69% | 78% | 0 | 36 | 80 | 104 | 8% | 5.6% | 0.049 |
| middlegame | 66 | 79% | 83% | 0 | 35 | 128 | 245 | 14% | 3.0% | 0.063 |
| opening | 18 | 78% | 89% | 0 | 7 | 17 | 26 | 0% | 0.0% | 0.020 |

## By structural tag (sorted by robust mean loss, n >= 8)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| locked_pawn_chain | 19 | 58% | 63% | 0 | 76 | 144 | 462 | 21% | 10.5% | 0.130 |
| exposed_king | 28 | 71% | 75% | 0 | 63 | 245 | 462 | 21% | 7.1% | 0.105 |
| connected_passers | 20 | 55% | 65% | 0 | 62 | 178 | 292 | 20% | 5.0% | 0.095 |
| exchange_imbalance | 15 | 47% | 60% | 0 | 51 | 245 | 245 | 20% | 0.0% | 0.086 |
| queenside_majority | 24 | 83% | 88% | 0 | 48 | 178 | 462 | 12% | 8.3% | 0.058 |
| opposite_side_castling | 14 | 79% | 79% | 0 | 48 | 178 | 178 | 14% | 7.1% | 0.066 |
| backward_pawn | 45 | 71% | 80% | 0 | 48 | 144 | 422 | 13% | 6.7% | 0.076 |
| passed_pawn | 60 | 70% | 77% | 0 | 47 | 142 | 292 | 15% | 5.0% | 0.075 |
| opposite_coloured_bishops | 12 | 83% | 83% | 0 | 46 | 57 | 57 | 8% | 8.3% | 0.050 |
| protected_passer | 30 | 73% | 73% | 0 | 43 | 128 | 292 | 13% | 3.3% | 0.075 |
| same_side_castling | 39 | 79% | 79% | 0 | 41 | 142 | 245 | 18% | 2.6% | 0.083 |
| space_advantage | 17 | 65% | 76% | 0 | 39 | 31 | 144 | 12% | 5.9% | 0.063 |
| open_file | 90 | 77% | 82% | 0 | 36 | 80 | 292 | 10% | 4.4% | 0.054 |
| isolated_pawn | 88 | 75% | 82% | 0 | 33 | 80 | 245 | 10% | 3.4% | 0.055 |
| rook_on_semi_open_file | 46 | 74% | 80% | 0 | 31 | 104 | 178 | 13% | 2.2% | 0.054 |
| semi_open_file | 110 | 77% | 83% | 0 | 30 | 80 | 178 | 10% | 2.7% | 0.051 |
| rook_on_open_file | 50 | 74% | 80% | 0 | 28 | 80 | 178 | 10% | 2.0% | 0.055 |
| knight_outpost | 17 | 82% | 82% | 0 | 27 | 28 | 142 | 12% | 0.0% | 0.047 |
| queenless_middlegame | 13 | 77% | 85% | 0 | 26 | 142 | 142 | 15% | 0.0% | 0.053 |
| bad_bishop | 40 | 78% | 85% | 0 | 25 | 74 | 128 | 10% | 2.5% | 0.048 |
| advanced_passer | 17 | 65% | 82% | 0 | 25 | 31 | 128 | 12% | 0.0% | 0.057 |
| unusual_king_placement | 11 | 82% | 82% | 0 | 22 | 104 | 142 | 18% | 0.0% | 0.067 |
| doubled_pawns | 40 | 78% | 85% | 0 | 22 | 60 | 104 | 8% | 2.5% | 0.038 |
| weak_colour_complex | 32 | 78% | 81% | 0 | 22 | 74 | 128 | 9% | 0.0% | 0.047 |
| closed_centre | 17 | 65% | 76% | 0 | 21 | 74 | 80 | 6% | 0.0% | 0.072 |
| material_imbalance | 92 | 78% | 86% | 0 | 21 | 59 | 128 | 8% | 1.1% | 0.035 |
| open_centre | 38 | 89% | 92% | 0 | 19 | 0 | 60 | 5% | 2.6% | 0.024 |
| rook_and_minor_ending | 14 | 57% | 71% | 0 | 18 | 80 | 80 | 7% | 0.0% | 0.045 |
| isolated_queen_pawn | 12 | 92% | 92% | 0 | 15 | 0 | 0 | 8% | 0.0% | 0.033 |
| complex_ending | 8 | 75% | 75% | 0 | 14 | 57 | 59 | 0% | 0.0% | 0.015 |
| bishop_pair | 34 | 79% | 88% | 0 | 13 | 60 | 74 | 6% | 0.0% | 0.031 |
| hanging_piece | 54 | 87% | 94% | 0 | 13 | 0 | 9 | 4% | 1.9% | 0.015 |
| king_in_centre | 24 | 75% | 92% | 0 | 7 | 17 | 60 | 0% | 0.0% | 0.014 |

## By opening family (n >= 4)

| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp | E-loss |
|---|---|---|---|---|---|---|---|---|---|---|
| french | 4 | 25% | 50% | 46 | 138 | 462 | 462 | 25% | 25.0% | 0.190 |
| queens_gambit_accepted | 4 | 75% | 75% | 0 | 44 | 178 | 178 | 25% | 0.0% | 0.100 |
| slav | 4 | 75% | 75% | 0 | 8 | 33 | 33 | 0% | 0.0% | 0.005 |

## Worst 25 positions

| id | loss | engine | best | engine score | family | tags | fen |
|---|---|---|---|---|---|---|---|
| st-098 | 9988 | a3a1 | a3f8 | -939 | sicilian | connected_passers, exposed_king, isolated_pawn, open_centre, opposite_coloured_bishops, passed_pawn, protected_passer, queenside_majority, rook_on_semi_open_file, same_side_castling | `1r4k1/5p1p/5PpQ/3Bp3/2Pb4/qP3R2/7P/7K b - - 6 36` |
| st-028 | 975 | b2f6 | b2c1 | -87 | ruy_lopez | backward_pawn, bad_bishop, hanging_piece, isolated_pawn, locked_pawn_chain, minor_piece_ending, passed_pawn | `8/6p1/5b1p/p2k3P/Pp2p1P1/1P6/1B2K3/8 w - - 9 45` |
| st-082 | 462 | g7e6 | f6d4 | 107 | french | backward_pawn, doubled_pawns, exposed_king, isolated_pawn, locked_pawn_chain, material_imbalance, opposite_side_castling, passed_pawn, queenside_majority, rook_on_open_file, space_advantage | `r1b1r1k1/5pn1/2p2qN1/3p2R1/1p1P4/pP1P1P2/P2Q3P/2KN2R1 b - - 0 25` |
| st-024 | 422 | c4b5 | e3d3 | 19 | old_indian | backward_pawn, pawn_ending | `8/2p5/3p3p/pp1Pk1p1/2P3P1/PP2K2P/8/8 w - - 0 40` |
| st-079 | 292 | a6b7 | g1g2 | -65 | alekhine | connected_passers, exchange_imbalance, exposed_king, isolated_pawn, knight_outpost, material_imbalance, passed_pawn, protected_passer, rook_on_open_file, same_side_castling | `4rbk1/3q3p/Q5p1/2pp2B1/3np2P/P5P1/8/1R3RK1 w - - 2 34` |
| st-068 | 245 | c8b8 | h7h6 | -133 | torre | advanced_passer, backward_pawn, exchange_imbalance, exposed_king, isolated_pawn, material_imbalance, passed_pawn, rook_on_semi_open_file, same_side_castling, weak_colour_complex | `2r3k1/3Q2pp/4p3/4Pp2/1PqPbP2/2p4P/5RPK/2R5 b - - 12 37` |
| st-005 | 178 | b8c8 | b8d8 | 41 | queens_gambit_accepted | connected_passers, isolated_pawn, isolated_queen_pawn, king_attack, material_imbalance, open_centre, opposite_side_castling, passed_pawn, protected_passer, queenless_middlegame, queenside_majority, rook_on_open_file, rook_on_semi_open_file | `1r4k1/8/R7/1r4p1/2NPnp2/1nB5/1PK5/7R b - - 1 43` |
| st-107 | 144 | g1f3 | f2f4 | 19 | caro_kann | backward_pawn, bad_bishop, closed_centre, exposed_king, isolated_pawn, locked_pawn_chain, rook_on_open_file, same_side_castling, space_advantage | `3q4/pQ1n1pk1/2p1p1p1/2PpP1br/3P4/4B3/P4PK1/1R4N1 w - - 14 36` |
| st-011 | 142 | d1d2 | f2e3 | 8 | petrov | backward_pawn, bishop_pair, hanging_piece, knight_outpost, locked_pawn_chain, material_imbalance, passed_pawn, queenless_middlegame, rook_on_semi_open_file, same_side_castling, unusual_king_placement, weak_colour_complex | `5r2/1p1r2k1/p1p1n1p1/P2pP2p/1R3p1P/2P1nP1K/1PB2BP1/3R4 w - - 14 39` |
| st-088 | 128 | e2c4 | g4g5 | -25 | polish | advanced_passer, bad_bishop, bishop_pair, connected_passers, doubled_pawns, material_imbalance, passed_pawn, protected_passer, rook_on_semi_open_file, same_side_castling, weak_colour_complex | `r4rk1/3b1ppp/Pq2pb2/1P1p4/2pNn1P1/4PN2/2Q1BPP1/RR4K1 w - - 1 25` |
| st-084 | 104 | e8c8 | c7c6 | 35 | chigorin | bad_bishop, doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, rook_and_minor_ending, rook_on_semi_open_file | `4r1k1/p1p2ppp/7r/8/3P4/PP2PP2/1B2KP1P/2R5 b - - 2 31` |
| st-106 | 104 | d4d3 | d8h8 | 0 | scandinavian | exposed_king, isolated_pawn, passed_pawn, rook_on_open_file, same_side_castling, unusual_king_placement | `3r4/8/kn2p1Q1/p3P3/2pq3P/2N5/PP6/1K3R2 b - - 0 39` |
| st-067 | 80 | b8b5 | e7d8 | -29 | benoni | backward_pawn, closed_centre, isolated_pawn, locked_pawn_chain, maroczy_bind, passed_pawn, protected_passer, rook_and_minor_ending, rook_on_open_file | `1r6/3kbp2/3p2p1/2pPp2p/n1N1P2P/P4PP1/2KB4/7R b - - 1 33` |
| st-053 | 74 | g8h6 | h7h6 | -48 | french | backward_pawn, bad_bishop, bishop_pair, closed_centre, doubled_pawns, isolated_pawn, king_in_centre, locked_pawn_chain, material_imbalance, weak_colour_complex | `r1b1k1nr/pp3p1p/2n1p1p1/q2pP3/P1pP2QP/2P5/2PB1PP1/R3KBNR b KQkq - 0 10` |
| st-091 | 60 | d8d1 | d8e7 | 23 | catalan | bad_bishop, bishop_pair, doubled_pawns, hanging_piece, king_in_centre, material_imbalance, open_centre, weak_colour_complex | `1r1qk2r/1pp1Nppp/p1n1b3/4P3/2p1n3/5NP1/PP3PBP/R1BQ1RK1 b k - 0 12` |
| st-069 | 59 | b7b5 | d7f5 | 34 | queens_gambit_declined | complex_ending, connected_passers, exchange_imbalance, isolated_pawn, material_imbalance, passed_pawn, protected_passer, rook_on_open_file | `8/kprq4/p7/8/5P2/PQ2PBp1/KP4P1/8 b - - 3 38` |
| st-100 | 57 | d8d1 | e5f6 | -106 | budapest | complex_ending, isolated_pawn, opposite_coloured_bishops | `3q4/7p/2p3pk/2P1bp2/2Q5/4P1P1/B4P1P/6K1 b - - 0 35` |
| st-010 | 33 | c3b5 | f3e5 | 28 | slav | carlsbad, connected_passers, doubled_pawns, exchange_imbalance, isolated_pawn, material_imbalance, passed_pawn, protected_passer, rook_and_minor_ending, rook_on_open_file, rook_on_semi_open_file | `r4rk1/5ppp/4p3/n2p4/3P1P2/1PNK1N2/P4PPP/2R5 w - - 1 21` |
| st-097 | 31 | f4f5 | g3f3 | -4 | dutch | advanced_passer, connected_passers, isolated_pawn, material_imbalance, passed_pawn, protected_passer, rook_and_minor_ending, rook_on_open_file, rook_on_semi_open_file, space_advantage, weak_colour_complex | `1r2b2k/6p1/1P5p/2P5/3R1P1P/6K1/8/8 w - - 1 42` |
| st-051 | 28 | f4e6 | a3b4 | 146 | english | backward_pawn, carlsbad, exchange_imbalance, exposed_king, isolated_pawn, king_attack, knight_outpost, material_imbalance, opposite_side_castling, passed_pawn, rook_on_open_file, rook_on_semi_open_file | `2k3r1/1b1n4/pp1b1p2/2pp4/3PnN1q/BP2PR1P/P1Q3B1/2R3K1 w - - 0 25` |
| st-110 | 26 | h7h6 | c7c6 | -33 | pirc | closed_centre, locked_pawn_chain, same_side_castling, space_advantage | `r1bq1rk1/1pp1npbp/p2p1np1/P2Pp3/4P3/2N2N2/1PP1BPPP/R1BQR1K1 b - - 0 10` |
| st-042 | 24 | f6g4 | c8g4 | 150 | kings_gambit | advanced_passer, bishop_pair, connected_passers, isolated_pawn, material_imbalance, passed_pawn, queenless_middlegame, queenside_majority | `r1b1k2r/pp3p2/2np1n1p/8/7P/2NPB1p1/PPP5/R3KB1R b KQkq - 2 15` |
| st-017 | 17 | g6f5 | e7h4 | 38 | polish | backward_pawn, bishop_pair, closed_centre, doubled_pawns, isolated_pawn, king_in_centre, maroczy_bind, material_imbalance, rook_on_semi_open_file | `r1b2rk1/1p2q1bp/p1n3p1/4pP2/2PpP3/N2P4/PP1QNPBP/R3K2R b KQ - 0 14` |
| st-118 | 17 | e1g1 | a1b1 | 49 | french | backward_pawn, closed_centre, king_in_centre, locked_pawn_chain | `r3kb1r/pp1bnppp/1q2p3/n2pP3/2pP4/P1P2N2/1PQNBPPP/R1B1K2R w KQkq - 6 10` |
| st-111 | 9 | a3b4 | d3c4 | -22 | vienna | bishop_pair, hanging_piece, king_in_centre, material_imbalance | `r1bq1rk1/pp1p1ppp/2p2n2/4p3/1bn1P3/P1NP2N1/1PPB1PPP/R2QK2R w KQ - 0 9` |
