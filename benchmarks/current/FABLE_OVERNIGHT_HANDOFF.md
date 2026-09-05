# Overnight handoff, 2026-09-05

Written for the morning. Every number below has a file behind it; the file is
named where it matters. Sections marked *pending* are filled in when the
timed match finishes.

## 1. What exact build is currently submitted?

**SUBMITTED V2.1 KING-PAWN.** `corpus/v2/kp/submission_v2_1_kingpawn.zip`,
43,489 bytes, SHA-256
`a8b95a5cab3e33aaac6e5d3e686eb7f292d3a600a115e18e077b9622f35bbd0a`, 13 Python
files, `king_pawn` on, `king_safety`/`passed`/`mopup` off, `TEMPO = 8`,
`KING_PAWN_EG = (0, 48, 36, 24, 12, 0, 0, 0)`. Not replaced during the night.

## 2. What exact Git commit matches it?

`10c92773c6770211cf56519c6757e9a90977e83c` (tag `v2.1-daily-candidate`), tree
`adaf2b6c…` = `champions/v2_1_kingpawn`, byte-identical to the archive once
line endings are normalised. Recovered by content in the previous session,
re-verified here.

## 3. What changed in the official rules?

Snapshot `benchmarks/current/2026-09-05-official-rules-snapshot.md`, raw pages
in `analysis/rules/`. Against the take-over brief:

* **No pondering.** "Your process is suspended while your opponent moves, so
  work you leave running between your own moves does not run." Extra threads
  on our own move are explicitly slower. The lane is closed by the rules.
* **No oracle book.** "A database of engine moves or evaluations shipped for
  lookup at runtime is an engine, not training data." Books are allowed only
  from our own code's output or non-engine data.
* Init budget is 90 s on the docs page and in every direct log (not 60).
* Ten uploads per team per day (not six).
* Unchanged: 13-round Swiss over locked builds by points; tie-breaks points,
  Buchholz, head-to-head, **earlier final submission**; uploads close 11
  September 11:00; 120 s + 0.5 s; 2 GB; one core; 50 MB; Python 3.12; the
  five packages; no native binaries; readable source; 300-ply material
  adjudication; validation is two smoke games.
* **Eligibility** is tied to a UK university student on the team. Not
  interpreted here. **Action for the user: get written organiser
  clarification.**

## 4. What is the user's rated record through Round 15?

**7 W, 3 D, 5 L = 8.5/15**; White 2W 2D 3L, Black 5W 1D 2L. Public rating
1598 after round 11, rank 85 of 243 (leaderboard snapshot, not rating at game
time). Canonical dataset `corpus/daily/rated_games.json/.txt`.

## 5. Which colours and results are confirmed versus inferred?

**All fifteen confirmed** from our public team page
(`analysis/refresh_2026-09-05/claudeshark_team_games.json`), cross-checked
against seven direct dashboard logs (`corpus/daily/logs/`) and the PGN
results: fifteen of fifteen consistent. Nothing is inferred any more. The two
earlier clock-fingerprint guesses (R4 Black, R5 White) were both right.

## 6. What were the largest recurring real-game failures?

`benchmarks/current/2026-09-05-rated-games-postmortem.md`. Three mechanisms:

1. **Evaluation blind to a dynamic attack**, ours or theirs — R1, R3
   (moves 18–20), R5, R10, R11. Three losses and half a draw. In round 10 the
   root read +77..+99 for five consecutive moves while Stockfish went −114 to
   −375.
2. **Conversion of a won position** — R3 (blind win at +443 shuffled into a
   threefold) and R7 (+521 spent into a perpetual check the six-ply search
   could not see). Two half-points.
3. **Opening error from a sharp curated start** — R15, decided by move 10.

Across 491 decisions: 104 correct-move/wrong-score, 18 wrong-move/wrong-score,
30 wrong-move/right-score, 4 blind wins, **0 false wins**. Depth 7 or 8
repairs 6 of the 27 key decisions (`corpus/daily/rated15_key_deeper.txt`).

## 7. What did the completed 226-game match show?

Submitted V2.1 king-pawn against rated-v1 at depth 6 on the organiser's own
113 start positions: **+41 =125 −60, 45.8%, −29.3 Elo, 54 informative
families of 113, cluster bootstrap −55.8..−4.6, leave-one-out −32.7..−26.4**,
as White 44.3%, as Black 47.4%. `corpus/daily/pool/v21_actual_verdict.txt`.

## 8. Is V2.1 king-pawn actually helping deployment strength?

