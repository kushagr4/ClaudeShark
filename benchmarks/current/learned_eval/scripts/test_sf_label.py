"""Sign and mate conventions of the labeller's info-line parser, plus a live check that
Stockfish's reported scores have the expected sign for the side to move.

Run: .venv/Scripts/python.exe -m pytest -q benchmarks/current/learned_eval/scripts/test_sf_label.py
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import sf_label  # noqa: E402


def toks(s):
    return s.split()


def test_cp_and_wdl_side_to_move():
    r = sf_label.parse(toks("info depth 12 seldepth 18 nodes 50000 score cp 87 wdl 312 650 38 pv e2e4 e7e5"),
                       "e2e4", 0.1)
    assert r["cp"] == 87 and r["mate"] is None
    assert r["wdl"] == [312, 650, 38]
    assert r["E"] == pytest.approx((312 + 325) / 1000)
    assert r["bestmove"] == "e2e4" and r["pv"][:2] == ["e2e4", "e7e5"]


def test_mate_for_side_to_move_saturates_to_one():
    r = sf_label.parse(toks("info depth 5 nodes 900 score mate 3 wdl 1000 0 0 pv a1a8"), "a1a8", 0.0)
    assert r["mate"] == 3 and r["cp"] is None and r["E"] == 1.0


def test_being_mated_saturates_to_zero():
    r = sf_label.parse(toks("info depth 5 nodes 900 score mate -2 wdl 0 0 1000 pv h7h8"), "h7h8", 0.0)
    assert r["mate"] == -2 and r["E"] == 0.0


def test_mate_zero_without_wdl_means_side_to_move_is_mated():
    r = sf_label.parse(toks("info depth 0 score mate 0"), "(none)", 0.0)
    assert r["mate"] == 0 and r["E"] == 0.0 and r["bestmove"] is None


def test_no_info_line():
    r = sf_label.parse(None, "(none)", 0.0)
    assert r["E"] is None and r["bestmove"] is None


@pytest.fixture(scope="module")
def engine():
    if not os.path.exists(sf_label.SF_DEFAULT):
        pytest.skip("Stockfish binary not present")
    e = sf_label.Engine(sf_label.SF_DEFAULT, 16)
    yield e
    e.close()


@pytest.mark.parametrize("fen,expect", [
    ("4k3/8/8/8/8/8/8/3QK3 w - - 0 1", "win"),   # white queen up, white to move
    ("4k3/8/8/8/8/8/8/3QK3 b - - 0 1", "loss"),  # same board, black to move: bad for the mover
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "mate+"),  # white mates in 1
    ("R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1", "mated"),  # black is already checkmated
    ("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "stalemate"),  # black to move has no legal move
])
def test_live_sign(engine, fen, expect):
    r = engine.label(fen, 20000)
    if expect == "win":
        assert r["E"] > 0.9 and (r["mate"] or 0) >= 0 and (r["cp"] is None or r["cp"] > 300)
    elif expect == "loss":
        assert r["E"] < 0.1 and (r["cp"] is None or r["cp"] < -300)
    elif expect == "mate+":
        assert r["mate"] == 1 and r["E"] == 1.0 and r["bestmove"] == "a1a8"
    elif expect == "stalemate":
        assert r["mate"] is None and r["E"] == 0.5 and r["bestmove"] is None
    else:
        assert r["mate"] == 0 and r["E"] == 0.0 and r["bestmove"] is None


def test_determinism(engine):
    fen = "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 9"
    a = engine.label(fen, 50000)
    b = engine.label(fen, 50000)
    for key in ("bestmove", "cp", "mate", "wdl", "E", "depth", "nodes", "pv"):
        assert a[key] == b[key], key
