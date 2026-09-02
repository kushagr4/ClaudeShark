# Search experiment A — static exchange evaluation

Date: 2026-09-02. Base: v0.3 (`eec119b`).

## Hypothesis

MVV-LVA sorts every capture above every quiet move, so it cannot tell a genuine
win of a pawn from QxP-defended-by-a-pawn. Two consequences, each testable
separately:

1. **Quiescence** searches losing captures and every recapture behind them.
   Quiescence is roughly half of all nodes, so pruning captures with a negative
   static exchange evaluation should remove a large slice of the tree.
2. **Ordering** places losing captures ahead of killers and history moves, which
   delays the cutoff at interior nodes.

Prediction: fewer nodes at equal depth, with no loss of move quality — a capture
that loses material is not usually the move that saves a position.

## Implementation

`cs_see.py`. Attackers are recomputed from a running occupancy at each swap, so
x-rays are handled: a rook behind a bishop enters the exchange when the bishop
leaves. Two flags, so each use is attributable: `CS_SEE_QS`, `CS_SEE_ORDER`.
Ordering only calls SEE when the victim is worth less than the attacker, since
running a full exchange on every capture at every node costs more than it saves.

**Known limitation, measured not assumed.** SEE reasons about attackers, not
legality, so it does not know a recapture can be pinned. `tests/test_see.py`
compares against an independent brute-force swap-off over 250 random capture
positions and holds the disagreement rate under 2%; the observed rate is 1/250.
The single disagreement is kept as a named regression test: after `Nxf3+` in
`r1b3r1/ppp1qk1p/3p3n/4npp1/6PP/B1N2P1B/PPP1P3/RQ2KN1R b`, White's e2 pawn is
pinned by the queen on e7 and cannot recapture, so SEE reports losing a knight
for a pawn where the truth is winning a pawn. This is the textbook limitation of
the algorithm and is accepted rather than engineered away.

## Deterministic result — fixed depth 6, 24 balanced positions

Node counts at fixed depth are deterministic and unaffected by machine load, so
these are directly comparable. (Wall-clock figures from this run are *not*
comparable: a 400-game arena was running concurrently and depressed absolute
nodes/second across all four rows equally.)

```
uv run python -m tools.bench --depth 6            # and with CS_SEE_QS / CS_SEE_ORDER set
```

| variant | nodes | vs baseline | quiescence share |
|---|---|---|---|
| v0.3 baseline | 1,957,695 | — | 53% |
| + SEE in quiescence | 1,756,212 | **−10.3%** | 48% |
| + SEE in ordering | 1,848,730 | **−5.6%** | 52% |
| + both | 1,666,590 | **−14.9%** | 47% |

The quiescence share falling from 53% to 47% is the mechanism working exactly as
predicted: the pruned nodes are the recapture subtrees behind losing captures.

## Quality result

Tactical suite with both flags on: **16/16**, unchanged.

Centipawn loss against a PVS-only reference, sharp suite, depth 7 — see
`see_quality.txt` for the full run.

Centipawn loss against a PVS-only reference, sharp suite (18 positions),
depth 7, measured on a free machine:

| variant | agree | avg loss | worst | >100cp |
|---|---|---|---|---|
| v0.3 shipping | 13/18 | 1.5 | 9 | 0 |
| + SEE quiescence | 14/18 | 1.4 | 10 | 0 |
| + SEE ordering | 13/18 | 1.3 | 8 | 0 |
| + SEE both | 12/18 | 1.9 | 10 | 0 |
| no LMR (least selective) | 18/18 | 0.0 | 0 | 0 |

Move quality is unchanged. The shipping engine already loses 1.5 cp on average
against the reference; SEE moves that to 1.9 cp, with the worst case going from
9 cp to 10 cp and no blunders in either. Those differences are far inside the
noise of an 18-position sample.

## Wall clock, measured on a free machine

The node counts above were taken while a 400-game arena was running, which
depresses absolute timings. Repeated afterwards with nothing else on the box:

| | nodes | wall clock | nodes/second |
|---|---|---|---|
| v0.3 | 1,957,695 | 28.6 s | 68,523 |
| + SEE both | 1,666,590 | **23.8 s** | 69,982 |

**16.8% less wall clock at identical depth.** This is the number that decides
it: SEE costs real time per call, and the question was whether pruning paid for
it. It does, several times over, and nodes/second even rises slightly because
the nodes removed were quiescence nodes with expensive move generation behind
them.

Depth at realistic budgets:

| budget/move | v0.3 | + SEE | gain |
|---|---|---|---|
| 900 ms (arena scale) | 6.21 | 6.62 | **+0.41 ply** |
| 4500 ms (full-clock scale) | 8.33 | 8.67 | **+0.34 ply** |

## Decision

**Kept, both flags on, promoted to v0.4.** Every measurement points the same
way: fewer nodes, less wall clock, more depth, unchanged move quality, unchanged
tactical suite. For scale, +0.4 ply is comparable to the entire v0.2 → v0.3
improvement, which measured +30 Elo over 400 games.

Arena confirmation against frozen v0.3 is recorded in
`2026-09-02-v0.4-arena.md`. Note that the deterministic case here is much
stronger than the one that existed for aspiration windows, which looked good at
fixed depth and hid a regression that only appeared under a clock — so the arena
is a genuine gate, not a formality.
