# Where the speed could come from

An investigation, not a decision. Nothing here is implemented.

## The situation

After the v0.3 evaluator work the engine runs at roughly **69k nodes/second**
and reaches **depth 8** on a 4.5 s budget. A competitive C engine at the same
budget reaches depth 14+. Every extra ply is worth somewhere around 50–70 Elo at
these depths, so speed is not a vanity metric — it is most of the remaining gap.

Where the time goes (`tools/profile_search.py`, updated after the evaluator
optimisation):

| area | share | ours? |
|---|---|---|
| legal move generation | ~32% | no — python-chess |
| `push` / `pop` | ~19% | no — python-chess |
| `cs_eval.evaluate` | ~19% | yes |
| move ordering | ~11% | yes |
| search bookkeeping | ~19% | yes |

**About half the time is inside python-chess.** That bounds what optimising our
own code can achieve: even a free evaluator and free ordering would leave the
engine at roughly 2x, which is one extra ply.

## The four options

### A. Stay on python-chess and optimise around it

Keep the library, reduce how often we call it and how much we do per node.
Remaining levers: staged move generation (try the transposition move before
generating anything), incremental evaluation maintained through push/pop,
cheaper ordering, and spending nodes better (static exchange evaluation, check
extensions) rather than producing more of them.

- Expected: **+15–35% effective speed**, plus Elo from node *quality* that is
  independent of speed.
- Effort: low, incremental, each piece independently testable.
- Correctness risk: low. Every step is A/B-able with the existing tools.
- Reversibility: total.

### B. Custom bitboards in pure Python

Own the board and move generation. The gain would come from dropping generality
we never use — Chess960, SAN parsing, `Move` objects — and from encoding moves
as integers rather than allocating an object per move.

- Expected: **1.5–2.5x** on movegen and make/unmake, so maybe **1.4–1.8x**
  overall. It is still interpreted Python; the constant factor improves, the
  order of magnitude does not.
- Effort: large. Move generation is where chess engines hide their bugs.
- Correctness risk: high, but *measurable*: perft against python-chess is an
  exact, exhaustive oracle, which makes this far safer to attempt than it
  sounds.
- Reversibility: poor once the search depends on the new representation.

### C. Numba-JIT bitboard engine

The only route to a genuine order of magnitude.

The critical thing to understand is that **Numba does not speed up a Python
function you call from Python** — the win comes from compiling a whole region
into machine code. Jitting only `evaluate` or only movegen would leave a
Python-level recursive search calling into it once per node, and boxing and
unboxing at every boundary would eat most of the gain. The starter's own
`baselines/numba` is exactly this cautionary tale: it jits the evaluation of a
two-ply search and scores barely better than the un-jitted version.

Getting the real win means the *entire* search — negamax, the transposition
table, move ordering, make/unmake — living in `nopython` mode over typed arrays,
with no Python objects in the hot path.

- Expected: **5–20x** if the whole search compiles; near zero if the boundary is
  crossed per node. There is no middle outcome, which is what makes this risky.
- Effort: very large. This is a rewrite of the engine, not of a module.
- Correctness risk: very high. Numba's `nopython` subset is restrictive —
  no dicts of tuples, no classes as we use them, recursion is supported but
  awkward; the transposition table becomes a typed array, killers and history
  become arrays, and `chess.Move` disappears entirely.
- Packaging: **compliant**. Native binaries inside the zip are rejected, but
  Numba is preinstalled and ships as readable Python source compiled at runtime,
  so nothing compiled enters the submission. Compilation must be warmed at
  import with the exact argument types the real calls use, inside the 60 s
  initialisation budget, which is ample. See `docs/SPEC.md`.
- Cold start: warm-up must cover every signature, or the first search of the
  game pays compilation on the clock.
- Reversibility: effectively none. This becomes the engine.

### D. Other compliant routes

- **Cython or a C extension — out.** Native binaries inside the zip are
  rejected, and no additional package installs at validation, so there is
  neither a way to ship a built extension nor a way to depend on one.
- **PyPy — unavailable.** The runtime is CPython 3.12.
- **Parallel search — pointless.** One dedicated core. The 128-process
  allowance does not create a second core.
- **Pondering — potentially large, currently blocked.** Thinking during the
  opponent's turn would be free on our own clock. The documentation read on
  2026-09-02 does say it is allowed, but the project is treating that as
  pending organiser confirmation and is **not implementing it**. Analysis in
  `docs/PONDERING.md`; status in `docs/SPEC.md`.
- **Spend nodes better instead of making more.** SEE-ordered captures, check
  extensions and a stronger evaluation raise Elo per node. This competes
  directly with a rewrite for engineering time and is far cheaper.

## Recommendation

**Stay on python-chess for now (A).**

Pondering (D) would be the next large lever, but it is blocked pending
organiser clarification and is not counted here.

The reasoning is about ratios, not about ambition. A full Numba rewrite offers
maybe three extra plies for an effort measured in weeks, with a real chance of
landing at zero if the search does not fully compile, and no way back.
Node-quality work — SEE, extensions, better ordering — is far cheaper, stacks
with everything else, and is where the next effort goes.

Before any rewrite is authorised, it should be gated on a **spike**, not a
promise: implement perft in Numba `nopython` mode over a bitboard
representation, warm it, and measure nodes/second end to end against
`python-chess` perft. If that spike does not show at least 5x on the same
machine, option C is not worth its risk and the answer is A indefinitely.
