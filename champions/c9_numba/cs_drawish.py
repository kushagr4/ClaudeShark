"""Low-material nominal-surplus scaling, V2.2a: three exact families, one correction.

The false-win audits found one mechanism behind the evaluator's confident
scores in drawn low-material endings: the material term pays the full
tapered value for a single-unit surplus that almost never converts. In
random oracle-labelled positions KRB v KR is drawn five times in six and
every win is tactical; KR v a lone minor is drawn four times in five; a lone
minor against one or two pawns never wins at all. The evaluator scored
those draws +150 to +310, and the decomposition showed the score to be the
material term to the centipawn, with tables, tempo and the king-pawn term
in single digits.

This term subtracts a fixed fraction of that surplus and nothing else. It
reads the position's piece counts and applies only when they match one of
three families exactly:

    A  no pawns, one rook each, exactly one minor on one side  -> keep 1/4 of the minor's value
    B  no pawns, one rook v exactly one lone minor             -> keep 1/2 of (rook - minor)
    C  one lone minor and no pawns v king + one or two pawns,
       no rooks, no queens                                    -> keep 1/4 of (minor - pawns)

Any queen, any extra piece, a pawn on the surplus side, a third pawn, a
second minor or rook, or pawns on both sides switches it off. The surplus
is the evaluator's own tapered material contribution of exactly those
pieces (the piece values folded into the tables, interpolated at the
position's phase), so the correction is consistent with the evaluator at
every phase; it is never applied when the nominal surplus is not
positive. Tables, tempo, the bishop pair and the king-pawn term are
untouched, and the whole evaluation is never scaled.

Tactical wins in these families are not protected here and do not need
to be: the search resolves them, and once material is taken the position
leaves the family. There is no mate-score logic in the evaluator because
the evaluator never sees mate scores.

Colour symmetry is exact: the surplus side is whichever colour holds the
family's surplus, never the side to move.
"""

from __future__ import annotations

import chess

from cs_constants import _EG_VALUE, _MG_VALUE, TOTAL_PHASE

# Numerator over 4 of the surplus that is REMOVED, per family: A and C keep
# one quarter (remove three quarters), B keeps one half (remove two quarters).
REMOVE_QUARTERS = {"A": 3, "B": 2, "C": 3}

_MG_PAWN, _EG_PAWN = _MG_VALUE[chess.PAWN], _EG_VALUE[chess.PAWN]


def _taper(mg: int, eg: int, phase: int) -> int:
    """The evaluator's interpolation, truncated toward zero."""
    total = mg * phase + eg * (TOTAL_PHASE - phase)
    return total // TOTAL_PHASE if total >= 0 else -(-total // TOTAL_PHASE)


def _correction(family: str, surplus_mg: int, surplus_eg: int, phase: int) -> int:
    """Centipawns to subtract from the surplus side, given the surplus's mg/eg material values."""
    surplus = _taper(surplus_mg, surplus_eg, phase)
    if surplus <= 0:
        return 0
    return surplus * REMOVE_QUARTERS[family] // 4


def low_material_reference(board: chess.Board) -> int:
    """White's-point-of-view correction, written out over piece counts. Not used in search."""
    if board.queens:
        return 0
    colours = (chess.WHITE, chess.BLACK)
    counts = {c: {pt: len(board.pieces(pt, c)) for pt in chess.PIECE_TYPES} for c in colours}
    phase = 0
    for c in colours:
        phase += counts[c][chess.KNIGHT] + counts[c][chess.BISHOP] + 2 * counts[c][chess.ROOK]
    phase = min(TOTAL_PHASE, phase)
    for strong in (chess.WHITE, chess.BLACK):
        a, b = counts[strong], counts[not strong]
        sign = 1 if strong == chess.WHITE else -1
        a_minors = a[chess.BISHOP] + a[chess.KNIGHT]
        b_minors = b[chess.BISHOP] + b[chess.KNIGHT]
        if a_minors == 1 and a[chess.PAWN] == 0 and b_minors == 0:
            minor = chess.BISHOP if a[chess.BISHOP] else chess.KNIGHT
            if b[chess.PAWN] == 0 and a[chess.ROOK] == 1 and b[chess.ROOK] == 1:
                # Family A: rook and minor against rook; the minor's owner has the surplus.
                return -sign * _correction("A", _MG_VALUE[minor], _EG_VALUE[minor], phase)
            if a[chess.ROOK] == 0 and b[chess.ROOK] == 0 and b[chess.PAWN] in (1, 2):
                # Family C: lone minor against one or two pawns.
                n = b[chess.PAWN]
                return -sign * _correction("C", _MG_VALUE[minor] - n * _MG_PAWN,
                                           _EG_VALUE[minor] - n * _EG_PAWN, phase)
        if (a[chess.ROOK] == 1 and a_minors == 0 and a[chess.PAWN] == 0
                and b[chess.ROOK] == 0 and b_minors == 1 and b[chess.PAWN] == 0):
            # Family B: rook against a lone minor; the rook's owner has the surplus.
            minor = chess.BISHOP if b[chess.BISHOP] else chess.KNIGHT
            return -sign * _correction("B", _MG_VALUE[chess.ROOK] - _MG_VALUE[minor],
                                       _EG_VALUE[chess.ROOK] - _EG_VALUE[minor], phase)
    return 0


def low_material(board: chess.Board) -> int:
    """White's-point-of-view correction; the fast version on bitboard popcounts."""
    if board.queens:
        return 0
    pawns = board.pawns
    rooks = board.rooks
    bishops = board.bishops
    knights = board.knights
    white = board.occupied_co[chess.WHITE]
    minors = bishops | knights
    n_rooks = rooks.bit_count()
    n_minors = minors.bit_count()
    if n_minors != 1 or n_rooks > 2:
        return 0
    minor_is_white = bool(minors & white)
    minor_type = chess.BISHOP if bishops else chess.KNIGHT
    phase = n_minors + 2 * n_rooks  # no queens here; never exceeds TOTAL_PHASE
    if not pawns:
        if n_rooks == 2 and (rooks & white).bit_count() == 1:
            # Family A: the minor's owner has the surplus.
            c = _correction("A", _MG_VALUE[minor_type], _EG_VALUE[minor_type], phase)
            return -c if minor_is_white else c
        if n_rooks == 1 and bool(rooks & white) != minor_is_white:
            # Family B: the rook's owner has the surplus.
            c = _correction("B", _MG_VALUE[chess.ROOK] - _MG_VALUE[minor_type],
                            _EG_VALUE[chess.ROOK] - _EG_VALUE[minor_type], phase)
            return c if minor_is_white else -c  # rook is the other colour
        return 0
    if n_rooks:
        return 0
    # Family C: the minor side has no pawns, the other side one or two.
    minor_side = white if minor_is_white else ~white
    if pawns & minor_side:
        return 0
    n = pawns.bit_count()
    if n > 2:
        return 0
    c = _correction("C", _MG_VALUE[minor_type] - n * _MG_PAWN,
                    _EG_VALUE[minor_type] - n * _EG_PAWN, phase)
    return -c if minor_is_white else c
