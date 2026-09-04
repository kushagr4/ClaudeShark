# Active research state — read this first after any compaction

This file, the repository and `benchmarks/current/V2_10H_SUMMARY.json` are the
source of truth. Conversational memory is not. After a compaction: read this
file, run `git status` and `git log --oneline origin/main..HEAD`, verify the
running jobs in section 6 **including that each output path has exactly one
root writer**, then continue from section 9. **Do not restart anything in
section 6 that is still running or already complete.**

## 1. Clock

* Session start **2026-09-04 09:37:20 +0100**, target finish about **19:37**.
* Last update to this file: **12:25**. Roughly seven hours remain.

## 2. Repository

* Branch **`v2.2-development`** (not `v2-development`, which is stale at
  `10c9277`). HEAD `cab6b23` at the time of writing.
* `rated-v1` → `98c48c89b3a8142e6567e5f46b2d2036df7297d1`; `main` and
  `origin/main` identical and untouched. Nothing pushed;
  `origin/v2.2-development` is still at `a116be2`.
* Identity `kushagr4 <ratrakushagra@gmail.com>` on every commit.
* Fingerprint with all experimental terms off: **1,712,405 nodes** at
  `tools.bench --depth 6`. 1,186 tests passed at the last full run, plus 11 new
  in `tests/test_matchlock.py`; `ruff check .` clean.

## 3. Version status

| build | status |
|---|---|
| **`rated-v1`** | **strongest supported build; the safe champion** |
| `champions/v2_1_kingpawn` | **POPULATION-SENSITIVE, NOT PROMOTED** (`27a096d`) |
| `champions/v2_2a_low_material` | targeted evaluator correction, **not strength-proven**, not promoted |
| `TEMPO = 32` | **NEGATIVE, permanently rejected** (`304ecb6`), −23 Elo on 54 informative clusters |
| colour-specific heuristics | **hypothesis CLOSED**; never implement one |
| **V3** | **LOCKED** — no validated V2 champion exists |

## 4. Experiment verdicts so far

| id | verdict | record |
|---|---|---|
| V2.2a low-material | KEEP FOR MORE TESTING, not promoted; Gate 2 had **1 informative cluster of 100** | `2026-09-04-v2.2a-low-material.md` |
| colour asymmetry | no engine defect; evaluator exact 600/600, search noise non-directional | `2026-09-04-colour-asymmetry-audit.md` |
| cluster-evidence methodology | mop-up's +3 Elo rests on **2 of 100**; V2.1's +19 on **41 of 100** | `corpus/daily/cluster_evidence.txt` |
| search ablation | **no selective mechanism at fault**; null move −2, aspiration +19, qs SEE +1, TT PV +8; depth 7 **+647**, depth 8 **+899** | `2026-09-04-search-ablation.md` |
| V2.3 tempo | diagnostic INCONCLUSIVE (one mate outlier), Gate 2 **NEGATIVE**, rejected | `2026-09-04-v2.3-tempo.md` |
| V2.1 champion review | POPULATION-SENSITIVE, not promoted | `2026-09-04-v2.1-champion-review.md` |
| public-data colour question | **CLOSED**; White scores 51.4% over 143 games | `corpus/daily/public_verification.txt`, `field_colour.txt` |
| single-writer guard | in place, tested, and one erratum recorded | `2026-09-04-single-writer-guard.md` |

**Deferred, not failed:** `tools.v2.lowmat_gate2` over the 166-game targeted
match — a 2–3 hour in-family re-score. **OPTIONAL LATER CONFIRMATION on a quiet
machine only**, and only if it answers a specific unresolved promotion
question. Do not run it in this session.

## 5. The live question

V2.1 against rated-v1, by population — **never pooled into one universal Elo**:

| population | games | score | nominal Elo | informative clusters | bootstrap |
|---|---|---|---|---|---|
| mid-game (`corpus/postmortem/pairs.json`) | 200 | 52.8% | **+19.1** | 41 of 100 | −7..+45 |
| synthetic competition profile | 120 | 48.3% | **−11.6** | 29 of 60 | −50..+26 |
| **actual organiser starts (113 FENs)** | **226** | **pending** | | | |

## 6. Running jobs — verify before touching anything

| job | owner | output | last seen |
|---|---|---|---|
| **V2.1 vs rated-v1 on 113 actual organiser FENs, 226 games, depth 6, 8 workers** | pid recorded in `corpus/daily/pool/games/v21_vs_ratedv1_actual.jsonl.owner` (was 22392) | `corpus/daily/pool/games/v21_vs_ratedv1_actual.jsonl`, log `corpus/daily/pool/play_v21_actual.log` | 43/226 at 12:15, about 2.3 games/min, finishing near **13:35** |

