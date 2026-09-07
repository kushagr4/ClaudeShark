"""Iterative deepening may only stop on a mate it could have proved.

RC-F left the root loop as soon as the score fell in the mate range, however
shallow the completed iteration. Those scores arrive from the transposition
table, built by earlier and deeper searches of other roots, so the engine could
play a mate in thirteen at completed depth one while it already held a mate in
eleven, with no search able to notice the regression. In round 54 that produced
a threefold draw in king and rook against a bare king.

These tests hold the new rule, and hold the mate-distance encoding that the rule
depends on.
"""

from __future__ import annotations

import chess
import numpy as np
import pytest

import cs_core as core
import cs_fast

# Every distance below was verified with Stockfish at three million nodes, not
# assumed: (fen, moves to mate for the side to move).
MATE_SUITE = [
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", 1),
    ("7k/8/6K1/8/8/8/8/1R6 w - - 0 1", 1),
    ("5k2/8/5K2/8/8/8/8/7Q w - - 0 1", 1),
    ("7k/8/5K2/8/8/8/8/R7 w - - 0 1", 2),
    ("3k4/8/3K4/8/8/8/8/4R3 w - - 0 1", 2),
    ("4k3/8/4K3/8/8/8/8/3Q4 w - - 0 1", 2),
    ("8/8/8/5k2/8/5K2/8/3Q4 w - - 0 1", 4),
    ("8/6k1/8/5K2/8/8/8/3R4 w - - 0 1", 5),
    ("8/8/6k1/8/6K1/8/8/2R5 w - - 0 1", 6),
    ("8/8/8/4k3/8/4K3/8/2Q5 w - - 0 1", 6),
    ("8/8/8/8/4k3/8/4K3/5Q2 w - - 0 1", 7),
]
# The side to move is the one being mated, in nine plies.
BEING_MATED = "8/8/8/8/8/1k6/8/K1R5 b - - 0 1"


@pytest.fixture(scope="module")
def searcher():
    return cs_fast.Searcher()


def mate_plies(score: int) -> int | None:
    if score > core.MATE_BOUND:
        return core.MATE_SCORE - score
    if score < -core.MATE_BOUND:
        return core.MATE_SCORE + score
    return None


# ------------------------------------------------------- mate-distance encoding


def test_mate_score_normalisation_round_trips_at_every_ply():
    for ply in range(0, 64):
        for score in (core.MATE_SCORE - 1, core.MATE_SCORE - 13, core.MATE_SCORE - 63,
                      -core.MATE_SCORE + 1, -core.MATE_SCORE + 13, -core.MATE_SCORE + 63,
                      0, 250, -250, core.MATE_BOUND, -core.MATE_BOUND):
            assert core.score_from_tt(core.score_to_tt(score, ply), ply) == score


def test_mate_distance_is_preserved_across_a_change_of_ply():
    """A mate stored deep in one search must read back correctly at another ply."""
    for stored_ply in range(0, 20):
        for read_ply in range(0, 20):
            score = core.MATE_SCORE - 9          # mate in nine plies from the root
            raw = core.score_to_tt(score, stored_ply)
            back = core.score_from_tt(raw, read_ply)
            # distance from the node is invariant; distance from the root shifts
            # by exactly the difference in ply
            assert back == score + stored_ply - read_ply


@pytest.mark.parametrize("bound", [core.BOUND_EXACT, core.BOUND_LOWER, core.BOUND_UPPER])
def test_table_round_trips_mate_scores_for_every_bound(bound):
    TK = np.zeros(1 << core.TT_BITS, dtype=np.int64)
    TV = np.zeros(1 << core.TT_BITS, dtype=np.int64)
    for ply in (0, 1, 5, 17):
        for score in (core.MATE_SCORE - 1, core.MATE_SCORE - 21,
                      -core.MATE_SCORE + 1, -core.MATE_SCORE + 21):
            key = (score * 7919 + ply * 104729 + bound) & ((1 << 62) - 1)
            core.tt_store(TK, TV, key, 9, core.score_to_tt(score, ply), bound, 1234)
            entry = core.tt_probe(TK, TV, key)
            assert entry >= 0
            assert core.tt_bound(entry) == bound
            assert core.score_from_tt(core.tt_score(entry), ply) == score


# ------------------------------------------------------------- the new rule


@pytest.mark.parametrize(("fen", "moves"), MATE_SUITE)
def test_known_mates_are_found_with_the_right_distance(searcher, fen, moves):
    searcher.new_game()
    move, info = searcher.search(chess.Board(fen), 0, max_depth=2 * moves + 4)
    assert move is not None
    assert info.score > core.MATE_BOUND, (fen, info.score)
    assert mate_plies(info.score) == 2 * moves - 1, (fen, info.score)


@pytest.mark.parametrize(("fen", "moves"), MATE_SUITE)
def test_a_claimed_mate_never_outruns_the_completed_depth(searcher, fen, moves):
    """The rule itself: an early stop implies the depth could prove the mate."""
    limit = 2 * moves + 6
    searcher.new_game()
    _, info = searcher.search(chess.Board(fen), 0, max_depth=limit)
    plies = mate_plies(info.score)
    if plies is not None and info.depth < limit:
        # the loop stopped before its depth limit, so it stopped on the mate
        assert plies <= info.depth, (fen, plies, info.depth)


def test_a_stale_deep_mate_entry_does_not_end_a_shallow_search(searcher):
    """The exact defect: a table mate from an earlier search, read at depth one.

    The first search fills the table from a position that mates quickly. The
    second search starts from the parent, where the same table entry is one ply
    away. RC-F stopped at depth one on that entry; the rule now requires the
    completed depth to cover the distance being claimed.
    """
    child = chess.Board("7k/8/6K1/8/8/8/8/3R4 w - - 0 1")
    searcher.new_game()
    _, deep = searcher.search(child, 0, max_depth=8)
    assert deep.score > core.MATE_BOUND

    parent = chess.Board("7k/8/8/6K1/8/8/8/3R4 w - - 0 1")
    assert parent.is_valid()
    _, info = searcher.search(parent, 0, max_depth=12)
    plies = mate_plies(info.score)
    if plies is not None and info.depth < 12:
        assert plies <= info.depth, (plies, info.depth)


def test_mate_in_one_still_ends_the_search_immediately(searcher):
    """Legitimate early exits are preserved: depth one proves a mate in one."""
    searcher.new_game()
    move, info = searcher.search(chess.Board("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"),
                                 0, max_depth=20)
    assert move.uci() == "a1a8"
    assert info.score == core.MATE_SCORE - 1
    assert info.depth == 1, "a proved mate in one must still stop at depth one"


def test_being_mated_is_also_held_to_the_rule(searcher):
    """The rule is symmetric: a losing mate score gets the same treatment."""
    searcher.new_game()
    board = chess.Board(BEING_MATED)
    assert board.is_valid()
    _, info = searcher.search(board, 0, max_depth=10)
    plies = mate_plies(info.score)
    if plies is not None and info.depth < 10:
        assert plies <= info.depth, (plies, info.depth)
