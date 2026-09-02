# Move-quality simulation: material candidate 'quiet (tol 30)'

MG [121, 506, 530, 688, 1210]  EG [141, 422, 407, 736, 1404]
(production MG [82, 337, 365, 477, 1025], EG [94, 281, 297, 512, 936])

## Runtime

| | evals/s |
|---|---|
| production values | 219,774 |
| candidate values | 218,173 |
| ratio | 0.993 |

## competition_like_v1.jsonl, depth 6

| metric | current | candidate | Δ |
|---|---|---|---|
| agree | 37.1% | 37.9% | 0.8% |
| le25 | 65.8% | 67.9% | 2.1% |
| le50 | 77.1% | 77.5% | 0.4% |
| robust | 35.3 | 30.8 | -4.5 |
| serious | 10.0% | 8.8% | -1.3% |
| catastrophic | 1.7% | 0.8% | -0.8% |

moves changed: 53/240  (better by >10cp: 27, worse: 18, neutral: 8)

## The seven persistent evaluation failures

| id | current move / loss | candidate move / loss | oracle |
|---|---|---|---|
| cl-170 | h3e6 / 484 | h3e6 / 484 | b2c3 |
| cl-097 | c1b3 / 334 | e7c7 / 22 | g2g4 |
| cl-125 | c4e3 / 225 | c4e3 / 225 | c4a3 |
| cl-144 | c4e4 / 204 | c4e4 / 204 | c4e2 |
| cl-202 | e3a7 / 195 | e3a7 / 195 | e2d4 |
| cl-094 | b5h5 / 175 | b5h5 / 175 | b5b4 |
| cl-198 | a2a1 / 165 | a2a1 / 165 | b8a7 |
