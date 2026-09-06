"""Passed-pawn evaluation, v1: one bonus, indexed by relative rank.

The blind-win audit found the endgame static blind to won positions: pawn
endings at the end of Stockfish's own line scored +4 where Stockfish said
+616, and the gap grew with the winner's most advanced passer, from about
+324 at ranks 1-3 to +665 at ranks 6-7. The PeSTO pawn tables already reward
advancement, so the information the evaluator lacks is not "this pawn is far
up the board" but "this pawn is far up the board and no enemy pawn can ever
stop it". This module adds exactly that and nothing else.

**Definition.** A pawn is passed when no enemy pawn stands ahead of it on
its own file or either adjacent file. "Ahead" is colour-correct: toward the
eighth rank for White, toward the first for Black. Enemy pawns level with or
behind the pawn do not disqualify it, and pieces of either colour in its path
are ignored -- a blocked passer is still a passer; whether it can advance is
the search's job.

**Doubled passers.** Two own pawns on one file can both satisfy the
definition. Only the most advanced is scored, so a doubled passer is one
passer, not two. This is a counting rule, not a doubled-pawn penalty.

**Value.** ``PASSED_MG[r]`` and ``PASSED_EG[r]`` by relative rank ``r``
(0 = own back rank, 7 = promotion rank), both monotonic in advancement, the
endgame table the larger. The pair is added to the evaluator's packed
middlegame/endgame total before the taper, so it is phased exactly as every
other term and there is no cutoff. Deliberately no king distances, no square
rule, no connected or protected or blocked adjustments: v1 tests the one
hypothesis that knowing a pawn is passed is worth something, and its result
must be attributable to that alone.

The tables were chosen once from a predefined family on the diagnostic half
of the blind-win regression suite and then frozen; see
`benchmarks/current/2026-09-03-passed-pawn-v1.md`.
"""

from __future__ import annotations

import chess

# Indexed by relative rank. Index 0 and 7 are unreachable for a pawn and stay 0.
PASSED_MG = (0, 0, 2, 4, 8, 16, 28, 0)
PASSED_EG = (0, 4, 8, 16, 32, 56, 88, 0)


def _ahead_on_file(square: int, white: bool) -> int:
    """Squares strictly ahead of ``square`` on its own file, for the given colour."""
    file_mask = chess.BB_FILES[square & 7]
    rank = square >> 3
    if white:
        return file_mask & ~((1 << (8 * (rank + 1))) - 1)
    return file_mask & ((1 << (8 * rank)) - 1)


def _front_span(square: int, white: bool) -> int:
    """Squares strictly ahead on the pawn's file and both neighbouring files."""
    file = square & 7
    span = _ahead_on_file(square, white)
    for adjacent in (file - 1, file + 1):
        if 0 <= adjacent < 8:
            span |= _ahead_on_file(chess.square(adjacent, square >> 3), white)
    return span


def is_passed(board: chess.Board, square: int, white: bool) -> bool:
    """The definition, written out: no enemy pawn ahead on the three files."""
    enemy_pawns = board.pawns & board.occupied_co[not white]
    return not (_front_span(square, white) & enemy_pawns)


def passed_pawns_reference(board: chess.Board) -> tuple[int, int]:
    """White's-point-of-view (middlegame, endgame) bonus, written to be obviously right.

    Not used in search; the fast version is tested against it.
    """
    mg = 0
    eg = 0
    for white, sign in ((True, 1), (False, -1)):
        own = board.pawns & board.occupied_co[white]
        for square in chess.scan_forward(own):
            if not is_passed(board, square, white):
                continue
            if _ahead_on_file(square, white) & own:
                continue  # doubled: only the front pawn of the file is scored
            rank = square >> 3
            relative = rank if white else 7 - rank
            mg += sign * PASSED_MG[relative]
            eg += sign * PASSED_EG[relative]
    return mg, eg


