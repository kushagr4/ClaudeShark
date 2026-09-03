# One-parameter material scale

Grid s in [1.0, 2.2] step 0.01. K refitted on train at every s. Selected on validation; test read once afterwards.

The quiet subset is the fitting set: a static evaluator is only meaningfully compared with an oracle where no tactic is pending. The all-positions curve is a robustness check, not the selector.

## Fitting set: quiet  (train 2668, val 557, test 576)

* validation argmin **s = 1.47** (K = 148); train argmin 1.22
* validation plateau within 1% of best: **s in [1.17, 1.87]** (width 0.70)

| s | K(train) | train ES-MSE | val ES-MSE | val vs s=1 |
|---|---|---|---|---|
| 1.00 | 116 | 0.04969 | 0.04406 | +0.00% |
| 1.10 | 122 | 0.04950 | 0.04352 | -1.21% |
| 1.20 | 128 | 0.04944 | 0.04315 | -2.06% |
| 1.30 | 136 | 0.04946 | 0.04300 | -2.39% |
| 1.40 | 144 | 0.04954 | 0.04294 | -2.53% |
| 1.50 | 152 | 0.04966 | 0.04294 | -2.53% |
| 1.60 | 160 | 0.04981 | 0.04298 | -2.43% |
| 1.70 | 168 | 0.04997 | 0.04306 | -2.26% |
| 1.80 | 176 | 0.05015 | 0.04316 | -2.03% |
| 1.90 | 186 | 0.05034 | 0.04336 | -1.57% |
| 2.00 | 194 | 0.05052 | 0.04348 | -1.30% |
| 2.10 | 204 | 0.05071 | 0.04369 | -0.82% |
| 2.20 | 212 | 0.05089 | 0.04382 | -0.53% |

* val (K=148): ES-MSE 0.04643 -> 0.04285 (-7.7%), MAE 80.9 -> 79.8
* test (K=148): ES-MSE 0.04401 -> 0.04290 (-2.5%), MAE 77.6 -> 79.0

## Fitting set: all  (train 4340, val 928, test 935)

* validation argmin **s = 1.00** (K = 192); train argmin 1.00
* validation plateau within 1% of best: **s in [1.00, 1.24]** (width 0.24)

| s | K(train) | train ES-MSE | val ES-MSE | val vs s=1 |
|---|---|---|---|---|
| 1.00 | 192 | 0.07164 | 0.06580 | +0.00%  <-- selected |
| 1.10 | 206 | 0.07190 | 0.06605 | +0.38% |
| 1.20 | 222 | 0.07217 | 0.06634 | +0.82% |
| 1.30 | 238 | 0.07245 | 0.06663 | +1.26% |
| 1.40 | 254 | 0.07271 | 0.06691 | +1.68% |
| 1.50 | 272 | 0.07297 | 0.06720 | +2.12% |
| 1.60 | 290 | 0.07321 | 0.06747 | +2.54% |
| 1.70 | 308 | 0.07344 | 0.06773 | +2.93% |
| 1.80 | 328 | 0.07365 | 0.06798 | +3.32% |
| 1.90 | 348 | 0.07385 | 0.06822 | +3.68% |
| 2.00 | 368 | 0.07404 | 0.06844 | +4.02% |
| 2.10 | 388 | 0.07421 | 0.06865 | +4.33% |
| 2.20 | 410 | 0.07438 | 0.06886 | +4.64% |

* val (K=192): ES-MSE 0.06580 -> 0.06580 (+0.0%), MAE 128.0 -> 128.0
* test (K=192): ES-MSE 0.06672 -> 0.06672 (+0.0%), MAE 152.6 -> 152.6

## Control: whole-evaluator scale, K free

| s | K(train) | val ES-MSE |
|---|---|---|
| 1.00 | 116 | 0.04406 |
| 1.20 | 138 | 0.04400 |
| 1.40 | 162 | 0.04404 |
| 1.60 | 184 | 0.04400 |
| 1.80 | 208 | 0.04403 |
| 2.00 | 230 | 0.04400 |

Flat across the whole grid (spread 0.00009), exactly as theory requires: for a uniform scale, s and K are the same parameter. The material scale reaches 0.04285 against this control's 0.04398, so the material/table rebalance is worth **2.6% beyond calibration**.

Any move-quality change a uniform scale produces in the real engine is search-margin calibration -- aspiration widths and delta margins are in centipawns and do not scale with it. Reported, never counted as an evaluation improvement.

## Candidate

s = 1.47, constants rounded once at construction.

| piece | MG now | MG scaled | EG now | EG scaled |
|---|---|---|---|---|
| pawn | 82 | 121 | 94 | 138 |
| knight | 337 | 495 | 281 | 413 |
| bishop | 365 | 537 | 297 | 437 |
| rook | 477 | 701 | 512 | 753 |
| queen | 1025 | 1507 | 936 | 1376 |
