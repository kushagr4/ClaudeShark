# LMR schedule variants: node counts at depth 8 and an equal-time move-quality screen

**Date:** 2026-09-05 (Mac). **Base:** working tree with the staged picker on
(`CS_STAGED_MOVES=1`) and the fast stalemate probe. **Knobs:** `CS_LMR_START`,
`CS_LMR_R2_INDEX/DEPTH`, `CS_LMR_R3_INDEX/DEPTH` (shipped 3, 6/6, off), added
in `6d25ab4` with fingerprints unchanged.

## Depth 8, first 12 suite positions (deterministic)

| variant | nodes | vs base | root moves changed |
|---|---|---|---|
| base (r=1 from index 3 at depth ≥3, r=2 from index 6 at depth ≥6) | 5,584,868 | — | — |
| r=2 from depth ≥4 (`CS_LMR_R2_DEPTH=4`) | 3,450,509 | **−38%** | 3 / 12 |
| r=2 from index 4 at depth ≥4 | 3,218,983 | −42% | 2 / 12 |
| r=3 from index 12 at depth ≥7 | 5,572,604 | −0.2% | 0 / 12 |
| start at index 2 | 5,654,117 | +1.2% | 1 / 12 |

Only the earlier second ply of reduction does anything; a third ply of
reduction almost never triggers and reducing one move earlier costs nodes.

## Equal-time screen, 80 blunder positions, 3,000 ms per move

Suite `corpus/daily/search_audit_positions.jsonl` (the 2026-09-04 search-audit
sample: positions where the mover lost ≥ 200 cp, stratified from four
annotated 200-game corpora). `tools.corpus.analyse --ms 3000 --workers 1`,
Stockfish 18 at 1M nodes per child. **Caveat:** both runs were made while the
C1 timed screen occupied 8 of 10 cores; the load was steady across the two
runs but the absolute depths are lower than a quiet machine would give.

| | base | r=2 from depth ≥4 |
|---|---|---|
| mean depth reached | 8.99 | 9.35 (+0.36 ply) |
| mean nodes | 129,726 | 143,354 |
| agree with the oracle | 40% | 38% |
| within 25 cp | 50% | 50% |
| robust mean loss (winsorised 500) | 152 | 150 |
| ≥ 100 cp / ≥ 300 cp | 45% / 23.8% | 46% / 23.8% |
| expected-score loss, sum over 80 | 14.59 | 15.58 |
| moves changed | — | 15 |
| variant better / worse by ≥ 50 cp | — | 5 / 5 |
| mean paired winsorised gain | — | +1.8 cp |

Raw: `corpus/daily/lmr/sa80_base_3000ms.{jsonl,md}`, `sa80_r2d4_3000ms.{jsonl,md}`,
`sa80_screen.log`.

## Decision

The extra third of a ply the earlier reduction buys is spent exactly as the
2026-09-04 ablation predicted: reduced search of the moves it now reduces.
Five positions improve, five get worse, the expected-score loss is slightly
higher. Under the rule that a change must beat the current best before it is
stacked, this does not earn a timed match. The LMR lane stays closed unless a
new mechanism (a check extension) changes what the reductions are applied to.
No default was changed.
