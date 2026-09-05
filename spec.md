# ClaudeShark RC-C Shared Specification

Canonical AI-to-AI coordination protocol for the RC-C cycle. The canonical
copy lives on `rc-c-integration`; only the coordinator changes canonical scope
there. A feature-branch owner edits only its own findings section on its own
branch. The central principle: **parallelise discovery, serialise promotion.**

## 1. Spec Revision

SPEC_REVISION: 2

LAST_UPDATED: 2026-09-05 21:50 UK (Windows PC)

CANONICAL_BRANCH: rc-c-integration

COORDINATOR: Kushagra / Fable

Whenever canonical scope materially changes, increment SPEC_REVISION and
update LAST_UPDATED. Editorial fixes that change no instruction do not bump
the revision.

## 2. Competition Ground Truth

CURRENT_SUBMITTED: RC-B

CURRENT_CHAMPION: RC-B

| field | value |
|---|---|
| archive | `corpus/release/claudeshark_rc_b.zip` |
| SHA-256 | `f7b94b6507c39f32c6ba40f453e302812ba0bfbce1c8be16d2129ecb458c9c1a` |
| bytes | 48,167 compressed, 131,795 uncompressed, 14 files |
| frozen engine commit | `3d918a5db6233e9f0c7a4dcbee6713b83f758c11` |
| frozen snapshot | `champions/rc_b` (blob-identical to the 14 shipped files at `3d918a5`) |
| uploaded | 2026-09-05 12:01 UK time, by the user |
| fallback | RC-A / exact rated-v1, `corpus/release/claudeshark_rated_v1_rc_a.zip`, SHA-256 `3a89bf3e2fbfab0b7e07baf2fff7e0edf2288fc2a4d372e8eda823db1767ff9b`, commit `98c48c8` |
| RC-B strength | +59 Elo over RC-A, 226 timed games, 80 of 113 families informative, bootstrap +25..+95 |

Never change CURRENT_SUBMITTED unless the USER explicitly confirms another
upload. RC-B's archive is immutable. No agent uploads anything.

Rules of record (`benchmarks/current/2026-09-05-official-rules-snapshot.md`):
Python 3.12 with python-chess/numpy/torch/onnxruntime/numba only; one thread;
120 s + 0.5 s; process suspended on the opponent's clock (no pondering); a
database of engine moves or evaluations shipped for runtime lookup is an
engine; 50 MB unzipped; 90 s init; 10 uploads/day, close 11 Sept 11:00.

## 3. Branch Ownership

| branch | owner | purpose |
|---|---|---|
| `rc-c-integration` | Kushagra / Fable | canonical coordination + proven integration; engine files are exact RC-B until a candidate earns promotion |
| `kushagra/rcc-speed-validation` | Kushagra / Fable | Candidate 3 (identity-preserving speed) validation |
| `friend/rcc-tactical-horizon` | Friend / Claude | tactical horizon / forcing-line robustness research, from exact RC-B |
| `mac-full-development` | historical | cross-machine handoff branch; no further development |
| `main`, tag `rated-v1` | frozen | RC-A history; never modified |

RULES:

* NO AGENT MAY DEVELOP ON ANOTHER OWNER'S FEATURE BRANCH.
* NO FRIEND AGENT MAY PUSH DIRECTLY TO `rc-c-integration`.
* NO FEATURE BRANCH MAY MODIFY `main` / `rated-v1` / frozen RC-B
  (`champions/rc_b`, `corpus/release/claudeshark_rc_b.zip`).
* The friend's branch is created FROM `rc-c-integration` (exact RC-B engine),
  never from `kushagra/rcc-speed-validation`.
* Git identity on every commit: `kushagr4 <ratrakushagra@gmail.com>`. No
  co-author, generated-by, assisted-by or model attribution anywhere.
* No force-push. No history rewriting. No pushes to `main`.

## 4. Mandatory Pre-Task Sync

Before EVERY new task, both agents must:

1. process sweep (section 5);
2. `git fetch origin`;
3. read canonical `spec.md` from `origin/rc-c-integration`
   (`git show origin/rc-c-integration:spec.md`);
4. compare SPEC_REVISION with the revision last acknowledged;
5. read new coordinator / agent messages (sections 13, 14, 18);
6. verify the current branch (`git branch --show-current`);
7. verify baseline / champion (section 2; `champions/rc_b` blobs unchanged);
8. verify no other task owned by that agent is still running;
9. define the task's expected decision and maximum useful runtime (section 6).

