# C25 — final codegen measurement: design, frozen before any control campaign

Lane `kushagra/c25-final-codegen`, rooted at `2bf6885`. `START_FRACTION` stays at
**0.45**; C22's 0.50 is preserved separately and is never combined with this. No
arena, no release, no merge. This is the last methodology iteration for the
codegen question.

Environment: Python 3.13.5, numba 0.67.0, numpy 2.5.2, 12 logical CPUs,
`cache=False` so every process recompiles.

---

## 1. What C24 got wrong, and the three fixes

C24's controls both failed. Null control corpus A: HL −0.44%, 90% CI
[−1.65, +0.86], sigma_pair 4.74pp. Corpus B: HL −1.17%, 90% CI [−2.19, −0.10] —
a residual ~1% directional effect on byte-identical code. Positive control: HL
+0.46%, 95% CI [−0.93, +2.14], **not detected**. No candidate was timed, and none
will be until both controls pass.

### Fix 1 — a predeclared canary, not post-hoc trimming

One C24 process took 12.65 s where its neighbours took 10.5 s, producing a
−16.19% pair delta on byte-identical code. Two rules that do **not** work were
tested against the C24 data before choosing:

* **Within-process repeat spread.** The bad process's repeat spread was 3.1%,
  entirely normal against 95 other processes ranging to 14.0%. It was
  *uniformly* slow, not intermittently disturbed. This rule would have missed it.
* **Raw search wall time.** It would catch it, but it would also void a positive
  control that is legitimately slower, which is the one arm that must survive.

So the canary is a **pointer chase compiled in the harness, not in the engine** —
byte-identical in every arm by construction, so its runtime depends only on the
machine and never on the code under test. It walks one permutation cycle of 4096
int64 slots (32 KB, L1-resident); each load's address is the previous load's
value, so the chain cannot be unrolled, vectorised or folded.

A first attempt used an integer multiply-add recurrence and measured **0.138
ns/iteration** — under one cycle, because LLVM closed-formed the affine
recurrence. A probe the compiler can evaluate is not a probe.

A second attempt took a single 3 ms sample before and after the search and used
the worse. That was far too noisy: in the first reference run one process read
**3.33 ns/hop** — twice the median — with a completely normal 8.50 s search,
while the process that really was slow (13.18 s) read only 1.73. Interference is
one-sided, so the reading is now the **minimum over five short batches**, taken
before and after the timed region, worse of the two.

**Reference distribution** (baseline arm only, 20 processes, both corpora, run
before any pairing so it cannot know which arm wins anything):

```
median 1.5680   mean 1.5663   sd 0.0094 ns/hop
min 1.5472   max 1.5833   max/median 1.0097
```

**FROZEN RULE: a process with canary > 1.6464 ns/hop is INVALID.**
That is the reference median × 1.05 — roughly eight standard deviations above a
distribution whose entire observed range is 1.0% wide, and it voids 0 of the 20
reference processes.

If **either** member of a pair is invalid, the **whole pair is voided** and
re-run in the same schedule slot with the same cell. The favourable half is never
kept. Every invalidation is recorded with its readings. The rule looks only at
process health; it never looks at which arm was faster, at the pair delta, or at
the treatment. **No effect-based trimming of any kind is used.**

*Stated limitation:* the canary detects core-clock degradation — throttling,
migration to a slower core, a noisy neighbour stealing frequency. Being
L1-resident it would **not** detect pure last-level-cache or memory-bandwidth
contention that leaves L1 latency intact. Raw wall time and conditioning
throughput are recorded for every process so that such a case is diagnosable
afterwards even though it is not voidable by rule.

### Fix 2 — counterbalance arm identity as well as order

C24 counterbalanced execution order but not module identity: the baseline source
always lived in `cs_core_a0`, the comparison always in `cs_core_a1`. Even with
equal-length names these are distinct compilation units, so any systematic
difference between them was inseparable from the treatment — and a persistent
−1.17% on corpus B is exactly what that looks like.

Each pair now draws from **four cells in equal numbers**:

```
{baseline source first, test source first} x {test source in arm 0, test source in arm 1}
```

shuffled from seed **20260910**, frozen before timing. The arm files are
regenerated per pair, so the test source really does change module identity. For
the null control both sources are byte-identical RC-J, so the identity split
measures any residual arm bias directly, and it is reported separately from the
order split.

### Fix 3 — a positive control sized to the target

C24's positive control was roughly a 1% true cost while the campaign was trying
to resolve 3–5%. It could not have been detected and its failure said nothing.

The injected cost is a serial dependent multiply chain per interior node stored
to `CTL[15]`, a slot the driver never reads: it cannot be optimised away and
cannot change the tree. Its strength is the chain length.

**FROZEN: `pc_x24`, a 24-step chain.** C24 measured the 4-step chain at roughly a
1% true cost, and the chain is serial, so cost scales with length: 24 steps is
about 5–6%, the target.

