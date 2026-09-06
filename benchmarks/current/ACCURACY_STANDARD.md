# Accuracy standard — CLAUDESHARK_ACCURACY_V1 (frozen 2026-09-06 12:10 UK)

| field | value |
|---|---|
| METRIC NAME | `CLAUDESHARK_ACCURACY_V1` (per game, per player) and `ACPL_V1` |
| FORMULA | per move of the scored player, with `cp_before` = the oracle's score of the position before the move and `cp_after` = the oracle's score after it, both from the mover's side and **clamped to ±1000** (mate scores become ±1000): `win(cp) = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)`; `move_accuracy = clamp(103.1668 * exp(-0.04354 * (win(cp_before) - win(cp_after))) - 3.1669, 0, 100)`. **Game accuracy = the arithmetic mean of `move_accuracy` over every move the player made in the game**, from the first move after the start position; no move is excluded (no book, no "forced" filter, no truncation at decided positions). `ACPL_V1` = mean over the same moves of `min(cp_loss, 1000)` where `cp_loss = max(0, best_cp_before - cp_after)` from the mover's side |
| TOOL | `tools/strength/accuracy.py` over the games schema produced by `tools.postmortem.annotate` (fields `sf_cp_white_before`, `sf_cp_white_after`, `cp_loss`, `turn`) |
| ORACLE | Stockfish 18 (`stockfish-windows-x86-64-avx2.exe`, sha256 prefix `c86215fa1977d53b`), single thread, node-limited: every position at 200,000 nodes, every position before/after a move losing >= 50 cp at that budget (and the last two moves of a game) re-scored at 1,000,000 nodes; the deeper number is used wherever it exists (`tools.postmortem.annotate --cheap 200000 --deep 1000000 --refine-at 50`) |
| MATE HANDLING | the annotator writes ±10,000 for mate scores; the accuracy formula clamps them to ±1000 so a mate-in-N versus a mate-in-N+3 is not an "error" and a mated player's last moves are not scored at −∞. `ACPL_V1` winsorises at 1000 |
| BOTH COLOURS | scored identically by construction (mover's view) |
| EARLY TERMINATION | a game that ends early (checkmate, repetition, adjudication) contributes only the moves it contains; a 20-move game and a 120-move game count equally in the game-level statistics, which is exactly why the **minimum single-game accuracy** is the headline number, not the mean |
| SETTINGS THAT MUST NOT CHANGE | the Lichess constants above, the ±1000 clamp, the oracle binary and node budgets, "all moves counted", the arithmetic mean. Any change creates `V2`; V1 and V2 numbers are never compared |
| KNOWN LIMITATIONS | (1) the oracle is node-limited Stockfish 18, not the platform's Stockfish 16 depth 16, so scores differ position by position; (2) a plain mean forgives one catastrophe surrounded by many perfect moves — hence the >= 100 / >= 300 cp counts and the result-flipping count are reported beside it; (3) the clamp means the metric cannot distinguish two lost positions; (4) short games are noisier |
| RELATION TO PUBLIC CHESSATHON ACCURACY | the platform publishes per-player "accuracy" and "acpl" from "Stockfish 16 · depth 16"; its formula is not published. Calibrated on the 22 AlphaFish public games (44 player-games) that the study annotated with this oracle: `V1` sits a mean **1.9 points below** the platform's accuracy (mean absolute difference 2.0, largest 7.5); the harmonic-mean and Lichess-hybrid aggregations were far worse (largest differences 99 and 51 on games with mates), which is why the arithmetic mean was chosen. The platform's acpl is not reproduced by any local acpl definition (it evidently excludes or caps mate-scale losses differently). So: **`V1 ≈ platform − 2` with ±2 noise, and 99.5% on `V1` is a harder bar than 99.5% on the platform** |
| VERSION | V1, frozen 2026-09-06 12:10 UK. Not to be edited during the programme |

## Reporting set (every serious benchmark)

MEAN, MEDIAN, MINIMUM, P10 accuracy; games < 99.5 / < 99.0 / < 98.0; games >= 99.5; >= 50 / >= 100 / >= 300 cp error rates (share of the player's moves, positions already beyond ±800 excluded as in the audit); result-flipping error count; `ACPL_V1`; clock floor; failures. The headline reliability number is the **minimum single-game accuracy**.

## Long-term qualification (unchanged from the brief)

100 fresh held-out games with **every** game >= 99.5% on `V1`, then a second fresh 100 with the same requirement, plus 0 protocol failures and 0 avoidable >= 300 cp errors; no tuning between the two. Not claimed from any smaller sample.
