"""King-to-pawn proximity, V2.1: the semantics the experiment relies on.

A: a king stepping one useful square closer to the nearest pawn moves the
term in that side's favour, monotonically. B: a *defending* king walking to
the attacker's pawn gains exactly as an attacking king does (C). D: colour
mirroring negates exactly. E: no pawns, no term. F: the nearest pawn decides.
G: a farther pawn changes nothing. H: pawn colour is irrelevant to the
geometry. I: the middlegame half is zero. J: switching the term on changes
only this term. Plus fast/reference equality on random legal play, random
king-and-pawn placements, and every retained calibration position.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import chess
import pytest

import cs_eval
import cs_terms
from cs_kingpawn import KING_PAWN_EG, king_pawn_distance, king_pawn_packed, king_pawn_reference

ROOT = Path(__file__).resolve().parent.parent

# White king far from a lone black pawn on e5, black king far too.
BASE = "8/8/8/4p3/8/8/8/K6k w - - 0 1"
NO_PAWNS = "8/8/3k4/8/8/2K5/8/8 w - - 0 1"
MIDDLEGAME = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
FALSE_WIN_KRB_KR = "3k4/4R3/8/5K2/4B3/8/4r3/8 w - - 0 1"


def eg(board: chess.Board) -> int:
    mg, value = king_pawn_reference(board)
    assert mg == 0
    return value


def place(white_king: str, black_king: str, pawns: dict[str, bool],
          turn: bool = chess.WHITE) -> chess.Board:
    board = chess.Board(None)
    board.set_piece_at(chess.parse_square(white_king), chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.parse_square(black_king), chess.Piece(chess.KING, chess.BLACK))
    for square, colour in pawns.items():
        board.set_piece_at(chess.parse_square(square), chess.Piece(chess.PAWN, colour))
    board.turn = turn
    assert board.is_valid(), board.fen()
    return board


def test_table_is_monotonic_non_increasing_and_zero_far_away() -> None:
    assert len(KING_PAWN_EG) == 8
    for d in range(1, 7):
        assert KING_PAWN_EG[d] >= KING_PAWN_EG[d + 1]
    assert KING_PAWN_EG[1] > 0
    assert KING_PAWN_EG[7] == 0


def test_a_king_approach_is_monotonic_in_that_sides_favour() -> None:
    # White king walks a1 -> b2 -> c3 -> d4 toward a black pawn on e5; black king fixed on h1.
    previous = None
    for square in ("a1", "b2", "c3", "d4"):
        board = place(square, "h1", {"e5": chess.BLACK})
        value = eg(board)
        if previous is not None:
            assert value >= previous, square
            if king_pawn_distance(board, chess.WHITE) <= 4:
                assert value > previous, square
        previous = value


def test_b_defending_king_gets_credit_for_reaching_the_attackers_pawn() -> None:
    # White pawn on e5 is the attacker's. Both kings start four squares from it.
    far = place("a1", "h1", {"e5": chess.WHITE}, turn=chess.BLACK)
    assert king_pawn_distance(far, chess.WHITE) == king_pawn_distance(far, chess.BLACK) == 4
    assert eg(far) == 0
    near = place("a1", "e6", {"e5": chess.WHITE}, turn=chess.BLACK)
    assert eg(near) < eg(far), "black's king reaching white's pawn must help black"
    # The credit is the same number an attacking king gets for the same distance.
    attacker = place("e4", "h1", {"e5": chess.WHITE}, turn=chess.BLACK)
    assert eg(attacker) - eg(far) == -(eg(near) - eg(far))


def test_c_attacking_king_gets_credit_for_reaching_its_own_pawn() -> None:
    far = place("a1", "h8", {"e5": chess.WHITE})
    near = place("e4", "h8", {"e5": chess.WHITE})
    assert eg(near) > eg(far)


def test_d_colour_mirroring_negates_exactly() -> None:
    fens = [BASE, NO_PAWNS, MIDDLEGAME, FALSE_WIN_KRB_KR, "8/5k2/7p/5p2/3K1P2/4P3/8/8 b - - 1 62",
            "8/1p4p1/4k1p1/p1P3P1/P2K4/1P6/8/8 w - - 3 47"]
    for fen in fens:
        board = chess.Board(fen)
        assert king_pawn_reference(board.mirror()) == (0, -eg(board)), fen
        assert king_pawn_packed(board.mirror()) == -king_pawn_packed(board), fen


def test_e_no_pawns_means_zero() -> None:
    for fen in (NO_PAWNS, FALSE_WIN_KRB_KR, "8/8/8/3k4/8/8/1Q6/4K3 w - - 0 1"):
        board = chess.Board(fen)
        assert king_pawn_reference(board) == (0, 0)
        assert king_pawn_packed(board) == 0


def test_f_the_nearest_pawn_decides_exactly() -> None:
    board = place("a1", "h8", {"b2": chess.BLACK, "e5": chess.WHITE, "g7": chess.BLACK})
    assert king_pawn_distance(board, chess.WHITE) == 1
    assert king_pawn_distance(board, chess.BLACK) == 1
    assert eg(board) == KING_PAWN_EG[1] - KING_PAWN_EG[1] == 0
    board = place("a1", "h8", {"c3": chess.BLACK, "e5": chess.WHITE})
    assert king_pawn_distance(board, chess.WHITE) == 2
    assert king_pawn_distance(board, chess.BLACK) == 3
    assert eg(board) == KING_PAWN_EG[2] - KING_PAWN_EG[3]


def test_g_adding_a_farther_pawn_changes_nothing() -> None:
    before = place("c3", "h8", {"e5": chess.WHITE})
    after = place("c3", "h8", {"e5": chess.WHITE, "b7": chess.BLACK})
    assert king_pawn_distance(before, chess.WHITE) == king_pawn_distance(after, chess.WHITE) == 2
    assert king_pawn_distance(before, chess.BLACK) == king_pawn_distance(after, chess.BLACK) == 3
    assert eg(after) == eg(before)
    assert king_pawn_packed(after) == king_pawn_packed(before)


def test_h_pawn_colour_does_not_change_the_geometry() -> None:
    own = place("d4", "h8", {"e5": chess.WHITE})
    enemy = place("d4", "h8", {"e5": chess.BLACK})
    assert king_pawn_distance(own, chess.WHITE) == king_pawn_distance(enemy, chess.WHITE) == 1
    assert eg(own) == eg(enemy)


def test_i_the_middlegame_half_is_zero() -> None:
    for fen in (BASE, MIDDLEGAME, "8/5k2/7p/5p2/3K1P2/4P3/8/8 b - - 1 62"):
        board = chess.Board(fen)
        assert king_pawn_reference(board)[0] == 0
        assert cs_terms.unpack(king_pawn_packed(board))[0] == 0
    # A full board with pawns everywhere: the term exists, the taper removes it.
    cs_eval.set_terms(())
    off = cs_eval.evaluate(chess.Board(MIDDLEGAME))
    cs_eval.set_terms(("king_pawn",))
    assert cs_eval.evaluate(chess.Board(MIDDLEGAME)) == off
    cs_eval.set_terms(())


def test_j_enabling_the_term_changes_only_this_term() -> None:
    board = chess.Board("8/1p4p1/4k1p1/p1P3P1/P2K4/1P6/8/8 w - - 3 47")  # pawn ending, phase 0
    cs_eval.set_terms(())
    off = cs_eval.evaluate(board)
    cs_eval.set_terms(("king_pawn",))
    on = cs_eval.evaluate(board)
    cs_eval.set_terms(())
    assert on - off == eg(board)
    assert cs_eval.USE_PASSED is False and cs_eval.USE_MOP_UP is False
    assert cs_eval.USE_KING_SAFETY is False


def test_the_shipped_default_is_off() -> None:
    assert cs_terms.DEFAULTS["king_pawn"] is False
    assert "king_pawn" not in cs_eval.ACTIVE_TERMS


def _random_play(count: int, seed: int) -> list[chess.Board]:
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        board = chess.Board()
        for _ in range(rng.randint(0, 100)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        out.append(board.copy(stack=False))
    return out


def _random_placements(count: int, seed: int) -> list[chess.Board]:
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        board = chess.Board(None)
        squares = rng.sample(range(64), 2 + rng.randint(0, 12))
        board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        for sq in squares[2:]:
            if chess.square_rank(sq) in (0, 7):
                continue
            kinds = (chess.PAWN, chess.PAWN, chess.PAWN, chess.ROOK,
                     chess.BISHOP, chess.KNIGHT, chess.QUEEN)
            kind = rng.choice(kinds)
            board.set_piece_at(sq, chess.Piece(kind, rng.choice((chess.WHITE, chess.BLACK))))
        board.turn = rng.choice((chess.WHITE, chess.BLACK))
        if board.is_valid():
            out.append(board)
    return out


def test_fast_matches_reference_on_random_play_and_placements() -> None:
    for board in _random_play(600, 2026) + _random_placements(3000, 904):
        assert cs_terms.unpack(king_pawn_packed(board)) == king_pawn_reference(board), board.fen()


SUITES = ["corpus/v2/endgame_calibration_v1.jsonl", "corpus/blindwin_regression_v1.jsonl"]


@pytest.mark.parametrize("path", SUITES)
def test_fast_matches_reference_on_every_retained_suite_position(path: str) -> None:
    file = ROOT / path
    if not file.exists():
        pytest.skip(f"{path} not present")
    rows = [json.loads(line) for line in file.open(encoding="utf-8")][1:]
    for r in rows:
        board = chess.Board(r["fen"])
        assert cs_terms.unpack(king_pawn_packed(board)) == king_pawn_reference(board), r["fen"]
        assert king_pawn_packed(board.mirror()) == -king_pawn_packed(board), r["fen"]
