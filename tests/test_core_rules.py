"""Targeted rule cases for the compiled core: the positions a catastrophic
correctness failure would show up in, held against python-chess and the
interpreted C5 modules rather than against remembered numbers."""

from __future__ import annotations

import random

import chess
import numpy as np
import pytest

import cs_core as core
import cs_fast
from cs_eval import is_material_draw as py_material_draw
from cs_search import PySearcher
from cs_search import rules_outcome as py_rules_outcome

# Double check, discovered check by en passant, en passant pinned along the
# rank, castling through or out of check, promotions and underpromotions with
# captures on the edge files, sliders on the corner squares (bit 63 is the
# sign bit of an int64 bitboard).
TARGETED = (
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
    "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",
    "r3k2r/8/8/8/8/8/8/4K3 b kq - 0 1",
    "4k3/8/8/8/8/8/6b1/4K2R w K - 0 1",
    "4k3/8/8/8/8/5b2/8/4K2R w K - 0 1",
    "4k3/8/8/8/8/8/8/4K2R w K - 0 1",
    "4k3/8/8/8/8/8/8/R3K3 w Q - 0 1",
    "8/8/8/2k5/2pP4/8/B7/4K3 b - d3 0 3",
    "8/8/4k3/8/2p5/8/B2P2K1/8 w - - 0 3",
    "8/8/8/8/k1p4R/8/3P4/3K4 w - - 0 3",
    "8/8/8/8/k1pP3R/8/8/3K4 b - d3 0 1",
    "8/8/8/8/1k6/8/K1Pp4/8 w - - 0 1",
    "8/8/8/k7/8/8/2p2R2/2K5 b - - 0 1",
    "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",
    "n1n5/1Pk5/8/8/8/8/5Kp1/5N1N w - - 0 1",
    "8/Pk6/8/8/8/8/6Kp/8 w - - 0 1",
    "K7/8/8/8/8/8/8/7k w - - 0 1",
    "k7/8/8/8/8/8/8/7K w - - 0 1",
    "r6k/8/8/8/8/8/8/1K5R b - - 0 1",
    "7k/8/8/8/8/8/8/K6R b - - 0 1",
    "6kb/8/8/8/8/8/8/B5K1 w - - 0 1",
    "6kq/8/8/8/8/8/8/Q5K1 w - - 0 1",
    "3k4/3p4/8/8/8/8/8/3K3R w - - 0 1",
    "5k2/8/8/8/8/8/1B6/4K3 b - - 0 1",
    "5k2/8/8/8/8/8/1B6/R3K3 w Q - 0 1",
    "2r1k3/8/8/8/8/8/8/4K2R w K - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "8/2p5/3p4/KP5r/1R3pPk/8/4P3/8 b - g3 0 1",
    "rnb2k1r/pp1Pbppp/2p5/q7/2B5/8/PPPQNnPP/RNB1K2R w KQ - 3 9",
    "r2q1rk1/pP1p2pp/Q4n2/bbp1p3/Np6/1B3NBn/pPPP1PPP/R3K2R b KQ - 0 1",
    "3K4/8/8/8/8/8/4p3/2k5 b - - 0 1",
    "8/8/1k6/8/8/8/2p5/K1n5 w - - 0 1",
)


def _arrays():
    B, O, M, S, U = core.new_board_arrays()
    MLS = np.zeros((core.STACK, core.MAX_MOVES), dtype=np.int64)
    return B, O, M, S, U, MLS


def _py_perft(board: chess.Board, depth: int) -> int:
    if depth == 0:
        return 1
    if depth == 1:
        return board.legal_moves.count()
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += _py_perft(board, depth - 1)
        board.pop()
    return total


@pytest.mark.parametrize("fen", TARGETED)
def test_targeted_perft_matches_python_chess(fen):
    board = chess.Board(fen)
    assert board.is_valid(), fen
    B, O, M, S, U, MLS = _arrays()
    core.load_board(board, B, O, M, S)
    depth = 3 if board.legal_moves.count() <= 30 else 2
    assert core.perft(B, O, M, S, U, MLS, depth) == _py_perft(board, depth), fen
    # The legal move set at the root, not just its size.
    n = core.gen_moves(B, O, M, S, MLS[0], False)
    got = set()
    for i in range(n):
        move = int(MLS[0, i])
        core.make_move(B, O, M, S, U, move)
        if core.is_legal_after_make(B, O, S):
            got.add(core.move_to_uci(move))
        core.unmake_move(B, O, M, S, U)
    assert got == {m.uci() for m in board.legal_moves}, fen


INSUFFICIENT = (
    "8/8/8/4k3/8/8/8/4K3 w - - 0 1",
    "8/8/8/4k3/8/8/8/4KB2 w - - 0 1",
    "8/8/8/4k3/8/8/8/4KN2 w - - 0 1",
    "8/8/8/4k3/8/8/8/4KNN1 w - - 0 1",
    "8/8/8/4k3/8/8/8/2B1KB2 w - - 0 1",
    "8/8/8/2b1k3/8/8/8/4KB2 w - - 0 1",
    "8/8/8/1b2k3/8/8/8/4KB2 w - - 0 1",
    "8/8/8/2n1k3/8/8/8/4KN2 w - - 0 1",
    "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1",
    "8/8/8/4k3/8/8/8/3QK3 w - - 0 1",
    "8/8/8/4k3/8/8/8/3RK3 w - - 0 1",
    "8/8/8/2b1k3/8/8/8/4KN2 w - - 0 1",
)


@pytest.mark.parametrize("fen", INSUFFICIENT)
def test_material_draw_matches_reference_on_targeted_endings(fen):
    board = chess.Board(fen)
    B, O, M, S, _, _ = _arrays()
    core.load_board(board, B, O, M, S)
    assert bool(core.is_material_draw(B)) == py_material_draw(board), fen


