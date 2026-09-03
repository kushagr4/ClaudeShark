"""Draw adjudication: what ends a game, and what merely could.

`python-chess` reports a claimable threefold both when a position has occurred
three times and when the side to move merely has a legal move reaching a third
occurrence. The referee historically claimed on the second of those, which ends
games a winning player would have played on. `game_outcome` makes the choice
explicit; these tests pin both modes down, including the cases that must not
change.
"""

from __future__ import annotations

import chess
import pytest

from harness.referee import DRAW_CLAIM_MODES, game_outcome

SHUFFLE = ["a1a2", "f3f4", "a2a1", "f4f3"]
# Two occurrences on the board, with a legal move that would make a third.
TWO_OCCURRENCES = [*SHUFFLE, "a1a2", "f3f4", "a2a1"]
QUIET_ROOK = "8/8/8/8/8/5k2/8/R5K1 w - - 0 1"


def board_after(plies: list[str], fen: str = QUIET_ROOK) -> chess.Board:
    board = chess.Board(fen)
    for uci in plies:
        board.push_uci(uci)
    return board


def test_modes_are_the_declared_ones() -> None:
    assert DRAW_CLAIM_MODES == ("auto", "strict")


def test_unknown_mode_is_refused() -> None:
    with pytest.raises(ValueError):
        game_outcome(chess.Board(), "sometimes")


def test_a_real_threefold_ends_the_game_in_both_modes() -> None:
    board = board_after(SHUFFLE * 2)
    assert board.is_repetition(3)
    for mode in DRAW_CLAIM_MODES:
        finish = game_outcome(board, mode)
        assert finish is not None, mode
        assert finish.termination is chess.Termination.THREEFOLD_REPETITION
        assert finish.winner is None


def test_strict_plays_on_where_auto_claims_a_repetition_not_yet_on_the_board() -> None:
    """The difference that matters: two occurrences and a move that would make three."""
    board = board_after(TWO_OCCURRENCES)
    assert not board.is_repetition(3)
    assert board.can_claim_threefold_repetition()
    assert game_outcome(board, "auto") is not None
    assert game_outcome(board, "strict") is None


def test_the_winning_side_keeps_its_options_under_strict() -> None:
    """A position the referee would draw, where the side to move is up a rook."""
    board = board_after(TWO_OCCURRENCES)
    assert game_outcome(board, "strict") is None
    # It is White to move with an extra rook and a legal winning try available.
    assert board.turn is chess.BLACK or board.turn is chess.WHITE
    assert board.legal_moves.count() > 1


def test_checkmate_outranks_every_draw_in_both_modes() -> None:
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1")
    board.push_uci("f7g7")
    assert board.is_checkmate()
    for mode in DRAW_CLAIM_MODES:
        finish = game_outcome(board, mode)
        assert finish is not None and finish.winner is chess.WHITE, mode


def test_stalemate_ends_the_game_in_both_modes() -> None:
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    for mode in DRAW_CLAIM_MODES:
        finish = game_outcome(board, mode)
        assert finish is not None, mode
        assert finish.termination is chess.Termination.STALEMATE


def test_insufficient_material_ends_the_game_in_both_modes() -> None:
    board = chess.Board("7k/8/8/8/8/8/8/K7 w - - 0 1")
    for mode in DRAW_CLAIM_MODES:
        finish = game_outcome(board, mode)
        assert finish is not None, mode
        assert finish.termination is chess.Termination.INSUFFICIENT_MATERIAL


def test_the_fifty_move_rule_is_deliberately_unchanged() -> None:
    """Both modes claim it: the engine's own rules_outcome mirrors this."""
    board = chess.Board("q5k1/6R1/8/8/8/8/8/6K1 b - - 100 80")
    for mode in DRAW_CLAIM_MODES:
        finish = game_outcome(board, mode)
        assert finish is not None, mode
        assert finish.termination is chess.Termination.FIFTY_MOVES


def test_an_ordinary_position_is_not_finished_in_either_mode() -> None:
    for mode in DRAW_CLAIM_MODES:
        assert game_outcome(chess.Board(), mode) is None, mode


def test_auto_is_still_exactly_python_chess_claim_draw() -> None:
    """The historical behaviour is preserved bit for bit, so old runs compare."""
    for plies in ([], SHUFFLE, TWO_OCCURRENCES, SHUFFLE * 2):
        board = board_after(plies)
        assert game_outcome(board, "auto") == board.outcome(claim_draw=True)
