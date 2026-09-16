# Optional NNUE in the engine (`CS_NNUE`)

Added 2026-09-16. `cs_core.py` and `cs_fast.py` can add the frozen **N1-U** network to the evaluation
the search uses, incrementally. It is **off by default**: with `CS_NNUE` unset the engine is RC-J
(`2bf6885`) node for node, and nothing ships or plays differently.

**Status: research-only.** N1-U was rejected as an evaluator on its own evidence
(`benchmarks/current/learned_eval/REPORT_N1.md`): it failed the magnitude audit, the balanced-position
gate G2 and the after-quiescence gate G3, and it runs at roughly 0.43× RC-J's speed. Putting it behind
a flag makes it available for experiments; it does not change that verdict, and no games have been
played with it.

## Using it

```bash
CS_NNUE=1 uv run python -m tools.bench --depth 8          # the engine with N1-U added
CS_NNUE=1 CS_NNUE_VERIFY=1 uv run python -m tools.bench --depth 6   # plus an exactness check at every evaluation
```

| variable | default | effect |
|---|---|---|
| `CS_NNUE` | unset (off) | `1` adds N1-U's correction to the search evaluation |
| `CS_NNUE_VERIFY` | unset (off) | with `CS_NNUE=1`: compares the incremental accumulator with a from-scratch rebuild at every evaluation and counts mismatches in `Searcher.NNA[cs_core.N1_CTRL, 4]` (slow; for testing) |
| `CS_NNUE_WEIGHTS` | the frozen file | another `.npz` with N1's quantised layers (`W1q b1q W2q b2q w3q b3q`, exact shapes and dtypes are enforced) |

Both flags are read once, when `cs_core` is imported, and compiled in as constants: change them only
between processes. The default weights are `benchmarks/current/learned_eval/results/n1/n1_weights.npz`,
checked against its frozen SHA-256 (`b1b809b7…1da201`) at import. That file is not part of a
submission archive, so an extracted release run with `CS_NNUE=1` stops at import with a clear error
unless `CS_NNUE_WEIGHTS` points at the weights; with the flag off nothing is loaded.

## Design

* `evaluate(B, S)` is untouched, so every other caller (tools, the learned-evaluation and C28 scripts,
  tests) still gets RC-J's evaluator whatever the flag.
* The search's five evaluation sites in `quiescence` and `negamax` call
  `evaluate_search(B, S, U, NNA, NNK)` = `evaluate(B, S)` plus, when enabled, `n1_eval`.
* `NNA` (int32, `STACK + 3` rows × 256) holds one accumulator row per ply, White's 128 units then
  Black's; `NNK[ply]` is the Zobrist key the row was built for, so a row is reused only for that exact
  position. Both are threaded through `search_root`, `negamax` and `quiescence` and allocated by
  `cs_fast.Searcher` whatever the flag, so the compiled search has a single signature.
* An evaluation catches up from the nearest valid ancestor by replaying moves from the undo stack
  (`make_move` records the moved piece in `U[ply, 7]` when the flag is on); `search_root` seeds the
  root row once per root search, so the search never rebuilds from the bitboards otherwise.
* The kernels (`n1_add`, `n1_rebuild`, `n1_apply`, `n1_ensure`, `n1_eval`, `n1_verify`,
  `n1_seed_root`) are the ones verified in the N1 stage's scratch engines
  (`learned_eval/scripts/engine_n1.py`), unchanged apart from comments and dropping the audit mode.

## Evidence

`scripts/verify_nnue.py` produced `results/verify_nnue.json`. RC-J is rebuilt from commit `2bf6885`
with `git archive` into a temporary directory; every engine run is a separate process, one at a time.

Run of 2026-09-16 on the Windows development machine (AMD Ryzen 5 5600X), all checks **passed**;
the input hashes recorded in the JSON (text sources LF-normalised) did not change during the run.

