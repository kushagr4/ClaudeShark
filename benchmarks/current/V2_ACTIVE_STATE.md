# Active research state — read this first after any compaction or machine change

Written **2026-09-05 07:20 local (Windows)** as the machine handoff; updated
**2026-09-05 08:35 local (Mac)** after the C1 Gate 0 and the launch of its timed
screen. Mac environment: Apple M4 (10 cores), uv 0.12.10, Python 3.12.14 in
`.venv`, Stockfish from Homebrew; fingerprint 1,712,405 reproduced. This file, the repository and
`benchmarks/current/MAC_HANDOFF.md` are the source of truth.

## 1. Builds and hashes

| identity | exact value |
|---|---|
| **CURRENT SUBMITTED BUILD** | **RC-A / exact rated-v1** |
| submitted archive | `corpus/release/claudeshark_rated_v1_rc_a.zip` (39,125 bytes; 106,863 unzipped; 11 files) |
| submitted SHA-256 | `3a89bf3e2fbfab0b7e07baf2fff7e0edf2288fc2a4d372e8eda823db1767ff9b` |
| underlying commit | `98c48c89b3a8142e6567e5f46b2d2036df7297d1` (tag `rated-v1`, also `main`) |
| **CURRENT BEST PROVEN BUILD** | **RC-A** (nothing has beaten it on the competition distribution) |
| **CURRENT DEVELOPMENT CANDIDATE** | **C1-search-staged**, wired: `staged_moves` feeds `_negamax` behind `CS_STAGED_MOVES` (default off; on = the candidate). Gate 0 passed 2026-09-05 08:25 (record `2026-09-05-c1-staged-move-picker.md`): tree not byte-identical (history refreshed at the tail, 93 of 133,487 staged nodes, 0 unexplained), 0/24 and 0/18 root moves changed, +17% knps, tactics 16/16, 1,204 tests. Frozen as `champions/c1_staged`. Timed screen running (section 8). |
| previous submitted build | V2.1 KING-PAWN, `corpus/v2/kp/submission_v2_1_kingpawn.zip`, sha256 `a8b95a5cab3e33aaac6e5d3e686eb7f292d3a600a115e18e077b9622f35bbd0a`, commit `10c9277`; **rejected for the locked build** |

Release-candidate stack: RC-A submitted and best proven; no RC-B. Never
overwrite an RC archive; freeze a new one under a new name.

## 2. Rated corpora — keep them separate

* **Yesterday (2026-09-04), rounds 1–15: all 15 games = V2.1 king-pawn**, per
  the user. 7W 3D 5L. Files: `corpus/daily/round*.pgn`, `corpus/daily/logs/`,
  `corpus/daily/games/rated15.jsonl` (+ `_annotated`), `corpus/daily/colours.json`
  (all 15 colours confirmed from the public team page), `corpus/daily/rated_games.json/.txt`
  (canonical dataset), `corpus/daily/rated15_report.txt/.jsonl`, `corpus/daily/rated_classes.json`,
  record `2026-09-05-rated-games-postmortem.md`.
  *Caveat kept on record, not acted on:* the only validation log on the Windows
  machine (`Downloads/aichessathon-v2-a75063c1f3fa.log`, 09-04 00:25Z) matches
  the root `submission.zip` (rated-v1 content, 107,651 bytes expanded), not the
  V2.1 archive (117,324 bytes, 13 files); no V2.1 validation log exists here.
* **Today: every rated game after the RC-A upload = RC-A**, unless a later
  user-confirmed submission exists. None had been played at 07:05 (team page
  listed 15 games; `analysis/refresh_2026-09-05/claudeshark_team_games_0700.json`).
  Ingest new games with `tools.daily.ingest` under BUILD = RC-A.
  **RC-A games so far (public team page fetched 08:53, 16 games listed):**
  Rated 16, ClaudeShark **White, won by checkmate** vs darKnight (Sicilian
  Sveshnikov start, 142 plies, mean spend 1.92 s, max 7.94 s). PGN
  `corpus/daily/rca/round16-darknight.pgn`, ingested
  `corpus/daily/rca/round16-darknight.jsonl`, annotated
  `round16-darknight_annotated.jsonl` (Stockfish 18, 200k/1M nodes): won from
  +529 at move 34, but 34.Qxe4 (−457) let it fall to +22 by move 39 and the
  win was re-earned on opponent errors — the conversion weakness again, not a
  new mechanism. Page snapshots in
  `analysis/refresh_2026-09-05/` (`_0853`). Keep RC-A games in `corpus/daily/rca/`,
  never merged into the V2.1 dataset.

