# ClaudeShark RC-C Shared Specification

Canonical AI-to-AI coordination protocol for the RC-C cycle. The canonical
copy lives on `rc-c-integration`; only the coordinator changes canonical scope
there. A feature-branch owner edits only its own findings section on its own
branch. The central principle: **parallelise discovery, serialise promotion.**

## 1. Spec Revision

SPEC_REVISION: 12

LAST_UPDATED: 2026-09-06 23:20 UK (Windows PC) — repository hygiene: closed lanes tagged and removed, RC-F integrated into rc-c-integration, README/PROJECT current-state summaries; RC-F unchanged

CANONICAL_BRANCH: rc-c-integration

COORDINATOR: Kushagra / Fable

Whenever canonical scope materially changes, increment SPEC_REVISION and
update LAST_UPDATED. Editorial fixes that change no instruction do not bump
the revision.

## 2. Competition Ground Truth

CURRENT_SUBMITTED: RC-C

CURRENT_CHAMPION: RC-C (the submitted build; every upload decision is measured against it)

DEVELOPMENT_CHAMPION: **RC-F = C9 (the C5 algorithm executed by a
Numba-compiled core) + the quiescence stalemate fix** (`champions/rc_f`, branch
`kushagra/rc-f-correctness`, engine commit `b7f42cf`; frozen 2026-09-06 20:00
UK). C9 itself (`champions/c9_numba`, `8131214`) was promoted 18:50 UK on
+55 =5 −0, 95.8%, +545 Elo over 60 games vs `champions/c5_rfp` (120 s + 0.5 s,
strict, 30/30 informative families, paired bootstrap +436..+800, 0 failures —
`benchmarks/current/2026-09-06-c9-numba-core-prereg.md`). The catastrophic-
correctness boundary (`benchmarks/current/2026-09-06-rc-f-boundary.md`) found
one defect: the compiled quiescence scored a stalemate whose only captures are
illegal as material (−849 where C5 gives 0); fixed in 10 lines, no speed cost,
53 targeted rule tests added. RC-F release-checked 16/16 as
`corpus/release/claudeshark_rc_f.zip`, sha256
`4ee4033e509bf8709d7d1090037d0aeb6b146da375c88f9986cb1a67789df13d`, 64,984
bytes, 16 files — **SUBMITTED — user-confirmed activation boundary 2026-09-06 21:07 UK**
(`benchmarks/current/RC_F_UPLOAD_CARD.md`). RC-E (`claudeshark_rc_e.zip`,
`fb8f8609…58aa`) is superseded and must not be uploaded. Every new candidate
starts from `champions/rc_f` and is measured against it. C9 is **a new
high-performance implementation of the C5 architecture**, not an
identity-preserving port (fixed-depth nodes differ by 1.3%).

SPRINT MODE (user brief 2026-09-06 17:35 UK): four days to a TOP-3 bot; one
champion, one active candidate per machine, ≤ 15 min diagnostics, ≤ 30 min
implementation, 40–60-game first screens (continue at ≥ 55%), promote or
reject, change lane after two hours without progress.

