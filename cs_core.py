"""Compiled search core: bitboard move generation, make/unmake, evaluation,
static exchange evaluation, transposition table, quiescence and negamax, all
inside one Numba region.

The algorithm is the C5 search (``cs_search.py``): PeSTO tapered tables with
the bishop pair and tempo, PVS, null move, the C5 late-move-reduction
schedule, reverse futility pruning, aspiration at the root, killers and
history, MVV-LVA with SEE-demoted losing captures, delta and SEE pruning in
quiescence with checking captures kept, repetition on the path and the game
history, the fifty-move and insufficient-material rules. What changed is the
executor: python-chess and CPython did about 55% and 45% of C5's runtime
respectively; here both are compiled.

Representation
--------------
* Bitboards are ``int64`` (two's complement; bit 63 is h8). Right shifts of a
  bitboard therefore go through ``shr8`` which masks the sign extension.
* Piece codes: 1..6 white P N B R Q K, 7..12 black. ``B[code]`` is the
  bitboard of that piece, ``O[0]``/``O[1]``/``O[2]`` white/black/all
  occupancy, ``M[sq]`` the mailbox.
* ``S`` holds the scalar state: side, castling rights (1 WK, 2 WQ, 4 BK,
  8 BQ), en-passant square (-1 none), halfmove clock, Zobrist key, packed
  piece-square sum (white-positive, ``(mg << 16) + eg``), stack depth.
* A move is ``from | to << 6 | promotion << 12 | flags << 15`` with flags
  1 en passant, 2 castling, 4 double pawn push.

Everything here is verified against python-chess by ``tests/test_core.py``:
perft on the standard positions and random games, evaluation against
``cs_eval.evaluate``, SEE against ``cs_see.see``.
"""

from __future__ import annotations

import numpy as np
from numba import njit, objmode
from time import perf_counter

import chess

from cs_constants import (
    BISHOP_PAIR_EG,
    BISHOP_PAIR_MG,
    EG_BLACK,
    EG_WHITE,
    MG_BLACK,
    MG_WHITE,
    TEMPO,
)

# ----------------------------------------------------------------- constants

INFINITY = 32_000
MATE_SCORE = 30_000
MATE_BOUND = 29_000
DRAW_SCORE = 0
MAX_PLY = 128
STACK = MAX_PLY + 16
MAX_MOVES = 256

BOUND_EXACT = 0
BOUND_LOWER = 1
BOUND_UPPER = 2

FLAG_EP = 1
FLAG_CASTLE = 2
FLAG_DPP = 4

# Search parameters, exactly C5's shipped values.
QS_MAX_PLY = 10
DELTA_MARGIN = 200
TT_HALFMOVE_LIMIT = 80
RFP_MARGIN = 120
RFP_MAX_DEPTH = 3
LMR_START = 3
LMR_R2_INDEX = 6
LMR_R2_DEPTH = 6
CHECK_INTERVAL = 1024

TT_BONUS = 2_000_000
PROMO_BONUS = 1_600_000
CAPTURE_BONUS = 1_000_000
KILLER_1 = 900_000
KILLER_2 = 899_000
LOSING_CAPTURE = 100_000
HISTORY_CAP = 800_000

TT_BITS = 22

PIECE_VALUE = np.array([0, 100, 320, 330, 500, 900, 20_000, 100, 320, 330, 500, 900, 20_000],
                       dtype=np.int64)
PHASE_INC = np.array([0, 0, 1, 1, 2, 4, 0, 0, 1, 1, 2, 4, 0], dtype=np.int64)
TOTAL_PHASE = 24

MASK56 = 0x00FFFFFFFFFFFFFF
RANK_1 = 0x00000000000000FF
RANK_2 = 0x000000000000FF00
RANK_3 = 0x0000000000FF0000
RANK_6 = 0x0000FF0000000000
RANK_7 = 0x00FF000000000000
RANK_8 = -0x0100000000000000  # 0xFF00000000000000 as int64
LIGHT_SQUARES = 0x55AA55AA55AA55AA
DARK_SQUARES = -0x55AA55AA55AA55AB  # 0xAA55AA55AA55AA55 as int64

_DEBRUIJN = np.int64(0x03F79D71B4CB0A89)
_LSB_INDEX = np.zeros(64, dtype=np.int64)
for _i in range(64):
    _LSB_INDEX[(((1 << _i) * 0x03F79D71B4CB0A89) & 0xFFFFFFFFFFFFFFFF) >> 58] = _i
_MSB8 = np.zeros(256, dtype=np.int64)
for _i in range(1, 256):
    _MSB8[_i] = _i.bit_length() - 1


def _to_i64(bb: int) -> int:
    return bb - (1 << 64) if bb >= (1 << 63) else bb


# ------------------------------------------------------------ attack tables

KNIGHT_ATT = np.zeros(64, dtype=np.int64)
KING_ATT = np.zeros(64, dtype=np.int64)
PAWN_ATT = np.zeros((2, 64), dtype=np.int64)  # [colour][square]: squares attacked
# Rays: 0 N, 1 NE, 2 E, 3 SE, 4 S, 5 SW, 6 W, 7 NW.
RAYS = np.zeros((8, 64), dtype=np.int64)
BETWEEN = np.zeros((64, 64), dtype=np.int64)
_DIRS = ((0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1))
for _sq in range(64):
    _f, _r = _sq & 7, _sq >> 3
    _k = 0
    for _df, _dr in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        if 0 <= _f + _df < 8 and 0 <= _r + _dr < 8:
            _k |= 1 << ((_r + _dr) * 8 + _f + _df)
    KNIGHT_ATT[_sq] = _to_i64(_k)
    _k = 0
    for _df in (-1, 0, 1):
        for _dr in (-1, 0, 1):
            if (_df or _dr) and 0 <= _f + _df < 8 and 0 <= _r + _dr < 8:
                _k |= 1 << ((_r + _dr) * 8 + _f + _df)
    KING_ATT[_sq] = _to_i64(_k)
    _k = 0
    for _df in (-1, 1):
        if 0 <= _f + _df < 8 and _r + 1 < 8:
            _k |= 1 << ((_r + 1) * 8 + _f + _df)
    PAWN_ATT[0, _sq] = _to_i64(_k)
    _k = 0
    for _df in (-1, 1):
        if 0 <= _f + _df < 8 and _r - 1 >= 0:
            _k |= 1 << ((_r - 1) * 8 + _f + _df)
    PAWN_ATT[1, _sq] = _to_i64(_k)
    for _d, (_df, _dr) in enumerate(_DIRS):
        _k = 0
        _ff, _rr = _f + _df, _r + _dr
        while 0 <= _ff < 8 and 0 <= _rr < 8:
            _k |= 1 << (_rr * 8 + _ff)
            _ff += _df
            _rr += _dr
        RAYS[_d, _sq] = _to_i64(_k)
