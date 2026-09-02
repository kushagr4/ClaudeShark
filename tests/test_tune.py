"""Tests for the offline tuning tooling.

The one that matters most is decomposition equivalence: the tuner fits a
reconstruction of the evaluator, and if that reconstruction drifted from the
real thing by even a centipawn, every fitted constant would be tuned against
the wrong function. The optimiser is checked on a synthetic problem with a
known answer, and the by-game split is checked for leakage.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import chess
import numpy as np
import pytest

from cs_eval import evaluate
from tools.tune.dataset import SPLIT_PATH
from tools.tune.features import EG_VALUE, MG_VALUE, decompose, reconstruct_white_pov
from tools.tune.material import LOWER, UPPER, fit, plausibility, sigmoid


def _random_boards(n: int, seed: int = 7) -> list[chess.Board]:
    rng = random.Random(seed)
    boards = []
    for _ in range(n):
        board = chess.Board()
        for _ in range(rng.randint(0, 100)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        boards.append(board)
    return boards


# ------------------------------------------------------------ decomposition


def test_decomposition_reproduces_the_evaluator_exactly() -> None:
    """Integer form must match evaluate() to the centipawn on random play."""
    mismatches = []
    for board in _random_boards(500):
        parts = decompose(board)
        sign = parts["stm"]
        expected = sign * evaluate(board)  # white POV
        got = reconstruct_white_pov(
            parts["counts"], parts["pst_mg"], parts["pst_eg"], parts["pair"],
            parts["phase"], parts["stm"], exact=True,
        )
        if int(got) != int(expected):
            mismatches.append((board.fen(), expected, got))
    assert not mismatches, f"{len(mismatches)} mismatches, first {mismatches[:2]}"


def test_continuous_form_is_within_a_centipawn_of_exact() -> None:
    for board in _random_boards(200, seed=11):
        parts = decompose(board)
        args = (parts["counts"], parts["pst_mg"], parts["pst_eg"], parts["pair"],
                parts["phase"], parts["stm"])
        assert abs(reconstruct_white_pov(*args, exact=True)
                   - reconstruct_white_pov(*args, exact=False)) < 1.0


def test_material_columns_are_white_minus_black_counts() -> None:
    board = chess.Board("4k3/8/8/8/8/8/8/R3K3 w - - 0 1")
    counts = decompose(board)["counts"]
    assert list(counts) == [0, 0, 0, 1, 0]
    board = chess.Board("3qk3/8/8/8/8/8/8/4K3 w - - 0 1")
    assert list(decompose(board)["counts"]) == [0, 0, 0, 0, -1]


def test_changing_a_material_value_moves_the_reconstruction_as_expected() -> None:
    """A +10 cp rook in a phase-24 position with one extra white rook = +10."""
    board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    board.remove_piece_at(chess.A8)  # white now has one extra rook
    parts = decompose(board)
    assert parts["phase"] >= 22
    args = (parts["counts"], parts["pst_mg"], parts["pst_eg"], parts["pair"],
            parts["phase"], parts["stm"])
    base = reconstruct_white_pov(*args, exact=False)
    bumped = MG_VALUE.copy()
    bumped[3] += 10
    moved = reconstruct_white_pov(*args, mg_value=bumped, exact=False)
    expected = 10 * parts["phase"] / 24
    assert moved - base == pytest.approx(expected, abs=0.01)


# ----------------------------------------------------------------- the split


@pytest.mark.skipif(not SPLIT_PATH.exists(), reason="split not generated")
def test_split_has_no_game_in_two_sets_and_is_roughly_stratified() -> None:
    split = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    assign = split["assign"]
    assert set(assign.values()) <= {"train", "val", "test"}
    labelled = Path(split["labelled"])
    if not labelled.exists():
        pytest.skip("labelled pool not present")
    seen: dict[str, str] = {}
    counts = {"train": 0, "val": 0, "test": 0}
    with labelled.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record") == "header":
                continue
            gid = record["game_id"]
            part = assign[gid]
            assert seen.setdefault(gid, part) == part, f"game {gid} in two splits"
            counts[part] += 1
    total = sum(counts.values())
    assert 0.6 < counts["train"] / total < 0.8
    assert 0.1 < counts["val"] / total < 0.2
    assert 0.1 < counts["test"] / total < 0.2


# -------------------------------------------------------------- the optimiser


def test_fit_recovers_a_known_material_shift_on_synthetic_data() -> None:
    """Plant a +60 cp knight (MG) and -40 cp rook (EG); the fit must find them."""
    rng = np.random.default_rng(3)
    n = 4000
    counts = rng.integers(-2, 3, size=(n, 5)).astype(float)
    phase = rng.integers(0, 25, size=n).astype(float)
    mgw = (phase / 24.0)[:, None]
    x = np.hstack([counts * mgw, counts * (1 - mgw)])
    true_delta = np.zeros(10)
    true_delta[1] = 60.0   # knight MG
    true_delta[8] = -40.0  # rook EG
    base = rng.normal(0, 150, size=n)
    k = 400.0
    es = sigmoid((base + x @ true_delta) / k) + rng.normal(0, 0.02, size=n)
    es = np.clip(es, 0, 1)
    delta = fit(x, base, es, k, lam=0.0, steps=3000)
    assert delta[1] == pytest.approx(60.0, abs=12)
    assert delta[8] == pytest.approx(-40.0, abs=12)
    # The untouched values must stay near zero.
    others = [i for i in range(10) if i not in (1, 8)]
    assert np.abs(delta[others]).max() < 15


def test_strong_ridge_returns_the_production_values() -> None:
    rng = np.random.default_rng(5)
    n = 500
    x = rng.integers(-2, 3, size=(n, 10)).astype(float)
    base = rng.normal(0, 100, size=n)
    es = np.clip(sigmoid(base / 400) + rng.normal(0, 0.05, size=n), 0, 1)
    delta = fit(x, base, es, 400.0, lam=1e6, steps=500)
    assert np.abs(delta).max() < 1.0


def test_fit_respects_the_plausibility_bounds() -> None:
    rng = np.random.default_rng(9)
    n = 500
    x = rng.integers(-2, 3, size=(n, 10)).astype(float)
    base = rng.normal(0, 100, size=n)
    # Adversarial target: says every piece is worth far more than it is.
    es = np.clip(sigmoid((base + x @ np.full(10, 900.0)) / 400), 0, 1)
    delta = fit(x, base, es, 400.0, lam=0.0, steps=800)
    prod = np.concatenate([MG_VALUE, EG_VALUE])
    assert np.all(prod + delta <= prod * UPPER + 1e-6)
    assert np.all(prod + delta >= prod * LOWER - 1e-6)


def test_plausibility_report_flags_a_broken_ordering() -> None:
    text = "\n".join(plausibility(np.array([100, 300, 300, 200, 900.0]), EG_VALUE))
    assert "**NO**" in text
    text = "\n".join(plausibility(MG_VALUE, EG_VALUE))
    assert "**yes**" in text
