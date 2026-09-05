"""The incremental piece-square sum must equal the full recomputation everywhere.

``pst_delta`` is applied before every push along random games (captures,
en passant, promotions and castling all occur) and compared with
``pst_packed`` of the resulting position; ``evaluate_packed`` with the running
sum must equal ``evaluate``. A search-level check then asserts the same at
every leaf the search evaluates, by wrapping ``evaluate_packed``.
"""

from __future__ import annotations

import random

import chess

import cs_eval
import cs_search
from cs_eval import evaluate, evaluate_packed, pst_delta, pst_packed


def test_delta_matches_full_recomputation_along_random_games() -> None:
    rng = random.Random(20260905)
    plies = castles = promotions = en_passant = 0
    for _ in range(300):
        board = chess.Board()
        packed = pst_packed(board)
        for _ in range(rng.randint(10, 120)):
            moves = list(board.legal_moves)
            if not moves:
                break
            special = [
                m for m in moves
                if m.promotion or board.is_castling(m) or board.is_en_passant(m)
            ]
            move = rng.choice(special) if special and rng.random() < 0.7 else rng.choice(moves)
            castles += board.is_castling(move)
            promotions += bool(move.promotion)
            en_passant += board.is_en_passant(move)
            packed += pst_delta(board, move)
            board.push(move)
            assert packed == pst_packed(board), (board.fen(), move)
            assert evaluate_packed(board, packed) == evaluate(board), board.fen()
            plies += 1
    assert plies > 10_000 and castles > 100 and promotions > 50 and en_passant > 10


def test_search_evaluates_with_the_true_sum(monkeypatch) -> None:
    calls = 0

    def checked(board: chess.Board, packed: int) -> int:
        nonlocal calls
        calls += 1
        assert packed == pst_packed(board), board.fen()
        return cs_eval.evaluate_packed(board, packed)

    monkeypatch.setattr(cs_search, "evaluate_packed", checked)
    fens = [
        chess.STARTING_FEN,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r2q1rk1/pP1p2pp/Q4n2/bbp1p3/Np6/1B3NBn/pPPP1PPP/R3K2R b KQ - 0 1",
        "rnbqkb1r/pp1p1ppp/2p5/4P3/2B5/8/PPP1NnPP/RNBQK2R w KQkq - 0 6",
    ]
    for fen in fens:
        searcher = cs_search.Searcher()
        searcher.search(chess.Board(fen), 0, max_depth=5)
    assert calls > 20_000
