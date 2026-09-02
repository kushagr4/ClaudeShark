"""Material-draw detection must match the rule, not a hunch.

The search returns a hard 0 when ``is_material_draw`` fires, and the referee
only claims a draw when FIDE says the position is dead. An earlier version
declared K+N vs K+N, K+B vs K+N and opposite-coloured K+B vs K+B to be draws.
All three are *drawish*; none is *dead*, because a helpmate exists in each. That
is a different claim, and the search had no business forcing 0 on it.

The central test is exhaustive equivalence against python-chess over every
small material configuration, so this cannot drift again.
"""

from __future__ import annotations

import itertools

import chess
import pytest

from cs_eval import is_material_draw

# (name, fen, expected)  -- expected is the FIDE/python-chess answer.
CASES = [
    ("K vs K", "4k3/8/8/8/8/8/8/4K3 w - - 0 1", True),
    ("K+B vs K", "4k3/8/8/8/8/8/8/3BK3 w - - 0 1", True),
    ("K+N vs K", "4k3/8/8/8/8/8/8/3NK3 w - - 0 1", True),
    ("K vs K+B", "3bk3/8/8/8/8/8/8/4K3 w - - 0 1", True),
    ("K vs K+N", "3nk3/8/8/8/8/8/8/4K3 w - - 0 1", True),
    # Two knights cannot force mate, but a helpmate exists, so not dead.
    ("K+N+N vs K", "4k3/8/8/8/8/8/8/2NNK3 w - - 0 1", False),
    # c1 and a3 are both dark. (c1 and f1 are *not* the same colour, which is
    # how the first draft of this fixture got it wrong.)
    ("K+B+B same colour vs K", "4k3/8/8/8/8/B7/8/2B1K3 w - - 0 1", True),
    ("K+B vs K+B same colour", "2b1k3/8/8/8/8/8/8/3BK3 w - - 0 1", True),
    # The three the old implementation got wrong.
    ("K+B vs K+B opposite colours", "4kb2/8/8/8/8/8/8/3BK3 w - - 0 1", False),
    ("K+N vs K+N", "3nk3/8/8/8/8/8/8/3NK3 w - - 0 1", False),
    ("K+B vs K+N", "3nk3/8/8/8/8/8/8/3BK3 w - - 0 1", False),
    # Anything that can mate is obviously not a material draw.
    ("K+P vs K", "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1", False),
    ("K+R vs K", "4k3/8/8/8/8/8/8/3RK3 w - - 0 1", False),
    ("K+Q vs K", "4k3/8/8/8/8/8/8/3QK3 w - - 0 1", False),
]


@pytest.mark.parametrize(("name", "fen", "expected"), CASES, ids=[c[0] for c in CASES])
def test_known_material_configurations(name: str, fen: str, expected: bool) -> None:
    board = chess.Board(fen)
    assert board.is_insufficient_material() == expected, f"test fixture wrong for {name}"
    assert is_material_draw(board) == expected, name


def _placements() -> list[str]:
    """Every small material configuration, on a few square arrangements.

    Squares are chosen so bishops land on both colours, which is the axis the
    rule actually turns on.
    """
    boards: list[str] = []
    pieces = ["", "N", "B", "NN", "BB", "NB", "R", "Q", "P"]
    white_squares = [chess.C1, chess.F1]
    black_squares = [chess.C8, chess.F8]
    for white, black in itertools.product(pieces, pieces):
        if len(white) + len(black) > 3:
            continue
        board = chess.Board(None)
        board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
        ok = True
        for index, symbol in enumerate(white):
            if index >= len(white_squares):
                ok = False
                break
            board.set_piece_at(white_squares[index], chess.Piece.from_symbol(symbol))
        for index, symbol in enumerate(black):
            if index >= len(black_squares):
                ok = False
                break
            board.set_piece_at(black_squares[index], chess.Piece.from_symbol(symbol.lower()))
        if ok and board.is_valid():
            boards.append(board.fen())
    return boards


def test_exhaustive_agreement_with_python_chess() -> None:
    """Equivalence over every configuration we can construct, not a sample."""
    disagreements = []
    for fen in _placements():
        board = chess.Board(fen)
        ours = is_material_draw(board)
        theirs = board.is_insufficient_material()
        if ours != theirs:
            disagreements.append(f"{fen}: ours={ours} python-chess={theirs}")
    assert not disagreements, "\n".join(disagreements)


def test_agreement_on_random_endgames() -> None:
    """Positions reached by play, not by construction."""
    import random

    rng = random.Random(20260902)
    disagreements = []
    checked = 0
    for _ in range(400):
        board = chess.Board()
        for _ in range(rng.randint(40, 120)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        checked += 1
        if is_material_draw(board) != board.is_insufficient_material():
            disagreements.append(board.fen())
    assert not disagreements, f"{len(disagreements)}/{checked}: {disagreements[:3]}"


def test_does_not_fire_on_a_drawish_but_live_position() -> None:
    """The behaviour change, stated as an assertion.

    K+N vs K+N is drawn with any sane play, but it is not a dead position and
    the search must not return a forced 0 for it.
    """
    board = chess.Board("3nk3/8/8/8/8/8/8/3NK3 w - - 0 1")
    assert not is_material_draw(board)