def test_fifty_move_outcome_matches_reference_at_clock_98_99_100():
    rng = random.Random(31)
    B, O, M, S, U, MLS = _arrays()
    checked = 0
    for _ in range(150):
        board = chess.Board()
        for _ in range(rng.randint(10, 120)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        if board.is_game_over():
            continue
        for clock in (98, 99, 100):
            board.halfmove_clock = clock
            core.load_board(board, B, O, M, S)
            in_check = board.is_check()
            want = py_rules_outcome(board, in_check, 3)
            got = core.rules_outcome(B, O, M, S, U, MLS[0], in_check, 3)
            if want is None:
                assert got == -core.INFINITY - 1, (board.fen(), got)
            else:
                assert got == want, (board.fen(), got, want)
            checked += 1
    assert checked >= 300


def test_tt_round_trip_keeps_every_field():
    TK = np.zeros(1 << core.TT_BITS, dtype=np.int64)
    TV = np.zeros(1 << core.TT_BITS, dtype=np.int64)
    rng = random.Random(37)
    for _ in range(500):
        key = rng.getrandbits(63)
        depth = rng.randint(0, 63)
        score = rng.choice(
            [rng.randint(-31000, 31000), core.MATE_SCORE - 5, -core.MATE_SCORE + 7, 0])
        bound = rng.choice([core.BOUND_EXACT, core.BOUND_LOWER, core.BOUND_UPPER])
        move = rng.getrandbits(18)
        core.tt_store(TK, TV, key, depth, score, bound, move)
        entry = core.tt_probe(TK, TV, key)
        assert entry >= 0
        assert core.tt_depth(entry) == depth
        assert core.tt_score(entry) == score
        assert core.tt_bound(entry) == bound
        assert core.tt_move(entry) == move


def test_mate_score_normalisation_round_trips():
    for ply in range(0, 60):
        for score in (core.MATE_SCORE - 1, core.MATE_SCORE - 9, -core.MATE_SCORE + 3,
                      150, -150, 0):
            assert core.score_from_tt(core.score_to_tt(score, ply), ply) == score
    # A stored mate is relative to the root; read from deeper it is closer.
    stored = core.score_to_tt(core.MATE_SCORE - 5, 2)
    assert core.score_from_tt(stored, 4) == core.MATE_SCORE - 7


def test_mate_found_through_the_table_reports_the_same_distance():
    searcher = cs_fast.Searcher()
    searcher.new_game()
    fen = "7k/8/5K2/8/8/8/8/R7 w - - 0 1"
    _, first = searcher.search(chess.Board(fen), 0, max_depth=6)
    _, again = searcher.search(chess.Board(fen), 0, max_depth=6)
    assert first.score == again.score == core.MATE_SCORE - 3


def _search_args(searcher):
    s = searcher
    return (s.B, s.O, s.M, s.S, s.U, s.MLS, s.MSS, s.PATH, s.GK, s.TK, s.TV, s.KILL,
            s.HIST, s.CTL, s.TCTL, s.GAINS, s.NNA, s.NNK)


def _prepare(searcher, fen):
    board = chess.Board(fen)
    searcher.new_game()
    searcher.CTL[:] = 0
    searcher.PATH[:] = 0
    searcher.TCTL[0] = 1e18
    core.load_board(board, searcher.B, searcher.O, searcher.M, searcher.S)
    return board


def test_repetition_on_the_current_line_is_a_draw_like_the_reference():
    # Mirrors tests/test_repetition.py on the compiled core: a position that
    # already stands at ply 1 of the line is scored 0 when ply 3 reaches it.
    searcher = cs_fast.Searcher()
    _prepare(searcher, "6k1/8/8/8/8/8/8/R5K1 w - - 10 20")
    searcher.PATH[1] = searcher.S[4]
    score = core.negamax(*_search_args(searcher), 2, -core.INFINITY, core.INFINITY, 3, False)
    assert score == core.DRAW_SCORE


def test_the_path_scan_is_bounded_by_the_halfmove_clock():
    # With a clock of 0 no repetition can have happened; the rook ending is
    # scored on its merits.
    searcher = cs_fast.Searcher()
    _prepare(searcher, "6k1/8/8/8/8/8/8/R5K1 w - - 0 1")
    searcher.PATH[1] = searcher.S[4]
    score = core.negamax(*_search_args(searcher), 2, -core.INFINITY, core.INFINITY, 3, False)
    assert score > 300


def test_root_positions_enter_the_game_record():
    # The engine sees only its own root positions; each one it is handed is
    # recorded so that reaching it again on a line scores as a draw.
    fast = cs_fast.Searcher()
    fast.new_game()
    board = chess.Board("4k3/8/8/8/8/8/8/4K2R w - - 0 1")
    fast.search(board, 0, max_depth=2)
    assert len(fast._game_keys) == 1
    B, O, M, S, U, MLS = _arrays()
    core.load_board(board, B, O, M, S)
    assert int(fast.GK[0]) == int(S[4])


def test_random_play_from_varied_positions_never_returns_an_illegal_move():
    rng = random.Random(41)
    fast = cs_fast.Searcher()
    fast.new_game()
    for _ in range(6):
        board = chess.Board()
        for _ in range(rng.randint(20, 100)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        for _ in range(30):
            if board.is_game_over(claim_draw=True):
                break
            move, _ = fast.search(board, 0, fixed_budget_ms=15)
            assert move in board.legal_moves, board.fen()
            board.push(move)
            replies = list(board.legal_moves)
            if not replies:
                break
            board.push(rng.choice(replies))
