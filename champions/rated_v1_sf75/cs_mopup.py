"""Mop-up evaluation, v1: a mating gradient for bare-king endings.

The conversion audit found that the engine recognises K+Q v K and K+R v K as
massively winning and still cannot finish them: with nothing in the evaluation
to prefer one queen move over another, the root score sits at about +1000 for
twenty plies and the game shuffles into a threefold. The only gradient the
PeSTO tables offer is 61 cp between a centralised and a cornered defending
king, against a queen worth 936; a depth-12 search cannot turn that into a
plan.

This adds the two geometric terms every mating pattern needs and nothing else:

* **drive the defending king to an edge** -- reward the attacker as the
  defender's distance from the nearest edge falls (3 in the centre, 0 on the
  rim);
* **bring the attacking king closer** -- reward the attacker as the Chebyshev
  distance between the kings falls (7 apart down to 1 adjacent).

Both are monotonic, both are in whole centipawns, and both are small against
the material that must already be on the board to switch them on.

**Activation is deliberately narrow.** The term fires only when one side has a
bare king -- no pawns, no pieces -- and the other has at least one rook or
queen. It is exactly zero in every other position, including pawn endings,
K+minor endings, and every middlegame, so it cannot touch the play the
evaluator was measured on. Symmetric by colour.

The two weights were chosen on the six real stuck positions from the audit
and checked on synthetic positions the selection never saw; see
`benchmarks/current/2026-09-03-mop-up-v1.md`.
"""

from __future__ import annotations

import chess

# Centipawns per step. EDGE applies to the defender's edge distance (0..3),
# PROXIMITY to the gap between the kings (1..7). At the maxima the whole
# term is 3 * EDGE + 6 * PROXIMITY, deliberately well under a rook.
EDGE = 30
PROXIMITY = 15


def _edge_distance(square: int) -> int:
    file = square & 7
    rank = square >> 3
    return min(file, 7 - file, rank, 7 - rank)


def _chebyshev(a: int, b: int) -> int:
    return max(abs((a & 7) - (b & 7)), abs((a >> 3) - (b >> 3)))


def mop_up_reference(board: chess.Board) -> int:
    """White's-point-of-view bonus, written to be obviously right.

    Not used in search; the fast version is tested against it.
    """
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    if white_king is None or black_king is None:
        return 0
    for attacker, defender, sign in ((chess.WHITE, chess.BLACK, 1), (chess.BLACK, chess.WHITE, -1)):
        defender_material = [
            sq for sq, piece in board.piece_map().items()
            if piece.color == defender and piece.piece_type != chess.KING
        ]
        if defender_material:
            continue
        heavy = board.pieces(chess.ROOK, attacker) | board.pieces(chess.QUEEN, attacker)
        if not heavy:
            continue
        their_king = board.king(defender)
        our_king = board.king(attacker)
        assert their_king is not None and our_king is not None
        edge = (3 - _edge_distance(their_king)) * EDGE
        near = (7 - _chebyshev(our_king, their_king)) * PROXIMITY
        bonus = edge + near
        return sign * bonus
    return 0


# Precomputed per square, so the fast path is two table reads and no arithmetic
# beyond the king-distance lookup.
_EDGE_BONUS = tuple((3 - _edge_distance(sq)) * EDGE for sq in range(64))
_PROXIMITY_BONUS = tuple(
    tuple((7 - _chebyshev(a, b)) * PROXIMITY for b in range(64)) for a in range(64)
)


def mop_up(board: chess.Board) -> int:
    """White's-point-of-view bonus; zero unless one side is a bare king."""
    kings = board.kings
    white = board.occupied_co[chess.WHITE]
    black = board.occupied_co[chess.BLACK]
    heavy = board.rooks | board.queens
    if black & ~kings == 0:
        # Black is a bare king; White needs a rook or queen.
        if heavy & white == 0:
            return 0
        their = (black & kings).bit_length() - 1
        our = (white & kings).bit_length() - 1
        return _EDGE_BONUS[their] + _PROXIMITY_BONUS[our][their]
    if white & ~kings == 0:
        if heavy & black == 0:
            return 0
        their = (white & kings).bit_length() - 1
        our = (black & kings).bit_length() - 1
        return -(_EDGE_BONUS[their] + _PROXIMITY_BONUS[our][their])
    return 0