| field | value |
|---|---|
| archive | `corpus/release/claudeshark_rc_f.zip` |
| SHA-256 | `4ee4033e509bf8709d7d1090037d0aeb6b146da375c88f9986cb1a67789df13d` |
| bytes | 64,984 compressed, 195,818 uncompressed, 16 files |
| frozen engine commit | `b7f42cf` (`kushagra/rc-f-correctness`); records `b863b42` |
| frozen snapshot | `champions/rc_f` (blob-identical to the archive contents) |
| **user-confirmed upload** | **2026-09-06 21:07 UK** (the user's stated activation boundary) |
| RC-F strength | C9 core +545 Elo over C5 (60 games); parity with the Stockfish 18 UCI_Elo 2800 proxy (+29 =53 −25 pooled over 107 games); 0 failures in 167 timed games |
| fallback / control | **RC-C**, `corpus/release/claudeshark_rc_c.zip`, SHA-256 `1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`, commit `f2543bd`, snapshot `champions/rc_c`, uploaded 2026-09-05 23:14 UK |
| second fallback | RC-B, `corpus/release/claudeshark_rc_b.zip`, SHA-256 `f7b94b6507c39f32c6ba40f453e302812ba0bfbce1c8be16d2129ecb458c9c1a`, commit `3d918a5`, snapshot `champions/rc_b` |

Every rated game clearly starting after 21:07 UK on 2026-09-06 belongs to
RC-F until the user confirms another upload (23:14 UK 2026-09-05 to 21:07 UK 2026-09-06 was RC-C); games in progress across the
boundary are attributed by their start time, and an ambiguous one is
labelled UNCERTAIN, not guessed. Never change CURRENT_SUBMITTED unless the
USER explicitly confirms another upload. The RC-F, RC-C and RC-B archives are
immutable. No agent uploads anything.

**Daily Five boundary (in effect from 23:15 UK 2026-09-05):** no agent may
solve, analyse, engine-check, look up or suggest moves for any position the
user is presented with in a live Daily Five attempt; if one is sent, refuse
and say why.

Rules of record (`benchmarks/current/2026-09-05-official-rules-snapshot.md`):
Python 3.12 with python-chess/numpy/torch/onnxruntime/numba only; one thread;
120 s + 0.5 s; process suspended on the opponent's clock (no pondering); a
database of engine moves or evaluations shipped for runtime lookup is an
engine; 50 MB unzipped; 90 s init; 10 uploads/day, close 11 Sept 11:00.

## 3. Branch Ownership

Branch audit 2026-09-06 23:20 UK (repository-hygiene pass): every closed
candidate lane was tagged at its tip and its branch removed from origin and
locally; nothing unique was discarded (every deleted branch's tip is a tag
below, and its records are in canonical history).

ACTIVE:

| branch | owner | baseline | purpose | status |
|---|---|---|---|---|
| `rc-c-integration` | Kushagra / Fable | **exact RC-F** (engine files = `champions/rc_f`, `b7f42cf`) since the 23:05 UK merge | canonical coordination + proven integration; carries every record and the RC-D archive | current |
| `kushagra/rc-f-correctness` | Kushagra / Fable | RC-F | the RC-E boundary, RC-F release and evening-review records; identical to integration except the RC-D archive files | complete, retained as the RC-F record lane |
| `kushagra/c10-log-lmr` | Kushagra / Fable | C9 (`99afd81`) + `a15ef48` | C10 logarithmic LMR schedule, fixed-depth Gate 1 only | **PAUSED**; rebase onto RC-F before any resumption |
| `friend/...` | Friend / Claude | branch from `origin/rc-c-integration` | the friend's independent RC-F review lane (not yet pushed) | expected 2026-09-07 |

FROZEN:

| ref | commit | meaning |
|---|---|---|
| `main` = tag `rated-v1` | `98c48c8` | RC-A / exact rated-v1, the fallback archive's source; never modified |
| tag `v2.1-daily-candidate` | `10c9277` | V2.1 king-pawn, the build that played rated rounds 1–15; rejected for the locked build |
| RC-B frozen engine | `3d918a5` | reachable from `rc-c-integration`; snapshot `champions/rc_b`, archive `corpus/release/claudeshark_rc_b.zip` |
| RC-C frozen engine | `f2543bd` | reachable from `rc-c-integration`; snapshot `champions/rc_c`, archive `corpus/release/claudeshark_rc_c.zip` |
| RC-F frozen engine | `b7f42cf` | reachable from `rc-c-integration`; snapshot `champions/rc_f`, archive `corpus/release/claudeshark_rc_f.zip` |

HISTORICAL (tags only, no branch):

| tag | commit | meaning |
|---|---|---|
| `handoff/pc-to-mac-2026-09-05` | `9d22cef` | Windows → Mac handoff (RC-A submitted, staged picker unwired); was branch `v2.2-development` |
| `handoff/mac-to-pc-2026-09-05` | `335bb8a` | Mac → PC handoff (RC-B champion, candidate 3 in the tree); was branch `mac-full-development` |
| `lane/rcc-speed-validation` | `b556571` | candidate 3 → RC-C validation lane (record copies only; engine `f2543bd` is in canonical history) |
| `lane/c4-instability-extension` | `db9a04e` | C4 instability time extension, REJECTED at Gate 1 (engine change lives only here) |
| `lane/c5-rfp` | `b0b1101` | C5 reverse futility pruning, promoted (fully merged) |
| `lane/c6-king-pressure` | `1582c72` | C6 selective king pressure, REJECTED (`cs_pressure.py` lives only here) |
| `lane/c7-lmr-safeguard` | `8c18190` | C7 LMR verification margin, REJECTED (engine change lives only here) |
| `lane/c8-proportional-time` | `f49bfaa` | C8 proportional timing, not promoted (fully merged) |
| `lane/c9-numba-core` | `99afd81` | C9 Numba core promotion (fully merged) |

DELETED 2026-09-06 23:15 UK (origin and local): `kushagra/competitor-659a3020-study`
(fully merged, zero unique commits) and the seven lanes tagged above.
Earlier deletions (2026-09-05 22:20 UK): `mac-full-development`, `v2.2-development`,
`v2-development`, `audit/aggression`, `audit/rook-endings`,
`backup/pre-history-cleanup-20260903` — all ancestors or identical-tree twins.

RULES:

* NO AGENT MAY DEVELOP ON ANOTHER OWNER'S FEATURE BRANCH.
* NO FRIEND AGENT MAY PUSH DIRECTLY TO `rc-c-integration`.
* NO FEATURE BRANCH MAY MODIFY `main` / `rated-v1` / frozen RC-B, RC-C or RC-F
  (`champions/rc_b`, `champions/rc_c`, `champions/rc_f`, `corpus/release/claudeshark_rc_b.zip`,
  `corpus/release/claudeshark_rc_c.zip`, `corpus/release/claudeshark_rc_f.zip`).
* The friend's branch is created FROM `rc-c-integration` at revision 6 or
  later (exact RC-C engine).
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
7. verify baseline / champion (section 2; `champions/rc_c` blobs unchanged);
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

Status 23:15 UK: steps 1–3 done and passed; RC-C frozen, **submitted and
champion (user-confirmed 23:14 UK)**. Step 4 (126-game extension) was not
run, on the user's instruction. The lane is complete.

DEVELOPMENT PAUSED for the user's Daily Five: no arena, no Stockfish, no
heavy analysis, no waiters, no background CPU work until the user resumes.

NEXT FABLE TASK (when the user resumes development; not started; ordered by
the competitor study in section 20 and the user's instruction of 23:15 UK;
every candidate must beat `champions/rc_c`):

1. classify RC-B's >= 100 cp errors across all available live losses (and
   the drawn games where a win was thrown away), using the friend's R21+
   audit and the study's public annotations as the inputs and verifying only
   the decisive positions — do not redo the friend's audit;
