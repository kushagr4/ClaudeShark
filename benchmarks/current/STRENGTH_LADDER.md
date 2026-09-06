# Strength ladder — RC-C → ~2300 → ~2400 programme

Updated 2026-09-05 23:36 UK. Source of truth for the external-strength
programme; the champion and submission identity stay in `spec.md` §2.

CURRENT CHAMPION: RC-C (`champions/rc_c`, archive `corpus/release/claudeshark_rc_c.zip`,
sha256 `1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`; submitted 23:14 UK)

CURRENT EXTERNAL TARGET: ~2300 BENCHMARK-A (definition: `STRENGTH_BENCHMARK_2300.md`)

| item | value |
|---|---|
| 2300 BASELINE (auto draw claim — SUPERSEDED, evidence only) | RC-C vs benchmark A with `--draw-claim auto` (dev set, 23:34–00:44): +49 =29 −22, 63.5%, +96 Elo, bootstrap 55.5%..71.0%, 35/50 informative, White 70.0% / Black 57.0%, 0 failures, mean 96 plies, our clock floor 3.8 s (1 game under 5 s, largest think 11.8 s). **All 29 draws were auto-claims, 18 on Stockfish's behalf while it was winning** (`STRENGTH_BENCHMARK_2300.md`, amendment); a strict-claim reading is nearer 50%. `corpus/strength/games/rcc_vs_sf2300_dev_100.jsonl` + `.pgn`, `swissrisk_rcc_sf2300_dev.txt` |
| 2300 BASELINE (strict draw claim — OFFICIAL) | **RC-C_2300_BASELINE_STRICT (dev set, 01:13–02:25): +44 =24 −32, 56.0%, +42 Elo, bootstrap 48.0%..64.0% / −14..+100, 30/50 informative, LOO +36..+50, White 52.0% / Black 60.0%, 0 failures, mean 109 plies, our clock floor 5.2 s (largest think 10.8 s).** Score clears 55% but the lower bound does not clear 50%: on this set the 2300 stage would need the confirmation route. `corpus/strength/games/rcc_vs_sf2300_dev_100_strict.jsonl` + `.pgn`, `swissrisk_rcc_sf2300_dev_strict.txt` |
| 2300 BEST RESULT | 56.0% (RC-C strict baseline; no candidate yet) |
| 2300 PASSED? | NO |
| 2400 BASELINE | — |
| 2400 BEST RESULT | — |
| 2400 PASSED? | NO |
| CURRENT >=100CP ERROR RATE | **8.95%** of our moves (360 of 4,023; >=300 cp 1.39%; average loss 79.7 cp; 4.50 errors per loss; 135 result-flipping) — auto-claim baseline games, `2026-09-06-rcc-2300-error-audit.md` |
| DOMINANT ERROR CLASSES | by result-flipping from live positions (120 largest): TACTICAL HORIZON 19, UNKNOWN/MIXED 16, SEARCH INSTABILITY 10, EVALUATION optimism 7 (optimism is the largest by count, 39, but mostly deepens already-lost positions) |
| CURRENT CANDIDATE | **C4 instability-triggered time extension** (`kushagra/c4-instability-extension`; pre-registration `2026-09-06-c4-instability-extension-prereg.md`); Gate 0: fingerprint 1,708,269 with the switch on and off |
| ACTIVE JOB | see `V2_ACTIVE_STATE.md` §8 |
| NEXT ACTION | C4 Gate 1 (instability probe + replay of 57 targets and 120 negatives at a 60 s clock), then 60-game screens |

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
