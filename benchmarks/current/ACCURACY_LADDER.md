# Accuracy ladder — CLAUDESHARK_ACCURACY_V1 (`ACCURACY_STANDARD.md`)

Updated 2026-09-06 12:20 UK. Headline reliability number: **minimum
single-game accuracy**. All rows use the same frozen metric and oracle;
rows against different opponents are not like-for-like in difficulty.

| BUILD | OPPONENT / TARGET | GAMES | W/D/L | SCORE | ELO | MEAN ACC | MEDIAN | MIN | P10 | >= 99.5 | < 99.5 | < 99 | < 98 | ACPL_V1 | >= 100CP | >= 300CP | FLIPS | CLOCK FLOOR | FAILURES |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RC-C | ~2300 A, dev, strict | 100 | +44 =24 −32 | 56.0% | +42 | 93.01 | 93.31 | **80.50** | 89.1 | 0 | 100 | 100 | 97 | 44.8 | 8.36% | 1.69% | 153 | 5.2 s | 0 |
| C5 | ~2300 A, dev, strict (screen) | 60 | +32 =6 −22 | 58.3% | +58 | 93.10 | 93.59 | **79.87** | 88.4 | 0 | 60 | 60 | 59 | 42.9 | 8.30% | 2.14% | 67 | 8.4 s | 0 |
| C5 | ~2400 A, dev2400, strict (baseline) | 100 | +40 =31 −29 | 55.5% | +38 | 94.64 | 95.16 | **83.58** | 89.6 | 3 | 97 | 93 | 89 | 40.6 | 6.54% | 1.44% | 102 | 6.0 s | 0 |
| C8 (prop. time) | C5, dev, strict (internal screen; paired control below) | 60 | +21 =17 −22 | 49.2% | −6 | 92.86 | 93.00 | 83.92 | 89.4 | 0 | 60 | 60 | 60 | 36.6 | 8.29% | 1.38% | 124 | 8.0 s | 0 |
| C5 (control) | C8, same 60 games | 60 | +22 =17 −21 | 50.8% | +6 | 92.86 | 93.19 | 81.96 | 89.5 | 0 | 60 | 60 | 60 | 36.2 | 8.60% | 1.26% | 130 | 8.4 s | 0 |

Reading: the engine's play is about 93–95% accurate on V1 with a floor near
80%; 3 of 260 scored games reach 99.5%. The 99.5%-in-every-game target is
not within reach of any build measured so far and is not claimed; the
programme reports the whole distribution and moves the floor. For scale,
AlphaFish's platform accuracy of 99.4% mean corresponds to roughly 97.5 on
V1 (`ACCURACY_STANDARD.md`, calibration).

Per-game tables: `2026-09-06-rcc-2300-strict-accuracy.md`,
`2026-09-06-c5-2300-accuracy.md`, `2026-09-06-c5-2400-accuracy.md`.
