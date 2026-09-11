# Learned evaluation: pilot report

Date: 2026-09-11. Engine: RC-J (runtime files byte-identical to `2bf6885`,
`main` at `3b9addd` when the pilot started). Preregistration: `DESIGN.md`
(written before any label was read). No runtime file changed; no upload, no
arena, no timing change. The upload window closed at 11:00 on 11 September, so
this is post-deadline research.

## Spec

| question | answer | source |
|---|---|---|
| offline Stockfish-labelled training | **allowed** ("training it on positions an existing engine labelled is allowed"); the network must be self-trained and a finalist shows how | `analysis/rules/docs_2026-09-05T0700.txt:65-66` |
| runtime learned weights | **allowed** (".onnx, .safetensors and .pt are fine"); only the 50 MB unzipped total limits size | docs:8, 66 |
| runtime stack | Python 3.12 + torch 2.13.0+cpu, numpy 2.5.2, python-chess 1.11.2, onnxruntime 1.29.0, numba 0.67.0; nothing else installs | docs:16-19 |
| runtime limits | one core (one thread is fastest), 2 GB, 90 s init (local harness 60 s; RC-J uses ~28 s), no network, no third-party engine or port of one, no native binaries, readable source; a shipped database of engine evaluations counts as an engine | docs:19, 26, 36-42, 65-66 |
| local gate | `tools/release_check.py` fails any file > 5 MB (:50), a `.bin` suffix (:80) and any `open(` line (:70); weights must load with `np.load(Path(__file__).parent / …)` | release_check.py |

## Current evaluator (E0)

`cs_core.evaluate(B, S)` (`cs_core.py:840-864`), the only evaluator the live
agent runs (`agent.py:21` imports `cs_fast`; `cs_eval`/`cs_terms` are never
imported): tapered PeSTO material + piece-square tables (phase = minors +
2·rooks + 4·queens, capped at 24), bishop pair 22/40, bare-king mop-up (≤ 180),
tempo +8 for the side to move. The PST sum is maintained incrementally in
`S[5]`. Cost: **16.7 ns per call** (59.9 M evaluations/s in a compiled loop over
the 1,031 test positions).

## Data

