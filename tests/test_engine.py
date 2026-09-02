"""Correctness tests for the engine.

These are the properties that lose games for free if they break: an illegal or
missing move, a crash on an edge case, a mate the engine walks into, a timeout.
"""

from __future__ import annotations

import time

import chess
import pytest

import agent
from cs_constants import MATE_BOUND, TOTAL_PHASE
from cs_eval import evaluate, is_material_draw
from cs_ordering import Heuristics, order_moves
from cs_search import Searcher
from cs_tt import TranspositionTable, score_from_tt, score_to_tt

# A deliberately varied set: quiet and tactical middlegames, open and closed
# structures, queenless play, and every endgame family. Rated games start from
# curated positions, so breadth matters more than opening theory.
SUITE = {
    "start": chess.STARTING_FEN,
    "open_middlegame": "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9",
    "closed_middlegame": "r1bq1rk1/1pp1npbp/p1np2p1/4p3/2PPP3/2N1BP2/PP1QN1PP/R3KB1R w KQ - 0 10",
    "tactical": "r2q1rk1/pp1bbppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP1QPPP/R1B2RK1 w - - 0 10",
    "queenless": "r3k2r/pp3ppp/2n1bn2/2bp4/8/2N1BN2/PPP2PPP/R3KB1R w KQkq - 0 11",
    "king_safety": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6",
    "rook_ending": "8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 40",
    "minor_ending": "8/5pk1/4b1p1/8/8/4N1P1/5P1P/6K1 w - - 0 40",
    "pawn_ending": "8/5pk1/6p1/8/6P1/5PK1/8/8 w - - 0 40",
    "opposite_bishops": "8/4kp2/6p1/2b5/8/4B1P1/5P1P/6K1 w - - 0 40",
    "material_imbalance": "r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/2KR1B1R w kq - 0 15",
}


def _search(fen: str, ms: int = 400) -> tuple[chess.Move, object]:
    board = chess.Board(fen)
    move, info = Searcher(tt_bits=16).search(board, ms)
    assert move is not None
    return move, info


# --------------------------------------------------------------- legality


@pytest.mark.parametrize("name", sorted(SUITE))
def test_returns_a_legal_move_everywhere(name: str) -> None:
    fen = SUITE[name]
    move, _ = _search(fen)
    assert move in chess.Board(fen).legal_moves


@pytest.mark.parametrize("name", sorted(SUITE))
def test_agent_entry_point_returns_legal_uci(name: str) -> None:
    fen = SUITE[name]
    uci = agent.get_move(fen, 1_000)
    assert chess.Move.from_uci(uci) in chess.Board(fen).legal_moves


def test_single_legal_move_is_returned_immediately() -> None:
    # Black is in check from the queen on h5 and only Ke7 escapes... use a
    # position constructed so exactly one legal move exists.
    fen = "7k/8/8/8/8/8/5Q2/6RK b - - 0 1"
    board = chess.Board(fen)
    assert len(list(board.legal_moves)) == 1
    started = time.perf_counter()
    uci = agent.get_move(fen, 120_000)
    elapsed = time.perf_counter() - started
    assert uci == next(iter(board.legal_moves)).uci()
    assert elapsed < 0.25, "a forced move must not consume search time"


def test_terminal_positions_do_not_crash() -> None:
    checkmate = chess.Board("R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1")
    assert checkmate.is_checkmate()
    assert agent.get_move(checkmate.fen(), 1_000) == "0000"

    stalemate = chess.Board("7k/5Q2/8/8/8/8/8/6K1 b - - 0 1")
    assert stalemate.is_stalemate()
    assert agent.get_move(stalemate.fen(), 1_000) == "0000"


def test_promotion_and_en_passant_paths() -> None:
    promotion = "8/4P1k1/8/8/8/8/6K1/8 w - - 0 1"
    assert chess.Move.from_uci(agent.get_move(promotion, 500)) in chess.Board(promotion).legal_moves

    en_passant = "k7/8/8/3pP3/8/8/8/7K w - d6 0 2"
    board = chess.Board(en_passant)
    assert board.has_legal_en_passant()
    assert chess.Move.from_uci(agent.get_move(en_passant, 500)) in board.legal_moves


# ----------------------------------------------------------------- tactics


def test_finds_mate_in_one() -> None:
    move, info = _search("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", 600)
    assert move.uci() == "a1a8"
    assert info.score > MATE_BOUND  # type: ignore[attr-defined]


def test_finds_back_rank_mate_in_two() -> None:
    # 1. Qd8+ Rxd8 2. Rxd8#
    move, info = _search("3r2k1/5ppp/8/8/8/8/5PPP/3QR1K1 w - - 0 1", 1_500)
    assert move.uci() == "d1d8"
    assert info.score > MATE_BOUND  # type: ignore[attr-defined]


def test_wins_a_hanging_queen() -> None:
    move, _ = _search("4k3/8/8/3q4/4P3/8/8/4K3 w - - 0 1", 600)
    assert move.uci() == "e4d5"


def test_avoids_a_free_hanging_piece() -> None:
    # White's knight on e5 is attacked by the d6 pawn and must not stay there.
    fen = "4k3/8/3p4/4N3/8/8/8/4K3 w - - 0 1"
    move, _ = _search(fen, 800)
    board = chess.Board(fen)
    board.push(move)
    assert not (board.piece_at(chess.E5) and board.piece_at(chess.E5).piece_type == chess.KNIGHT)


def test_recaptures_rather_than_dropping_material() -> None:
    # Black just took on d5 with the queen; white recaptures with the knight.
    move, _ = _search("rnb1kbnr/ppp1pppp/8/3q4/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 4", 900)
    assert move.uci() == "c3d5"


