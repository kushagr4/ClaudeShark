"""Quiescence terminal-handling regression tests.

These assert the **score**, not merely that some parent position returns a legal
move. The defect they cover returned a large static evaluation for a stalemate,
which a legality test cannot see: the engine happily plays on and simply
believes a drawn position is won.
"""

from __future__ import annotations

import chess

from cs_constants import INFINITY, MATE_BOUND
from cs_search import Searcher


def q(fen: str, alpha: int = -INFINITY, beta: int = INFINITY) -> int:
    return Searcher(tt_bits=14)._quiescence(chess.Board(fen), alpha, beta, 0, 0)


def test_stalemate_leaf_scores_as_a_draw() -> None:
    """The reported defect: a stalemate scored -990 from its static evaluation.

    Black is stalemated and a queen down, so the static score is hugely
    negative. The correct answer is 0 -- the game is drawn.
    """
    fen = "7k/5Q2/8/8/8/8/8/6K1 b - - 0 1"
    board = chess.Board(fen)
    assert board.is_stalemate()
    assert q(fen) == 0


def test_stalemate_is_detected_before_the_stand_pat_cutoff() -> None:
    """The ordering that matters, tested directly through the window.

    The dangerous case is a stalemate whose static evaluation is good enough to
    pass the stand-pat beta cutoff, because the old code returned that score
    without ever asking whether a legal move existed. Rather than hunt for an
    exotic position where a stalemated side is winning, this drives the same
    path by choosing a beta the static score clears: black's evaluation here is
    about -990, so a beta of -2000 would have cut immediately and returned it.
    """
    fen = "7k/5Q2/8/8/8/8/8/6K1 b - - 0 1"
    assert chess.Board(fen).is_stalemate()
    assert q(fen, alpha=-3000, beta=-2000) == 0


def test_checkmate_leaf_scores_as_mate() -> None:
    fen = "R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1"
    assert chess.Board(fen).is_checkmate()
    assert q(fen) < -MATE_BOUND


def test_fifty_move_leaf_scores_as_a_draw() -> None:
    """A quiet position with the counter exhausted is a draw, not its evaluation."""
    fen = "6k1/8/8/8/8/8/8/R5K1 w - - 100 80"
    board = chess.Board(fen)
    assert board.is_fifty_moves()
    assert q(fen) == 0


def test_the_draw_threshold_is_the_referee_s_not_a_round_number() -> None:
    """Clock 99 is already drawn; 98 is not.

    This test previously asserted that 99 was still a rook up, which encoded a
    `>= 100` threshold. The referee ends the game with
    `outcome(claim_draw=True)`, and `can_claim_fifty_moves()` is true at 99
    whenever a legal move does not reset the counter -- the claim may be made
    for the move about to be played.
    """
    at_98 = "6k1/8/8/8/8/8/8/R5K1 w - - 98 80"
    at_99 = "6k1/8/8/8/8/8/8/R5K1 w - - 99 80"

    assert chess.Board(at_98).outcome(claim_draw=True) is None
    assert chess.Board(at_99).outcome(claim_draw=True) is not None

    assert q(at_98) > 300, "not yet claimable, so still a rook up"
    assert q(at_99) == 0, "the referee has already drawn this"


def test_insufficient_material_leaf_scores_as_a_draw() -> None:
    fen = "4k3/8/8/8/8/8/8/3BK3 w - - 0 1"
    assert chess.Board(fen).is_insufficient_material()
    assert q(fen) == 0


def test_normal_quiet_position_still_returns_its_evaluation() -> None:
    """The draw checks must not swallow ordinary positions."""
    fen = "6k1/8/8/8/8/8/8/R5K1 w - - 0 1"
    assert q(fen) > 300


def test_a_capture_available_does_not_trigger_the_stalemate_path() -> None:
    """Sanity: the stalemate test only runs when no tactical move exists."""
    fen = "4k3/8/8/3q4/4P3/8/8/4K3 w - - 0 1"
    assert q(fen) > 0


def test_search_prefers_mate_over_stalemate_when_both_are_available() -> None:
    """End to end: the engine must not throw away a win by stalemating.

    White can mate with Qg7 or stalemate with Kh6. Before the quiescence fix a
    stalemate leaf looked like a winning static score.
    """
    fen = "7k/8/6K1/8/8/8/8/6Q1 w - - 0 1"
    board = chess.Board(fen)
    move, info = Searcher(tt_bits=16).search(chess.Board(fen), 0, max_depth=4)
    assert move is not None
    board.push(move)
    assert not board.is_stalemate(), f"stalemated with {move.uci()}"
    assert info.score > MATE_BOUND
