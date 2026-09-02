# Material-only fit

K = 185 cp. Ten parameters, everything else frozen. Ridge on deltas, bounds [0.6x, 1.5x] of production.

## Subset: all positions  (train 4340, val 928, test 935)

### Lambda sweep (selected on validation)

| lambda | ‖delta‖ max | val ES-MSE | val MAE | val Huber | Δ ES-MSE vs current |
|---|---|---|---|---|---|
| 100 | 0 | 0.06572 | 128.0 | 9172 | -0.00000 |
| 30 | 0 | 0.06571 | 128.0 | 9171 | -0.00000 |
| 10 | 0 | 0.06572 | 128.0 | 9172 | -0.00000 |
| 3 | 0 | 0.06571 | 128.0 | 9172 | -0.00000 |
| 1 | 0 | 0.06571 | 128.0 | 9171 | -0.00001 |
| 0.3 | 0 | 0.06569 | 128.0 | 9169 | -0.00003 |
| 0.1 | 1 | 0.06564 | 127.9 | 9164 | -0.00008 |
| 0.03 | 4 | 0.06549 | 127.8 | 9149 | -0.00022 |
| 0 | 410 | 0.06268 | 121.6 | 8503 | -0.00303 |
| current | 0 | 0.06572 | 128.0 | 9172 | — |

### Chosen lambda = 0 (strongest within 2% of best validation loss)

| piece | MG now | MG fit | Δ | EG now | EG fit | Δ |
|---|---|---|---|---|---|---|
| pawn | 82 | 80 | -2 | 94 | 141 | +47 |
| knight | 337 | 202 | -135 | 281 | 404 | +123 |
| bishop | 365 | 219 | -146 | 297 | 402 | +105 |
| rook | 477 | 321 | -156 | 512 | 674 | +162 |
| queen | 1025 | 615 | -410 | 936 | 1253 | +317 |

### Held-out test (touched once)

| set | ES-MSE now | ES-MSE fit | MAE now | MAE fit | Huber now | Huber fit |
|---|---|---|---|---|---|---|
| train | 0.07165 | 0.06838 | 150.1 | 143.5 | 11240 | 10579 |
| val | 0.06572 | 0.06268 | 128.0 | 121.6 | 9172 | 8503 |
| test | 0.06670 | 0.06367 | 152.6 | 144.7 | 11522 | 10767 |

### Chess plausibility

| balance | value (cp) |
|---|---|
| Q vs 2R (MG) | -27 |
| Q vs 2R (EG) | -94 |
| Q vs R+B (MG) | +75 |
| Q vs R+B (EG) | +177 |
| R vs B+N (MG) | -100 |
| R vs B+N (EG) | -133 |
| B vs N (MG) | +17 |
| B vs N (EG) | -2 |
| 3P vs N (MG) | +38 |
| 3P vs N (EG) | +19 |
| R vs N+2P (MG) | -41 |
| R vs N+2P (EG) | -12 |
| exchange R-B (MG) | +102 |
| exchange R-B (EG) | +272 |

ordering Q > R > minor > P in both phases: **yes**

## Subset: quiet (tol 30)  (train 2668, val 557, test 576)

### Lambda sweep (selected on validation)

| lambda | ‖delta‖ max | val ES-MSE | val MAE | val Huber | Δ ES-MSE vs current |
|---|---|---|---|---|---|
| 100 | 0 | 0.04959 | 80.9 | 4775 | -0.00000 |
| 30 | 0 | 0.04959 | 80.9 | 4774 | -0.00000 |
| 10 | 0 | 0.04959 | 80.9 | 4774 | -0.00000 |
| 3 | 0 | 0.04959 | 80.9 | 4774 | -0.00000 |
| 1 | 0 | 0.04958 | 80.9 | 4773 | -0.00001 |
| 0.3 | 0 | 0.04956 | 80.9 | 4771 | -0.00003 |
| 0.1 | 2 | 0.04949 | 80.8 | 4762 | -0.00010 |
| 0.03 | 5 | 0.04932 | 80.7 | 4741 | -0.00027 |
| 0 | 468 | 0.04497 | 79.2 | 4529 | -0.00462 |
| current | 0 | 0.04959 | 80.9 | 4775 | — |

### Chosen lambda = 0 (strongest within 2% of best validation loss)

| piece | MG now | MG fit | Δ | EG now | EG fit | Δ |
|---|---|---|---|---|---|---|
| pawn | 82 | 121 | +39 | 94 | 141 | +47 |
| knight | 337 | 506 | +168 | 281 | 422 | +140 |
| bishop | 365 | 530 | +165 | 297 | 407 | +110 |
| rook | 477 | 688 | +211 | 512 | 736 | +224 |
| queen | 1025 | 1210 | +185 | 936 | 1404 | +468 |

### Held-out test (touched once)

| set | ES-MSE now | ES-MSE fit | MAE now | MAE fit | Huber now | Huber fit |
|---|---|---|---|---|---|---|
| train | 0.05266 | 0.04980 | 88.8 | 85.9 | 5360 | 5117 |
| val | 0.04959 | 0.04497 | 80.9 | 79.2 | 4775 | 4529 |
| test | 0.04661 | 0.04398 | 77.6 | 76.8 | 4321 | 4258 |

### Chess plausibility

| balance | value (cp) |
|---|---|
| Q vs 2R (MG) | -167 |
| Q vs 2R (EG) | -67 |
| Q vs R+B (MG) | -9 |
| Q vs R+B (EG) | +261 |
| R vs B+N (MG) | -347 |
| R vs B+N (EG) | -93 |
| B vs N (MG) | +25 |
| B vs N (EG) | -15 |
| 3P vs N (MG) | -141 |
| 3P vs N (EG) | +2 |
| R vs N+2P (MG) | -60 |
| R vs N+2P (EG) | +32 |
| exchange R-B (MG) | +158 |
| exchange R-B (EG) | +329 |

ordering Q > R > minor > P in both phases: **yes**

