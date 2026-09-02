"""Structural labels for a position, computed from the board alone.

These tags describe chess properties -- pawn structure, king placement, piece
configuration, material composition -- rather than opening names. They drive
the diversity selection when a corpus is built and the breakdowns when the
engine's move quality is analysed, so that a weakness can be tied to a
structure ("undervalues passed pawns") rather than to an opening.

Every tag is a deliberately simple, documented heuristic. They are labels for
grouping, not an evaluator: a tag being slightly generous or strict changes
which bucket a position lands in, not whether anything is measured correctly.
Definitions are next to the code that computes them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import chess

PAWN_UNITS = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}

# Game phase on the engine's own 0..24 scale, so structural buckets line up with
# the taper the evaluator actually uses.
_PHASE_INC = {chess.KNIGHT: 1, chess.BISHOP: 1, chess.ROOK: 2, chess.QUEEN: 4}


@dataclass
class Structure:
    phase: str  # opening | middlegame | endgame
    phase24: int  # 0 = bare pawns, 24 = full board
    material_white: int
    material_black: int
    material_diff: int  # white minus black, in pawn units
    # even | pawns | bishop_vs_knight | exchange | minor_vs_pawns | piece |
    # queen_vs_pieces | other
    imbalance: str
    tags: list[str] = field(default_factory=list)

    def as_json(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "phase24": self.phase24,
            "material_white": self.material_white,
            "material_black": self.material_black,
            "material_diff": self.material_diff,
            "imbalance": self.imbalance,
            "tags": list(self.tags),
        }


def _pawn_files(pawns: int) -> list[int]:
    return [chess.square_file(square) for square in chess.scan_forward(pawns)]


def _file_mask(file_index: int) -> int:
    return chess.BB_FILES[file_index] if 0 <= file_index < 8 else 0


def _ahead_mask(square: int, colour: bool) -> int:
    """Squares on the same file strictly in front of ``square`` for ``colour``."""
    rank = chess.square_rank(square)
    file_mask = chess.BB_FILES[chess.square_file(square)]
    if colour == chess.WHITE:
        return file_mask & ~((1 << (8 * (rank + 1))) - 1)
    return file_mask & ((1 << (8 * rank)) - 1)


def _passed(board: chess.Board, square: int, colour: bool) -> bool:
    file_index = chess.square_file(square)
    span = _ahead_mask(square, colour)
    for adjacent in (file_index - 1, file_index + 1):
        if 0 <= adjacent < 8:
            span |= _ahead_mask(chess.square(adjacent, chess.square_rank(square)), colour)
    return not (span & board.pawns & board.occupied_co[not colour])


def _pawn_features(board: chess.Board, colour: bool) -> dict[str, int]:
    own = board.pawns & board.occupied_co[colour]
    them = board.pawns & board.occupied_co[not colour]
    files = _pawn_files(own)
    counts = [files.count(f) for f in range(8)]

    isolated = doubled = passed = protected = backward = 0
    passed_squares: list[int] = []
    for square in chess.scan_forward(own):
        f = chess.square_file(square)
        neighbours = (counts[f - 1] if f > 0 else 0) + (counts[f + 1] if f < 7 else 0)
        if neighbours == 0:
            isolated += 1
        if counts[f] > 1:
            doubled += 1
        if _passed(board, square, colour):
            passed += 1
            passed_squares.append(square)
            if board.attackers(colour, square) & own:
                protected += 1
        # Backward: no friendly pawn beside or behind it on adjacent files, and
        # the square in front is controlled by an enemy pawn, so it cannot
        # safely advance.
        if neighbours:
            behind_or_level = 0
            for adjacent in (f - 1, f + 1):
                if 0 <= adjacent < 8:
                    mask = _file_mask(adjacent) & own
                    for other in chess.scan_forward(mask):
                        rank_diff = chess.square_rank(other) - chess.square_rank(square)
                        if (rank_diff <= 0) if colour == chess.WHITE else (rank_diff >= 0):
                            behind_or_level += 1
            if not behind_or_level:
                step = 8 if colour == chess.WHITE else -8
                front = square + step
                if 0 <= front < 64 and board.attackers(not colour, front) & them:
                    backward += 1

    connected_passers = 0
    for square in passed_squares:
        f = chess.square_file(square)
        for other in passed_squares:
            if other != square and abs(chess.square_file(other) - f) == 1:
                connected_passers += 1
                break

    advanced = sum(
        1 for square in passed_squares
        if (chess.square_rank(square) >= 5 if colour == chess.WHITE
            else chess.square_rank(square) <= 2)
    )
    return {
        "isolated": isolated,
        "doubled": doubled,
        "passed": passed,
        "protected_passed": protected,
        "connected_passed": connected_passers,
        "advanced_passed": advanced,
        "backward": backward,
    }


def _material(board: chess.Board, colour: bool) -> int:
    total = 0
    for piece_type, units in PAWN_UNITS.items():
        total += units * chess.popcount(board.pieces_mask(piece_type, colour))
    return total


def _non_pawn(board: chess.Board, colour: bool) -> int:
    return _material(board, colour) - chess.popcount(board.pieces_mask(chess.PAWN, colour))


def _imbalance(board: chess.Board) -> str:
    """Name the material composition difference, ignoring who is ahead."""
    diff = {
        piece_type: chess.popcount(board.pieces_mask(piece_type, chess.WHITE))
        - chess.popcount(board.pieces_mask(piece_type, chess.BLACK))
        for piece_type in PAWN_UNITS
    }
    pieces = {k: v for k, v in diff.items() if k != chess.PAWN and v}
    pawns = diff[chess.PAWN]
    if not pieces:
        return "even" if pawns == 0 else "pawns"
    if set(pieces) == {chess.BISHOP, chess.KNIGHT} and (
            pieces[chess.BISHOP] == -pieces[chess.KNIGHT]):
        return "bishop_vs_knight"
    if chess.ROOK in pieces and abs(pieces[chess.ROOK]) == 1 and (
        (chess.BISHOP in pieces or chess.KNIGHT in pieces)
        and sum(v for k, v in pieces.items() if k in (chess.BISHOP, chess.KNIGHT))
        == -pieces[chess.ROOK]
    ):
        return "exchange"
    if len(pieces) == 1:
        piece_type, count = next(iter(pieces.items()))
        if abs(count) == 1 and piece_type in (chess.BISHOP, chess.KNIGHT) and pawns * count < 0:
            return "minor_vs_pawns"
        return "piece"
    if chess.QUEEN in pieces:
        return "queen_vs_pieces"
    return "other"


def _king_zone_shelter(board: chess.Board, colour: bool) -> int:
    king = board.king(colour)
    if king is None:
        return 0
    own_pawns = board.pawns & board.occupied_co[colour]
    kf = chess.square_file(king)
    kr = chess.square_rank(king)
    shelter = 0
    for df in (-1, 0, 1):
        f = kf + df
        if not 0 <= f < 8:
            continue
        for dr in (1, 2):
            r = kr + dr if colour == chess.WHITE else kr - dr
            if 0 <= r < 8 and own_pawns & chess.BB_SQUARES[chess.square(f, r)]:
                shelter += 1
                break
    return shelter


def _attackers_near_king(board: chess.Board, defender: bool) -> int:
    king = board.king(defender)
    if king is None:
        return 0
    zone = chess.BB_KING_ATTACKS[king] | chess.BB_SQUARES[king]
    attacker = not defender
    count = 0
    for piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
        for square in chess.scan_forward(board.pieces_mask(piece_type, attacker)):
            if board.attacks(square) & zone:
                count += 1
    return count


def _outposts(board: chess.Board, colour: bool) -> int:
    own_pawns = board.pawns & board.occupied_co[colour]
    them_pawns = board.pawns & board.occupied_co[not colour]
    count = 0
    for square in chess.scan_forward(board.pieces_mask(chess.KNIGHT, colour)):
        rank = chess.square_rank(square)
        in_enemy_half = rank >= 3 if colour == chess.WHITE else rank <= 4
        if not in_enemy_half:
            continue
        if not board.attackers(colour, square) & own_pawns:
            continue
        # No enemy pawn can ever attack the square: none on an adjacent file
        # that is still behind (from the enemy's perspective) the square.
        f = chess.square_file(square)
        threat = 0
        for adjacent in (f - 1, f + 1):
            if 0 <= adjacent < 8:
                threat |= _ahead_mask(chess.square(adjacent, rank), colour)
        if not threat & them_pawns:
            count += 1
    return count


def _hanging_piece(board: chess.Board) -> bool:
    """A non-pawn piece of either side attacked and not defended."""
    for colour in (chess.WHITE, chess.BLACK):
        for piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
            for square in chess.scan_forward(board.pieces_mask(piece_type, colour)):
                if board.attackers(not colour, square) and not board.attackers(colour, square):
                    return True
    return False


def _bishop_colour_mask(board: chess.Board, colour: bool) -> tuple[bool, bool]:
    bishops = board.pieces_mask(chess.BISHOP, colour)
    return bool(bishops & chess.BB_LIGHT_SQUARES), bool(bishops & chess.BB_DARK_SQUARES)


def analyse_structure(board: chess.Board) -> Structure:
    tags: list[str] = []
    white_pawns = board.pawns & board.occupied_co[chess.WHITE]
    black_pawns = board.pawns & board.occupied_co[chess.BLACK]

    phase24 = 0
    for piece_type, inc in _PHASE_INC.items():
        phase24 += inc * chess.popcount(board.pieces_mask(piece_type, chess.WHITE))
        phase24 += inc * chess.popcount(board.pieces_mask(piece_type, chess.BLACK))
    phase24 = min(24, phase24)

    mat_w = _material(board, chess.WHITE)
    mat_b = _material(board, chess.BLACK)
    non_pawn_total = _non_pawn(board, chess.WHITE) + _non_pawn(board, chess.BLACK)

    # Phase. Endgame once the non-pawn material on the board is at most two
    # rooks and two minors in total (26 units), which is where king activity
    # starts to matter more than shelter. Opening while the queens and most
    # minors are still on and the game is young.
    if non_pawn_total <= 26:
        phase = "endgame"
    elif board.fullmove_number <= 10 and phase24 >= 20:
        phase = "opening"
    else:
        phase = "middlegame"

    # ---------------------------------------------------------------- pawns
    pw = _pawn_features(board, chess.WHITE)
    pb = _pawn_features(board, chess.BLACK)
    if pw["isolated"] or pb["isolated"]:
        tags.append("isolated_pawn")
    if pw["doubled"] or pb["doubled"]:
        tags.append("doubled_pawns")
    if pw["passed"] or pb["passed"]:
        tags.append("passed_pawn")
    if pw["protected_passed"] or pb["protected_passed"]:
        tags.append("protected_passer")
    if pw["connected_passed"] or pb["connected_passed"]:
        tags.append("connected_passers")
    if pw["advanced_passed"] or pb["advanced_passed"]:
        tags.append("advanced_passer")
    if pw["backward"] or pb["backward"]:
        tags.append("backward_pawn")

    wf = _pawn_files(white_pawns)
    bf = _pawn_files(black_pawns)

    # Isolated queen's pawn: a lone d-pawn with no c- or e-pawn beside it, on
    # d4 for White or d5 for Black, facing no enemy d-pawn.
    for colour, files, pawns in ((chess.WHITE, wf, white_pawns), (chess.BLACK, bf, black_pawns)):
        d_square = chess.D4 if colour == chess.WHITE else chess.D5
        enemy_files = bf if colour == chess.WHITE else wf
        if (pawns & chess.BB_SQUARES[d_square]) and 2 not in files and 4 not in files \
                and 3 not in enemy_files:
            tags.append("isolated_queen_pawn")
            break

    # Hanging pawns: c- and d-pawns side by side on the fourth rank (fifth for
    # Black), no own b- or e-pawn, facing no enemy c- or d-pawn.
    for colour, files, pawns in ((chess.WHITE, wf, white_pawns), (chess.BLACK, bf, black_pawns)):
        c_square, d_square = (chess.C4, chess.D4) if colour == chess.WHITE else (chess.C5, chess.D5)
        enemy_files = bf if colour == chess.WHITE else wf
        if (pawns & chess.BB_SQUARES[c_square]) and (pawns & chess.BB_SQUARES[d_square]) \
                and 1 not in files and 4 not in files \
                and 2 not in enemy_files and 3 not in enemy_files:
            tags.append("hanging_pawns")
            break

    # Carlsbad: the Exchange QGD skeleton. One side has d4 and e3 but no
    # c-pawn; the other has d5 and c6 but no e-pawn (colours either way).
    if (white_pawns & chess.BB_D4 and 2 not in wf and 4 in wf
            and black_pawns & chess.BB_D5 and 5 in bf and 4 not in bf) or (
            black_pawns & chess.BB_D5 and 2 not in bf and 4 in bf
            and white_pawns & chess.BB_D4 and 5 in wf and 4 not in wf):
        tags.append("carlsbad")
    # Minority attack: the Carlsbad skeleton with the two-against-three side
    # having pushed its b-pawn.
    if "carlsbad" in tags and ((white_pawns & (chess.BB_B4 | chess.BB_B5))
                               or (black_pawns & (chess.BB_B5 | chess.BB_B4))):
        tags.append("minority_attack")

    # Maróczy bind: pawns on c4 and e4 against a side with no c-pawn (the
    # Sicilian c-pawn already exchanged) and no pawn on d5.
    if (white_pawns & chess.BB_C4 and white_pawns & chess.BB_E4
            and 2 not in bf and not (black_pawns & chess.BB_D5)):
        tags.append("maroczy_bind")
    if (black_pawns & chess.BB_C5 and black_pawns & chess.BB_E5
            and 2 not in wf and not (white_pawns & chess.BB_D4)):
        tags.append("maroczy_bind")

    # Files.
    open_files = sum(1 for f in range(8) if f not in wf and f not in bf)
    semi_open = sum(1 for f in range(8) if (f in wf) != (f in bf))
    if open_files:
        tags.append("open_file")
    if semi_open:
        tags.append("semi_open_file")
    for colour, files, enemy_files in ((chess.WHITE, wf, bf), (chess.BLACK, bf, wf)):
        for square in chess.scan_forward(board.pieces_mask(chess.ROOK, colour)):
            f = chess.square_file(square)
            if f not in files and f not in enemy_files:
                tags.append("rook_on_open_file")
                break
            if f not in files:
                tags.append("rook_on_semi_open_file")
                break

    # Centre.
    centre = chess.BB_D4 | chess.BB_D5 | chess.BB_E4 | chess.BB_E5
    centre_pawns = chess.popcount(board.pawns & centre)
    blocked = 0
    for square in chess.scan_forward(white_pawns):
        if square + 8 < 64 and black_pawns & chess.BB_SQUARES[square + 8]:
            blocked += 1
    d_blocked = any(
        white_pawns & chess.BB_SQUARES[chess.square(3, r)]
        and black_pawns & chess.BB_SQUARES[chess.square(3, r + 1)]
        for r in range(1, 7)
    )
    e_blocked = any(
        white_pawns & chess.BB_SQUARES[chess.square(4, r)]
        and black_pawns & chess.BB_SQUARES[chess.square(4, r + 1)]
        for r in range(1, 7)
    )
    if (phase != "endgame" and centre_pawns <= 1 and (3 not in wf or 3 not in bf)
            and (4 not in wf or 4 not in bf)):
        tags.append("open_centre")
    elif d_blocked and e_blocked:
        tags.append("closed_centre")
    if blocked >= 3:
        tags.append("locked_pawn_chain")

    # Space: pawns established on the fifth rank and beyond.
    space_w = chess.popcount(white_pawns & (chess.BB_RANK_5 | chess.BB_RANK_6))
    space_b = chess.popcount(black_pawns & (chess.BB_RANK_4 | chess.BB_RANK_3))
    if abs(space_w - space_b) >= 2:
        tags.append("space_advantage")

    # Majorities: asymmetric pawn distribution across the wings.
    q_w = sum(1 for f in wf if f <= 2)
    q_b = sum(1 for f in bf if f <= 2)
    k_w = sum(1 for f in wf if f >= 5)
    k_b = sum(1 for f in bf if f >= 5)
    if (q_w > q_b and k_w < k_b) or (q_b > q_w and k_b < k_w):
        tags.append("queenside_majority")

    # ---------------------------------------------------------------- kings
    wk = board.king(chess.WHITE)
    bk = board.king(chess.BLACK)
    if wk is not None and bk is not None:
        wkf, bkf = chess.square_file(wk), chess.square_file(bk)
        queens_on = bool(board.queens)
        if phase != "endgame":
            if (wkf >= 5 and bkf >= 5) or (wkf <= 2 and bkf <= 2):
                tags.append("same_side_castling")
            elif (wkf >= 5 and bkf <= 2) or (wkf <= 2 and bkf >= 5):
                tags.append("opposite_side_castling")
            uncastled = (wkf in (3, 4) and chess.square_rank(wk) == 0) or (
                bkf in (3, 4) and chess.square_rank(bk) == 7)
            if uncastled and queens_on and board.fullmove_number >= 8:
                tags.append("king_in_centre")
            if chess.square_rank(wk) >= 2 or chess.square_rank(bk) <= 5:
                tags.append("unusual_king_placement")
            # A king still on its starting file with its centre pawns advanced
            # is uncastled, not exposed; count shelter for wing kings, or for
            # any king once the opening is over.
            for colour, kfile in ((chess.WHITE, wkf), (chess.BLACK, bkf)):
                on_wing = kfile <= 2 or kfile >= 5
                if (queens_on and (on_wing or board.fullmove_number >= 15)
                        and _king_zone_shelter(board, colour) <= 1):
                    tags.append("exposed_king")
                    break
            if _attackers_near_king(board, chess.WHITE) >= 3 or \
                    _attackers_near_king(board, chess.BLACK) >= 3:
                tags.append("king_attack")

    # --------------------------------------------------------------- pieces
    wb_light, wb_dark = _bishop_colour_mask(board, chess.WHITE)
    bb_light, bb_dark = _bishop_colour_mask(board, chess.BLACK)
    w_bishops = chess.popcount(board.pieces_mask(chess.BISHOP, chess.WHITE))
    b_bishops = chess.popcount(board.pieces_mask(chess.BISHOP, chess.BLACK))
    if (w_bishops >= 2) != (b_bishops >= 2):
        tags.append("bishop_pair")
    if w_bishops == 1 and b_bishops == 1 and (wb_light != bb_light):
        tags.append("opposite_coloured_bishops")
    # Bad bishop: a lone bishop with most of its own pawns fixed on its colour.
    for light, dark, pawns in (
        (wb_light, wb_dark, white_pawns), (bb_light, bb_dark, black_pawns)
    ):
        if light != dark:
            colour_mask = chess.BB_LIGHT_SQUARES if light else chess.BB_DARK_SQUARES
            own_on_colour = chess.popcount(pawns & colour_mask)
            total = chess.popcount(pawns)
            if total >= 4 and own_on_colour * 3 >= total * 2:
                tags.append("bad_bishop")
                break
    # Weak colour complex: no bishop of one colour, most pawns on the other,
    # and the opponent keeps a bishop of the missing colour.
    for light, dark, pawns, enemy_light, enemy_dark in (
        (wb_light, wb_dark, white_pawns, bb_light, bb_dark),
        (bb_light, bb_dark, black_pawns, wb_light, wb_dark),
    ):
        total = chess.popcount(pawns)
        if total < 4:
            continue
        on_light = chess.popcount(pawns & chess.BB_LIGHT_SQUARES)
        if not light and enemy_light and (total - on_light) * 3 >= total * 2:
            tags.append("weak_colour_complex")
            break
        if not dark and enemy_dark and on_light * 3 >= total * 2:
            tags.append("weak_colour_complex")
            break
    if _outposts(board, chess.WHITE) or _outposts(board, chess.BLACK):
        tags.append("knight_outpost")

    # -------------------------------------------------------------- material
    imbalance = _imbalance(board)
    if imbalance not in ("even", "pawns"):
        tags.append("material_imbalance")
    if imbalance == "exchange":
        tags.append("exchange_imbalance")
    if not board.queens and phase != "endgame":
        tags.append("queenless_middlegame")
    if phase == "endgame":
        minors = chess.popcount(board.knights | board.bishops)
        rooks = chess.popcount(board.rooks)
        queens = chess.popcount(board.queens)
        if not (minors or rooks or queens):
            tags.append("pawn_ending")
        elif rooks and not minors and not queens:
            tags.append("rook_ending")
        elif minors and not rooks and not queens:
            tags.append("minor_piece_ending")
        elif queens and not rooks and not minors:
            tags.append("queen_ending")
        elif rooks and minors and not queens:
            tags.append("rook_and_minor_ending")
        else:
            tags.append("complex_ending")

    # ------------------------------------------------------------- tactical
    if board.is_check():
        tags.append("in_check")
    if _hanging_piece(board):
        tags.append("hanging_piece")

    return Structure(
        phase=phase, phase24=phase24, material_white=mat_w, material_black=mat_b,
        material_diff=mat_w - mat_b, imbalance=imbalance, tags=sorted(set(tags)),
    )


def structure_of(fen: str) -> Structure:
    return analyse_structure(chess.Board(fen))
