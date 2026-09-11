# N1 learned evaluation (100K): preregistration

Date: 2026-09-11. Engine: RC-J (runtime files byte-identical to `2bf6885`).
The user approved this stage after the linear pilot (`REPORT.md`) with twenty
hard requirements, which this document implements. Scope limits:
* 100K positions only; no 500K, N2 or N3;
* `START_FRACTION` stays 0.45;
* no search change, no search-state work, no arena;
* `main` only, zero tags, no push.

Stop and report at the end.

**Provenance, disclosed.** The first draft was reviewed adversarially by three
independent read-only reviewers (holdout discipline, statistics, engineering)
and revised before any validation or test label existed. The pool was built
from the draft's parameters before this file was committed. The train
labelling job (50k nodes, train positions only) was started before the commit;
no label of any split had been read when this version was committed. Labels
are valid only for the pool hash below.

## 1. Question

Does a small NNUE-style network trained on 100K Stockfish-labelled positions,
added to RC-J's evaluator, judge near-balanced positions better than RC-J's
evaluator does, at a search-speed cost the engine can afford? "Better" is
tested three ways:
* after calibration (including a richer calibration family);
* against a shrink-toward-a-draw control;
* after RC-J's own quiescence resolution.

## 2. Data

`scripts/build_pool.py --seed N1-20260911 --twic-min-elo 2200 --twic-per-game 4
--twic-games 26000 --per-game PUBLIC=8,VS_SF=6,SELFPLAY=6 --target 100000`

* **Pool:** `pool.jsonl` SHA-256
  `f016e26af726e46c57dbdfc698eb9b12845a15dd337feb5a3532948c04099560`: 100,000
  positions from 25,823 games. The TWIC 2200 floor was sufficient: 24,298
  eligible, 23,772 used.
* **Sources and exclusions:** as in the pilot (`DESIGN.md` §3). Split by group:
  `sha1("N1-20260911|" + group) mod 10`, 0-7 train, 8 validation, 9 test.
  Leakage on UUIDs, positions, start families, move sequences and cross-split
  groups: zero.
* **Near-duplicate rule** (`scripts/pool_audit_n1.py`, run before any
  validation or test label existed): a validation or test position one piece
  displacement from any train position is dropped from evaluation. Such a
  position has the same placement once one piece of the same colour and type is
  removed from each, with side to move ignored. 241 were dropped (226 at
  ply <= 30).
* **Final sizes:**

  | split | positions | sorted-pid SHA-256 |
  |---|---|---|
  | train | 79,673 | `22a5a174a47ebaabafd4a266b6b42fdfb31ee9fdd0ea98c02347ef6819cf07f5` |
  | validation | 9,870 | `917c2011dcde6cc55a3c9dfb9a569c58bac447dbbcf1397c72b8604bbcfe2e30` |
  | test | 10,216 | `c9b29de50759c7cde74df4df56aaa72d46624041d5f69cad9cfd122c3766b397` |

* **Sealed test:** the test tasks, labels and pairs live under
  `n1/test_sealed/`. Nothing test-derived enters a directory read by training
  or selection.
* **Pilot overlap** (`pool_audit.json`, report only):
  * validation includes 142 pilot-validation groups and 280 pilot-test groups;
  * test includes 166 pilot-validation groups and 205 pilot-test groups;
  * about 100 positions are identical to pilot positions.

  The gates are also reported on the subset that excludes every group the pilot
  saw in its validation or test split (§9 sensitivity). No N1 script reads
  pilot labels.
* **RC-J holdout:** the 19 confirmed serious-error positions and everything
  from the 30 R76-R105 games are excluded from every split. Nothing reads them
  before §12.

## 3. Labels

Stockfish 18 (SHA-256 `c86215fa…9118911`), one thread, Hash 32 MB,
`UCI_ShowWDL`, `ucinewgame` per position, fixed nodes, last exact info line.

* **Train:** 50,000 nodes, train positions only. `train_n1.py` asserts the
  file holds no validation or test pid. Validation and test are never
  labelled at 50k, apart from the 300-position noise subset below.