## 3. Experiments — status, result, artifact

| experiment | status | result | artifact |
|---|---|---|---|
| V2.1 king-pawn vs rated-v1, 226 fixed-depth games, organiser starts | **complete, decisive** | 45.8%, −29.3 Elo, 54 informative families, bootstrap −55.8..−4.6 | `corpus/daily/pool/games/v21_vs_ratedv1_actual.jsonl`, `corpus/daily/pool/v21_actual_verdict.txt` |
| V2.4 sf60 (`START_FRACTION` 0.60) vs rated-v1, 226 timed games | complete | 50.2%, +1.5 Elo, 70 informative, bootstrap −31..+32, lowest clock 2.2 s v 6.7 s; **rejected** | `corpus/daily/time/games/sf60_vs_ratedv1_120s.jsonl`, `swissrisk_sf60.txt` (its PGN was never written: arena bug, fixed in `03af6ab`) |
| V2.4b early16 (fewer moves-to-go above 60 s) vs rated-v1, 226 timed games | complete | 49.3%, −4.6 Elo, 65 informative, bootstrap −40..+31, lowest clock 4.1 s v 6.1 s; **rejected** | `corpus/daily/time/games/early16_vs_ratedv1_120s.jsonl` + `.pgn`, `swissrisk_early16.txt` |
| Timed confirmation V2.1 vs rated-v1 | **PARTIAL — NON-DECISIVE — STOPPED FOR TIME BUDGET** at 69/226 (48.6%) | must not revise the fixed-depth verdict | `corpus/daily/time/games/v21_vs_ratedv1_120s.PARTIAL-NON-DECISIVE-STOPPED-FOR-TIME-BUDGET.jsonl` + `.txt` |
| C1-search-staged Gate 0 | **complete, passed** | −0.24% nodes, 0/42 root moves changed, +17% knps, 16/16 tactics | `2026-09-05-c1-staged-move-picker.md`, `corpus/daily/time/gate0_c1staged.txt` |
| C1-search-staged timed screen vs rated-v1, 226 games | **RUNNING** (section 8) | — | `corpus/daily/time/games/c1staged_vs_ratedv1_120s.jsonl` |
| depth repair on 27 key rated decisions | complete | depth 7 or 8 repairs 6 of 27 | `corpus/daily/rated15_key_deeper.txt` |
| public start-FEN recurrence | complete | 84–87% by rounds 14–15; a book is legal only from our own engine's moves | `2026-09-05-start-book-recurrence.md` |
| tablebases | measured | ≤5-piece positions in 1 of 15 rated games; not worth shipping | `FABLE_OVERNIGHT_HANDOFF.md` |
| RC-A release verification | complete | 15/15 gate twice, 1,202 tests, Python 3.12.13 fresh-extraction smoke, ladder PASS, 0 failures in 521 timed games | `corpus/release/RC_A_MANIFEST.txt`, `rc_a_smoke_py312.json`, `RC_A_UPLOAD_CARD.md` |

One experiment is running (the C1 timed screen, section 8).

## 4. Rejected candidates (do not reopen without new evidence)

V2.1 king-pawn (organiser starts, −29); V2.4 sf60 and V2.4b early16 (timed,
flat, lower clock floor); TEMPO 32 (−23 on 54 informative); broad king safety
(global regression); global material scaling (−40); generic contempt or
aggression (unsupported); colour-specific heuristics (closed); sf75/sf90
(soft deadline no longer functions); V2.2a low-material (correct but not
strength-proven, 1 informative cluster); mop-up and passed pawns (targeted
value only). Pondering: impossible under the rules. Oracle book: prohibited.

## 5. Rules snapshot

`2026-09-05-official-rules-snapshot.md` with raw pages in `analysis/rules/`
(01:11 and 07:00 fetches identical). Of record: 90 s init; 10 uploads/day,
close 11 Sept 11:00; process suspended on the opponent's clock (no
pondering); one thread; books and tablebases allowed as shipped data but "a
database of engine moves or evaluations shipped for lookup at runtime is an
engine"; 50 MB unzipped; Python 3.12 with python-chess 1.11.2, numpy, torch,
onnxruntime, numba only; 13-round Swiss over locked builds; tie-breaks
points, Buchholz, head-to-head, earlier final submission. Eligibility (UK
university student on the team) needs written organiser clarification.

## 6. Development priorities (from `ENGINE_OPPORTUNITY_MAP.md`)

