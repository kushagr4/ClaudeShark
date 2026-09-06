# Strength ladder — RC-C → ~2300 → ~2400 programme

Updated 2026-09-06 07:20 UK. Source of truth for the external-strength
programme; the champion and submission identity stay in `spec.md` §2.

CURRENT SUBMITTED / CONTROL: RC-C (`champions/rc_c`, archive `corpus/release/claudeshark_rc_c.zip`,
sha256 `1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`; submitted 23:14 UK)

CURRENT DEVELOPMENT CHAMPION (from 2026-09-06 18:50 UK): **C9 = the C5 search
executed by a Numba-compiled core** (`champions/c9_numba`, branch
`kushagra/c9-numba-core`, engine commit `8131214`). Promoted on +55 =5 −0
(95.8%, +545 Elo) over 60 games vs `champions/c5_rfp`; release-checked as
RC-E (`corpus/release/claudeshark_rc_e.zip`, sha256 `fb8f8609…58aa`), **not
submitted** — `RC_E_UPLOAD_CARD.md`. Later candidates are measured against C9.
Previous: C5 (`champions/c5_rfp`, 06:36–18:50 UK, RC-D never submitted).

CURRENT EXTERNAL TARGET: ~2300 BENCHMARK-A (definition: `STRENGTH_BENCHMARK_2300.md`)