* **Validation:** 1,000,000 nodes.
* **Test:** 1,000,000 nodes, labelled only after the freeze manifest (§8)
  exists, into `test_sealed/`.
* **Noise subset:** 300 seeded validation positions, labelled at 50k and at 4M
  as well as their 1M validation labels. Reported: mean |dE|, WDL-category
  agreement, best-move agreement, band-membership agreement across
  50k/1M/4M, and the signed mean E shift from 50k to 1M, overall and within the
  band. A signed shift above 0.01 is reported as a calibration caveat on G1/G2.
  Nothing about the noise subset can change a verdict, a threshold or the U/B
  choice.
* **Move-ranking pairs:**
  * roots: 1,200 validation roots (before training) and 5,000 test roots (after
    the freeze, sealed);
  * candidates: the 1M-node best move, the game move if different, and one
    seeded random legal move, each scored by a root-restricted 1M-node search
    from the same root;
  * a pair counts when |dE| >= 0.05 or |dcp| >= 30 (cp clipped to ±1500, mate
    saturating).

Target: E = (W + D/2)/1000 for the side to move. "Quiet" means the label's best
move is not a capture or promotion. The band is |E − 0.5| < 0.10 on the
split's own label.

## 4. Calibration (fixed before any model is judged)

* **(a) Frozen phase link** `p = sigmoid(eval · (m / K_mg + (1 − m) / K_eg))`,
  `m = phase / 24`. It is fitted once for E0 on train ∩ quiet, then frozen. It
  is the N1 training link and the primary comparison link, so the pilot's
  calibration gain sits inside the baseline.
* **(b) Rich link family:** a separate scale for each phase band (>= 16, 8-15,
  < 8) × pawn-count bucket (<= 8, 9-12, >= 13), nine scales in all. It is
  fitted on validation ∩ quiet separately for E0 and for N1q before the test
  opens. G1 and G2(i) must pass under (a) and also with both models in (b). The
  share of N1's gain that (b) removes is reported.
* Diagnostics only: each model's own phase link refitted on train ∩ quiet, and
  E0 × 1.5 refitted, which must reproduce E0. No diagnostic can change a
  verdict.