2. find the dominant causal mechanisms (horizon past the capture-only
   quiescence, conversion, evaluation, time);
3. rank the four candidate lanes by expected reduction in the LARGE
   (>= 100 cp) ERROR RATE per development minute: (a) further safe search
   efficiency (identity-preserving), (b) proportional capped timing,
   (c) the specific dominant search / horizon mechanism, (d) conversion;
4. choose on that basis and pre-register before measuring.

QUEUED HYPOTHESIS — proportional capped timing (from section 20, finding 4):
spend ≈ 0.033 × remaining clock + 0.19 s, cap ≈ 4.4 s, smooth decay, no
early-iteration gamble. This is a different variable from the closed
`START_FRACTION` (sf60) and early-surplus (early16) tests, so the "time lane
closed" verdict does not cover it. It is NOT to be implemented before the
user's RC-C decision, and it must be tested as RC-C + timing (or RC-B +
timing) under section 12, never bundled.

## 8. Current Friend/Claude Scope

INITIAL SCOPE: TACTICAL HORIZON / FORCING-LINE ROBUSTNESS.

Start from exact RC-C (`rc-c-integration` at revision 6 or later; RC-C is
RC-B with an identical search tree searched ~16% faster, so every RC-B
diagnosis below still applies).

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
* **Gate 2A** — economical controlled strength screen vs `champions/rc_c`
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

