"""King safety, v1.

A deliberately small term with four concepts, added because king structures
carry the worst error rates in the calibrated corpus: `unusual_king_placement`
errs at 2.67x the baseline rate and `exposed_king` at 2.04x, the two highest of
any structural tag.

* **Open and semi-open files at the king.** A file with no friendly pawn is a
  road to the king. It only matters if the enemy has a rook or queen to drive
  down it, so the penalty is gated on that.
* **Pieces attacking the king ring** -- the eight squares around the king plus
  the king square. Sliding attacks are computed through the real occupancy, so
  a blocked bishop does not count.
* **Enemy pawns bearing on the ring.** Pawns are attackers too, and leaving
  them out is not a simplification but a hole: on corpus position cl-170 a
  piece-only count scored both kings at 16 and cancelled to exactly zero, while
  the real danger was black's pawns on g3 and h4 beside the white king.
* **Pawn shelter**, a modest offset for friendly pawns in front of the king.

Everything is middlegame-weighted and tapers to zero in the endgame, where an
active king is an asset rather than a liability. Getting that backwards would
teach the engine to hide its king in exactly the positions where it should be
marching, so the endgame component of every term here is zero by construction.

**On cost.** This runs inside `evaluate`, which the search calls at every
quiescence leaf, so it is written around precomputed masks. The obvious version
-- iterate every enemy slider and look up its attack set -- measured 9.70 us per
evaluation against a 3.71 us baseline, a 62% throughput loss, because each
slider costs a dictionary lookup keyed on a large integer. The version below
pre-filters with a zone mask so those lookups happen only for the handful of
pieces that could possibly reach the ring, and knights need no loop at all.
``king_safety_mg_reference`` is the slow, obvious version, kept so a test can
assert the two agree on every position.

**Status: measured, and OFF by default.** The deterministic gate did not pass.
Over the 240-position calibrated suite at fixed depth 6, judged by Stockfish 18
at 1M nodes per child:

===========================  ============  ============
metric                       off           on
===========================  ============  ============
best-move agreement          37%           37%
within 25 cp                 66%           65%
robust mean loss             35.3          35.5
serious errors (>=100 cp)    10.0%         10.4%
catastrophic (>=300 cp)      1.7%          1.7%
===========================  ============  ============

49 positions changed move: 19 improved by more than 10 cp, 20 got worse, 10 were
a wash. That is a coin flip.

The structural split is the interesting part, and the reason this file survives
rather than being deleted:

===========================  ====  ===================  ==================
subset                          n  robust loss off/on   serious off/on
===========================  ====  ===================  ==================
exposed_king                   54  57.9 -> 48.1         20.4% -> 14.8%
king-tagged (any)             108  46.5 -> 43.4         13.9% -> 13.0%
NOT king-tagged               132  26.1 -> 29.1          6.8% ->  8.3%
===========================  ====  ===================  ==================

The term helps the subset it was built for and hurts everything else by about
the same amount. That is what a uniformly-applied penalty does: every
middlegame position has two kings, so it perturbs positions where king safety
was never the issue.

It also fixed **none** of the seven persistent evaluation errors that motivated
it -- all seven play the identical move. cl-170 is the clearest case: the term
now scores it -18 in the right direction, but the error is 484 cp, so an 18 cp
nudge cannot move it. The weights are too small to change a decision, and
raising them would deepen the damage to the other 132 positions.

What a v2 would need, on this evidence: to fire *selectively* rather than on
every position, and to be large enough to matter when it does. That is a
different design, not a retuning of these constants.
"""

from __future__ import annotations

import chess

# --------------------------------------------------------------------- masks

_FILES = tuple(chess.BB_FILES)

_KING_RING: list[int] = []
# The up-to-three file bitboards at the king, as a tuple so the hot loop needs
# no arithmetic to find them.
_KING_FILE_LIST: list[tuple[int, ...]] = []
# Union of all three, for the pawn lookups.
_KING_FILES: list[int] = []
# Squares in front of the king, two ranks deep, on its own and adjacent files.
_SHELTER: list[list[int]] = [[0] * 64, [0] * 64]

for _square in range(64):
    _file = chess.square_file(_square)
    _rank = chess.square_rank(_square)

    _list = tuple(_FILES[f] for f in range(max(0, _file - 1), min(8, _file + 2)))
    _KING_FILE_LIST.append(_list)
    _union = 0
    for _one in _list:
        _union |= _one
    _KING_FILES.append(_union)

    _KING_RING.append(chess.BB_KING_ATTACKS[_square] | chess.BB_SQUARES[_square])

    for _colour in (chess.BLACK, chess.WHITE):
        _mask = 0
        _step = 1 if _colour == chess.WHITE else -1
        for _ahead in (1, 2):
            _r = _rank + _step * _ahead
            if 0 <= _r <= 7:
                _mask |= _union & chess.BB_RANKS[_r]
        _SHELTER[_colour][_square] = _mask

