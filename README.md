# ClaudeShark

An entry for the [AI Chessathon](https://aichessathon.com): an iterative-deepening
alpha-beta chess engine in Python, over `python-chess`.

```bash
uv sync                                     # set up
uv run python -m pytest -q                  # correctness tests
uv run python -m tools.bench --depth 6      # deterministic search benchmark
uv run python -m tools.attribute --depth 6  # which search features pay
uv run python -m tools.tactics --ms 1000    # are the moves any good
uv run python -m harness.package            # build submission.zip

# Strength gate: candidate vs the frozen champion, at a competition-scale
# per-move budget. Do not speed this up by lowering the time control.
CS_INCREMENT_MS=200 uv run python -m tools.arena --opponent champions/v0_2 \
    --games 120 --base-ms 20000 --increment-ms 200 --ply-cap 200
```

Two rules this repository learned the hard way, both documented in
[BENCHMARKS.md](BENCHMARKS.md): **an A/B time control must produce a per-move
budget in the competition's range**, and **a change validated only at fixed
depth has not been validated for time-limited play**.

`agent.py` is the submission: one function, `get_move(fen, time_left_ms) -> str`.
Everything else it needs lives in the `cs_*` modules beside it.

See [PROJECT.md](PROJECT.md) for the competition constraints, the architecture
and the testing methodology, and [BENCHMARKS.md](BENCHMARKS.md) for the measured
record of every version.

`harness/` and `baselines/` are vendored unchanged from the official
[starter repository](https://github.com/advitrocks9/aichessathon-starter)
(MIT, see `THIRD_PARTY_LICENSE`) so local games are played under the same clock
and the same protocol as the platform.