EVERY NEW CANDIDATE MUST BEAT THE CURRENT CHAMPION — RC-C from 23:14 UK
2026-09-05 (RC-C itself beat RC-B; beating RC-B or RC-A is no longer
sufficient).

Fixing one diagnostic position is not sufficient. Running faster is not
sufficient. Beating RC-A is not sufficient.

A promoted change requires: correctness; causal repair; negative controls;
controlled strength; meaningful family evidence; safe clock behaviour (clock
floor not below RC-B's in the same match, no flags); no serious live
regression.

If no candidate beats the champion, the champion remains.

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

SPEC_REVISION: 6

CURRENT FRIEND SCOPE: tactical horizon / forcing-line robustness (section 8)
and the R21+ loss audit (section 9).

PRIORITY:
1. Set up: create `friend/rcc-tactical-horizon` from `origin/rc-c-integration`
   (revision 6 or later); confirm the engine is exact RC-C (`uv run python
   -m tools.bench --depth 6` = 1,708,269 nodes; the engine files hash to
   `champions/rc_c`; `uv run python -m pytest -q` passes, 1,228 on Windows).
   **Do not start any CPU-heavy work while the user's Daily Five is live;
   the user will say when development resumes.**
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
* change `cs_eval.pst_*` / `evaluate_packed` / `cs_ordering.legal_captures`
  (the RC-C speed machinery; any candidate must keep the identity tests
  `tests/test_pst_incremental.py` and `tests/test_legal_captures.py` passing);
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

LATEST COORDINATOR MESSAGE: 2026-09-05 23:15 UK — revision 6. **RC-C is
SUBMITTED and CHAMPION (user-confirmed 23:14 UK).** `rc-c-integration` now
carries the exact RC-C engine; branch from it, and measure every candidate
against `champions/rc_c`. RC-B is the frozen fallback. Development is
paused for the user's Daily Five; keep the machine free of arenas,
Stockfish and background CPU work until the user resumes. When development
resumes, the priority is reducing our own >= 100 cp errors (below).

Previous message (revision 5, still relevant): (a) Candidate 3 passed its
fresh 100-game screen vs RC-B (58.0%, +56 Elo, 34 informative families, no
failures, clock equivalent). (b) Section 20 is canonical: a public-data
study of the rank-1 team AlphaFish. The high-priority hypothesis for your
audit framing: RC-B's dominant observable gap is its own UNFORCED >= 100 cp
error rate (RC-B R16–R20 ≈ 14.5% of moves vs AlphaFish ≈ 0.6%; caveat: not
matched populations, so this does not prove the whole gap), NOT a failure
to punish opponents (at 29 positions after an opponent error >= 100 cp, RC-B
keeps the gain 24/29, AlphaFish 20/29). So: in every R21+ loss, count and
classify OUR >= 100 cp errors (unforced vs provoked by a sound forcing
sequence), and do not prioritise generic tactical aggression because
AlphaFish wins often. Do not treat the study's architecture guess (NNUE /
numba) as evidence of anything. Revisions 2–3 still apply (losses
R23/R24/R25; branch from `origin/rc-c-integration`).

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

2026-09-06 04:12 UK — **RC-C → ~2300 → ~2400 strength programme** (user
brief 23:20 UK; ladder in `benchmarks/current/STRENGTH_LADDER.md`).
* Benchmark A defined and frozen (`STRENGTH_BENCHMARK_2300.md`): Stockfish
  18 `UCI_Elo 2300`, competition clock, **strict draw claim** — the arena's
  `auto` claim gifted 18 of 29 draws to a winning opponent in the first run
  (all 29 "draws" were claimable-only); start sets frozen
  (`corpus/strength/FROZEN.md`: dev 50 / val 40 / holdout_a 50 / holdout_b 50).
