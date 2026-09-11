# C25 — corrected audit (addendum)

**Status of this document.** `REPORT.md`, `DESIGN.md` and every result, log and
summary file in this directory are left exactly as committed in `e41714a`,
`8a7459c` and `bcb66a9`. They remain the historical record. This audit was
accepted on review and **supersedes REPORT.md's interpretation** wherever the
two differ.

**The correction in brief**

- **The frozen null gate failed.** The exact 90% CI was not inside ±1.5% on either
  corpus: A [−2.01, +0.91], B [−1.70, +0.50]. So C25 is **FAILED — BENCHMARK
  UNVALIDATED** (frozen label: BENCHMARK STILL TOO NOISY), however the positive
  control is read.
- **`pc_x24` was not a clean positive control.** Its 24 multiplies survived
  compilation, but the insertion also changed code generation throughout
  `negamax`: 944 → 930 call sites, register-indirect call allocation reshuffled,
  and a lower net instruction count. It was never guaranteed to run slower, so its
  failure is not evidence that the harness lacks power.
- **Positive-control selection violated the originally frozen design.** Fix 3's
  frozen rule ("chosen on a separate development sample … targeting ≈5%
  slowdown") was rewritten at `8a7459c`, after the calibration data existed. The
  control was frozen by extrapolation from a C24 figure that was never measured,
  and the development sample reused the powered control's positions.
- **`pvs_cascade_single_callsite` was never timed.**
- **No codegen candidate was established.**
- **CODEGEN LANE CLOSED.**

The machine-code figures in section 4 come from compile-and-inspect runs of
`negamax` (no timing) made during the audit. Those inspection scripts are not
part of this commit. Section 8's route recommendation was written before the
actual-loss autopsy of RC-J's Chessathon games and is superseded by it.

---

# C25 — corrected final audit (accepted)

Read-only audit of the committed C25 record: branch `kushagra/c25-final-codegen`, results commit `bcb66a9`. Nothing was re-run and nothing was timed.

Evidence used:
- my own recomputation from the raw pair records;
- nine read-only auditors and three adversarial reviewers, each recomputing from the raw JSONL;
- two compile-and-inspect runs of `negamax`'s machine code, done before the hold point, with no timing.

---

## 1. Frozen design, gates and chronology

| commit | time | what it froze |
|---|---|---|
| `e41714a` | 11:33:52 | **Design.** Canary rule: a process reading >1.6464 ns/hop voids the whole pair, which is re-run in the same slot and cell. Four-cell counterbalance with seed 20260910. n = 16 valid pairs per corpus, with no sequential rule. **Gates:** the null passes if its exact 90% CI lies inside ±1.5% on both corpora *and* there is no persistent arm-identity bias. The positive passes if its exact 95% CI lies entirely on the slower side *and* its magnitude is directionally consistent with the calibrated cost. If either fails: BENCHMARK STILL TOO NOISY, time no candidate. |
| `8a7459c` | 11:52:29 | Positive control frozen at `pc_x24`; calibration data committed |
| `bcb66a9` | 13:25:36 | Control results, `analyse.py`, summaries, REPORT |

- **Nothing that governs the verdict was edited after results.** Every harness file is byte-identical from `e41714a` to `bcb66a9`, and DESIGN §3/§4 never changed.
- **Run timing is consistent, not proven.** Commit order is proven. File mtimes put the calibration start about 13 s after `e41714a` and the null-A start about 12 s after `8a7459c`.
- **`analyse.py` was not frozen in git.** It was first committed with the results. Its thresholds match the frozen DESIGN, so the verdict does not depend on it.
- **The arm-identity clause cannot be scored.** It has no numeric threshold, so it is *not scorable*, not "pass".

## 2. Null control — FAIL (independently confirmed)

| corpus | n | voids | HL | exact 90% CI (standard) | committed 90% CI | sd | faster |
|---|---|---|---|---|---|---|---|
| A | 16 | 0 | −0.58% | **[−2.01, +0.91]** | [−1.96, +0.90] | 2.83pp | 10/16 |
| B | 16 | 0 | −0.74% | **[−1.70, +0.50]** | [−1.69, +0.39] | 5.44pp | 12/16 |

- **The gate fails on both corpora under every interval tried.** Both the standard exact Wilcoxon inversion and `analyse.py`'s convention put the lower bound below −1.5. So do the t, sign-test and permutation intervals.
- **The raw data check out.** All 56 pair deltas recompute from per-process minima with zero error. No effect-based trimming exists anywhere. There are two voids in total, both decided on canary readings alone and both re-run in the same slot and cell.
- **`analyse.py`'s "exact" CI is one order statistic too narrow.** Its coverage is 94.9% at the 95% level and 89.5% at the 90% level. The gate outcome does not change.
- **Arm identity.** The per-process arm bias b is −0.92pp on means in both nulls (p = 0.20 and 0.77). It is neither demonstrated nor excluded. The committed "+0.96 / +0.18pp separation" is −2b on medians.
- **Order effect.** The sign flips between corpora, so there is no persistent order effect. The interaction is not significant.
- **Operating characteristic of the frozen gate.** This is disclosed only; it rescues nothing. A perfectly unbiased harness at the observed sigmas would pass about 27–31% of the time on A and about 0.2% on B. So the failure is a precision failure and weak evidence of bias, but the benchmark is unvalidated either way.
- **Power.** Frozen n = 16. A 3% effect was detectable on A (power about 0.97) but not on B (about 0.5; 28–32 pairs needed). A 5% effect was detectable on both. So n was only partly adequate.
- **The −20.76% null-B pair.** It was the first process of the campaign, and the baseline was the slow member. Its canary read 1.6055: under the ceiling, but the highest of all 112 valid processes. Conditioning ran at a normal 0.943×. The slowdown decayed across reps (1.42×, 1.41×, 1.24×) and was 1.03× on the final search. Non-engine overhead (the numpy table fill) also ran 1.30× slower. The committed attribution ("JIT code placement, not interference") is **contradicted**. The cause is not determinable. The data fit a transient external disturbance that an L1 canary is largely blind to.

## 3. Positive control — construction and calibration chronology

1. **`e41714a`, frozen:** the strength would be "chosen on a separate development sample and frozen in the commit that follows… targeting ≈5% slowdown".
2. **Calibration** (seed 777, 4 pairs each, the *same 16 corpus-A positions* as the powered control):
   - `pc_x16`: +0.86, +9.01, +0.75, −3.55 (median +0.81%).
   - `pc_x24`: −4.41, −4.89, −5.84, +3.32 (median −4.65%, faster in 3 of 4 pairs).
   - One attempt was voided (baseline canary 2.046) and re-run in its cell. DESIGN and REPORT say "clean on every process" and leave it out.
3. **`8a7459c`: the frozen selection rule was rewritten after the calibration data existed.** `pc_x24` was "frozen on that mechanism argument, not on the calibration deltas". The argument extrapolated "C24 measured the 4-step chain at ~1%" to 24 steps ≈ 5–6%. C24 never measured 1%. It measured +0.46%, 95% CI [−0.93, +2.14], not detected; the "~1%" was a guess.
4. **The powered control was then run expecting to fail.** `analyse.py` already contained the "measured FASTER" branch before any positive-control data existed.

**DESIGN VIOLATION RECORDED.** Fix 3's frozen selection rule was replaced after calibration. The change was disclosed, came before any control data, and moved no threshold. The control was never calibrated to about 5%, and the development sample was not separate positions. It has not been repaired or rerun.

**Powered result.** n = 16, 1 void (test canary 1.724, re-run in its cell). HL −7.72%, exact 95% CI [−9.17, −6.22], 16 of 16 pairs faster, p = 3.05e-5 (reported as 0.0000). **The frozen gate FAILS.** The search tree is identical on all 8 fingerprint counters. `CTL[15]` is in bounds and never read.

## 4. Corrected interpretation of `pc_x24`

`negamax` machine code, compiled and inspected only (nothing timed):

| build | instructions | imul/mul | call sites | net movq | stack refs |
|---|---:|---:|---:|---:|---:|
| baseline | 15,516 | 90 | 944 | — | 6,911 |
| pc_x4 | 15,477 | 94 | 931 | −38 | 6,896 |
| pc_x24 | 15,513 | 114 | 930 | −40 | 6,876 |

- **The chain survived.** Exactly +24 `imull` and +24 `addl`, one pair per source step, narrowed to 32 bits with the masks removed. "24 extra dependent multiplies" is true, but per `negamax` call, not per interior node.
- **But the insertion changed code generation throughout `negamax`.**
  - Call sites fell 944 → 930. All are register-indirect, so the callees can't be identified.
  - There are 40 fewer `movq` and 35 fewer stack references, and the net instruction count fell.
  - Register assignment was reshuffled across the whole function: calls through `%rdi` went 34 → 106 and through `%rbx` 161 → 89.
  - Even the 4-step version removed 13 call sites.
- **The effect tracks `negamax` call density.** This is exploratory, within-data evidence. `pc_x24`'s effect scales at −74.8 ns per call; `pc_x24` minus null is −54.1 ns per call (95% −83.6 to −20.8). That fits an edit that lowered `negamax`'s per-call cost.
- **The magnitude depends on the session:** −4.5% in calibration against −7.7% powered (p ≈ 0.01).

**So `pc_x24` is not a clean positive control.** It is a codegen-confounded edit that is not guaranteed to run slower. Its failed detection is not evidence that the harness lacks power; on corpus A it could resolve about 2%.

The data license one thing: a tree-preserving edit at the top of `negamax` shifted measured search time by about 5–8%.

**Claims withdrawn from the committed REPORT:**
- that a positive control is "not constructible" and "any injection reshapes the code" — a generalisation from one insertion site;
- "layout 8–11% vs ≈5% cost" — neither number was measured, and they contradict each other (a 5% cost implies −12.1%);
- "strictly more work" — true at source level only;
- "all three fixes worked" — Fix 3 was not achieved;
- "power was never binding" — false for the null gate;
- the "JIT placement" attribution of the null-B outlier;
- "unchanged by any arm" — `pc_x24` compile time was +4.1% and working set +0.45%, in 16 of 16 pairs;
- "exact" CIs — they are anti-conservative;
- p = 0.0000.

## 5. Is any candidate timing scientifically usable?

**No.**
- `pvs_cascade_single_callsite` was never timed.
- Even if it had been, a usable number was impossible. The null gate failed, and `pc_x24` shows that an incidental edit shifts timing by 5–8%, the same size as the effect a candidate would need to show.
- **The static evidence stands but is weaker than stated.**
  - The tree is identical: 62 positions, 14,328,759 nodes.
  - `negamax` went 15,516 → 15,268 instructions and 6,911 → 6,639 stack references, a real structural change.
  - Call sites went 4 → 1, not 3 → 1.
  - Executed calls per move are unchanged. The stage loop still makes 1–3 calls, each passing all 21 arguments, so the saving is code size, not executed stores.
  - The automated "code differs" gate cannot fail: a fixed residual appears in seven untouched functions for every variant.

## 6. Final C25 verdict

**FAILED — BENCHMARK UNVALIDATED** (the frozen label is BENCHMARK STILL TOO NOISY).

- The frozen null gate failed on both corpora, so this stands regardless of how the positive control is interpreted.
- The positive control separately failed its frozen gate. It is also recorded as an invalid construction with a Fix-3 design deviation.
- No candidate was timed, and none would be usable.

## 7. CODEGEN LANE: **CLOSED**

Nothing in the committed evidence passed its original frozen gates. There will be no C26, no redesign and no further campaign, and `pvs_cascade` stays untimed.

## 8. Recommended next route

**B — close codegen and consider C22's preserved START_FRACTION 0.50.**

- It is the only prepared candidate whose deterministic gates passed.
- It targets a measured structural inefficiency: C20 found RC-J uses 59% of its soft time and leaves about 55 s unspent over 40 moves.
- Its remaining question, strength, needs a paired arena, and that needs your explicit instruction.
- Temper expectations. C26 found that +1 or +2 depth repaired none of the diagnosed public failures; their cause is evaluation misjudgement of 75–415 cp.
- The evidence-backed alternative is evaluation tuning on held-out positions (C26/C27).
- 0.50 must never be combined with any other change.