1. **C1-search-staged**: wire `staged_moves` into `_negamax` behind
   `CS_STAGED_MOVES` (default on), guarded by "no own pawn on the seventh
   rank" (fall back to `order_moves`); Gate 0 = per-position node counts
   identical with the flag on and off over the 24-position suite, the sharp
   suite and random positions (fingerprint must stay 1,712,405), full tests,
   NPS before/after (`tools.bench --depth 6`); then a short timed screen
   (64–100 games at 120 s + 0.5 s on `corpus/daily/pool/competition_actual_suite.jsonl`)
   with informative families. Expected 10–20% NPS with an identical tree;
   measured today: 79% of interior nodes cut on their first move, 22% have a
   table move, the stalemate probe costs only 2.3 µs (not worth touching).
2. **Lane B, attack blindness**: the largest deployment loss source (R1, R3,
   R5, R10, R11; 104 correct-move/wrong-score decisions; depth repairs 1 in 4).
   Build a positive set from those positions and matched negatives (material
   deficits that are genuinely bad), test the smallest separating signal
   (safe checks, escape squares, attacker/defender counts, pinned defenders)
   at static / qsearch / root; never resurrect broad king safety.
3. Conversion (R3, R7) only with time; time policy closed (five nulls).

## 7. Next three actions for the Mac session

1. `git checkout v2.2-development`, read this file and `MAC_HANDOFF.md`, run
   `uv run python -m pytest -q` (1,205 tests) and `uv run python -m tools.bench --depth 6`
   (expect 1,712,405 nodes) to confirm the environment.
2. Finish C1: wire the picker, Gate 0 identity and NPS, short timed screen;
   freeze RC-B only if the tree is identical and the screen is not negative.
3. Start Lane B with the pre-registered positive/negative set from
   `corpus/daily/rated15_key_positions.json` and the round 10/11 sequences.

## 8. Live background jobs

**ONE (CPU-heavy).** C1 timed screen, registered 2026-09-05 08:31 local (Mac):

* PID 19304 (`.venv/bin/python3 -m tools.arena`), parent 19302 (`uv run`, launched
  with `nohup` from the Claude session shell); 16 `harness/runner.py` children.
* Purpose: Gate 2 timed screen of C1-search-staged against RC-A at the
  competition clock on the 113 organiser starts, both colours.
* Command: `tools.arena --agent champions/c1_staged --opponent champions/rated_v1
  --games 226 --base-ms 120000 --increment-ms 500 --ply-cap 300 --workers 8
  --corpus corpus/daily/pool/competition_actual_suite.jsonl
  --jsonl corpus/daily/time/games/c1staged_vs_ratedv1_120s.jsonl --set-env CS_STAGED_MOVES=1`.
* Started 08:30:03 local; expected finish about 10:30 (the two Windows
  226-game runs at this control took 1 h 57 min and 2 h 04 min on 8 workers).
* Output: `corpus/daily/time/games/c1staged_vs_ratedv1_120s.jsonl` (+ `.pgn`),
  stdout in `corpus/daily/time/games/c1staged_vs_ratedv1_120s.log` (gitignored).
* Kill condition: only if a failure termination attributable to the candidate
  appears, or the user asks. Otherwise let it finish; do not start a second
  CPU-heavy job while it runs.

Rules for future jobs: one CPU-heavy job at a time, registered here (PID,
parent, purpose, command, start, expected finish, output, sidecar, CPU-heavy,
kill condition), removed when it ends; no waiter shells; a probe must never
match its own command line.

## 9. Known DO-NOT-USE artifacts

* `corpus/daily/pool/games/v21_vs_ratedv1.CORRUPT-DISCARDED.jsonl` and
  `…_actual.CORRUPT-DISCARDED-2.jsonl` (duplicate-writer corruption; tooling evidence only).
* `corpus/daily/time/games/v21_vs_ratedv1_120s.PARTIAL-NON-DECISIVE-STOPPED-FOR-TIME-BUDGET.jsonl` (partial).
* `corpus/daily/report_chunks/` (shards already merged into `rated15_report.*`; untracked, regenerable).
* `champions/v2_1_kingpawn_sf*` and `_tempo*` (rejected variants, untracked on Windows).
* Frozen splits in `corpus/daily/splits/` are not to be reshuffled; the holdout
  is not for feature design.

## 10. What was and was not run before this handoff

Run: `ruff check` on the touched files; `tests/test_staged_moves.py`; the
full suite (`pytest -q`, 1,205 passed, 2 min 5 s). Not run: any arena, bench
or annotation (none needed; the engine's shipped behaviour is unchanged since
`98c48c8` for every shipped module except the unused `staged_moves` helper).
