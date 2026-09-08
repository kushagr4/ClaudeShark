"""The compiled mop-up gradient against the shipped reference in ``cs_mopup``.

The term is a straight port: same gate, same weights, same point of view. These
tests hold it to the reference exactly, prove it is colour symmetric, and prove
it is exactly zero on every position of the competition-like corpus, which is
what makes the candidate inert outside bare-king endings.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import chess
import numpy as np
import pytest

import cs_core as core
from cs_mopup import mop_up, mop_up_reference

CORPUS = Path(__file__).resolve().parent.parent / "corpus" / "competition_like_v1.jsonl"


def _arrays():
    B, O, M, S, U = core.new_board_arrays()
    return B, O, M, S


def _bonus(board: chess.Board) -> int:
    B, O, M, S = _arrays()
    core.load_board(board, B, O, M, S)
    return int(core.mop_up_bonus(B))


def _place(rng, attacker_pieces, attacker=chess.WHITE, tries=400):
    """A legal position: bare defending king versus ``attacker_pieces``."""
    for _ in range(tries):
        board = chess.Board(None)
        squares = rng.sample(range(64), 2 + len(attacker_pieces))
        board.set_piece_at(squares[0], chess.Piece(chess.KING, attacker))
        board.set_piece_at(squares[1], chess.Piece(chess.KING, not attacker))
        for sq, pt in zip(squares[2:], attacker_pieces):
            board.set_piece_at(sq, chess.Piece(pt, attacker))
        board.turn = attacker
        if board.is_valid():
            return board
    return None


ELIGIBLE = ((chess.ROOK,), (chess.QUEEN,), (chess.ROOK, chess.ROOK),
            (chess.QUEEN, chess.ROOK), (chess.ROOK, chess.BISHOP),
            (chess.QUEEN, chess.KNIGHT))
INELIGIBLE = ((chess.BISHOP, chess.KNIGHT), (chess.BISHOP, chess.BISHOP),
              (chess.KNIGHT, chess.KNIGHT), (chess.BISHOP,), (chess.KNIGHT,),
              (chess.PAWN,))


def _sample(rng, count=260):
    """A mixed bag: eligible bare-king endings, ineligible ones, and normal play."""
    boards = []
    for i in range(count // 2):
        pieces = (ELIGIBLE + INELIGIBLE)[i % (len(ELIGIBLE) + len(INELIGIBLE))]
        colour = chess.WHITE if i % 2 == 0 else chess.BLACK
        board = _place(rng, pieces, colour)
        if board is not None:
            boards.append(board)
    for _ in range(count - len(boards)):
        board = chess.Board()
        for _ in range(rng.randint(0, 80)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        if not board.is_game_over():
            boards.append(board)
    return boards


def test_compiled_bonus_matches_the_shipped_reference_exactly():
    rng = random.Random(20260907)
    boards = _sample(rng, 320)
    assert len(boards) >= 250
    eligible = 0
    for board in boards:
        want = mop_up_reference(board)
        assert mop_up(board) == want, board.fen()          # the two shipped forms agree
        assert _bonus(board) == want, board.fen()          # and the compiled port matches
        eligible += want != 0
    assert eligible >= 40, f"only {eligible} positions actually exercised the term"


def test_colour_symmetry_under_mirror():
    rng = random.Random(4242)
    checked = 0
    for board in _sample(rng, 220):
        mirrored = board.mirror()
        assert _bonus(mirrored) == -_bonus(board), board.fen()
        checked += 1
    assert checked >= 180


@pytest.mark.parametrize("pieces", ELIGIBLE)
def test_gate_admits_a_bare_king_against_a_rook_or_queen(pieces):
    rng = random.Random(hash(pieces) & 0xFFFF)
    board = _place(rng, pieces)
    assert board is not None
    assert _bonus(board) > 0, board.fen()
    assert _bonus(board) == mop_up_reference(board)


@pytest.mark.parametrize("pieces", INELIGIBLE)
def test_gate_excludes_everything_without_a_rook_or_queen(pieces):
    rng = random.Random(hash(pieces) & 0xFFFF)
    board = _place(rng, pieces)
    assert board is not None
    assert _bonus(board) == 0, board.fen()


def test_king_versus_king_is_zero():
    assert _bonus(chess.Board("8/8/8/4k3/8/8/8/4K3 w - - 0 1")) == 0


def test_bonus_is_zero_on_every_competition_like_position():
    rows = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines()]
    fens = [r["fen"] for r in rows if "fen" in r]
    assert len(fens) >= 200
    nonzero = [fen for fen in fens if _bonus(chess.Board(fen)) != 0]
    assert nonzero == [], nonzero


def test_gradient_rewards_driving_the_king_to_the_edge_and_closing_in():
    # The rook is kept off the defending king's file and rank so that every
    # fixture is a legal position with the defender not in check.
    centre = chess.Board("8/8/8/3k4/8/8/8/R3K3 w - - 0 1")
    edge = chess.Board("k7/8/8/8/8/8/8/1R2K3 w - - 0 1")
    assert _bonus(edge) > _bonus(centre)
    far = chess.Board("k7/8/8/8/8/8/8/1R2K3 w - - 0 1")
    near = chess.Board("k7/2K5/8/8/8/8/8/1R6 w - - 0 1")
    assert _bonus(near) > _bonus(far)


def test_compiled_score_is_the_interpreted_score_plus_the_bonus():
    """Ties the two implementations together, including the point-of-view flip.

    ``cs_eval`` ships every registry term off, so the interpreted evaluation is
    the tapered score without the gradient. The compiled evaluation is that
    score plus the mop-up bonus, negated when black is to move.
    """
    from cs_eval import evaluate as py_evaluate

    rng = random.Random(99)
    boards = _sample(rng, 240)
    exercised = 0
    for board in boards:
        B, O, M, S = _arrays()
        core.load_board(board, B, O, M, S)
        bonus = int(core.mop_up_bonus(B))
        expected = py_evaluate(board) + (bonus if board.turn == chess.WHITE else -bonus)
        assert int(core.evaluate(B, S)) == expected, board.fen()
        exercised += bonus != 0
    assert exercised >= 40
