# Offline evaluator tuning — audit and tuner design

Date: 2026-09-02. Base: `a832ce7`. **No production value was changed.** Every
candidate below was applied to a scratch copy of the engine for simulation.

The question this session had to answer: does offline tuning of the *existing*
evaluator's parameters have a trustworthy, zero-runtime strength candidate in
it? Short answer: the material values do not — they are already essentially
right — but the fit exposes a **material-versus-position scale** that does
change moves for the better on the calibrated suite. The retained regression's
"−1088 cp queen" is explained and is not a chess value.

Reproduce everything with:

```
uv run python -m tools.tune.features            # cache + equivalence proof
uv run python -m tools.tune.dataset --split     # verification + frozen split
uv run python -m tools.tune.audit               # coefficient explanation, quiet subset, baselines
uv run python -m tools.tune.material            # ridge-regularised material fit
uv run python -m tools.tune.hanging             # hanging_pieces by search depth
uv run python -m tools.tune.simulate --candidate "quiet (tol 30)"
```

Artefacts in `corpus/tune/`: `audit.md`, `material.md`, `material_candidates.json`,
`hanging.md`, `simulate.md`, `simulate_analysis.jsonl`, `scale_diagnostic.txt`,
`leakage_check.txt`, `split.json`. The feature cache (`*.npz`, 0.8 MB) is
derived and not tracked.

## 1. Dataset verification

| | |
|---|---|
| positions | **6,203** (header agrees) |
| oracle | Stockfish 18, 1,000,000 nodes, multipv 2, Threads 1, Hash 256, hash cleared per position |
| binary | outside the repository; SHA-256 `c86215fa1977d53b…` recorded |
| `cp_white == sign·cp_stm` | **6,203 / 6,203** |
| `wdl_white` consistent with `wdl_stm` | **6,203 / 6,203**, none missing |
| cp sign agrees with WDL side (\|cp\| ≥ 15) | 5,118 / 5,118 |
| static (white POV) vs oracle correlation | +0.254 on a 1-in-7 sample — positive, so no perspective bug |
| mate-labelled | 14 |
| invalid FENs | 0 |
| unique FENs | 6,198 / 6,203 (5 duplicates across different games — noted, negligible) |
| source games | 5,318; 1–2 positions each |
| phase | opening 595, middlegame 4,341, endgame 1,267; phase24 ≥ 19: 3,460 |
| material_diff | 0: 3,558; ±1: 1,488; \|≥2\|: 1,157 |
| oracle cp quantiles | p5 −364, p25 −34, p50 +19, p75 +91, p95 +398 |
| \|cp\| > 600 | 107 (18 above 1,000) — the positions the retained clip bites |

**Perspective is consistent everywhere.** A sign error is ruled out as the
source of the suspicious coefficient.

## 2. Exact decomposition

