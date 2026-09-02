# Position corpora

Everything the arena and the move-quality analysis start from, with the
evidence that each position deserves to be there. Built by the tooling in
`tools/corpus/`; nothing in this directory ships.

## Why this exists

`tools/positions.py` (corpus v2, 24 `BALANCED_OPENINGS` + 18
`SHARP_POSITIONS`) is proven legal, unique and non-terminal. It was never
calibrated: no position carried a label from anything but the engine under
test. `legacy_v2_calibration.md` is the first external calibration of it, and
the reason the two suites below were built.

The old suite is **not deleted or reordered**. Every historical arena record
names its corpus version and hash, and those records stay reproducible.

## The reference oracle

Tooling only. Never packaged, never imported by anything under the root
`cs_*` modules, and `tools/release_check.py` would reject a binary in the zip
anyway.

| | |
|---|---|
| engine | Stockfish 18, official release build `stockfish-windows-x86-64-avx2` |
| provenance | `https://github.com/official-stockfish/Stockfish/releases/tag/sf_18`; zip SHA-256 `6f6c272ebd6ea594…`, binary SHA-256 recorded in every label header |
| location | outside the repository (`C:\Users\epick\engines\stockfish\`), `ORACLE_ENGINE_PATH` overrides |
| settings | `Threads 1`, `Hash 256`, `UCI_ShowWDL true`, hash cleared before every position |
| limit | **fixed nodes**, never wall-clock: 1,000,000 nodes for pool screening, 4,000,000 for the legacy calibration, 1,000,000 per child when scoring the engine's moves |

Fixed nodes with a single thread and a cleared hash is reproducible: the same
binary returns the same score, move and PV for the same position on any
machine. `tools/corpus/oracle.py` verifies this on start-up in its tests.

## Source games

The Week in Chess (TWIC) issues 1500, 1520, 1540, 1560, 1580, 1600, 1620 and
1640 -- 61,459 master games spanning 2023 to 2026, kept outside the repository
(`C:\Users\epick\engines\twic\`, zip SHA-256s in the session record). Games
with both players rated 2300+ (2100+ for niche openings, which are rare at the
top) and at least 24 plies are eligible. Each game contributes at most one
position to a suite.

## Files

| file | what |
|---|---|
| `legacy_v2_calibration.{jsonl,md}` | every position of corpus v2 with its oracle label, structure and verdict |
| `candidates.jsonl` | the extracted pool: 6,203 positions from 4,563 games across 49 opening families, with provenance and structural tags |
| `candidates_labelled.jsonl` | the same pool with oracle labels at 1,000,000 nodes, multipv 2 |
| `competition_like_v1.{jsonl,md}` | **the strength-measurement suite**: near-level, not forced, diverse, one per game |
| `stress_test_v1.{jsonl,md}` | **the failure-finding suite**: imbalances, compensation, races, locked centres, classical endgame themes. Never part of a headline Elo |
| `analysis_*.{jsonl,md}` | ClaudeShark's oracle-judged move quality on a suite |
| `diagnosis_*.{jsonl,md}` | why each serious error happened: search, pruning, time, horizon or evaluation |
| `eval_residuals.md` | what the static evaluator is missing, as a regression against the oracle |

## Reproduction (Windows CMD, from the repository root)

```
uv run python -m tools.corpus.calibrate_legacy --nodes 4000000 --workers 8
uv run python -m tools.corpus.extract --pgn-dir C:\Users\epick\engines\twic --out corpus\candidates.jsonl --min-elo 2300 --niche-min-elo 2100
uv run python -m tools.corpus.label --in corpus\candidates.jsonl --out corpus\candidates_labelled.jsonl --nodes 1000000 --multipv 2 --workers 8
uv run python -m tools.corpus.build --labelled corpus\candidates_labelled.jsonl --sensitivity
uv run python -m tools.corpus.build --labelled corpus\candidates_labelled.jsonl --band 50 --max-gap 100 --max-dev 0.15 --size 240 --out-dir corpus
uv run python -m tools.corpus.analyse --suite corpus\competition_like_v1.jsonl --depth 6 --nodes 1000000 --workers 8 --out corpus\analysis_cl_v1_d6.jsonl
uv run python -m tools.corpus.diagnose --analysis corpus\analysis_cl_v1_d6.jsonl --min-loss 100 --max-depth 9 --ms 4500 --workers 6 --out corpus\diagnosis_cl_v1.jsonl
uv run python -m tools.corpus.eval_residuals --labelled corpus\candidates_labelled.jsonl --out corpus\eval_residuals.md
uv run python -m tools.arena --opponent champions\v0_5_1_correctness --corpus corpus\competition_like_v1.jsonl --games 480 --base-ms 20000 --increment-ms 200 --set-env CS_INCREMENT_MS=200 --jsonl benchmarks\current\<date>-<name>.jsonl
```

`tools.corpus.extract` needs the PGN files; everything after `label` needs
only the JSONL in this directory and, for anything that scores a move, the
oracle binary. `uv run python -m pytest tests\test_corpus_tools.py` checks the
suites without the oracle.