**No.** Fixed-depth evidence against it on the competition distribution
(above), and in the fifteen rated games it chose a different move from
rated-v1 at 5 of 90 critical positions, none of which changed anything. The
three-population picture is +19 (mid-game), −12 (synthetic competition), −29
(actual organiser starts). **Rejected for the locked build.**

## 9. Is pondering already implemented?

No (`agent.py` is single-threaded; no `threading` anywhere in the engine), and
under the current rules it cannot work. Not built.

## 10. If tested, how much did pondering help?

Not tested; impossible under the rules.

## 11. How much exact start-FEN recurrence exists?

High and rising: by rounds 14–15, 84–87% of a round's distinct starts had
appeared in an earlier round; four of our rounds 6–15 began from previously
public positions; 239 distinct starts seen in 447 public games.
`benchmarks/current/2026-09-05-start-book-recurrence.md`.

## 12. Is a legal public-start book worth shipping?

Not tonight. The only legal form is our own engine's deeper first move per
known start, a one-move gain that could not also be tested under the Swiss
lens in the same night. Recorded as the best next idea, with a pre-registered
acceptance rule.

## 13. Did time management materially cost games?

Not by time trouble: every serious error was made with 45–113 s on the clock,
spending ~2.5 s. What cost games is that the engine **never uses** its clock:
21–82 s unspent at the end of every game, 69% of its own soft budget used.
V2.4 (below) is the response.

## 14. What is the strongest currently supported build?

**RATED-V1** (`champions/rated_v1`, commit `98c48c8`, tag `rated-v1`).
Nothing has beaten it on the competition distribution. *Pending:* whether
rated-v1 with `START_FRACTION = 0.60` beats it under the real clock.

## 15. Is there an exact release candidate ready?

*Pending Stage 2.* The candidate is one of:

* **RC-A: rated-v1 exactly** (`champions/rated_v1`) — passes the release gate
  now (`tools.release_check --fast --source champions/rated_v1`: 15/15 PASS,
  39,125 bytes compressed, 106,863 unzipped).
* **RC-B: rated-v1 + `START_FRACTION = 0.60`** (`champions/rated_v1_sf60`) —
  Stage 1 passed (+0.50 ply, 93% budget used, ladder PASS); Stage 2 running.

Either is a **reversion of the submitted feature**, which the evidence
supports on its own.

## 16. Should the user submit it?

*Pending Stage 2.* See section 19 for the decision rule written before the
result.

## 17. Top unresolved risks before the final Swiss

* Dynamic-attack blindness (mechanism 1) is the largest loss source and no
  evaluator change on file addresses it; broad king safety was rejected
  globally on 2026-09-02. Depth helps about one error in four.
* Perpetual-check horizon (R7) and blind-win shuffling (R3) turn wins into
  draws; the repetition audit found the fixed-depth engine rarely repeats
  from a winning *score*, but its score is wrong in exactly these endings.
* Eligibility clarification (section 3).
* The 300-ply material adjudication rule is not modelled by the engine.

## 18. What must not be touched or reused

* `main`, `rated-v1` (`98c48c8`), the submitted archive and `10c9277`.
* Corrupt artifacts: `corpus/daily/pool/games/v21_vs_ratedv1.CORRUPT-DISCARDED.jsonl`,
  `…_actual.CORRUPT-DISCARDED-2.jsonl`.
* Frozen splits in `corpus/daily/splits/` (the 226-game and the timed
  matches cover all 113 families; both are exploratory distribution evidence
  for pre-existing builds, not feature-design data).
* Rejected: TEMPO 32, broad king safety, global material scaling, generic
  contempt, colour-specific heuristics, V2.1 king-pawn (now), V2.2a (not
  strength-proven), sf75/sf90 (soft deadline no longer functions).

## 19. What should be done next

Decision rule for Stage 2, fixed before the result: RC-B is recommended only
if (a) zero flags, crashes or illegal moves in 226 games, (b) the lowest clock
it ever held is at least 10 s, (c) its score is not below rated-v1's with the
cluster bootstrap not excluding a positive value, and (d) informative
families are reported. If (a) or (b) fails, RC-A. If (c) fails, RC-A. In
every case the recommendation is to **revert the submitted king-pawn
feature**.

After that: the own-engine start book (section 12); a timed confirmation of
V2.1 vs rated-v1 if anyone still doubts the fixed-depth result; and, for the
attack-blindness mechanism, a narrow causal audit on the round-1/10/11
positions rather than another broad king-safety term.
