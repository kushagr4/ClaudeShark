# V2 autonomous session — handoff for an independent red-team review

This document exists to be attacked. It is written for a reviewer whose job is
to disprove its conclusions, so it separates what was measured from what was
inferred, states sample sizes before results, and keeps the negative and
inconclusive experiments in the same detail as the positive ones.

The single most important thing in it is not an Elo number. It is section D.2:
a measurement-quality finding that changes how several *previously recorded*
results in this repository should be read.

---

## A. Exact repository state

| item | value |
|---|---|
| branch | `v2.2-development` |
| `rated-v1` tag → commit | `98c48c89b3a8142e6567e5f46b2d2036df7297d1` |
| `main` | `98c48c89b3a8142e6567e5f46b2d2036df7297d1` (unchanged, identical to `rated-v1`) |
| `origin/main` | `98c48c89b3a8142e6567e5f46b2d2036df7297d1` (unchanged) |
| session start HEAD | `a116be26fcbf026005fb1de158c5dc24b26ba533` |
| Git identity | `kushagr4 <ratrakushagra@gmail.com>` on every commit |
| pushed | **nothing**; `origin/v2.2-development` is still at `a116be2` |
| deterministic fingerprint | `uv run python -m tools.bench --depth 6` → **1,712,405 nodes**, identical to rated V1, with every experimental term off |

Commits made this session are listed in section I.

`rated-v1` and `main` were not touched: no retag, no merge, no rewrite, no
force. Verify with `git rev-parse rated-v1^{commit} main origin/main`.

## B. The champion model as it stands

| role | directory | status |
|---|---|---|
| historical rated submission | `champions/rated_v1` | immutable |
| **V2 champion** | `champions/v2_1_kingpawn` | promoted in a previous session on +19 Elo over 200 paired games; **the interval still spans zero** |
| frozen, not promoted | `champions/v2_2a_low_material` | Gate 1 pass, no demonstrated game effect |
| derived variants for the tempo experiment | `champions/v2_1_kingpawn_tempo{16,24,32}` | one constant differs; built and verified by `tools.make_time_variants` |

The V2.1 Daily package `corpus/v2/kp/submission_v2_1_kingpawn.zip` still hashes
to `a8b95a5cab3e33aaac6e5d3e686eb7f292d3a600a115e18e077b9622f35bbd0a`.

## C. Experiments

Each entry gives the hypothesis, the evidence that motivated it, what was
measured, and the verdict. The machine-readable version is
`benchmarks/current/V2_10H_SUMMARY.json`.

### C.1 V2.2a low-material nominal-surplus scaling — KEEP FOR MORE TESTING

Full record: `benchmarks/current/2026-09-04-v2.2a-low-material.md`.
Commit `0de5912`.

Gate 1 passes on every stated target (421 of 429 audited false wins removed, no
genuine or strategic win pushed under +100, +1.8% evaluator time), and in real
Gate 2 games the in-family false-win evaluations fall from 17 of 65 to 0 of 65.
Overall 200-game result: +38 =125 −37, 50.2%, Elo +2, cluster bootstrap −0..+5.

Not promoted. See D.2 for why that Elo figure carries almost no evidence, and
the record for the four adverse targeted clusters, two of which are genuine
regressions verified against Stockfish at 5,000,000 nodes.

### C.2 Colour asymmetry audit — no engine defect found

Full record: `benchmarks/current/2026-09-04-colour-asymmetry-audit.md`.
Commit `70f526e`.

Evaluator exactly symmetric on 600 mirrored pairs; search symmetric to within
non-directional tie-break noise; no colour anywhere in the clock code and
74.8 s versus 75.0 s spent in the two rated games. Internally White scores
52.2% over 1,334 paired games. All four known competition start positions have
Black to move, which is the only colour hypothesis the audit leaves open, and
it is a property of the organisers' position pool rather than of any engine.

### C.3 Cluster-evidence audit — a measurement-quality result

Commit `dd257ac`. Output `corpus/daily/cluster_evidence.txt`. See D.2.

### C.4 V2.3 tempo — pre-registered, result in section C.5

Design fixed and committed (`d059187`) *before* any candidate was measured:
`benchmarks/current/2026-09-04-v2.3-tempo.md`.

### C.5 Results filled in at the end of the session

See the sections appended below the red-team questions.

## D. The strongest claims, and the counter-evidence to each

### D.1 ClaudeShark's engine is colour symmetric — **high confidence**

*Evidence.* 600 colour-reflected position pairs: static and quiescence scores
negate on 600 of 600, covering castling, en passant, promotable, pawnless and
in-check positions. Root scores and best moves differ on 45 and 33 of 600
respectively, but with no direction (mean root difference −0.03 cp; sign split
27 versus 18, z = +1.34; total node ratio 0.9943). No colour appears in
`cs_time.py` or `agent.py`, and measured clock use in the two rated games
differs by 0.2 s out of 75.