* RC-C strict baseline (dev): +44 =24 −32, **56.0%**, bootstrap 48–64%.
  Qualification on holdout_a: +50 =11 −39, **55.5%**, bootstrap 47–64%,
  0 failures — score bar met, lower bound not; confirmation run (holdout_b)
  required and queued.
* Error audit (`2026-09-06-rcc-2300-error-audit.md`): **8.95% of our moves
  lose >= 100 cp, 1.39% >= 300**; the 120 largest classified — TACTICAL
  HORIZON 41 (19 result flips), EVALUATION optimism 39 (static +269 cp above
  the oracle, mostly deepening lost positions, 7 flips), SEARCH INSTABILITY
  16 (10 flips), UNKNOWN 17 (16 flips), conversion/endgame 7.
* C4 instability-triggered time extension: **REJECTED at Gate 1** (7/38
  repairs at +44% time; the trigger fires on 64% of ordinary moves).
* C5 reverse futility pruning (`kushagra/c5-rfp`, `champions/c5_rfp`):
  Gate 0 pass (−17.5% nodes at depth 6, −29.9% at depth 8, no quality loss
  at equal depth); Gate 1 equal-time suite **better** (robust loss 34 → 31,
  +0.46 ply, paired +3.4 cp) while the target-replay leg missed its bar by
  one position — proceeding to Gate 2A as a recorded deviation. External
  screen running (section 17).
* Speed lane after profiling RC-C on the PC: remaining hot paths are
  python-chess `push`/generation; a delta pre-check in quiescence would fire
  on 4.4% of nodes — not worth it. Speed lane parked.

2026-09-06 08:40 UK — **C5 promoted as development champion (06:36)**:
internal 140 games vs RC-C +44 =59 −37, 52.5%, +17 Elo, 49 informative
families, LOO +13..+23; external 58.3% over 60; like-for-like error rate
8.30% vs RC-C 8.36% (flat). **C5 cleared the ~2300 stage on the untouched
`holdout_b`: +53 =16 −31, 61.0%, bootstrap 53–69%, 0 failures.** RC-D
(`corpus/release/claudeshark_rc_d.zip`, sha256 `3dab7d89…51e7`, release gate
15/15, Python 3.12.13 smoke PASS, fingerprint 1,409,912 from the zip) is
built and carded, **not uploaded** — the user's call. C6 (selective
king-pressure evaluation term on top of C5, `kushagra/c6-king-pressure`) is
at Gate 0/1; the ~2400 stage is being set up.

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
**PC Gate 0: PASS** — 1,228 tests pass on the lane.

2026-09-05 23:10 UK — **Gate 2A PASS; RC-C frozen.** Fresh 100-game screen
vs `champions/rc_b` (21:42–22:56, 6 workers, nothing else running):
**+39 =38 −23, 58.0%, +56 Elo**, 50 families / 34 informative (68%),
bootstrap Elo −0.0..+115, leave-one-out +50..+64, White 60.0% / Black
56.0%, 0 failures either side, clock floor 5.6 s vs 5.9 s with equivalent
distributions and a shorter largest think (9.8 vs 13.0 s). Promoted on the
identity-preserving standard (section 11 exception; the bootstrap lower
bound is exactly zero, so it does not meet the general standard on its
own). Frozen: `corpus/release/claudeshark_rc_c.zip`, sha256
`1389813694461865c8b0d505046f745179f099682a86de96bc5be57a66060dd7`, 50,258
bytes, release gate 15/15, fingerprint 1,708,269 from the zip, clock ladder
PASS, Python 3.12.13 smoke PASS; card
`benchmarks/current/RC_C_UPLOAD_CARD.md`. **Not uploaded; RC-B remains
SUBMITTED and the friend's baseline.** Optional: a 126-game extension to
226 (~2.5 h) to tighten the interval.

