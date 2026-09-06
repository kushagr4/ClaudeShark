# Strength ladder — RC-C → ~2300 → ~2400 programme

Updated 2026-09-05 23:36 UK. Source of truth for the external-strength
programme; the champion and submission identity stay in `spec.md` §2.

CURRENT CHAMPION: RC-C (`champions/rc_c`, archive `corpus/release/claudeshark_rc_c.zip`,
sha256 `1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`; submitted 23:14 UK)

CURRENT EXTERNAL TARGET: ~2300 BENCHMARK-A (definition: `STRENGTH_BENCHMARK_2300.md`)

| item | value |
|---|---|
| 2300 BASELINE (auto draw claim — SUPERSEDED, evidence only) | RC-C vs benchmark A with `--draw-claim auto` (dev set, 23:34–00:44): +49 =29 −22, 63.5%, +96 Elo, bootstrap 55.5%..71.0%, 35/50 informative, White 70.0% / Black 57.0%, 0 failures, mean 96 plies, our clock floor 3.8 s (1 game under 5 s, largest think 11.8 s). **All 29 draws were auto-claims, 18 on Stockfish's behalf while it was winning** (`STRENGTH_BENCHMARK_2300.md`, amendment); a strict-claim reading is nearer 50%. `corpus/strength/games/rcc_vs_sf2300_dev_100.jsonl` + `.pgn`, `swissrisk_rcc_sf2300_dev.txt` |
| 2300 BASELINE (strict draw claim — OFFICIAL) | pending: rerun on the same dev set with `--draw-claim strict` after the error audit finishes |
| 2300 BEST RESULT | — (no valid baseline yet) |
| 2300 PASSED? | NO |
| 2400 BASELINE | — |
| 2400 BEST RESULT | — |
| 2400 PASSED? | NO |
| CURRENT >=100CP ERROR RATE | not yet measured on this benchmark (RC-B R16–R20 public estimate ≈ 14.5% of moves, unmatched population) |
| DOMINANT ERROR CLASSES | not yet classified |
| CURRENT CANDIDATE | none (baseline first) |
| ACTIVE JOB | RC-C_2300_BASELINE, PID 15968 (see `V2_ACTIVE_STATE.md` §8) |
| NEXT ACTION | oracle error audit of the baseline games, then mechanism ranking |

## Error-rate scoreboard

| BUILD | TARGET | GAMES | SCORE | <50CP | 50–99CP | >=100CP | >=300CP | AVG CPL | FLAGS | CLOCK FLOOR | ERRORS/LOSS | RESULT-FLIPPING ERRORS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RC-C | ~2300 A (dev) | pending | | | | | | | | | | |

## Start sets (frozen, `corpus/strength/FROZEN.md`)

dev 50 / val 40 (positions internal arenas already used); holdout_a 50 /
holdout_b 50 (never played by any internal arena). Qualification uses
holdout_a, confirmation holdout_b; neither is inspected during design.

## Promotion log

| BASELINE | CANDIDATE | COMMIT | FEATURE | GATES | EXTERNAL RESULT | INTERNAL RESULT | ERROR-RATE CHANGE | PROMOTION REASON |
|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — |
