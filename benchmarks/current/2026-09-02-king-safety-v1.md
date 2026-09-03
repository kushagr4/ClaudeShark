# King safety v1 — measured, rejected

Date: 2026-09-02. Base: `27e7f8c` (`champions/v0_5_2_correctness`).
**Verdict: REVERT.** The feature ships present but flag-gated OFF.

## Why it was tried

The structural analysis put king safety at the top of the evaluation
weakness list. Reproduced independently before implementing anything:

| claim | verdict |
|---|---|
| 24 serious errors at depth 6; 12 search_depth, 7 evaluation | **confirmed exactly** |
| king structures have the worst error rates | **confirmed** — `unusual_king_placement` 26.7% (2.67x baseline), `exposed_king` 20.4% (2.04x), the two highest of any tag |
| "5 of 7 evaluation errors are material grabs with an exposed king" | **partly** — 5 of 7 carry a king tag, but only **3 of 7 are captures**, and the flagship cl-170 plays `Qh3-e6` into an **empty square**, so it is not a pawn grab |
| seed weights ~24 cp open files, ~16 cp per attacker | **not supported by the retained regression**, which gives `king_open_files` −9.3 cp at \|t\|=1.6 (below its own "well determined" threshold) and `king_zone_attackers` −11.6 cp, with drop-one dR² of 0.0003 and 0.0014 against `hanging_pieces` at 0.0205 |

So the *diagnostic* evidence supported the feature and the *regression* evidence
was weak. Weights were seeded at or below the regression magnitudes rather than
above them.

## What was built

`cs_king.py`, four concepts, middlegame only, endgame zero by construction:

| term | weight |
|---|---|
| open file at the king (enemy rook/queen present) | 12 cp |
| semi-open file, same gating | 6 cp |
| piece attacking the king ring | 8 cp each, capped at 6 |
| enemy pawn bearing on the ring | 6 cp each, capped at 3 |
| friendly shelter pawn | −4 cp each, capped at 3 |

Two things were found while building it.

**Pawns were missing from the attacker count.** On cl-170 a piece-only count
scored both kings at exactly 16 and cancelled to zero — while the actual danger
was black's pawns on g3 and h4 beside the white king. Pawns are attackers; that
was a hole in the definition, not a simplification.

**A queen was double-counted.** The fast path counted her once on the diagonal
loop and once on the rank/file loop. Caught by an equivalence test against a
deliberately slow reference implementation: 92 mismatches over 1200 random
positions. Attackers now accumulate as a bitboard.

## Cost

| | evals/s | µs/eval |
|---|---|---|
| baseline | 276,767 | 3.61 |
| first implementation | 103,078 | 9.70 |
| **after zone pre-filtering** | **149,949** | **6.67** |

The first version cost −62% of evaluator throughput because every enemy slider
meant a dictionary lookup keyed on a large integer. Pre-filtering candidates
with a precomputed "could this piece reach the ring on an empty board" mask cut
that to +3.06 µs, slightly cheaper than the +3.8 µs reference it was asked to
beat. Search cost: **62,051 → 54,861 NPS, −11.6%**.

## The gate

240 calibrated positions, fixed depth 6, judged by Stockfish 18 at 1M nodes per
child.

| metric | off | on | |
|---|---|---|---|
| best-move agreement | 37% | 37% | — |
| within 25 cp | 66% | 65% | worse |
| median loss | 2 | 0 | better |
| robust mean loss | 35.3 | 35.5 | worse |
| serious (>=100 cp) | 10.0% | 10.4% | worse |
| catastrophic (>=300 cp) | 1.7% | 1.7% | — |

49 positions changed move: **19 improved, 20 worsened, 10 neutral.** Total
winsorised loss 8465 → 8522 (+57).

**Targeted set: 0 of 7 persistent evaluation errors fixed.** All seven play the
identical move.

```
cl-170  484 -> 484   h3e6 -> h3e6   oracle b2c3
cl-097  334 -> 334   c1b3 -> c1b3   oracle g2g4
cl-125  225 -> 225   c4e3 -> c4e3   oracle c4a3
cl-144  204 -> 204   c4e4 -> c4e4   oracle c4e2
cl-202  195 -> 195   e3a7 -> e3a7   oracle e2d4
cl-094  175 -> 175   b5h5 -> b5h5   oracle b5b4
cl-198  165 -> 165   a2a1 -> a2a1   oracle b8a7
```

Tactics 16/16 both ways; verifier clean.

## The finding worth keeping

| subset | n | robust loss off → on | serious off → on |
|---|---|---|---|
| **exposed_king** | 54 | 57.9 → **48.1** | 20.4% → **14.8%** |
| king-tagged (any) | 108 | 46.5 → 43.4 | 13.9% → 13.0% |
| **NOT king-tagged** | 132 | 26.1 → **29.1** | 6.8% → **8.3%** |

The term does what it was designed to do on the subset it was designed for, and
hurts everything else by about the same amount. That is what a uniformly applied
penalty does: every middlegame position has two kings, so it perturbs positions
where king safety was never the issue.

Both movements are small — three positions here, two there — so neither is
established on its own. The *pattern* is the useful output.

## Why not just raise the weights

Because the same lever does both things. cl-170 needs the term to move a 484 cp
decision; it currently contributes 18 cp in the right direction. Scaling it by
the factor needed there would multiply the damage across the 132 non-king
positions, where the term is already net negative.

## What a v2 would need

Not a retuning of these constants. A different shape:

* **fire selectively** — apply only where an attack actually exists (say, two or
  more attackers, or an open file *with* a heavy piece already on it), so quiet
  positions are untouched;
* **be non-linear** — real engines use an attack-weight table that stays near
  zero for one or two attackers and rises steeply after, which is exactly the
  "small everywhere / large when it matters" profile this version lacks;
* **be judged on the exposed_king subset separately**, since that is where the
  signal is, with the non-king subset as the regression guard.

## Decision

**REVERT.** `CS_EVAL_KING_SAFETY` defaults to `0`. Depth-6 node count with the
flag off is 1,712,405, identical to `champions/v0_5_2_correctness`, so
production play is unchanged. No arena was run: the brief's gate requires
overall move quality to improve and serious errors to fall, and neither did.

The code, its tests and this record stay because the structural split is a real
lead for a v2, and re-deriving it would cost another session.
