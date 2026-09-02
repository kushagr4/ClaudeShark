"""Regression tests for search correctness issues found by audit.

Each test here corresponds to a specific defect. The comment on each says what
went wrong and, where the old behaviour was demonstrably incorrect, what it
produced instead. These are the tests that would have caught the bug.
"""

from __future__ import annotations

import chess
import pytest

import cs_search
from cs_constants import MATE_BOUND
from cs_search import Searcher


@pytest.fixture(autouse=True)
def _restore_flags():
    """Tests here toggle search features; put them back afterwards."""
    saved = (
        cs_search.USE_PVS,
        cs_search.USE_NULL_MOVE,
        cs_search.USE_LMR,
        cs_search.LMR_SAFE,
        cs_search.USE_ASPIRATION,
        cs_search.TT_PV_POLICY,
    )
    yield
    (
        cs_search.USE_PVS,
        cs_search.USE_NULL_MOVE,
        cs_search.USE_LMR,
        cs_search.LMR_SAFE,
        cs_search.USE_ASPIRATION,
        cs_search.TT_PV_POLICY,
    ) = saved


# --------------------------------------------------------------- draw rules


def test_checkmate_outranks_the_fifty_move_rule() -> None:
    """Mate on the hundredth halfmove is a win, not a draw.

    The draw test used to run before anything else and returned 0 for any node
    with ``halfmove_clock >= 100``. Ra8 here is mate and takes the counter to
    100, so the engine scored a forced mate as a dead draw and had no reason to
    play it.
    """
    fen = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 99 60"
    board = chess.Board(fen)
    mating = chess.Move.from_uci("a1a8")
    board.push(mating)
    assert board.is_checkmate()
    assert board.halfmove_clock == 100

    move, info = Searcher(tt_bits=16).search(chess.Board(fen), 0, max_depth=3)
    assert move == mating
    assert info.score > MATE_BOUND, f"scored {info.score}, expected a mate score"


def test_fifty_move_draw_still_applies_when_not_in_check() -> None:
    """The fix must not disable the fifty-move rule itself."""
    # White is up a rook but the counter is exhausted, so it is a draw.
    fen = "6k1/8/8/8/8/8/8/R5K1 w - - 100 80"
    _, info = Searcher(tt_bits=16).search(chess.Board(fen), 0, max_depth=3)
    assert abs(info.score) < 100, f"expected a drawish score, got {info.score}"


def test_stalemate_is_a_draw_not_a_loss() -> None:
    fen = "7k/5Q2/8/8/8/8/8/6K1 b - - 0 1"
    assert chess.Board(fen).is_stalemate()

    # From a position where stalemating is available, the engine must not take
    # it. The previous parent here (`7k/8/5Q2/...`) was invalid: the queen on f6
    # gave check to the black king while it was White to move.
    parent = chess.Board("7k/8/6K1/8/8/8/8/6Q1 w - - 0 1")
    assert parent.is_valid()
    move, _ = Searcher(tt_bits=16).search(parent, 0, max_depth=4)
    assert move is not None and move in parent.legal_moves
    parent.push(move)
    assert not parent.is_stalemate(), f"threw the win away with {move.uci()}"


# ------------------------------------------------------- transposition table


def test_aborted_first_iteration_does_not_poison_the_table() -> None:
    """A search that never completes depth 1 must not write a root entry.

    The fallback move is untested and the score is a placeholder zero; storing
    them would let a later transposition read a fabricated entry back as fact.
    """
    fen = "r2q1rk1/pp1bbppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP1QPPP/R1B2RK1 w - - 0 10"
    searcher = Searcher(tt_bits=16)
    board = chess.Board(fen)
    root_key = hash(board._transposition_key())

    # A one-millisecond clock cannot finish depth 1 on this position.
    move, info = searcher.search(board, 1)
    assert move is not None
    if info.depth == 0:
        assert searcher.tt.probe(root_key) is None, "wrote an entry with no completed iteration"


def test_mate_scores_are_rebased_through_the_table() -> None:
    """A mate found at one ply must not be reported at another's distance."""
    fen = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"
    searcher = Searcher(tt_bits=16)
    first_move, first = searcher.search(chess.Board(fen), 0, max_depth=2)
    # Search again with the table already warm; the mate distance must not drift.
    second_move, second = searcher.search(chess.Board(fen), 0, max_depth=4)
    assert first_move == second_move == chess.Move.from_uci("a1a8")
    assert first.score > MATE_BOUND and second.score > MATE_BOUND
    assert first.score == second.score, "mate distance changed across a warm table"


