# Control: whole-evaluator scale x1.47

Every evaluation constant scaled -- material, both piece-square table families, bishop pair, tempo. Search margins deliberately unchanged.

A uniform scale is statically decision-invariant, so anything that moves here is search-margin calibration, not evaluation.

| metric | current | uniform x1.47 | delta |
|---|---|---|---|
| agree | 37.1% | 35.8% | -1.3% |
| le25 | 65.8% | 64.2% | -1.7% |
| le50 | 77.1% | 76.2% | -0.8% |
| robust | 35.3 | 34.7 | -0.6 |
| serious | 10.0% | 10.0% | 0.0% |
| catastrophic | 1.7% | 1.7% | 0.0% |

moves changed: 48/240 (better by >10cp: 20, worse: 22, neutral: 6)

If this is near zero the search margins are not materially miscalibrated at this scale, and the material-scale result can be read as evaluation.
