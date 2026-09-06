# ~2400 BENCHMARK-A — definition (frozen 2026-09-06 08:50 UK, before any result was seen)

Identical to `STRENGTH_BENCHMARK_2300.md` except for the strength limit and
the start sets. A **proxy**, labelled "~2400 BENCHMARK", not "exactly 2400
Chess.com".

| field | value |
|---|---|
| OPPONENT IMPLEMENTATION | Stockfish 18, `stockfish-windows-x86-64-avx2.exe` (sha256 prefix `c86215fa1977d53b`) |
| SETTINGS | `UCI_LimitStrength true`, **`UCI_Elo 2400`**, `Threads 1`, `Hash 16`; no book, no tablebases, no pondering; fresh process per game |
| TIME CONTROL | 120 s + 0.5 s per side, 300-ply cap, **`--draw-claim strict`** |
| RATING CALIBRATION SOURCE | Stockfish's documentation: "calibrated at a time control of 120s+1s and anchored to CCRL 40/4" — CCRL, not Chess.com |
| START SETS | `corpus/strength/dev2400.jsonl` (50), `val2400.jsonl` (40), `holdout2400_a.jsonl` (50), `holdout2400_b.jsonl` (50): drawn with seed 20260906 from `corpus/competition_like_v1.jsonl`, the 240-position competition-like suite that has served only as a move-quality suite and never as game starts; positions overlapping any 2300 set removed. Hashes in `corpus/strength/FROZEN.md` |
| WHY NOT ORGANISER STARTS | every observed organiser start position (239 minus ours) is already committed to the 2300 sets; the competition-like suite is the nearest reproducible substitute and is documented as such |
| HARNESS / MACHINE | as the 2300 definition |

## Limitations

All of the 2300 definition's, plus: the 2400 sets are synthesised
competition-like positions, not organiser starts, so a 2300→2400 comparison
across stages is not like-for-like; within the stage every build plays the
same sets.

## Pass standard (unchanged)

Qualification on `holdout2400_a`: score >= 55%, no critical failures, no
colour/start pathology, and either a family-bootstrap lower bound above 50%
or a second fresh 100 games above 50% on `holdout2400_b`.