| | |
|---|---|
| sources | TWIC master games (both 2300+, ≥ 24 plies, games behind cl240 excluded) 3,998 games, 1 position each; Chessathon public games 486 (4 each); ClaudeShark vs Stockfish UCI_Elo arenas 740 (2 each); timed ClaudeShark self-play 825 (2 each) |
| games | 6,049 (175 more excluded for sharing one of the 28 RC-J autopsy start families; 108 duplicate games) |
| pilot positions | **8,991** (not in check, not over; four-field-FEN deduplicated, 21 duplicates dropped with priority test > val > train) |
| split (by group, frozen hash) | train 7,291 (3,473 groups) / validation 669 (419) / test 1,031 (430) |
| fitted subset ("quiet": Stockfish's best move is not a capture or promotion) | train 5,645 / validation 521 / test 802 |
| RC-J leakage | **ZERO**: UUIDs 0, positions 0 (3,957 game positions + 852 scanned), start families 0, move sequences 0, groups shared across splits 0 |

## Labels

| | |
|---|---|
| Stockfish | 18, official build, SHA-256 `c86215fa1977d53b82ed854540a4c7b025be4cd042276c85ba3de53fb9118911`; Threads 1, Hash 32, `UCI_ShowWDL`, `ucinewgame` per position, last exact info line |
| budget | **50,000 nodes**, the frozen rule's smallest qualifying budget: against a 4M-node reference on 300 positions, mean \|ΔE\| 0.023 (median 0.0015), WDL-category agreement 96.0%, Spearman 0.977; 30/30 identical on relabelling |
| budget caveat | at 50k nodes Stockfish's best move equals the 4M-node best move only 72.7% of the time (1M: 89.3%) |
| target | E = (W + D/2)/1000, side to move; mates saturate; cp and mate kept for diagnostics only |
| throughput | **87.8 positions/s** on 10 workers at 50k (8,991 in 102 s); ≈ 5.8/s at 1M |
| estimated cost at 50k | 50k positions ≈ 10 min; 100k ≈ 19 min; 500k ≈ 1.6 h (at 1M nodes: 100k ≈ 4.8 h, 500k ≈ 24 h). About 0.4 GB on disk at 500k |

## Linear pilot (E1)

E1 = E0 + a learned correction over 31 side-to-move-relative features
(material, mobility, pawn structure, rooks, king, space, outposts/bishop pair,
threats), each with a middlegame and an endgame weight, plus a tapered
intercept: **64 parameters**. E0 keeps coefficient 1 and the probability scale
is fixed at E0's K0 = 162.2, so E1 stays in E0's centipawn units. Validation
chose λ = 0.

| metric (quiet subset) | train E0 → E1 | validation E0 → E1 | **test E0 → E1** |
|---|---|---|---|
| binary cross-entropy (own K) | 0.5614 → 0.5310 | 0.5970 → 0.5696 | **0.5615 → 0.5290** |
| E-MSE | 0.0638 → 0.0520 | 0.0642 → 0.0533 | 0.0737 → 0.0628 |
| Spearman vs Stockfish cp | 0.653 → 0.739 | 0.567 → 0.636 | 0.660 → 0.711 |
| sign accuracy (\|E − 0.5\| ≥ 0.15) | 83.1% → 89.4% | 81.8% → 83.3% | 82.7% → 86.6% |

* Test relative BCE change **−5.8%, bootstrap 95% [−8.9%, −2.7%]** over 339 test
  groups. The uniform-scale control (E0 × 1.5, K refitted) reproduces E0 exactly
  (0.5615), as it must.
* **Where the gain is.** Unbalanced test positions (\|E − 0.5\| ≥ 0.3, n = 427):
  −18.2% BCE. **Near-balanced positions (\|E − 0.5\| < 0.1, n = 317): E1 is
  worse**, BCE +2.5%, E-MSE 0.0178 → 0.0251. By family: VS_SF −13.6%, PUBLIC
  −9.5%, SELFPLAY −3.8%, TWIC −0.8%. By phase: ≥ 16 −6.9%, 8–15 −5.2%, < 8
  −2.9%.
* **Calibration artefact.** The fitted material corrections are large and
  opposite by phase (queen −300 middlegame / +295 endgame; rook −209/+222;
  bishop −195/+124; knight −135/+147), which is material scaled about 0.6× in
  the middlegame and 1.3× in the endgame. Stockfish's WDL model is
  material-dependent: fitted separately, its scale is K = 285 in the middlegame
  and 116 in the endgame. With one K, E1 buys that calibration through its
  material counts; it is units, not chess.
* **Post-hoc check (not part of the verdict; `results/diag_phasek/`).** Giving E0
  a phase-dependent scale improves its test BCE to 0.5518 on its own. Refitted on
  top of that, the correction still improves test BCE by **−4.7% [−7.6%, −1.9%]**
  (E1b), and by **−4.5% [−7.3%, −1.9%] with no material terms at all** (E1c). The
  positional signal survives the calibration correction. It does not fix the
  near-balanced band: there every learned variant, with either calibration, is
  worse than E0 (E-MSE 0.0173 for E0 against 0.0244–0.0278;
  `results/diag_phasek/diag_strata.json`).
* Feature usefulness (validation BCE increase when a family is dropped):
  mobility 0.0065, material 0.0035, threats 0.0029, pawn structure 0.0029, king
  0.0011, rooks 0.0006, minor pieces 0.0006, space −0.0010 (space hurts).

**Pairwise move ranking** (799 test roots; each move scored by a
root-restricted 50k-node Stockfish search; 729 pairs with |ΔE| ≥ 0.05 from 458
roots, 245 groups):

| subset | n | static E0 → E1 | Δ [95%] | **quiescence-resolved E0 → E1** | Δ [95%] |
|---|---|---|---|---|---|
| all pairs | 729 | 63.9% → 74.8% | +10.8 [+7.3, +14.5] | **84.5% → 85.6%** | +1.1 [−1.0, +3.6] |
| quiet pairs | 467 | 58.9% → 71.5% | +12.6 [+7.5, +18.2] | 81.4% → 82.7% | +1.3 [−2.0, +4.7] |
| best vs game move | 92 | 54.3% → 52.2% | −2.2 [−12.4, +8.8] | 48.9% → 52.2% | +3.3 [−7.2, +13.9] |
| best vs random | 449 | 66.4% → 78.4% | +12.0 [+7.4, +16.7] | 90.4% → 90.4% | 0.0 [−2.7, +2.6] |
| game vs random | 188 | 62.8% → 77.1% | +14.4 [+6.9, +21.4] | 87.8% → 90.4% | +2.7 [−1.2, +7.1] |

The static gain is mostly what RC-J's quiescence already recovers. On the
hardest pairs, Stockfish's best move against the move actually played in the
game, both evaluators are at chance. Post-hoc E1c: quiescence-resolved
84.5% → 87.0% [0.0, +5.2], quiet pairs 81.4% → 85.0% [+0.4, +7.4], best vs game
48.9% → 57.6%.

## RC-J real-loss holdout

Not trained on: **YES** (all 30 R76–R105 games, their positions and their 28
start families excluded; leakage zero). Ground truth: Stockfish's 10M-node best
move against RC-J's played move, ordered by the 10M-node E values in
`rcj_loss_autopsy/data/verify.json`. Ties count as errors.

| set | E0 static | E1 static | E0 quiescence | E1 quiescence |
|---|---|---|---|---|
| 14 first decisive errors | 3/14 | 5/14 | **1/14** | **4/14** |
| 19 confirmed serious errors | 6/19 | 8/19 | 4/19 | 7/19 |

On the 14, E1's quiescence-resolved ranking flips R83-20w, R94-44w and
R101-29b to Stockfish's move and loses none; statically it gains those three
and loses R79-12w. Post-hoc E1c: static 6/14, quiescence 4/14. Fourteen items
make this descriptive only (three flips against none is a sign-test p of
0.25). Static repair is not search repair; no search replay was run in the
pilot.

## Runtime pilot

Measured, not estimated (`results/speed.json`, idle machine, each engine in its
own process, alternated over two rounds; the E1 engines are scratch copies of
RC-J whose `evaluate` adds the correction, never the repository's runtime files).

| | RC-J (E0) | E1 zero-weight copy | E1 |
|---|---|---|---|
| static evaluation | 16.7 ns (59.9 M/s) | — | 738 ns (1.35 M/s), 44× |
| depth 10, 24 balanced openings: nodes | 16,818,635 (= recorded C15-v2 fingerprint) | **16,818,635, same moves** (plumbing control passes) | 26,258,913 (+56%) |
| depth 10: nodes per second | 2.20 M | 1.32 M (0.60×) | 1.26 M (**0.58×**) |
| 1,000 ms per position: mean completed depth | 12.02 | 11.42 | **11.31 (−0.71 ply)** |
| 1,000 ms per position: nodes per second | 2.20 M | 1.49 M | 1.47 M (0.67×) |
| compile at import | 27.5–31.5 s | 33.2–33.6 s | 33.2–34.2 s |

The zero-weight copy searches the identical tree and is still 40% slower, so
the whole slowdown is the feature computation (attack maps and pawn structure
recomputed at every leaf), not the plumbing. By the guidance bands this is
more than 30% NPS: **E1 as implemented is not an engine candidate** and was not
integrated. Cheaper routes, all untested: drop the families with little value
(space hurts; rooks, minor pieces and king add little), reuse attack maps
already computed for move generation, or evaluate the correction lazily only
where it can change a stand-pat cutoff.

## Neural pilot design (not trained)

Input: NNUE-style sparse piece-square features from both perspectives,
colour-flipped so the network is symmetric by construction; an accumulator per
perspective, side to move's first, then a small dense head. Integer inference
in Numba with the weights passed as arrays (not module globals, which Numba
freezes into the compiled code).

| candidate | input | accumulator | head | parameters | int16 size |
|---|---|---|---|---|---|
| N1 | 768 (piece × square) | 128 per perspective | 256 → 32 → 1 | ≈ 107k | ≈ 0.2 MB |
| N2 | 4 king buckets × 768 = 3,072 | 128 | 256 → 32 → 32 → 1 | ≈ 403k | ≈ 0.8 MB |
| N3 | 8 king buckets × 768 = 6,144 | 256 | 512 → 32 → 32 → 1 | ≈ 1.59M | ≈ 3.2 MB (under the local 5 MB gate) |

Quantisation plan: train in float32 with the same calibrated WDL loss (with a
phase-dependent K; see the calibration finding), then int16 accumulator weights
with int32 sums, and int8 head weights with a clipped-ReLU. Compare float and
quantised on test loss, pairwise ranking and speed. Full recomputation costs
about 30 active features × 128 × 2 additions plus the head per evaluation,
several microseconds, which is far above RC-J's node time. Incremental
accumulators updated in `make_move`/`unmake_move` (per-ply stack indexed by
`S[6]`, refreshed on king-bucket change) will be needed, not optional. Data
needs: N1 about 100k+ positions, N2 about 0.5–1M, N3 several million.

## Pilot verdict

**SCALE DATASET**, by the frozen rule: the labels are stable at 50k nodes, E1
improves the test calibrated loss with an interval excluding zero (−5.8%
[−8.9%, −2.7%]), and its quiescence-resolved pairwise accuracy is not below
E0's (85.6% against 84.5%).

What that verdict does and does not say:

* Held-out signal exists, and it survives correcting the calibration artefact
  (−4.5% with no material terms).
* It lives in unbalanced positions. On near-balanced positions, where RC-J's
  real-loss errors begin (E 0.35–0.50), every linear variant is worse than E0,
  the quiescence-resolved ranking gain is not significant, and on Stockfish's
  move against the game move both evaluators are at chance. Cheap handcrafted
  features do not reach the quiet positional judgement the autopsy pointed at.
* E1 costs 42% NPS and 0.7 ply at 1 s per move. It is a measuring stick, not a
  candidate, and nothing was integrated.

So scaling is justified for Stage C, a representation that can learn quiet
positional structure, not for promoting the linear model. Proposed for
approval before any main job:

1. **Target:** a phase-dependent sigmoid scale (Stockfish's WDL is
   material-dependent: K 285 middlegame against 116 endgame), so no model buys
   calibration through material weights.
2. **Main labels:** 100k positions at the frozen 50k-node budget, about 20 min
   on 10 workers. At 2300+ the TWIC pool supplies about 58k at 4 per game.
   Reaching 100k needs 6 per game or a 2100 floor. 500k needs all 61k TWIC
   games or new self-play, which is CPU-heavy and needs approval.
3. **Evaluation labels:** the 50k-node best move agrees with 4M nodes only 73%
   of the time, so relabel the validation and test splits (and all pair
   moves) at 1M nodes, about 1 h, to make the ranking tests less noisy.
4. **Stage C order:** N1 (768 → 2×128 → 32 → 1), float then int16. Speed is
   judged with incremental accumulators from the start, because a full
   recompute at E1's cost already fails the NPS band.

## Reproduction (Windows CMD, repository root)

```
set D=C:\Users\epick\Documents\ClaudeShark-data\learned_eval\pilot
set S=benchmarks\current\learned_eval\scripts
set R=benchmarks\current\learned_eval\results
uv run python -m pytest -q %S%\test_sf_label.py %S%\test_features.py %S%\test_evalkit.py
uv run python %S%\build_pool.py --out %D%
uv run python %S%\budget_pilot.py %D% --workers 10
uv run python %S%\sf_label.py %D%\tasks.jsonl %D%\labels_50000.jsonl --nodes 50000 --workers 10 --hash 32
uv run python %S%\train_eval.py %D% %D%\labels_50000.jsonl %R%
uv run python %S%\pairs.py build %D% %D%\labels_50000.jsonl
uv run python %S%\sf_label.py %D%\pairs\pair_tasks.jsonl %D%\pairs\pair_labels.jsonl --nodes 50000 --workers 10 --hash 32
uv run python %S%\pairs.py score %D% %D%\labels_50000.jsonl %R%\e1_weights.json %R%
uv run python %S%\diag_phasek.py %D% %D%\labels_50000.jsonl %R%\diag_phasek
uv run python %S%\pairs.py score %D% %D%\labels_50000.jsonl %R%\diag_phasek\E1c_phaseK_no_material_weights.json %R%\diag_phasek
uv run python %S%\diag_strata.py %D% %D%\labels_50000.jsonl %R%
uv run python %S%\speed.py %D% %R%\e1_weights.json %D%\speed --rounds 2
```

One CPU-heavy step at a time; `speed.py` only on an idle machine.

## Artefacts

* Tracked: `DESIGN.md` (preregistration), this report, `scripts/`, `results/`
  (weights, static and pairwise metrics, post-hoc diagnostics, speed, and
  `results/provenance/`: pool manifest with input hashes, budget decision,
  labeller metadata, SHA-256 of every external data file).
* External, not tracked: `C:\Users\epick\Documents\ClaudeShark-data\learned_eval\pilot\`
  holds the pool (8,991 rows), the 50k-node labels, the budget-run labels, the
  pair tasks and labels, and the scratch speed engines. The hashes are in
  `results/provenance/data_hashes.json`.

## RECORD THIS

1. **The calibration trap, caught.** Show `results/e1_weights.json` material
   rows (queen −300 middlegame, +295 endgame) next to the phase-scale fit
   (K 285 middlegame against 116 endgame), then the post-hoc result that the
   gain survives with no material terms. Command: `uv run python
   benchmarks\current\learned_eval\scripts\diag_phasek.py
   C:\Users\epick\Documents\ClaudeShark-data\learned_eval\pilot
   C:\Users\epick\Documents\ClaudeShark-data\learned_eval\pilot\labels_50000.jsonl
   benchmarks\current\learned_eval\results\diag_phasek`; capture the `K_mg` /
   `K_eg` lines and the two `_vs_E0_phaseK_rel_bce` blocks.
2. **Better overall, worse where it matters.** The stratum table: E1 improves
   unbalanced positions by 18% and is worse on near-balanced ones (E-MSE 0.0178
   → 0.0251), which is where RC-J's real losses start (E 0.35–0.50). Source:
   `results/static_metrics.json`, key `strata`.
3. **A coin flip between Stockfish's move and a master's move.** Best-vs-game
   pairs: E0 48.9%, E1 52.2% with quiescence (table above,
   `results/pairwise_metrics.json`, key `kind_best-game`).
4. **One holdout board.** R94-44w, `8/1r2pk2/p2p4/P2P1p2/P1p3p1/2P3P1/rb1B1PK1/1R1R4 w - - 4 44`:
   RC-J played Bc1 (d2c1); Stockfish's 10M-node move is Rh1 (d1h1). E0's
   quiescence margin is −54 cp against Rh1, E1's +61 cp for it.
5. **The fingerprint check.** RC-J's depth-10 node count over the 24 balanced
   openings reproduced the recorded C15-v2 fingerprint exactly
   (16,818,635) before any E1 measurement.
