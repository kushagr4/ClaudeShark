"""Passed pawns v1: the detector, the counting rule, the tables, and the evaluator hook.

The feature is one bonus indexed by relative rank for pawns no enemy pawn can
stop. Every property below is one the experiment relies on: the definition is
colour-correct and ignores pieces, doubled passers count once, both tables are
monotonic in advancement, the term is antisymmetric under mirroring, the fast
bitboard version agrees with the written-out reference on every position
tried, and the flag adds exactly the term to the evaluation and nothing else.
"""

from __future__ import annotations

import random
from itertools import pairwise

import chess
import pytest

import cs_eval
from cs_passed import (
    PASSED_EG,
    PASSED_MG,
    is_passed,
    passed_pawn_mask,
    passed_pawns_packed,
    passed_pawns_reference,
)

# One white pawn on e5, black king far away. Variations add a black pawn.
LONE = "4k3/8/8/4P3/8/8/8/4K3 w - - 0 1"
ENEMY_AHEAD_SAME_FILE = "4k3/4p3/8/4P3/8/8/8/4K3 w - - 0 1"
ENEMY_AHEAD_ADJACENT = "4k3/3p4/8/4P3/8/8/8/4K3 w - - 0 1"
ENEMY_AHEAD_OTHER_ADJACENT = "4k3/5p2/8/4P3/8/8/8/4K3 w - - 0 1"
ENEMY_LEVEL_ADJACENT = "4k3/8/8/3pP3/8/8/8/4K3 w - - 0 1"
ENEMY_BEHIND = "4k3/8/8/4P3/3p4/8/8/4K3 w - - 0 1"
ENEMY_TWO_FILES_AWAY = "4k3/2p5/8/4P3/8/8/8/4K3 w - - 0 1"
A_FILE_FREE = "4k3/1p6/8/P7/8/8/8/4K3 w - - 0 1"  # b7 is ahead and adjacent: not passed
A_FILE_PASSED = "4k3/8/8/P7/8/8/2p5/4K3 w - - 0 1"
H_FILE_FREE = "4k3/6p1/8/7P/8/8/8/4K3 w - - 0 1"  # g7 is ahead and adjacent: not passed
H_FILE_PASSED = "4k3/8/8/7P/8/8/5p2/4K3 w - - 0 1"
DOUBLED = "4k3/8/8/4P3/4P3/8/8/4K3 w - - 0 1"
CONNECTED = "4k3/8/8/3PP3/8/8/8/4K3 w - - 0 1"
OWN_PIECE_BLOCKER = "4k3/8/4N3/4P3/8/8/8/4K3 w - - 0 1"
ENEMY_PIECE_BLOCKER = "4k3/8/4n3/4P3/8/8/8/4K3 w - - 0 1"
MULTIPLE = "4k3/8/8/P3P2P/8/8/8/4K3 w - - 0 1"
# Black just played d7-d5 beside a white pawn on e5. By the definition the d5
# pawn is level, not ahead, so e5 stays passed regardless of the en-passant right.
EN_PASSANT = "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2"
MIDDLEGAME = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"


def white_passers(fen: str) -> list[int]:
    return list(chess.scan_forward(passed_pawn_mask(chess.Board(fen), chess.WHITE)))


def test_a_lone_pawn_is_passed() -> None:
    assert white_passers(LONE) == [chess.E5]


def test_an_enemy_pawn_ahead_on_the_same_file_blocks() -> None:
    assert white_passers(ENEMY_AHEAD_SAME_FILE) == []


def test_an_enemy_pawn_ahead_on_either_adjacent_file_blocks() -> None:
    assert white_passers(ENEMY_AHEAD_ADJACENT) == []
    assert white_passers(ENEMY_AHEAD_OTHER_ADJACENT) == []


def test_an_enemy_pawn_level_or_behind_does_not_block() -> None:
    assert white_passers(ENEMY_LEVEL_ADJACENT) == [chess.E5]
    assert white_passers(ENEMY_BEHIND) == [chess.E5]


