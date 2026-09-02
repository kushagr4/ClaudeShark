# Diagnosis of 24 serious errors (loss >= 100 cp at depth 6)

Fixed means the oracle-scored loss of the new move is <= 50 cp. Ladder from depth 4 to 9; timed search 4500 ms; feature-off variants at depth 6.

| cause | count |
|---|---|
| search_depth | 12 |
| evaluation | 7 |
| pruning | 3 |
| horizon | 1 |
| unresolved | 1 |

## Cause by structural tag (tags with >= 3 errors)

| tag | errors | pruning | search_depth | horizon | time | evaluation | unresolved |
|---|---|---|---|---|---|---|---|
| isolated_pawn | 20 | 2 | 11 | 1 | 0 | 5 | 1 |
| material_imbalance | 18 | 2 | 9 | 1 | 0 | 5 | 1 |
| rook_on_open_file | 17 | 2 | 8 | 1 | 0 | 5 | 1 |
| passed_pawn | 16 | 1 | 8 | 1 | 0 | 5 | 1 |
| same_side_castling | 15 | 2 | 8 | 1 | 0 | 3 | 1 |
| exposed_king | 11 | 2 | 6 | 0 | 0 | 3 | 0 |
| rook_on_semi_open_file | 11 | 2 | 4 | 1 | 0 | 4 | 0 |
| open_centre | 10 | 1 | 5 | 1 | 0 | 2 | 1 |
| queenside_majority | 8 | 1 | 4 | 1 | 0 | 2 | 0 |
| bad_bishop | 7 | 1 | 2 | 0 | 0 | 3 | 1 |
| backward_pawn | 7 | 2 | 3 | 0 | 0 | 2 | 0 |
| doubled_pawns | 7 | 2 | 2 | 1 | 0 | 2 | 0 |
| bishop_pair | 6 | 1 | 3 | 1 | 0 | 1 | 0 |
| hanging_piece | 6 | 0 | 2 | 1 | 0 | 2 | 1 |
| knight_outpost | 6 | 0 | 5 | 0 | 0 | 1 | 0 |
| advanced_passer | 5 | 1 | 1 | 1 | 0 | 2 | 0 |
| space_advantage | 5 | 2 | 1 | 0 | 0 | 2 | 0 |
| queenless_middlegame | 5 | 0 | 2 | 1 | 0 | 2 | 0 |
| weak_colour_complex | 4 | 0 | 2 | 0 | 0 | 2 | 0 |
| protected_passer | 4 | 1 | 0 | 1 | 0 | 2 | 0 |
| unusual_king_placement | 4 | 0 | 2 | 1 | 0 | 1 | 0 |
| connected_passers | 3 | 0 | 1 | 1 | 0 | 1 | 0 |
| locked_pawn_chain | 3 | 1 | 1 | 0 | 0 | 1 | 0 |

## Every position

