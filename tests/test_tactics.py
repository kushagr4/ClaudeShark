"""Run the tactical suite as part of the test gate.

The forced-mate/draw bug showed that ordinary unit tests do not catch a search
that reaches the right depth and returns the wrong move. These do, and they run
in seconds, so there is no reason not to have them on every change.

The suite's own labels are checked first. A puzzle whose expected answer is
wrong is worse than no puzzle at all: it fails on a correct engine and gets
"fixed" by widening the accepted set until it proves nothing.
"""

from __future__ import annotations

import chess
import pytest

from cs_search import Searcher
from tools.tactics import (
    SUITE,
    _saves_the_knight,
    mate_plies,
    safe_and_losing_moves,
    stalemating_moves,
    verify,
)

# Enough to solve everything in the suite while keeping the whole file quick.
BUDGET_MS = 400


def test_every_puzzle_position_is_legal() -> None:
    for puzzle in SUITE:
        board = chess.Board(puzzle.fen)
        assert board.is_valid(), f"{puzzle.name}: {board.status()!r}"
        assert list(board.legal_moves), f"{puzzle.name} has no legal moves"


def test_every_listed_best_move_is_legal() -> None:
    for puzzle in SUITE:
        legal = {move.uci() for move in chess.Board(puzzle.fen).legal_moves}
        illegal = [uci for uci in puzzle.best if uci not in legal]
        assert not illegal, f"{puzzle.name} lists illegal moves {illegal}"


def test_the_suite_verifies_itself() -> None:
    """Mates are proven, and avoid/stalemate puzzles are non-degenerate."""
    assert verify() == 0


def test_mate_puzzles_are_actually_mates() -> None:
    for puzzle in SUITE:
        if puzzle.kind != "mate":
            continue
        assert mate_plies(chess.Board(puzzle.fen)) is not None, puzzle.name


def test_avoid_mate_puzzles_have_both_outcomes() -> None:
    """A puzzle with no losing move cannot fail, and proves nothing."""
    for puzzle in SUITE:
        if puzzle.kind != "avoid_mate":
            continue
        safe, losing = safe_and_losing_moves(chess.Board(puzzle.fen))
        assert safe and losing, f"{puzzle.name} is degenerate"


def test_stalemate_puzzles_have_both_outcomes() -> None:
    for puzzle in SUITE:
        if puzzle.kind != "no_stalemate":
            continue
        stalemating, fine = stalemating_moves(chess.Board(puzzle.fen))
        assert stalemating and fine, f"{puzzle.name} is degenerate"


@pytest.mark.parametrize("puzzle", SUITE, ids=lambda p: p.name)
def test_engine_solves_puzzle(puzzle) -> None:  # type: ignore[no-untyped-def]
    board = chess.Board(puzzle.fen)
    move, _ = Searcher(tt_bits=16).search(chess.Board(puzzle.fen), 0,
                                          fixed_budget_ms=BUDGET_MS)
    assert move is not None and move in board.legal_moves

    if puzzle.name == "save_the_knight":
        assert _saves_the_knight(board, move)
    elif puzzle.kind == "avoid_mate":
        safe, _ = safe_and_losing_moves(board)
        assert move.uci() in safe, f"walked into mate with {move.uci()}"
    elif puzzle.kind == "no_stalemate":
        board.push(move)
        assert not board.is_stalemate(), f"stalemated the opponent with {move.uci()}"
    else:
        assert move.uci() in puzzle.best, f"played {move.uci()}, want {puzzle.best}"
