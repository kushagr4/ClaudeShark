# hanging_pieces: evaluation feature or search signal?

Residual = clip(oracle) - clip(engine score at depth). Full 56-column feature regression; the hanging_pieces row only.

## all positions (n = 6203)

| engine score | residual R² (all feats) | hanging MG cp | ±se | hanging EG cp | ±se | drop-one ΔR² | mean |residual| |
|---|---|---|---|---|---|---|---|
| static (depth 0) | 0.319 | -40.3 | 8.5 | -137.6 | 14.8 | 0.0245 | 121 |
| depth 1 | 0.134 | +10.6 | 7.2 | -57.0 | 12.6 | 0.0031 | 94 |
| depth 3 | 0.139 | +4.3 | 6.7 | -48.0 | 11.7 | 0.0029 | 88 |

## quiet subset (tol 30) (n = 3801)

| engine score | residual R² (all feats) | hanging MG cp | ±se | hanging EG cp | ±se | drop-one ΔR² | mean |residual| |
|---|---|---|---|---|---|---|---|
| static (depth 0) | 0.181 | -34.9 | 11.5 | -18.7 | 18.0 | 0.0041 | 85 |
| depth 1 | 0.178 | -23.3 | 11.3 | -17.5 | 17.8 | 0.0022 | 84 |
| depth 3 | 0.185 | -24.1 | 10.6 | -12.8 | 16.7 | 0.0023 | 79 |

## What quiescence does to positions with a hanging piece

| group | n | mean (depth1 - static) | mean |oracle - static| | mean |oracle - depth1| | mean |oracle - depth3| |
|---|---|---|---|---|---|
| hanging ≠ 0 | 901 | -4 | 222 | 115 | 104 |
| hanging = 0 | 5302 | +1 | 104 | 90 | 85 |