*Counter-evidence.* The sample is 600 positions at depth 5, not thousands at
depth 8; a directional effect smaller than about 5 cp would not be detected.
The two rated games are two games.

### D.2 Several recorded Gate 2 results rest on a handful of start clusters — **high confidence**

*Evidence.* `corpus/daily/cluster_evidence.txt`. A paired match plays each
start position twice with the colours swapped; two deterministic engines that
differ only in rare positions play the *same game* both ways, and such a
cluster contributes a win and a loss to the headline and nothing to the
evidence.

| match | informative clusters | headline |
|---|---|---|
| V2.1 king-pawn vs rated-v1 | **41 of 100** | +19.1 Elo |
| passed pawns v1 | **42 of 100** | +1.7 Elo |
| mop-up v1 | **2 of 100** | +3.5 Elo |
| V2.2a low material | **1 of 100** | +1.7 Elo |
| V2.2a targeted | **4 of 83** | −8.4 Elo |

*Consequence.* The mop-up entry in `PROJECT.md` now carries an erratum. The
V2.1 result survives: leave-one-cluster-out gives +15.8..+22.8 Elo and the six
best clusters must be removed before the estimate reaches zero, so it is a
broad small edge rather than one lucky position.

*Counter-evidence.* "Informative" here means the pair was not mirror-identical;
a cluster can also be uninformative in softer ways this count does not capture.

### D.3 The engine's evaluation is symmetric and compressed, not optimistic — **high confidence**

*Evidence.* `corpus/daily/calibration_all_phases.txt`, 35,202 positions from
every ply of four annotated 200-game corpora, unselected. Blind wins 13.8% of
eligible positions against blind losses 11.8%; false wins 5.6% against false
losses 5.6%. When the mover is winning the root reads +428 against an oracle
+559; when losing, −416 against −559. Those are mirror images.

*Why this matters.* Reading only the two rated games suggests the opposite —
in the 16 positions where ClaudeShark lost 50 cp or more its root was higher
than the oracle in 14. That is selection bias: those positions were chosen
*because* the engine erred. The unselected measurement says there is no
optimism to fix.

*Counter-evidence.* The oracle scores come from a 200k/1M-node two-pass
annotation, not a deep analysis; compression could be partly an artefact of
comparing a depth-6 root with a node-limited Stockfish.

### D.4 The biggest remaining residuals are search, not evaluation — **medium confidence**

*Evidence.* `corpus/daily/attribution_endgame_calibrated.txt`. After removing
the engine's uniform compression by calibrating an expected root per 50 cp
oracle band, the largest departures belong to advanced passed pawns — own best
passer on the sixth rank +41, on the seventh +61; enemy best passer on the
seventh −67 — while the *static* departure in the same buckets is small or of
the opposite sign (−18, +15, −11). A bucket whose root departs and whose
static does not is a horizon effect.

*Counter-evidence.* The static and root columns are not measured on the same
footing: the root is the value of the best move found, which is a maximum over
noisy leaves and is upward biased by construction. Some of the gap between the
two columns is that bias rather than horizon.

*Consequence.* It argues against the obvious next evaluation term — reshaping
the passed-pawn curve — and it is consistent with the recorded failure of
passed pawns v1, which added a steeply convex bonus at exactly the ranks where
the engine is already too optimistic and then reached seventh-rank passers far
more often while performing worse.

### D.5 ClaudeShark's rated loss was a strength gap, not a blunder — **medium confidence, n = 1**

*Evidence.* `corpus/daily/rated_report.txt`. In round 1 ClaudeShark's median
centipawn loss was 36 and it made no error of 100 cp or more until move 21; its
opponent's median loss was **2** and it made none at all. The evaluation drifted
from +87 to −112 across moves 10 to 17 through five inaccuracies of 39 to 96 cp,
none individually decisive.

*Counter-evidence.* One game. The round-2 opponent was much weaker (median 24,
two blunders over 300 cp) and ClaudeShark won it while playing at a median loss
of 4.

## E. Claims not to trust

1. **Any Elo point estimate in this repository from a paired match with few
   informative clusters.** See D.2. This includes the +3 Elo mop-up figure and
   the +2 Elo V2.2a figure.
2. **The V2.1 promotion is not proven.** +19 Elo with a cluster bootstrap of
   −7..+45 is "promising", and this session's independent pool match is the
   first attempt to narrow it.
3. **The two rated games.** One win and one loss. Every per-colour statement
   drawn from them is anecdote; they are retained as external holdout, not as
   evidence.