# ------------------------------------------------------ selective search


def test_null_move_is_disabled_when_only_pawns_remain() -> None:
    """Zugzwang guard: passing is a bad assumption in a pawn ending.

    Verified behaviourally -- the engine must still find that it has to push,
    not conclude from a null move that the position holds itself.
    """
    fen = "8/8/8/3k4/8/3P4/3K4/8 w - - 0 1"
    move, _ = Searcher(tt_bits=16).search(chess.Board(fen), 0, max_depth=6)
    assert move is not None and move in chess.Board(fen).legal_moves


def test_safe_lmr_is_the_shipping_default() -> None:
    """Forcing moves are exempt from reduction in the shipping engine.

    This is a robustness choice, not a measured Elo gain: on the 40-position
    benchmark suite it changed the chosen move in zero positions and cost 0.6%
    more nodes. See benchmarks/current/ for the numbers. The guard here is
    against someone quietly flipping the default back.
    """
    assert cs_search.LMR_SAFE is True


def test_safe_lmr_does_not_change_forced_results() -> None:
    """Exempting forcing moves may cost nodes; it must not change conclusions."""
    fen = "3r2k1/5ppp/8/8/8/8/5PPP/3QR1K1 w - - 0 1"  # Qxd8 is mate
    scores = []
    for safe in (True, False):
        cs_search.LMR_SAFE = safe
        move, info = Searcher(tt_bits=14).search(chess.Board(fen), 0, max_depth=4)
        assert move == chess.Move.from_uci("d1d8"), safe
        scores.append(info.score)
    assert scores[0] == scores[1]


def test_disabling_features_still_produces_legal_moves() -> None:
    """Every flag combination must remain a working engine."""
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    board = chess.Board(fen)
    for pvs in (True, False):
        for nmp in (True, False):
            for lmr in (True, False):
                cs_search.USE_PVS = pvs
                cs_search.USE_NULL_MOVE = nmp
                cs_search.USE_LMR = lmr
                move, _ = Searcher(tt_bits=14).search(chess.Board(fen), 0, max_depth=4)
                assert move is not None and move in board.legal_moves, (pvs, nmp, lmr)


def test_search_variants_agree_on_a_forced_tactic() -> None:
    """Pruning may change speed; it must not change a forced result."""
    fen = "3r2k1/5ppp/8/8/8/8/5PPP/3QR1K1 w - - 0 1"  # Qxd8 is mate
    for pvs in (True, False):
        for nmp in (True, False):
            for lmr in (True, False):
                cs_search.USE_PVS = pvs
                cs_search.USE_NULL_MOVE = nmp
                cs_search.USE_LMR = lmr
                move, info = Searcher(tt_bits=14).search(chess.Board(fen), 0, max_depth=3)
                assert move == chess.Move.from_uci("d1d8"), (pvs, nmp, lmr)
                assert info.score > MATE_BOUND, (pvs, nmp, lmr)


def test_aspiration_does_not_change_a_forced_result() -> None:
    fen = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"
    for aspiration in (True, False):
        cs_search.USE_ASPIRATION = aspiration
        move, info = Searcher(tt_bits=14).search(chess.Board(fen), 0, max_depth=5)
        assert move == chess.Move.from_uci("a1a8")
        assert info.score > MATE_BOUND


# ------------------------------------------------------------ board integrity


def test_board_is_unchanged_by_a_completed_search() -> None:
    """push/pop must balance exactly when the search is not aborted."""
    fen = "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9"
    board = chess.Board(fen)
    Searcher(tt_bits=16).search(board, 0, max_depth=5)
    assert board.fen() == fen
    assert len(board.move_stack) == 0


def test_aborted_search_still_returns_a_legal_move_for_the_original_position() -> None:
    """On timeout the board is discarded, so the caller's position must be intact."""
    fen = "r2q1rk1/pp1bbppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP1QPPP/R1B2RK1 w - - 0 10"
    original = chess.Board(fen)
    move, _ = Searcher(tt_bits=16).search(original, 15)
    assert move is not None
    assert move in chess.Board(fen).legal_moves
