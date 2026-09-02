# ClaudeShark

An entry for the [AI Chessathon](https://aichessathon.com): an iterative-deepening
alpha-beta chess engine in Python, over `python-chess`.

```bash
uv sync                                  # set up
uv run python -m pytest -q               # correctness tests
uv run python -m tools.bench             # search benchmark
uv run python -m tools.arena --opponent baselines/minimax --games 24
uv run python -m harness.package         # build submission.zip
```

`agent.py` is the submission: one function, `get_move(fen, time_left_ms) -> str`.
Everything else it needs lives in the `cs_*` modules beside it.

See [PROJECT.md](PROJECT.md) for the competition constraints, the architecture
and the testing methodology, and [BENCHMARKS.md](BENCHMARKS.md) for the measured
record of every version.

`harness/` and `baselines/` are vendored unchanged from the official
[starter repository](https://github.com/advitrocks9/aichessathon-starter)
(MIT, see `THIRD_PARTY_LICENSE`) so local games are played under the same clock
and the same protocol as the platform.