If SPEC_REVISION changed: READ IT BEFORE DOING ANY WORK. The friend's Claude
must obey a new coordinator scope before beginning its next task.

## 5. Task/Process Hygiene — HARD RULE

NO TASK MAY LINGER WITHOUT A DECISION PURPOSE.

Normally per agent: MAXIMUM 1 CPU-heavy process; TARGET 0 background
processes between experiments.

PROHIBITED: stale waiter shells; permanent polling loops; detached jobs with
unknown ownership; duplicate arena writers; orphaned Stockfish; "leave it
running just in case"; a liveness probe whose pattern matches its own command
line (it never resolves).

Every running task must be recorded in section 17 with: AGENT, TASK, PID,
START, OUTPUT, EXPECTED FINISH, MAX RUNTIME, KILL CONDITION.

At EVERY task boundary: verify the previous process tree has exited (on
Windows: `wmic process where "commandline like '%arena%'" get ProcessId`;
kill trees with `taskkill /PID <pid> /T /F`; on macOS: `pgrep -af arena`,
`kill` the parent then verify the children are gone).

If stopped early: preserve valid rows, record progress, kill the complete
tree, verify exit, clean sidecars after exit, and label the artifact
`PARTIAL-NON-DECISIVE` in its filename. Never silently treat partial output as
completed evidence.

Never write two processes to one artifact. Never let diagnostic Stockfish
compete for CPU with a timed engine measurement. Never test locks or writers
on a live experiment path; infrastructure tests use temporary directories,
synthetic files and synthetic processes only.

This rule applies on every machine.

## 6. Time Management — HARD RULE

TIME IS SCARCE. Optimise DECISIONS PER MINUTE, not experiments started, lines
of code or total games.

Before every task state: QUESTION TO ANSWER, EXPECTED DECISION, ESTIMATED
MINUTES, HARD STOP / REJECTION CONDITION.

Default guidance unless evidence demands otherwise:

| activity | budget |
|---|---|
| state recovery / sync | <= 5 minutes |
| targeted causal diagnostic | ~5–15 minutes |
| small implementation | ~10–25 minutes |
| Gate 0 | as short as correctness permits |
| Gate 1 | targeted positions, not bulk annotation |
| first strength screen | economical 64–100 paired games / families |
| long 160–226 screen | ONLY for a survivor that can plausibly become champion |

Do NOT launch multi-hour work merely because compute is available. If a
10-minute diagnostic can falsify an idea, run it before a large arena. If the
remaining useful working time is less than the expected experiment runtime,
DO NOT START IT.

## 7. Current Kushagra/Fable Scope

Candidate 3: identity-preserving speed (`champions/rcc_speed`, engine files
at commit `f2543bd` on `kushagra/rcc-speed-validation`): incremental
piece-square sum threaded through the search + inline out-of-check capture
generation. Gate 0 passed on the Mac (fingerprints 1,708,269 / 1,852,716
identical to RC-B; 1,227 tests + 1 skip; +18.7% knps). The interrupted Mac
screen (59/100, +18 =25 −16) is NOT evidence.

Goal: reproduce the speed improvement on Windows and establish whether the
candidate is actually stronger than RC-B.

Required sequence:

1. PC speed / profile transfer check (RC-B vs Candidate 3, alternated,
   identical conditions, quiet machine);
2. Gate 0 confirmation on the PC (fingerprint, tests);
3. fresh controlled short screen vs RC-B (new artifact; never append to the
   Mac partial);
4. longer validation only if the candidate remains a plausible champion.

Fable may choose a different lane after Candidate 3 is rejected or promoted.

## 8. Current Friend/Claude Scope

INITIAL SCOPE: TACTICAL HORIZON / FORCING-LINE ROBUSTNESS.

Start from exact RC-B (`rc-c-integration`), NOT Candidate 3.

Primary aim: find a general and competition-useful way of reducing RC-B
tactical horizon failures without reproducing the rejected broad
check-extension regression (candidate 1: −24 Elo / 100 games vs RC-B at the
competition clock, clock floor 3.4 s; candidate 2, frontier-bounded: −0.55
ply on ordinary positions, same result; record
`benchmarks/current/2026-09-05-rcc-check-extension-prereg.md`).

Known failure instances to diagnose first (files in `corpus/daily/rcb/` and
`corpus/daily/rca/`):