4. **Mechanism labels.** "Tactical/horizon", "king-to-pawn coordination" and
   the rest come from a labelling pass, not from ablation. D.4 is the first
   attempt to test one of them directly.
5. **All NPS numbers taken during this session are contaminated.** The machine
   ran six to eight concurrent game workers and a Stockfish pool for most of
   it. Node counts and fixed-depth results are unaffected; wall-clock and NPS
   figures must be re-measured on a quiet machine before being quoted.
6. **The competition start-position claim rests on four FENs.** Two rated games
   plus two smoke games in the submission's build log.

## F. Top unresolved failure positions

`corpus/daily/failure_gallery.txt` and `.json` hold the fifteen widest
engine-oracle disagreements, one per source cluster, with the oracle score and
move, the engine's root and static, the structural label and the source. Two
worth singling out:

* `8/8/3k4/8/P1P1p3/4K3/5P2/8 w - - 1 56` — oracle **+1898**, engine root
  **+320**. A pure pawn ending with two connected passers on the fourth rank,
  which the attribution report independently identifies as the bucket where the
  engine most under-values its own position.
* `8/1p2B3/2p5/2P2K2/6P1/8/5k2/8 b - - 0 60` — oracle **−1910**, engine root
  **−447**. The mirror failure: the engine does not see that it is lost.

## G. The rated games

| | round 1, "the castle gambit" | round 2, "trio duo" |
|---|---|---|
| our colour | **White** (86.2% move agreement) | **Black** (100% move agreement) |
| result | **loss**, checkmate | **win**, checkmate |
| start FEN | `rnbqk2r/p3nppp/1p2p3/2ppP3/P2P4/2P2N2/2P2PPP/R1BQKB1R b KQkq - 0 8` | `rn1qkbnr/pp2pppp/2p3b1/8/3P4/4B1N1/PPP2PPP/R2QKBNR b KQkq - 4 6` |
| oracle at the start | +38 for White | +26 for White |
| first inaccuracy | move 11 O-O, −62 (oracle preferred exf6) | move 9 Qb6, −89 |
| first serious error | move 21 Bb2, −145 | move 13 Bc3, −113 |
| largest error | move 31 Qb3, mate in one allowed | move 18 O-O, −149 |
| our median cp loss | **36** | **4** |
| opponent median cp loss | **2** | **24** |
| our errors ≥ 100 cp | 5 | 2 |
| opponent errors ≥ 100 cp | **0** | 4, two of them over 300 |
| clock | 74.8 s spent, **57.3 s left** | 75.0 s spent, **57.2 s left** |
| main mechanism | slow positional drift in a closed centre; Black's c5/d5 duo becomes a passed d-pawn that queens | opponent blunders; our own two errors were not punished |
| time issue | under-use, not a flag | under-use, not a flag |
| does V2.1 repair it? | **no** — identical move in all ten error positions | **no** — identical move in all six |
| does V2.2a repair it? | **no** | **no** |

**Cross-game.** The only mechanism appearing in both games is that neither
candidate changes a single one of ClaudeShark's sixteen error moves: V2.1 and
V2.2a play exactly what rated-v1 played in fifteen of sixteen, and the
sixteenth is already lost. Nothing else repeats; two games cannot establish a
repeated external signal, and none is claimed. The rated games remain external
holdout and no coefficient or feature in this session was chosen from them.

## H. Reproduction commands

Windows CMD, from the repository root.

```
uv run python -m tools.bench --depth 6
uv run python -m pytest -q
uv run ruff check .
uv run python -m tools.release_check
```

```
uv run python -m tools.daily.ingest --pgn corpus/daily/round1-the-castle-gambit.pgn corpus/daily/round2-trio-duo.pgn --out corpus/daily/games/rated.jsonl
uv run python -m tools.daily.whoami --games corpus/daily/games/rated.jsonl --engine champions/rated_v1 --depth 6 --out corpus/daily/whoami_rated_v1_d6.txt
uv run python -m tools.postmortem.annotate --games corpus/daily/games/rated.jsonl --out corpus/daily/games/rated_annotated.jsonl --cheap 300000 --deep 3000000 --refine-at 40 --workers 8
uv run python -m tools.daily.report --games corpus/daily/games/rated_annotated.jsonl --colours corpus/daily/colours.json --depth 6 --threshold 50 --out corpus/daily/rated_report.txt
```

```
uv run python -m tools.daily.symmetry --engine champions/rated_v1 --depth 5 --positions 600 --out corpus/daily/symmetry_rated_v1_d5.txt
uv run python -m tools.daily.colour --out corpus/daily/colour_split.txt
uv run python -m tools.daily.calibrate --out corpus/daily/calibration_all_phases.txt
uv run python -m tools.daily.attribute --out corpus/daily/attribution_endgame_calibrated.txt
uv run python -m tools.daily.gallery --count 15 --out corpus/daily/failure_gallery.txt
uv run python -m tools.daily.clusters --games corpus/v2/kp/games/gate2_fixed_depth.jsonl corpus/v2/fw/lowmat/games/gate2_fixed_depth.jsonl --out corpus/daily/cluster_evidence.txt
```

