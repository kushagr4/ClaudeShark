# C15-v2 pre-registration

Frozen 2026-09-08 before any candidate code was measured. Baseline RC-I
(`6c104cb`). Every set below is taken unchanged from the C15 attempt so the two
implementations are judged on the same positions with the same thresholds.

## Hypothesis

C15's chess benefit came from one rule: a quiet, non-promoting pawn move that
arrives on the sixth rank or beyond keeps its full search depth instead of
being late-move-reduced. C15-v2 asserts that this rule can be evaluated from a
bitboard of eligible from-squares computed once per node, and that doing so
costs an order of magnitude less than C15's per-move mailbox read while
searching the identical tree.

## Position sets (from `research_top3/serious_errors.json`, n = 144)

| set | predicate | n |
|---|---|---|
| TARGET | `enemy_passer_advance >= 5` | 35 |
| HELD-OUT | `enemy_passers > 0 and enemy_passer_advance < 5` | 33 |
| NEGATIVE CONTROL | `enemy_passers == 0` | 76 |
| ALL | every serious error | 144 |
| RETENTION | the 17 positions C15 repaired (`c15_repaired_fens.json`) | 17 |

Search depth 12, oracle Stockfish at 1,000,000 nodes, identical to the C15 run.

## Chess gate

* RETENTION: at least 14 of the 17 repaired, and no more than 2 worsened over
  ALL. Strong pass at 15; exceptional at 17.
* TARGET: the rank-6+ subset must keep a meaningful improvement on C15's
  22 -> 19.
* HELD-OUT: must improve, so the benefit is not target-only.
* Denominator note: C15 was measured against C12 and C15-v2 is measured against
  RC-I. RC-I adds the mop-up term (bare-king endings only) and root repetition
  (empty history in a fresh search), so the two baselines are expected to agree
  on these positions; any position where they disagree is reported rather than
  quietly absorbed.

## Behavioural gate

240-position competition-like corpus at fixed depth 8, RC-I against C15-v2.
C15 produced 7 root move changes and 10 root score changes on this corpus. If
C15-v2 is semantics-preserving it must reproduce **exactly that set of 7 FENs**.
Any extra or missing change falsifies the equivalence claim and must be
explained before the candidate proceeds.

## Performance gate

Fixed 2,000 ms over the 24-position suite, alternating runs, three rounds.

| delta vs RC-I | verdict |
|---|---|
| <= 2% | preferred |
| <= 3% | PASS |
| 3-4% | REVIEW |
| > 4% | REJECT unless the chess repair is live-result-flipping |

Cross-checked at fixed depth 10, where node counts are deterministic, so the
time is a pure speed measurement.

## Other gates

Core and rule tests pass; tactics 16/16; clock ladder PASS with no overrun.

## Stop rule

No threshold on this page may be changed after any result is seen.
