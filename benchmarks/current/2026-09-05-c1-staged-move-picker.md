# C1-search-staged: lazy move picker at interior nodes

**Date:** 2026-09-05 (Mac, Apple M4, Python 3.12.14, python-chess 1.11.2).
**Base:** RC-A / exact rated-v1 (`champions/rated_v1`, commit `98c48c8`).
**Change:** `cs_search._negamax` takes its moves from `cs_ordering.staged_moves`
behind `CS_STAGED_MOVES` (shipping default **off** until promoted). The picker
yields the table move, then the captures that are not losing (MVV-LVA), then
the killers, all from masked generation, and only builds and sorts the full
legal list if the search asks for more. A side with a pawn on its seventh
rank (promotions available) falls back to `order_moves`. Nothing else in the
search changed; the flag off is byte-for-byte RC-A behaviour (fingerprint
1,712,405 reproduced on this machine, all 1,204 tests + 1 skip pass).

## Gate 0

The handoff asked for an *identical* tree. It is not identical, and the
reason is structural, not a bug: `order_moves` reads history for the quiet
tail once, at node entry; the picker reads it when the tail is reached, after
the head moves' subtrees have run, and grandchild cutoffs update this side's
history in between. A diagnostic that wrapped the picker with an entry-time
snapshot over the 24-position depth-6 suite found

| staged nodes | tails that diverged from the entry-time order | explained by refreshed history | unexplained |
|---|---|---|---|
| 133,487 | 93 (0.07%) | 93 | **0** |

so the picker reproduces the sort exactly and the only difference is fresher
history at the tail. Making it identical would need a per-node copy of the
4,096-entry history half, which costs about what the picker saves; not worth
it for 0.07% of nodes. C1 is therefore a near-identical-tree speedup and was
gated as a search change: root moves and tactics as well as node counts.

| measurement | flag off (RC-A) | flag on (C1) |
|---|---|---|
| 24-position suite, depth 6, nodes | 1,712,405 | 1,708,269 (−0.24%) |
| root moves changed | — | **0 / 24** |
| knps, two alternated runs each | 118,487 / 118,942 | 138,501 / 139,684 (**+17%**) |
| wall at depth 6 | 14.5 s / 14.4 s | 12.3 s / 12.2 s (−15%) |
| sharp suite (18), depth 6, nodes | 1,850,917 | 1,852,716 (+0.10%) |
| sharp suite root moves changed | — | **0 / 18** |
| tactics, 1,000 ms per puzzle | 16/16, avg depth 8.00, 695,782 nodes | 16/16, avg depth 8.12, 717,719 nodes |
| full test suite | 1,204 passed, 1 skipped | 1,204 passed, 1 skipped |
| `tests/test_staged_moves.py` | 300+ random positions, random killers/history/table moves, with and without SEE: identical sequences | |
| ruff / mypy on `cs_search.py`, `cs_ordering.py` | clean (the 5 mypy errors in `cs_eval.py` pre-date this change) | |

Raw: `corpus/daily/time/gate0_c1staged.txt` (bench, sharp, tactics outputs).

The Windows opportunity map expected 10–20% NPS from this mechanism, on the
measurement that 79% of interior nodes cut on their first move and only 22%
have a table move; +17% on the M4 is inside that band.

## Timed screen (Gate 2 at the competition clock)

Launched 2026-09-05 (time in the log): `tools.arena --agent champions/c1_staged
--opponent champions/rated_v1 --games 226 --base-ms 120000 --increment-ms 500
--ply-cap 300 --workers 8 --corpus corpus/daily/pool/competition_actual_suite.jsonl
--set-env CS_STAGED_MOVES=1`. `champions/c1_staged` is the working tree frozen
at this commit. Against `champions/rated_v1` it carries the V2 term registry
(`cs_terms.py`, `cs_drawish.py`, `cs_kingpawn.py`, the registry hook in
`cs_eval.py`) with every term off, which is RC-A behaviour to the node
(fingerprint 1,712,405 with the flag off), plus the picker in `cs_search.py`
and `cs_ordering.py`. Only the candidate declares `CS_STAGED_MOVES`;
`rated_v1` ignores it, so the environment reaches one side. Output
`corpus/daily/time/games/c1staged_vs_ratedv1_120s.jsonl` + `.pgn`, risk report
by `tools.daily.swissrisk` to `corpus/daily/time/swissrisk_c1staged.txt`.

Pre-registered decision rule: freeze RC-B from this build only if the timed
screen is not negative (nominal Elo ≥ 0 or the bootstrap comfortably covering
0 with a clock floor no worse than rated-v1's) and there are no failures. A
same-strength result still promotes it as the new development base, because
the mechanism buys depth at zero evaluation change; a negative result closes
the lane and the flag stays off.

Result: appended when the match completes.
