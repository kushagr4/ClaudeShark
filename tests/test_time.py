"""Time-management tests.

A flag is a whole point and it is the most self-inflicted way to lose one, so
these are the tests that matter most. They cover three things:

* the published increment is used as a constant, not rediscovered;
* a single move never plans to spend anywhere near the clock it was handed;
* an entire game, played with the referee's own clock arithmetic, never
  approaches zero.

The clock ladder runs real searches rather than checking arithmetic, because
the failure mode we care about is the search overrunning its deadline, not the
allocator computing a tidy number.
"""

from __future__ import annotations

import time

import chess
import pytest

import agent
import cs_time
from cs_search import Searcher
from cs_time import OVERHEAD_MS, RESERVE_MS, TimeManager

# Every clock the engine could plausibly be handed, from nearly-flagged to the
# opening move of a competition game.
CLOCK_LADDER = (50, 100, 250, 500, 1_000, 2_000, 5_000, 10_000, 30_000, 60_000, 120_000)

MIDDLEGAME = "r2q1rk1/pp1bbppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP1QPPP/R1B2RK1 w - - 0 10"


def test_increment_is_the_published_competition_constant() -> None:
    """120 s + 0.5 s is published. It is a constant, not something to infer."""
    assert cs_time.INCREMENT_MS == 500.0


def test_time_manager_exposes_no_increment_inference() -> None:
    """The old inference API is gone; nothing should quietly depend on it."""
    assert not hasattr(TimeManager(), "observe")
    assert not hasattr(TimeManager(), "record_spend")


@pytest.mark.parametrize("clock", CLOCK_LADDER)
def test_allocation_stays_well_inside_the_clock(clock: int) -> None:
    manager = TimeManager()
    manager.begin(clock, phase=24)
    assert manager.soft_ms <= manager.hard_ms
    # The hard deadline must leave the overhead and the reserve untouched.
    assert manager.hard_ms < clock - OVERHEAD_MS - RESERVE_MS + 1.0 or clock <= 250
    assert manager.hard_ms < clock * 0.5, f"{manager.hard_ms:.0f}ms of a {clock}ms clock"


@pytest.mark.parametrize("clock", CLOCK_LADDER)
def test_search_returns_inside_its_clock(clock: int) -> None:
    board = chess.Board(MIDDLEGAME)
    searcher = Searcher(tt_bits=16)
    started = time.perf_counter()
    move, _ = searcher.search(board, clock)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    assert move is not None
    assert move in chess.Board(MIDDLEGAME).legal_moves
    assert elapsed_ms < clock * 0.6, f"used {elapsed_ms:.0f}ms of a {clock}ms clock"


@pytest.mark.parametrize("clock", (1, 5, 20, 50))
def test_panic_clocks_still_return_a_legal_move(clock: int) -> None:
    uci = agent.get_move(MIDDLEGAME, clock)
    assert chess.Move.from_uci(uci) in chess.Board(MIDDLEGAME).legal_moves


def test_a_whole_game_on_a_real_clock_never_flags() -> None:
    """Play both sides with the referee's clock arithmetic and watch the clock.

    The referee subtracts wall time around the whole request and then credits
    the increment. A base clock much smaller than the competition's is used so
    the test runs in seconds, which makes it *harder* to survive than 120 s
    would be, not easier.
    """
    base_ms = 3_000
    increment_ms = cs_time.INCREMENT_MS

    board = chess.Board()
    clocks = {chess.WHITE: float(base_ms), chess.BLACK: float(base_ms)}
    searchers = {chess.WHITE: Searcher(tt_bits=16), chess.BLACK: Searcher(tt_bits=16)}
    lowest = float(base_ms)

    for _ in range(80):
        if board.is_game_over(claim_draw=True):
            break
        mover = board.turn
        started = time.perf_counter()
        move, _ = searchers[mover].search(chess.Board(board.fen()), int(clocks[mover]))
        elapsed_ms = (time.perf_counter() - started) * 1000.0

        assert move is not None and move in board.legal_moves
        clocks[mover] -= elapsed_ms
        lowest = min(lowest, clocks[mover])
        assert clocks[mover] > 0.0, f"flagged with {move} at ply {len(board.move_stack)}"
        clocks[mover] += increment_ms
        board.push(move)

    # Surviving is the requirement; keeping a real margin is the point.
    assert lowest > base_ms * 0.2, f"clock fell to {lowest:.0f}ms of {base_ms}ms"


def test_a_fresh_budget_allows_another_iteration() -> None:
    manager = TimeManager()
    manager.begin(120_000, phase=24)
    assert manager.should_start_iteration()
    assert 0.0 < cs_time.START_FRACTION < 1.0


def test_panic_mode_refuses_further_iterations() -> None:
    manager = TimeManager()
    manager.begin(10, phase=24)
    assert manager.panicking
    assert not manager.should_start_iteration()