* Round 20 (RC-B, Black): five consecutive 100–143 cp errors on moves 8–12;
  12…Nxd5 root +9 against a true −481 because 13.Qxd5 … 16.Nc7+ is a fork by
  check one ply past the capture-only quiescence.
* Round 18 (RC-A, repaired by RC-B's extra ply): 15…g6 piece trap one ply
  past depth 6.
* Round 17 (RC-A, RC-B identical): 47.Re1 throws +518 into a perpetual; not
  repaired by depth 9.

Claude must diagnose before coding. Possible mechanisms may include:
qsearch, forcing-line handling, selective checks, pruning, move ordering,
instability verification, leaf tactical verification, or another
demonstrated mechanism. These are possibilities, NOT mandatory
implementations. A mechanism that repairs the diagnostic positions must also
be shown not to lose depth on ordinary positions (the 240-position
equal-time suite in `corpus/daily/rcc/cl240_*` is the existing negative
control) before any timed arena.

Do NOT duplicate Kushagra's speed lane unless canonical spec.md explicitly
reassigns scope.

## 9. Friend Loss-Analysis Responsibility — R21+

The friend's Claude owns systematic analysis of EVERY GAME CLAUDESHARK LOST
TODAY FROM ROUND 21 ONWARD, inclusive. DATE: 2026-09-05. Sources: the public
team page (`tools.aichessathon_public`), the platform logs the user
downloads, `tools.daily.ingest`, `tools.postmortem.annotate` (Stockfish is
research-only and never ships).

For each available Round >= 21 loss:

1. find PGN / log;
2. establish exact build attribution (every game after 12:01 UK on
   2026-09-05 is RC-B unless section 2 records a later user-confirmed upload);
3. find the first meaningful deterioration;
4. first >= 100 cp ClaudeShark error;
5. largest cp loss;
6. first win/draw -> loss transition;
7. opponent's attacking sequence;
8. opponent's oracle accuracy;
9. ClaudeShark's defensive errors;
10. classify what actually caused the loss.

DO NOT merely call an opponent "aggressive". Operationally distinguish:

* **A. SPECULATIVE AGGRESSION** — high forcing-move density / sacrifices /
  direct king attack, but some attacking moves are objectively questionable
  or depend on ClaudeShark errors.
* **B. CALCULATED FORCING ATTACK** — checks / captures / threats form a sound
  concrete sequence; the oracle approves the attack and the opponent's
  calculation is accurate.
* **C. PLANNED / PREPARED ATTACK** — several preparatory moves precede the
  breakthrough: piece coordination, pawn breaks, rook lifts, queen
  repositioning, line opening, king-zone buildup, restriction of defenders.
* **D. MIXED** — planned buildup followed by sound forcing calculation.
* **E. NOT ATTACK-DRIVEN** — ClaudeShark loses primarily because of a
  tactical blunder, endgame error, conversion failure, material loss, time
  issue, or another cause unrelated to opponent attacking style.

For each game record: ROUND, BUILD, BUILD CONFIDENCE, COLOUR, RESULT, ATTACK
START MOVE, OPPONENT FORCING-MOVE DENSITY, QUIET PREPARATORY MOVES,
SACRIFICE / MATERIAL INVESTMENT, ORACLE QUALITY OF ATTACK, FIRST CLAUDESHARK
>= 100 CP ERROR, LARGEST CLAUDESHARK ERROR, PRIMARY LOSS MECHANISM, STYLE
CLASSIFICATION, CONFIDENCE, DOES CURRENT RC-C WORK ADDRESS IT?

Then aggregate all losses R21+: how many were speculative aggression,
calculated forcing attacks, planned attacks, mixed, not attack-driven.
Determine whether there is REAL evidence that ClaudeShark is systematically
weak against aggressive opponents, or whether those losses are caused by
something narrower. Do not infer opponent style from result alone.

If a Round >= 21 loss file is unavailable: record MISSING SOURCE. Do not
fabricate analysis.

Detailed evidence goes in a tracked lane report under `benchmarks/current/`
(suggested `2026-09-05-r21plus-loss-audit.md`); the summary goes in
section 14.

## 10. Experimental Gates

* **Gate 0** — correctness / legal moves / regression / fingerprint /
  baseline equivalence. RC-B reference: depth-6 suite 1,708,269 nodes
  (`uv run python -m tools.bench --depth 6`), sharp suite 1,852,716; full
  test suite passes.
* **Gate 1** — causal target + matched negative controls (the mechanism
  repairs the pre-registered positive positions and does not change the
  decision or lose depth on the matched negatives).
* **Gate 2A** — economical controlled strength screen vs `champions/rc_b`
  at 120 s + 0.5 s, 300-ply cap, on
  `corpus/daily/pool/competition_actual_suite.jsonl` (paired colours).
* **Gate 2B** — long validation (160–226 games) only for a real survivor.

For serious matches always report: W/D/L, score, nominal Elo, total
families, informative families, informative fraction, family bootstrap,
leave-one-informative-out, colour split, failures, clock floor
(`tools.daily.swissrisk` produces all of these from the arena JSONL).

Mirrored games do not equal independent evidence: a family whose two games
are a win and a loss by colour contributes zero information.

## 11. Promotion Rules

RC-C MUST BEAT RC-B.

Fixing one diagnostic position is not sufficient. Running faster is not
sufficient. Beating RC-A is not sufficient.

A promoted change requires: correctness; causal repair; negative controls;
controlled strength; meaningful family evidence; safe clock behaviour (clock
floor not below RC-B's in the same match, no flags); no serious live
regression.

If no candidate beats RC-B, RC-B remains champion.

Exception for identity-preserving changes (identical tree, fingerprint
unchanged): the strength screen is a non-regression and clock check; the
promotion standard is Gate 0 identity plus a non-negative screen, the
standard RC-B's stalemate probe met.

## 12. Combination Rules

If Kushagra's Candidate A and the friend's Candidate B are independently
positive: DO NOT simply merge them and call it RC-C.

Test RC-B + A, RC-B + B, then RC-B + A + B. The combined candidate must
separately earn promotion under section 11.

## 13. Fable → Friend Instructions

SPEC_REVISION: 2

CURRENT FRIEND SCOPE: tactical horizon / forcing-line robustness (section 8)
and the R21+ loss audit (section 9).

PRIORITY:
1. Set up: create `friend/rcc-tactical-horizon` from `origin/rc-c-integration`;
   confirm the engine is exact RC-B (`uv run python -m tools.bench --depth 6`
   = 1,708,269 nodes; `uv run python -m pytest -q` passes).
2. R21+ loss audit (section 9) — the cheapest source of new information; it
   drives both lanes. Public team page fetched 21:50 UK
   (`analysis/refresh_2026-09-05/claudeshark_team_games_2150.json`, 29
   games listed): rounds 21–29 are all RC-B, 3W 3D 3L. The three losses:
   **Rated 23** (Black vs David Naylor, Caro-Kann Classical), **Rated 24**
   (Black vs Rustic Alpha 3, Sicilian Closed), **Rated 25** (White, opponent
   name did not parse, Semi-Slav Defence). Draws: R21 (White vs "AI < human",
   Sicilian Dragon), R22 (Black vs "this team", Sicilian Closed), R29 (White
   vs NotLLM, Catalan). Wins: R26, R27, R28. Game pages are
   `https://aichessathon.com/game/<game_id>` from that JSON; ingest with
   `tools.daily.ingest` under BUILD = RC-B and annotate with
   `tools.postmortem.annotate`. The three draws are worth the same
   first-deterioration pass if time allows (R17-style conversion failures
   count as losses of half a point).
3. Tactical-horizon diagnosis on the R20 / R18 / R17 positions, then a
   mechanism only if the diagnosis supports one.

DO:
* keep every experiment on your own branch; commit records under
  `benchmarks/current/`, raw data under `corpus/daily/`;
* pre-register hypothesis, mechanism, what must stay unchanged, and the
  rejection condition before measuring;
* run the fixed-depth negative control (ordinary positions must not lose
  depth or nodes materially) before any timed arena;
* update section 14 of your branch's `spec.md` on every push.

DO NOT:
* start from Candidate 3 or touch `cs_eval.pst_*` / `legal_captures`
  (Kushagra's lane);
* resurrect the rejected check-extension implementation because it fixes
  the R20 puzzle;
* modify `main`, `rated-v1`, `champions/rc_b`, `corpus/release/*`;
* push to `rc-c-integration`;
* run more than one CPU-heavy job, or leave any job running between tasks;
* use Stockfish for anything that ships.

QUESTIONS TO ANSWER:
1. Of the R21+ losses, how many are attack-driven (A–D) versus not (E)?
2. Is there one mechanism that explains more than one loss?
3. Can a horizon repair be made that costs less than 0.2 ply on the
   240-position ordinary suite at equal time?

STOP CONDITION: a candidate mechanism either (a) fails the fixed-depth
negative control, or (b) scores below 50% vs RC-B in a 64–100 game screen
with a bootstrap that excludes zero — record and move on; or the audit shows
the losses are not horizon-driven — report and await re-scoping.

MAX SUGGESTED TIME: audit 60–90 minutes; diagnosis 30 minutes; one
mechanism implementation 25 minutes + Gate 0/1 30 minutes before any arena.

LATEST COORDINATOR MESSAGE: 2026-09-05 21:50 UK — revision 2: the R21+
game list above is now known (three losses, R23/R24/R25, all RC-B). Start
the audit there. Candidate 3's speed transferred to the PC (+16.5% knps,
identical tree) and its 100-game screen vs RC-B is running until ~22:55; I
will read your section 14 at that boundary.

## 14. Friend → Fable Findings

(Controlled by the friend's Claude on its feature branch. Every push updates
this section there; the coordinator copies relevant findings here.)

ACKNOWLEDGED_SPEC_REVISION: —
CURRENT TASK: —
STATUS: not started
COMMIT: —
FILES CHANGED: —
HYPOTHESIS: —
RESULT: —
KEY NUMBERS: —
ROUND 21+ FINDINGS: —
REJECTED IDEAS: —
OPEN QUESTIONS: —
RECOMMENDED NEXT ACTION: —
ACTIVE JOBS: NONE

## 15. Fable Lane Findings

2026-09-05 21:35 UK — Candidate 3 (`champions/rcc_speed`): Gate 0 passed on
the Mac (identical fingerprints, 1,227 tests, +18.7% knps). Windows: process
sweep clean; `rc-c-integration` normalised to exact RC-B (engine blobs equal
to `3d918a5` and `champions/rc_b`; the two candidate-3 tests removed from the
integration branch, kept on the lane branch). The Mac partial (59 games) is
historical non-decisive data only.

2026-09-05 21:42 UK — **PC speed transfer: PASS.** Depth-6 suite, alternated
RC-B / candidate / RC-B / candidate on a quiet machine: RC-B 75,764 and
76,234 knps; candidate 88,104 and 89,056 knps (**+16.5%**; Mac +18.7%);
1,708,269 nodes in all four runs (`corpus/daily/rcc/pc_speed_transfer_depth6.txt`).
**PC Gate 0: PASS** — 1,228 tests pass on the lane. Fresh Gate 2A screen
launched 21:42 (section 17); the decision is made from that artifact only.

## 16. Integration Queue

Nothing enters here without evidence.

| CANDIDATE | OWNER | COMMIT | GATE STATUS | CONTROLLED RESULT | READY TO INTEGRATE? | REASON |
|---|---|---|---|---|---|---|
| Candidate 3 speed | Kushagra / Fable | `f2543bd` | Gate 0 PASS (Mac); Gate 2A pending (PC) | none complete | NO | screen not run in full |

## 17. Active Jobs

| agent | PID | task | output | start | expected finish | max runtime | kill condition |
|---|---|---|---|---|---|---|---|
| Fable (PC) | 24324 (uv) → 22576 (arena) + 6 workers | Gate 2A: `champions/rcc_speed` vs `champions/rc_b`, 100 games, 120 s + 0.5 s, 300-ply cap, 6 workers, `competition_actual_suite` | `corpus/daily/rcc/speed_vs_rcb_120s_100_pc.jsonl` (+ `.pgn` at the end, `.log`) | 2026-09-05 21:42 UK | ~22:55 UK | 90 min | any flag / crash / illegal move on the candidate side; or a clearly negative decision before 100 games; if stopped early the artifact is renamed `PARTIAL-NON-DECISIVE` |

(Any listed job needs: agent, PID, task, output, start, expected finish,
kill condition. Remove it immediately after completion.)

## 18. Inter-Agent Messages

* 2026-09-05 21:35 UK — Fable → Friend: revision 1 published. Branch from
  `origin/rc-c-integration`. Your scope is sections 8, 9 and 13. Report in
  section 14 on your branch; I read it at my task boundaries, not by polling.
* 2026-09-05 21:50 UK — Fable → Friend: revision 2. Rounds 21–29 fetched;
  losses are R23, R24, R25 (details in section 13). Candidate 3 screen
  running on the PC until ~22:55.

## 19. Codex Monday

Reserve Codex primarily for: independent red-team; candidate review;
statistical / methodological challenge; independent failure diagnosis; or a
genuinely separate third lane. Do not automatically use Codex to reproduce
work Claude already completed.
