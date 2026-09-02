# Evaluator residuals against the oracle

6203 labelled positions; oracle scores clipped to +/-600 cp; all scores from White's point of view.

## How well does the engine's own evaluation track the oracle?

| engine score | corr | R^2 vs oracle | mean |error| | median |error| |
|---|---|---|---|---|
| static evaluate() | 0.485 | 0.035 | 126 | 73 |
| depth-1 + quiescence | 0.710 | 0.502 | 95 | 61 |

## Residual regression: oracle - static score

R^2 of the residual explained by the features: **0.385** (baseline static R^2 0.035; with the fitted terms added 0.409).

Coefficients are centipawns per unit of (white minus black), middlegame and endgame fitted separately by phase taper. |t| >= 3 is well determined.

| feature | MG cp | MG t | EG cp | EG t | drop-one dR^2 |
|---|---|---|---|---|---|
| queen | -1088.5 | -27.4 | +239.2 | +3.7 | 0.1187 |
| knight | -270.3 | -23.3 | +47.8 | +2.2 | 0.0659 |
| rook | -325.3 | -17.4 | -63.7 | -2.6 | 0.0615 |
| bishop | -273.3 | -18.5 | +12.6 | +0.6 | 0.0478 |
| tempo | +27.3 | +9.2 | +55.6 | +9.7 | 0.0310 |
| hanging_pieces | -38.6 | -4.4 | -137.0 | -9.0 | 0.0205 |
| pawn | -40.1 | -6.2 | +43.5 | +4.4 | 0.0040 |
| doubled | -4.1 | -1.1 | -31.7 | -4.7 | 0.0038 |
| rook_open_file | +21.3 | +3.1 | +17.0 | +1.5 | 0.0025 |
| rook_semi_open | -0.1 | -0.0 | +49.6 | +4.1 | 0.0024 |
| pawn_chain_links | +4.1 | +1.7 | +18.4 | +3.0 | 0.0021 |
| passed_advance | +10.8 | +2.3 | +6.7 | +1.3 | 0.0015 |
| king_zone_attackers | -11.6 | -3.0 | -2.9 | -0.4 | 0.0014 |
| mobility_rook | +0.6 | +0.6 | +4.9 | +2.7 | 0.0013 |
| isolated | -1.4 | -0.4 | -16.1 | -2.8 | 0.0012 |
| backward | -6.3 | -1.1 | -23.9 | -2.3 | 0.0011 |
| mobility_knight | +2.6 | +2.1 | +3.9 | +1.1 | 0.0009 |
| mobility_bishop | +1.3 | +1.4 | +3.6 | +1.6 | 0.0007 |
| mobility_queen | +2.1 | +2.2 | -2.1 | -0.6 | 0.0005 |
| outpost | +10.6 | +1.0 | +25.5 | +1.3 | 0.0005 |
| connected_passed | +25.8 | +2.0 | -27.1 | -1.9 | 0.0005 |
| bishop_pair | -9.8 | -0.7 | +46.2 | +2.1 | 0.0005 |
| space | +7.8 | +1.8 | -0.9 | -0.1 | 0.0004 |
| passed | -22.9 | -1.6 | +7.5 | +0.4 | 0.0003 |
| king_open_files | -9.3 | -1.6 | +8.9 | +1.2 | 0.0003 |
| rook_seventh | +21.2 | +1.0 | +4.8 | +0.3 | 0.0002 |
| king_shelter | +0.2 | +0.1 | +6.7 | +1.1 | 0.0002 |
| protected_passed | +5.4 | +0.3 | +10.3 | +0.5 | 0.0001 |

## Residual regression: oracle - quiet score

R^2 of the residual explained by the features: **0.114** (baseline quiet R^2 0.502; with the fitted terms added 0.561).

Coefficients are centipawns per unit of (white minus black), middlegame and endgame fitted separately by phase taper. |t| >= 3 is well determined.

