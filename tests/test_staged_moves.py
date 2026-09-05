"""``staged_moves`` must reproduce ``order_moves`` exactly, move for move.

The lazy picker is only a speed change: at every position where it is valid
(no pawn of the side to move on its seventh rank) the sequence it yields has
to be identical to the fully sorted list, with any table move, any killers
and any history state. Random positions with random heuristics tables are the
fixture; a single mismatch is a bug, not a tolerance.
"""

from __future__ import annotations

import random

import chess

from cs_ordering import Heuristics, order_moves, staged_moves
from cs_search import _see_losing


def _random_board(rng: random.Random) -> chess.Board:
    board = chess.Board()
    for _ in range(rng.randint(0, 60)):
        moves = list(board.legal_moves)
        if not moves or board.is_game_over():
            break
        board.push(rng.choice(moves))
    return board


def _valid(board: chess.Board) -> bool:
    seventh = chess.BB_RANK_7 if board.turn else chess.BB_RANK_2
    return not (board.pawns & board.occupied_co[board.turn] & seventh)


def test_staged_moves_matches_order_moves_on_random_positions() -> None:
    rng = random.Random(20260905)
    checked = 0
    for _ in range(600):
        board = _random_board(rng)
        legal = list(board.legal_moves)
        if not legal or not _valid(board):
            continue
        heuristics = Heuristics()
        for i in range(8192):
            if rng.random() < 0.3:
                heuristics.history[i] = rng.randint(0, 800_000)
        ply = rng.randint(0, 20)
        for slot in (0, 1):
            if rng.random() < 0.7:
                heuristics.killers[ply * 2 + slot] = rng.choice(legal)
        tt_move = rng.choice(legal) if rng.random() < 0.6 else None
        if rng.random() < 0.1:
            tt_move = chess.Move.from_uci("a1h8")  # an illegal table move
        for see in (None, _see_losing):
            expected = order_moves(board, list(legal), tt_move, ply, heuristics, see)
            produced = list(staged_moves(board, tt_move, ply, heuristics, see))
            assert produced == expected, (board.fen(), tt_move, expected[:6], produced[:6])
        checked += 1
    assert checked > 300


def test_staged_moves_is_empty_when_no_legal_moves() -> None:
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")  # stalemate
    assert not list(board.legal_moves)
    assert list(staged_moves(board, None, 0, Heuristics(), None)) == []
