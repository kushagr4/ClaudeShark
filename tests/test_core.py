"""The compiled core (cs_core / cs_fast) against python-chess and the C5 reference.

Move generation is held exact by perft; the evaluation and static exchange
evaluation are held exact against the interpreted modules on random
positions; the search is checked on the rule cases the interpreted search
documents (mate scores, stalemate, the fifty-move claim, repetition) and on
agreement with the interpreted C5 search at fixed depth.
"""

from __future__ import annotations

import random

import chess
import numpy as np
import pytest

import cs_core as core
import cs_fast
from cs_eval import evaluate as py_evaluate
from cs_eval import is_material_draw as py_material_draw
from cs_see import see as py_see

PERFT_CASES = (
    (chess.STARTING_FEN, 4, 197_281),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3, 97_862),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5, 674_624),
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 4, 422_333),
    ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 3, 62_379),
    ("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 3, 89_890),
)


def _arrays():
    B, O, M, S, U = core.new_board_arrays()
    MLS = np.zeros((core.STACK, core.MAX_MOVES), dtype=np.int64)
    return B, O, M, S, U, MLS


def _random_board(rng: random.Random, plies: int) -> chess.Board:
    board = chess.Board()
    for _ in range(plies):
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(rng.choice(moves))
    return board


def _py_perft(board: chess.Board, depth: int) -> int:
    if depth == 1:
        return board.legal_moves.count()
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += _py_perft(board, depth - 1)
        board.pop()
    return total


@pytest.mark.parametrize(("fen", "depth", "expected"), PERFT_CASES)
def test_perft_standard_positions(fen, depth, expected):
    B, O, M, S, U, MLS = _arrays()
    core.load_board(chess.Board(fen), B, O, M, S)
    key, packed = S[4], S[5]
    assert core.perft(B, O, M, S, U, MLS, depth) == expected
    assert (S[4], S[5], S[6]) == (key, packed, 0), "state not restored after perft"


def test_perft_random_positions_match_python_chess():
    rng = random.Random(20260906)
    B, O, M, S, U, MLS = _arrays()
    checked = 0
    for game in range(40):
        board = _random_board(rng, rng.randint(0, 90))
        if board.is_game_over():
            continue
        core.load_board(board, B, O, M, S)
        depth = 3 if game % 4 == 0 else 2
        assert core.perft(B, O, M, S, U, MLS, depth) == _py_perft(board, depth), board.fen()
        checked += 1
    assert checked >= 30


def test_make_unmake_keeps_key_packed_and_board_exact():
    rng = random.Random(7)
    B, O, M, S, U, MLS = _arrays()
    B2, O2, M2, S2, _ = core.new_board_arrays()
    for _ in range(60):
        board = _random_board(rng, rng.randint(0, 100))
        if board.is_game_over():
            continue
        core.load_board(board, B, O, M, S)
        count = core.gen_moves(B, O, M, S, MLS[0], False)
        for i in range(count):
            move = int(MLS[0, i])
            core.make_move(B, O, M, S, U, move)
            if core.is_legal_after_make(B, O, S):
                assert core.compute_key(B, M, S) == S[4]
                assert core.compute_packed(M) == S[5]
                after = board.copy()
                after.push(core.move_to_chess(move))
                core.load_board(after, B2, O2, M2, S2)
                assert np.array_equal(B, B2) and np.array_equal(M, M2)
                assert (S[0], S[1], S[3]) == (S2[0], S2[1], S2[3])
            core.unmake_move(B, O, M, S, U)
        assert core.compute_key(B, M, S) == S[4] and S[6] == 0


def test_evaluation_and_material_draw_match_reference():
    rng = random.Random(11)
    B, O, M, S, _, _ = _arrays()
    for _ in range(300):
        board = _random_board(rng, rng.randint(0, 140))
        if board.is_game_over():
            continue
        core.load_board(board, B, O, M, S)
        assert core.evaluate(B, S) == py_evaluate(board), board.fen()
        assert bool(core.is_material_draw(B)) == py_material_draw(board), board.fen()


def test_see_matches_reference():
    rng = random.Random(13)
    B, O, M, S, _, _ = _arrays()
    gains = np.zeros(40, dtype=np.int64)
    checked = 0
    for _ in range(300):
        board = _random_board(rng, rng.randint(0, 120))
        if board.is_game_over():
            continue
        core.load_board(board, B, O, M, S)
        for move in board.legal_moves:
            if board.is_capture(move) or move.promotion:
                encoded = core.encode_move(board, move)
                assert core.see(B, O, M, S, encoded, gains) == py_see(board, move), (
                    board.fen(), move)
                checked += 1
    assert checked > 500


def test_has_legal_move_is_exact():
    rng = random.Random(17)
    B, O, M, S, U, MLS = _arrays()
    for _ in range(300):
        board = _random_board(rng, rng.randint(0, 160))
        if board.is_check():
            continue
        core.load_board(board, B, O, M, S)
        assert bool(core.has_legal_move(B, O, M, S, U, MLS[0])) == any(board.legal_moves)


# ------------------------------------------------------------------ search


@pytest.fixture(scope="module")
def searcher():
    return cs_fast.Searcher()


def _search(searcher, fen, depth):
    searcher.new_game()
    return searcher.search(chess.Board(fen), 0, max_depth=depth)


def test_finds_mate_in_one_and_reports_mate_score(searcher):
    move, info = _search(searcher, "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", 4)
    assert move.uci() == "a1a8"
    assert info.score == core.MATE_SCORE - 1