for _a in range(64):
    for _b in range(64):
        _k = 0
        _df = (_b & 7) - (_a & 7)
        _dr = (_b >> 3) - (_a >> 3)
        if _a != _b and (_df == 0 or _dr == 0 or abs(_df) == abs(_dr)):
            _sf = (_df > 0) - (_df < 0)
            _sr = (_dr > 0) - (_dr < 0)
            _ff, _rr = (_a & 7) + _sf, (_a >> 3) + _sr
            while (_rr * 8 + _ff) != _b:
                _k |= 1 << (_rr * 8 + _ff)
                _ff += _sf
                _rr += _sr
        BETWEEN[_a, _b] = _to_i64(_k)

# Castling-rights mask by square touched (from or to).
CASTLE_MASK = np.full(64, 15, dtype=np.int64)
CASTLE_MASK[chess.E1] = 15 & ~3
CASTLE_MASK[chess.H1] = 15 & ~1
CASTLE_MASK[chess.A1] = 15 & ~2
CASTLE_MASK[chess.E8] = 15 & ~12
CASTLE_MASK[chess.H8] = 15 & ~4
CASTLE_MASK[chess.A8] = 15 & ~8

# Zobrist keys.
_rng = np.random.default_rng(20260906)
ZP = _rng.integers(-(1 << 63), (1 << 63) - 1, size=(13, 64), dtype=np.int64)
ZC = _rng.integers(-(1 << 63), (1 << 63) - 1, size=16, dtype=np.int64)
ZEP = _rng.integers(-(1 << 63), (1 << 63) - 1, size=8, dtype=np.int64)
ZSIDE = int(_rng.integers(-(1 << 63), (1 << 63) - 1, dtype=np.int64))

# Packed piece-square values, signed so that packed sum = white - black.
PSTV = np.zeros((13, 64), dtype=np.int64)
for _pt in range(1, 7):
    for _sq in range(64):
        PSTV[_pt, _sq] = (MG_WHITE[_pt][_sq] << 16) + EG_WHITE[_pt][_sq]
        PSTV[_pt + 6, _sq] = -((MG_BLACK[_pt][_sq] << 16) + EG_BLACK[_pt][_sq])
BISHOP_PAIR_PACKED = (BISHOP_PAIR_MG << 16) + BISHOP_PAIR_EG

# Mop-up mating gradient, ported unchanged from cs_mopup.py. Two geometric
# terms for bare-king endings: drive the defending king to an edge, and bring
# the attacking king closer. Whole centipawns, added after the taper because
# these positions are endgames by definition and the gradient must not be
# diluted (cs_eval applies the same term at the same "post" stage).
MOPUP_EDGE = 30
MOPUP_PROXIMITY = 15
MOPUP_EDGE_BONUS = np.zeros(64, dtype=np.int64)
MOPUP_PROX_BONUS = np.zeros((64, 64), dtype=np.int64)
for _sq in range(64):
    _file = _sq & 7
    _rank = _sq >> 3
    MOPUP_EDGE_BONUS[_sq] = (3 - min(_file, 7 - _file, _rank, 7 - _rank)) * MOPUP_EDGE
for _a in range(64):
    for _b in range(64):
        _cheb = max(abs((_a & 7) - (_b & 7)), abs((_a >> 3) - (_b >> 3)))
        MOPUP_PROX_BONUS[_a, _b] = (7 - _cheb) * MOPUP_PROXIMITY




# ------------------------------------------------------------- bit helpers


@njit(cache=False)
def lsb(bb):
    x = bb & -bb
    return _LSB_INDEX[((x * _DEBRUIJN) >> 58) & 63]


@njit(cache=False)
def msb(bb):
    for i in range(7, -1, -1):
        b = (bb >> (8 * i)) & 0xFF
        if b:
            return 8 * i + _MSB8[b]
    return -1


@njit(cache=False)
def popcount(x):
    x = x - ((x >> 1) & 0x5555555555555555)
    x = (x & 0x3333333333333333) + ((x >> 2) & 0x3333333333333333)
    x = (x + (x >> 4)) & 0x0F0F0F0F0F0F0F0F
    return (x * 0x0101010101010101) >> 56


@njit(cache=False)
def shr8(bb):
    return (bb >> 8) & MASK56


@njit(cache=False)
def ray_pos(d, sq, occ):
    ray = RAYS[d, sq]
    b = ray & occ
    if b == 0:
        return ray
    return ray ^ RAYS[d, lsb(b)]


@njit(cache=False)
def ray_neg(d, sq, occ):
    ray = RAYS[d, sq]
    b = ray & occ
    if b == 0:
        return ray
    return ray ^ RAYS[d, msb(b)]


@njit(cache=False)
def rook_attacks(sq, occ):
    return ray_pos(0, sq, occ) | ray_pos(2, sq, occ) | ray_neg(4, sq, occ) | ray_neg(6, sq, occ)


@njit(cache=False)
def bishop_attacks(sq, occ):
    return ray_pos(1, sq, occ) | ray_pos(7, sq, occ) | ray_neg(3, sq, occ) | ray_neg(5, sq, occ)


@njit(cache=False)
def attackers_to(B, sq, occ):
    """Every piece of either colour attacking ``sq`` for the given occupancy."""
    a = KING_ATT[sq] & (B[6] | B[12])
    a |= KNIGHT_ATT[sq] & (B[2] | B[8])
    a |= rook_attacks(sq, occ) & (B[4] | B[5] | B[10] | B[11])
    a |= bishop_attacks(sq, occ) & (B[3] | B[5] | B[9] | B[11])
    a |= PAWN_ATT[1, sq] & B[1]
    a |= PAWN_ATT[0, sq] & B[7]
    return a & occ


@njit(cache=False)
def is_attacked(B, sq, by, occ):
    base = 6 * by
    if PAWN_ATT[1 - by, sq] & B[1 + base]:
        return True
    if KNIGHT_ATT[sq] & B[2 + base]:
        return True
    if KING_ATT[sq] & B[6 + base]:
        return True
    if rook_attacks(sq, occ) & (B[4 + base] | B[5 + base]):
        return True
    if bishop_attacks(sq, occ) & (B[3 + base] | B[5 + base]):
        return True
    return False


@njit(cache=False)
def in_check(B, O, S):
    side = S[0]
    return is_attacked(B, lsb(B[6 + 6 * side]), 1 - side, O[2])