| check | result |
|---|---|
| **identity**, flag unset vs RC-J at depth 10 on the 24 balanced openings | **16,818,635 = 16,818,635 nodes** (RC-J's recorded fingerprint); moves identical 24/24; completed depths identical; NNUE counters all 0 |
| **in-search shadow verification**, `CS_NNUE=1 CS_NNUE_VERIFY=1`, depth 10 on the openings | 22,560,120 nodes, 13,247,205 evaluations, **0 mismatches**; rebuilds 250 = root seeds 250 |
| same, 60 plies of self-play at depth 5 without `new_game` | 870,404 evaluations, **0 mismatches**; rebuilds 326 = root seeds 326 |
| **random make/unmake walk**, 400 playouts plus the special positions | 19,075 transitions, **10,194 exact checks** (accumulator = rebuild, correction = independent numpy forward pass, `evaluate_search` = `evaluate` + correction), 0 failures; every kind covered: 5,599 captures, 48 en passant, all four castles (31–45 each), all four promotions (30–39 each), 2,604 king moves, 912 null moves, 2,779 unmakes, 3,596 multi-ply catch-ups |
| **speed**, flag unset vs RC-J, depth 10 (identical trees), 3 ABBA rounds | flag-off/RC-J NPS ratio per round 1.0035, 1.0691, 1.0070; median **1.007** — no measurable cost (the flag-off build is not slower) |
| null control, RC-J vs a second RC-J copy | per-round 0.9963, 1.0073, 1.0339; median 1.0073, within ±2%: block **VALID** |

With the flag on, N1-U chooses a different move from RC-J in 12 of the 24 openings at depth 10.
That is a description, not a strength claim: no games were played.

Speeds are whole-search wall time and include the Python root work both engines share. On this
machine a single round can move by several percent, which is why the verdict rests on the median
and the null control rather than on any one run.

`tests/test_nnue.py` keeps a lighter version of these checks in the regular suite: the flag is off by
default, verify needs the flag, the frozen network loads with the right types and bad weights are
refused, a default search never touches the NNUE state, a random walk of over 2,000 transitions is
exact, a search with verification on has zero mismatches and rebuilds equal to root seeds, and the
shipped modules still pass `tools/release_check.py`'s source scan.

Reproduce:

```bash
uv run python benchmarks/current/nnue/scripts/verify_nnue.py --speed --rounds 3 --walks 400
CS_NNUE=1 uv run python benchmarks/current/nnue/scripts/accumulator_walk.py --walks 400
uv run python -m pytest -q tests/test_nnue.py
```

## Effects on other tools

* **Direct callers of the search kernels** must pass two more arguments, `NNA, NNK`, straight after
  `GAINS`: `tests/test_core.py`, `tests/test_core_rules.py`, `tools/review_c9_repro.py` and
  `benchmarks/current/learned_eval/scripts/test_evalkit.py` were updated.
  `benchmarks/current/c12_mate/trace.py` was deliberately left as it was: it is historical, runs
  against a build directory named on its command line and reads a PGN from a scratch folder that no
  longer exists, so run it against a pre-NNUE build.
* **The N1 stage's own scripts** read the live tree: `learned_eval/scripts/engine_n1.py` (used by
  `n1_engine_checks.py` and `audit_n1.py`) builds its scratch engines by patching the live
  `cs_core.py` by exact text, and `speed_n1.py` takes the live tree as its RC-J reference. Their
  SHA-256s are part of N1's frozen record (`results/n1/freeze.json`), so they were not edited; the
  builder now stops with an assertion on this tree. To reproduce N1's evidence, run them from an
  extraction of a pre-NNUE commit, for example `git archive 459711e | tar -x -C <dir>`.
* **Migration tooling** (`migration/`): the runtime-identity checks now expect `cs_core.py` and
  `cs_fast.py` to differ from `2bf6885` and every other production module to match it, and they
  confirm that the flag reads as off with `CS_NNUE` unset.
* **Packaging and release checks** are unchanged: the submission archive contains the same modules,
  no weights, and the source scan still finds no file-open or write calls.
