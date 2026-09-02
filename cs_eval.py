"""Static evaluation: tapered material + piece-square tables, plus bishop pair.

Called once per quiescence leaf, so it is written as one flat function with
locals bound up front and no allocation. Every term here has to earn its
runtime cost; extra features belong behind an A/B test, not in this file.
"""

from __future__ import annotations

import chess

from cs_constants import (
    BISHOP_PAIR_EG,
    BISHOP_PAIR_MG,
    EG_BLACK,
    EG_WHITE,
    MG_BLACK,
    MG_WHITE,
    TEMPO,
    TOTAL_PHASE,
)

_MG_P, _MG_N, _MG_B, _MG_R, _MG_Q, _MG_K = MG_WHITE[1:]
_EG_P, _EG_N, _EG_B, _EG_R, _EG_Q, _EG_K = EG_WHITE[1:]
_MG_p, _MG_n, _MG_b, _MG_r, _MG_q, _MG_k = MG_BLACK[1:]
_EG_p, _EG_n, _EG_b, _EG_r, _EG_q, _EG_k = EG_BLACK[1:]

_WHITE_TABLES = (
    (_MG_P, _EG_P),
    (_MG_N, _EG_N),
    (_MG_B, _EG_B),
    (_MG_R, _EG_R),
    (_MG_Q, _EG_Q),
    (_MG_K, _EG_K),
)
_BLACK_TABLES = (
    (_MG_p, _EG_p),
    (_MG_n, _EG_n),
    (_MG_b, _EG_b),
    (_MG_r, _EG_r),
    (_MG_q, _EG_q),
    (_MG_k, _EG_k),
)


def evaluate(board: chess.Board) -> int:
    """Score the position in centipawns from the side to move's point of view."""
    occupied_co = board.occupied_co
    white = occupied_co[chess.WHITE]
    black = occupied_co[chess.BLACK]

    pawns = board.pawns
    knights = board.knights
    bishops = board.bishops
    rooks = board.rooks
    queens = board.queens
    kings = board.kings

    phase = (knights | bishops).bit_count() + 2 * rooks.bit_count() + 4 * queens.bit_count()
    if phase > TOTAL_PHASE:
        phase = TOTAL_PHASE  # early promotions can push the count past a full board

    mg = 0
    eg = 0

    boards = (pawns, knights, bishops, rooks, queens, kings)
    for index in range(6):
        piece_bb = boards[index]

        mg_table, eg_table = _WHITE_TABLES[index]
        bb = piece_bb & white
        while bb:
            square = (bb & -bb).bit_length() - 1
            bb &= bb - 1
            mg += mg_table[square]
            eg += eg_table[square]

        mg_table, eg_table = _BLACK_TABLES[index]
        bb = piece_bb & black
        while bb:
            square = (bb & -bb).bit_length() - 1
            bb &= bb - 1
            mg -= mg_table[square]
            eg -= eg_table[square]

    if (bishops & white).bit_count() > 1:
        mg += BISHOP_PAIR_MG
        eg += BISHOP_PAIR_EG
    if (bishops & black).bit_count() > 1:
        mg -= BISHOP_PAIR_MG
        eg -= BISHOP_PAIR_EG

    total = mg * phase + eg * (TOTAL_PHASE - phase)
    # Truncate toward zero rather than using floor division, so that mirroring
    # the position negates the score exactly. Floor division rounds negatives
    # away from zero and would give white a systematic one-centipawn edge.
    score = total // TOTAL_PHASE if total >= 0 else -(-total // TOTAL_PHASE)
    if board.turn:  # chess.WHITE is True
        return score + TEMPO
    return -score + TEMPO


def is_material_draw(board: chess.Board) -> bool:
    """Cheap insufficient-material test used to score dead positions as draws.

    Deliberately narrower than ``board.is_insufficient_material()``: it only
    fires when no pawns, rooks or queens remain and neither side has enough
    minor pieces to force mate.
    """
    if board.pawns or board.rooks or board.queens:
        return False
    knights = board.knights
    bishops = board.bishops
    if not knights and not bishops:
        return True
    minors = knights | bishops
    if minors.bit_count() > 2:
        return False
    white_minors = (minors & board.occupied_co[chess.WHITE]).bit_count()
    black_minors = (minors & board.occupied_co[chess.BLACK]).bit_count()
    # KN/KB vs K, and KN vs KN or KB vs KB, cannot be forced.
    return max(white_minors, black_minors) <= 1