@njit(cache=False)
def ep_key_term(B, S):
    """The en-passant part of the key: only when a pawn could capture."""
    ep = S[2]
    if ep < 0:
        return 0
    side = S[0]
    if PAWN_ATT[1 - side, ep] & B[1 + 6 * side]:
        return ZEP[ep & 7]
    return 0


# ---------------------------------------------------------- make / unmake


@njit(cache=False)
def make_move(B, O, M, S, U, move):
    ply = S[6]
    U[ply, 1] = S[1]
    U[ply, 2] = S[2]
    U[ply, 3] = S[3]
    U[ply, 4] = S[4]
    U[ply, 5] = S[5]
    U[ply, 6] = move
    side = S[0]
    them = 1 - side
    fr = move & 63
    to = (move >> 6) & 63
    promo = (move >> 12) & 7
    flags = move >> 15
    piece = M[fr]
    key = S[4] ^ ep_key_term(B, S)
    packed = S[5]
    from_bb = np.int64(1) << fr
    to_bb = np.int64(1) << to

    captured = 0
    if flags & FLAG_EP:
        cap_sq = to - 8 if side == 0 else to + 8
        captured = M[cap_sq]
        cap_bb = np.int64(1) << cap_sq
        B[captured] ^= cap_bb
        O[them] ^= cap_bb
        O[2] ^= cap_bb
        M[cap_sq] = 0
        key ^= ZP[captured, cap_sq]
        packed -= PSTV[captured, cap_sq]
    else:
        captured = M[to]
        if captured:
            B[captured] ^= to_bb
            O[them] ^= to_bb
            O[2] ^= to_bb
            key ^= ZP[captured, to]
            packed -= PSTV[captured, to]
    U[ply, 0] = captured

    both = from_bb | to_bb
    B[piece] ^= both
    O[side] ^= both
    O[2] ^= both
    M[fr] = 0
    M[to] = piece
    key ^= ZP[piece, fr] ^ ZP[piece, to]
    packed += PSTV[piece, to] - PSTV[piece, fr]

    if promo:
        newp = promo + 6 * side
        B[piece] ^= to_bb
        B[newp] |= to_bb
        M[to] = newp
        key ^= ZP[piece, to] ^ ZP[newp, to]
        packed += PSTV[newp, to] - PSTV[piece, to]

    if flags & FLAG_CASTLE:
        if to == 6:
            rf, rt = 7, 5
        elif to == 2:
            rf, rt = 0, 3
        elif to == 62:
            rf, rt = 63, 61
        else:
            rf, rt = 56, 59
        rook = 4 + 6 * side
        rb = (np.int64(1) << rf) | (np.int64(1) << rt)
        B[rook] ^= rb
        O[side] ^= rb
        O[2] ^= rb
        M[rf] = 0
        M[rt] = rook
        key ^= ZP[rook, rf] ^ ZP[rook, rt]
        packed += PSTV[rook, rt] - PSTV[rook, rf]

    if piece == 1 + 6 * side or captured:
        S[3] = 0
    else:
        S[3] += 1

    ep = -1
    if flags & FLAG_DPP:
        ep = (fr + to) >> 1
    newc = S[1] & CASTLE_MASK[fr] & CASTLE_MASK[to]
    key ^= ZC[S[1]] ^ ZC[newc] ^ ZSIDE
    S[0] = them
    S[1] = newc
    S[2] = ep
    S[5] = packed
    S[6] = ply + 1
    S[4] = key ^ ep_key_term(B, S)


@njit(cache=False)
def unmake_move(B, O, M, S, U):
    ply = S[6] - 1
    move = U[ply, 6]
    captured = U[ply, 0]
    S[6] = ply
    S[0] = 1 - S[0]
    side = S[0]
    them = 1 - side
    S[1] = U[ply, 1]
    S[2] = U[ply, 2]
    S[3] = U[ply, 3]
    S[4] = U[ply, 4]
    S[5] = U[ply, 5]
    fr = move & 63
    to = (move >> 6) & 63
    promo = (move >> 12) & 7
    flags = move >> 15
    from_bb = np.int64(1) << fr
    to_bb = np.int64(1) << to
    piece = M[to]
    if promo:
        B[piece] ^= to_bb
        piece = 1 + 6 * side
        B[piece] ^= to_bb
    both = from_bb | to_bb
    B[piece] ^= both
    O[side] ^= both
    O[2] ^= both
    M[fr] = piece
    M[to] = 0
    if flags & FLAG_EP:
        cap_sq = to - 8 if side == 0 else to + 8
        cap_bb = np.int64(1) << cap_sq
        B[captured] |= cap_bb
        O[them] |= cap_bb
        O[2] |= cap_bb
        M[cap_sq] = captured
    elif captured:
        B[captured] |= to_bb
        O[them] |= to_bb
        O[2] |= to_bb
        M[to] = captured
    if flags & FLAG_CASTLE:
        if to == 6:
            rf, rt = 7, 5
        elif to == 2:
            rf, rt = 0, 3
        elif to == 62:
            rf, rt = 63, 61
        else:
            rf, rt = 56, 59
        rook = 4 + 6 * side
        rb = (np.int64(1) << rf) | (np.int64(1) << rt)
        B[rook] ^= rb
        O[side] ^= rb
        O[2] ^= rb
        M[rf] = rook
        M[rt] = 0


@njit(cache=False)
def make_null(B, O, M, S, U):
    ply = S[6]
    U[ply, 1] = S[1]
    U[ply, 2] = S[2]
    U[ply, 3] = S[3]
    U[ply, 4] = S[4]
    U[ply, 5] = S[5]
    U[ply, 6] = 0
    key = S[4] ^ ep_key_term(B, S) ^ ZSIDE
    S[0] = 1 - S[0]
    S[2] = -1
    S[3] += 1
    S[4] = key
    S[6] = ply + 1


@njit(cache=False)
def unmake_null(B, O, M, S, U):
    ply = S[6] - 1
    S[6] = ply
    S[0] = 1 - S[0]
    S[1] = U[ply, 1]
    S[2] = U[ply, 2]
    S[3] = U[ply, 3]
    S[4] = U[ply, 4]
    S[5] = U[ply, 5]


# ------------------------------------------------------------- generation


@njit(cache=False)
def _add_pawn_moves(ML, n, fr, to, flags, promo_rank_bb):
    to_bb = np.int64(1) << to
    if to_bb & promo_rank_bb:
        ML[n] = fr | (to << 6) | (5 << 12)
        ML[n + 1] = fr | (to << 6) | (4 << 12)
        ML[n + 2] = fr | (to << 6) | (3 << 12)
        ML[n + 3] = fr | (to << 6) | (2 << 12)
        return n + 4
    ML[n] = fr | (to << 6) | (flags << 15)
    return n + 1


