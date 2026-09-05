# Active research state — read this first after any compaction or machine change

Written **2026-09-05 07:20 local (Windows)** as the machine handoff; updated
**2026-09-05 08:35 local (Mac)** after the C1 Gate 0 and the launch of its timed
screen. Mac environment: Apple M4 (10 cores), uv 0.12.10, Python 3.12.14 in
`.venv`, Stockfish from Homebrew; fingerprint 1,712,405 reproduced. This file, the repository and
`benchmarks/current/MAC_HANDOFF.md` are the source of truth.

## 1. Builds and hashes

| identity | exact value |
|---|---|
| **CURRENT SUBMITTED BUILD** | **RC-B** — uploaded by the user **2026-09-05 12:01 UK local**: `corpus/release/claudeshark_rc_b.zip`, sha256 `f7b94b6507c39f32c6ba40f453e302812ba0bfbce1c8be16d2129ecb458c9c1a`, commit `3d918a5db6233e9f0c7a4dcbee6713b83f758c11`. RC-A (`3a89bf3e…ff9b`, commit `98c48c8`) is the historical fallback/control. |
| submitted archive | `corpus/release/claudeshark_rated_v1_rc_a.zip` (39,125 bytes; 106,863 unzipped; 11 files) |
| submitted SHA-256 | `3a89bf3e2fbfab0b7e07baf2fff7e0edf2288fc2a4d372e8eda823db1767ff9b` |
| underlying commit | `98c48c89b3a8142e6567e5f46b2d2036df7297d1` (tag `rated-v1`, also `main`) |
| **CURRENT BEST PROVEN BUILD** | **RC-B** = `champions/rc_b` = `corpus/release/claudeshark_rc_b.zip` (48,167 bytes; 131,795 unzipped; 14 files), sha256 `f7b94b6507c39f32c6ba40f453e302812ba0bfbce1c8be16d2129ecb458c9c1a`, shipped files identical from commit `3d918a5db6233e9f0c7a4dcbee6713b83f758c11` through HEAD on `mac-full-development`; 1,213 tests + 1 skip; release gate 15/15 READY TO UPLOAD; clock ladder PASS; Python 3.12.14 fresh-extraction smoke PASS. Strength: +83 =98 −45 (58.4%, +59 Elo, family bootstrap +25..+95) over RC-A, 226 games, **80 of 113 families informative (71%)**, leave-one-informative-family-out +56..+63, family means 0×6 ¼×18 ½×33 ¾×44 1×12. **Sleep sensitivity PASS**: dropping the 8 games (5 families) in flight across the 10:20–11:31 sleep gives +79 =93 −44, 58.1%, +57 Elo, bootstrap +21..+92 (`corpus/daily/time/c1staged_family_sensitivity.txt`). **CHAMPION and SUBMITTED** (uploaded 12:01); every candidate is measured against `champions/rc_b`. |
| **CURRENT DEVELOPMENT CANDIDATE** | RC-C candidate 1 (unbounded check extension) **REJECTED at Gate 2a** 13:37: +25 =43 −32 (46.5%, −24 Elo) vs RC-B over 100 games / 50 families, leave-one-out −32..−18, clock floor 3.4 s v 8.0 s. Candidate 2 = frontier-bounded check extension (`CS_CHECK_EXT_MAXDEPTH`), same targets, stricter cost bound; in Gate 0/1. RC-B remains champion. |
| previous submitted build | V2.1 KING-PAWN, `corpus/v2/kp/submission_v2_1_kingpawn.zip`, sha256 `a8b95a5cab3e33aaac6e5d3e686eb7f292d3a600a115e18e077b9622f35bbd0a`, commit `10c9277`; **rejected for the locked build** |