# Zones: every square from which a piece of the given kind could reach the ring
# on an empty board. Used as a pre-filter -- a piece outside the zone cannot be
# an attacker whatever the occupancy, and one inside still gets the exact test.
_RING_KNIGHT: list[int] = []   # exact for knights: nothing blocks them
_RING_DIAG: list[int] = []
_RING_LINE: list[int] = []
# Squares from which an ENEMY pawn attacks the ring, by defending colour.
_RING_PAWN: list[list[int]] = [[0] * 64, [0] * 64]

for _square in range(64):
    _ring = _KING_RING[_square]
    _knight = _diag = _line = 0
    for _r in chess.scan_forward(_ring):
        _knight |= chess.BB_KNIGHT_ATTACKS[_r]
        _diag |= chess.BB_DIAG_ATTACKS[_r][0]
        _line |= chess.BB_RANK_ATTACKS[_r][0] | chess.BB_FILE_ATTACKS[_r][0]
    _RING_KNIGHT.append(_knight)
    _RING_DIAG.append(_diag)
    _RING_LINE.append(_line)

    for _colour in (chess.BLACK, chess.WHITE):
        _mask = 0
        for _from in range(64):
            if chess.BB_PAWN_ATTACKS[not _colour][_from] & _ring:
                _mask |= chess.BB_SQUARES[_from]
        _RING_PAWN[_colour][_square] = _mask

_KING_RING_T = tuple(_KING_RING)
_KING_FILE_LIST_T = tuple(_KING_FILE_LIST)
_KING_FILES_T = tuple(_KING_FILES)
_SHELTER_W = tuple(_SHELTER[chess.WHITE])
_SHELTER_B = tuple(_SHELTER[chess.BLACK])
_RING_KNIGHT_T = tuple(_RING_KNIGHT)
_RING_DIAG_T = tuple(_RING_DIAG)
_RING_LINE_T = tuple(_RING_LINE)
_RING_PAWN_W = tuple(_RING_PAWN[chess.WHITE])
_RING_PAWN_B = tuple(_RING_PAWN[chess.BLACK])

_DIAG_ATTACKS = chess.BB_DIAG_ATTACKS
_DIAG_MASKS = chess.BB_DIAG_MASKS
_RANK_ATTACKS = chess.BB_RANK_ATTACKS
_RANK_MASKS = chess.BB_RANK_MASKS
_FILE_ATTACKS = chess.BB_FILE_ATTACKS
_FILE_MASKS = chess.BB_FILE_MASKS

# ------------------------------------------------------------------- weights
#
# Seeds, not settled values. The residual regression over the 6203-position
# labelled pool put king-zone attackers at -11.6 cp (t = -3.0) and king open
# files at -9.3 cp (t = -1.6, which that table's own threshold calls not well
# determined). These sit at or below those magnitudes rather than above: the
# regression is the only quantitative evidence available and it is weak, so
# overshooting it would be inventing a number.
#
# Middlegame only. Every endgame weight is zero.
OPEN_FILE_MG = 12
SEMI_OPEN_FILE_MG = 6
RING_ATTACKER_MG = 8
RING_ATTACK_CAP = 6
PAWN_STORM_MG = 6
PAWN_STORM_CAP = 3
SHELTER_PAWN_MG = 4
SHELTER_MAX = 3