| id | loss | engine | best | cause | ladder losses | features fixed | timed loss | static prefers engine move | fen |
|---|---|---|---|---|---|---|---|---|---|
| cl-000 | 10000 | e7e5 | e7e8 | **search_depth** | d4:10000, d5:10000, d6:10000, d7:10000, d8:0, d9:0 | - | 10000 | no | `2k5/1pp1rp1p/8/1NP5/P6n/2N5/1P4bP/2KR4 b - - 0 27` |
| cl-170 | 484 | h3e6 | b2c3 | **evaluation** | d4:484, d5:484, d6:484, d7:484, d8:484, d9:484 | - | 484 | yes | `3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 4 41` |
| cl-097 | 334 | c1b3 | g2g4 | **evaluation** | d4:22, d5:334, d6:334, d7:334, d8:334, d9:334 | - | 334 | yes | `r2r4/4R3/2k1p2p/2p1Bbp1/8/2N1p3/1PP3PP/1KN5 w - - 0 25` |
| cl-201 | 331 | f8d8 | c8d8 | **search_depth** | d4:487, d5:331, d6:331, d7:331, d8:0, d9:0 | - | 331 | yes | `2r2rk1/pp3p1p/4P1p1/8/1p2B2R/3Q2PP/2P2PK1/2q5 b - - 1 25` |
| cl-151 | 251 | f1f5 | d8f8 | **search_depth** | d4:0, d5:0, d6:251, d7:0, d8:0, d9:0 | lmr_off, see_qs_off, aspiration_off | 0 | no | `3r3k/p2q2p1/P1p1R2p/1pb1P3/8/1BP1n1BP/1P2Q1PK/4Rr2 b - - 4 33` |
| cl-174 | 243 | b7c7 | b7b2 | **search_depth** | d4:243, d5:243, d6:243, d7:243, d8:36, d9:36 | - | 243 | no | `Q7/1r3ppk/2q1p2p/5b2/2P1n3/P2B1N2/1R3PPP/2n1B1K1 b - - 3 29` |
| cl-125 | 225 | c4e3 | c4a3 | **evaluation** | d4:225, d5:225, d6:225, d7:225, d8:225, d9:225 | - | 225 | yes | `r3k2r/4npbp/1qp1p1p1/3pP2P/2nP1P2/PpQ1B3/1P1N2P1/1KR2N1R b kq - 4 20` |
| cl-117 | 212 | e1g1 | e3h6 | **pruning** | d4:87, d5:87, d6:212, d7:212, d8:212, d9:212 | lmr_off | 87 | no | `2kr3r/pp1bn1q1/3p1npp/2pPp3/2P1P2Q/2P1B3/P2NBPP1/R3K2R w KQ - 12 16` |
| cl-144 | 204 | c4e4 | c4e2 | **evaluation** | d4:204, d5:204, d6:204, d7:204, d8:204, d9:204 | - | 204 | yes | `r7/pp1kNpQ1/3p4/8/2q1P3/2P3R1/PP3r2/2KR4 b - - 0 24` |
| cl-202 | 195 | e3a7 | e2d4 | **evaluation** | d4:195, d5:195, d6:195, d7:195, d8:195, d9:195 | - | 195 | yes | `3rkb1r/ppp2pp1/2b5/4P2p/4p3/2P1B1P1/PPP1N2P/R3KR2 w Qk - 2 14` |
| cl-087 | 191 | e5e6 | f1e1 | **search_depth** | d4:191, d5:191, d6:191, d7:191, d8:0, d9:191 | - | 191 | yes | `r2r3k/ppp1b1pp/2n2p2/4P3/2B2P2/2P2N2/P1b3PP/R1B2RK1 w - - 0 15` |
| cl-094 | 175 | b5h5 | b5b4 | **evaluation** | d4:175, d5:175, d6:175, d7:175, d8:112, d9:152 | - | 175 | yes | `r4rk1/pp1b1ppp/2np4/1q6/P2PB3/5N1P/1P1Q1PP1/R3R1K1 b - - 0 19` |
| cl-198 | 165 | a2a1 | b8a7 | **evaluation** | d4:165, d5:165, d6:165, d7:165, d8:165, d9:165 | - | 165 | yes | `1k1r4/1p3p1R/5N2/p1pPPQ2/b7/2P5/qP3Pr1/2K4R b - - 1 29` |
| cl-128 | 161 | d3d8 | d3a3 | **search_depth** | d4:161, d5:161, d6:161, d7:161, d8:0, d9:0 | - | 161 | no | `4r1k1/pp3pnn/8/8/4PN2/P2q1P2/5Q1P/6RK b - - 1 32` |
| cl-014 | 159 | h2h4 | e5f6 | **search_depth** | d4:118, d5:118, d6:159, d7:159, d8:3, d9:118 | - | 118 | no | `8/pp2k1p1/4p2p/4Pp2/8/PPK3P1/2P4P/8 w - f6 0 32` |
| cl-169 | 134 | g6h6 | g8h7 | **horizon** | d4:134, d5:134, d6:134, d7:134, d8:134, d9:0 | - | 134 | no | `1r4k1/2b3n1/p1P3r1/5pR1/BP2p3/2P1B2K/8/R7 b - - 1 39` |
| cl-149 | 125 | c5e3 | e2f3 | **pruning** | d4:125, d5:125, d6:125, d7:125, d8:125, d9:125 | nmp_off, lmr_off, see_qs_off | 125 | no | `r2qr1k1/pp1bnpp1/5b1p/2Bp1P1P/6P1/2PB4/PP1NQP2/R4RK1 w - - 7 17` |
| cl-066 | 116 | c8d8 | c8e8 | **search_depth** | d4:0, d5:0, d6:116, d7:0, d8:0, d9:0 | lmr_off | 116 | yes | `2r3k1/3q3p/3p1P1n/1p1Pr1p1/2p3P1/1nP4P/2B2Q1K/3NRR2 b - - 2 30` |
| cl-110 | 116 | f4g4 | f4f8 | **unresolved** | d4:342, d5:130, d6:116, d7:116, d8:130, d9:130 | - | 116 | no | `r4rk1/7p/6p1/p1q5/BpPnPR2/8/PQ4PP/2R4K w - - 1 28` |
| cl-158 | 113 | e8c8 | e7d6 | **search_depth** | d4:38, d5:7, d6:113, d7:113, d8:0, d9:38 | - | 113 | yes | `r3k2r/1p2bp2/2p3b1/p2pNp1p/N2PnP2/P2BP1P1/1P5P/2R1K1R1 b kq - 1 20` |
| cl-189 | 109 | e3g5 | d4d5 | **search_depth** | d4:491, d5:109, d6:109, d7:7, d8:7, d9:7 | - | 109 | no | `8/5pkp/4p1p1/1q1nP3/3R4/P3BQPK/5P1P/6r1 w - - 17 44` |
| cl-162 | 105 | g1h1 | h2h3 | **pruning** | d4:120, d5:105, d6:105, d7:105, d8:105, d9:105 | delta_off | 105 | no | `5rk1/3PQ1pp/1q6/1p6/2p5/2Pp4/3NbPPP/4R1K1 w - - 3 26` |
| cl-096 | 102 | e7e6 | f5f4 | **search_depth** | d4:102, d5:102, d6:102, d7:102, d8:0, d9:0 | - | 102 | no | `4r3/R2bp2p/3p1qpk/2nB1p2/2PN3P/4P1P1/5P2/1Q4K1 b - - 2 32` |
| cl-038 | 101 | h5e2 | g8b8 | **search_depth** | d4:135, d5:101, d6:101, d7:0, d8:0, d9:0 | - | 0 | no | `6R1/8/3k4/pp1p2pB/1n5b/4K2P/8/8 w - - 0 40` |