@njit(cache=False)
def gen_moves(B, O, M, S, ML, captures_only):
    """Pseudo-legal moves into ``ML``; returns the count.

    ``captures_only`` produces captures, en passant and queen promotions
    (the quiescence set); the caller still has to test legality by making
    the move and asking whether its own king is attacked.
    """
    side = S[0]
    them = 1 - side
    base = 6 * side
    occ = O[2]
    own = O[side]
    enemy = O[them]
    empty = ~occ
    n = 0

    # Pawns.
    pawns = B[1 + base]
    if side == 0:
        promo_rank = RANK_8
        single = (pawns << 8) & empty
        double = ((single & RANK_3) << 8) & empty
    else:
        promo_rank = RANK_1
        single = shr8(pawns) & empty
        double = shr8(single & RANK_6) & empty
    if captures_only:
        single &= promo_rank
        double = 0
    bb = single
    while bb:
        to = lsb(bb)
        bb &= bb - 1
        fr = to - 8 if side == 0 else to + 8
        if captures_only:
            ML[n] = fr | (to << 6) | (5 << 12)
            n += 1
        else:
            n = _add_pawn_moves(ML, n, fr, to, 0, promo_rank)
    bb = double
    while bb:
        to = lsb(bb)
        bb &= bb - 1
        fr = to - 16 if side == 0 else to + 16
        ML[n] = fr | (to << 6) | (FLAG_DPP << 15)
        n += 1
    bb = pawns
    while bb:
        fr = lsb(bb)
        bb &= bb - 1
        att = PAWN_ATT[side, fr] & enemy
        while att:
            to = lsb(att)
            att &= att - 1
            if captures_only:
                if (np.int64(1) << to) & promo_rank:
                    ML[n] = fr | (to << 6) | (5 << 12)
                    n += 1
                else:
                    ML[n] = fr | (to << 6)
                    n += 1
            else:
                n = _add_pawn_moves(ML, n, fr, to, 0, promo_rank)
    ep = S[2]
    if ep >= 0:
        att = PAWN_ATT[them, ep] & pawns
        while att:
            fr = lsb(att)
            att &= att - 1
            ML[n] = fr | (ep << 6) | (FLAG_EP << 15)
            n += 1

    target = enemy if captures_only else ~own

    bb = B[2 + base]
    while bb:
        fr = lsb(bb)
        bb &= bb - 1
        att = KNIGHT_ATT[fr] & target
        while att:
            to = lsb(att)
            att &= att - 1
            ML[n] = fr | (to << 6)
            n += 1
    bb = B[3 + base]
    while bb:
        fr = lsb(bb)
        bb &= bb - 1
        att = bishop_attacks(fr, occ) & target
        while att:
            to = lsb(att)
            att &= att - 1
            ML[n] = fr | (to << 6)
            n += 1
    bb = B[4 + base]
    while bb:
        fr = lsb(bb)
        bb &= bb - 1
        att = rook_attacks(fr, occ) & target
        while att:
            to = lsb(att)
            att &= att - 1
            ML[n] = fr | (to << 6)
            n += 1
    bb = B[5 + base]
    while bb:
        fr = lsb(bb)
        bb &= bb - 1
        att = (rook_attacks(fr, occ) | bishop_attacks(fr, occ)) & target
        while att:
            to = lsb(att)
            att &= att - 1
            ML[n] = fr | (to << 6)
            n += 1
    king = B[6 + base]
    if king:
        fr = lsb(king)
        att = KING_ATT[fr] & target
        while att:
            to = lsb(att)
            att &= att - 1
            ML[n] = fr | (to << 6)
            n += 1
        if not captures_only:
            rights = S[1]
            if side == 0:
                if (rights & 1) and fr == 4 and (M[7] == 4) and not (occ & 0x60):
                    if (not is_attacked(B, 4, 1, occ) and not is_attacked(B, 5, 1, occ)
                            and not is_attacked(B, 6, 1, occ)):
                        ML[n] = 4 | (6 << 6) | (FLAG_CASTLE << 15)
                        n += 1
                if (rights & 2) and fr == 4 and (M[0] == 4) and not (occ & 0x0E):
                    if (not is_attacked(B, 4, 1, occ) and not is_attacked(B, 3, 1, occ)
                            and not is_attacked(B, 2, 1, occ)):
                        ML[n] = 4 | (2 << 6) | (FLAG_CASTLE << 15)
                        n += 1
            else:
                if (rights & 4) and fr == 60 and (M[63] == 10) and not (occ & 0x6000000000000000):
                    if (not is_attacked(B, 60, 0, occ) and not is_attacked(B, 61, 0, occ)
                            and not is_attacked(B, 62, 0, occ)):
                        ML[n] = 60 | (62 << 6) | (FLAG_CASTLE << 15)
                        n += 1
                if (rights & 8) and fr == 60 and (M[56] == 10) and not (occ & 0x0E00000000000000):
                    if (not is_attacked(B, 60, 0, occ) and not is_attacked(B, 59, 0, occ)
                            and not is_attacked(B, 58, 0, occ)):
                        ML[n] = 60 | (58 << 6) | (FLAG_CASTLE << 15)
                        n += 1
    return n


@njit(cache=False)
def is_legal_after_make(B, O, S):
    """After ``make_move``: was the move legal (the mover's king is safe)?"""
    mover = 1 - S[0]
    return not is_attacked(B, lsb(B[6 + 6 * mover]), S[0], O[2])


@njit(cache=False)
def pinned_pieces(B, O, S):
    """Own pieces that shield the own king from an enemy slider."""
    side = S[0]
    base = 6 * side
    ebase = 6 * (1 - side)
    king = lsb(B[6 + base])
    occ = O[2]
    own = O[side]
    pinned = np.int64(0)
    snipers = (rook_attacks(king, 0) & (B[4 + ebase] | B[5 + ebase])) | (
        bishop_attacks(king, 0) & (B[3 + ebase] | B[5 + ebase]))
    while snipers:
        s = lsb(snipers)
        snipers &= snipers - 1
        between = BETWEEN[king, s] & occ
        if between and (between & (between - 1)) == 0 and (between & own):
            pinned |= between
    return pinned


