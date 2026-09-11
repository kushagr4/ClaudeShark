"""The pairwise-test quiescence equals RC-J's own for E0, and the compiled E1 correction equals
the training formula.

Run: .venv/Scripts/python.exe -m pytest -q benchmarks/current/learned_eval/scripts/test_evalkit.py
"""
import json
import os
import random
import sys

import chess
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
import evalkit  # noqa: E402
import features as F  # noqa: E402

C = F.C
POOL = "C:/Users/epick/Documents/ClaudeShark-data/learned_eval/pilot/pool_v0.jsonl"


def boards(n):
    if not os.path.exists(POOL):
        pytest.skip("pool not built")
    rows = [json.loads(l) for l in open(POOL, encoding="utf-8")]
    random.Random(2).shuffle(rows)
    out = []
    for r in rows:
        b = chess.Board(r["fen"])
        if b.halfmove_clock < 90 and not b.is_insufficient_material():
            out.append(b)
        if len(out) == n:
            break
    return out


def test_qsearch_e0_equals_rcj_quiescence():
    B, O, M, S, U = C.new_board_arrays()
    MLS = np.zeros((C.STACK, C.MAX_MOVES), dtype=np.int64)
    MSS = np.zeros((C.STACK, C.MAX_MOVES), dtype=np.int64)
    GAINS = np.zeros(40, dtype=np.int64)
    PATH = np.zeros(C.STACK, dtype=np.int64)
    GK = np.zeros(64, dtype=np.int64)
    TK = np.zeros(16, dtype=np.int64)
    TV = np.zeros(16, dtype=np.int64)
    KILL = np.zeros(2 * C.STACK, dtype=np.int64)
    HIST = np.zeros(8192, dtype=np.int64)
    CTL = np.zeros(16, dtype=np.int64)
    TCTL = np.array([1e18, 1e18])
    W = np.zeros(2 * F.NF + 2)
    for b in boards(300):
        C.load_board(b, B, O, M, S)
        ours = evalkit.qsearch(B, O, M, S, U, MLS, MSS, GAINS, W, False, -C.INFINITY, C.INFINITY, 0, 0)
        ours_w0 = evalkit.qsearch(B, O, M, S, U, MLS, MSS, GAINS, W, True, -C.INFINITY, C.INFINITY, 0, 0)
        theirs = C.quiescence(B, O, M, S, U, MLS, MSS, PATH, GK, TK, TV, KILL, HIST, CTL, TCTL, GAINS,
                              -C.INFINITY, C.INFINITY, 0, 0)
        assert ours == theirs == ours_w0, b.fen()


def test_compiled_correction_equals_training_formula():
    bs = boards(300)
    X, PH, _ = F.extract(bs)
    rng = np.random.default_rng(3)
    W = rng.normal(0, 20, 2 * F.NF + 2)
    m = (PH / 24.0)[:, None]
    Z = np.hstack([X * m, X * (1 - m), m, 1 - m])
    ref = Z @ W
    BB, SS, STM = F.arrays_from_boards(bs)
    got = np.array([F.correction(BB[i], STM[i], W) for i in range(len(bs))])
    assert np.allclose(got, ref, atol=1e-7)
    got_m = np.array([F.correction(*[F.arrays_from_boards([b.mirror()])[k][0] for k in (0, 2)], W) for b in bs[:50]])
    assert np.allclose(got_m, ref[:50], atol=1e-7)
