"""The advanced-pawn exemption must select exactly the moves it claims to.

The rule is stated in chess terms: a quiet, non-promoting move by one of our
pawns that arrives on the sixth rank or beyond keeps its full depth. The search
does not evaluate that sentence -- it tests one bit of a per-node bitboard of
eligible from-squares. These tests hold the two descriptions together, because
if they ever come apart the search silently changes shape and nothing else in
the suite would notice.
"""

from __future__ import annotations

import random

import chess
import pytest

import cs_core as core


def eligible(board: chess.Board) -> int:
    """The bitboard the search computes once per node."""
    B, O, M, S, U = core.new_board_arrays()
    core.load_board(board, B, O, M, S)
    side = int(S[0])
    return int(B[1 + 6 * side]) & int(core.ADV_PUSH_SRC[side])


def selected_by_mask(board: chess.Board) -> set[str]:
    """Moves the search exempts: quiet, non-promoting, from an eligible square."""
    mask = eligible(board)
    out = set()
    for move in board.legal_moves:
        if move.promotion or board.is_capture(move):
            continue
        if mask & (1 << move.from_square):
            out.add(move.uci())
    return out


def selected_by_definition(board: chess.Board) -> set[str]:
    """The same set, written the way the rule is stated in prose."""
    white = board.turn == chess.WHITE
    out = set()
    for move in board.legal_moves:
        if move.promotion or board.is_capture(move):
            continue
        piece = board.piece_at(move.from_square)
        if piece is None or piece.piece_type != chess.PAWN:
            continue
        rank = chess.square_rank(move.to_square)
        reached = rank if white else 7 - rank
        if reached >= 5:
            out.add(move.uci())
    return out


POSITIONS = [
    # A white pawn one square from the sixth rank, and one on it.
    "8/8/8/3P4/8/8/8/K6k w - - 0 1",
    "8/8/3P4/8/8/8/8/K6k w - - 0 1",
    # The mirror, Black to move.
    "k6K/8/8/8/4p3/8/8/8 b - - 0 1",
    "k6K/8/8/8/8/4p3/8/8 b - - 0 1",
    # A pawn on the seventh: its push promotes and must never be selected.
    "8/3P4/8/8/8/8/8/K6k w - - 0 1",
    "k6K/8/8/8/8/8/3p4/8 b - - 0 1",
    # Captures onto the sixth rank are excluded by the enclosing condition.
    "8/8/2n1n3/3P4/8/8/8/K6k w - - 0 1",
    # A blocked advanced pawn: eligible square, no legal push.
    "8/8/3n4/3P4/8/8/8/K6k w - - 0 1",
    # Pieces of ours sitting on eligible squares must not be selected.
    "8/8/8/3N4/8/8/8/K6k w - - 0 1",
    "8/8/8/3R4/3P4/8/8/K6k w - - 0 1",
    # Ordinary middlegame and endgame traffic.
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "8/5k2/1p2ppp1/p1p1P3/P1P2PPK/1P6/8/8 w - - 2 44",
    "b7/2p5/1pP2k2/1P1Pp3/4Pp2/4qBp1/1Q4P1/5K2 b - - 3 45",
    chess.STARTING_FEN,
]


@pytest.mark.parametrize("fen", POSITIONS)
def test_mask_matches_the_stated_rule(fen):
    board = chess.Board(fen)
    assert board.is_valid(), fen
    assert selected_by_mask(board) == selected_by_definition(board)


def test_random_games_agree_on_every_ply():
    """Ten thousand real positions, both descriptions, no disagreement."""
    rng = random.Random(20260908)
    checked = 0
    for _ in range(120):
        board = chess.Board()
        for _ in range(120):
            moves = list(board.legal_moves)
            if not moves or board.is_game_over(claim_draw=False):
                break
            assert selected_by_mask(board) == selected_by_definition(board), board.fen()
            checked += 1
            board.push(rng.choice(moves))
    assert checked > 5000, checked


def test_a_seventh_rank_pawn_is_never_eligible():
    """Its only push promotes, and promotions were never reduced to begin with."""
    for fen, square in (("8/3P4/8/8/8/8/8/K6k w - - 0 1", chess.D7),
                        ("k6K/8/8/8/8/8/3p4/8 b - - 0 1", chess.D2)):
        board = chess.Board(fen)
        assert eligible(board) & (1 << square) == 0


def test_the_mask_is_empty_in_the_opening():
    """Nothing is exempted from the starting position, for either side."""
    board = chess.Board()
    assert eligible(board) == 0
    board.push_uci("e2e4")
    assert eligible(board) == 0


def test_the_two_side_masks_are_mirror_images():
    """Colour symmetry: the rule must not favour one side."""
    white, black = int(core.ADV_PUSH_SRC[0]) & 0xFFFFFFFFFFFFFFFF, int(
        core.ADV_PUSH_SRC[1]) & 0xFFFFFFFFFFFFFFFF
    mirrored = 0
    for square in range(64):
        if white & (1 << square):
            mirrored |= 1 << (square ^ 56)
    assert mirrored == black
