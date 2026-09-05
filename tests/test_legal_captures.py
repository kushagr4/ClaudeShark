"""``legal_captures`` must yield exactly what python-chess yields, in order.

It is a speed path for the two capture sites that already know whether they
are in check, so the only question is agreement: the sequence has to equal
``list(board.generate_legal_captures())`` on every position, in check or not,
with pins, en passant and king captures all represented.
"""

from __future__ import annotations

import random

import chess

from cs_ordering import legal_captures


def _random_game_position(rng: random.Random) -> chess.Board:
    board = chess.Board()
    for _ in range(rng.randint(0, 90)):
        moves = list(board.legal_moves)
        if not moves:
            break
        # Bias towards captures and checks so pins and exposed kings are common.
        tactical = [m for m in moves if board.is_capture(m) or board.gives_check(m)]
        board.push(rng.choice(tactical) if tactical and rng.random() < 0.5 else rng.choice(moves))
    return board


def _random_sparse_position(rng: random.Random) -> chess.Board | None:
    board = chess.Board(None)
    squares = rng.sample(range(64), rng.randint(3, 12))
    board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
    for square in squares[2:]:
        board.set_piece_at(square, chess.Piece.from_symbol(rng.choice("QRBNPqrbnp")))
    board.turn = rng.random() < 0.5
    return board if board.is_valid() else None


def test_agrees_with_python_chess_on_random_positions() -> None:
    rng = random.Random(20260905)
    checked = pinned = in_check = ep = 0
    for _ in range(4000):
        board = _random_game_position(rng) if rng.random() < 0.6 else _random_sparse_position(rng)
        if board is None:
            continue
        check = board.is_check()
        expected = list(board.generate_legal_captures())
        produced = list(legal_captures(board, check))
        assert produced == expected, (board.fen(), check, expected, produced)
        checked += 1
        in_check += check
        ep += board.ep_square is not None
        king = board.king(board.turn)
        pinned += bool(king is not None and board._slider_blockers(king))
    assert checked > 3000
    assert pinned > 100 and in_check > 200 and ep > 20


def test_specific_cases() -> None:
    cases = [
        "4k3/8/8/8/8/8/3r4/4KR2 w - - 0 1",  # pinned rook may capture along the pin
        "4k3/8/8/8/1b6/8/3N4/4K3 w - - 0 1",  # pinned knight cannot capture
        "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",  # en passant available
        "8/8/8/2k5/3Pp3/8/8/4K2R b K d3 0 1",  # black ep with a rook on the rank
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1",  # in check: evasions order
    ]
    for fen in cases:
        board = chess.Board(fen)
        expected = list(board.generate_legal_captures())
        assert list(legal_captures(board, board.is_check())) == expected, fen
