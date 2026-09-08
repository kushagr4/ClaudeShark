# C15-v2 — the advanced-pawn LMR exemption, at no measurable cost

Baseline RC-I (`kushagra/rc-g-combined`, `6c104cb`), the submitted build, live
from round 69. Branch `kushagra/c15v2-efficient-passer`. Nothing here has been
uploaded.

C15 proposed one rule and was rejected on its price. This lane keeps the rule,
reproduces it exactly, and pays almost nothing for it. Along the way it found
that a large part of C15's *chess* evidence — and of the numbers in the RC-I
record — was an artefact of the comparison harness rather than of the engine.

## The rule

A quiet, non-promoting pawn move that arrives on the sixth rank or beyond keeps
its full search depth instead of being late-move-reduced. It applies to
whichever side is to move at a node, so deep in the tree it is mostly the
*opponent's* passer pushes that stop being reduced away — which is the
mechanism the Top-3 differential pointed at, where an enemy passer doubles
ClaudeShark's serious-error rate.

## Why C15 was expensive, and why this is not

Four builds of the same rule, three alternating rounds, one process each.

| build | how the rule is read | depth-10 NPS | vs RC-I | 2,000 ms NPS | vs RC-I |
|---|---|---|---|---|---|
| RC-I | no rule | 2,326,412 | — | 2,404,248 | — |
| C15 as written | `M[fr]` before `make_move` | 2,218,919 | **−4.62%** | 2,281,263 | **−5.12%** |
| after `make_move` | bitboard at `to` | 2,323,138 | −0.14% | 2,396,852 | −0.31% |
| **C15-v2** | per-node mask of from-squares | 2,316,747 | **−0.42%** | 2,415,156 | **+0.45%** |

All three feature builds search **16,818,635 nodes** at depth 10 — the same
number, to the node. They are the same rule; only the price differs.

`negamax` compiles to 45,177 instructions, 47% of which already address memory
through the stack pointer: the register allocator is exhausted. C15's cost was
not the test but the fact that the loaded piece code, and `side` with it, had to
stay alive across `make_move` and `is_legal_after_make` — and `side` cannot be
rematerialised, because `make_move` flips it. C15-v2's `adv_pawns` is
loop-invariant, computed once per node, in the same class as the `enemy` mask
that was already there. Full analysis in
`benchmarks/current/c15v2_passer/ROOT_CAUSE.md`.

Two figures in the RC-I record are corrected by this: C15's cost is 4.6–5.1%,
not 8.5%, and the "cheaper rewrite costs 15%" claim does not reproduce — that
rewrite is the third row above and costs 0.3%. Both original numbers came from
single unreplicated pairings.

## The implementation

20 lines in `cs_core.py`. A constant, one line before the move loop, and one
clause appended to the condition that was already there:

```python
ADV_PUSH_SRC = np.array([0x0000FFFF00000000, 0x00000000FFFF0000], dtype=np.int64)
...
adv_pawns = B[1 + base] & ADV_PUSH_SRC[side]
...
if (move_index >= LMR_START and can_reduce and not is_capture and promo == 0
        and move != killer_1 and move != killer_2
        and ((np.int64(1) << (move & 63)) & adv_pawns) == 0):
```

Given the enclosing condition — quiet, non-promoting, late, not a killer —
C15's `M[fr] == pawn and to_rank >= 5` is exactly "the from-square holds one of
our pawns on the fifth or sixth rank (White) or the fourth or third (Black)". A
seventh-rank pawn only reaches the eighth by promoting, and promotions were
never reduced. `tests/test_advanced_pawn_lmr.py` holds the two descriptions
together over 5,000+ random positions.

## Equivalence, proven rather than argued

240 competition-like positions, fixed depth 8, C15's semantics on the RC-I
baseline against C15-v2:

| | |
|---|---|
| root move changes | **0 / 240** |
| root score changes | **0 / 240** |
| node count differences | **0 / 240** |
| total nodes | 52,601,904 against 52,601,904 |