Release-candidate stack: RC-A submitted; RC-B frozen from the C1 result and
awaiting the user's upload decision. Never overwrite an RC archive; freeze a
new one under a new name.

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
  **Round 20 (loss, Black, vs The Huxley Knights) = RC-B, HIGH confidence by
  timing, not proven by moves:** uploaded 12:01 UK; the game finished 11:10:35
  UTC = 12:10:35 UK after 194 s, so it started about 12:07; the platform log
  carries no build identity (init 2.2 s, both builds start in ~1.6 s here); a
  cold replay of all 43 Black moves has the two builds differing at only 3
  positions (1 matches RC-B, 2 RC-A), so move agreement is neutral. Files
  `corpus/daily/rcb/round20-huxley-knights.{pgn,log,jsonl,_annotated.jsonl}`.
  Mechanism: five consecutive 100–143 cp errors on moves 8–12 (Bh5, Be7, b5,
  d5, Nxd5), the last two walking into 13.Qxd5! … 16.Nc7+; root +9 at 12…
  against a true −481 because the fork is a check one ply past the
  capture-only quiescence. This selected the check-extension lane.
  **RC-A live record today: R16 W, R17 D, R18 L, R19 W** (files
  `corpus/daily/rca/round1{6,7,8,9}-*.{pgn,jsonl,_annotated.jsonl}`, record
  `2026-09-05-rca-live-games-r16-r19.md`). Not an Elo test; mechanisms only:
  R17 = conversion failure by perpetual-check horizon at 47.Re1 (root +354,
  truth 0, not repaired by depth 9; RC-B identical); R18 = tactical horizon at
  15…g6 (piece trap one ply past depth 6; **RC-B plays 15…f6 at the game
  budget and repairs it**); R19 = mate found, RC-B identical.

## 3. Experiments — status, result, artifact

| experiment | status | result | artifact |
|---|---|---|---|
| V2.1 king-pawn vs rated-v1, 226 fixed-depth games, organiser starts | **complete, decisive** | 45.8%, −29.3 Elo, 54 informative families, bootstrap −55.8..−4.6 | `corpus/daily/pool/games/v21_vs_ratedv1_actual.jsonl`, `corpus/daily/pool/v21_actual_verdict.txt` |
| V2.4 sf60 (`START_FRACTION` 0.60) vs rated-v1, 226 timed games | complete | 50.2%, +1.5 Elo, 70 informative, bootstrap −31..+32, lowest clock 2.2 s v 6.7 s; **rejected** | `corpus/daily/time/games/sf60_vs_ratedv1_120s.jsonl`, `swissrisk_sf60.txt` (its PGN was never written: arena bug, fixed in `03af6ab`) |
| V2.4b early16 (fewer moves-to-go above 60 s) vs rated-v1, 226 timed games | complete | 49.3%, −4.6 Elo, 65 informative, bootstrap −40..+31, lowest clock 4.1 s v 6.1 s; **rejected** | `corpus/daily/time/games/early16_vs_ratedv1_120s.jsonl` + `.pgn`, `swissrisk_early16.txt` |
| Timed confirmation V2.1 vs rated-v1 | **PARTIAL — NON-DECISIVE — STOPPED FOR TIME BUDGET** at 69/226 (48.6%) | must not revise the fixed-depth verdict | `corpus/daily/time/games/v21_vs_ratedv1_120s.PARTIAL-NON-DECISIVE-STOPPED-FOR-TIME-BUDGET.jsonl` + `.txt` |
| C1-search-staged Gate 0 | **complete, passed** | −0.24% nodes, 0/42 root moves changed, +17% knps, 16/16 tactics | `2026-09-05-c1-staged-move-picker.md`, `corpus/daily/time/gate0_c1staged.txt` |
| C1-search-staged timed screen vs rated-v1, 226 games, competition clock (family + sleep sensitivity in `c1staged_family_sensitivity.txt`) | **complete, decisive, PROMOTED** | +83 =98 −45, 58.4%, **+59 Elo**, 80 informative, bootstrap +25..+93, clock floor 5.7 s v 4.7 s, 0 failures | `corpus/daily/time/games/c1staged_vs_ratedv1_120s.jsonl` + `.pgn`, `swissrisk_c1staged.txt` |
| fast stalemate probe (identical tree) | complete | +11% knps on top of C1, fingerprints unchanged | `2026-09-05-c1-staged-move-picker.md`, `tests/test_has_legal_move.py` |
| Lane B static king-attack signals | **complete, negative, closed** | best AUC 0.61, sign agreement <40%, signals zero through the early phase of the R1/R11 attacks | `2026-09-05-lane-b-static-attack-signals.md`, `corpus/daily/laneb_signals.txt` |
| LMR schedule variants (r=2 from depth 4 etc.) | complete, flat, closed | −38% nodes at depth 8 but 5 better / 5 worse at equal time, E-loss slightly worse | `2026-09-05-lmr-schedule-screen.md`, `corpus/daily/lmr/` |
| RC-C candidate 1: check extension vs RC-B, 100 timed games | **complete, REJECTED** | 46.5%, −24 Elo, 32 informative, bootstrap −74..+24, LOO −32..−18, clock floor 3.4 s v 8.0 s; equal-time blunder screen had been +22 cp | `2026-09-05-rcc-check-extension-prereg.md`, `corpus/daily/rcc/checkext_vs_rcb_120s_100.jsonl` + `.pgn`, `swissrisk_checkext_100.txt` |
| depth repair on 27 key rated decisions | complete | depth 7 or 8 repairs 6 of 27 | `corpus/daily/rated15_key_deeper.txt` |
| public start-FEN recurrence | complete | 84–87% by rounds 14–15; a book is legal only from our own engine's moves | `2026-09-05-start-book-recurrence.md` |
| tablebases | measured | ≤5-piece positions in 1 of 15 rated games; not worth shipping | `FABLE_OVERNIGHT_HANDOFF.md` |
| RC-A release verification | complete | 15/15 gate twice, 1,202 tests, Python 3.12.13 fresh-extraction smoke, ladder PASS, 0 failures in 521 timed games | `corpus/release/RC_A_MANIFEST.txt`, `rc_a_smoke_py312.json`, `RC_A_UPLOAD_CARD.md` |