2026-09-06 15:30 UK — **accuracy programme** (user brief 11:45 UK).
`ACCURACY_STANDARD.md` freezes `CLAUDESHARK_ACCURACY_V1` (Lichess move
formula on our Stockfish-18 oracle, arithmetic mean, ±1000 clamp; calibrated
≈ platform − 2 points on 44 public player-games). C5 on the ~2400 proxy:
mean **94.6**, median 95.2, **minimum 83.6**, p10 89.6, 3 of 100 games at
99.5 or above; RC-C on ~2300: mean 93.0, min 80.5, 0 of 100. The 99.5%
per-game target is not near any measured build and is not claimed. 2400
audit (268 errors, all replayed): result flips UNKNOWN 31, HORIZON 24,
INSTABILITY 22, OPTIMISM 9, CONVERSION 8, ENDGAME 8. Fixed-depth ablation
traced the instability/unknown errors to **late-move reductions** (LMR off
repairs 20 of 74 at depth 8; RFP 6, null move 4), but no safeguard survived
equal time: C7 (verification margin) net +1 at −0.5 ply, rejected; C8
(proportional capped timing, the AlphaFish curve reproduced to 4.0 s at a
full clock) flat internally, identical paired accuracy, 51.7% vs 55.5%
externally, not promoted; C6 (king-pressure term) rejected earlier. Lanes
closed today with evidence: time policy (four directions), LMR safeguards,
static king pressure. Remaining lanes: conversion/endgame knowledge (16
flips; historically costly), structural speed (python-chess boundary).
C5 / RC-D remains the development champion; its 2400 qualification on
`holdout2400_a` is running.

## 16. Integration Queue

Nothing enters here without evidence.

