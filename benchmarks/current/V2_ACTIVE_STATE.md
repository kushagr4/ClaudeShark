# Active research state — read this first after any compaction

This file, the repository and `benchmarks/current/V2_10H_SUMMARY.json` are the
source of truth. Conversational memory is not. After a compaction: read this
file, run `git status` and `git log --oneline origin/main..HEAD`, check the
running jobs listed in section 6 by tailing their output paths, then continue
from section 8. **Do not restart anything in section 6 that is still running or
already complete.**

## 1. Clock

* Session start: **2026-09-04 09:37:20 +0100**
* Target finish: approximately **19:37 local**
* Last update to this file: 11:15

## 2. Repository

* Branch **`v2.2-development`**, HEAD `679f491` at the time of writing (check
  `git log` for later commits).
* `rated-v1` → `98c48c89b3a8142e6567e5f46b2d2036df7297d1`; `main` and
  `origin/main` identical and untouched.
* Git identity `kushagr4 <ratrakushagra@gmail.com>` on every commit.
* **Nothing has been pushed.** `origin/v2.2-development` is still at `a116be2`.
* Deterministic fingerprint with every experimental term off:
  `uv run python -m tools.bench --depth 6` → **1,712,405 nodes** (matches rated V1).
* Full suite last run: **1,186 tests passed**, `ruff check .` clean.

## 3. Champions

| role | directory | status |
|---|---|---|
| rated baseline | `champions/rated_v1` | immutable |
| V2 champion **under challenge** | `champions/v2_1_kingpawn` | see section 5 |
| frozen, not promoted | `champions/v2_2a_low_material` | Gate 1 pass, no game effect |
| derived variants | `champions/v2_1_kingpawn_tempo{16,24,32}`, `_sf{60,75,90}` | single-constant, built by `tools.make_time_variants` |

V2.1 Daily package `corpus/v2/kp/submission_v2_1_kingpawn.zip`, SHA-256
`a8b95a5cab3e33aaac6e5d3e686eb7f292d3a600a115e18e077b9622f35bbd0a`.

## 4. Experiments completed and their verdicts

| id | verdict | record |
|---|---|---|
| V2.2a low-material | **KEEP FOR MORE TESTING, not promoted** — Gate 1 pass, Gate 2 has 1 informative cluster of 100 | `2026-09-04-v2.2a-low-material.md` |
| colour asymmetry audit | **no engine defect**; evaluator exact 600/600, search noise non-directional, no colour in the clock code | `2026-09-04-colour-asymmetry-audit.md` |
| cluster-evidence audit | mop-up +3 Elo rests on 2 informative clusters of 100; V2.1's +19 on 41 | `corpus/daily/cluster_evidence.txt` |
| search ablation | **no selective mechanism is at fault**; null move −2, aspiration +19, qs SEE +1, TT PV +8; depth 7 **+647**, depth 8 **+899** | `2026-09-04-search-ablation.md` |
| V2.3 tempo | **INCONCLUSIVE** — the pre-registered mean statistic was outlier-dominated; robust statistics show nothing. **Validation has been read.** | `2026-09-04-v2.3-tempo.md` |
| V2.4 time policy | **pre-registered, not yet measured** | `2026-09-04-v2.4-time-policy.md` |

## 5. The live question: is V2.1 actually a champion?

* V2.1 vs rated-v1 on the **mid-game** pool (`corpus/postmortem/pairs.json`):
  **+41 =129 −30, 52.75%, +19 Elo**, cluster bootstrap −7..+45, **41 of 100
  clusters informative**, leave-one-out +15.8..+22.8, six best clusters must go
  before it reaches zero.
* V2.1 vs rated-v1 on the **competition-profile opening** pool (60 positions,
  Black to move, move 6–9, |SF| ≤ 40): **running**, at 86 of 120 games it is
  **45.9%**.

If the second holds, V2.1 is +19 Elo on one population and roughly −20 on the
other, which is **not** a champion. Under the V3 escalation rule that means
**V3 work must not begin** and V2 keeps being tested.

## 6. Running jobs — check before restarting anything

