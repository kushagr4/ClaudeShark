# Move-quality simulation: material candidate 'scale 1.47'

MG [121, 495, 537, 701, 1507]  EG [138, 413, 437, 753, 1376]
(production MG [82, 337, 365, 477, 1025], EG [94, 281, 297, 512, 936])

## Runtime

| | evals/s |
|---|---|
| production values | 221,592 |
| candidate values | 220,860 |
| ratio | 0.997 |

## competition_like_v1.jsonl, depth 6

| metric | current | candidate | Δ |
|---|---|---|---|
| agree | 37.1% | 37.5% | 0.4% |
| le25 | 65.8% | 65.4% | -0.4% |
| le50 | 77.1% | 77.5% | 0.4% |
| robust | 35.3 | 33.2 | -2.1 |
| serious | 10.0% | 9.6% | -0.4% |
| catastrophic | 1.7% | 1.7% | 0.0% |

moves changed: 60/240  (better by >10cp: 26, worse: 22, neutral: 12)

## The seven persistent evaluation failures

| id | current move / loss | candidate move / loss | oracle |
|---|---|---|---|
| cl-170 | h3e6 / 484 | h3e6 / 484 | b2c3 |
| cl-097 | c1b3 / 334 | c1b3 / 334 | g2g4 |
| cl-125 | c4e3 / 225 | c4a5 / 121 | c4a3 |
| cl-144 | c4e4 / 204 | c4e4 / 204 | c4e2 |
| cl-202 | e3a7 / 195 | e3a7 / 195 | e2d4 |
| cl-094 | b5h5 / 175 | b5h5 / 175 | b5b4 |
| cl-198 | a2a1 / 165 | a2a1 / 165 | b8a7 |
