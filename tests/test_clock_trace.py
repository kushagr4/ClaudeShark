"""The referee records every side's clock, and the arena summarises it.

A time-policy change is only trusted once a match shows each side's lowest
clock and largest think, so the trace must be one entry per ply actually
played, alternate sides, and carry a clock that respects the increment.
"""

from __future__ import annotations

from pathlib import Path

from harness.referee import clock_summary, play_match
from harness.sandbox import local

ROOT = Path(__file__).resolve().parent.parent
GREEDY = ROOT / "baselines" / "greedy"


def test_play_match_traces_every_ply() -> None:
    outcome = play_match(local(GREEDY), local(GREEDY), 2_000, 100, ply_cap=6)
    trace = outcome.clock_trace
    assert outcome.termination == "adjudication"
    assert len(trace) == 6
    assert [entry[0] for entry in trace] == [1, 2, 3, 4, 5, 6]
    assert [entry[1] for entry in trace] == ["w", "b"] * 3
    for _, _, spent_ms, clock_after in trace:
        assert spent_ms >= 0.0
        assert clock_after <= 2_000 + 3 * 100
        assert clock_after > 0.0


def test_clock_summary_reads_one_side() -> None:
    trace = ((1, "w", 100.0, 2000.0), (2, "b", 50.0, 2050.0), (3, "w", 300.0, 1800.0))
    white = clock_summary(trace, "w")
    assert white == {"plies": 2, "min_clock_ms": 1800.0, "max_spend_ms": 300.0,
                     "mean_spend_ms": 200.0, "final_clock_ms": 1800.0}
    assert clock_summary(trace, "b")["plies"] == 1
    assert clock_summary((), "w")["plies"] == 0
    assert clock_summary((), "w")["min_clock_ms"] is None