# -------------------------------------------------------------- evaluation


def test_evaluation_is_symmetric_under_colour_flip() -> None:
    for fen in SUITE.values():
        board = chess.Board(fen)
        mirrored = board.mirror()
        assert evaluate(board) == evaluate(mirrored), fen


def test_evaluation_prefers_more_material() -> None:
    even = chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
    up_a_rook = chess.Board("4k3/8/8/8/8/8/8/R3K3 w - - 0 1")
    assert evaluate(up_a_rook) > evaluate(even) + 400


def test_phase_never_exceeds_the_total() -> None:
    # Nine queens is legal after promotions and must not overflow the taper.
    board = chess.Board("QQQQkQQQ/QQQ5/8/8/8/8/8/4K3 w - - 0 1")
    phase = (
        (board.knights | board.bishops).bit_count()
        + 2 * board.rooks.bit_count()
        + 4 * board.queens.bit_count()
    )
    assert phase > TOTAL_PHASE
    evaluate(board)  # must not raise or produce a nonsense taper


def test_material_draw_detection() -> None:
    assert is_material_draw(chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1"))
    assert is_material_draw(chess.Board("4k3/8/8/8/8/8/8/3BK3 w - - 0 1"))
    assert is_material_draw(chess.Board("4k1n1/8/8/8/8/8/8/3BK3 w - - 0 1"))
    assert not is_material_draw(chess.Board("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"))
    assert not is_material_draw(chess.Board("4k3/8/8/8/8/8/8/3RK3 w - - 0 1"))
    assert not is_material_draw(chess.Board("4k3/8/8/8/8/8/8/2BBK3 w - - 0 1"))


# ------------------------------------------------------- tables and search


def test_transposition_table_round_trip() -> None:
    table = TranspositionTable(bits=8)
    move = chess.Move.from_uci("e2e4")
    table.store(12345, 4, 100, 0, move)
    entry = table.probe(12345)
    assert entry is not None and entry[1] == 4 and entry[4] == move
    assert table.probe(54321) is None


def test_transposition_table_is_fixed_size() -> None:
    table = TranspositionTable(bits=8)
    for key in range(10_000):
        table.store(key, 1, 0, 0, None)
    assert len(table._slots) == 256


def test_mate_scores_survive_the_tt_round_trip() -> None:
    for score in (29_500, -29_500, 120, -120, 0):
        for ply in (0, 3, 17):
            assert score_from_tt(score_to_tt(score, ply), ply) == score


def test_tt_move_is_ordered_first() -> None:
    board = chess.Board(SUITE["open_middlegame"])
    moves = list(board.legal_moves)
    chosen = moves[len(moves) // 2]
    ordered = order_moves(board, moves, chosen, 0, Heuristics())
    assert ordered[0] == chosen
    assert sorted(ordered, key=str) == sorted(moves, key=str), "ordering must not lose moves"


def test_captures_are_ordered_before_quiet_moves() -> None:
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    moves = list(board.legal_moves)
    ordered = order_moves(board, moves, None, 0, Heuristics())
    first_quiet = next(i for i, m in enumerate(ordered) if not board.is_capture(m))
    last_capture = max(i for i, m in enumerate(ordered) if board.is_capture(m))
    assert last_capture < first_quiet


def test_deeper_search_is_not_worse_at_finding_the_win() -> None:
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    _, shallow = _search(fen, 200)
    _, deep = _search(fen, 1_200)
    assert deep.depth >= shallow.depth  # type: ignore[attr-defined]


# ------------------------------------------------------------ time control


@pytest.mark.parametrize("budget", [50, 200, 1_000, 3_000])
def test_search_respects_its_budget(budget: int) -> None:
    board = chess.Board(SUITE["tactical"])
    searcher = Searcher(tt_bits=16)
    started = time.perf_counter()
    move, _ = searcher.search(board, budget)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    assert move is not None
    assert elapsed_ms < budget * 0.9, f"used {elapsed_ms:.0f}ms of a {budget}ms clock"


def test_survives_a_nearly_flagged_clock() -> None:
    for budget in (1, 5, 20, 100):
        uci = agent.get_move(SUITE["tactical"], budget)
        assert chess.Move.from_uci(uci) in chess.Board(SUITE["tactical"]).legal_moves


def test_fixed_depth_search_is_deterministic() -> None:
    """Fixed-depth searches must not depend on the clock or the machine.

    This is what makes tools/attribute.py and tools/movequality.py trustworthy:
    if the same depth gave different node counts run to run, every pruning
    comparison built on them would be measuring noise.
    """
    fen = SUITE["open_middlegame"]
    first_move, first = Searcher(tt_bits=16).search(chess.Board(fen), 0, max_depth=5)
    second_move, second = Searcher(tt_bits=16).search(chess.Board(fen), 0, max_depth=5)
    assert first_move == second_move
    assert first.nodes == second.nodes
    assert first.score == second.score


def test_a_whole_game_against_itself_stays_legal() -> None:
    """The cheapest way to flush out rare paths: play a real game end to end."""
    board = chess.Board()
    white = Searcher(tt_bits=14)
    black = Searcher(tt_bits=14)
    for _ in range(120):
        if board.is_game_over(claim_draw=True):
            break
        searcher = white if board.turn == chess.WHITE else black
        move, _ = searcher.search(chess.Board(board.fen()), 120)
        assert move is not None
        assert move in board.legal_moves, f"illegal move {move} in {board.fen()}"
        board.push(move)
