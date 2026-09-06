"""Endgame king-to-pawn proximity, V2.1: one relational term, endgame only.

The V2 calibration set showed the two endgame failure classes to be mirror
images in one number: in the blind wins (Stockfish +540, V1 +28) the
winning side's king is nearer the pawns than the defender's; in the false
wins (V1 +266, Stockfish level) it is the *defending* king that stands
among the pawns and holds them. The evaluator's king tables reward
centralisation, which is a different thing: a king on d4 with every pawn on
the h-file is central and useless. This term supplies the relation.

**Definition.** For each side, the Chebyshev distance from that side's king
to the nearest pawn *of either colour*; the score is
``EG[distance_white] - EG[distance_black]`` from White's point of view,
with ``EG`` non-increasing in distance. The middlegame value is zero, so the
taper phases the term in as pieces come off and it is absent from a full
board. No pawns on the board: zero.

"Any pawn" is the hypothesis, not an approximation of it. A defending king
that reaches the attacker's passer must get exactly the credit an attacking
king gets for reaching its own, because the evidence says both matter and
because the term is meant to be about the king, not about the pawn. Own-pawn
distance, enemy-pawn distance, passer distance and promotion-square distance
are different hypotheses and are not encoded here.

The table was chosen once from a predefined family on the diagnostic halves
of the calibration set and then frozen; see
`benchmarks/current/2026-09-04-v2.1-king-pawn-proximity.md`.
"""

from __future__ import annotations

import chess

# Indexed by Chebyshev distance 1..7 (index 0 is unreachable and unused).
# Non-increasing in distance; zero beyond four squares.
KING_PAWN_EG = (0, 48, 36, 24, 12, 0, 0, 0)


def _chebyshev(a: int, b: int) -> int:
    return max(abs((a & 7) - (b & 7)), abs((a >> 3) - (b >> 3)))


def king_pawn_distance(board: chess.Board, colour: bool) -> int:
    """Chebyshev distance from the side's king to the nearest pawn of either colour.

    Zero when there are no pawns.
    """
    king = board.king(colour)
    if king is None or not board.pawns:
        return 0
    return min(_chebyshev(king, square) for square in chess.scan_forward(board.pawns))


def king_pawn_reference(board: chess.Board) -> tuple[int, int]:
    """White's-point-of-view (middlegame, endgame) value, written to be obviously right."""
    if not board.pawns:
        return 0, 0
    white = king_pawn_distance(board, chess.WHITE)
    black = king_pawn_distance(board, chess.BLACK)
    return 0, KING_PAWN_EG[white] - KING_PAWN_EG[black]


def _rings() -> tuple[tuple[int, ...], ...]:
    """For every square, the mask of squares within Chebyshev distance d, for d = 0..7."""
    out = []
    for square in range(64):
        masks = []
        for d in range(8):
            mask = 0
            for other in range(64):
                if _chebyshev(square, other) <= d:
                    mask |= 1 << other
            masks.append(mask)
        out.append(tuple(masks))
    return tuple(out)


# _RING[square][d]: every square within d of `square`. _RING[square][7] is the
# whole board, so the distance scan below always terminates.
_RING = _rings()


def king_pawn_packed(board: chess.Board) -> int:
    """White's-point-of-view value in the evaluator's packed format; the middlegame half is zero."""
    pawns = board.pawns
    if not pawns:
        return 0
    kings = board.kings
    white_king = (kings & board.occupied_co[chess.WHITE]).bit_length() - 1
    black_king = (kings & ~board.occupied_co[chess.WHITE]).bit_length() - 1
    ring = _RING[white_king]
    d = 1
    while not (ring[d] & pawns):
        d += 1
    value = KING_PAWN_EG[d]
    ring = _RING[black_king]
    d = 1
    while not (ring[d] & pawns):
        d += 1
    return value - KING_PAWN_EG[d]
