# ClaudeShark

**Current state (2026-09-06 21:07 UK):** the submitted build is **RC-F**
(`corpus/release/claudeshark_rc_f.zip`, SHA-256
`4ee4033e509bf8709d7d1090037d0aeb6b146da375c88f9986cb1a67789df13d`, engine
commit `b7f42cf`, frozen snapshot `champions/rc_f`). RC-F is also the
development champion: every new candidate starts from `champions/rc_f` and is
measured against it. Primary goal: a top-3 Chessathon finish. Next: the
friend's independent review, Astra's independent audit, then the highest-EV
candidate from RC-F. **`spec.md` is the source of truth** for the submitted
build, the champion, open lanes and active jobs; `benchmarks/current/` holds
the current-programme records (`STRENGTH_LADDER.md`, `V2_ACTIVE_STATE.md`,
the RC-F boundary and evening-review records).

Where things live: engine source at the repository root (`agent.py`, the
`cs_*` modules; `cs_core.py` + `cs_fast.py` are the Numba search core);
frozen builds in `champions/`; release archives in `corpus/release/`; tests
in `tests/`; tooling in `tools/`; match and audit evidence in
`corpus/strength/`.

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