| item | value |
|---|---|
| 2300 BASELINE (auto draw claim — SUPERSEDED, evidence only) | RC-C vs benchmark A with `--draw-claim auto` (dev set, 23:34–00:44): +49 =29 −22, 63.5%, +96 Elo, bootstrap 55.5%..71.0%, 35/50 informative, White 70.0% / Black 57.0%, 0 failures, mean 96 plies, our clock floor 3.8 s (1 game under 5 s, largest think 11.8 s). **All 29 draws were auto-claims, 18 on Stockfish's behalf while it was winning** (`STRENGTH_BENCHMARK_2300.md`, amendment); a strict-claim reading is nearer 50%. `corpus/strength/games/rcc_vs_sf2300_dev_100.jsonl` + `.pgn`, `swissrisk_rcc_sf2300_dev.txt` |
| 2300 BASELINE (strict draw claim — OFFICIAL) | **RC-C_2300_BASELINE_STRICT (dev set, 01:13–02:25): +44 =24 −32, 56.0%, +42 Elo, bootstrap 48.0%..64.0% / −14..+100, 30/50 informative, LOO +36..+50, White 52.0% / Black 60.0%, 0 failures, mean 109 plies, our clock floor 5.2 s (largest think 10.8 s).** Score clears 55% but the lower bound does not clear 50%: on this set the 2300 stage would need the confirmation route. `corpus/strength/games/rcc_vs_sf2300_dev_100_strict.jsonl` + `.pgn`, `swissrisk_rcc_sf2300_dev_strict.txt` |
| 2300 QUALIFICATION (RC-C, holdout_a, strict, 02:39–03:46) | **+50 =11 −39, 55.5%, +38 Elo, bootstrap 47.0%..64.0%**, 28/50 informative, LOO +32..+46, White 59.0% / Black 52.0%, 0 failures, clock floor 4.1 s (1 game under 5 s, largest think 9.4 s), mean 98 plies. Score ≥ 55% ✓, no failures ✓, no colour pathology ✓, lower bound > 50% ✗ → passes only via a second fresh 100-game confirmation above 50% (`holdout_b`, benchmark B). `corpus/strength/games/rcc_vs_sf2300_holdout_a_100_strict.jsonl` + `.pgn`, `swissrisk_rcc_sf2300_holdout_a_strict.txt` |
| 2300 QUALIFICATION (C5, holdout_b, strict, 07:18–08:28) | **+53 =16 −31, 61.0%, +78 Elo, bootstrap 53.0%..69.0% / +21..+139**, 30/50 informative, LOO +72..+87, White 61.0% / Black 61.0%, 0 failures, clock floor 5.1 s (largest think 13.2 s, mean 2.15 s). Score ≥ 55% ✓, no failures ✓, no colour/start pathology ✓, **lower bound > 50% ✓ (route A)**. `corpus/strength/c5/c5_vs_sf2300_holdout_b_100_strict.jsonl` + `.pgn`, `swissrisk_c5_sf2300_holdout_b_100.txt` |
| 2300 BEST RESULT | **61.0% on holdout_b — C5** (RC-C: 56.0% dev, 55.5% holdout_a) |
| 2300 PASSED? | **YES — 2300 TARGET CLEARED 2026-09-06 08:28 UK by C5** on the ~2300 BENCHMARK-A proxy (Stockfish 18 UCI_Elo 2300, strict). Build: C5 = RC-C + reverse futility pruning, `champions/c5_rfp`, branch `kushagra/c5-rfp`, engine commit `f6c0d30`; archive `corpus/release/claudeshark_rc_d.zip` (RC-D, sha256 `3dab7d89fee56a84ddb18540f52fb388f65ebb73f258de585f3a73f3329951e7`, 50,597 bytes, 14 files, release gate 15/15). Error rates: >=100 cp 8.30%, >=300 cp 2.14% (60 strict dev games). Not submitted — the user's decision (`RC_D_UPLOAD_CARD.md`) |
| 2400 BASELINE (C5, dev2400, strict, 08:45–09:51) | **+40 =31 −29, 55.5%, +38 Elo, bootstrap 47.5%..63.5% / −17..+96**, 35/50 informative, LOO +32..+46, White 53.0% / Black 58.0%, 0 failures, clock floor 6.0 s (largest think 17.8 s, mean 2.25 s), terminations checkmate 68 / threefold 23 / fifty-move 6 / adjudication 2 / insufficient 1. `corpus/strength/c5/c5_vs_sf2400_dev2400_100_strict.jsonl` + `.pgn`, `swissrisk_c5_sf2400_dev2400_100.txt`. Note the sets differ from the 2300 stage (competition-like suite, not organiser starts), so 55.5% here is not comparable with the 2300 numbers |
| 2400 QUALIFICATION (C5, holdout2400_a, strict, 15:23–16:33) | **+37 =38 −25, 56.0%, +42 Elo, bootstrap 48.5%..64.0% / −10..+100**, 31/50 informative, LOO +36..+50, White 60.0% / Black 52.0%, 0 failures, clock floor 3.0 s (three 266–300-ply games living on the increment at 0.3–0.4 s per move; no flag), largest think 15.0 s. Score ≥ 55% ✓, failures ✓, colour ✓, lower bound > 50% ✗ → route B: confirmation on `holdout2400_b` above 50%. Accuracy V1: mean 94.72, median 95.39, min 86.13, p10 89.64, 3/100 ≥ 99.5, ≥100 cp 5.96%, ≥300 cp 1.10%, 120 flips. `corpus/strength/c5/c5_vs_sf2400_holdout2400_a_100_strict.*`, `2026-09-06-c5-2400-qualification-accuracy.md` |
| 2400 BEST RESULT | 56.0% on holdout2400_a (C5 qualification); 55.5% dev2400 baseline |
| 2400 CONFIRMATION (C5, holdout2400_b, strict, 16:48–17:30) | **PARTIAL-NON-DECISIVE — stopped by the user at 61/100: +21 =18 −22, 49.2%**. Not re-run: the sprint rule (2026-09-06 17:35) spends compute on new candidates, not on unchanged-C5 validation. `corpus/strength/c5/c5_vs_sf2400_holdout2400_b_100_strict.jsonl` (61 games) |
| 2400 PASSED? | **NO** — qualification 56.0% (lower bound 48.5%), confirmation partial 49.2%/61; the 2400 label is not claimed for C5 |
| 99.5% PER-GAME | **NOT PASSED** — best build: 3 of 100 games ≥ 99.5 on V1 (`ACCURACY_LADDER.md`) |
| CURRENT >=100CP ERROR RATE | C5 **8.30%** (194 of 2,337 moves, 60 strict games; >=300 cp 2.14%) against RC-C **8.36%** on its 100 strict games (>=300 cp 1.69%) — the same rate; RFP bought depth, not fewer large errors. RC-C auto-claim audit (the classified one): 8.95%, `2026-09-06-rcc-2300-error-audit.md` |
| DOMINANT ERROR CLASSES | by result-flipping from live positions (120 largest): TACTICAL HORIZON 19, UNKNOWN/MIXED 16, SEARCH INSTABILITY 10, EVALUATION optimism 7 (optimism is the largest by count, 39, but mostly deepens already-lost positions) |
| CURRENT CANDIDATE | none — C9 promoted 18:50; external calibration vs Stockfish UCI_Elo 2800 running (dev2400, 60 games) |
| ACTIVE JOB | C9 vs Stockfish UCI_Elo 2800, 60 games, dev2400, strict (from 18:53) |
| NEXT ACTION | the user's RC-E upload decision; C10 (next search candidate on the compiled core) pre-registered and screened 60 games vs `champions/c9_numba` |

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
| C5 | **C9 Numba search core** | `8131214` | the C5 algorithm (movegen, make/unmake, PeSTO eval, SEE, ordering, TT, quiescence, negamax) compiled by Numba; python-chess only parses the FEN | Gate 0 PASS: perft exact vs python-chess (6 standard + 58 random positions), eval exact on 391 positions, SEE exact on 1,620 captures, fingerprint 1,391,318 (C5 1,409,912), tactics 16/16, ladder PASS, 1,260 tests, release 16/16 | pending (vs Stockfish 2800 running) | **+55 =5 −0, 95.8% / 60 vs C5, +545 Elo, 30/30 informative, bootstrap +436..+800, LOO +538..+579, 0 failures** | not yet audited | 26× nps, +5.2 plies at 2 s; development champion, RC-E built, not submitted |
| RC-C | **C5 reverse futility pruning** | `f6c0d30` | static − 120·depth ≥ beta fails high at depth ≤ 3, null window, not in check | Gate 0 PASS; Gate 1 suite PASS (targets missed by one, deviation recorded) | 58.3% / 60 vs benchmark A strict (baseline 56.0%) | 52.5% / 140 vs RC-C, +17 Elo, 49 informative, bootstrap 45.7–59.3%, LOO +13..+23 | ≥100 cp 8.30% vs 8.36% (flat); ≥300 cp 2.14% vs 1.69% (50 vs 79 events, within noise) | non-negative internally, positive externally and on the equal-time suite; development champion, not submitted |