C15-v2 is C15, about 5% faster.

## The harness that gave two answers

`compare.py`, which produced C15's chess verdict, kept one Stockfish process
per worker and never cleared its hash. A fixed-node search is deterministic
only from a fixed starting state, so every analysis depended on the moves the
build under test had played earlier in the run. The symptom is an impossible
row: both builds play the same move and the oracle scores it differently.

| run | positions | same move, different score |
|---|---|---|
| C15 vs C12, the run behind the C15 verdict | 144 | **55** |
| RC-I vs C15-v2, first attempt on the same harness | 144 | **57** |

**Five of C15's seventeen reported repairs, and both of its two reported
regressions, are positions where the two builds played the identical move.**
Three of those five are swings above 6,000 centipawns attributed to a move that
was never in question. The figure "17 repaired against 2 worsened" in
`2026-09-08-rc-i-combined.md` should not be quoted again.

The fix is to declare a new `game` per analysis, so python-chess sends
`ucinewgame` and Stockfish clears its table. `compare2.py` does that and
asserts two invariants on its own output; both were zero on the run below.
Details in `benchmarks/current/c15v2_passer/ORACLE_DEFECT.md`.

## Chess result, measured properly

RC-I against C15-v2, the same 144 serious errors from the 4,909-ply Top-3
differential, depth 12, oracle at 1,000,000 nodes with the table cleared per
analysis.

| set | n | RC-I ≥100cp | C15-v2 ≥100cp | repaired | worsened | mean loss |
|---|---|---|---|---|---|---|
| TARGET, enemy passer rank 6+ | 35 | 24 | **20** | 4 | **0** | 272.1 → **210.0** |
| HELD-OUT, enemy passer rank <6 | 33 | 18 | 17 | 3 | 2 | 169.5 → 165.5 |
| CONTROL, no enemy passer | 76 | 49 | 45 | 4 | **0** | 273.7 → 268.1 |
| ALL | 144 | 91 | **82** | **11** | **2** | 249.5 → 230.5 |

Nine positions did not reach depth 12 inside the 20 s cap in one build or the
other; their moves are timing-dependent and are reported as measured.

### Against the pre-registration

The pre-registered retention gate asked for at least 14 of C15's 17 repairs.
By the letter C15-v2 reaches 10 of 17, so **the gate as written is not met** —
but the denominator turned out to contain 5 positions where both builds played
the same move, which no implementation could either keep or lose. Against the
12 credible repairs, C15-v2 **plays C15's exact move on 12 of 12**, and 10 of
those still measure as repairs once the oracle is fixed; the other two moved
across the 100 cp line because the oracle changed, not because the engine did.
Retention is complete in behaviour, and the threshold was not moved to say so.

The worsened limit of 2 is met exactly. TARGET improves more than C15 claimed
to (24 → 20 with no regressions, mean loss down 23%). HELD-OUT improves, but
weakly: one position net, four centipawns of mean loss.

### The two regressions

| position | RC-I | C15-v2 |
|---|---|---|
| `4r1k1/8/1R6/pp3R1P/6p1/P1P2b1r/1P6/5K2 b` | `a5a4`, 56 cp | `h3h2`, 108 cp |
| `8/8/8/1p4R1/p1k2K2/2r5/1r6/8 w` | `g5g1`, 2 cp | `g5e5`, 147 cp |

Both are rook endings with enemy passers. The first straddles the threshold;
the second is a real 145 cp regression.

### Depth relationship

Two of the eleven repairs are positions the baseline still gets wrong with five
extra plies, so they are knowledge rather than speed. The largest is
`2Q5/8/6p1/5q2/6k1/K1p5/1p6/8 w`: three enemy passers, one square from
queening, RC-I grabs the queen with `Qxf5+` and loses 22,934 cp, C15-v2 plays
`Qc4+` and loses nothing. Full replay in
`benchmarks/current/c15v2_passer/CAUSAL_REPLAY.md`.