@njit(cache=False)
def has_legal_move(B, O, M, S, U, ML):
    """Does the side to move, **out of check**, have a legal move? Exact."""
    side = S[0]
    base = 6 * side
    own = O[side]
    enemy = O[1 - side]
    occ = O[2]
    free = own & ~pinned_pieces(B, O, S)
    not_own = ~own
    bb = B[2 + base] & free
    while bb:
        sq = lsb(bb)
        bb &= bb - 1
        if KNIGHT_ATT[sq] & not_own:
            return True
    pawns = B[1 + base] & free
    if pawns:
        pushes = ((pawns << 8) if side == 0 else shr8(pawns)) & ~occ
        if pushes:
            return True
        scan = pawns
        while scan:
            sq = lsb(scan)
            scan &= scan - 1
            if PAWN_ATT[side, sq] & enemy:
                return True
    bb = (B[3 + base] | B[5 + base]) & free
    while bb:
        sq = lsb(bb)
        bb &= bb - 1
        if bishop_attacks(sq, occ) & not_own:
            return True
    bb = (B[4 + base] | B[5 + base]) & free
    while bb:
        sq = lsb(bb)
        bb &= bb - 1
        if rook_attacks(sq, occ) & not_own:
            return True
    n = gen_moves(B, O, M, S, ML, False)
    for i in range(n):
        make_move(B, O, M, S, U, ML[i])
        legal = is_legal_after_make(B, O, S)
        unmake_move(B, O, M, S, U)
        if legal:
            return True
    return False


@njit(cache=False)
def any_legal_move(B, O, M, S, U, ML):
    """Does the side to move have a legal move (in or out of check)? Exact."""
    n = gen_moves(B, O, M, S, ML, False)
    for i in range(n):
        make_move(B, O, M, S, U, ML[i])
        legal = is_legal_after_make(B, O, S)
        unmake_move(B, O, M, S, U)
        if legal:
            return True
    return False


@njit(cache=False)
def perft(B, O, M, S, U, MLS, depth):
    ply = S[6]
    n = gen_moves(B, O, M, S, MLS[ply], False)
    if depth == 1:
        count = 0
        for i in range(n):
            make_move(B, O, M, S, U, MLS[ply, i])
            if is_legal_after_make(B, O, S):
                count += 1
            unmake_move(B, O, M, S, U)
        return count
    total = 0
    for i in range(n):
        make_move(B, O, M, S, U, MLS[ply, i])
        if is_legal_after_make(B, O, S):
            total += perft(B, O, M, S, U, MLS, depth - 1)
        unmake_move(B, O, M, S, U)
    return total


# ------------------------------------------------------------- evaluation


@njit(cache=False)
def is_material_draw(B):
    if B[1] | B[7] | B[4] | B[10] | B[5] | B[11]:
        return False
    knights = B[2] | B[8]
    bishops = B[3] | B[9]
    count = popcount(knights | bishops)
    if count <= 1:
        return True
    if knights:
        return False
    return (bishops & DARK_SQUARES) == 0 or (bishops & LIGHT_SQUARES) == 0


@njit(cache=False)
def mop_up_bonus(B):
    """White's-point-of-view mating gradient; zero unless one side is a bare king.

    The same gate as ``cs_mopup.mop_up``: the defender must have nothing but
    its king, and the attacker must hold at least one rook or queen. Every
    other position, including K+B+N and K+B+B against a bare king, scores
    exactly zero, so ordinary play is untouched.
    """
    black_pieces = B[7] | B[8] | B[9] | B[10] | B[11]
    if black_pieces == 0:
        if (B[4] | B[5]) == 0:
            return 0
        their = lsb(B[12])
        our = lsb(B[6])
        return MOPUP_EDGE_BONUS[their] + MOPUP_PROX_BONUS[our, their]
    white_pieces = B[1] | B[2] | B[3] | B[4] | B[5]
    if white_pieces == 0:
        if (B[10] | B[11]) == 0:
            return 0
        their = lsb(B[6])
        our = lsb(B[12])
        return -(MOPUP_EDGE_BONUS[their] + MOPUP_PROX_BONUS[our, their])
    return 0


