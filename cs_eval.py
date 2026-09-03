"""Static evaluation: tapered material + piece-square tables, plus bishop pair.

This is the largest hot path the engine actually owns -- move generation and
make/unmake belong to python-chess -- so it is written for speed rather than
elegance, and two decisions deserve explaining.

**Packed scores.** Middlegame and endgame values are stored in one integer per
square as ``(mg << 16) + eg`` and accumulated together, so each piece costs one
table lookup and one addition instead of two of each. The pair is separated
once at the end. This is sound as long as the endgame total stays inside a
signed 16-bit range, which a legal position cannot exceed: the largest possible
material total is far below 32767.

**Unrolled scans.** The twelve piece/colour bitboards are scanned in twelve
explicit blocks rather than a loop over a table of tables. At roughly 200 ns of
budget per piece, the per-iteration tuple unpacking a loop needs is a
measurable fraction of the whole function.

``evaluate_reference`` is the obvious, slow, transparently-correct version. It
is not used in the search; it exists so a test can assert the fast path agrees
with it on every position, which is what makes optimising this file safe.
"""

from __future__ import annotations

import chess

import cs_terms
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


def _pack(mg_tables: tuple[tuple[int, ...], ...], eg_tables: tuple[tuple[int, ...], ...],
          piece_type: int) -> tuple[int, ...]:
    mg = mg_tables[piece_type]
    eg = eg_tables[piece_type]
    return tuple((mg[square] << 16) + eg[square] for square in range(64))


# Indexed by square; already includes the material value for that piece type.
_W_PAWN = _pack(MG_WHITE, EG_WHITE, chess.PAWN)
_W_KNIGHT = _pack(MG_WHITE, EG_WHITE, chess.KNIGHT)
_W_BISHOP = _pack(MG_WHITE, EG_WHITE, chess.BISHOP)
_W_ROOK = _pack(MG_WHITE, EG_WHITE, chess.ROOK)
_W_QUEEN = _pack(MG_WHITE, EG_WHITE, chess.QUEEN)
_W_KING = _pack(MG_WHITE, EG_WHITE, chess.KING)

_B_PAWN = _pack(MG_BLACK, EG_BLACK, chess.PAWN)
_B_KNIGHT = _pack(MG_BLACK, EG_BLACK, chess.KNIGHT)
_B_BISHOP = _pack(MG_BLACK, EG_BLACK, chess.BISHOP)
_B_ROOK = _pack(MG_BLACK, EG_BLACK, chess.ROOK)
_B_QUEEN = _pack(MG_BLACK, EG_BLACK, chess.QUEEN)
_B_KING = _pack(MG_BLACK, EG_BLACK, chess.KING)

_BISHOP_PAIR = (BISHOP_PAIR_MG << 16) + BISHOP_PAIR_EG

# Optional positional terms, from the registry in cs_terms. The active set is
# decided once at import from the environment and the shipped DEFAULTS table;
# tests and tools change it with set_terms / set_term. With nothing active the
# two loops below never run and the evaluator is exactly the tapered tables.
ACTIVE_TERMS: frozenset[str] = frozenset()
_PACKED_TERMS: tuple = ()
_POST_TERMS: tuple = ()
_PACKED_REFERENCE: tuple = ()
_POST_REFERENCE: tuple = ()
# Read-only mirrors of the three original flags, kept for tools and tests
# that ask "is this on?"; assigning to them does nothing. Use set_term.
USE_KING_SAFETY = False
USE_MOP_UP = False
USE_PASSED = False


def set_terms(names) -> None:
    """Make exactly these registry terms active, in registry order."""
    global ACTIVE_TERMS, _PACKED_TERMS, _POST_TERMS, _PACKED_REFERENCE, _POST_REFERENCE
    global USE_KING_SAFETY, USE_MOP_UP, USE_PASSED
    wanted = frozenset(names)
    unknown = wanted - set(cs_terms.BY_NAME)
    if unknown:
        raise ValueError(f"unknown evaluation terms {sorted(unknown)}")
    active = [term for term in cs_terms.TERMS if term.name in wanted]
    ACTIVE_TERMS = wanted
    _PACKED_TERMS = tuple(t.fast for t in active if t.stage == "packed")
    _POST_TERMS = tuple(t.fast for t in active if t.stage == "post")
    _PACKED_REFERENCE = tuple(t.reference for t in active if t.stage == "packed")
    _POST_REFERENCE = tuple(t.reference for t in active if t.stage == "post")
    USE_KING_SAFETY = "king_safety" in wanted
    USE_MOP_UP = "mopup" in wanted
    USE_PASSED = "passed" in wanted


def set_term(name: str, on: bool) -> None:
    """Switch one registry term on or off, leaving the others as they are."""
    set_terms((ACTIVE_TERMS | {name}) if on else (ACTIVE_TERMS - {name}))


set_terms(cs_terms.enabled_from_environment())