def test_finds_mate_in_two(searcher):
    # 1.Kg6 Kg8 2.Ra8#: a forced mate in two, reported as such.
    move, info = _search(searcher, "7k/8/5K2/8/8/8/8/R7 w - - 0 1", 6)
    assert move.uci() == "f6g6"
    assert info.score == core.MATE_SCORE - 3


def test_stalemate_is_avoided_when_mate_exists(searcher):
    # Qf7 stalemates, Qa8 mates: the search must not score the stalemate as
    # a queen up.
    board = chess.Board("7k/8/6K1/8/8/8/Q7/8 w - - 0 1")
    move, info = _search(searcher, board.fen(), 6)
    board.push(move)
    assert not board.is_stalemate()
    assert info.score > core.MATE_BOUND


def test_fifty_move_claim_beats_material(searcher):
    # White is a queen down but every move leaves the counter at 101, which
    # python-chess claims as a draw; the score must be 0, not about -900.
    move, info = _search(searcher, "7k/8/8/8/8/8/4q3/7K w - - 100 60", 4)
    assert info.score == 0


def test_root_moves_agree_with_interpreted_c5_at_fixed_depth(searcher):
    from cs_search import PySearcher

    reference = PySearcher()
    agreed = 0
    fens = (
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 1",
        "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1",
        "r1bqk2r/pp1nbppp/2p1pn2/3p4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 1",
        "rnbqkb1r/pp2pppp/2p2n2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R b KQkq - 0 1",
    )
    for fen in fens:
        reference.new_game()
        ref_move, ref_info = reference.search(chess.Board(fen), 0, max_depth=4)
        fast_move, fast_info = _search(searcher, fen, 4)
        if ref_move == fast_move:
            agreed += 1
        assert abs(ref_info.score - fast_info.score) <= 40
    assert agreed >= 3


def test_search_never_returns_illegal_move_in_random_play(searcher):
    rng = random.Random(23)
    board = chess.Board()
    searcher.new_game()
    for _ in range(80):
        if board.is_game_over():
            break
        move, _ = searcher.search(board, 0, fixed_budget_ms=20)
        assert move in board.legal_moves
        board.push(move)
        reply = list(board.legal_moves)
        if not reply:
            break
        board.push(rng.choice(reply))


def test_time_abort_returns_promptly(searcher):
    from time import perf_counter

    searcher.new_game()
    started = perf_counter()
    move, info = searcher.search(
        chess.Board("r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 1"),
        0, fixed_budget_ms=150)
    elapsed = perf_counter() - started
    assert move is not None
    assert elapsed < 0.6


# Stalemates whose only pseudo-legal captures are illegal. The compiled
# quiescence generates pseudo-legal captures and used to fall through to the
# stand-pat score when every one of them was rejected after make, scoring the
# stalemated side as simply behind on material (reproduction in
# tools/review_c9_repro.py).
STALEMATES_WITH_ILLEGAL_CAPTURE = (
    "6Bk/5K2/8/8/8/8/8/R7 b - - 0 1",
    "k7/P7/K7/8/8/8/8/8 b - - 0 1",
    "8/8/8/8/8/5k2/5p2/5K2 w - - 0 1",
)


def _prepare(searcher, board):
    searcher.new_game()
    searcher.CTL[:] = 0
    searcher.PATH[:] = 0
    searcher.TCTL[0] = 1e18
    core.load_board(board, searcher.B, searcher.O, searcher.M, searcher.S)
    s = searcher
    return (s.B, s.O, s.M, s.S, s.U, s.MLS, s.MSS, s.PATH, s.GK, s.TK, s.TV, s.KILL,
            s.HIST, s.CTL, s.TCTL, s.GAINS)


@pytest.mark.parametrize("fen", STALEMATES_WITH_ILLEGAL_CAPTURE)
def test_quiescence_scores_stalemate_as_draw_when_captures_are_illegal(searcher, fen):
    board = chess.Board(fen)
    assert board.is_valid() and board.is_stalemate(), fen
    args = _prepare(searcher, board)
    tactical = core.gen_moves(searcher.B, searcher.O, searcher.M, searcher.S,
                              searcher.MLS[0], True)
    assert tactical >= 1, "fixture should offer a pseudo-legal capture"
    assert core.quiescence(*args, -core.INFINITY, core.INFINITY, 0, 0) == core.DRAW_SCORE
    args = _prepare(searcher, board)
    assert core.negamax(*args, 1, -core.INFINITY, core.INFINITY, 0, False) == core.DRAW_SCORE


def test_search_does_not_count_a_stalemating_move_as_a_win(searcher):
    # Kb6-a6 stalemates; every white move draws, so the root score must be 0
    # rather than the +800 a mis-scored stalemate produced.
    move, info = _search(searcher, "k7/P7/1K6/8/8/8/8/8 w - - 0 1", 4)
    assert info.score == core.DRAW_SCORE


def test_quiescence_values_track_the_interpreted_reference():
    from cs_search import PySearcher

    rng = random.Random(29)
    fast = cs_fast.Searcher()
    reference = PySearcher(tt_bits=12)
    reference.time.begin_fixed(3_600_000.0)
    agreed = checked = 0
    for _ in range(200):
        board = _random_board(rng, rng.randint(0, 120))
        if board.is_game_over() or board.is_check():
            continue
        args = _prepare(fast, board)
        got = core.quiescence(*args, -core.INFINITY, core.INFINITY, 0, 0)
        want = reference._quiescence(board, -core.INFINITY, core.INFINITY, 0, 0)
        checked += 1
        agreed += got == want
        # Never a draw on one side and a decisive material verdict on the other.
        assert (got == 0) == (want == 0) or abs(got - want) < 150, (board.fen(), got, want)
    assert checked >= 120
    assert agreed >= 0.9 * checked, (agreed, checked)
