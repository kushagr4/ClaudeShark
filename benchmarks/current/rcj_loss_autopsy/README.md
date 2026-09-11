# RC-J real-loss autopsy — final, accepted

Engine under study: RC-J, source `2bf6885`. Diagnostic only: nothing in this
directory changes engine behaviour. The autopsy was accepted on review;
engine development is frozen.

## Final conclusion

| | |
|---|---|
| RC-J R76–R105 | **30 games, 10W 6D 14L, 13.0/30 = 43.3%** |
| First decisive errors | **14**, of **57–158 cp** after final verification (Stockfish, 10M nodes) |
| First decisive errors repaired by +1 ply | **0 / 14** |
| Broader serious-error set | **19** |
| Repaired by deeper RC-J | **3** (R81 m8 at +1; R99 and R103 at +2) |
| Result flips repaired | **2 / 18** |
| ≥300 cp errors repaired | **0 / 2** |
| C22 START_FRACTION 0.50 | **LOW VALUE**: its extra iteration does not repair the demonstrated losing decisions |
| Dominant observed weakness | quiet early-to-middle middlegame positional misjudgements |
| Causal evaluation feature | **none isolated** strongly enough to justify a last-minute patch; after adversarial review **8 of 14** decisive losses remain **UNKNOWN** |
| Final candidate decision | **D — KEEP RC-J** |

The UNKNOWN categories are deliberate. Stockfish disagreeing with a move, or
deeper RC-J search failing to repair it, is evidence against a simple horizon
failure. It is not proof of an evaluation error, and no category here is
promoted to one without its own measured support.

## Method in brief

- **Inventory.** 30 contiguous RC-J games, R76–R105, all terminated and with
  consistent terminations (`data/inventory.json`, PGNs in `pgn/`). R94–R105
  were fetched read-only from the public team page. R69–R75 are RC-I and are
  excluded.
- **Reference.**
  - Stockfish binary sha256 `c86215fa1977d53b…`, the same binary as C26; it is
    not included here. One thread, and a fresh `game` tag per analysis, so there
    is no persistent hash.
  - The played move is scored by a root-restricted search from the same root as
    the best move. A played move equal to the engine's own choice scores 0,
    which avoids same-move phantom losses.
  - The last *exact* info line is used, and scores are taken from RC-J's point
    of view.
- **Categories.** From Stockfish's WDL expectation E: win at E ≥ 0.75, loss at
  E ≤ 0.25, otherwise draw.
- **First decisive error (frozen rule, `scripts/analyse_scan.py`).** The
  earliest result flip after which RC-J never regains the pre-flip category.
  When the decline is gradual, it is the largest drop in E made while RC-J was
  not yet lost.
- **Verification.** Every decisive position is re-verified at 10M nodes
  (`data/verify*.json`).
- **Depth test.** RC-J (shipped core, via the trace driver) is run from a cold
  table at its recorded clock and at fixed depths d, d+1 and d+2. RC-J's own
  value of the played move and of the best move is recorded too. Frozen
  classification (`scripts/repair.py`): GOOD ≤ 30 cp, BAD ≥ 40 cp. A case is
  STATE-DEPENDENT when the cold search does not reproduce the live move.
- **Causes.** Seven read-only agents classified each loss from measured
  evidence (`data/bundles/`). Three adversarial reviewers then corrected
  categories, clusters and the timing verdict (`data/classification.json`,
  `wf/`).

## Files

| path | contents |
|---|---|
| `REPORT.md` | the full accepted report: loss table with FENs, depth summary, clusters, timing verdict, RECORD THIS |
| `data/inventory.json` | the 30-game R76–R105 inventory |
| `data/scan_all.jsonl` | isolated Stockfish scan of every RC-J move in the 14 losses (925 moves) |
| `data/decisive.json` | first decisive error per loss |
| `data/ladder.json`, `data/ladder_sup.json` | RC-J cold depth ladders |
| `data/verify.json`, `data/verify_sup.json` | Stockfish 10M verification |
| `data/repair.json` | deterministic depth-repair classification |
| `data/dossier.json` | per-position feature evidence (material swings, king zone, mobility, pawns, unshipped terms) |
| `data/classification.json` | agent classifications and skeptic corrections |
| `data/bundles/` | per-loss evidence bundles |
| `pgn/` | game PGNs |
| `scripts/` | the pipeline: `sf_scan.py`, `analyse_scan.py`, `rcj_ladder.py`, `sf_verify.py`, `repair.py`, `dossier.py`, `stage2.py`, `stage3.py`, plus `make_trace_driver.py`, which generates the trace driver `rcj_ladder.py` imports |
| `wf/` | classification and skeptic working scripts and outputs |

## Reproducing

The scripts hard-code the session paths they ran from: the RC-J worktree
holding the generated `cs_fast_trace.py`, and its `.venv` Python. Edit those
constants, generate the trace driver with `make_trace_driver.py` in an RC-J
(`2bf6885`) tree, then run `stage2.py` followed by `stage3.py`. Results depend on
Stockfish's node-limited search and are reproducible to within its
nondeterminism at the stated node counts.
