"""Transposition cutoffs at PV nodes.

The defect these guard against was the worst tactical failure this project has
found. On

    1r4k1/5p1p/5PpQ/3Bp3/2Pb4/qP3R2/7P/7K b - - 0 1

Qf8 is the only move that holds. Stockfish 18 at 4M nodes: Qf8 -26 cp with a
WDL of 6/945/49, second best Qc1+ at -586, and Qa1+ -- which the engine played
at every depth from 6 to 10 -- at -962 with a WDL of 0/0/1000.

The cause was taking a cutoff on a LOWER or UPPER bound at a PV node. Each
aspiration re-search widened the root window, the Qf8 child failed high against
its own beta, a LOWER bound was stored at that value, and the next re-search
read it back and returned a larger number still: 7, 31, 100, 212, 464, 939. The
score chased the window upward until the only saving move looked like the worst.
EXACT entries in the same subtree were correct throughout.
"""

from __future__ import annotations

import chess
import pytest

import cs_search
from cs_constants import BOUND_EXACT, BOUND_LOWER, BOUND_UPPER, INFINITY
from cs_search import Searcher
from cs_tt import TranspositionTable

ONLY_MOVE_HOLDS = "1r4k1/5p1p/5PpQ/3Bp3/2Pb4/qP3R2/7P/7K b - - 0 1"
QF8 = "a3f8"


@pytest.fixture(autouse=True)
def _restore_policy():
    saved = cs_search.TT_PV_POLICY
    yield
    cs_search.TT_PV_POLICY = saved


def test_the_position_is_what_the_oracle_says_it_is() -> None:
    """Pin the fixture down before asserting engine behaviour on it."""
    board = chess.Board(ONLY_MOVE_HOLDS)
    assert board.is_valid()
    assert not board.is_check()
    assert chess.Move.from_uci(QF8) in board.legal_moves


@pytest.mark.parametrize("depth", [6, 8])
def test_the_only_defensive_move_is_found(depth: int) -> None:
    """The regression itself: shipping settings must play Qf8."""
    move, info = Searcher(tt_bits=18).search(chess.Board(ONLY_MOVE_HOLDS), 0, max_depth=depth)
    assert move is not None
    assert move.uci() == QF8, (
        f"depth {depth}: played {move.uci()} scoring {info.score}; "
        f"Qf8 is the only move that holds and everything else loses"
    )
    # A engine that finds Qf8 also stops believing it is nine pawns down.
    assert info.score > -300, f"scored {info.score}, expected roughly level"


def test_the_broken_policy_still_reproduces_the_failure() -> None:
    """Keep the defect demonstrable, so the fix cannot be quietly reverted.

    If this ever starts passing Qf8 under policy "all", the mechanism has
    changed and the rest of this file needs revisiting rather than deleting.
    """
    cs_search.TT_PV_POLICY = "all"
    move, info = Searcher(tt_bits=18).search(chess.Board(ONLY_MOVE_HOLDS), 0, max_depth=6)
    assert move is not None
    assert move.uci() != QF8, "policy 'all' unexpectedly found Qf8"
    assert info.score < -500, "policy 'all' unexpectedly avoided the huge score error"


@pytest.mark.parametrize("policy", ["exact", "none"])
def test_both_safe_policies_fix_it(policy: str) -> None:
    cs_search.TT_PV_POLICY = policy
    move, _ = Searcher(tt_bits=18).search(chess.Board(ONLY_MOVE_HOLDS), 0, max_depth=6)
    assert move is not None and move.uci() == QF8


def test_exact_is_the_shipping_default() -> None:
    """'exact' keeps proven scores and discards only unproven bounds."""
    assert cs_search.TT_PV_POLICY == "exact"


# --------------------------------------------------------------- the invariant


def _probe_returns(policy: str, bound: int, stored: int, alpha: int, beta: int) -> int | None:
    """Drive one TT probe through the search and report whether it cut.

    Builds a searcher whose table already holds a single entry for the root
    position, then searches that position at a depth the entry dominates.
    """
    cs_search.TT_PV_POLICY = policy
    fen = "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9"
    board = chess.Board(fen)
    searcher = Searcher(tt_bits=16)
    key = hash(board._transposition_key())
    searcher.tt.store(key, 20, stored, bound, chess.Move.from_uci("d3e2"))
    searcher.time.begin_fixed(5_000.0)
    searcher._path[0] = key
    return searcher._negamax(board, 4, alpha, beta, 1)


def test_non_pv_nodes_still_cut_on_every_bound() -> None:
    """The fix must not cost the table its value where bounds are actionable."""
    # Null window: beta - alpha == 1, so this is a non-PV node.
    assert _probe_returns("exact", BOUND_LOWER, stored=500, alpha=99, beta=100) == 500
    assert _probe_returns("exact", BOUND_UPPER, stored=-500, alpha=99, beta=100) == -500
    assert _probe_returns("exact", BOUND_EXACT, stored=42, alpha=99, beta=100) == 42


def test_pv_nodes_cut_only_on_exact_under_the_shipping_policy() -> None:
    """The invariant the fix establishes."""
    wide = {"alpha": -INFINITY, "beta": INFINITY}
    # EXACT still cuts and returns the stored score verbatim.
    assert _probe_returns("exact", BOUND_EXACT, stored=42, **wide) == 42
    # A LOWER bound big enough to beat any beta must NOT be returned.
    assert _probe_returns("exact", BOUND_LOWER, stored=9000, **wide) != 9000
    # Nor an UPPER bound below any alpha.
    assert _probe_returns("exact", BOUND_UPPER, stored=-9000, **wide) != -9000


def test_policy_all_does_cut_on_bounds_at_pv_nodes() -> None:
    """Characterise the old behaviour, so the difference is explicit."""
    assert _probe_returns("all", BOUND_LOWER, stored=9000, alpha=-INFINITY, beta=8000) == 9000


def test_policy_none_refuses_even_exact_at_pv_nodes() -> None:
    assert _probe_returns("none", BOUND_EXACT, stored=42, alpha=-INFINITY, beta=INFINITY) != 42
    # But non-PV nodes are untouched by the PV policy.
    assert _probe_returns("none", BOUND_EXACT, stored=42, alpha=99, beta=100) == 42


def test_an_unknown_policy_is_rejected_loudly() -> None:
    """A typo must not silently fall back to the broken behaviour."""
    import os

    saved = os.environ.get("CS_TT_PV_POLICY")
    try:
        os.environ["CS_TT_PV_POLICY"] = "exactt"
        with pytest.raises(ValueError, match="CS_TT_PV_POLICY"):
            cs_search._policy("CS_TT_PV_POLICY", "exact", ("all", "exact", "none"))
    finally:
        if saved is None:
            os.environ.pop("CS_TT_PV_POLICY", None)
        else:
            os.environ["CS_TT_PV_POLICY"] = saved


def test_table_still_stores_and_returns_exact_scores() -> None:
    """Sanity: the table itself is unchanged by this policy."""
    table = TranspositionTable(bits=8)
    move = chess.Move.from_uci("e2e4")
    table.store(1234, 5, 77, BOUND_EXACT, move)
    entry = table.probe(1234)
    assert entry is not None and entry[2] == 77 and entry[4] == move