@njit(cache=False)
def evaluate(B, S):
    """C5's evaluation: tapered PeSTO + bishop pair + tempo, side to move's view."""
    packed = S[5]
    phase = popcount(B[2] | B[8] | B[3] | B[9]) + 2 * popcount(B[4] | B[10]) + 4 * popcount(
        B[5] | B[11])
    if phase > TOTAL_PHASE:
        phase = TOTAL_PHASE
    if popcount(B[3]) > 1:
        packed += BISHOP_PAIR_PACKED
    if popcount(B[9]) > 1:
        packed -= BISHOP_PAIR_PACKED
    eg = packed & 0xFFFF
    if eg >= 0x8000:
        eg -= 0x10000
    mg = (packed - eg) >> 16
    total = mg * phase + eg * (TOTAL_PHASE - phase)
    if total >= 0:
        score = total // TOTAL_PHASE
    else:
        score = -((-total) // TOTAL_PHASE)
    score += mop_up_bonus(B)
    if S[0] == 0:
        return score + TEMPO
    return -score + TEMPO


@njit(cache=False)
def compute_packed(M):
    packed = 0
    for sq in range(64):
        p = M[sq]
        if p:
            packed += PSTV[p, sq]
    return packed


@njit(cache=False)
def compute_key(B, M, S):
    key = np.int64(0)
    for sq in range(64):
        p = M[sq]
        if p:
            key ^= ZP[p, sq]
    key ^= ZC[S[1]]
    if S[0] == 1:
        key ^= ZSIDE
    key ^= ep_key_term(B, S)
    return key


# --------------------------------------------------------------------- SEE


@njit(cache=False)
def _least_valuable(B, attackers, colour):
    side = attackers & (B[1 + 6 * colour] | B[2 + 6 * colour] | B[3 + 6 * colour]
                        | B[4 + 6 * colour] | B[5 + 6 * colour] | B[6 + 6 * colour])
    if side == 0:
        return np.int64(0), 0
    base = 6 * colour
    for pt in range(1, 7):
        subset = side & B[pt + base]
        if subset:
            return subset & -subset, pt
    return np.int64(0), 0


@njit(cache=False)
def see(B, O, M, S, move, gains):
    """Centipawn outcome of the exchange on the target square, for the mover."""
    fr = move & 63
    to = (move >> 6) & 63
    promo = (move >> 12) & 7
    flags = move >> 15
    side = S[0]
    captured = M[to]
    if captured == 0:
        if flags & FLAG_EP:
            captured = 1
        else:
            return 0
    attacker = M[fr]
    if attacker == 0:
        return 0
    cap_t = captured if captured <= 6 else captured - 6
    att_t = attacker if attacker <= 6 else attacker - 6
    gains[0] = PIECE_VALUE[cap_t]
    occ = O[2] & ~(np.int64(1) << fr)
    if flags & FLAG_EP:
        cap_sq = to - 8 if side == 0 else to + 8
        occ &= ~(np.int64(1) << cap_sq)
    on_square = promo if promo else att_t
    if promo:
        gains[0] += PIECE_VALUE[promo] - PIECE_VALUE[1]
    colour = 1 - side
    attackers = attackers_to(B, to, occ) & occ
    depth = 0
    while True:
        square_mask, pt = _least_valuable(B, attackers, colour)
        if square_mask == 0:
            break
        depth += 1
        gains[depth] = PIECE_VALUE[on_square] - gains[depth - 1]
        if pt == 6 and (attackers & O[1 - colour]):
            depth -= 1
            break
        on_square = pt
        occ &= ~square_mask
        attackers = attackers_to(B, to, occ) & occ
        colour = 1 - colour
        if depth >= 30:
            break
    while depth:
        a = -gains[depth - 1]
        b = gains[depth]
        gains[depth - 1] = -(a if a > b else b)
        depth -= 1
    return gains[0]


# ----------------------------------------------------------------- ordering


@njit(cache=False)
def score_moves(B, O, M, S, ML, MS, n, tt_move, killer_1, killer_2, HIST, gains):
    """C5's ``order_moves`` scores; losing captures are demoted by SEE."""
    side = S[0]
    enemy = O[1 - side]
    hbase = 4096 if side == 0 else 0
    for i in range(n):
        move = ML[i]
        if move == tt_move:
            MS[i] = TT_BONUS
            continue
        fr = move & 63
        to = (move >> 6) & 63
        promo = (move >> 12) & 7
        flags = move >> 15
        to_bb = np.int64(1) << to
        if to_bb & enemy:
            victim = M[to]
            victim_t = victim if victim <= 6 else victim - 6
            attacker = M[fr]
            attacker_t = attacker if attacker <= 6 else attacker - 6
            sc = CAPTURE_BONUS + PIECE_VALUE[victim_t] * 16 - PIECE_VALUE[attacker_t]
            if promo:
                sc += PROMO_BONUS if promo == 5 else -PROMO_BONUS
            elif PIECE_VALUE[victim_t] < PIECE_VALUE[attacker_t] and see(B, O, M, S, move, gains) < 0:
                sc = LOSING_CAPTURE + PIECE_VALUE[victim_t] * 16 - PIECE_VALUE[attacker_t]
            MS[i] = sc
            continue
        if promo:
            MS[i] = PROMO_BONUS if promo == 5 else 0
            continue
        if flags & FLAG_EP:
            MS[i] = CAPTURE_BONUS + PIECE_VALUE[1] * 16 - PIECE_VALUE[1]
            continue
        if move == killer_1:
            MS[i] = KILLER_1
            continue
        if move == killer_2:
            MS[i] = KILLER_2
            continue
        MS[i] = HIST[hbase + (fr << 6) + to]


@njit(cache=False)
def score_captures(M, ML, MS, n):
    """C5's ``order_captures``: MVV-LVA, a promotion bonus, quiet evasions low."""
    for i in range(n):
        move = ML[i]
        fr = move & 63
        to = (move >> 6) & 63
        promo = (move >> 12) & 7
        victim = M[to]
        victim_t = victim if victim <= 6 else victim - 6
        victim_value = PIECE_VALUE[victim_t] if victim else PIECE_VALUE[1]
        attacker = M[fr]
        attacker_t = attacker if attacker <= 6 else attacker - 6
        sc = victim_value * 16 - PIECE_VALUE[attacker_t]
        if promo == 5:
            sc += PROMO_BONUS
        MS[i] = sc


@njit(cache=False)
def pick_next(ML, MS, n, i):
    """Move the best-scored remaining move into slot ``i`` (stable on ties)."""
    best = i
    best_score = MS[i]
    for j in range(i + 1, n):
        if MS[j] > best_score:
            best = j
            best_score = MS[j]
    if best != i:
        tm = ML[i]
        ts = MS[i]
        ML[i] = ML[best]
        MS[i] = MS[best]
        ML[best] = tm
        MS[best] = ts
    return ML[i]


@njit(cache=False)
def update_history(HIST, side, move, depth):
    fr = move & 63
    to = (move >> 6) & 63
    index = (4096 if side == 0 else 0) + (fr << 6) + to
    value = HIST[index] + depth * depth
    if value > HISTORY_CAP:
        for i in range(8192):
            HIST[i] >>= 1
        value >>= 1
    HIST[index] = value


# ---------------------------------------------------------- transposition


@njit(cache=False)
def tt_probe(TK, TV, key):
    index = key & ((1 << TT_BITS) - 1)
    if TK[index] == key:
        return TV[index]
    return np.int64(-1)


@njit(cache=False)
def tt_store(TK, TV, key, depth, score, bound, move):
    index = key & ((1 << TT_BITS) - 1)
    if TK[index] == key:
        old = TV[index]
        if old >= 0 and ((old >> 16) & 0xFF) > depth:
            return
    TK[index] = key
    TV[index] = (score + 32768) | (depth << 16) | (bound << 24) | (move << 26)


@njit(cache=False)
def tt_depth(v):
    return (v >> 16) & 0xFF


@njit(cache=False)
def tt_score(v):
    return (v & 0xFFFF) - 32768


@njit(cache=False)
def tt_bound(v):
    return (v >> 24) & 3


@njit(cache=False)
def tt_move(v):
    return v >> 26


@njit(cache=False)
def score_to_tt(score, ply):
    if score > MATE_BOUND:
        return score + ply
    if score < -MATE_BOUND:
        return score - ply
    return score


@njit(cache=False)
def score_from_tt(score, ply):
    if score > MATE_BOUND:
        return score - ply
    if score < -MATE_BOUND:
        return score + ply
    return score


# ------------------------------------------------------------------- rules


@njit(cache=False)
def rules_outcome(B, O, M, S, U, ML, checked, ply):
    """The score the rules force, or -INFINITY - 1 when play continues."""
    if S[3] >= 99:
        if not any_legal_move(B, O, M, S, U, ML):
            return -MATE_SCORE + ply if checked else DRAW_SCORE
        if S[3] >= 100:
            return DRAW_SCORE
        # Clock 99: claimable if some legal non-zeroing move leaves the
        # opponent a legal move (python-chess can_claim_fifty_moves).
        n = gen_moves(B, O, M, S, ML, False)
        side = S[0]
        for i in range(n):
            move = ML[i]
            fr = move & 63
            to = (move >> 6) & 63
            if M[fr] == 1 + 6 * side or M[to] != 0 or (move >> 15) & FLAG_EP:
                continue
            make_move(B, O, M, S, U, move)
            ok = is_legal_after_make(B, O, S)
            if ok:
                ok = any_legal_move(B, O, M, S, U, ML[128:])
            unmake_move(B, O, M, S, U)
            if ok:
                return DRAW_SCORE
    if is_material_draw(B):
        return DRAW_SCORE
    return -INFINITY - 1


# ------------------------------------------------------------------ search


@njit(cache=False)
def _check_time(CTL, TCTL):
    CTL[2] += 1
    if (CTL[2] & (CHECK_INTERVAL - 1)) == 0:
        with objmode(t="f8"):
            t = perf_counter()
        if t >= TCTL[0]:
            CTL[0] = 1


@njit(cache=False)
def quiescence(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL, GAINS,
               alpha, beta, ply, qply):
    _check_time(CTL, TCTL)
    CTL[3] += 1
    if CTL[0]:
        return 0
    ML = MLS[ply]
    MS = MSS[ply]
    checked = in_check(B, O, S)
    forced = rules_outcome(B, O, M, S, U, ML, checked, ply)
    if forced != -INFINITY - 1:
        return forced
    at_cap = qply >= QS_MAX_PLY or ply >= MAX_PLY - 2
    side = S[0]
    if checked:
        n = gen_moves(B, O, M, S, ML, False)
        # Keep only legal evasions; mate if none.
        legal = 0
        for i in range(n):
            make_move(B, O, M, S, U, ML[i])
            ok = is_legal_after_make(B, O, S)
            unmake_move(B, O, M, S, U)
            if ok:
                ML[legal] = ML[i]
                legal += 1
        n = legal
        if n == 0:
            return -MATE_SCORE + ply
        if at_cap:
            return evaluate(B, S)
        score_captures(M, ML, MS, n)
        best_score = -INFINITY
        stand_pat = -INFINITY
    else:
        if at_cap:
            if not has_legal_move(B, O, M, S, U, ML):
                return DRAW_SCORE
            return evaluate(B, S)
        stand_pat = evaluate(B, S)
        if stand_pat >= beta:
            if has_legal_move(B, O, M, S, U, ML):
                return stand_pat
            return DRAW_SCORE
        if stand_pat > alpha:
            alpha = stand_pat
        best_score = stand_pat
        n = gen_moves(B, O, M, S, ML, True)
        if n == 0:
            if has_legal_move(B, O, M, S, U, ML):
                return stand_pat
            return DRAW_SCORE
        score_captures(M, ML, MS, n)

    # Tactical moves are pseudo-legal here (the reference filters them through
    # python-chess first), so a position whose every capture is illegal must
    # still be told apart from a stalemate: `searched` counts the moves that
    # proved legal, and a non-check node that found none asks has_legal_move
    # before it is allowed to return the stand-pat score.
    searched = 0
    for i in range(n):
        move = pick_next(ML, MS, n, i)
        losing = False
        if not checked:
            to = (move >> 6) & 63
            victim = M[to]
            victim_t = victim if victim <= 6 else victim - 6
            gain = PIECE_VALUE[victim_t] if victim else PIECE_VALUE[1]
            if ((move >> 12) & 7) == 5:
                gain += PIECE_VALUE[5]
            if stand_pat + gain + DELTA_MARGIN < alpha:
                continue
            losing = see(B, O, M, S, move, GAINS) < 0
        make_move(B, O, M, S, U, move)
        if not is_legal_after_make(B, O, S):
            unmake_move(B, O, M, S, U)
            continue
        searched += 1
        if losing and not in_check(B, O, S):
            unmake_move(B, O, M, S, U)
            continue
        score = -quiescence(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL,
                            GAINS, -beta, -alpha, ply + 1, qply + 1)
        unmake_move(B, O, M, S, U)
        if CTL[0]:
            return 0
        if score > best_score:
            best_score = score
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    CTL[4] += 1
                    break
    if searched == 0 and not checked:
        if not has_legal_move(B, O, M, S, U, ML):
            return DRAW_SCORE
    return best_score


@njit(cache=False)
def negamax(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL, GAINS,
            depth, alpha, beta, ply, allow_null):
    _check_time(CTL, TCTL)
    if CTL[0]:
        return 0
    ML = MLS[ply]
    MS = MSS[ply]

    if S[3] >= 99:
        forced = rules_outcome(B, O, M, S, U, ML, in_check(B, O, S), ply)
        if forced != -INFINITY - 1:
            return forced
    elif is_material_draw(B):
        return DRAW_SCORE

    key = S[4]
    # Repetition on the path (same side to move, stride two) and against the
    # positions the engine has already been handed this game.
    index = ply - 2
    limit = ply - S[3]
    if limit < 0:
        limit = 0
    while index >= limit:
        if PATH[index] == key:
            return DRAW_SCORE
        index -= 2
    ngame = CTL[10]
    for g in range(ngame):
        if GK[g] == key:
            return DRAW_SCORE
    PATH[ply] = key

    tt_usable = S[3] < TT_HALFMOVE_LIMIT
    CTL[7] += 1
    entry = tt_probe(TK, TV, key)
    ttm = 0
    if entry >= 0:
        CTL[8] += 1
        ttm = tt_move(entry)
        entry_depth = tt_depth(entry) if tt_usable else -1
        if entry_depth >= depth:
            non_pv = beta - alpha == 1
            score = score_from_tt(tt_score(entry), ply)
            bound = tt_bound(entry)
            if bound == BOUND_EXACT:
                return score
            elif non_pv:
                if bound == BOUND_LOWER:
                    if score >= beta:
                        return score
                elif score <= alpha:
                    return score

    if depth <= 0:
        return quiescence(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL,
                          GAINS, alpha, beta, ply, 0)

    checked = in_check(B, O, S)
    if ply >= MAX_PLY - 2:
        if not any_legal_move(B, O, M, S, U, ML):
            return -MATE_SCORE + ply if checked else DRAW_SCORE
        return evaluate(B, S)

    side = S[0]
    base = 6 * side

    if (not checked and depth <= RFP_MAX_DEPTH and beta - alpha == 1
            and -MATE_BOUND < beta < MATE_BOUND):
        static = evaluate(B, S)
        if static - RFP_MARGIN * depth >= beta:
            return static

    if (allow_null and not checked and depth >= 3 and beta - alpha == 1
            and (O[side] & ~(B[1 + base] | B[6 + base]))):
        reduction = 3 if depth > 6 else 2
        make_null(B, O, M, S, U)
        null_score = -negamax(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL,
                              GAINS, depth - 1 - reduction, -beta, -beta + 1, ply + 1, False)
        unmake_null(B, O, M, S, U)
        if CTL[0]:
            return 0
        if null_score >= beta:
            return beta if null_score > MATE_BOUND else null_score

    n = gen_moves(B, O, M, S, ML, False)
    killer_1 = KILL[ply * 2]
    killer_2 = KILL[ply * 2 + 1]
    score_moves(B, O, M, S, ML, MS, n, ttm, killer_1, killer_2, HIST, GAINS)

    original_alpha = alpha
    best_score = -INFINITY
    best_move = 0
    child_depth = depth - 1
    enemy = O[1 - side]
    can_reduce = depth >= 3 and not checked
    move_index = -1

    for i in range(n):
        move = pick_next(ML, MS, n, i)
        fr = move & 63
        to = (move >> 6) & 63
        promo = (move >> 12) & 7
        flags = move >> 15
        is_capture = ((np.int64(1) << to) & enemy) != 0 or (flags & FLAG_EP) != 0

        make_move(B, O, M, S, U, move)
        if not is_legal_after_make(B, O, S):
            unmake_move(B, O, M, S, U)
            continue
        move_index += 1

        reduction = 0
        if (move_index >= LMR_START and can_reduce and not is_capture and promo == 0
                and move != killer_1 and move != killer_2):
            if move_index >= LMR_R2_INDEX and depth >= LMR_R2_DEPTH:
                reduction = 2
            else:
                reduction = 1
            if reduction > child_depth - 1:
                reduction = child_depth - 1
            if reduction > 0 and in_check(B, O, S):
                reduction = 0

        if move_index == 0:
            score = -negamax(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL,
                             GAINS, child_depth, -beta, -alpha, ply + 1, True)
        else:
            score = -negamax(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL,
                             GAINS, child_depth - reduction, -alpha - 1, -alpha, ply + 1, True)
            if reduction and score > alpha and not CTL[0]:
                score = -negamax(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL,
                                 TCTL, GAINS, child_depth, -alpha - 1, -alpha, ply + 1, True)
            if alpha < score < beta and not CTL[0]:
                score = -negamax(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL,
                                 TCTL, GAINS, child_depth, -beta, -alpha, ply + 1, True)
        unmake_move(B, O, M, S, U)
        if CTL[0]:
            return 0

        if score > best_score:
            best_score = score
            best_move = move
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    CTL[4] += 1
                    if not is_capture and promo == 0:
                        if KILL[ply * 2] != move:
                            KILL[ply * 2 + 1] = KILL[ply * 2]
                            KILL[ply * 2] = move
                        update_history(HIST, side, move, depth)
                    break

    if move_index < 0:
        return -MATE_SCORE + ply if checked else DRAW_SCORE

    if best_score >= beta:
        bound = BOUND_LOWER
    elif best_score > original_alpha:
        bound = BOUND_EXACT
    else:
        bound = BOUND_UPPER
    if tt_usable:
        tt_store(TK, TV, key, depth, score_to_tt(best_score, ply), bound, best_move)
    return best_score


@njit(cache=False)
def search_root(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL, GAINS,
                ROOT, RS, nroot, depth, alpha, beta):
    """C5's root loop: full window for every move, partial-move commit.

    ``ROOT`` holds the root moves in search order, ``RS`` receives their
    scores. ``CTL[5]``/``CTL[6]`` receive the partial move and score (a move
    fully searched at this depth that beat the original alpha).
    """
    original_alpha = alpha
    best_score = -INFINITY
    best_move = ROOT[0]
    PATH[0] = S[4]
    for i in range(nroot):
        move = ROOT[i]
        make_move(B, O, M, S, U, move)
        score = -negamax(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL, GAINS,
                         depth - 1, -beta, -alpha, 1, True)
        unmake_move(B, O, M, S, U)
        if CTL[0]:
            RS[i] = -INFINITY
            for j in range(i + 1, nroot):
                RS[j] = -INFINITY
            return best_score, best_move
        RS[i] = score
        if score > best_score:
            best_score = score
            best_move = move
            if score > original_alpha:
                CTL[5] = move
                CTL[6] = score
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    for j in range(i + 1, nroot):
                        RS[j] = -INFINITY
                    break
    return best_score, best_move


# ---------------------------------------------------------------- loading


def new_board_arrays():
    B = np.zeros(13, dtype=np.int64)
    O = np.zeros(3, dtype=np.int64)
    M = np.zeros(64, dtype=np.int64)
    S = np.zeros(8, dtype=np.int64)
    U = np.zeros((STACK, 8), dtype=np.int64)
    return B, O, M, S, U


def load_board(board: chess.Board, B, O, M, S) -> None:
    """Fill the arrays from a python-chess board."""
    B[:] = 0
    O[:] = 0
    M[:] = 0
    for sq, piece in board.piece_map().items():
        code = piece.piece_type + (0 if piece.color else 6)
        M[sq] = code
        B[code] |= np.int64(_to_i64(1 << sq))
    O[0] = _to_i64(int(board.occupied_co[chess.WHITE]))
    O[1] = _to_i64(int(board.occupied_co[chess.BLACK]))
    O[2] = O[0] | O[1]
    S[0] = 0 if board.turn else 1
    rights = 0
    cr = board.castling_rights
    if cr & chess.BB_H1:
        rights |= 1
    if cr & chess.BB_A1:
        rights |= 2
    if cr & chess.BB_H8:
        rights |= 4
    if cr & chess.BB_A8:
        rights |= 8
    S[1] = rights
    S[2] = board.ep_square if board.ep_square is not None else -1
    S[3] = board.halfmove_clock
    S[6] = 0
    S[5] = compute_packed(M)
    S[4] = compute_key(B, M, S)


def move_to_uci(move: int) -> str:
    fr = move & 63
    to = (move >> 6) & 63
    promo = (move >> 12) & 7
    text = chess.SQUARE_NAMES[fr] + chess.SQUARE_NAMES[to]
    if promo:
        text += chess.piece_symbol(promo)
    return text


def move_to_chess(move: int) -> chess.Move:
    return chess.Move(move & 63, (move >> 6) & 63, ((move >> 12) & 7) or None)


def encode_move(board: chess.Board, move: chess.Move) -> int:
    """Encode a python-chess move for this board (flags derived from the board)."""
    code = move.from_square | (move.to_square << 6)
    if move.promotion:
        code |= move.promotion << 12
    piece = board.piece_type_at(move.from_square)
    if piece == chess.PAWN:
        if move.to_square == board.ep_square and abs(move.from_square - move.to_square) in (7, 9):
            code |= FLAG_EP << 15
        elif abs(move.from_square - move.to_square) == 16:
            code |= FLAG_DPP << 15
    elif piece == chess.KING and abs((move.from_square & 7) - (move.to_square & 7)) == 2:
        code |= FLAG_CASTLE << 15
    return code