| CANDIDATE | OWNER | COMMIT | GATE STATUS | CONTROLLED RESULT | READY TO INTEGRATE? | REASON |
|---|---|---|---|---|---|---|
| Candidate 3 speed = RC-C | Kushagra / Fable | `f2543bd` (archive `claudeshark_rc_c.zip`, sha256 `13898136…60dd7`) | Gate 0 PASS (Mac + PC); Gate 2A PASS (PC) | +39 =38 −23 vs RC-B, 58.0%, +56 Elo, 34 informative, bootstrap −0.0..+115, LOO +50..+64, 0 failures, clock equivalent | **INTEGRATED and SUBMITTED** (user-confirmed 23:14 UK; `rc-c-integration` engine = RC-C at revision 6) | identity-preserving standard met; the optional 126-game extension was not run (user's instruction) |

| C4 instability time extension | Kushagra / Fable | `db0fb1c` (branch `kushagra/c4-instability-extension`) | Gate 0 PASS, Gate 1 FAIL | — | NO — REJECTED | trigger not selective; +35–44% time |
| C5 reverse futility pruning | Kushagra / Fable | `f6c0d30` (branch `kushagra/c5-rfp`, snapshot `champions/c5_rfp`, archive RC-D `claudeshark_rc_d.zip` sha256 `3dab7d89…51e7`) | Gate 0 PASS; Gate 1 suite PASS (targets by one, deviation recorded); Gate 2A external 58.3%/60, internal 52.5%/140; 2300 qualification 61.0%/100 (bootstrap 53–69%) | see left | **READY FOR INTEGRATION TEST / UPLOAD DECISION** — development champion; RC-D carded, not submitted | non-negative internally, positive externally on fresh holdout with a lower bound above 50% |
| C6 selective king-pressure term | Kushagra / Fable | `cb34d9c` (`kushagra/c6-king-pressure`) | Gate 0 PASS, Gate 1 FAIL | — | NO — REJECTED | 5 of 50 target repairs, root-score change median 0, equal-time −2.2 cp |
| C7 LMR verification margin | Kushagra / Fable | `8c18190` (`kushagra/c7-lmr-safeguard`) | Gate 0 PASS, Gate 1 FAIL | — | NO — REJECTED | net +1 of 74 at the game clock for −0.5 ply; LMR start index / no-escape also closed |
| **C9 Numba search core** | Kushagra / Fable | `8131214` (`kushagra/c9-numba-core`, `champions/c9_numba`, archive RC-E `claudeshark_rc_e.zip` sha256 `fb8f8609…58aa`) | Gate 0 PASS (perft/eval/SEE exact, fingerprint 1,391,318, tactics 16/16, ladder PASS, release 16/16); Gate 2A internal **95.8% over 60 vs C5, +545 Elo** | 26× nps, +5.2 plies at 2 s | **YES — PROMOTED (development champion); RC-E awaits the user's upload decision** | the largest strength gain in the project's history; compile 27 s inside the 90 s init budget |
| **RC-F = C9 + quiescence stalemate fix** | Kushagra / Fable | `b7f42cf` (`kushagra/rc-f-correctness`, `champions/rc_f`, archive `claudeshark_rc_f.zip` sha256 `4ee4033e…f13d`) | correctness boundary PASS (perft, 33 targeted rule positions, legacy suite on the compiled core 1,299 pass, fixed-depth agreement 38/40 and 15/16 with C5); Gate 0 PASS (2.55 Mnps vs 2.50, tactics 16/16, ladder PASS); release 16/16 | inherits C9's +55 =5 −0 vs C5; clean 2800 calibration +11 =35 −14 (47.5%, paired bootstrap −83..+47, 0 failures); pooled C9-core record vs the 2800 proxy +29 =53 −25 over 107 games | **YES — development champion; upload awaits the USER** | fixes a real stalemate mis-score; everything else byte-identical to RC-E |
| C8 proportional capped timing | Kushagra / Fable | `61afb13` (`kushagra/c8-proportional-time`, `champions/c8_prop`) | Gate 0 PASS; Gate 2A internal 49.2%, paired accuracy identical; external 51.7% (C5 55.5%) | see left | NO — NOT PROMOTED | neutral everywhere; clock floor 4.8 s |

Anything new must beat `champions/rc_f` (the development champion; C10 is paused on `kushagra/c10-log-lmr` and must be rebased onto RC-F before it resumes); an upload decision is measured against the submitted RC-C.

## 17. Active Jobs

None (22:45 UK). Evening self-review finished; machine swept clean. C10 stays
paused. First candidate for tomorrow (after the friend's and Astra's
independent RC-F reviews): per-move reset of table/killers/history,
pre-registered in `2026-09-06-rc-f-evening-review.md`.

(Any listed job needs: agent, PID, task, output, start, expected finish,
kill condition. Remove it immediately after completion.)

## 18. Inter-Agent Messages

* 2026-09-05 21:35 UK — Fable → Friend: revision 1 published. Branch from
  `origin/rc-c-integration`. Your scope is sections 8, 9 and 13. Report in
  section 14 on your branch; I read it at my task boundaries, not by polling.
* 2026-09-05 21:50 UK — Fable → Friend: revision 2. Rounds 21–29 fetched;
  losses are R23, R24, R25 (details in section 13). Candidate 3 screen
  running on the PC until ~22:55.
* 2026-09-05 22:25 UK — Fable → Friend: revision 3, branch audit. Origin now
  carries only `main`, `rc-c-integration`, `kushagra/rcc-speed-validation`
  and the tags in section 3. Nothing about your scope changed.
* 2026-09-05 23:10 UK — Fable → Friend: revision 4. Candidate 3 passed and
  is frozen as RC-C (section 15/16). Your baseline remains exact RC-B; the
  combination is tested separately under section 12 once your lane has a
  positive result. Still nothing in your section 14 on origin — I will read
  it at my next boundary.
* 2026-09-05 23:25 UK — Fable → Friend: revision 5. The AlphaFish study
  (section 20, merged from `kushagra/competitor-659a3020-study`, analysis
  only) reframes the audit: count our unforced >= 100 cp errors per loss;
  the punish control says exploitation is not our deficit. Read section 13.
* 2026-09-05 23:15 UK — Fable → Friend: revision 6. RC-C submitted and
  champion (user-confirmed 23:14 UK); `rc-c-integration` engine is now
  RC-C; your baseline and every Gate 2 opponent is `champions/rc_c`.
  Development paused for the Daily Five until the user resumes.

## 19. Codex Monday

Reserve Codex primarily for: independent red-team; candidate review;
statistical / methodological challenge; independent failure diagnosis; or a
genuinely separate third lane. Do not automatically use Codex to reproduce
work Claude already completed.

## 20. Competitor Study — AlphaFish (`659a3020`), 2026-09-05 22:45 UK (Mac, analysis only)

COORDINATOR NOTE (23:25 UK, revision 5): merged into canonical at `b103982`
(no engine files; commit `8fe76c9`). Read with two caveats fixed by the
user: (1) the error-rate comparison is between UNMATCHED game populations
(AlphaFish's 22 games vs RC-B's R16–R20), so it is a high-priority
hypothesis about the dominant observable gap, not proof of the whole
strength gap; (2) finding 6 (NNUE / numba) is inference from public
behaviour and must not be treated as knowledge of AlphaFish's build. The
actionable content is findings 2–4: our own >= 100 cp error rate is the
variable to reduce; punishing opponents is not our deficit (24/29 vs 20/29);
and the proportional capped timing curve is a new, separately testable
hypothesis (queued in section 7, not to be implemented before the user's
RC-C decision).

Branch `kushagra/competitor-659a3020-study`; full report
`analysis/competitors/659a3020_alphafish/REPORT.md` with all public data
(22 games R9–R30, PGNs, platform review, our Stockfish annotation of both
sides, 3,241 labelled moves). No engine change; nothing uploaded.

FINDINGS:
1. AlphaFish is **rank 1, 2216** after R29 (rank 20 / 1867 at 00:12 UTC):
   16W 5D 1L (84%), performance ≈ 2290, **10W 4D 0L vs opponents ≥ 1970**,
   all 16 wins by checkmate. ClaudeShark is rank 109 / 1589; no meeting yet,
   unlikely at a 630-point gap.
2. **The gap is unforced error rate.** Per-move oracle loss (|eval| < 800):
   AlphaFish mean 6.5 cp, median 0, **≥ 100 cp on 0.6% of moves, ≥ 300 cp
   never**; its top-15 opponents 15.2 / 2.6% / 0.6%; **RC-B (R16–R20) 41.7
   / 14.5% / 1.7%**; V2.1 31.8 / 7.7%. Flat across phases (opening 5.5,
   middlegame 8.6, endings 4.0). Platform review: acpl 2.8 mean, max 21.
3. **Not tactical exploitation**: in AlphaFish's seat at the 29 positions
   where its opponents erred ≥ 100 cp, RC-B at 2.5 s keeps the gain 24/29
   (AlphaFish 20/29). Our deficit is the 1-in-7 ordinary move where RC-B
   gives ≥ 100 cp away unprovoked.
4. **Time policy**: spend ≈ 0.033 × clock + 0.19 s (89% of variance
   explained; ours 40%), hard cap 4.4 s, 3.9 s median in the first 20
   moves (ours 3.0 s), smooth decay to 0.5 s, lowest clock 4.9 s, never
   flags; found mates are played instantly. No opening book (full time on
   move 1).
5. **Contempt zero**: took a 0.00 repetition at move 9 as Black vs a
   lower-rated top-10 team (R28). Its one visible weakness is conversion
   (R22 +203 → fifty-move draw; R24 525-ply shuffle from +35). Its only loss
   was a positional grind (no blunder ≥ 100 cp) to a 1639 team.
6. **Likely build (inference only)**: numba-compiled search and/or an
   NNUE-style numpy/torch/onnxruntime evaluator; the flat, phase-independent
   error profile and the positional loss point at the evaluator.

IMPLICATIONS (for the coordinator, not instructions):
* every lane that lowers RC-B's unforced ≥ 100 cp rate at equal time
  (speed → depth, horizon) is aimed at the right variable; books,
  tablebases and new evaluation terms are not what separates us from the top;
* a proportional time policy (clock/30 + increment, cap ~4.4 s, no
  early-iteration gamble) is a cheap controlled test once the speed lane
  settles — it changes a different variable from the closed sf60/early16
  tests;
* conversion of +200 has cross-engine evidence (their R22, our R17);
* the standings bar we can realistically target is their *opponents'*
  profile: 2.6% ≥ 100 cp errors.