def test_an_enemy_pawn_two_files_away_does_not_block() -> None:
    assert white_passers(ENEMY_TWO_FILES_AWAY) == [chess.E5]


def test_the_definition_is_mirrored_for_black() -> None:
    for fen, expected in ((LONE, 1), (ENEMY_AHEAD_SAME_FILE, 0), (ENEMY_AHEAD_ADJACENT, 0),
                          (ENEMY_BEHIND, 1), (ENEMY_LEVEL_ADJACENT, 1)):
        mirrored = chess.Board(fen).mirror()
        assert passed_pawn_mask(mirrored, chess.BLACK).bit_count() == expected, fen
        assert passed_pawn_mask(mirrored, chess.WHITE).bit_count() == (
            passed_pawn_mask(chess.Board(fen), chess.BLACK).bit_count()), fen


def test_edge_files_only_have_one_neighbour() -> None:
    assert white_passers(A_FILE_FREE) == []
    assert white_passers(A_FILE_PASSED) == [chess.A5]
    assert white_passers(H_FILE_FREE) == []
    assert white_passers(H_FILE_PASSED) == [chess.H5]


def test_doubled_passers_count_once_and_score_the_front_pawn() -> None:
    board = chess.Board(DOUBLED)
    assert is_passed(board, chess.E5, chess.WHITE)
    assert is_passed(board, chess.E4, chess.WHITE)
    assert white_passers(DOUBLED) == [chess.E5]
    assert passed_pawns_reference(board) == (PASSED_MG[4], PASSED_EG[4])


def test_connected_passers_are_two_passers() -> None:
    assert white_passers(CONNECTED) == [chess.D5, chess.E5]
    assert passed_pawns_reference(chess.Board(CONNECTED)) == (2 * PASSED_MG[4], 2 * PASSED_EG[4])


def test_pieces_in_the_path_do_not_change_the_answer() -> None:
    assert white_passers(OWN_PIECE_BLOCKER) == [chess.E5]
    assert white_passers(ENEMY_PIECE_BLOCKER) == [chess.E5]
    blocked = passed_pawns_reference(chess.Board(ENEMY_PIECE_BLOCKER))
    assert blocked == passed_pawns_reference(chess.Board(LONE))


def test_multiple_passers_add_up() -> None:
    assert white_passers(MULTIPLE) == [chess.A5, chess.E5, chess.H5]
    assert passed_pawns_reference(chess.Board(MULTIPLE)) == (3 * PASSED_MG[4], 3 * PASSED_EG[4])


def test_en_passant_target_does_not_affect_the_definition() -> None:
    board = chess.Board(EN_PASSANT)
    assert board.ep_square == chess.D6
    assert white_passers(EN_PASSANT) == [chess.E5]
    assert list(chess.scan_forward(passed_pawn_mask(board, chess.BLACK))) == [chess.D5]


def test_no_passers_in_a_normal_middlegame() -> None:
    board = chess.Board(MIDDLEGAME)
    assert passed_pawn_mask(board, chess.WHITE) == 0
    assert passed_pawn_mask(board, chess.BLACK) == 0
    assert passed_pawns_packed(board) == 0
    assert passed_pawns_packed(chess.Board()) == 0


def test_tables_are_monotonic_in_advancement_and_zero_off_the_board() -> None:
    for table in (PASSED_MG, PASSED_EG):
        assert len(table) == 8
        assert table[0] == 0 and table[7] == 0
        for earlier, later in pairwise(table[1:7]):
            assert later >= earlier, table
        assert table[6] > table[1]
    for r in range(1, 7):
        assert PASSED_EG[r] >= PASSED_MG[r]