## 5. Model N1 (the only architecture trained)

    N1_stm = E0_stm + f(position)      (a residual on RC-J's own evaluation)
    features   768 per perspective: (own 0 / opponent 384) + (piece type − 1) · 64 + square,
               squares flipped vertically for Black's perspective
    accumulator  A_p = b1 + Σ W1[idx]          128 units, weights shared by both perspectives
    h1 = [CReLU(A_stm), CReLU(A_opp)]          256, clipped to [0, 1]
    h2 = CReLU(W2 · h1 + b2)                   32
    f  = 100 · (w3 · h2 + b3)                  centipawns, side to move

Parameters: 106,689. The network is colour-symmetric by construction. A king
move is an ordinary feature update. The output layer starts at zero, so the
untrained network equals E0.

## 6. Training (float32, CPU, deterministic, seed 20260911)

* **Loss:** binary cross-entropy of the frozen link (a) of `E0 + f` against E.
* **Optimiser:** Adam, learning rate 1e-3, batch 1,024, no weight decay, at
  most 60 epochs; W2 is clamped to ±127/64 after every step.
* **Early stopping:** lowest validation quiet BCE (unweighted, link (a)),
  patience 6.
* **Runs:** U weights every train position 1. B weights positions with
  |E − 0.5| < 0.10 (train label) 2 and the rest 1, normalised to mean 1.

## 7. Selection on validation (test and holdout closed)

For each run, on the validation quiet subset (link (a)) and all validation
pairs, a run is **eligible** if it passes the validation versions of the gates:
* band E-MSE below E0's;
* band E-MSE below the shrinkage control's (§9 G2(ii));
* band Spearman above E0's;
* band magnitude ratio in [0.8, 1.25];
* band BCE change <= 0;
* 0.10-0.30 band BCE change <= +1%;
* quiescence-resolved pair accuracy above E0's.

All are point estimates.

* If both runs are eligible, choose B only if its band E-MSE is lower than U's
  by more than one paired-bootstrap standard error (validation groups);
  otherwise U.
* If only one is eligible, choose it.
* If neither is eligible, freeze U, carry on, and attach **VALIDATION FAIL** to
  the verdict.

## 8. Freeze, quantisation and pre-test acceptance

After selection:

1. **Quantise.** Layer 1 is int16 `round(W1·255)` with an int32 accumulator
   and CReLU clip [0, 255]. Layer 2 is int8 `round(W2·64)` with an int32 bias
   `round(b2·255·64)` and `h2 = clip(z // 64, 0, 255)`. The output is int32
   `round(w3·64)`, `round(b3·255·64)` and `f = trunc(100·out / 16320)`. Clip
   counts per layer are reported. These constants are frozen, and float results
   never substitute for N1q in any gate.
2. **N1q acceptance** (validation only):
   * balanced-band E-MSE of N1q within 2% (relative) of float;
   * maximum |cp| difference from float <= 10;
   * quiescence-resolved pair agreement with float >= 99%.

   On failure: stop and report; the test is never opened.
3. **Magnitude audit** (§10). Every criterion must hold before the test
   opens. Any failure means MAGNITUDE-INCOMPATIBLE: the verdict is REJECTED,
   §11 is not run, and f is never rescaled or clamped and no margin changes.
4. **Rich-link fits** (§4b) for E0 and N1q on validation.
5. **Freeze manifest** (`results/n1/freeze.json`): weights SHA-256, the chosen
   run, the calibrations, acceptance, audit, the rich links and timestamps.
   Every later step checks it.

**After any test label or test pair label is read**, there is no retraining,
reselection, re-quantisation, link refit, weight edit or change to any gate
threshold. A failure is recorded as FAIL and the stage stops for review.

Steps that read test data, in order, each requiring the freeze manifest:
1. test labelling;
2. building and labelling the test pairs;
3. `gates_n1.py`;
4. the regression corpus (§11).

## 9. Test gates

Unit: N1q against E0, test split, 1M labels. Bootstrap: 1,000 paired
resamples of test groups (the same draws for both models), seed 20260911,
percentile 2.5/97.5; relative BCE is the ratio of resampled means.

* **G1 aggregate (quiet):** the relative BCE change has its 95% interval
  entirely below zero under link (a), and also with both models in link (b).
* **G2 balanced, PRIMARY** (band, quiet):
  * (i) E-MSE difference (N1q − E0) has its 95% interval entirely below zero
    under (a), and also under (b);
  * (ii) shrinkage control. s* ∈ {0.5, 0.6, …, 1.0} minimises the train ∩ quiet
    band E-MSE of E0·s under (a). The N1q − E0·s* band E-MSE difference has its
    95% interval entirely below zero;
  * (iii) within-band discrimination. The difference in Spearman correlation
    with Stockfish cp (clipped to ±300), N1q minus E0, has its 95% interval
    entirely above zero;
  * (iv) median |N1q| / median |E0| on the band lies in [0.8, 1.25];
  * (v) the band BCE change is <= 0 and the 0.10-0.30 band BCE change is
    <= +1% (points).
* **G3 after RC-J quiescence resolution:**
  * (i) on all test pairs, the quiescence-resolved accuracy difference has its
    95% interval entirely above zero. If the interval contains both 0 and +2.0
    points, G3 is **UNDERPOWERED/UNKNOWN**: not passed, and nothing is
    relabelled or rerun;
  * (ii) on pairs with a balanced root, the lower 95% bound of the difference
    is >= −1.0 point (non-inferiority);
  * (iii) the quiescence-resolved root score, `qsearch(root, −INF, INF)` on
    band quiet positions, has an E-MSE difference with its 95% interval
    entirely below zero under (a).
* **G4 non-quiet:** BCE on non-quiet test positions (a), N1q relative to E0
  <= +1% (point).

**Static PASS = G1 ∧ G2 ∧ G3 ∧ G4.**

Sensitivity flags, not gates:
* G1 and G2(i) on the TWIC-only subset (one cluster per game); a fail is
  flagged "cluster-driven";
* G1-G3 on the subset excluding groups the pilot saw in validation or test;
* group counts per family.

## 10. Runtime

* **Incremental inference only.** A scratch copy of RC-J (`engine_n1.py`,
  never the repository's runtime files) threads `NNA` (int32, STACK+1 × 256,
  the last row scratch) and `NNK` (int64, STACK) through `search_root`,
  `negamax` and `quiescence` into `evaluate`. `make_move` records the moved
  piece in the unused `U[ply, 7]`. `evaluate` works lazily:
  * it finds the nearest ply whose stored key equals that ply's position key
    (`U[j, 4]`, or `S[4]` at the current ply);
  * it applies each later move's feature deltas (move, capture, en passant,
    castling rook, promotion; a null move is a copy);
  * with no valid ancestor, it rebuilds from the bitboards.

  Legality probes cost nothing.
