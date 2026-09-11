# C25 — the codegen question is not measurable, and the positive control proves it

Lane `kushagra/c25-final-codegen`, rooted at `2bf6885`. Design frozen at
`e41714a`, positive control frozen at `8a7459c`, both before the campaigns they
govern. `START_FRACTION` 0.45 throughout. **No candidate was timed.** No arena,
no release, no merge.

**Verdict: BENCHMARK STILL TOO NOISY — and, more usefully, the obstacle is now
identified rather than merely measured.**

---

## 1. The result in one table

| control | n | Hodges-Lehmann | exact 95% CI | sigma_pair | pairs faster | verdict |
|---|---|---|---|---|---|---|
| **null, corpus A** | 16 | −0.58% | [−2.16, +1.06] | 2.83pp | 10/16 | **FAIL** |
| **null, corpus B** | 16 | −0.74% | [−1.96, +0.62] | 5.44pp | 12/16 | **FAIL** |
| **positive, `pc_x24`** | 16 | **−7.72%** | **[−9.15, −6.23]** | **2.50pp** | **16/16** | **FAIL** |

The positive control is the finding. `pc_x24` executes **24 extra dependent
multiplies per interior node** and searches a byte-identical tree. It does
strictly more work than the baseline, and it measured **7.72% faster**, with an
exact sign-flip p of **0.0000**, sixteen pairs out of sixteen, and the *tightest*
sigma of any campaign in this lane.

That is not an underpowered measurement. It is a precise measurement of the wrong
quantity.

---

## 2. Why a positive control cannot be built for this function

The three fixes C24 asked for were all implemented and all worked as intended:

* **The canary** is stable to 0.6% (reference median 1.5680 ns/hop, sd 0.0094,
  full range 1.0% over 20 baseline processes). It voided exactly one pair across
  the three campaigns, and that pair was re-run in the same schedule cell.
* **Arm identity** is counterbalanced alongside order. The residual identity
  separation fell to +0.96pp (null A), +0.18pp (null B) and +1.25pp (positive) —
  C24's uncontrolled −1.17% corpus-B drift is gone.
* **The positive control was sized to the target**, 24 chain steps against C24's
  4, on the mechanism argument that C24 measured the 4-step version at ≈1%.

And the positive control still failed, in the opposite direction, decisively.

The reason is structural: **you cannot add a known cost to `negamax` without also
perturbing its code layout, and the layout effect is larger than the cost.**
`negamax` is a 15,516-instruction function; changing its source at all changes
what LLVM emits and where, and that moves performance by roughly 8–11% — more
than the ≈5% of arithmetic the injection was supposed to add. The injected work
is real and unavoidable; it is simply swamped.

This is the same phenomenon the C20 instrumentation study saw when adding
counters made the core 11% *faster*, and which C23 correctly refused to believe
on a single run. It is now confirmed at n = 16 with p = 0.0000.

**A positive control of this design is therefore not constructible for this
function.** Any injection large enough to detect is large enough to reshape the
code around it.

---

## 3. Two distinct noise terms, now separated

The campaigns distinguish them, which earlier lanes could not.

**Per-source layout, large and consistent.** `pc_x24` moved −7.72% with sigma
2.50pp and 16/16 agreement. A given source compiles to a given layout, and that
layout's cost is stable across processes. This is a *real, reproducible* property
of the build — it is simply not a property of the algorithm.

**Per-process placement, smaller and heavy-tailed.** On byte-identical code the
null control still shows sigma 2.83pp (corpus A) and 5.44pp (corpus B), including
one pair at **−20.76%**. That pair is diagnostic:

```
baseline process wall 10.99 s   every other process in the campaign 7.72-8.98 s
canary 1.6055 (ceiling 1.6464)  -> CLEAN, core clock healthy
slower on ALL 16 positions       per-position deltas -6% to -30%
```

A process ran ~34% slow, uniformly, for its whole lifetime, with a healthy core
clock. That is not throttling and not interference; it is that process's own JIT
code placement. The canary is doing its job and correctly reports the machine as
healthy — the slowness is in the layout, exactly the limitation §1 of the design
declared in advance.