| job | command | output | last seen |
|---|---|---|---|
| competition-pool match | `tools.postmortem.play --cand champions/v2_1_kingpawn --base champions/rated_v1 --pairs corpus/daily/pool/competition_like_pairs.json --depth 6 --workers 6` | `corpus/daily/pool/games/v21_vs_ratedv1.jsonl`, log `corpus/daily/pool/play_v21.log` | 86/120, candidate 45.9% |
| tempo32 Gate 2 | `tools.postmortem.play --cand champions/v2_1_kingpawn_tempo32 --base champions/v2_1_kingpawn --pairs corpus/postmortem/pairs.json --depth 6 --workers 4` | `corpus/daily/tempo/games/gate2_tempo32.jsonl`, log `corpus/daily/tempo_gate2.log` | 45/200, candidate 51.1% |
| depth repair of the round-3 blind wins | `tools.daily.deeper --positions corpus/daily/round3_blindwins.json --depths 6 8` | `corpus/daily/round3_blindwins_deeper.txt`, log `corpus/daily/deeper3.log` | rated-v1 depth 6 done |

`pkill -f` **does not work in this shell**; two copies of the pool match once
ran against the same file and corrupted it (retained as
`corpus/daily/pool/games/v21_vs_ratedv1.CORRUPT-DISCARDED.jsonl`). Kill process
trees with `cmd //c "taskkill /PID <pid> /T /F"` after listing them with
`wmic process where "name like '%python%'" get ProcessId,ParentProcessId,CommandLine`.

## 7. Important negative and self-audit results — do not re-derive

* **The engine is not optimistic.** 35,202 unselected positions: blind wins
  13.8% against blind losses 11.8%, false wins 5.6% against false losses 5.6%.
  The apparent optimism in the rated games was selection bias.
* **A paired match with mirror-identical pairs carries no information.** Always
  report informative clusters (`tools.daily.clusters`).
* **Mean oracle-scored move loss is outlier-dominated** by mate-valued
  positions. Use the clamped mean, the median and the ≥100/≥300 counts.
* **Advanced-passer residuals are a search effect, not an evaluation gap**: the
  root departs, the static does not. Do not reshape the passed-pawn curve.
* **Neither `king_safety` nor `king_pawn` helps the round-3 blind wins**:
  king safety moves the static by +10..+15 cp, king-pawn by 0..3, against gaps
  of 231 to 816.
* Depth repairs **1 of 16** rated-game error positions and damages 1; neither
  V2.1 nor V2.2a changes any of them.

## 8. Next actions, in priority order

1. **Finish the competition-pool match** and decide the champion question. If
   V2.1 is not convincingly better than rated-v1 across both pools, say so and
   do not promote; the strongest supported build is then `rated-v1`.
2. **Finish the tempo32 Gate 2** and close V2.3 with a game-based verdict.
3. **Read `corpus/daily/round3_blindwins_deeper.txt`** — does depth repair the
   seven external blind wins? This is the link between the rated evidence and
   the depth lever.
4. **V2.4 time policy, stage 1, on a quiet machine**: `tools.clocksim` at a
   120,000 ms clock and `tools.clockladder` for `champions/v2_1_kingpawn` and
   the three `_sf` variants. Selection rule is fixed in the record; a ladder
   failure eliminates a variant regardless of depth gain.
5. **V2.4 stage 2** only if stage 1 shows at least +0.4 ply: arena at
   **120,000 ms + 500 ms**, selected variant against the baseline. Do not start
   it without roughly three clear hours.
6. Final validation: `ruff check .`, `pytest -q`, `tools.release_check`,
   fingerprint, package build and extracted-zip smoke, SHA-256.
7. Update `V2_10H_CODEX_HANDOFF.md` and `V2_10H_SUMMARY.json`, and write the
   final report.

## 9. Version status as it stands

* **rated-v1** — `98c48c89`, immutable, currently the strongest *supported*
  build.
* **V2** — `champions/v2_1_kingpawn`, promoted in an earlier session on the
  mid-game pool; that promotion is under active challenge by the
  competition-profile pool and may be withdrawn.
* **V3** — **not attempted.** The escalation rule requires a V2 champion whose
  Gate 2 is genuinely positive; that condition is not currently met.