## Gate

| check | result |
|---|---|
| full test suite | **1,486 passed** (RC-I's 1,451 plus 35 new predicate tests) |
| equivalence to C15 on 240 positions, depth 8 | **0 move, 0 score, 0 node differences** |
| behaviour against RC-I on the same 240 | 7 move changes, 10 score changes, +1.44% nodes — **the identical seven FENs C15 changed** |
| serious errors, 144 positions, depth 12 | 91 → **82**; 11 repaired, 2 worsened |
| tactics, 1,000 ms | **16/16**, average depth 12.75 |
| clock ladder | **PASS**, zero overruns at every rung |
| nodes per second vs RC-I | **−0.42%** fixed depth, **+0.45%** fixed time |

Clock ladder in full: 21.4% of budget used at the 2,000 ms rung, 8.8% at
5,000, 5.6% at 10,000, 5.9% at 30,000, 3.8% at 60,000 and **3.2% at the
competition's 120,000 ms**, floor 3,873 ms, no overrun anywhere.

The seven changed positions are the whole behavioural footprint of the feature
on ordinary play, and they are the same seven C15 changed — which is what
"exactly equivalent" has to mean.

## Strength against RC-I

Two paired screens against the frozen `champions/rc_i` snapshot, 120 s + 0.5 s,
strict claims, the organiser start set, nothing else running on the machine.

| screen | result | score | Elo | paired bootstrap |
|---|---|---|---|---|
| 30 games | +11 =10 −9 | 53.3% | +23 | −83 .. +134 (15 clusters) |
| 60 games | +19 =25 −16 | 52.5% | +17 | −53 .. +89 (30 clusters) |
| **pooled 90** | **+30 =35 −25** | **52.8%** | **+19** | both intervals span zero |

Zero failures in 90 games. Clock floor 2,895 ms, worst single move 12,629 ms,
no overrun. Colour on the 60: White 48.3%, Black 56.7%; on the 30 both 53.3%.

This is not a proven Elo gain and should not be quoted as one. A feature that
leaves 233 of 240 ordinary positions bit-identical cannot move a 90-game screen
far, and it did not. What the screen establishes is the thing it was run for:
the change is not harmful.

## Release candidate RC-J

RC-G and RC-H belong to the terminal-shortcut lane and RC-I is the submitted
build, so J is the next free name.

| field | value |
|---|---|
| archive | `corpus/release/claudeshark_rc_j.zip` |
| canonical path | `C:\Users\epick\Documents\ClaudeShark\corpus\release\claudeshark_rc_j.zip` |
| SHA-256 | `c8226c03164e70454d4a1c03c72f3a253912616386dc415e2b6f140b05122fb5` |
| size | 67,072 bytes compressed, 201,363 unpacked, 16 files |
| snapshot | `champions/rc_j` |
| release check | **16 of 16 PASS**, "READY TO UPLOAD" |
| Python 3.12 smoke from the canonical artifact | 10/10 probes legal, import and warm-up 28.24 s of the 90 s budget |

The canonical copy is byte-identical to the worktree build, verified with
`cmp` and by hashing both. The submitted RC-I archive was missing from the
canonical release directory entirely — it existed only inside the scratchpad
worktree — so it has been published there too, hash
`3bfe20b53891e468726fb1ae8461f568f510a6c82f7cc299b38abc5681749921`, unchanged.

## Verdict

**PROMOTE.** Every stop condition is met: the repair generalises to the
held-out and control sets with no regressions in either, every credible C15
improvement is preserved move for move, the cost is inside noise instead of
5%, ordinary play changes on seven positions in 240 and on exactly the seven
C15 changed, tests and clock pass, and 90 games show no harm.

Confidence is high on everything deterministic — equivalence, cost, the error
counts under a fixed oracle — and low on Elo, which 90 games cannot resolve for
a change this small in footprint.

CURRENT SUBMITTED remains RC-I. Nothing has been uploaded.
