# Legacy corpus v2: reference calibration

Oracle: **Stockfish 18**, single thread, hash cleared per position, fixed **4,000,000 nodes**, multipv 3. Binary SHA-256 `c86215fa1977d53b...`. Corpus v2 (`c269c63bb74391f0`). 37 s.

Scores are centipawns from White's point of view. WDL is per mille from White's point of view. `gap` is the oracle's best line minus its second line, from the side to move, so a large gap means one move dominates.

| suite | # | eval | W/D/L | E[score] | best | gap | phase | mat | verdict | tags | fen |
|---|---|---|---|---|---|---|---|---|---|---|---|
| balanced | 0 | +0.22 | 40/953/7 | 0.52 | a2a3 | 5 | opening | +0 | near-equal | same_side_castling | `r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9` |
| balanced | 1 | +0.33 | 71/923/6 | 0.53 | c2c3 | 0 | opening | +0 | near-equal |  | `r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6` |
| balanced | 2 | -1.15 | 0/357/643 | 0.18 | a2a3 | 14 | opening | -1 | moderate edge | same_side_castling | `r1bq1rk1/pp3ppp/2n1pn2/2pp4/1b1P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9` |
| balanced | 3 | +0.61 | 183/815/2 | 0.59 | d1b3 | -1 | opening | +0 | moderate edge |  | `rn1qkb1r/pp2pppp/2p2n2/3p1b2/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5` |
| balanced | 4 | +0.99 | 492/508/0 | 0.75 | d4d5 | 23 | opening | +0 | moderate edge | king_in_centre | `r1bq1rk1/1pp1npbp/p1np2p1/4p3/2PPP3/2N1BP2/PP1QN1PP/R3KB1R w KQ - 0 10` |
| balanced | 5 | +0.50 | 127/870/3 | 0.56 | b2b3 | 6 | opening | +0 | near-equal | king_in_centre | `r1bqk2r/pp1nbppp/2p1pn2/3p4/2PP4/2N1PN2/PPQ1BPPP/R1B1K2R w KQkq - 0 8` |
| balanced | 6 | +0.58 | 167/831/2 | 0.58 | d3d4 | 10 | opening | +0 | moderate edge |  | `r1bqk2r/ppp1bppp/2np1n2/4p3/2P5/2NPPN2/PP2BPPP/R1BQK2R w KQkq - 0 7` |
| balanced | 7 | +0.13 | 35/952/13 | 0.51 | a2a4 | 3 | opening | +0 | near-equal | backward_pawn, same_side_castling | `r2q1rk1/pp1bbppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP1QPPP/R1B2RK1 w - - 0 10` |
| balanced | 8 | +2.29 | 995/5/0 | 1.00 | d4f5 | 75 | opening | +0 | clear advantage | king_in_centre, open_centre | `r1b1k2r/ppppqppp/2n2n2/2b5/3NP3/2N5/PPP1BPPP/R1BQ1RK1 w kq - 0 8` |
| balanced | 9 | +0.75 | 234/766/0 | 0.62 | e1g1 | 11 | opening | +0 | moderate edge | isolated_pawn, king_in_centre | `rnbq1rk1/pp2ppbp/6p1/2p5/3PP3/2P2N2/P3BPPP/R1BQK2R w KQ - 0 9` |
| balanced | 10 | +0.23 | 49/942/9 | 0.52 | h2h3 | 7 | opening | +0 | near-equal | king_in_centre | `r1bqk2r/pp2bppp/2n1pn2/2pp4/3P1B2/2P1PN2/PP1N1PPP/R2QKB1R w KQkq - 0 8` |
| balanced | 11 | +0.24 | 51/940/9 | 0.52 | f1d3 | 9 | opening | +0 | near-equal | king_in_centre | `r2qk2r/pb1nbppp/1pp1pn2/3p4/2PP4/1PN1PN2/PB3PPP/R2QKB1R w KQkq - 0 9` |
| balanced | 12 | +4.92 | 1000/0/0 | 1.00 | e3c5 | 407 | middlegame | +0 | tactically forced | hanging_piece, isolated_pawn, isolated_queen_pawn, open_centre, queenless_middlegame | `r3k2r/pp3ppp/2n1bn2/2bp4/8/2N1BN2/PPP2PPP/R3KB1R w KQkq - 0 11` |
| balanced | 13 | +1.03 | 553/447/0 | 0.78 | f3e5 | 5 | middlegame | +0 | moderate edge | closed_centre, queenless_middlegame | `r3k2r/ppp2ppp/2n2n2/3pp3/3PP3/2N2N2/PPP2PPP/R3K2R w KQkq - 0 9` |
| balanced | 14 | +7.31 | 1000/0/0 | 1.00 | b3b6 | 16 | endgame | +6 | decisive | material_imbalance, rook_ending, rook_on_open_file | `8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 40` |
| balanced | 15 | +0.00 | 1/998/1 | 0.50 | b3b7 | 235 | endgame | -1 | tactically forced | connected_passers, passed_pawn, queenside_majority, rook_ending, rook_on_semi_open_file | `8/pp3pk1/6p1/8/8/1R4P1/r4P1P/6K1 w - - 0 35` |
| balanced | 16 | +0.00 | 1/998/1 | 0.50 | h2h3 | 0 | endgame | +1 | near-equal | rook_ending, rook_on_open_file | `8/5ppk/8/8/8/1R6/r4PPP/6K1 w - - 0 38` |
| balanced | 17 | +0.28 | 9/991/0 | 0.50 | f2f4 | 0 | endgame | +1 | near-equal | material_imbalance, minor_piece_ending | `8/5pk1/4b1p1/8/8/4N1P1/5P1P/6K1 w - - 0 40` |
| balanced | 18 | +6.34 | 1000/0/0 | 1.00 | e3c5 | 612 | endgame | +1 | tactically forced | hanging_piece, minor_piece_ending | `8/4kp2/6p1/2b5/8/4B1P1/5P1P/6K1 w - - 0 40` |
| balanced | 19 | +0.15 | 4/996/0 | 0.50 | g1g2 | 0 | endgame | +1 | near-equal | material_imbalance, minor_piece_ending | `8/2n2pk1/6p1/8/8/4B1P1/5P1P/6K1 w - - 0 40` |
| balanced | 20 | +0.00 | 1/998/1 | 0.50 | g4g5 | 0 | endgame | +0 | near-equal | pawn_ending | `8/5pk1/6p1/8/6P1/5PK1/8/8 w - - 0 40` |
| balanced | 21 | +0.00 | 1/998/1 | 0.50 | g3f4 | 0 | endgame | +0 | near-equal | pawn_ending | `8/p4pk1/1p4p1/8/1P4P1/P4PK1/8/8 w - - 0 36` |
| balanced | 22 | +5.58 | 1000/0/0 | 1.00 | f1c4 | 34 | endgame | +3 | decisive | material_imbalance, rook_and_minor_ending, rook_on_open_file | `r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/2KR1B1R w kq - 0 15` |
| balanced | 23 | +0.03 | 2/997/1 | 0.50 | a2a4 | -1 | endgame | +0 | near-equal | opposite_coloured_bishops, rook_and_minor_ending | `r1b1k2r/pppp1ppp/8/8/8/8/PPPP1PPP/R1B1K2R w KQkq - 0 12` |
| sharp | 0 | +0.63 | 183/816/1 | 0.59 | e1c1 | 19 | opening | +0 | moderate edge | king_in_centre | `r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 9` |
| sharp | 1 | +0.92 | 415/585/0 | 0.71 | f1b5 | 16 | opening | +0 | moderate edge | carlsbad, king_in_centre | `r2qk2r/ppp1bppp/2n1bn2/3p4/3P1B2/2N1PN2/PPQ2PPP/R3KB1R w KQkq - 0 9` |
| sharp | 2 | +0.59 | 174/824/2 | 0.59 | c4d5 | 3 | opening | +0 | moderate edge | king_in_centre | `r1bqk2r/pp1nbppp/2p1pn2/3p2B1/2PP4/2N1PN2/PPQ2PPP/R3KB1R w KQkq - 0 8` |
| sharp | 3 | +0.27 | 58/934/8 | 0.53 | f3g5 | 4 | opening | +0 | near-equal |  | `r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4` |
| sharp | 4 | -1.14 | 0/367/633 | 0.18 | c4d5 | 19 | opening | -1 | moderate edge |  | `r1bqkb1r/pppp1ppp/2n5/4p3/2B1n3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5` |
| sharp | 5 | -1.45 | 0/152/848 | 0.08 | c6d4 | 22 | opening | +0 | moderate edge | hanging_piece | `r1bqk2r/pppp1ppp/2n2n2/2b1p3/2BPP3/5N2/PPP2PPP/RNBQK2R b KQkq - 0 5` |
| sharp | 6 | +0.14 | 29/961/10 | 0.51 | f3e5 | 6 | opening | +0 | near-equal |  | `r2qkb1r/pp2pppp/2n2n2/3p1b2/3P4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 7` |
| sharp | 7 | +0.62 | 190/808/2 | 0.59 | d1a4 | 6 | opening | +0 | moderate edge |  | `rnbqk2r/ppp2ppp/4pn2/3p4/1bPP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 6` |
| sharp | 8 | +0.15 | 37/951/12 | 0.51 | c4d5 | 2 | opening | +0 | near-equal |  | `r1bqkb1r/pp3ppp/2n1pn2/2pp4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 7` |
| sharp | 9 | +0.72 | 252/747/1 | 0.63 | e7e6 | 10 | opening | +0 | moderate edge |  | `rnbqkb1r/pp2pppp/3p1n2/2pP4/4P3/2N5/PPP2PPP/R1BQKBNR b KQkq - 0 5` |
| sharp | 10 | +0.46 | 110/886/4 | 0.55 | c2c3 | 11 | opening | +0 | near-equal |  | `r1bqkbnr/pp1p1ppp/2n5/2p1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4` |
| sharp | 11 | -1.78 | 0/40/960 | 0.02 | b3e6 | -5 | middlegame | +0 | clear advantage | opposite_side_castling, rook_on_semi_open_file | `r2q1rk1/1b1nbppp/p2ppn2/1p6/3NPP2/1BN1B3/PPPQ2PP/2KR3R w - - 0 13` |
| sharp | 12 | +0.53 | 141/856/3 | 0.57 | c4c5 | 15 | opening | +0 | moderate edge | same_side_castling | `r1b2rk1/pp1nqppp/2pbpn2/3p4/2PP4/2NBPN2/PPQ2PPP/R1B2RK1 w - - 0 10` |
| sharp | 13 | -3.42 | 0/0/1000 | 0.00 | c6e5 | 381 | opening | +1 | tactically forced | hanging_piece | `r1bqk2r/ppppbppp/2n2n2/4N3/2B1P3/8/PPPP1PPP/RNBQK2R b KQkq - 0 5` |
| sharp | 14 | +0.25 | 49/944/7 | 0.52 | e6d5 | 40 | opening | +1 | near-equal | doubled_pawns | `rnbqkb1r/ppp2ppp/4pn2/3P4/3P4/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 4` |
| sharp | 15 | -0.16 | 11/950/39 | 0.49 | g8f6 | 4 | opening | +0 | near-equal |  | `r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR b KQkq - 0 3` |
| sharp | 16 | +100.00 | 1000/0/0 | 1.00 | e5e6 | 10000 | endgame | +0 | tactically forced | isolated_pawn, isolated_queen_pawn, passed_pawn, pawn_ending | `k7/8/8/3pP3/8/8/8/7K w - d6 0 2` |
| sharp | 17 | +1.16 | 645/355/0 | 0.82 | d2d4 | 20 | opening | +0 | moderate edge |  | `rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 4` |

## Band sensitivity, BALANCED_OPENINGS (24)

| band (cp) | inside | outside |
|---|---|---|
| +/-25 | 10 | 14 |
| +/-50 | 13 | 11 |
| +/-75 | 16 | 8 |
| +/-100 | 17 | 7 |

## Verdicts

* **balanced**: near-equal 12, moderate edge 6, tactically forced 3, decisive 2, clear advantage 1
* **sharp**: moderate edge 9, near-equal 6, tactically forced 2, clear advantage 1