def test_a_further_advanced_passer_scores_at_least_as_much() -> None:
    previous = None
    for rank in range(1, 7):
        board = chess.Board(None)
        board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(chess.A8, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(chess.square(4, rank), chess.Piece(chess.PAWN, chess.WHITE))
        assert board.is_valid()
        mg, eg = passed_pawns_reference(board)
        if previous is not None:
            assert (mg, eg) >= previous
        previous = (mg, eg)


def test_colour_mirroring_negates_the_term() -> None:
    for fen in (LONE, ENEMY_BEHIND, DOUBLED, CONNECTED, MULTIPLE, EN_PASSANT, MIDDLEGAME,
                "8/5k2/7p/5p2/3K1P2/4P3/8/8 b - - 1 62"):
        board = chess.Board(fen)
        mg, eg = passed_pawns_reference(board)
        assert passed_pawns_reference(board.mirror()) == (-mg, -eg), fen
        assert passed_pawns_packed(board.mirror()) == -passed_pawns_packed(board), fen


def _unpack(packed: int) -> tuple[int, int]:
    eg = packed & 0xFFFF
    if eg >= 0x8000:
        eg -= 0x10000
    return (packed - eg) >> 16, eg


def test_fast_and_reference_agree_on_random_play_and_random_placement() -> None:
    rng = random.Random(20260903)
    checked = 0
    for _ in range(400):
        board = chess.Board()
        for _ in range(rng.randint(0, 80)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        assert _unpack(passed_pawns_packed(board)) == passed_pawns_reference(board), board.fen()
        checked += 1
    for _ in range(3000):
        board = chess.Board(None)
        squares = rng.sample(range(64), 2 + rng.randint(0, 10))
        board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        for sq in squares[2:]:
            if chess.square_rank(sq) in (0, 7):
                continue
            board.set_piece_at(sq, chess.Piece(chess.PAWN, rng.choice((chess.WHITE, chess.BLACK))))
        board.turn = rng.choice((chess.WHITE, chess.BLACK))
        if not board.is_valid():
            continue
        assert _unpack(passed_pawns_packed(board)) == passed_pawns_reference(board), board.fen()
        checked += 1
    assert checked > 2500


CLUSTER_31 = "8/5k2/7p/5p2/3K1P2/4P3/8/8 b - - 1 62"


@pytest.mark.parametrize("fen", [LONE, DOUBLED, MULTIPLE, MIDDLEGAME, CLUSTER_31])
def test_full_evaluators_agree_and_stay_symmetric_with_the_flag_on(monkeypatch, fen: str) -> None:
    cs_eval.set_term("passed", True)
    board = chess.Board(fen)
    assert cs_eval.evaluate(board) == cs_eval.evaluate_reference(board)
    assert cs_eval.evaluate(board) == cs_eval.evaluate(board.mirror())


def test_the_flag_adds_exactly_the_tapered_term_and_nothing_else(monkeypatch) -> None:
    from cs_constants import TOTAL_PHASE

    board = chess.Board("4k3/8/8/4P3/8/8/8/4K3 w - - 0 1")  # pure pawn ending: phase 0
    cs_eval.set_term("passed", False)
    off = cs_eval.evaluate(board)
    middlegame_off = cs_eval.evaluate(chess.Board(MIDDLEGAME))
    cs_eval.set_term("passed", True)
    mg, eg = passed_pawns_reference(board)
    assert cs_eval.evaluate(board) - off == eg  # phase 0: the endgame value, whole
    assert cs_eval.evaluate(chess.Board(MIDDLEGAME)) == middlegame_off
    # With one queen each the same pawn is tapered.
    queens = chess.Board("4k3/8/8/4P3/8/8/8/q3K2Q w - - 0 1")
    cs_eval.set_term("passed", False)
    q_off = cs_eval.evaluate(queens)
    cs_eval.set_term("passed", True)
    phase = 8
    expected = (mg * phase + eg * (TOTAL_PHASE - phase)) // TOTAL_PHASE
    assert abs((cs_eval.evaluate(queens) - q_off) - expected) <= 1


def test_the_shipped_default_is_off() -> None:
    assert cs_eval.USE_PASSED is False


def test_the_term_stays_a_conditional_adjustment() -> None:
    # A single passer on the seventh is worth less than a pawn and a half in
    # the endgame table: it adjusts the pawn PST, it does not replace it.
    assert PASSED_EG[6] < 150
    assert PASSED_MG[6] < 80