def evaluate(board: chess.Board) -> int:
    """Score the position in centipawns from the side to move's point of view."""
    white = board.occupied_co[chess.WHITE]
    black = board.occupied_co[chess.BLACK]

    pawns = board.pawns
    knights = board.knights
    bishops = board.bishops
    rooks = board.rooks
    queens = board.queens
    kings = board.kings

    phase = (knights | bishops).bit_count() + 2 * rooks.bit_count() + 4 * queens.bit_count()
    if phase > TOTAL_PHASE:
        phase = TOTAL_PHASE  # promotions can push the count past a full board

    packed = 0

    bb = pawns & white
    while bb:
        packed += _W_PAWN[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = knights & white
    while bb:
        packed += _W_KNIGHT[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = bishops & white
    while bb:
        packed += _W_BISHOP[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = rooks & white
    while bb:
        packed += _W_ROOK[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = queens & white
    while bb:
        packed += _W_QUEEN[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = kings & white
    while bb:
        packed += _W_KING[(bb & -bb).bit_length() - 1]
        bb &= bb - 1

    bb = pawns & black
    while bb:
        packed -= _B_PAWN[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = knights & black
    while bb:
        packed -= _B_KNIGHT[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = bishops & black
    while bb:
        packed -= _B_BISHOP[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = rooks & black
    while bb:
        packed -= _B_ROOK[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = queens & black
    while bb:
        packed -= _B_QUEEN[(bb & -bb).bit_length() - 1]
        bb &= bb - 1
    bb = kings & black
    while bb:
        packed -= _B_KING[(bb & -bb).bit_length() - 1]
        bb &= bb - 1

    if (bishops & white).bit_count() > 1:
        packed += _BISHOP_PAIR
    if (bishops & black).bit_count() > 1:
        packed -= _BISHOP_PAIR

    if _PACKED_TERMS:
        # Packed like the tables, so each is tapered with them below.
        for term in _PACKED_TERMS:
            packed += term(board)

    # Split the pair back out. The endgame half is the low 16 bits, sign
    # extended; whatever is left is an exact multiple of 65536.
    eg = packed & 0xFFFF
    if eg >= 0x8000:
        eg -= 0x10000
    mg = (packed - eg) >> 16

    total = mg * phase + eg * (TOTAL_PHASE - phase)
    # Truncate toward zero rather than using floor division, so mirroring the
    # position negates the score exactly. Floor division rounds negatives away
    # from zero and would hand white a systematic one-centipawn edge.
    score = total // TOTAL_PHASE if total >= 0 else -(-total // TOTAL_PHASE)
    if _POST_TERMS:
        # Added after the taper, in whole centipawns: terms whose positions
        # are endgames by definition and whose gradient must not be diluted.
        for term in _POST_TERMS:
            score += term(board)
    if board.turn:  # chess.WHITE is True
        return score + TEMPO
    return -score + TEMPO


def evaluate_reference(board: chess.Board) -> int:
    """Transparently correct evaluation. Not used in search; used to test it."""
    white = board.occupied_co[chess.WHITE]
    black = board.occupied_co[chess.BLACK]

    boards = (board.pawns, board.knights, board.bishops, board.rooks, board.queens, board.kings)
    phase = (
        (board.knights | board.bishops).bit_count()
        + 2 * board.rooks.bit_count()
        + 4 * board.queens.bit_count()
    )
    if phase > TOTAL_PHASE:
        phase = TOTAL_PHASE

    mg = 0
    eg = 0
    for index in range(6):
        piece_type = index + 1
        bb = boards[index] & white
        while bb:
            square = (bb & -bb).bit_length() - 1
            bb &= bb - 1
            mg += MG_WHITE[piece_type][square]
            eg += EG_WHITE[piece_type][square]
        bb = boards[index] & black
        while bb:
            square = (bb & -bb).bit_length() - 1
            bb &= bb - 1
            mg -= MG_BLACK[piece_type][square]
            eg -= EG_BLACK[piece_type][square]

    if (board.bishops & white).bit_count() > 1:
        mg += BISHOP_PAIR_MG
        eg += BISHOP_PAIR_EG
    if (board.bishops & black).bit_count() > 1:
        mg -= BISHOP_PAIR_MG
        eg -= BISHOP_PAIR_EG

    for reference in _PACKED_REFERENCE:
        term_mg, term_eg = reference(board)
        mg += term_mg
        eg += term_eg

    total = mg * phase + eg * (TOTAL_PHASE - phase)
    score = total // TOTAL_PHASE if total >= 0 else -(-total // TOTAL_PHASE)
    for reference in _POST_REFERENCE:
        score += reference(board)
    if board.turn:
        return score + TEMPO
    return -score + TEMPO


def is_material_draw(board: chess.Board) -> bool:
    """Rule-accurate insufficient-material test, matching python-chess.

    This must agree with ``board.is_insufficient_material()`` exactly, because
    the search returns a hard 0 when it fires and the referee only claims a draw
    when the *rule* says so. An earlier version was a strategic heuristic
    wearing a rule's name: it declared K+N vs K+N, K+B vs K+N and
    opposite-coloured K+B vs K+B to be draws. None of those is a dead position
    under FIDE -- a helpmate exists in each -- so the search was forcing 0 in
    positions that are merely *drawish*, which is a different claim and not one
    the rules support.

    Kept as our own implementation rather than delegating because
    ``board.is_insufficient_material()`` measures 521 ns against 168 ns here,
    and this runs at every node. Equivalence is asserted over exhaustive
    material configurations in ``tests/test_eval.py``.
    """
    if board.pawns or board.rooks or board.queens:
        return False

    knights = board.knights
    bishops = board.bishops
    minors = knights | bishops
    count = minors.bit_count()

    if count <= 1:
        # Bare kings, or a single minor piece: no mate can be forced or helped.
        return True
    if knights:
        # Any knight alongside another minor admits a helpmate, so the position
        # is not dead even though it is almost always drawn in practice.
        return False
    # Bishops only: dead exactly when every bishop stands on one colour.
    return not (bishops & chess.BB_DARK_SQUARES) or not (bishops & chess.BB_LIGHT_SQUARES)