* **Root seeding.** Search never evaluates at ply 0, so at the start of every
  root search `search_root` rebuilds row 0 and validates its key. Every
  catch-up then ends at a valid row, and search never rebuilds from the
  bitboards otherwise. Counters (evaluate calls, rebuilds, catch-up steps,
  root seeds) are reported, with the preregistered expectation that
  rebuilds == root seeds.
* **Correctness:**
  * At least 5,000 random legal transitions, run once with random weights and
    once with the frozen weights. Captures, castling (all four), en passant,
    promotions (including underpromotions), king moves, null moves and unmakes
    are all forced. The incremental accumulator must equal a rebuild exactly,
    and the compiled correction must equal the numpy forward pass exactly.
  * A **shadow-verify build** (frozen weights, the value not added) compares
    the incremental row with a rebuild at every evaluation inside real search:
    depth 10 and 1,000 ms on the 24 openings, and a 40-move self-play sequence
    without `new_game`. It requires zero mismatches and RC-J's exact node
    count at depth 10.
* **Plumbing control:** with zero weights, the depth-10 node count must be
  16,818,635 with the same moves as RC-J. It is re-run after the root-seeding
  change.
* **Speed.** The implementation is frozen, with its file hash recorded, after
  the correctness tests and before the first speed run. Only bit-exact
  optimisations are allowed before that freeze, and every run is reported
  (no best-of). Idle machine. Two blocks:
  * **Shadow cost** (frozen weights, value computed and stored, not added):
    identical tree to RC-J, so the depth-10 NPS ratio is the per-node cost.
  * **Real N1q** at 1,000 ms per position.

  Each block runs 5 ABBA rounds (RC-J / candidate, each run its own process) on
  the 24 balanced openings. A null control of RC-J against a second RC-J
  process must stay within ±2% (median per-round ratio); otherwise the block is
  void and rerun once. The **NPS cost** is taken from the pessimistic end
  (minimum) of the per-round ratios, worse of the two blocks; the median is
  reported. Completed depth excludes partial iterations (an iteration stopped
  after a committed root move counts as partial). Researches and unstable
  iterations are reported for both engines, as are the compile and warm-up
  seconds of the trained build next to RC-J's.

  Each band requires the stated evidence:

  | NPS cost | verdict |
  |---|---|
  | <= 10% | static PASS and §11 pass |
  | 10-15% | additionally the G3(i) lower bound >= +1.0 point, the §11 >= 100 cp bucket with net improvement at one-sided binomial p < 0.10, and a completed-depth loss at 1,000 ms <= 0.5 ply |
  | 15-20% | additionally the G3(i) lower bound >= +2.0 points and the balanced-root lower bound > 0 |
  | > 20% | rejected in this stage (no §11 run; a redesign needs new approval) |
  | > 30% | automatic rejection |

  The holdout never supplies this evidence.