# The hot path never loops over all pawns. Squares an enemy pawn controls or
# occupies ahead of a pawn are computed for the whole board at once with a
# file fill (three shifts), widened to the neighbouring files (two shifts), and
# the same fill of the side's own pawns gives the "own pawn ahead" test for the
# doubled rule. What remains is the passer set, usually empty, and only that is
# looped over to read the rank table. The packed table holds (mg << 16) + eg,
# the evaluator's format.
_ALL = 0xFFFF_FFFF_FFFF_FFFF
_NOT_A = ~chess.BB_FILE_A & _ALL
_NOT_H = ~chess.BB_FILE_H & _ALL
_W_PACKED = tuple((PASSED_MG[sq >> 3] << 16) + PASSED_EG[sq >> 3] for sq in range(64))
_B_PACKED = tuple((PASSED_MG[7 - (sq >> 3)] << 16) + PASSED_EG[7 - (sq >> 3)] for sq in range(64))


def _fill_down(bb: int) -> int:
    """Every square strictly below (toward rank 1) a set bit, on the same file."""
    bb >>= 8
    bb |= bb >> 8
    bb |= bb >> 16
    bb |= bb >> 32
    return bb


def _fill_up(bb: int) -> int:
    """Every square strictly above (toward rank 8) a set bit, on the same file."""
    bb = (bb << 8) & _ALL
    bb |= (bb << 8) & _ALL
    bb |= (bb << 16) & _ALL
    bb |= (bb << 32) & _ALL
    return bb


def _passer_sets(board: chess.Board) -> tuple[int, int]:
    """(white passers, black passers), front pawn of each file only."""
    pawns = board.pawns
    white = pawns & board.occupied_co[chess.WHITE]
    black = pawns & board.occupied_co[chess.BLACK]
    # For White, a square is "stopped" if a black pawn stands ahead of it on
    # its file or a neighbouring file: fill black downward, widen sideways.
    down = _fill_down(black)
    stopped_white = down | ((down & _NOT_A) >> 1) | ((down & _NOT_H) << 1)
    white_passers = white & ~stopped_white & ~_fill_down(white)
    up = _fill_up(white)
    stopped_black = up | ((up & _NOT_A) >> 1) | ((up & _NOT_H) << 1)
    black_passers = black & ~stopped_black & ~_fill_up(black)
    return white_passers, black_passers


def _packed_for(white: int, black: int) -> int:
    down = _fill_down(black)
    stopped = down | ((down & _NOT_A) >> 1) | ((down & _NOT_H) << 1)
    packed = 0
    bb = white & ~stopped & ~_fill_down(white)
    while bb:
        packed += _W_PACKED[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    up = _fill_up(white)
    stopped = up | ((up & _NOT_A) >> 1) | ((up & _NOT_H) << 1)
    bb = black & ~stopped & ~_fill_up(black)
    while bb:
        packed -= _B_PACKED[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    return packed


# Pawn-structure cache. The term depends only on the two pawn bitboards, and
# within a search tree those change on a small fraction of nodes, so the
# fills above run once per structure and every other evaluation is one
# dictionary read. The value is a pure function of the key, so the cache
# cannot change any result, only its cost. Bounded by clearing when full.
_CACHE: dict[int, int] = {}
_CACHE_LIMIT = 1 << 15


def passed_pawns_packed(board: chess.Board) -> int:
    """White's-point-of-view bonus as a packed (mg << 16) + eg integer."""
    pawns = board.pawns
    white = pawns & board.occupied_co[chess.WHITE]
    key = (white << 64) | (pawns ^ white)
    packed = _CACHE.get(key)
    if packed is None:
        if len(_CACHE) >= _CACHE_LIMIT:
            _CACHE.clear()
        packed = _CACHE[key] = _packed_for(white, pawns ^ white)
    return packed


def passed_pawn_mask(board: chess.Board, white: bool) -> int:
    """Bitboard of the side's passed pawns, front pawn of each file only. For tests and tools."""
    white_passers, black_passers = _passer_sets(board)
    return white_passers if white else black_passers