| feature | MG cp | MG t | EG cp | EG t | drop-one dR^2 |
|---|---|---|---|---|---|
| rook_open_file | +25.4 | +4.3 | +16.9 | +1.7 | 0.0063 |
| passed_advance | +19.9 | +4.9 | +2.6 | +0.6 | 0.0058 |
| king_zone_attackers | -16.4 | -4.9 | -4.8 | -0.8 | 0.0057 |
| doubled | -5.2 | -1.6 | -22.5 | -3.8 | 0.0046 |
| mobility_bishop | +2.7 | +3.4 | +4.7 | +2.3 | 0.0040 |
| king_open_files | -24.3 | -5.0 | +17.5 | +2.7 | 0.0036 |
| rook_semi_open | +10.1 | +2.2 | +26.0 | +2.5 | 0.0034 |
| pawn | -7.7 | -1.4 | +39.7 | +4.6 | 0.0033 |
| mobility_knight | +3.1 | +2.8 | +6.1 | +2.1 | 0.0030 |
| space | +6.5 | +1.8 | +15.1 | +2.6 | 0.0026 |
| queen | -143.3 | -4.2 | +173.6 | +3.1 | 0.0025 |
| mobility_rook | +1.5 | +1.8 | +3.4 | +2.2 | 0.0025 |
| passed | -46.2 | -3.8 | +13.6 | +0.9 | 0.0024 |
| pawn_chain_links | +2.4 | +1.2 | +15.6 | +3.0 | 0.0024 |
| knight | -35.5 | -3.5 | +63.5 | +3.3 | 0.0023 |
| isolated | -0.3 | -0.1 | -16.2 | -3.2 | 0.0021 |
| connected_passed | +40.3 | +3.6 | -29.3 | -2.4 | 0.0019 |
| mobility_queen | +2.4 | +2.9 | -1.8 | -0.6 | 0.0015 |
| bishop_pair | -10.8 | -0.9 | +59.2 | +3.1 | 0.0015 |
| hanging_pieces | +12.6 | +1.7 | -41.1 | -3.2 | 0.0014 |
| rook_seventh | +53.2 | +2.9 | -17.5 | -1.1 | 0.0014 |
| rook | -47.5 | -2.9 | +45.4 | +2.1 | 0.0013 |
| bishop | -33.1 | -2.6 | +26.9 | +1.4 | 0.0010 |
| backward | -5.6 | -1.1 | -11.9 | -1.3 | 0.0008 |
| outpost | +9.2 | +1.0 | +18.0 | +1.1 | 0.0006 |
| tempo | -1.3 | -0.5 | +10.1 | +2.1 | 0.0006 |
| protected_passed | +0.1 | +0.0 | +17.7 | +1.1 | 0.0002 |
| king_shelter | +1.2 | +0.4 | +2.9 | +0.5 | 0.0001 |

## Mean absolute error of the quiet score by structural tag (n >= 30)

| tag | n | mean |error| | mean signed (oracle - engine) |
|---|---|---|---|
| king_attack | 79 | 179 | -6 |
| advanced_passer | 416 | 172 | +1 |
| connected_passers | 235 | 169 | +29 |
| protected_passer | 488 | 151 | +12 |
| exchange_imbalance | 289 | 151 | +4 |
| unusual_king_placement | 84 | 148 | -9 |
| exposed_king | 960 | 143 | +0 |
| queenside_majority | 534 | 140 | +5 |
| passed_pawn | 1648 | 140 | +7 |
| space_advantage | 444 | 137 | +24 |
| rook_ending | 140 | 134 | -21 |
| complex_ending | 139 | 130 | +20 |
| opposite_side_castling | 415 | 129 | +32 |
| weak_colour_complex | 579 | 125 | +29 |
| minor_piece_ending | 191 | 124 | +8 |
| hanging_piece | 985 | 121 | +14 |
| knight_outpost | 590 | 118 | +10 |
| material_imbalance | 2783 | 116 | +12 |
| isolated_pawn | 3322 | 114 | +7 |
| rook_and_minor_ending | 763 | 114 | +6 |
| rook_on_open_file | 2345 | 114 | +8 |
| opposite_coloured_bishops | 273 | 109 | +4 |
| backward_pawn | 1828 | 107 | +8 |
| locked_pawn_chain | 301 | 106 | +15 |
| doubled_pawns | 1636 | 106 | +12 |
| bad_bishop | 1012 | 105 | +15 |
| rook_on_semi_open_file | 2287 | 103 | +11 |
| open_centre | 1826 | 102 | +12 |
| bishop_pair | 1302 | 98 | +15 |
| isolated_queen_pawn | 261 | 95 | +14 |
| maroczy_bind | 72 | 93 | +5 |
| minority_attack | 36 | 91 | +36 |
| same_side_castling | 3070 | 87 | +7 |
| closed_centre | 287 | 81 | +15 |
| queenless_middlegame | 479 | 81 | +11 |
| king_in_centre | 1185 | 79 | +18 |
| carlsbad | 225 | 71 | +7 |
