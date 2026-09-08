# RC-I — C12 verified mate + C13 compiled mop-up + C14 real-history threefold

Baseline: C12 (`kushagra/c12-verified-mate-score`, `02705b1`). Current submitted
build remains RC-F (`4ee4033e…f13d`); nothing here has been uploaded.

## What went in, and what did not

| candidate | mechanism | verdict |
|---|---|---|
| C13 | compiled mop-up mating gradient, gated to a bare defending king with a rook or queen | **PASS**, integrated |
| C14 | score the threefold the engine's own move creates, from real observed history, at the root | **PASS**, integrated |
| C15 | exempt advanced quiet pawn pushes from late-move reduction | **REJECT** on cost |
| C16 | mating-net / quiet forcing-move awareness | not attempted, see below |
| C17 | selective effective depth | not attempted, see below |

C15 repaired 17 of 144 serious errors against 2 worsened and improved every
pre-registered set, but cost 8.5% nodes per second on an essentially identical
tree (+0.05% nodes at fixed depth). Rewriting the test to read the piece after
`make_move`, inside the branch that was about to reduce, made it worse (−15%),
so the cost is the compiled core reacting to the edit rather than the work
itself. Rejected under the gate's >5% rule and left for a cheaper
implementation.

C16 and C17 were not attempted. Both would have needed the same kind of
per-move test inside `negamax` that C15 has now twice shown to be expensive,
and C17's obvious mechanism, an instability-triggered time extension, is the
closed C4 lane. Attempting either today had low expected value against the
measured cost.

## Combined gate

| check | result |
|---|---|
| full test suite | **1,451 passed** |
| elementary conversion, 4 KRK + 4 KQK, depths 8/10/12/14 | **8/8** at 3-of-4 or better (C12 6/8), cells 31/32 |
| K+B+N control, outside the mop-up gate | unchanged, 1/4 both builds |
| 240 competition-like positions, fixed depth 8 | **0 root move changes, 0 score changes**, 1 node |
| tactics, 1,000 ms | **16/16** |
| clock ladder | **PASS**, worst 5.2%, zero overruns |
| nodes per second vs C12 | **−1.35%** |
| nodes per second vs RC-F | −4.6% |

## Strength against the submitted build

Two independent screens against frozen `champions/rc_f`, 120 s + 0.5 s, strict
claims, organiser start set, quiet machine.

| screen | result | score | Elo | interval |
|---|---|---|---|---|
| 30 games | +12 =11 −7 | 58.3% | +58 | bootstrap −47 .. +176 |
| 60 games | +21 =23 −16 | 54.2% | +29 | bootstrap −41 .. +95 |
| pooled 90 | +33 =34 −23 | **55.6%** | **+39** | intervals span zero |

Zero failures. Clock floor 2,915 ms. Colour split on the 60: White 48.3%,
Black 60.0%.

The class these features exist for: across both screens **18 games reached a
position where the opponent had only a king; 16 were converted to checkmate and
none was drawn by repetition or the fifty-move rule.**

## Archive

`corpus/release/claudeshark_rc_i.zip`, 66,552 bytes compressed, 200,210
unpacked, 16 files, snapshot `champions/rc_i`. SHA-256
`3bfe20b53891e468726fb1ae8461f568f510a6c82f7cc299b38abc5681749921`. Release
check 16 of 16 PASS. Fresh-extraction smoke under Python 3.12.13 with numba
0.67.0: 10/10 probes legal, import and warm-up 27.66 s inside the 90 s budget.

## Honest reading

Each screen's interval spans zero, so this is not a proven Elo gain. What is
proven is deterministic: conversion 6/8 to 8/8, sixteen bare-king endings mated
and none repeated, ordinary play bit-identical on 240 positions, and a 1.35%
speed cost. The published site metric puts ClaudeShark at 48.8 ACPL and 55
blunders against the Top 3's 17.8–23.2 and 8–20, so the remaining gap is
middlegame accuracy, which none of today's features addresses.
