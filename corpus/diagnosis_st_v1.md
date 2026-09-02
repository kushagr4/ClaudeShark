# Diagnosis of 12 serious errors (loss >= 100 cp at depth 6)

Fixed means the oracle-scored loss of the new move is <= 50 cp. Ladder from depth 4 to 9; timed search 0 ms; feature-off variants at depth 6.

| cause | count |
|---|---|
| search_depth | 6 |
| pruning | 3 |
| unresolved | 2 |
| evaluation | 1 |

## Cause by structural tag (tags with >= 3 errors)

| tag | errors | pruning | search_depth | horizon | time | evaluation | unresolved |
|---|---|---|---|---|---|---|---|
| isolated_pawn | 9 | 3 | 5 | 0 | 0 | 0 | 1 |
| passed_pawn | 9 | 2 | 5 | 0 | 0 | 0 | 2 |
| same_side_castling | 7 | 1 | 4 | 0 | 0 | 0 | 2 |
| material_imbalance | 7 | 2 | 3 | 0 | 0 | 0 | 2 |
| exposed_king | 6 | 1 | 4 | 0 | 0 | 0 | 1 |
| rook_on_semi_open_file | 6 | 3 | 1 | 0 | 0 | 0 | 2 |
| backward_pawn | 6 | 0 | 3 | 0 | 0 | 1 | 2 |
| rook_on_open_file | 5 | 1 | 4 | 0 | 0 | 0 | 0 |
| connected_passers | 4 | 2 | 2 | 0 | 0 | 0 | 0 |
| protected_passer | 4 | 2 | 2 | 0 | 0 | 0 | 0 |
| bad_bishop | 4 | 1 | 3 | 0 | 0 | 0 | 0 |
| locked_pawn_chain | 4 | 0 | 3 | 0 | 0 | 0 | 1 |
| queenside_majority | 3 | 2 | 1 | 0 | 0 | 0 | 0 |
| doubled_pawns | 3 | 1 | 2 | 0 | 0 | 0 | 0 |
| exchange_imbalance | 3 | 1 | 1 | 0 | 0 | 0 | 1 |
| weak_colour_complex | 3 | 0 | 1 | 0 | 0 | 0 | 2 |

## Every position

| id | loss | engine | best | cause | ladder losses | features fixed | timed loss | static prefers engine move | fen |
|---|---|---|---|---|---|---|---|---|---|
| st-098 | 9988 | a3a1 | a3f8 | **pruning** | d4:9988, d5:9988, d6:9988, d7:9988, d8:9988, d9:9988 | tt_pv_cutoff_off | None | yes | `1r4k1/5p1p/5PpQ/3Bp3/2Pb4/qP3R2/7P/7K b - - 6 36` |
| st-028 | 975 | b2f6 | b2c1 | **search_depth** | d4:975, d5:975, d6:975, d7:0, d8:0, d9:0 | - | None | yes | `8/6p1/5b1p/p2k3P/Pp2p1P1/1P6/1B2K3/8 w - - 9 45` |
| st-082 | 462 | g7e6 | f6d4 | **search_depth** | d4:0, d5:0, d6:462, d7:462, d8:0, d9:0 | - | None | no | `r1b1r1k1/5pn1/2p2qN1/3p2R1/1p1P4/pP1P1P2/P2Q3P/2KN2R1 b - - 0 25` |
| st-024 | 422 | c4b5 | e3d3 | **evaluation** | d4:422, d5:422, d6:422, d7:422, d8:422, d9:422 | - | None | yes | `8/2p5/3p3p/pp1Pk1p1/2P3P1/PP2K2P/8/8 w - - 0 40` |
| st-079 | 292 | a6b7 | g1g2 | **search_depth** | d4:0, d5:0, d6:292, d7:0, d8:0, d9:0 | - | None | no | `4rbk1/3q3p/Q5p1/2pp2B1/3np2P/P5P1/8/1R3RK1 w - - 2 34` |
| st-068 | 245 | c8b8 | h7h6 | **unresolved** | d4:245, d5:245, d6:245, d7:245, d8:276, d9:276 | - | None | no | `2r3k1/3Q2pp/4p3/4Pp2/1PqPbP2/2p4P/5RPK/2R5 b - - 12 37` |
| st-005 | 178 | b8c8 | b8d8 | **pruning** | d4:178, d5:227, d6:178, d7:178, d8:178, d9:227 | lmr_off | None | no | `1r4k1/8/R7/1r4p1/2NPnp2/1nB5/1PK5/7R b - - 1 43` |
| st-107 | 144 | g1f3 | f2f4 | **search_depth** | d4:0, d5:0, d6:144, d7:144, d8:0, d9:0 | - | None | yes | `3q4/pQ1n1pk1/2p1p1p1/2PpP1br/3P4/4B3/P4PK1/1R4N1 w - - 14 36` |
| st-011 | 142 | d1d2 | f2e3 | **unresolved** | d4:142, d5:142, d6:142, d7:142, d8:142, d9:142 | - | None | no | `5r2/1p1r2k1/p1p1n1p1/P2pP2p/1R3p1P/2P1nP1K/1PB2BP1/3R4 w - - 14 39` |
| st-088 | 128 | e2c4 | g4g5 | **search_depth** | d4:128, d5:128, d6:128, d7:29, d8:29, d9:29 | lmr_off, see_qs_off | None | yes | `r4rk1/3b1ppp/Pq2pb2/1P1p4/2pNn1P1/4PN2/2Q1BPP1/RR4K1 w - - 1 25` |
| st-084 | 104 | e8c8 | c7c6 | **pruning** | d4:104, d5:104, d6:104, d7:104, d8:104, d9:0 | lmr_off | None | yes | `4r1k1/p1p2ppp/7r/8/3P4/PP2PP2/1B2KP1P/2R5 b - - 2 31` |
| st-106 | 104 | d4d3 | d8h8 | **search_depth** | d4:8, d5:104, d6:104, d7:8, d8:8, d9:104 | - | None | yes | `3r4/8/kn2p1Q1/p3P3/2pq3P/2N5/PP6/1K3R2 b - - 0 39` |
