# Strength ladder — RC-C → ~2300 → ~2400 programme

Updated 2026-09-06 07:20 UK. Source of truth for the external-strength
programme; the champion and submission identity stay in `spec.md` §2.

CURRENT SUBMITTED / CONTROL: RC-C (`champions/rc_c`, archive `corpus/release/claudeshark_rc_c.zip`,
sha256 `1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`; submitted 23:14 UK)

CURRENT DEVELOPMENT CHAMPION (from 2026-09-06 06:36 UK): **C5 = RC-C + reverse
futility pruning** (`champions/c5_rfp`, branch `kushagra/c5-rfp`, engine commit
`f6c0d30`). Promoted on non-negative evidence (52.5% over 140 internal games,
+17 Elo; 58.3% external over 60; +0.46 ply at equal time); **not
release-checked, not carded, not submitted** — see
`2026-09-06-c5-rfp-prereg.md`. Later candidates are measured against C5.

CURRENT EXTERNAL TARGET: ~2300 BENCHMARK-A (definition: `STRENGTH_BENCHMARK_2300.md`)

| item | value |
|---|---|
| 2300 BASELINE (auto draw claim — SUPERSEDED, evidence only) | RC-C vs benchmark A with `--draw-claim auto` (dev set, 23:34–00:44): +49 =29 −22, 63.5%, +96 Elo, bootstrap 55.5%..71.0%, 35/50 informative, White 70.0% / Black 57.0%, 0 failures, mean 96 plies, our clock floor 3.8 s (1 game under 5 s, largest think 11.8 s). **All 29 draws were auto-claims, 18 on Stockfish's behalf while it was winning** (`STRENGTH_BENCHMARK_2300.md`, amendment); a strict-claim reading is nearer 50%. `corpus/strength/games/rcc_vs_sf2300_dev_100.jsonl` + `.pgn`, `swissrisk_rcc_sf2300_dev.txt` |
| 2300 BASELINE (strict draw claim — OFFICIAL) | **RC-C_2300_BASELINE_STRICT (dev set, 01:13–02:25): +44 =24 −32, 56.0%, +42 Elo, bootstrap 48.0%..64.0% / −14..+100, 30/50 informative, LOO +36..+50, White 52.0% / Black 60.0%, 0 failures, mean 109 plies, our clock floor 5.2 s (largest think 10.8 s).** Score clears 55% but the lower bound does not clear 50%: on this set the 2300 stage would need the confirmation route. `corpus/strength/games/rcc_vs_sf2300_dev_100_strict.jsonl` + `.pgn`, `swissrisk_rcc_sf2300_dev_strict.txt` |
| 2300 QUALIFICATION (RC-C, holdout_a, strict, 02:39–03:46) | **+50 =11 −39, 55.5%, +38 Elo, bootstrap 47.0%..64.0%**, 28/50 informative, LOO +32..+46, White 59.0% / Black 52.0%, 0 failures, clock floor 4.1 s (1 game under 5 s, largest think 9.4 s), mean 98 plies. Score ≥ 55% ✓, no failures ✓, no colour pathology ✓, lower bound > 50% ✗ → passes only via a second fresh 100-game confirmation above 50% (`holdout_b`, benchmark B). `corpus/strength/games/rcc_vs_sf2300_holdout_a_100_strict.jsonl` + `.pgn`, `swissrisk_rcc_sf2300_holdout_a_strict.txt` |
| 2300 QUALIFICATION (C5, holdout_b, strict, 07:18–08:28) | **+53 =16 −31, 61.0%, +78 Elo, bootstrap 53.0%..69.0% / +21..+139**, 30/50 informative, LOO +72..+87, White 61.0% / Black 61.0%, 0 failures, clock floor 5.1 s (largest think 13.2 s, mean 2.15 s). Score ≥ 55% ✓, no failures ✓, no colour/start pathology ✓, **lower bound > 50% ✓ (route A)**. `corpus/strength/c5/c5_vs_sf2300_holdout_b_100_strict.jsonl` + `.pgn`, `swissrisk_c5_sf2300_holdout_b_100.txt` |
| 2300 BEST RESULT | **61.0% on holdout_b — C5** (RC-C: 56.0% dev, 55.5% holdout_a) |
| 2300 PASSED? | **YES — 2300 TARGET CLEARED 2026-09-06 08:28 UK by C5** on the ~2300 BENCHMARK-A proxy (Stockfish 18 UCI_Elo 2300, strict). Build: C5 = RC-C + reverse futility pruning, `champions/c5_rfp`, branch `kushagra/c5-rfp`, engine commit `f6c0d30`; archive `corpus/release/claudeshark_rc_d.zip` (RC-D, sha256 `3dab7d89fee56a84ddb18540f52fb388f65ebb73f258de585f3a73f3329951e7`, 50,597 bytes, 14 files, release gate 15/15). Error rates: >=100 cp 8.30%, >=300 cp 2.14% (60 strict dev games). Not submitted — the user's decision (`RC_D_UPLOAD_CARD.md`) |
| 2400 BASELINE | — |
| 2400 BEST RESULT | — |
| 2400 PASSED? | NO |
| CURRENT >=100CP ERROR RATE | C5 **8.30%** (194 of 2,337 moves, 60 strict games; >=300 cp 2.14%) against RC-C **8.36%** on its 100 strict games (>=300 cp 1.69%) — the same rate; RFP bought depth, not fewer large errors. RC-C auto-claim audit (the classified one): 8.95%, `2026-09-06-rcc-2300-error-audit.md` |
| DOMINANT ERROR CLASSES | by result-flipping from live positions (120 largest): TACTICAL HORIZON 19, UNKNOWN/MIXED 16, SEARCH INSTABILITY 10, EVALUATION optimism 7 (optimism is the largest by count, 39, but mostly deepens already-lost positions) |
| CURRENT CANDIDATE | none — C5 promoted 06:36; its 60-game error audit running |
| ACTIVE JOB | C5 2300 qualification on `holdout_b` (launched 07:18; see `V2_ACTIVE_STATE.md` §8) |
| NEXT ACTION | C5's own 2300 qualification on `holdout_b` (fresh 100 games, strict), then confirmation on `holdout_c` if the lower bound does not clear 50% |

