# Tuning audit

6203 positions. Sigmoid scale K fitted on the current evaluator: **185 cp** per unit logit.

## 1. Why the retained regression wanted a ~-1000 cp queen

The same material design matrix, five targets. Coefficients are cp per unit of (white minus black) count, ± standard error.

n = 6203

| variant | pawn MG | knight MG | bishop MG | rook MG | queen MG | pawn EG | knight EG | bishop EG | rook EG | queen EG |
|---|---|---|---|---|---|---|---|---|---|---|
| A retained (clip oracle, raw static) | -42±5 | -300±10 | -319±10 | -380±18 | -1174±38 | +45±6 | +45±15 | +21±15 | -23±21 | +201±46 |
| B no clipping | -70±14 | -400±29 | -430±30 | -632±54 | -1730±113 | +103±17 | +520±44 | +525±44 | +794±62 | +1835±136 |
| C both clipped | -39±5 | -288±10 | -307±10 | -358±18 | -857±38 | +53±6 | +103±15 | +83±15 | +71±21 | +259±46 |
| F depth-1 residual, both clipped | -3±4 | -26±8 | -31±8 | -50±15 | -164±32 | +54±5 | +125±12 | +102±12 | +153±17 | +299±38 |
| D direct: clip(oracle) ~ material | +37±5 | +45±10 | +61±11 | +79±19 | -178±40 | +153±6 | +318±15 | +318±16 | +481±22 | +1137±48 |
| D' direct: raw oracle ~ material | +9±14 | -55±29 | -50±30 | -172±54 | -734±114 | +211±17 | +792±44 | +822±45 | +1299±63 | +2772±138 |

Production values: MG pawn 82, knight 337, bishop 365, rook 477, queen 1025 / EG pawn 94, knight 281, bishop 297, rook 512, queen 936

### The mechanism, shown directly

Split by queen balance. Under variant A the oracle is clipped at ±600 but the static score is not, so every queen-up position carries a large negative residual that has nothing to do with what a queen is worth:

| queen balance | n | mean static | mean oracle | mean clip(oracle) | mean residual (A) |
|---|---|---|---|---|---|
| white +Q | 90 | +524 | +317 | +197 | -327 |
| even | 6038 | +11 | +24 | +23 | +12 |
| black +Q | 75 | -509 | -417 | -163 | +346 |

## 2. Quiet subset

| tolerance (cp) | kept | dropped | queen MG (A) | queen MG (C) | queen MG (D) |
|---|---|---|---|---|---|
| 0 | 85 | 6118 | +0 | +0 | +0 |
| 15 | 2621 | 3582 | -240 | -264 | +645 |
| 30 | 3801 | 2402 | -383 | -319 | +553 |
| 60 | 4307 | 1896 | -342 | -289 | +605 |
| 100 | 4525 | 1678 | -343 | -273 | +606 |
| all (no tactical filter) | 4674 | 1529 | -580 | -494 | +329 |

Full coefficient table on the quiet subset (tolerance 30 cp):

n = 3801

| variant | pawn MG | knight MG | bishop MG | rook MG | queen MG | pawn EG | knight EG | bishop EG | rook EG | queen EG |
|---|---|---|---|---|---|---|---|---|---|---|
| A retained (clip oracle, raw static) | -9±5 | -62±18 | -73±18 | -122±26 | -383±76 | +65±6 | +230±19 | +200±19 | +321±27 | +570±69 |
| B no clipping | -9±5 | -66±18 | -77±19 | -126±26 | -414±77 | +70±6 | +261±19 | +236±20 | +362±28 | +665±70 |
| C both clipped | -8±5 | -59±18 | -70±18 | -117±26 | -319±75 | +67±6 | +237±19 | +208±19 | +331±27 | +565±69 |
| F depth-1 residual, both clipped | -7±5 | -58±18 | -68±18 | -112±25 | -319±74 | +67±5 | +231±19 | +204±19 | +325±27 | +562±68 |
| D direct: clip(oracle) ~ material | +59±6 | +243±20 | +268±20 | +288±28 | +553±82 | +178±6 | +518±21 | +510±21 | +843±30 | +1498±75 |
| D' direct: raw oracle ~ material | +59±6 | +240±20 | +263±20 | +284±29 | +522±84 | +183±6 | +550±21 | +546±21 | +884±30 | +1593±76 |

Production values: MG pawn 82, knight 337, bishop 365, rook 477, queen 1025 / EG pawn 94, knight 281, bishop 297, rook 512, queen 936

## 3. Baseline error of the current evaluator

Static evaluator, white POV, against the oracle. ES-MSE is mean squared error in expected score after the sigmoid, which is the target the tuner optimises.

| subset | n | MAE | median AE | Huber | corr | ES-MSE |
|---|---|---|---|---|---|---|
| train | 4340 | 150 | 74 | 11240 | 0.272 | 0.0716 |
| val | 928 | 128 | 66 | 9172 | 0.472 | 0.0657 |
| test | 935 | 153 | 70 | 11522 | 0.309 | 0.0667 |
| middlegame (phase>=13) | 4571 | 139 | 67 | 10208 | 0.187 | 0.0688 |
| endgame (phase<13) | 1632 | 171 | 97 | 13116 | 0.502 | 0.0733 |
| materially balanced | 5046 | 96 | 59 | 6115 | 0.292 | 0.0585 |
| materially imbalanced | 1157 | 369 | 215 | 32160 | 0.302 | 0.1203 |
| quiet subset (tol 30) | 3801 | 86 | 56 | 5116 | 0.731 | 0.0513 |
