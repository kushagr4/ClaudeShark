# Why C15's passer exemption cost so much, and why C15-v2's does not

The rule both implementations apply is the same sentence: *a quiet,
non-promoting pawn move arriving on the sixth rank or beyond keeps its full
depth instead of being late-move-reduced.* Four builds of the same rule were
compiled and measured against each other, three rounds, alternating, one
process each, so thermal drift and background noise fall on all four equally.

| build | how the rule is evaluated |
|---|---|
| v0 | no rule at all — RC-I, the control |
| v1 | C15 exactly: `mover = M[fr]` read from the mailbox **before** `make_move`, then `mover == 1 + 6 * side` and a rank test |
| v2 | the same predicate read back off the bitboards **after** `make_move`, inside the branch that was about to reduce |
| v3 | **C15-v2**: one loop-invariant bitboard of eligible from-squares, tested at the end of the existing short-circuit chain |

## The measurement

Fixed depth 10 and fixed 2,000 ms over the 24-position suite.

| build | nodes at depth 10 | depth-10 NPS (mean of 3) | vs v0 | 2,000 ms NPS (mean of 3) | vs v0 |
|---|---|---|---|---|---|
| v0 | 16,795,023 | 2,326,412 | — | 2,404,248 | — |
| v1 | **16,818,635** | 2,218,919 | **−4.62%** | 2,281,263 | **−5.12%** |
| v2 | **16,818,635** | 2,323,138 | −0.14% | 2,396,852 | −0.31% |
| v3 | **16,818,635** | 2,316,747 | −0.42% | 2,415,156 | **+0.45%** |

The three feature builds produce **exactly the same node count**, to the node,
at a fixed depth. They search the identical tree. Every difference in the table
is therefore implementation cost and nothing else. v3 is 4.41% faster than v1
at fixed depth and 5.87% faster at fixed time while doing identical work.

## The mechanism

It is not the predicate. It is what the predicate forces the compiler to keep
alive.

`negamax` is compiled as one enormous function — 45,177 machine instructions,
of which 21,433, or **47%, already address memory through the stack pointer**.
Numba inlines move generation, make/unmake and the evaluation into it, and the
register allocator has long since run out of registers. In a function in that
state, the cost of a new value is not the arithmetic; it is whether the value
has to survive a call.

C15 reads `M[fr]` *before* `make_move`, and uses it *after* `make_move` and
`is_legal_after_make`. The loaded piece code therefore has to survive two calls
in the hottest loop in the engine, and `1 + 6 * side` makes `side` loop-live as
well — and `side` cannot be rematerialised from `S[0]`, because `make_move`
flips it. Two extra values crossing every call in an already-spilling function:

| build | instructions | stack-addressed | added vs v0 |
|---|---|---|---|
| v0 | 45,177 | 21,433 | — |
| v1 | 45,317 | 21,512 | +140 insns, **+79 stack** |
| v2 | 45,278 | 21,481 | +101 insns, +48 stack |
| v3 | 45,286 | 21,496 | +109 insns, +63 stack |

v1 adds the most stack traffic of the three and is the only one that is slow.
v2 and v3 add code of comparable size and cost nothing measurable, because
neither creates a value that has to cross a call: v2 reads the bitboards after
the move is on the board, and v3's `adv_pawns` is loop-invariant, computed once
per node, in the same class as the `enemy` mask that was already there.

C15-v2 uses v3 rather than v2 because it is exactly equivalent by construction
rather than by coincidence of the enclosing conditions, and because it moves
the work from once per move to once per node.

## What this corrects in the record

The RC-I record states C15 cost "8.5% nodes per second on an essentially
identical tree". Re-measured today against RC-I, three alternating rounds, the
same code costs **4.6% at fixed depth and 5.1% at fixed time**. The direction
and the rejection stand; the magnitude in that record was a single pairing on a
busier machine and was overstated. The 15% figure recorded for the "cheaper
rewrite" is not reproduced either — v2 here is the same idea and costs 0.3%.
Both original numbers came from one unreplicated pairing, which is the lesson
worth keeping.

## The rule the two builds share, stated exactly

Given the enclosing condition — the move is quiet, non-promoting, late and not
a killer — C15's test `M[fr] == pawn and to_rank >= 5` selects precisely the
moves whose from-square holds one of our pawns on the fifth or sixth rank
(White) or the fourth or third (Black). A pawn on the seventh only reaches the
eighth by promoting, and promotions were already exempt. So the whole predicate
collapses to one bit of a per-node mask, which is what C15-v2 tests.
`tests/test_advanced_pawn_lmr.py` holds the two descriptions together over
5,000+ random positions, and the identical node counts above confirm it in the
compiled search.