* **Magnitude audit** (`scripts/audit_n1.py`, before the test opens). The
  consumers are:
  * reverse futility (120·depth);
  * stand-pat and delta pruning (200 + piece value);
  * aspiration (30 → 800);
  * the 16-bit TT field;
  * the `MATE_BOUND` guards;
  * the draw score and the root drawing rule;
  * mop-up;
  * the 50 cp instability counter.

  Criteria, all required:
  * an audit build samples every 4,096th evaluate call's position during
    depth-10 searches of the 24 openings and depth-8 searches of 300 validation
    roots; the p99 of |f| at those call sites is <= 250 cp in every phase band
    (mean, sd, p1, p99 and max are reported). A band with no sampled call site
    fails the criterion.

    **Disclosed deviation** (before the test opened, and before any audit
    result was judged): the stride was 64. The 20,000-row sample buffer then
    filled within the first few openings, after about 1.3M of the 58M calls,
    so it held no endgame call site at all. The first audit run crashed on
    that empty band. The stride was raised so the fixed buffer spans every
    search; the criterion itself is unchanged.
  * the mean of f on the validation balanced band has |mean| <= 10 cp;
  * the slope of N1q on E0 over validation positions lies in [0.8, 1.25] per
    phase band;
  * N1q's own phase link refitted on train ∩ quiet has K_mg and K_eg within
    ±10% of the frozen link;
  * the analytic bound of f over all inputs, `[trunc(100(b3q + 255 Σ min(0, w3q)) / 16320),
    trunc(100(b3q + 255 Σ max(0, w3q)) / 16320)]`, has max |f| <= 3,000 cp;
    no W1 parameter is clipped in quantisation;
  * on 20 seeded bare-king positions (10 KQK, 10 KRK) played out by each
    engine against itself at 200 ms per move (at most 100 plies), N1 mates
    every position RC-J mates, using at most RC-J's plies + 10.

## 11. Regression corpus (only after static PASS and a magnitude-audit pass)

* **Corpus:** 800 seeded test positions (labelled test positions), stated to
  be the regression corpus.
* **Replay:** on an idle machine, RC-J and N1 each in their own process,
  alternated. Primary is `fixed_budget_ms = 1000` with a fresh table; fixed
  depth 8 is a deterministic secondary.
* **Scoring:** where the moves differ, both are scored by a root-restricted
  1M-node search from the same root. N1's move is improved if dE >= +0.05 and
  worsened if dE <= −0.05. The cp buckets use Stockfish's cp of N1's move minus
  RC-J's (±1500 clip): >= 50, >= 100, >= 300.
* **Pass:** improved >= worsened, and the one-sided binomial p for
  "worsened > improved" >= 0.10, in the dE bucket and the >= 100 cp bucket.
  The >= 300 cp bucket is report-only when it has fewer than 10 items. The
  same rule is also applied to balanced roots on their own.

## 12. RC-J real-loss holdout (last; descriptive only)

`holdout_n1.py` refuses to run unless the freeze manifest, the test-gate,
magnitude-audit, speed and (when run) regression-corpus result files exist,
and it records their hashes. The pilot's `pairs.py score`, which prints
holdout rows, is not used anywhere in N1.
* For the 14 first decisive errors and the 19 confirmed serious errors:
  static and quiescence-resolved pairwise for E0 and N1q.
* Cold replays of the §10 N1q scratch engine and of RC-J, at the recorded
  clock and at the autopsy's timed depth. New moves are classified by a
  root-restricted 10M-node search against `verify*.json` (GOOD <= 30 cp,
  BAD >= 40 cp).
* Reported: repaired, worsened, result flips, and the >= 100 and >= 300 cp
  buckets.

The holdout can neither promote nor rescue; a holdout regression is a flag. No
retraining or reselection follows.

## 13. Verdict (frozen)

* **N1 REJECTED:** static FAIL (other than the underpowered case below), a
  magnitude-audit fail, an N1q acceptance fail, or NPS cost > 20%.
* **N1 UNKNOWN / UNDERPOWERED:** every other static gate passes and G3(i) is
  underpowered.
* **N1 STATIC-ONLY:** static PASS, but the speed band's evidence or the §11
  pass is missing.
* **N1 CANDIDATE PENDING APPROVAL:** static PASS, audit pass, §11 pass, and
  the speed band's evidence.
* **VALIDATION FAIL** is attached when §7 found no eligible run.

In every case: stop and report. No 500K, N2, N3, arena or search-state work
follows automatically.
