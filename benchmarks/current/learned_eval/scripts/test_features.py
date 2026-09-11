"""Colour symmetry and hand-checked values of the E1 feature extractor, and E0 identity.

Run: .venv/Scripts/python.exe -m pytest -q benchmarks/current/learned_eval/scripts/test_features.py
"""
import json
import os
import random
import sys

import chess
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
import features as F  # noqa: E402

POOL = "C:/Users/epick/Documents/ClaudeShark-data/learned_eval/pilot/pool.jsonl"


def feats(fen):
    X, PH, E0 = F.extract([chess.Board(fen)])
    return dict(zip(F.NAMES, X[0].tolist())), int(PH[0]), int(E0[0])


def sample_boards(n=600):
    if not os.path.exists(POOL):
        pytest.skip("pool not built")
    rows = [json.loads(l) for l in open(POOL, encoding="utf-8")]
    random.Random(1).shuffle(rows)
    return [chess.Board(r["fen"]) for r in rows[:n]]


def test_mirror_symmetry_features_and_e0():
    boards = sample_boards()
    X, PH, E0 = F.extract(boards)
    Xm, PHm, E0m = F.extract([b.mirror() for b in boards])
    assert np.array_equal(X, Xm)
    assert np.array_equal(PH, PHm)
    assert np.array_equal(E0, E0m)


def test_e0_matches_live_evaluate_path():
    import cs_core as C
    boards = sample_boards(50)
    _, _, E0 = F.extract(boards)
    B, O, M, S, _ = C.new_board_arrays()
    for b, e in zip(boards, E0):
        C.load_board(b, B, O, M, S)
        assert C.evaluate(B, S) == e


def test_zero_weights_zero_correction():
    b = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
    B, O, M, S, _ = F.C.new_board_arrays()
    F.C.load_board(b, B, O, M, S)
    assert F.correction(B, 0, np.zeros(2 * F.NF + 2)) == 0.0


def test_pawn_structure_counts():
    # White pawns c2 c3 d5 e6, black pawn h7, kings only otherwise.
    f, ph, _ = feats("4k3/7p/4P3/3P4/8/2P5/2P5/4K3 w - - 0 1")
    assert f["doubled"] == 1 - 0          # c2 has c3 in front of it
    assert f["isolated"] == 0 - 1         # the c-pawns have the d5 neighbour; h7 is isolated
    assert f["passed"] == 3 - 1           # c3, d5, e6 (c2 is behind its own pawn); h7 for black
    assert f["protected_passed"] == 1     # e6 is defended by d5
    assert f["connected_passed"] == 3     # c3-d5-e6 each have a passer on an adjacent file
    assert f["chain_links"] == 1          # e6 defended by a pawn
    assert f["backward"] == 0
    assert ph == 0


def test_threats_split_by_side_to_move():
    # White knight on d4 attacked by the black pawn on e5 and undefended; black to move.
    f, _, _ = feats("4k3/8/8/4p3/3N4/8/8/4K3 b - - 0 1")
    assert f["hanging_them"] == 1 and f["hanging_us"] == 0
    assert f["attacked_by_lower_them"] == 1 and f["attacked_by_lower_us"] == 0
    f2, _, _ = feats("4k3/8/8/4p3/3N4/8/8/4K3 w - - 0 1")
    assert f2["hanging_us"] == 1 and f2["attacked_by_lower_us"] == 1
