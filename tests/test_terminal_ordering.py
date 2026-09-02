"""Terminal-status ordering: rules before caps, evaluation or pruning.

This file exists because the ordering has now been got wrong twice in opposite
directions:

1. the fifty-move test ran before checkmate detection, so a forced mate on the
   hundredth halfmove scored 0;
2. the repair guarded it with `not in_check`, which conflates "in check" with
   "checkmated", so a *claimable* fifty-move draw while in check scored +928.

And separately, the quiescence depth cap returned a static evaluation before
terminal status was considered at all, so the same stalemate scored 0 at
qply 9 and -990 at qply 10.

Every expectation below is checked against python-chess rather than asserted
from memory, and the referee's own semantics -- `board.outcome(claim_draw=True)`
-- are the reference, because that is what ends a real game.
"""

from __future__ import annotations

import chess
import pytest

from cs_constants import INFINITY, MATE_BOUND
from cs_search import QS_MAX_PLY, Searcher, no_legal_move_score, rules_outcome


def q(fen: str, qply: int = 0, alpha: int = -INFINITY, beta: int = INFINITY) -> int:
    return Searcher(tt_bits=14)._quiescence(chess.Board(fen), alpha, beta, 0, qply)


def n(fen: str, depth: int = 3) -> int:
    return Searcher(tt_bits=14)._negamax(chess.Board(fen), depth, -INFINITY, INFINITY, 1)


# --------------------------------------------------------- the reported bug

FIFTY_IN_CHECK = "q5k1/6R1/8/8/8/8/8/6K1 b - - 100 80"


def test_the_reported_position_is_what_we_think_it_is() -> None:
    """Pin down the fixture against python-chess before asserting anything."""
    board = chess.Board(FIFTY_IN_CHECK)
    assert board.is_valid()
    assert board.is_check()
    assert not board.is_checkmate()
    assert list(board.legal_moves)
    assert board.can_claim_fifty_moves()
    outcome = board.outcome(claim_draw=True)
    assert outcome is not None and outcome.winner is None


def test_claimable_fifty_move_draw_while_in_check_scores_zero() -> None:
    """Was +928 in quiescence and +986 in negamax."""
    assert q(FIFTY_IN_CHECK) == 0
    assert n(FIFTY_IN_CHECK) == 0


def test_checkmate_still_outranks_the_fifty_move_rule() -> None:
    """The opposite error must not come back."""
    fen = "6k1/5ppp/8/8/8/8/8/R5K1 w - - 99 60"
    board = chess.Board(fen)
    mating = chess.Move.from_uci("a1a8")
    board.push(mating)
    assert board.is_checkmate()

    move, info = Searcher(tt_bits=16).search(chess.Board(fen), 0, max_depth=3)
    assert move == mating
    assert info.score > MATE_BOUND


def test_a_mated_position_with_an_exhausted_counter_is_a_loss_not_a_draw() -> None:
    fen = "R5k1/5ppp/8/8/8/8/8/6K1 b - - 100 80"
    board = chess.Board(fen)
    assert board.is_checkmate()
    assert not board.is_fifty_moves(), "python-chess: no legal move means no fifty-move draw"
    assert q(fen) < -MATE_BOUND
    assert n(fen) < -MATE_BOUND


# ------------------------------------------------------- fifty-move ladder

QUIET_ROOK_UP = "6k1/8/8/8/8/8/8/R5K1 b - - {clock} 80"


@pytest.mark.parametrize("clock", [98, 99, 100, 101])
def test_fifty_move_ladder_matches_the_referee(clock: int) -> None:
    """The engine must agree with `outcome(claim_draw=True)` at every clock.

    The referee already draws at 99, not 100, because the claim may be made for
    the move about to be played. An engine thresholded at 100 scores a position
    the referee has drawn as a rook up.
    """
    fen = QUIET_ROOK_UP.format(clock=clock)
    board = chess.Board(fen)
    referee_draws = board.outcome(claim_draw=True) is not None

    engine = rules_outcome(board, board.is_check(), ply=1)
    if referee_draws:
        assert engine == 0, f"clock {clock}: referee draws, engine said {engine}"
        assert q(fen) == 0
        assert n(fen) == 0
    else:
        assert engine is None, f"clock {clock}: referee plays on, engine forced {engine}"
        assert q(fen) < -300, "black is a rook down and it is not yet drawn"


def test_a_zeroing_move_does_not_make_the_claim_available() -> None:
    """At clock 99 the claim needs a move that does *not* reset the counter."""
    # Black's only legal moves are pawn moves and captures, all of which zero.
    fen = "8/8/8/8/8/8/6pk/6K1 b - - 99 80"
    board = chess.Board(fen)
    if not list(board.legal_moves):
        pytest.skip("fixture has no legal moves")
    expected_draw = board.outcome(claim_draw=True) is not None
    engine = rules_outcome(board, board.is_check(), ply=1)
    assert (engine == 0) == expected_draw


# --------------------------------------------------------- quiescence cap


@pytest.mark.parametrize("qply", [0, QS_MAX_PLY - 1, QS_MAX_PLY, QS_MAX_PLY + 1])
def test_stalemate_scores_zero_at_every_qply(qply: int) -> None:
    """Was 0 below the cap and -990 at or above it."""
    fen = "7k/5Q2/8/8/8/8/8/6K1 b - - 0 1"
    assert chess.Board(fen).is_stalemate()
    assert q(fen, qply=qply) == 0


@pytest.mark.parametrize("qply", [0, QS_MAX_PLY - 1, QS_MAX_PLY, QS_MAX_PLY + 1])
def test_checkmate_scores_as_mate_at_every_qply(qply: int) -> None:
    fen = "R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1"
    assert chess.Board(fen).is_checkmate()
    assert q(fen, qply=qply) < -MATE_BOUND


@pytest.mark.parametrize("qply", [0, QS_MAX_PLY, QS_MAX_PLY + 1])
def test_insufficient_material_scores_zero_at_every_qply(qply: int) -> None:
    fen = "4k3/8/8/8/8/8/8/3BK3 w - - 0 1"
    assert chess.Board(fen).is_insufficient_material()
    assert q(fen, qply=qply) == 0


def test_a_live_position_is_not_forced_at_the_cap() -> None:
    """The cap must still fall through to the evaluator when play continues."""
    fen = "6k1/8/8/8/8/8/8/R5K1 w - - 0 1"
    assert q(fen, qply=QS_MAX_PLY) > 300


# ------------------------------------------------------------- the helpers


def test_rules_outcome_returns_none_for_an_ordinary_position() -> None:
    board = chess.Board()
    assert rules_outcome(board, board.is_check(), ply=1) is None


def test_no_legal_move_score_distinguishes_mate_from_stalemate() -> None:
    mate = chess.Board("R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1")
    assert no_legal_move_score(mate, True, ply=4) == pytest.approx(-30000 + 4)

    stalemate = chess.Board("7k/5Q2/8/8/8/8/8/6K1 b - - 0 1")
    assert no_legal_move_score(stalemate, False, ply=4) == 0

    live = chess.Board()
    assert no_legal_move_score(live, False, ply=1) is None


def test_mate_score_still_encodes_distance() -> None:
    """A deeper mate must score lower, or the engine stops preferring fast ones."""
    shallow = no_legal_move_score(
        chess.Board("R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1"), True, ply=2
    )
    deep = no_legal_move_score(
        chess.Board("R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1"), True, ply=8
    )
    assert shallow is not None and deep is not None
    assert shallow < deep