`tools/tune/features.py` splits each position into: white-minus-black counts
of the five piece types; raw PeSTO piece-square sums per type (material value
*not* folded in), including the king; bishop pair; tempo (as +TEMPO for white
to move, −TEMPO for black, in white's POV); and phase. Recombining with the
production constants and the production integer truncation reproduces
`cs_eval.evaluate` **exactly on 6,203 / 6,203 positions**. The build refuses to
write its cache otherwise, and `tests/test_tune.py` re-proves it on random play.

## 3. Why the regression wanted a −1000 cp queen

Same tapered material design matrix, five targets. Coefficients in cp per unit
of (white − black) count, ± standard error. Production queen MG is 1,025.

| variant | queen MG | knight MG | rook MG | queen EG |
|---|---|---|---|---|
| **A** retained: `clip(oracle, ±600) − static` | **−1174 ± 38** | −300 | −380 | +201 |
| B no clipping | −1730 ± 113 | −400 | −632 | +1835 |
| C both sides clipped | −857 ± 38 | −288 | −358 | +259 |
| **F** depth-1 residual, both clipped | **−164 ± 32** | −26 | −50 | +299 |
| C on the quiet subset | −319 ± 75 | −59 | −117 | +565 |

Three stacked causes, in order of size:

**Tactical instability, ~700 cp of it.** Replacing the static score with the
engine's own one-ply quiescence score (variant F) takes the queen coefficient
from −857 to −164. The residual regression was being fitted on positions where
a queen is en prise, mid-exchange, or about to be recaptured: static says
+1,000, Stockfish says roughly 0, and the regression attributes the difference
to "the queen is worth less". Quiescence — which the search already runs —
removes most of it.

**Asymmetric clipping, ~300 cp.** The retained method clipped the oracle at
±600 but not the static score. Shown directly by queen balance:

| queen balance | n | mean static | mean oracle | mean clip(oracle) | mean residual (A) |
|---|---|---|---|---|---|
| white +Q | 90 | +524 | +317 | +197 | **−327** |
| even | 6,038 | +11 | +24 | +23 | +12 |
| black +Q | 75 | −509 | −417 | −163 | **+346** |

Every queen-up position carries a residual of about −330 that has nothing to do
with what a queen is worth. Clipping both sides (C) removes it.

**Selection bias.** Even unclipped, queen-up positions in a pool drawn from
real games score +317 against a static +524: a queen imbalance that persists is
rare in master play, so the ones that appear in a random sample are
disproportionately transient.

The direct fit (`oracle ~ material`, variant D) on the quiet subset also shows
why *any* unconstrained linear fit of MG and EG separately is unreliable here:
queen MG +553 ± 82 against queen EG +1,498 ± 75. With 56% of positions at
phase ≥ 19 the two columns are nearly collinear and the split between them is
poorly determined.

**Verdict on −1088: not a chess value.** It is a measurement of clipping plus
unresolved tactics, and it disappears when either is handled.

## 4. Quiet / stable subset

A position is *quiet* when: no mate score; side to move not in check; the
oracle's best move is not a capture or promotion; and the engine's own
one-ply quiescence moves its static score by at most `tol` cp.

| tol | kept | queen MG (C) |
|---|---|---|
| 0 | 85 | +0 |
| 15 | 2,621 | −264 |
| **30** | **3,801** | **−319** |
| 60 | 4,307 | −289 |
| 100 | 4,525 | −273 |
| none | 6,203 | −857 |

Tolerance 30 is used: it keeps 61% of the pool and the coefficient is stable
from 30 to 100. The subset transforms the baseline — static-vs-oracle MAE
**150 → 86**, correlation **0.27 → 0.73**. The evaluator is much better than its
headline error suggests; the headline is dominated by positions where a static
score is not a meaningful quantity.

## 5. Frozen split

By source game, seed 20260902, stratified on (phase bucket × balanced/imbalanced):
**train 4,340 / val 928 / test 935** positions from 5,318 games. Hash
`e02ceb490f25ebad`, file `corpus/tune/split.json`. `tests/test_tune.py`
asserts no game appears in two parts.

## 6. Baseline error of the current evaluator

Sigmoid scale K fitted on the current evaluator: **185 cp** per logit (low —
the current cp are "over-confident" relative to expected score, because the
fit is dragged by tactical positions).

| subset | n | MAE | median AE | corr | ES-MSE |
|---|---|---|---|---|---|
| train | 4,340 | 150 | 74 | 0.27 | 0.0716 |
| val | 928 | 128 | 66 | 0.47 | 0.0657 |
| test | 935 | 153 | 70 | 0.31 | 0.0667 |
| middlegame | 4,571 | 139 | 67 | 0.19 | 0.0688 |
| endgame | 1,632 | 171 | 97 | 0.50 | 0.0733 |
| balanced | 5,046 | 96 | 59 | 0.29 | 0.0585 |
| imbalanced | 1,157 | **369** | 215 | 0.30 | 0.1203 |
| quiet (tol 30) | 3,801 | 86 | 56 | 0.73 | 0.0513 |

## 7. Material-only fit

Model: production evaluator with the ten material values replaced by
`production + δ`; every PST, the pair and tempo frozen. Target: expected score
from WDL through the sigmoid. Loss: mean squared expected-score error plus a
ridge penalty on δ (scaled so 100 cp costs the same for every piece). Bounds:
[0.6×, 1.5×] of production. Ordering checked, not enforced. λ chosen on
validation; test touched once.

### The λ sweep is flat until zero

| λ | max \|δ\| | val ES-MSE, all | val ES-MSE, quiet |
|---|---|---|---|
| 100 → 0.3 | 0 | 0.06572 → 0.06569 | 0.04959 → 0.04956 |
| 0.03 | 4–5 | −0.3% | −0.6% |
| 0.001 | 38–47 | −2.0% | −2.8% |
| **0** | **410–468 (on the bounds)** | **−4.6%** | **−9.3%** |

Every regularised solution moves the values by less than 50 cp for a gain
under 3%; the rest of the gain requires driving four of ten parameters to a
bound. That is the Pareto shape the brief said to reject on its own.

### The two subsets disagree on direction

| | all positions, λ = 0 | quiet, λ = 0 |
|---|---|---|
| MG | P 80, N **202**, B **219**, R 321, Q **615** | P 121, N **506**, B 530, R 688, Q 1210 |
| EG | P **141**, N 404, B 402, R 674, Q 1253 | P **141**, N **422**, B 407, R 736, Q **1404** |
| on a bound | knight MG, bishop MG, queen MG, pawn EG | knight MG, pawn EG, knight EG, queen EG |

The all-positions fit shrinks middlegame material to the 0.6× floor — the
tactical-contamination direction — and produces implausible chess (rook vs
B+N −100, three pawns beat a knight). The quiet fit grows *everything*, both
phases, toward the 1.5× ceiling.

### It is a scale, not a set of values — RECORD THIS

`corpus/tune/scale_diagnostic.txt`, quiet subset, validation ES-MSE:

| model | parameters | val gain | test gain |
|---|---|---|---|
| 10-parameter fit, λ = 0 | 10 | −9.3% | −5.6% |
| **material × s**, s = 2.00 | 1 | **−13.0%** | −5.4% |
| **whole evaluator × s**, s = 1.94 | 1 | **−12.5%** | — |

A single scalar on the whole evaluator — which **cannot change any move
choice**, since argmax is scale-invariant — beats the ten-parameter fit on the
regression target. The fitted *relative* values are production to within
noise:

| ratio to pawn | production | quiet fit |
|---|---|---|
| MG N / B / R / Q | 4.11 / 4.45 / 5.82 / 12.5 | 4.16 / 4.37 / 5.67 / 9.96 |
| EG N / B / R / Q | 2.99 / 3.16 / 5.45 / 9.96 | 2.99 / 2.89 / 5.22 / 9.96 |

Only the middlegame queen moves relative to the others (12.5 → 10 pawns).
Everything else the regression "wanted" was K being wrong for quiet positions.

**Conclusion for material tuning:** the piece values do not have trustworthy
headroom. The regression signal is a global scale.

### Plausibility of the quiet candidate

| balance | production | candidate |
|---|---|---|
| Q vs 2R (MG / EG) | +71 / −88 | **−167** / −67 |
| Q vs R+B (MG) | +183 | −9 |
| R vs B+N (MG / EG) | −225 / −66 | **−347** / −93 |
| 3P vs N (MG / EG) | −91 / +1 | **−141** / +2 |
| exchange R−B (MG / EG) | +112 / +215 | +158 / +329 |

Ordering Q > R > minor > P holds in both phases. The queen is relatively
cheaper and the exchange relatively dearer than production; neither is
pathological, both are movements a stronger engine would recognise.

## 8. Move-quality simulation — RECORD THIS

The quiet candidate — MG `121, 506, 530, 688, 1210`, EG `141, 422, 407, 736,
1404` — applied to a scratch copy, on `corpus/competition_like_v1.jsonl` at
depth 6, judged by Stockfish 18 at 1M nodes per child.

| metric | current | candidate | Δ |
|---|---|---|---|
| best-move agreement | 37.1% | 37.9% | +0.8 |
| within 25 cp | 65.8% | **67.9%** | +2.1 |
| within 50 cp | 77.1% | 77.5% | +0.4 |
| robust mean loss | 35.3 | **30.8** | **−4.5 (−13%)** |
| serious (≥100 cp) | 10.0% | **8.8%** | −1.3 |
| catastrophic (≥300 cp) | 1.7% | **0.8%** | −0.8 |

53 of 240 moves changed: **27 better by more than 10 cp, 18 worse, 8 neutral.**
Runtime: **0.993** (218,173 vs 219,774 evals/s — identical, as a constant
change must be).

This is the opposite of what the brief anticipated ("regression score
improving but move quality not"): here regression improvement *did* translate.
It is also better on every metric than the king-safety term that was rejected
last session, at zero cost rather than −11.6% NPS.

**The seven persistent evaluation failures:** one fixed — `cl-097`, 334 → 22
cp (`c1b3` → `e7c7`; oracle `g2g4`). The other six play the identical move.

### Leakage check

All 240 suite positions are in the labelled pool; **172 are in the train
split**. Two controls:

* **Refit with every suite game excluded from training:** max change to any
  value is 33 cp (queen MG 1210 → 1243); all others within 3 cp. The fit is not
  driven by the suite.
* **External-only view** — the 68 suite positions whose games are in val/test:
  robust loss **31.6 → 25.8**, serious 8.8% → 7.4%, catastrophic **1.5% →
  0.0%**, agreement 41.2% → 39.7%. Direction holds; n is small and agreement
  dipped slightly.

### What is actually being measured

Given §7, the mechanism is almost certainly the **material-versus-position
scale**, not the piece ratios: material is scaled ~1.45× relative to the
PeSTO tables, pair and tempo, which makes the engine less willing to trade
material for table gains. PeSTO's positional values are large (the knight table
spans −167 to +129, a third of a knight), and this evidence says they are too
large *relative* to material for this engine. The candidate reaches that
correction indirectly and stops at the bounds.

## 9. `hanging_pieces` is a search signal, not an evaluation feature — RECORD THIS

`corpus/tune/hanging.md`. Full 56-feature residual regression, the
`hanging_pieces` row, by engine depth:

| engine score | hanging MG cp ± se | hanging EG cp ± se | drop-one ΔR² |
|---|---|---|---|
| static | −40 ± 8.5 | −138 ± 15 | **0.0245** |
| depth 1 (quiescence) | +11 ± 7 (n.s.) | −57 ± 13 | 0.0031 |
| depth 3 | +4 ± 7 (n.s.) | −48 ± 12 | 0.0029 |

Explanatory power falls **8×** after one ply of quiescence and the middlegame
coefficient changes sign to insignificant. On positions with a hanging piece,
mean \|oracle − static\| is 222 cp; \|oracle − depth 1\| is 115. The search
already resolves most of it. Adding the term to static evaluation would count
those tactics twice. **Do not implement it in evaluation.** What remains at
depth 3 (EG −48, ΔR² 0.003) is small.

## 10. PST tuning — design only

**Not recommended next**, for three reasons that all come from this session's
numbers.

* The only strong signal found is a single scale between material and the
  tables. That is one parameter, not 768.
* PeSTO was tuned on far more data than 3,801 quiet positions. Twelve 64-entry
  tables against 2,668 training positions is ~3.5 samples per parameter; any
  unregularised fit will memorise.
* The regression's MG/EG collinearity (§3, variant D) gets worse, not better,
  with more parameters.

If it is attempted later, the defensible design is: fit **deltas from PeSTO**
with a strong ridge toward zero; impose left-right symmetry (halving the
parameters); add a smoothness penalty between neighbouring squares; use a
low-dimensional basis first (per-piece centralisation, rank advancement, file
edge — six to ten parameters per piece) and only graduate to per-square deltas
if the basis shows held-out gain; select λ by game-grouped cross-validation;
and gate on the 240-position move-quality suite exactly as above. Expect the
honest outcome to be "PeSTO plus a scale".

## 11. Learned evaluator — assessment, no implementation

| | tapered linear (this path) | tiny learned evaluator |
|---|---|---|
| remaining headroom | material: ~none; material/PST scale: real but one knob; PST: probably small | unknown; the residual R² after all 56 hand features is 0.32–0.39, so most of the oracle's signal is *not linear in these features* |
| runtime | zero | a 256→32→1 net on ~800 binary inputs is ~10–30 µs in numpy per position — 3–8× the current evaluator; ONNX Runtime brings it toward 5–10 µs; incremental accumulators are what make NNUE cheap and are a large project |
| 60 s init | not needed | exactly what it is for: model load, ONNX session, warm-up |
| risk | low | high: training pipeline, quantisation, and a search that expects 60k+ evals/s |
| interpretability | full | none |
| release | source constants | weights file inside 50 MB, model trained by us — permitted |

The linear path has one more cheap, high-evidence step (the scale). After
that its headroom is small: the residual regression's own ceiling with every
hand feature is R² ≈ 0.4, and the quiet-subset correlation of 0.73 means the
evaluator is already capturing what a linear model of these features can. A
learned evaluator becomes justified **after** the scale experiment, not
instead of it — and only with the 60 s init budget and an incremental-update
design, or it will cost more in nodes than it returns in accuracy.

## 12. Recommended next implementation

Exactly one frozen candidate, for Claude to implement flag-gated and arena:

**`v0.6-material-scale` — the simulated quiet candidate, verbatim:**
MG `(0, 121, 506, 530, 688, 1210, 0)`, EG `(0, 141, 422, 407, 736, 1404, 0)`.

Two controls alongside it, because the mechanism matters for what comes next:

1. **A one-parameter material scale** `s ≈ 1.45` applied to production values
   (P 119, N 489, B 529, R 692, Q 1486 MG; EG likewise) — if it matches the
   candidate on the 240-suite, the whole gain is the scale and the piece ratios
   should stay at PeSTO's.
2. **The bounds widened** to [0.5×, 2.0×] and refit — to see whether the
   deterministic gain keeps growing or the fit has found its level.

Gate as always: 240-suite move quality first, then ~200 games against
`champions/v0_5_2_correctness` with the repaired arena.

## RECORD THIS

1. **−1174 → −164.** The queen coefficient under the retained method vs. after
   the engine's own quiescence. Show the variant table and the queen-balance
   clipping demo.
2. **All-positions vs quiet: opposite directions.** MG shrinks to 0.6× on all
   positions, grows to 1.5× on quiet ones.
3. **A decision-invariant rescale beats the 10-parameter fit** on the
   regression target (−12.5% vs −9.3%). The "tuning gain" is mostly K.
4. **Regression gain translated to move quality this time** — robust loss
   35.3 → 30.8, catastrophic 1.7% → 0.8%, runtime 0.993 — and survives a
   leakage check on the external subset.
5. **`hanging_pieces` collapses 8× after one ply of quiescence.** A search
   signal wearing an evaluation feature's name.
