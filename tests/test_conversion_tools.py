"""The conversion-audit tooling: episodes, trade detection, imbalance labels.

These tools reduce thousands of annotated moves to a few tables that the
audit's conclusions rest on, so the reductions themselves need pinning: an
episode must be the *first* crossing only, standing must be taken from the
right side, an equal exchange must be recognised from either colour, and a
king capture must not be mistaken for a trade.
"""

from __future__ import annotations

import chess

from tools.conversion.calibration import imbalance, material, trade_kind
from tools.conversion.episodes import episode, imbalance_kind, standing

# A rook-up endgame, White to move: the simplest "clearly ahead" material state.
ROOK_UP = "6k1/8/8/8/8/8/8/R5K1 w - - 0 1"
# Queens face each other on d-file; Qxd8 is an equal queen trade for White.
QUEEN_TRADE = "3q2k1/8/8/8/8/8/8/3QK3 w - - 0 1"
# A king capture of a rook: not a trade, and must not raise.
KING_TAKES = "8/8/8/8/8/8/4r3/4K2k w - - 0 1"


def move(
    fen: str, uci: str, turn: str, sf_white: int, mover: str = "base", loss: int = 0, ply: int = 0
):
    return {
        "ply": ply, "fen": fen, "mover": mover, "move": uci, "turn": turn,
        "score_stm": 0, "cand_static": 0, "base_static": 0,
        "sf_cp_white_before": sf_white, "cp_loss": loss, "sf_best": uci,
    }


def test_standing_is_taken_from_the_right_side() -> None:
    m = move(ROOK_UP, "a1a8", "w", 450)
    assert standing(m, True) == 450
    assert standing(m, False) == -450


def test_episode_uses_the_first_crossing_only() -> None:
    moves = [
        move(ROOK_UP, "a1a2", "w", 50, ply=0),
        move(ROOK_UP, "g8f8", "b", 250, mover="cand", ply=1),
        move(ROOK_UP, "a2a3", "w", 300, ply=2),
        move(ROOK_UP, "f8e8", "b", 310, mover="cand", ply=3),
    ]
    game = {"cluster": 1, "cand_white": False, "cand_score": 0.0, "termination": "checkmate",
            "final_fen": ROOK_UP, "moves": moves}
    e = episode(game, "base", 200, {})
    assert e is not None
    assert e["ply"] == 1, "the first ply at or above +200 from White's view"
    assert e["sf_cp"] == 250
    assert e["result"] == 1.0
    assert e["peak"] == 310


def test_no_episode_when_the_threshold_is_never_reached() -> None:
    moves = [move(ROOK_UP, "a1a2", "w", 50, ply=0)]
    game = {"cluster": 1, "cand_white": False, "cand_score": 0.5, "termination": "x",
            "final_fen": ROOK_UP, "moves": moves}
    assert episode(game, "base", 200, {}) is None


def test_equal_queen_trade_is_recognised() -> None:
    board = chess.Board(QUEEN_TRADE)
    assert trade_kind(board, "d1d8") == "queen trade"


def test_a_king_capture_is_not_a_trade() -> None:
    board = chess.Board(KING_TAKES)
    assert board.is_capture(chess.Move.from_uci("e1e2"))
    assert trade_kind(board, "e1e2") is None


def test_quiet_move_is_not_a_trade() -> None:
    assert trade_kind(chess.Board(ROOK_UP), "a1a2") is None


def test_imbalance_labels_agree_between_the_two_modules() -> None:
    board = chess.Board(ROOK_UP)
    assert imbalance(board, True) == "rook up"
    assert imbalance_kind(board, True) == "rook up"
    assert imbalance(board, False) == "rook down"
    assert material(board, True) == 5
