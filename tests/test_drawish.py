"""Low-material nominal-surplus scaling, V2.2a.

The three families, the exclusions, and the arithmetic.

Every included family is checked in both colours and with both sides to
move; the correction equals the stated fraction of the evaluator's own
tapered material surplus; mirroring negates exactly; every near-miss
outside the rule returns exactly zero; the fast version equals the
reference on random play, random placements of each family and of each
near-miss, and every retained audit position; the term enters the
evaluation only through the registry and touches nothing else.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import chess
import pytest

import cs_eval
import cs_terms
from cs_constants import _EG_VALUE, _MG_VALUE, TOTAL_PHASE
from cs_drawish import REMOVE_QUARTERS, low_material, low_material_reference

ROOT = Path(__file__).resolve().parent.parent


def taper(mg: int, eg: int, phase: int) -> int:
    total = mg * phase + eg * (TOTAL_PHASE - phase)
    return total // TOTAL_PHASE if total >= 0 else -(-total // TOTAL_PHASE)


def place(pieces: dict[str, str], turn: bool = chess.WHITE) -> chess.Board:
    """pieces: square -> piece symbol (upper white, lower black)."""
    board = chess.Board(None)
    for square, symbol in pieces.items():
        board.set_piece_at(chess.parse_square(square), chess.Piece.from_symbol(symbol))
    board.turn = turn
    assert board.is_valid(), board.fen()
    return board


# Family A: rook and minor against rook, no pawns.
KRB_KR = {"d8": "k", "e7": "R", "f5": "K", "e4": "B", "e2": "r"}
KRN_KR = {"d8": "k", "e7": "R", "f5": "K", "e4": "N", "e2": "r"}
# Family B: rook against a lone minor.
KR_KB = {"e2": "K", "g3": "k", "d6": "R", "e4": "b"}
KR_KN = {"e2": "K", "g3": "k", "d6": "R", "e4": "n"}
# Family C: lone minor against one or two pawns.
KB_KP = {"e3": "K", "e5": "k", "c4": "B", "f5": "p"}
KN_KP = {"e3": "K", "e5": "k", "c3": "N", "f5": "p"}
KB_KPP = {"e3": "K", "e5": "k", "c4": "B", "f5": "p", "a5": "p"}
KN_KPP = {"e3": "K", "e5": "k", "c3": "N", "f5": "p", "a5": "p"}

FAMILIES = {
    "A KRB v KR": (KRB_KR, "A", (chess.BISHOP, 0)),
    "A KRN v KR": (KRN_KR, "A", (chess.KNIGHT, 0)),
    "B KR v KB": (KR_KB, "B", (chess.BISHOP, 0)),
    "B KR v KN": (KR_KN, "B", (chess.KNIGHT, 0)),
    "C KB v K+P": (KB_KP, "C", (chess.BISHOP, 1)),
    "C KN v K+P": (KN_KP, "C", (chess.KNIGHT, 1)),
    "C KB v K+2P": (KB_KPP, "C", (chess.BISHOP, 2)),
    "C KN v K+2P": (KN_KPP, "C", (chess.KNIGHT, 2)),
}


def expected(family: str, minor: int, pawns: int, phase: int) -> int:
    if family == "A":
        surplus = taper(_MG_VALUE[minor], _EG_VALUE[minor], phase)
    elif family == "B":
        surplus = taper(_MG_VALUE[chess.ROOK] - _MG_VALUE[minor],
                        _EG_VALUE[chess.ROOK] - _EG_VALUE[minor], phase)
    else:
        surplus = taper(_MG_VALUE[minor] - pawns * _MG_VALUE[chess.PAWN],
                        _EG_VALUE[minor] - pawns * _EG_VALUE[chess.PAWN], phase)
    return surplus * REMOVE_QUARTERS[family] // 4


def swap_colours(pieces: dict[str, str]) -> dict[str, str]:
    """Same squares mirrored vertically, colours swapped: the exact colour mirror."""
    out = {}
    for square, symbol in pieces.items():
        sq = chess.parse_square(square)
        mirrored = chess.square(chess.square_file(sq), 7 - chess.square_rank(sq))
        out[chess.square_name(mirrored)] = symbol.swapcase()
    return out


@pytest.mark.parametrize("name", list(FAMILIES))
def test_family_correction_is_the_stated_fraction_of_the_tapered_surplus(name: str) -> None:
    pieces, family, (minor, pawns) = FAMILIES[name]
    for turn in (chess.WHITE, chess.BLACK):
        board = place(pieces, turn)
        phase = (board.knights | board.bishops).bit_count() + 2 * board.rooks.bit_count()
        want = expected(family, minor, pawns, phase)
        assert want > 0
        # White holds the surplus in every fixture as written: the correction is negative for White.
        assert low_material_reference(board) == -want, name
        assert low_material(board) == -want, name
        # Colour-swapped: Black holds the surplus, the correction is positive for White.
        swapped = place(swap_colours(pieces), not turn)
        assert low_material(swapped) == want, name
        assert low_material_reference(swapped) == want, name


@pytest.mark.parametrize("name", list(FAMILIES))
def test_mirroring_negates_exactly_and_side_to_move_does_not_matter(name: str) -> None:
    pieces = FAMILIES[name][0]
    for turn in (chess.WHITE, chess.BLACK):
        board = place(pieces, turn)
        assert low_material(board.mirror()) == -low_material(board)
        assert low_material(place(pieces, not turn)) == low_material(board)


def test_family_c_never_manufactures_an_advantage_for_the_minor_side() -> None:
    # Two pawns against a knight leaves a positive nominal surplus (281 - 188 in the endgame);
    # the correction removes three quarters of exactly that, not of the knight.
    board = place(KN_KPP)
    phase = 1
    surplus = taper(_MG_VALUE[chess.KNIGHT] - 2 * _MG_VALUE[chess.PAWN],
                    _EG_VALUE[chess.KNIGHT] - 2 * _EG_VALUE[chess.PAWN], phase)
    assert 0 < surplus < _EG_VALUE[chess.KNIGHT]
    assert low_material(board) == -(surplus * 3 // 4)


NEAR_MISSES = {
    "KRB+P v KR": {"d8": "k", "e7": "R", "f5": "K", "e4": "B", "e2": "r", "a3": "P"},
    "KRN+P v KR": {"d8": "k", "e7": "R", "f5": "K", "e4": "N", "e2": "r", "a3": "P"},
    "KRR v KR": {"d8": "k", "e7": "R", "f5": "K", "a1": "R", "e2": "r"},
    "KRB v KRR": {"d8": "k", "e7": "R", "f5": "K", "e4": "B", "e2": "r", "h8": "r"},
    "KR v KB+P": {"e2": "K", "g3": "k", "d6": "R", "e4": "b", "h5": "p"},
    "KB+P v K+P": {"e3": "K", "e5": "k", "c4": "B", "f5": "p", "a3": "P"},
    "KB v K+3P": {"e3": "K", "e5": "k", "c4": "B", "f5": "p", "a5": "p", "h6": "p"},
    "KN v K+3P": {"e3": "K", "e5": "k", "c3": "N", "f5": "p", "a5": "p", "h6": "p"},
    "KQ v KB": {"e2": "K", "g3": "k", "d7": "Q", "e4": "b"},
    "KRB v KR + queen": {"d8": "k", "e7": "R", "f5": "K", "e4": "B", "e2": "r", "a1": "q"},
    "KBN v K": {"e3": "K", "e5": "k", "c4": "B", "a1": "N"},
    "KBB v KR": {"e2": "K", "g3": "k", "d6": "r", "e4": "B", "a1": "B"},
    "KRB v KRB": {"d8": "k", "e7": "R", "f5": "K", "e4": "B", "e2": "r", "h6": "b"},
    "KRB v KRN": {"d8": "k", "e7": "R", "f5": "K", "e4": "B", "e2": "r", "h6": "n"},
    "KR v K": {"e2": "K", "g4": "k", "d6": "R"},
    "KB v K": {"e2": "K", "g4": "k", "d6": "B"},
    "KRB v KR + weak-side pawn": {"d8": "k", "e7": "R", "f5": "K", "e4": "B", "e2": "r", "h5": "p"},
    "KN+P v K+P (pawns both sides)": {"e3": "K", "e5": "k", "c3": "N", "f5": "p", "a3": "P"},
    "KB v K+2P with a rook": {"e3": "K", "e5": "k", "c4": "B", "f5": "p", "a5": "p", "h1": "R"},
    "starting position": None,
}


@pytest.mark.parametrize("name", list(NEAR_MISSES))
def test_near_misses_are_exactly_zero(name: str) -> None:
    pieces = NEAR_MISSES[name]
    board = chess.Board() if pieces is None else place(pieces)
    assert low_material(board) == 0, name
    assert low_material_reference(board) == 0, name
    assert low_material(board.mirror()) == 0, name


def _random_play(count: int, seed: int) -> list[chess.Board]:
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        board = chess.Board()
        for _ in range(rng.randint(0, 120)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        out.append(board.copy(stack=False))
    return out


def _random_family_placements(count: int, seed: int) -> list[chess.Board]:
    rng = random.Random(seed)
    kinds = [
        ["R", "r", "B"], ["R", "r", "N"], ["R", "b"], ["R", "n"], ["B", "p"], ["N", "p"],
        ["B", "p", "p"], ["N", "p", "p"], ["R", "r", "B", "P"], ["R", "r", "B", "b"],
        ["R", "R", "r"],
        ["B", "p", "p", "p"], ["Q", "b"], ["B", "N"], ["R"], ["B", "P", "p"],
    ]
    out = []
    while len(out) < count:
        board = chess.Board(None)
        symbols = rng.choice(kinds)
        if rng.random() < 0.5:
            symbols = [s.swapcase() for s in symbols]
        squares = rng.sample(range(64), 2 + len(symbols))
        board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        ok = True
        for sq, symbol in zip(squares[2:], symbols, strict=True):
            if symbol.lower() == "p" and chess.square_rank(sq) in (0, 7):
                ok = False
                break
            board.set_piece_at(sq, chess.Piece.from_symbol(symbol))
        board.turn = rng.choice((chess.WHITE, chess.BLACK))
        if ok and board.is_valid():
            out.append(board)
    return out


def test_fast_matches_reference_on_random_play_and_placements() -> None:
    for board in _random_play(500, 2026) + _random_family_placements(4000, 905):
        assert low_material(board) == low_material_reference(board), board.fen()
        assert low_material(board.mirror()) == -low_material(board), board.fen()


AUDIT_FILES = ["corpus/v2/fw/krminor/01_report.jsonl", "corpus/v2/fw/lowmat/01_report.jsonl"]


@pytest.mark.parametrize("path", AUDIT_FILES)
def test_fast_matches_reference_on_every_audited_position(path: str) -> None:
    file = ROOT / path
    if not file.exists():
        pytest.skip(f"{path} not present")
    rows = [json.loads(line) for line in file.open(encoding="utf-8")]
    for r in rows:
        board = chess.Board(r["fen"])
        value = low_material(board)
        assert value == low_material_reference(board), r["fen"]
        assert value != 0, r["fen"]
        # The surplus side is the one the audit called strong: the correction goes against it.
        assert (value < 0) == r["strong_white"], r["fen"]
        assert low_material(board.mirror()) == -value


def test_the_term_enters_only_through_the_registry_at_the_post_stage() -> None:
    term = cs_terms.BY_NAME["low_material"]
    assert term.stage == "post"
    assert cs_terms.DEFAULTS["low_material"] is False
    assert "low_material" not in cs_eval.ACTIVE_TERMS
    board = place(KRB_KR)
    cs_eval.set_terms(("king_pawn",))
    v21 = cs_eval.evaluate(board)
    cs_eval.set_terms(("king_pawn", "low_material"))
    on = cs_eval.evaluate(board)
    cs_eval.set_terms(("king_pawn",))
    assert on - v21 == low_material(board)  # White to move: the correction as is
    middlegame = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    cs_eval.set_terms(("king_pawn", "low_material"))
    with_term = cs_eval.evaluate(middlegame)
    cs_eval.set_terms(("king_pawn",))
    assert with_term == cs_eval.evaluate(middlegame)
    cs_eval.set_terms(())
