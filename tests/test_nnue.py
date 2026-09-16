"""The optional NNUE (``CS_NNUE=1``) and its default-off guarantee.

``cs_core`` reads the flag once, at import, and compiles it in as a constant. The enabled paths
therefore run in subprocesses started with the flag set; the default-off checks run in this process,
which the suite starts without it. The heavier evidence (RC-J's depth-10 node fingerprint with the
flag off, an in-search shadow verification over the 24 openings, a walk of about 19,000
transitions, speed against RC-J) is produced by ``benchmarks/current/nnue/scripts/verify_nnue.py``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import chess
import pytest

import cs_core as core
import cs_fast

ROOT = Path(__file__).resolve().parent.parent
WALK = ROOT / "benchmarks" / "current" / "nnue" / "scripts" / "accumulator_walk.py"


def _env(**flags: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("CS_NNUE")}
    env.update(flags)
    return env


def _run(code: str, **flags: str) -> dict:
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=_env(**flags),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert out.returncode == 0, out.stderr[-3000:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_flag_is_off_by_default() -> None:
    res = _run(
        "import json, cs_core as c; "
        "print(json.dumps(dict(on=c.NNUE_ENABLED, verify=c.NNUE_VERIFY, w1=list(c.N1_W1.shape))))"
    )
    assert res == {"on": False, "verify": False, "w1": [1, 128]}


def test_verify_needs_the_flag() -> None:
    res = _run(
        "import json, cs_core as c; "
        "print(json.dumps(dict(on=c.NNUE_ENABLED, verify=c.NNUE_VERIFY)))",
        CS_NNUE_VERIFY="1",
    )
    assert res == {"on": False, "verify": False}


def test_enabled_loads_the_frozen_network() -> None:
    res = _run(
        "import json, cs_core as c; "
        "print(json.dumps(dict(on=c.NNUE_ENABLED, w1=list(c.N1_W1.shape), w2=list(c.N1_W2.shape), "
        "dt=[str(c.N1_W1.dtype), str(c.N1_W2.dtype)])))",
        CS_NNUE="1",
    )
    assert res == {"on": True, "w1": [768, 128], "w2": [32, 256], "dt": ["int16", "int8"]}


def test_enabled_refuses_missing_weights(tmp_path: Path) -> None:
    out = subprocess.run(
        [sys.executable, "-c", "import cs_core"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=_env(CS_NNUE="1", CS_NNUE_WEIGHTS=str(tmp_path / "absent.npz")),
        timeout=120,
    )
    assert out.returncode != 0 and "no N1-U weights" in out.stderr


@pytest.mark.skipif(core.NNUE_ENABLED, reason="the suite itself was started with CS_NNUE=1")
def test_default_search_never_touches_nnue_state() -> None:
    searcher = cs_fast.Searcher()
    for fen in (
        chess.STARTING_FEN,
        "r3k2r/pppq1ppp/2npbn2/4p3/4P3/2NPBN2/PPPQ1PPP/R3K2R w KQkq - 0 1",
    ):
        searcher.new_game()
        move, info = searcher.search(chess.Board(fen), 0, max_depth=5)
        assert move is not None and info.nodes > 0
    assert not searcher.NNA.any() and not searcher.NNK.any()
    assert not searcher.U[:, 7].any()


def test_accumulator_matches_rebuild_and_reference_over_random_walks() -> None:
    out = subprocess.run(
        [sys.executable, str(WALK), "--walks", "25", "--steps", "40"],
        cwd=ROOT,
        env=_env(CS_NNUE="1"),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert out.stdout.strip(), out.stderr[-3000:]
    res = json.loads(out.stdout.strip().splitlines()[-1])
    assert res["passed"], res["first_failures"]
    counts = res["counts"]
    assert counts["transitions"] >= 2000 and counts["evaluations"] >= 1000
    for kind in (
        "capture",
        "en_passant",
        "king_move",
        "null_move",
        "unmake",
        "multi_ply_catch_up",
        "promotion_queen",
        "promotion_knight",
        "castle_kingside_white",
        "castle_queenside_black",
    ):
        assert counts.get(kind, 0) > 0, f"the walk never produced {kind}"


def test_enabled_search_keeps_the_accumulator_exact() -> None:
    code = """
import json, chess, cs_core, cs_fast
s = cs_fast.Searcher()
moves = []
for fen in (chess.STARTING_FEN,
            "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
            "8/P1P3kp/8/8/8/8/1p3p1K/8 w - - 0 1"):
    s.new_game()
    mv, info = s.search(chess.Board(fen), 0, max_depth=6)
    moves.append(chess.Board(fen).is_legal(mv))
board = chess.Board("r3k2r/pppq1ppp/2npbn2/4p3/4P3/2NPBN2/PPPQ1PPP/R3K2R w KQkq - 0 1")
s.new_game()
for _ in range(16):
    mv, info = s.search(board, 0, max_depth=4)
    moves.append(board.is_legal(mv))
    board.push(mv)
    if board.is_game_over():
        break
c = s.NNA[cs_core.N1_CTRL]
print(json.dumps(dict(on=cs_core.NNUE_ENABLED, verify=cs_core.NNUE_VERIFY, legal=all(moves),
                      evaluations=int(c[0]), rebuilds=int(c[1]), mismatches=int(c[4]),
                      seeds=int(c[7]))))
"""
    res = _run(code, CS_NNUE="1", CS_NNUE_VERIFY="1")
    assert res["on"] and res["verify"] and res["legal"]
    assert res["evaluations"] > 1000
    assert res["mismatches"] == 0
    assert res["rebuilds"] == res["seeds"], (
        "the search rebuilt an accumulator outside the root seed"
    )


def test_shipped_modules_stay_release_clean(tmp_path: Path) -> None:
    """The NNUE loader lives in a shipped module, so release_check's source scan (no file-open
    or write calls, no machine-specific paths) must still pass on every root module."""
    from tools.release_check import check_source_hygiene

    for path in ROOT.glob("*.py"):
        (tmp_path / path.name).write_bytes(path.read_bytes())
    failed = [(c.name, c.detail) for c in check_source_hygiene(tmp_path) if not c.ok]
    assert not failed, failed


def test_enabled_rejects_weights_with_the_wrong_types(tmp_path: Path) -> None:
    import numpy as np

    with np.load(core.NNUE_WEIGHTS_DEFAULT) as z:
        layers = {k: z[k] for k in ("W1q", "b1q", "W2q", "b2q", "w3q", "b3q")}
    layers["W2q"] = layers["W2q"].astype(np.float32)
    bad = tmp_path / "float_w2.npz"
    np.savez(bad, **layers)
    out = subprocess.run(
        [sys.executable, "-c", "import cs_core"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=_env(CS_NNUE="1", CS_NNUE_WEIGHTS=str(bad)),
        timeout=120,
    )
    assert out.returncode != 0 and "quantised layers" in out.stderr