No experiment is running.

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

## 6. Development priorities (updated 11:45 Mac, after the day's results)

Done today: C1 (promoted, +59), the fast stalemate probe (+11% knps,
identical tree), Lane B static signals (closed), LMR schedule (closed). The
evidence order of the user's plan for what remains:

1. **RC-B release**: release check, card, user decision on upload. RC-A
   stays the fallback.
2. **Speed (lane 6), next targets from the C1 profile**: capture generation
   for quiescence and the staged head (~14% and ~12% of search time), `is_check`
   at quiescence entry (~7%), the evaluator's piece scan (~23%; already tight).
   Every candidate here must keep the fingerprint (1,708,269) and is gated by
   knps + tests only.
3. **qsearch / TT lanes (4, 5)**: no evidence yet either way; the 2026-09-04
   ablation found SEE pruning and the PV cutoff policy neutral. Only with a
   concrete mechanism.
4. **Conversion (lane 9)**: Rated 16 (RC-A) repeated the pattern (+529 → +22
   after 34.Qxe4); R3, R7 yesterday. Still the largest evaluation-side loss
   source that a term could address; prior mop-up/passed/V2.2a were not
   strength-proven. Needs a pre-registered positive/negative set like Lane B.
5. Check extension (A4): the only remaining search lever with a mechanism;
   would re-open the LMR question. Fixed-depth node growth + tactics first.

## 7. Next three actions

1. Read `RC_B_UPLOAD_CARD.md`; if the user confirms, upload
   `corpus/release/claudeshark_rc_b.zip` and record the SHA-256 and time in
   section 1. Until then, every rated game is RC-A.
2. Ingest any new RC-A rated games from the public team page into
   `corpus/daily/rca/` (tool flow: `tools.aichessathon_public.fetch` +
   `parse_team_games`, then `tools.daily.ingest`, then
   `tools.postmortem.annotate --workers 1`).
3. Continue lane 6 with fingerprint-gated speedups, one at a time.

## 8. Live background jobs

**NONE.** Sweep 13:40: the candidate-1 arena (PID 30573) and its caffeinate guard exited; no python, Stockfish or waiters.

Rules: one CPU-heavy job at a time, registered here, removed when it ends;
no waiter shells; keep the lid open and the charger in during timed screens.

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
