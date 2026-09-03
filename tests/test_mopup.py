"""Mop-up v1: activation domain, monotonicity, symmetry, and exact equivalence.

The term exists to give a bare-king ending a gradient toward mate. Every
property below is one the audit relied on: it fires only when one side is a
bare king and the other has a rook or queen, it is exactly zero everywhere
else, it prefers the defending king on an edge and the attacking king close,
it is antisymmetric under colour mirroring, and the bitboard version agrees
with the transparently written reference on every position tried.
"""

from __future__ import annotations

import random

import chess

import cs_eval
from cs_mopup import EDGE, PROXIMITY, mop_up, mop_up_reference

# Activating: one bare king, the other side with a rook or queen.
KQK = "8/8/8/3k4/8/8/1Q6/4K3 w - - 0 1"
KRK = "8/8/8/3k4/8/8/1R6/4K3 w - - 0 1"
KRNK = "8/8/8/3k4/8/8/1R6/1N2K3 w - - 0 1"
KRBK = "8/8/8/3k4/8/8/1R6/1B2K3 w - - 0 1"
KQRK_BLACK_ATTACKS = "q3k3/8/8/8/3K4/8/8/r7 b - - 0 1"
# Not activating.
DEFENDER_HAS_PAWN = "8/8/8/3k4/3p4/8/1Q6/4K3 w - - 0 1"
DEFENDER_HAS_MINOR = "8/8/8/3k4/3n4/8/1Q6/4K3 w - - 0 1"
ATTACKER_ONLY_MINORS = "8/8/8/3k4/8/8/1B6/1N2K3 w - - 0 1"
INSUFFICIENT = "8/8/8/3k4/8/8/1B6/4K3 w - - 0 1"
MIDDLEGAME = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
PAWN_ENDING = "8/5pk1/6p1/8/8/6P1/5PK1/8 w - - 0 1"
ROOK_ENDING_WITH_PAWNS = "8/5pk1/8/8/8/8/5PK1/R6r w - - 0 1"


def test_activates_for_each_intended_material() -> None:
    for fen in (KQK, KRK, KRNK, KRBK):
        assert mop_up(chess.Board(fen)) > 0, fen
    assert mop_up(chess.Board(KQRK_BLACK_ATTACKS)) < 0


def test_is_exactly_zero_outside_the_domain() -> None:
    for fen in (DEFENDER_HAS_PAWN, DEFENDER_HAS_MINOR, ATTACKER_ONLY_MINORS, INSUFFICIENT,
                MIDDLEGAME, PAWN_ENDING, ROOK_ENDING_WITH_PAWNS, chess.STARTING_FEN):
        assert mop_up(chess.Board(fen)) == 0, fen
        assert mop_up_reference(chess.Board(fen)) == 0, fen


def test_insufficient_material_stays_a_rules_draw_for_the_search() -> None:
    board = chess.Board(INSUFFICIENT)
    assert cs_eval.is_material_draw(board)
    assert mop_up(board) == 0


def test_driving_the_defending_king_to_the_edge_scores_higher() -> None:
    # Attacking king on h5: d5, d7 and d8 are all four squares away, so only the
    # defender's edge distance (3, 1, 0) changes between the three positions.
    centre = chess.Board("8/8/8/3k3K/8/8/1Q6/8 w - - 0 1")
    near_edge = chess.Board("8/3k4/8/7K/8/8/1Q6/8 w - - 0 1")
    edge = chess.Board("3k4/8/8/7K/8/8/1Q6/8 w - - 0 1")
    assert mop_up(centre) < mop_up(near_edge) < mop_up(edge)
    assert mop_up(near_edge) - mop_up(centre) == 2 * EDGE
    assert mop_up(edge) - mop_up(centre) == 3 * EDGE


def test_moving_the_defending_king_toward_the_centre_scores_lower() -> None:
    corner = chess.Board("k7/8/8/8/8/8/8/1Q2K3 w - - 0 1")  # edge 0, kings 7 apart
    centre = chess.Board("8/8/8/8/3k4/8/8/1Q2K3 w - - 0 1")  # edge 3, kings 3 apart
    assert mop_up(corner) == 3 * EDGE + (7 - 7) * PROXIMITY
    assert mop_up(centre) == 0 * EDGE + (7 - 3) * PROXIMITY
    assert mop_up(centre) < mop_up(corner), "with the shipped weights the edge term dominates"


def test_bringing_the_attacking_king_closer_scores_higher() -> None:
    far = chess.Board("k7/8/8/8/8/8/8/1Q5K w - - 0 1")      # kings 7 apart
    nearer = chess.Board("k7/8/8/8/3K4/8/8/1Q6 w - - 0 1")  # 4 apart
    close = chess.Board("k7/8/2K5/8/8/8/8/1Q6 w - - 0 1")   # 2 apart
    assert mop_up(far) < mop_up(nearer) < mop_up(close)
    assert mop_up(close) - mop_up(far) == 5 * PROXIMITY


def test_colour_mirroring_negates_the_term() -> None:
    for fen in (KQK, KRK, KRNK, KRBK, KQRK_BLACK_ATTACKS, "k7/8/2K5/8/8/8/8/1Q6 w - - 0 1"):
        board = chess.Board(fen)
        assert mop_up(board.mirror()) == -mop_up(board), fen


def test_fast_and_reference_agree_on_random_positions() -> None:
    rng = random.Random(20260903)
    checked = 0
    pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
    for _ in range(3000):
        board = chess.Board(None)
        squares = rng.sample(range(64), 6)
        board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        extra = rng.randint(0, 4)
        for sq in squares[2:2 + extra]:
            piece_type = rng.choice(pieces)
            colour = rng.choice((chess.WHITE, chess.BLACK))
            if piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7):
                continue
            board.set_piece_at(sq, chess.Piece(piece_type, colour))
        board.turn = rng.choice((chess.WHITE, chess.BLACK))
        if not board.is_valid():
            continue
        assert mop_up(board) == mop_up_reference(board), board.fen()
        checked += 1
    assert checked > 2000


def test_the_flag_adds_exactly_the_term_and_nothing_else(monkeypatch) -> None:
    board = chess.Board(KQK)
    cs_eval.set_term("mopup", False)
    off = cs_eval.evaluate(board)
    middlegame_off = cs_eval.evaluate(chess.Board(MIDDLEGAME))
    cs_eval.set_term("mopup", True)
    assert cs_eval.evaluate(board) - off == mop_up(board)
    assert cs_eval.evaluate(chess.Board(MIDDLEGAME)) == middlegame_off


def test_the_shipped_default_is_off() -> None:
    assert cs_eval.USE_MOP_UP is False


def test_material_still_dominates_the_term() -> None:
    board = chess.Board("k7/8/2K5/8/8/8/8/1Q6 w - - 0 1")  # cornered, kings 2 apart
    assert mop_up(board) == 3 * EDGE + 5 * PROXIMITY
    assert mop_up(board) < 300