def _side_penalty(
    board: chess.Board, colour: chess.Color, us: int, them: int, occupied: int
) -> int:
    king_bb = board.kings & us
    if not king_bb:
        return 0
    square = (king_bb & -king_bb).bit_length() - 1

    pawns = board.pawns
    rooks_queens = board.rooks | board.queens
    penalty = 0

    # --- files at the king, gated on the enemy having something to use them
    if rooks_queens & them:
        files = _KING_FILES_T[square]
        ours = pawns & us & files
        theirs = pawns & them & files
        for one in _KING_FILE_LIST_T[square]:
            if not (ours & one):
                penalty += OPEN_FILE_MG if not (theirs & one) else SEMI_OPEN_FILE_MG

    ring = _KING_RING_T[square]

    # --- knights: the zone mask is exact, so no per-piece test is needed
    found = board.knights & them & _RING_KNIGHT_T[square]

    # --- sliders: pre-filter by zone, then test the survivors exactly.
    #
    # Attackers accumulate as a bitboard rather than a counter, because a queen
    # can reach the ring both diagonally and orthogonally and must still count
    # once. Counting per loop double-counted her and disagreed with the
    # reference on 92 of 1200 random positions.
    bb = (board.bishops | board.queens) & them & _RING_DIAG_T[square]
    while bb:
        low = bb & -bb
        attacker = low.bit_length() - 1
        bb &= bb - 1
        if _DIAG_ATTACKS[attacker][_DIAG_MASKS[attacker] & occupied] & ring:
            found |= low

    bb = rooks_queens & them & _RING_LINE_T[square]
    while bb:
        low = bb & -bb
        attacker = low.bit_length() - 1
        bb &= bb - 1
        if (
            _RANK_ATTACKS[attacker][_RANK_MASKS[attacker] & occupied] & ring
            or _FILE_ATTACKS[attacker][_FILE_MASKS[attacker] & occupied] & ring
        ):
            found |= low

    attackers = found.bit_count()
    if attackers:
        penalty += RING_ATTACKER_MG * (
            attackers if attackers < RING_ATTACK_CAP else RING_ATTACK_CAP
        )

    # --- enemy pawns bearing on the ring
    storm_mask = _RING_PAWN_W[square] if colour == chess.WHITE else _RING_PAWN_B[square]
    storm = (pawns & them & storm_mask).bit_count()
    if storm:
        penalty += PAWN_STORM_MG * (storm if storm < PAWN_STORM_CAP else PAWN_STORM_CAP)

    # --- shelter, a modest offset against the above
    shelter_mask = _SHELTER_W[square] if colour == chess.WHITE else _SHELTER_B[square]
    shelter = (pawns & us & shelter_mask).bit_count()
    if shelter:
        penalty -= SHELTER_PAWN_MG * (shelter if shelter < SHELTER_MAX else SHELTER_MAX)

    return penalty


def king_safety_mg(board: chess.Board) -> int:
    """Middlegame king-safety score in centipawns, white minus black.

    Endgame contribution is zero by design, so the caller applies this to the
    middlegame half of the taper only.
    """
    occupied = board.occupied
    white = board.occupied_co[chess.WHITE]
    black = board.occupied_co[chess.BLACK]
    return _side_penalty(board, chess.BLACK, black, white, occupied) - _side_penalty(
        board, chess.WHITE, white, black, occupied
    )


def king_safety_mg_reference(board: chess.Board) -> int:
    """The obvious implementation: no zone pre-filter, every piece tested.

    Not used in search. It exists so a test can assert the fast path agrees
    with it, which is what makes the mask work above safe to rely on.
    """
    occupied = board.occupied
    total = 0
    for colour in (chess.WHITE, chess.BLACK):
        us = board.occupied_co[colour]
        them = board.occupied_co[not colour]
        king_bb = board.kings & us
        if not king_bb:
            continue
        square = (king_bb & -king_bb).bit_length() - 1
        file_index = chess.square_file(square)
        penalty = 0

        if (board.rooks | board.queens) & them:
            for f in range(max(0, file_index - 1), min(8, file_index + 2)):
                one = _FILES[f]
                if not (board.pawns & us & one):
                    penalty += (
                        OPEN_FILE_MG if not (board.pawns & them & one) else SEMI_OPEN_FILE_MG
                    )

        ring = chess.BB_KING_ATTACKS[square] | chess.BB_SQUARES[square]
        attackers = 0
        for attacker in chess.scan_forward(them & ~board.pawns & ~board.kings):
            piece = board.piece_type_at(attacker)
            if piece == chess.KNIGHT:
                if chess.BB_KNIGHT_ATTACKS[attacker] & ring:
                    attackers += 1
            else:
                reach = 0
                if piece in (chess.BISHOP, chess.QUEEN):
                    reach |= _DIAG_ATTACKS[attacker][_DIAG_MASKS[attacker] & occupied]
                if piece in (chess.ROOK, chess.QUEEN):
                    reach |= _RANK_ATTACKS[attacker][_RANK_MASKS[attacker] & occupied]
                    reach |= _FILE_ATTACKS[attacker][_FILE_MASKS[attacker] & occupied]
                if reach & ring:
                    attackers += 1
        if attackers:
            penalty += RING_ATTACKER_MG * min(attackers, RING_ATTACK_CAP)

        storm = sum(
            1
            for attacker in chess.scan_forward(board.pawns & them)
            if chess.BB_PAWN_ATTACKS[not colour][attacker] & ring
        )
        if storm:
            penalty += PAWN_STORM_MG * min(storm, PAWN_STORM_CAP)

        shelter_mask = _SHELTER_W[square] if colour == chess.WHITE else _SHELTER_B[square]
        shelter = (board.pawns & us & shelter_mask).bit_count()
        if shelter:
            penalty -= SHELTER_PAWN_MG * min(shelter, SHELTER_MAX)

        total += -penalty if colour == chess.WHITE else penalty
    return total