---

## 4. What this means for the candidate

`pvs_cascade_single_callsite` was **NOT TIMED**, per the frozen rule that no
candidate is timed until both controls pass.

Its static evidence stands and is unaffected: fixed-tree PASS over 62 positions
and 14,328,759 nodes with zero differences in move, score, nodes, quiescence
nodes, cutoffs or depth; `negamax` 15,516 → 15,268 instructions and 6,911 → 6,639
stack references, the largest reduction of the ten variants screened.

But §2 and §3 together say something stronger than "we could not measure it".
Suppose a campaign had returned a clean −5% for it. That number would be
indistinguishable from the −7.72% that a build doing *more* work produced. And
because the effect is per-source, it would not survive the next unrelated edit to
`cs_core.py` — a future evaluation change would reshuffle the layout and take the
gain with it.

**Chasing codegen in this engine means chasing a quantity that any subsequent
source change destroys, using a measurement that cannot tell it apart from doing
more work.**

---

## 5. Against the frozen acceptance criteria

| criterion, frozen before timing | outcome |
|---|---|
| null: exact 90% CI inside ±1.5% on both corpora | **FAIL** — [−1.96, +0.90] and [−1.69, +0.39] |
| null: no persistent arm-identity bias | pass — separations 0.96pp and 0.18pp |
| positive: exact 95% CI entirely above zero | **FAIL** — [−9.15, −6.23], the wrong side |
| positive: magnitude consistent with ≈5% cost | **FAIL** — inverted |
| candidate timed only if both controls pass | honoured — **not timed** |
| no effect-based trimming | honoured — one pair voided, on canary alone, re-run in cell |

Power was never the binding constraint. At the observed sigmas, 16 pairs resolve
3% on corpus A (9 needed) and 5% on both (4 and 12 needed). The estimator was
precise. It was pointed at the wrong thing.

---

## 6. RECORD THIS

**Shot 1 — the control that ran backwards.** One line:
`POSITIVE pc_x24 … HL −7.72%, 95% CI [−9.15, −6.23], p = 0.0000, 16/16 pairs
faster`. Then the explanation: *this build does twenty-four extra multiplies per
node and it is measured, with overwhelming significance, as almost eight percent
faster.* The point lands because the statistics are impeccable and the conclusion
is still wrong.

**Shot 2 — the honest canary.** The −20.76% pair on byte-identical code: baseline
wall 10.99 s against 7.72–8.98 s everywhere else, canary 1.6055 under a 1.6464
ceiling, slower on all sixteen positions. The health probe says the machine is
fine, and it is right. The slowness is in where the compiler put the code.

**Shot 3 — three lanes, one lesson.** C23 said ±6% on identical code and refused
to believe it. C24 tightened the harness and still failed. C25 fixed all three
named defects, achieved sigma 2.5pp, and used that precision to prove the
measurement cannot answer the question. Show the three verdicts in sequence.

---

## 7. Reproduction

```
uv run python benchmarks\current\final_codegen\reference.py --n 10 --out reference2.json
uv run python benchmarks\current\final_codegen\campaign.py --test-variant baseline --corpus A --pairs 16 --canary-max 1.6464 --out pairs_null_A.jsonl
uv run python benchmarks\current\final_codegen\campaign.py --test-variant baseline --corpus B --pairs 16 --canary-max 1.6464 --out pairs_null_B.jsonl
uv run python benchmarks\current\final_codegen\campaign.py --test-variant pc_x24 --corpus A --pairs 16 --canary-max 1.6464 --out pairs_pos_A.jsonl
uv run python benchmarks\current\final_codegen\analyse.py --files pairs_null_A.jsonl pairs_null_B.jsonl --label null --control null
uv run python benchmarks\current\final_codegen\analyse.py --files pairs_pos_A.jsonl --label positive --control positive
```

Environment: Python 3.13.5, numba 0.67.0, numpy 2.5.2, 12 logical CPUs, all
processes pinned to CPU 4, `cache=False`. Peak working set 432–439 MB, compile
26–30 s per process — both well inside competition limits and unchanged by any
arm.
