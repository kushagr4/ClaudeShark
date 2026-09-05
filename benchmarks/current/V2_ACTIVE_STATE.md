# Active research state — read this first after any compaction

This file, the repository and `benchmarks/current/FABLE_OVERNIGHT_HANDOFF.md`
(when written) are the source of truth. After a compaction: read this file,
run `git status`, `git log --oneline -n 20`, list python processes with
`wmic process where "name like '%python%'" get ProcessId,ParentProcessId,CommandLine`,
check `.owner` sidecars, then continue from section 10.

## 1. Clock

* Fable take-over session began **2026-09-05 01:05 local**. Last update to this
  file: **01:52**. (Earlier drafts of this file overstated the clock; times here are from file timestamps.) The user is asleep; a morning handoff is due.

## 2. Repository

* Branch **`v2.2-development`**, HEAD `3421401` at take-over, **`ff36869`** after the 01:33 checkpoint (rounds 6–15, rules, 226 verdict, tools); `rated-v1` =
  `98c48c8` = `main` = `origin/main`, untouched. Nothing pushed. Identity
  `kushagr4 <ratrakushagra@gmail.com>` verified.
* Untracked work at take-over (from the previous session): `analysis/`,
  `tools/aichessathon_public.py`, `tests/test_aichessathon_public.py`, the
  `champions/*_sf*` and `*_tempo*` variants, `corpus/daily/pool/games/v21_vs_ratedv1_actual.jsonl`.

## 3. Version status — four distinct things, never conflated

| name | what it is | status |
|---|---|---|
| **SUBMITTED V2.1 KING-PAWN** | `corpus/v2/kp/submission_v2_1_kingpawn.zip`, 43,489 B, sha256 `a8b95a5c…35bbd0a`, commit `10c9277`, tree `adaf2b6c` = `champions/v2_1_kingpawn` | playing the ladder; **measured −29 Elo vs rated-v1 on the organiser's own starts** (section 5) |
| **RATED-V1 HISTORICAL BASELINE** | `98c48c8`, tag `rated-v1`, `champions/rated_v1` | immutable; **strongest build supported by evidence** |
| **LOCAL DEVELOPMENT HEAD** | `v2.2-development` | every term ships off; reproduces the rated-v1 fingerprint (1,712,405 nodes at depth 6) |
| **CURRENT EXPERIMENTAL CANDIDATE** | none promoted; time-policy variants `champions/rated_v1_sf{60,75,90}` exist untested under V2.4 | see section 9 |

## 4. Official rules snapshot (2026-09-05 01:11)

`benchmarks/current/2026-09-05-official-rules-snapshot.md`, raw HTML in
`analysis/rules/`. Decisive points:

* **Pondering is impossible**: "Your process is suspended while your opponent
  moves, so work you leave running between your own moves does not run."
  Extra threads on our own move are slower. The pondering lane is closed by the
  rules; the engine has no threads (audited: `agent.py` single-threaded).
* **A Stockfish-annotated book is prohibited**: "a database of engine moves or
  evaluations shipped for lookup at runtime is an engine, not training data."
  Books are allowed only from our own code's output or non-engine data.
* Init budget 90 s; 10 uploads/day; close 11 Sept 11:00; 13-round Swiss over
  locked builds by points; tie-breaks points, Buchholz, head-to-head, **earlier
  final submission**; 300-ply material adjudication; validation = two smoke
  games; eligibility tied to a UK university student on the team → **user must
  get written organiser clarification**.

## 5. The 226-game actual-organiser match — COMPLETE, do not rerun

`corpus/daily/pool/games/v21_vs_ratedv1_actual.jsonl` (single owner, finished
2026-09-04 13:22). Verdict in `corpus/daily/pool/v21_actual_verdict.txt`:

| population | games | score | Elo | informative families | bootstrap |
|---|---|---|---|---|---|
| mid-game starts | 200 | 52.8% | +19.1 | 41/100 | −7..+45 |
| synthetic competition profile | 120 | 48.3% | −11.6 | 29/60 | −50..+26 |
| **actual organiser starts** | **226** | **45.8%** | **−29.3** | **54/113** | **−55.8..−4.6** |

+41 =125 −60; LOO −32.7..−26.4; as White 44.3%, as Black 47.4%; family
histogram 0.00×6 0.25×28 0.50×59 0.75×19 1.00×1. **The submitted build is
measurably weaker than rated-v1 on the distribution the competition uses.**
V2.1 king-pawn: **REJECTED for the locked build.**

## 6. Rated corpus through Round 15 — all colours CONFIRMED

Source: our public team page `https://aichessathon.com/team/6532bc56-58ba-48b5-977d-0c039fe3fd7b`
(`analysis/refresh_2026-09-05/claudeshark_team_games.json`), cross-checked
against seven direct logs (`corpus/daily/logs/`) and PGN results; all 15
consistent (`corpus/daily/rated_games.txt`). Record **7 W 3 D 5 L = 8.5/15**;
White 2W 2D 3L, Black 5W 1D 2L.