```
uv run python -m tools.postmortem.play --cand champions/v2_2a_low_material --base champions/v2_1_kingpawn --pairs corpus/postmortem/pairs.json --depth 6 --workers 6 --out corpus/v2/fw/lowmat/games/gate2_fixed_depth.jsonl
uv run python -m tools.postmortem.annotate --games corpus/v2/fw/lowmat/games/gate2_fixed_depth.jsonl --out corpus/v2/fw/lowmat/games/gate2_annotated.jsonl --workers 8
uv run python -m tools.v2.lowmat_gate2 --games corpus/v2/fw/lowmat/games/gate2_annotated.jsonl --cand champions/v2_2a_low_material --base champions/v2_1_kingpawn --out corpus/v2/fw/lowmat/17_gate2.txt
```

```
uv run python -m tools.daily.pool --count 60 --out corpus/daily/pool/competition_like_pairs.json
uv run python -m tools.postmortem.play --cand champions/v2_1_kingpawn --base champions/rated_v1 --pairs corpus/daily/pool/competition_like_pairs.json --depth 6 --workers 6 --out corpus/daily/pool/games/v21_vs_ratedv1.jsonl
uv run python -m tools.daily.searchaudit --engine champions/v2_1_kingpawn --depth 6 --threshold 200 --limit 80 --out corpus/daily/search_audit_v21.txt
uv run python -m tools.make_time_variants --base champions/v2_1_kingpawn --module cs_constants.py --constant TEMPO --values 16 24 32 --suffix tempo
uv run python -m tools.daily.variants --engines champions/v2_1_kingpawn champions/v2_1_kingpawn_tempo16 champions/v2_1_kingpawn_tempo24 champions/v2_1_kingpawn_tempo32 --depth 6 --per-bucket 30 --out corpus/daily/tempo_variants.txt
```

The oracle is Stockfish driven at fixed nodes, single threaded, hash cleared
before every position, binary path and SHA-256 recorded in each provenance
file. It lives outside the repository and never ships.

## I. Red-team questions, with where to look

1. Is the V2.1 promotion statistically justified? — `corpus/daily/cluster_evidence.txt`, and the pool match in section C.5.
2. Is the apparent Elo gain driven by a few starting clusters? — leave-one-cluster-out in the same file. Our answer is no for V2.1 and yes for mop-up and V2.2a.
3. Are the paired games genuinely symmetric enough? — every match plays both colours from the same FEN; the mirror-identical pair count is the honest measure of how much that buys.
4. Is there diagnostic/validation leakage? — splits are by source cluster in `tools/daily/variants.py` and by role in the V2 suites; check that no position appears in both.
5. Did repeated FENs from the same trajectory inflate the evidence? — the gallery keeps one position per cluster; the calibration report does not deduplicate, and that is stated.
6. Are Stockfish scores consistently oriented? — every tool converts to the mover's point of view at one place; `tools/daily/calibrate.py` and `attribute.py` are the ones to check.
7. Did any summary tool distort W/D/L? — the V2.2a headline was checked by hand against the raw games and the discrepancy is documented rather than corrected away.
8. Does the new evaluator double-count PeSTO information? — the king-pawn term is Chebyshev distance to the nearest pawn, which the piece-square tables cannot express; the low-material term acts only on the material component.
9. Are there adversarial endgames that defeat the new terms? — `corpus/v2/fw/lowmat/11_near_miss.txt` and `12_kp_adversarial.txt`.
10. Does V2.2a reduce blind wins at the cost of creating false wins? — `corpus/v2/fw/lowmat/06_blindwin_candidate.txt`: no move changed.
11. Does it reduce false wins by compressing all endgame scores? — it applies only inside three exact material signatures, 0.9% of evaluations.
12. Is the NPS measurement clean? — **no**, see E.5.
13. Are the causal mechanism labels supported? — partly; D.4 is the first direct test and it contradicts one of them.
14. Do the rated games provide a repeated external signal? — no, and none is claimed.
15. Is the champion genuinely safer and stronger than rated-v1? — see C.5.
16. What is the strongest argument against promoting the current champion? — its Gate 2 interval spans zero, it repairs none of the sixteen rated-game errors, and its only independent test is the pool match in C.5.
17. What one experiment should be run next? — see the closing section.
18. Which result should be reproduced before another Daily submission? — the V2.1 versus rated-v1 comparison, at 400 games or in a Daily round.