**Paused deliberately** so as not to compete with it: the Round-4 colour
move-agreement job (`tools.daily.whoami` over all four rated games), stopped at
88 of 258 plies. The tool writes only at the end, so nothing partial exists.
Resume it after the match.

**Queued until the machine is quiet:** `tools.daily.samefen` scoring phase, any
Stockfish annotation, and every NPS or timed measurement.

### Process rules that are not optional

* `pkill -f` silently matches nothing in this shell. Kill trees with
  `cmd //c "taskkill /PID <pid> /T /F"` after listing with
  `wmic process where "name like '%python%'" get ProcessId,ParentProcessId,CommandLine`.
* **Never smoke-test infrastructure against a live experiment path.** Doing
  exactly that destroyed the first attempt at this match. Use a temporary
  directory and synthetic files.
* Two corrupt artifacts are retained as evidence of tooling failure and must
  never enter statistics:
  `corpus/daily/pool/games/v21_vs_ratedv1.CORRUPT-DISCARDED.jsonl` and
  `corpus/daily/pool/games/v21_vs_ratedv1_actual.CORRUPT-DISCARDED-2.jsonl`.

## 7. Frozen splits — do not reshuffle, do not inspect the holdout

`corpus/daily/splits/`, seed **20260904**, by exact FEN family, zero overlaps
asserted, our three rated starts excluded. Diagnostic 51 families / 71 games,
validation 29 / 35, holdout 33 / 35, each with a FEN-list SHA-256 in
`FROZEN.md`. Hypothesis formation happens in the diagnostic split only;
validation is read once after a feature freezes; the holdout is not inspected
during design.

The running 226-game match covers all 113 families including holdout ones.
That is acceptable for V2.1, which was frozen long before these positions
existed here, and it makes that population **exploratory distribution
evidence**. The headline verdict aggregates all 113; next-feature design is
restricted to the diagnostic split.

## 8. Negative and methodological results — do not re-derive

* The engine is **not optimistic**: over 35,202 unselected positions, blind wins
  13.8% against blind losses 11.8%, false wins 5.6% against false losses 5.6%.
  The rated-game impression of optimism was selection bias.
* A paired match of near-identical deterministic engines carries information
  only in clusters whose pair is **not** mirror-identical. Always report
  informative clusters.
* Mean oracle-scored move loss is **outlier-dominated** by mate-valued
  positions; use the clamped mean, the median and the ≥100/≥300 counts.
* Advanced-passer residuals are a **search** effect, not an evaluation gap.
* Neither `king_safety` nor `king_pawn` helps the round-3 blind wins: +10..+15
  cp and 0..3 cp against gaps of 231 to 816.
* **Depth 8 repairs 1 of 7** round-3 blind wins and 1 of 16 rated-game errors.
* Round 3 contains two distinct mechanisms, kept separate: **dynamic attack
  compensation** (moves 18–20, static −378 against oracle +438) and
  **rook-versus-minor with pawns** (moves 39–40, root +45/+56 against +304/+422).
* Several round-3 positions are **correct move, wrong score** — the engine plays
  well while mis-valuing the position by hundreds of centipawns, which is how a
  won game became a repetition draw.

## 9. Next actions, in priority order

1. **Let the 226-game match finish (~13:35).** Then report games, W/D/L, score,
   nominal Elo, 113 families, informative families and fraction, family
   bootstrap, leave-one-informative-family-out, colour split, and the
   distribution of family scores across 0.00/0.25/0.50/0.75/1.00. Compare the
   three populations separately; do not pool.
2. Resume `tools.daily.whoami` and confirm the round-4 colour with a second
   method. Clock fingerprint currently points at **Black** (sd 1.19, max 6.02,
   two instant moves, against 0.78 and 4.67 for White) but that is a hypothesis.
3. Analyse round 4 as external holdout — never for tuning.
4. `tools.daily.samefen` scoring phase on the ranked diagnostic families
   (`corpus/daily/samefen_families.txt`; the top family has four games, four
   different first moves and a 2–2 colour split).
5. Cluster recurring external failure mechanisms and compare with round 3.
6. Choose **one** next V2 hypothesis on breadth of independent support.
7. Gate 0, Gate 1, and Gate 2 only if warranted and time permits.
8. Final validation, package check, Codex handoff.
