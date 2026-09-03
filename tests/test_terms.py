"""The term registry.

Every registered term is independent, antisymmetric, reference-equivalent and off by default.

These are the properties any new term inherits a test for by being added
to ``cs_terms.TERMS``: it is zero-cost and invisible when off, it negates
under colour mirroring, its fast and reference versions agree on random
positions, it enters the evaluator at the stage it declares and nowhere
else, and switching it on changes nothing about any other term.
"""

from __future__ import annotations

import random

import chess
import pytest

import cs_eval
import cs_terms
from cs_constants import TOTAL_PHASE

MIDDLEGAME = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
ENDGAME = "8/5k2/7p/5p2/3K1P2/4P3/8/8 b - - 1 62"
BARE_KING = "8/8/8/3k4/8/8/1Q6/4K3 w - - 0 1"
EXPOSED = "3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 0 1"
FENS = (chess.STARTING_FEN, MIDDLEGAME, ENDGAME, BARE_KING, EXPOSED)


def random_boards(count: int, seed: int) -> list[chess.Board]:
    rng = random.Random(seed)
    out = []
    while len(out) < count:
        board = chess.Board()
        for _ in range(rng.randint(0, 90)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        out.append(board.copy(stack=False))
    return out


def test_shipped_defaults_are_all_off_and_nothing_is_active() -> None:
    assert all(value is False for value in cs_terms.DEFAULTS.values())
    assert frozenset() == cs_eval.ACTIVE_TERMS
    assert cs_eval._PACKED_TERMS == () and cs_eval._POST_TERMS == ()


def test_every_term_has_a_default_a_stage_and_a_flag() -> None:
    for term in cs_terms.TERMS:
        assert term.name in cs_terms.DEFAULTS
        assert term.stage in ("packed", "post")
        assert term.flag.startswith("CS_EVAL_")


@pytest.mark.parametrize("term", cs_terms.TERMS, ids=lambda t: t.name)
def test_term_is_antisymmetric_under_colour_mirroring(term: cs_terms.Term) -> None:
    for board in [chess.Board(f) for f in FENS] + random_boards(150, 7):
        mirrored = board.mirror()
        if term.stage == "packed":
            mg, eg = cs_terms.unpack(term.fast(board))
            assert cs_terms.unpack(term.fast(mirrored)) == (-mg, -eg), (term.name, board.fen())
        else:
            assert term.fast(mirrored) == -term.fast(board), (term.name, board.fen())


@pytest.mark.parametrize("term", cs_terms.TERMS, ids=lambda t: t.name)
def test_fast_and_reference_agree(term: cs_terms.Term) -> None:
    for board in [chess.Board(f) for f in FENS] + random_boards(200, 11):
        if term.stage == "packed":
            expected = tuple(term.reference(board))
            assert cs_terms.unpack(term.fast(board)) == expected, (term.name, board.fen())
        else:
            assert term.fast(board) == term.reference(board), (term.name, board.fen())


@pytest.mark.parametrize("term", cs_terms.TERMS, ids=lambda t: t.name)
def test_switching_a_term_on_adds_exactly_that_term_at_its_stage(term: cs_terms.Term) -> None:
    for board in [chess.Board(f) for f in FENS] + random_boards(60, 13):
        cs_eval.set_terms(())
        off = cs_eval.evaluate(board)
        off_reference = cs_eval.evaluate_reference(board)
        assert off == off_reference
        cs_eval.set_terms((term.name,))
        on = cs_eval.evaluate(board)
        assert on == cs_eval.evaluate_reference(board), (term.name, board.fen())
        sign = 1 if board.turn else -1
        if term.stage == "post":
            assert on - off == sign * term.fast(board), (term.name, board.fen())
        else:
            phase = ((board.knights | board.bishops).bit_count() + 2 * board.rooks.bit_count()
                     + 4 * board.queens.bit_count())
            phase = min(TOTAL_PHASE, phase)
            mg, eg = cs_terms.unpack(term.fast(board))
            expected = (mg * phase + eg * (TOTAL_PHASE - phase)) / TOTAL_PHASE
            assert abs((on - off) - sign * expected) <= 1, (term.name, board.fen())
        cs_eval.set_terms(())


def test_terms_do_not_interact() -> None:
    names = [t.name for t in cs_terms.TERMS]
    for board in [chess.Board(f) for f in FENS] + random_boards(60, 17):
        cs_eval.set_terms(())
        base = cs_eval.evaluate(board)
        deltas = []
        for name in names:
            cs_eval.set_terms((name,))
            deltas.append(cs_eval.evaluate(board) - base)
        cs_eval.set_terms(names)
        together = cs_eval.evaluate(board) - base
        cs_eval.set_terms(())
        # Packed terms share one truncating division, so the sum may differ by
        # the rounding of that division; nothing larger is allowed.
        assert abs(together - sum(deltas)) <= len(names), board.fen()


def test_full_evaluation_stays_symmetric_with_every_term_on() -> None:
    cs_eval.set_terms([t.name for t in cs_terms.TERMS])
    try:
        for board in [chess.Board(f) for f in FENS] + random_boards(100, 19):
            assert cs_eval.evaluate(board) == cs_eval.evaluate(board.mirror()), board.fen()
    finally:
        cs_eval.set_terms(())


def test_environment_list_and_flags_resolve_the_same_way(monkeypatch) -> None:
    monkeypatch.delenv("CS_EVAL_TERMS", raising=False)
    for term in cs_terms.TERMS:
        monkeypatch.delenv(term.flag, raising=False)
    assert cs_terms.enabled_from_environment() == frozenset()
    monkeypatch.setenv("CS_EVAL_PASSED", "1")
    assert cs_terms.enabled_from_environment() == frozenset({"passed"})
    monkeypatch.setenv("CS_EVAL_TERMS", "mopup, king_safety")
    assert cs_terms.enabled_from_environment() == frozenset({"passed", "mopup", "king_safety"})
    monkeypatch.setenv("CS_EVAL_TERMS", "nonsense")
    with pytest.raises(ValueError):
        cs_terms.enabled_from_environment()


def test_set_term_rejects_unknown_names() -> None:
    with pytest.raises(ValueError):
        cs_eval.set_term("not_a_term", True)


def test_mirrors_follow_the_active_set() -> None:
    cs_eval.set_term("mopup", True)
    assert cs_eval.USE_MOP_UP is True and cs_eval.USE_PASSED is False
    cs_eval.set_term("mopup", False)
    assert cs_eval.USE_MOP_UP is False