The strength is frozen **on that mechanism argument, not on the calibration
deltas**, because the development sample did not produce a usable cost curve —
and that failure is itself the first result of this lane. Four pairs per arm,
canary clean on every process (worst 1.5800 against the 1.6464 ceiling):

| arm | pair deltas | median | sd |
|---|---|---|---|
| `pc_x16` | +0.86, +9.01, +0.75, −3.55 | +0.81% | 5.25pp |
| `pc_x24` | −4.41, −4.89, −5.84, +3.32 | **−4.65%** | 4.23pp |

`pc_x24` does strictly more work than `pc_x16`, which does strictly more work
than the baseline. The measured ordering is inverted: the heaviest build reads
4.65% **faster** than the baseline and 5.5pp faster than the lighter injected
build. Three of its four pairs show a build that cannot be faster measuring 4–6%
faster.

That is not a power problem that more pairs would fix, and it is not core-clock
health, which the canary independently rules out. It is what the frozen campaign
now has to confirm or refute at n = 16.

---

## 2. Everything C24 got right, kept

One engine module per fresh process; one JIT lifecycle; import, compile and
search timed separately with only search reported as speed; affinity pinned to
CPU 4 for every arm; a fixed 45 s conditioning deadline filled with engine work
rather than sleep, so an arm's own compile duration cannot leak into the thermal
state the timed region inherits; rep-major sweeps; per-position minima aggregated
as a geometric mean of ratios rather than a ratio of sums; gc disabled and
frozen; equal-length module names; and a per-position work fingerprint — move,
score, nodes, qnodes, TT probes, TT hits, cutoffs, depth — asserted identical
across every process of an arm and between baseline and test.

---

## 3. Frozen parameters

```
depth 9    positions 16    reps 3    pin CPU 4    settle 45 s
seed 20260910              canary ceiling 1.6464 ns/hop
n = 16 VALID pairs per arm per corpus
corpus A = curated benchmark positions
corpus B = competition_like_v1 real-game positions, used in no part of
           choosing any variant
```

**n = 16 is fixed now.** It is not raised after seeing a trend, and there is no
sequential stopping rule. At n = 16 the 80%-power two-sided MDE is
0.77 × sigma_pair: 1.8% at sigma 2.3, 2.3% at sigma 3.0, 3.1% at sigma 4.0. So 16
valid pairs resolve a 3% effect for any sigma up to about 3.9pp, and comfortably
resolve 5%.

---

## 4. Acceptance, declared now

**Null control** — byte-identical twin. The exact **90% CI must lie entirely
inside ±1.5%** on both corpora, and the arm-identity split must show no
persistent bias.

C24 used ±1.0%, which at its sigma of 4.74pp was arithmetically unreachable — a
self-defeating threshold. ±1.5% is **not a relaxation to pass**: it is half the
3% PROMISING threshold, so a harness inside it cannot manufacture or mask a 3%
effect's direction, and at n = 16 the 90% CI half-width is 0.44 × sigma_pair —
1.01% at sigma 2.3, 1.31% at sigma 3.0 — so the test is achievable by a clean
harness and still fails a dirty one.

**Positive control** — the exact **95% CI must lie entirely above zero**, and the
magnitude must be directionally consistent with the calibrated cost. If the
harness cannot see an injected ≈5% cost it cannot see a real 5% speedup.

**If either control fails: BENCHMARK STILL TOO NOISY, stop, time no candidate.**

**Candidate**, on the worst corpus:

| HL speedup | verdict |
|---|---|
| < 2% | NO EFFECT |
| 2–3% | WEAK |
| ≥ 3% | PROMISING |
| ≥ 5% and both CIs exclude zero | STRONG — requires a separate confirmation batch |
| ≥ 8% | VERY STRONG — same, with a new seed |

---

## 5. The one candidate

`pvs_cascade_single_callsite`, and only it. Arms 4 and 5 from C24 are not timed
unless a human asks later.

Static evidence, already established: fixed-tree PASS over 62 positions and
14,328,759 nodes with zero differences; `negamax` **15,516 → 15,268
instructions** and **6,911 → 6,639 stack references**, the largest reduction of
the ten screened variants. Mechanism: the PVS/LMR cascade becomes a three-stage
schedule over one call site instead of three, so a twenty-argument list is
marshalled once per move rather than up to three times.

**The static improvement is real. The runtime improvement is unknown — that is
what this measures.** No arena, no release, no integration, whatever the result.

## 6. Order of execution

1. calibrate the positive control on a development sample, freeze it;
2. null control, corpus A and corpus B;
3. positive control, corpus A;
4. **only if both pass**, `pvs_cascade_single_callsite`, corpus A and corpus B;
5. only if it reaches STRONG, an independent confirmation batch with a new seed.
