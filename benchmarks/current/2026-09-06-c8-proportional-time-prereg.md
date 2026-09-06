# C8 — proportional capped time allocation (pre-registered 2026-09-06 13:50 UK, before any measurement)

| field | value |
|---|---|
| CANDIDATE | C8-proportional-time: `CS_TIME_PROP=1` — the soft budget is a fixed fraction of the remaining clock plus a constant, capped, replacing the moves-to-go formula (branch `kushagra/c8-proportional-time`, on top of C5) |
| BASELINE | C5 (`champions/c5_rfp`) |
| HYPOTHESIS | C5 ends games with a median **42.7 s of its 120 s unused** (p10 12.2 s, min 6.5 s in the 2400 baseline) and spends 3.1 s median at a full clock against AlphaFish's public 3.9 s; the unused third of the clock is depth never bought. The audit shows depth repairs errors (46 of the 120 largest 2300 errors at one or two more plies) and C4 measured +0.46 ply for +44% time. A proportional, capped allocation spends more while the clock is full and tapers smoothly, converting the unused clock into depth on every move without the early-iteration gamble of the rejected `START_FRACTION` variants. This is the public behavioural hypothesis from the AlphaFish study, not a claim about its implementation |
| TARGET ERROR CLASS | TACTICAL HORIZON and ROOT INSTABILITY (depth-repairable), 46 of 102 flips in the 2400 audit |
| TARGET LOW-ACCURACY GAMES | the games whose flips are in those classes (13 of the 20 worst) |
| TARGET RESULT-FLIPPING POSITIONS | none singled out — a time policy is judged on games, not replays (C4 showed replays of a time change reward only the +time itself) |
| EXPECTED GENERAL BENEFIT | +0.3 to +0.5 ply mean depth at the competition clock; fewer >= 100 cp errors; non-negative internal strength |
| EXPECTED ACCURACY BENEFIT | fewer games below 98 and a higher minimum than C5 on the same 60 internal positions; on the 2400 screen a >= 100 cp rate below 6.54% |
| EXPECTED SPEED COST | none per node |
| EXPECTED CLOCK COST | final clock median falls from ~43 s towards ~20 s; the floor must stay above 4 s and no flag may occur; largest single think must stay under the current hard cap (18 s observed) |
| MATCHED NEGATIVE CONTROLS | the clock ladder (1 ms..120 s, nothing over hard); the 240-suite is not informative (fixed 3,000 ms); the opponent's side of the internal screen is the paired accuracy control |
| REJECTION CRITERION | any of: fingerprint changes (it must not — fixed depth ignores the clock); a test fails; clock ladder fails; any flag or a clock floor below 4 s in either screen; internal 60-game screen vs `champions/c5_rfp` below 48%, or with more games below 98 accuracy than C5's side; external 60 games vs benchmark 2400 with a >= 100 cp rate above 6.54% or a minimum accuracy below 83.6 |
| MAX USEFUL TIME | 20 min implementation + Gate 0; screens 60 + 60 games (~110 min) |
| SWITCH | `CS_TIME_PROP` (declared time variable; 0 = C5). Constants fixed now: realised-spend target 0.033 × clock + 0.19 s, cap 4.4 s. Because iterations start only while `elapsed < START_FRACTION × soft` and the last iteration overruns, C5's realised spend is about 0.65 × soft; the soft budget is therefore set to `min(6.8 s, 0.051 × clock + 0.29 s)` so that the realised spend lands near the target. Hard = `min(0.33 × usable, 3 × soft)` as before; panic and reserve unchanged |

## Mechanism (exact)

In `cs_time.TimeManager.begin`, when `TIME_PROP` is on and the clock is not
in panic: `soft = min(PROP_CAP_MS, PROP_SLOPE * time_left_ms + PROP_INTERCEPT_MS)`,
`hard = min(usable * MAX_SHARE_OF_CLOCK, soft * 3.0)`, `soft = min(soft, hard)`.
`should_start_iteration`, the hard deadline check, panic and the reserve are
unchanged. Fixed-depth and fixed-budget searches never touch this path.

## Gate plan

* Gate 0: fingerprint 1,409,912 with the switch on and off; full suite;
  `tools.clockladder` with the switch on.
* Gate 1: none applicable beyond the ladder (recorded as such); the
  realised spend-by-clock-band curve is measured from the screens' clock
  traces and compared with the target.
* Gate 2A internal: 60 games vs `champions/c5_rfp`, strict, dev set, accuracy on both sides.
* Gate 2A external: 60 games vs Stockfish UCI_Elo 2400 strict on dev2400, accuracy.

## Gate 0 — PASS (13:52–13:58 UK)

Fingerprint 1,409,912 with the switch on and off; 1,228 tests; clock ladder
with the switch on PASS 1 ms..120 s (worst 3.8 s at 120 s). Snapshot
`champions/c8_prop` = the C5 files with `TIME_PROP_DEFAULT = "1"`.

## Gate 2A internal — 60 games vs `champions/c5_rfp` (strict, dev set), 13:38–14:23 UK

**+21 =17 −22, 49.2%** (−6 Elo), 30 families / 20 informative, bootstrap
38.3%..60.0%, LOO −18..+6, White 53.3% / Black 45.0%, 0 failures; clock
floor 8.0 s (C5 8.4 s), largest think 15.6 s (C5 9.3 s), median final clock
18.3 s (C5 24.7 s). Realised spend by clock band (median seconds; target in
brackets): 100–121 s **4.04** (4.15) vs C5 3.02; 60–100 s 2.81 vs 2.24;
30–60 s 1.61 vs 1.51; 15–30 s 0.93 vs 0.92 — the policy does what it was
designed to do: it moves time to the full-clock phase and converges to C5's
curve below 30 s. Strength: flat within noise (bar: not below 48% ✓).
Accuracy on both sides (the paired control) decides; annotation running.
