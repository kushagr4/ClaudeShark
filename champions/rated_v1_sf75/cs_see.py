"""Static exchange evaluation.

Answers "if I capture here and both sides keep recapturing with their cheapest
piece, what do I end up with?" -- in centipawns, without searching.

Move ordering by MVV-LVA cannot tell QxP-defended-by-a-pawn from a genuine win
of a pawn: both are captures, so both sort above every quiet move. SEE can, and
the payoff is largest in quiescence, which is where roughly half of this
engine's nodes are spent and where every losing capture drags a whole subtree
along with it.

The attacker set is recomputed from a running occupancy on each swap rather than
taken once at the start, which is what makes x-rays come out right: a rook
behind a bishop joins the exchange the moment the bishop leaves.

**Known limitation: pins are ignored.** SEE reasons about which pieces attack a
square, not about whether they may legally move, so a recapture by a pinned
piece is counted as if it were available. This is the standard trade -- checking
legality per swap would cost more than the inaccuracy does -- and it is measured
rather than assumed: `tests/test_see.py` compares against an independent
brute-force swap-off over random positions and holds the disagreement rate under
2%, with a named regression test for the pinned-recapture case.
"""

from __future__ import annotations

import chess

from cs_constants import PIECE_VALUE

_BB_RANK_MASKS = chess.BB_RANK_MASKS
_BB_RANK_ATTACKS = chess.BB_RANK_ATTACKS
_BB_FILE_MASKS = chess.BB_FILE_MASKS
_BB_FILE_ATTACKS = chess.BB_FILE_ATTACKS
_BB_DIAG_MASKS = chess.BB_DIAG_MASKS
_BB_DIAG_ATTACKS = chess.BB_DIAG_ATTACKS
_BB_KNIGHT_ATTACKS = chess.BB_KNIGHT_ATTACKS
_BB_KING_ATTACKS = chess.BB_KING_ATTACKS
_BB_PAWN_ATTACKS = chess.BB_PAWN_ATTACKS

_WHITE = chess.WHITE
_BLACK = chess.BLACK
_PAWN = chess.PAWN
_QUEEN = chess.QUEEN


def attackers_to(board: chess.Board, square: int, occupied: int) -> int:
    """Every piece of either colour attacking ``square`` for a given occupancy.

    Mirrors python-chess's own ``attackers_mask`` but takes the occupancy as a
    parameter, so the exchange loop can remove pieces as they are captured and
    have sliders behind them appear.
    """
    rank_pieces = _BB_RANK_MASKS[square] & occupied
    file_pieces = _BB_FILE_MASKS[square] & occupied
    diag_pieces = _BB_DIAG_MASKS[square] & occupied

    queens_and_rooks = board.queens | board.rooks
    queens_and_bishops = board.queens | board.bishops

    attackers = (
        (_BB_KING_ATTACKS[square] & board.kings)
        | (_BB_KNIGHT_ATTACKS[square] & board.knights)
        | (_BB_RANK_ATTACKS[square][rank_pieces] & queens_and_rooks)
        | (_BB_FILE_ATTACKS[square][file_pieces] & queens_and_rooks)
        | (_BB_DIAG_ATTACKS[square][diag_pieces] & queens_and_bishops)
        | (_BB_PAWN_ATTACKS[_BLACK][square] & board.pawns & board.occupied_co[_WHITE])
        | (_BB_PAWN_ATTACKS[_WHITE][square] & board.pawns & board.occupied_co[_BLACK])
    )
    return attackers & occupied


def _least_valuable(board: chess.Board, attackers: int, colour: bool) -> tuple[int, int]:
    """Cheapest attacker of ``colour``. Returns (square_mask, piece_type), or (0, 0)."""
    side = attackers & board.occupied_co[colour]
    if not side:
        return 0, 0
    for piece_type, bb in (
        (1, board.pawns),
        (2, board.knights),
        (3, board.bishops),
        (4, board.rooks),
        (5, board.queens),
        (6, board.kings),
    ):
        subset = side & bb
        if subset:
            return subset & -subset, piece_type
    return 0, 0


def see(board: chess.Board, move: chess.Move) -> int:
    """Centipawn outcome of the exchange on ``move.to_square``, for the mover.

    Positive means the capture wins material with best play from both sides.
    Non-captures score 0.
    """
    to_square = move.to_square
    from_square = move.from_square

    captured = board.piece_type_at(to_square)
    if captured is None:
        # En passant: the target square is empty but a pawn is taken.
        if move.to_square == board.ep_square and board.piece_type_at(from_square) == _PAWN:
            captured = _PAWN
        else:
            return 0

    attacker = board.piece_type_at(from_square)
    if attacker is None:
        return 0

    # gains[i] is the material balance for the side that moved at ply i, on the
    # assumption the exchange stops there.
    gains = [PIECE_VALUE[captured]]

    occupied = board.occupied & ~(1 << from_square)
    if captured == _PAWN and to_square == board.ep_square:
        # The captured pawn is not on the destination square.
        captured_square = to_square + (-8 if board.turn == _WHITE else 8)
        occupied &= ~(1 << captured_square)

    # A promotion changes what sits on the square for the rest of the exchange.
    on_square = move.promotion if move.promotion else attacker
    if move.promotion:
        gains[0] += PIECE_VALUE[move.promotion] - PIECE_VALUE[_PAWN]

    colour = not board.turn
    attackers = attackers_to(board, to_square, occupied) & occupied

    depth = 0
    while True:
        square_mask, piece_type = _least_valuable(board, attackers, colour)
        if not square_mask:
            break

        depth += 1
        # If this side captures, it wins what stands on the square and then
        # exposes its own piece to the reply.
        gains.append(PIECE_VALUE[on_square] - gains[depth - 1])

        # A king cannot capture into a defended square, so if the other side
        # still attacks it the exchange simply stops before this capture.
        if piece_type == 6 and (attackers & board.occupied_co[not colour]):
            gains.pop()
            depth -= 1
            break

        on_square = piece_type
        occupied &= ~square_mask
        attackers = attackers_to(board, to_square, occupied) & occupied
        colour = not colour

    # Fold back: each side stops the exchange whenever continuing is worse.
    while depth:
        gains[depth - 1] = -max(-gains[depth - 1], gains[depth])
        depth -= 1
    return gains[0]


def is_losing_capture(board: chess.Board, move: chess.Move) -> bool:
    """True when the exchange on this square comes out negative for the mover."""
    return see(board, move) < 0
