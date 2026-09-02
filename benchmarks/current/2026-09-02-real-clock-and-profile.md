# Real-clock behaviour and updated profile

Date: 2026-09-02. Engine: v0.4 candidate (v0.3 + SEE).

## Whole games on 120 s + 0.5 s

```
uv run python -m tools.gamesim --games 2 --csv benchmarks/current/2026-09-02-clock-120-0.5.csv
```

Two full games, 234 plies, played with the referee's own clock arithmetic
(subtract measured wall time, then credit the increment). Per-ply detail in the
CSV beside this file.

| | |
|---|---|
| time per move | mean 2018 ms, median 1847 ms, max 7053 ms |
| soft budget used | 67.9% mean |
| depth | mean 7.59, max 12 |
| first half vs second half | 2183 ms vs 1853 ms per move |
| lowest clock at any point | **25,007 ms of 120,000 (20.8% remaining)** |
| hard-deadline overruns | **0** |
| panic-mode plies | **0** |

### What this says

**Flag risk: none observed.** The clock never fell below a fifth of its starting
value across 234 plies, no move exceeded its hard deadline, and emergency mode
never activated. The increment accounting is behaving: spending declines gently
through the game rather than collapsing, which is what a correctly credited
increment looks like.

**Mild front-loading, within reason.** 2183 ms per move in the first half
against 1853 ms in the second is a ratio of 1.18. That is the natural
consequence of allocating a share of the *remaining* clock and is not a defect.

**The engine is leaving time on the table.** Two figures say so: only 67.9% of
the soft budget is consumed on an average move, and the worst-case clock still
holds 20.8% of the original 120 s at the end of a 117-ply game. Roughly a fifth
of the thinking time available is never used.

The cause is not a bug. The iteration-start threshold (`START_FRACTION = 0.45`)
refuses to begin an iteration once 45% of the soft budget is gone, on the
reasoning that the next ply costs 2–4x the last. That is sound, but combined
with a moves-to-go estimate of 26 it compounds into a persistent underspend.

**Not acted on in this session, deliberately.** The obvious experiment is a
single-parameter change — raise `START_FRACTION`, or lower
`DEFAULT_MOVES_TO_GO` from 26 to around 22 — and it is worth perhaps 0.2 ply.
It is not being bundled with the SEE change under test: two changes measured
together is exactly the mistake that made the v0.2 attribution worthless. It is
the next isolated A/B.

## Updated profile

```
uv run python -m tools.profile_search --ms 3000 --positions 6
uv run python -m tools.profile_eval
```

21.479 s total, six positions at a 3 s budget. Percentages are cumulative time.

| area | share | ours? |
|---|---|---|
| legal move generation | **32.0%** | no — python-chess |
| `cs_eval.evaluate` | **18.0%** | yes |
| `push` / `pop` | **17.2%** | no — python-chess |
| move ordering | **13.2%** | yes |
| search overhead (`_negamax` itself) | 6.9% | yes |
| static exchange evaluation | 4.2% | yes |
| quiescence overhead | 1.9% | yes |
| transposition table | below the top 16 | yes |

Evaluator throughput: **256,628 evaluations/second, 3.90 µs each** (42
positions, 25.6 pieces on average).

### Does python-chess still dominate enough to justify migration?

**Yes, but no more than before, and the case has not strengthened.** Move
generation plus make/unmake is 49.2% of runtime, essentially unchanged from the
51% measured for v0.2 — the evaluator optimisation and SEE moved work around
inside our own 42% rather than changing the split.

The arithmetic that matters has not moved: making python-chess free would give
roughly 2x, which is about one ply. That is the ceiling on optimising around it,
and it is well short of what a full Numba rewrite would need to deliver to
justify its risk. Ordering is now the most attackable piece of our own code at
13.2%, having grown with the SEE calls added to it.

No rewrite is recommended. See `docs/MOVEGEN.md` for the full option analysis
and the perft-spike gate that any such decision should be held to.
