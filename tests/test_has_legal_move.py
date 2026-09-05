"""``_has_legal_move`` must agree with python-chess on every out-of-check position.

It is a speed path for the quiescence stalemate probe, so it is only ever a
correctness question: the answer has to be identical to
``any(board.generate_legal_moves())``. Random game positions cover the common
case; random sparse placements cover the stalemates and near-stalemates that
games rarely reach, and pinned pieces are the case the fast path must not get
wrong, so positions where the fast path finds nothing are counted to make
sure the fallback is actually exercised.
"""

from __future__ import annotations

import random

import chess

from cs_search import _has_legal_move


def _random_game_position(rng: random.Random) -> chess.Board:
    board = chess.Board()
    for _ in range(rng.randint(0, 80)):
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(rng.choice(moves))
    return board


def _random_sparse_position(rng: random.Random) -> chess.Board | None:
    board = chess.Board(None)
    squares = rng.sample(range(64), rng.randint(2, 8))
    board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
    for square in squares[2:]:
        piece = rng.choice("QRBNPqrbnp")
        board.set_piece_at(square, chess.Piece.from_symbol(piece))
    board.turn = rng.random() < 0.5
    if not board.is_valid():
        return None
    return board


def test_agrees_with_generator_on_random_positions() -> None:
    rng = random.Random(20260905)
    checked = stalemates = 0
    for _ in range(3000):
        board = _random_game_position(rng) if rng.random() < 0.5 else _random_sparse_position(rng)
        if board is None or board.is_check():
            continue
        expected = any(board.generate_legal_moves())
        assert _has_legal_move(board) == expected, board.fen()
        checked += 1
        stalemates += not expected
    assert checked > 1500
    assert stalemates >= 2, "the sparse positions should include some stalemates"


def test_known_stalemates_and_pins() -> None:
    cases = {
        "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1": False,  # classic stalemate
        "k7/P7/K7/8/8/8/8/8 b - - 0 1": False,  # pawn-locked stalemate
        "8/8/8/8/8/1k6/1p6/1K6 w - - 0 1": False,  # king boxed in by king and pawn
        "5bnr/4p1pq/4Qpkr/7p/7P/4P3/PPPP1PP1/RNB1KBNR b KQ - 0 10": False,  # ten-move stalemate
        "k7/8/1K6/8/8/8/8/1R6 b - - 0 1": True,  # only a king move exists (fallback path)
        "4k3/4r3/8/8/8/8/4R3/4K3 w - - 0 1": True,  # pinned rook can slide on the file
        "k1N5/1bK5/8/8/8/8/8/7B b - - 0 1": True,  # only the pinned bishop can move
    }
    for fen, expected in cases.items():
        board = chess.Board(fen)
        assert not board.is_check(), fen
        assert _has_legal_move(board) == expected, fen