| R | colour | result | opponent | first serious error | note |
|---|---|---|---|---|---|
| 1 | W | L | The Castle Gambit | 22 Nxd4 | dynamic attack after opponent sac |
| 2 | B | W | Trio Duo | 18 O-O | |
| 3 | B | D | Baryon | 14 Bd7 | **blind win +443 → repetition** (R v B+pawns) |
| 4 | B | W | Prophylaxis | 15 Re8 | |
| 5 | W | L | Stonkfish | 17 bxc3 | +184 → gradual → 23 hxg4 tactical −338 |
| 6 | W | W | e=π=2 | 19 Qd3 | |
| 7 | W | D | Desai | 33 Bb4 | **+521 → perpetual check at 48 Ke2** (conversion) |
| 8 | B | W | 404 Not Found | none | |
| 9 | W | W | PawnStorm | none | |
| 10 | B | L | Elbow Grease | 13 Bb7 | collapse under kingside attack, moves 13–18 |
| 11 | W | L | mangodogo | 13 a4 | gradual positional then tactical (31 Nxe4) |
| 12 | B | W | Rudra | 43 e3 | |
| 13 | W | D | Tobias Carlsen | 10 Nxe5 | short repetition at −42, acceptable |
| 14 | B | W | does 4th place get a trophy | 16 Rde8 | |
| 15 | B | L | Zagreus 5.0 | **5 d5** | opening errors from a Nb5 start; −354 by move 10 |

Files: `corpus/daily/games/rated15.jsonl` (ingest), `rated15_annotated.jsonl`
(Stockfish), `corpus/daily/colours.json` (15 entries with sources),
`corpus/daily/rated_games.json/.txt` (canonical dataset, `tools.daily.dataset`).

## 7. Start-FEN recurrence (public 447 games, 239 distinct starts)

By rounds 14–15, **84–87%** of a round's distinct starts had appeared in an
earlier round; 4 of our rounds 6–15 (R7, R10, R12, R13) began from previously
observed positions. The curated pool is finite (~240+ seen). A book is
therefore *coverable*, but only from our own engine's offline search (rule
above), and the Swiss may use a different draw. Not yet valued.

## 8. Tablebases

Rated corpus: 3/15 games reach ≤7 pieces (71 plies), 1/15 reaches ≤5 (13
plies). Public: 82/447 reach ≤5 pieces. Syzygy 3-4-5 is ~1 GB, far over 50 MB;
only 3–4-piece tables fit, whose positions the engine already wins. **Not
worth shipping.**

## 9. Running jobs — verify before touching anything

| job | output | status |
|---|---|---|
| **V2.4 Stage 2: timed arena 120 s + 0.5 s, `champions/rated_v1_sf60` vs `champions/rated_v1`, 226 games on the 113 organiser starts, 8 workers** | `corpus/daily/time/games/sf60_vs_ratedv1_120s.jsonl` (+ `.pgn`), log `corpus/daily/time/stage2_sf60.log` | started **01:45**, python pids 23168/23136 (uv shim + arena); expected 3–3.5 h |

Complete: report shards (merged into `corpus/daily/rated15_report.*`),
`tools.daily.deeper` (`corpus/daily/rated15_key_deeper.txt`), V2.4 Stage 1
(`corpus/daily/time/stage1_*.txt`, sf60 selected by the pre-registered rule).

Do not start another CPU-heavy job while the arena runs; it is a timed match
and contention changes what is being measured. **Never smoke-test
infrastructure on a live path.** Corrupt artifacts that must never enter
statistics: `corpus/daily/pool/games/v21_vs_ratedv1.CORRUPT-DISCARDED.jsonl`,
`…_actual.CORRUPT-DISCARDED-2.jsonl`.

## 10. Plan

1. When the report finishes: rerun `tools.daily.dataset`, classify each game's
   mechanism (`corpus/daily/rated_classes.json`), write the postmortem record.
2. V2.4 time policy, on the **rated-v1 base** (not V2.1): Stage 1
   `tools.clocksim` + `tools.clockladder` for `champions/rated_v1_sf60/75/90`;
   Stage 2 timed arena 120 s + 0.5 s on actual organiser starts, sf-variant vs
   `champions/rated_v1`, with informative-cluster reporting and a Swiss risk
   table (flags, crashes, ≥300 cp errors).
3. If time remains: timed confirmation of V2.1 vs rated-v1 on organiser starts.
4. Freeze a release candidate (rated-v1 features, plus the time constant only
   if Stage 2 is positive and safe), run `tools.release_check`, write
   `FABLE_OVERNIGHT_HANDOFF.md`.