## Error-rate scoreboard

| BUILD | TARGET | GAMES | SCORE | <50CP | 50–99CP | >=100CP | >=300CP | AVG CPL | FLAGS | CLOCK FLOOR | ERRORS/LOSS | RESULT-FLIPPING ERRORS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RC-C | ~2300 A (dev, auto claim — the audited games) | 100 | 63.5% (auto) / 56.0% (strict rerun) | 81.6% | 9.4% | **8.95%** (360) | 1.39% (56) | 79.7 | 0 | 3.8 s (auto run), 5.2 s (strict) | 4.50 | 135 |
| RC-C | ~2300 A (dev, strict — like-for-like row) | 100 | 56.0% | 84.4% | 7.2% | **8.36%** (390) | 1.69% (79) | 103.6 | 0 | 5.2 s | 5.88 | 153 |
| RC-C | ~2300 A (holdout_a, strict) | 100 | 55.5% | not audited | | | | | 0 | 4.1 s | | |
| C5 | ~2300 A (dev, strict, 60-game screen) | 60 | 58.3% | 82.9% | 8.8% | **8.30%** (194) | 2.14% (50) | 128.2 | 0 | 8.4 s | 5.50 | 67 |

## Start sets (frozen, `corpus/strength/FROZEN.md`)

dev 50 / val 40 (positions internal arenas already used); holdout_a 50 /
holdout_b 50 (never played by any internal arena). Qualification uses
holdout_a, confirmation holdout_b; neither is inspected during design.

## Promotion log

| BASELINE | CANDIDATE | COMMIT | FEATURE | GATES | EXTERNAL RESULT | INTERNAL RESULT | ERROR-RATE CHANGE | PROMOTION REASON |
|---|---|---|---|---|---|---|---|---|
| RC-C | C4 instability time extension | `db0fb1c` | soft budget ×1.6 once per move after an unstable iteration | Gate 0 PASS, Gate 1 FAIL | — | — | targets 38 → 34 at +44% time; trigger on 64% of ordinary moves | REJECTED |
| RC-C | **C5 reverse futility pruning** | `f6c0d30` | static − 120·depth ≥ beta fails high at depth ≤ 3, null window, not in check | Gate 0 PASS; Gate 1 suite PASS (targets missed by one, deviation recorded) | 58.3% / 60 vs benchmark A strict (baseline 56.0%) | 52.5% / 140 vs RC-C, +17 Elo, 49 informative, bootstrap 45.7–59.3%, LOO +13..+23 | ≥100 cp 8.30% vs 8.36% (flat); ≥300 cp 2.14% vs 1.69% (50 vs 79 events, within noise) | non-negative internally, positive externally and on the equal-time suite; development champion, not submitted |
