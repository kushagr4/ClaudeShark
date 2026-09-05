"""Null-move pruning must not chain nulls.

A null-move search is given a null window, which is exactly the condition
null-move pruning tests for, so without a guard the child passes again
immediately. Two nulls in a row means neither side has moved: the resulting
score says nothing about the position and the subtree is wasted.

Measured before the fix, searching three positions to depth 10: **1125** lines
containing consecutive nulls. An earlier depth-7 probe found none, which is why
this test searches deep enough to matter -- a second null needs a non-PV node at
depth >= 6, since the first reduces the child by three or four plies.
"""

from __future__ import annotations

import chess
import pytest

import cs_search
from cs_search import Searcher

NULL = chess.Move.null()

POSITIONS = (
    "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 9",
    "r2q1rk1/1b1nbppp/p2ppn2/1p6/3NPP2/1BN1B3/PPPQ2PP/2KR3R w - - 0 13",
)


def _consecutive_null_lines(fen: str, depth: int) -> list[list[str]]:
    """Search, recording any line where two nulls are played back to back."""
    searcher = Searcher(tt_bits=18)
    original = searcher._negamax
    found: list[list[str]] = []

    def traced(board, d, alpha, beta, ply, allow_null=True):  # type: ignore[no-untyped-def]
        stack = board.move_stack
        if len(stack) >= 2 and stack[-1] == NULL and stack[-2] == NULL:
            found.append([m.uci() for m in stack])
        return original(board, d, alpha, beta, ply, allow_null)

    searcher._negamax = traced  # type: ignore[method-assign]
    searcher.search(chess.Board(fen), 0, max_depth=depth)
    return found


@pytest.mark.parametrize("fen", POSITIONS)
def test_no_consecutive_null_moves(fen: str) -> None:
    found = _consecutive_null_lines(fen, depth=9)
    assert not found, f"{len(found)} lines with back-to-back nulls, e.g. {found[0]}"


def test_null_move_still_fires() -> None:
    """The guard must block chaining, not disable null-move pruning entirely."""
    searcher = Searcher(tt_bits=18)
    original = searcher._negamax
    nulls = 0

    def traced(board, d, alpha, beta, ply, allow_null=True):  # type: ignore[no-untyped-def]
        nonlocal nulls
        stack = board.move_stack
        if stack and stack[-1] == NULL:
            nulls += 1
        return original(board, d, alpha, beta, ply, allow_null)

    searcher._negamax = traced  # type: ignore[method-assign]
    searcher.search(chess.Board(POSITIONS[0]), 0, max_depth=7)
    assert nulls > 0, "null-move pruning stopped firing altogether"


def test_allow_null_blocks_this_node_only() -> None:
    """A node told not to null must not null *itself*.

    The guard is deliberately narrow: it stops the immediate child of a null
    search from nulling again. Descendants reached through real moves may null,
    which is correct -- the defect was two nulls in a row, not two nulls in a
    line. So the assertion is about a null played directly from this node, not
    about nulls anywhere beneath it.
    """
    searcher = Searcher(tt_bits=16)
    original = searcher._negamax
    stacks: list[list[chess.Move]] = []

    def traced(board, d, alpha, beta, ply, allow_null=True):  # type: ignore[no-untyped-def]
        stacks.append(list(board.move_stack))
        return original(board, d, alpha, beta, ply, allow_null)

    searcher._negamax = traced  # type: ignore[method-assign]
    board = chess.Board(POSITIONS[0])
    searcher.time.begin_fixed(5_000.0)
    searcher._path[0] = hash(board._transposition_key())
    traced(board, 8, -1, 0, 1, False)

    # A null played directly from the node under test would appear as a child
    # whose entire move stack is a single null move.
    assert [NULL] not in stacks, "nulled despite allow_null=False"


def test_disabling_null_move_entirely_still_searches() -> None:
    saved = cs_search.USE_NULL_MOVE
    try:
        cs_search.USE_NULL_MOVE = False
        move, _ = Searcher(tt_bits=16).search(chess.Board(POSITIONS[0]), 0, max_depth=5)
        assert move is not None
    finally:
        cs_search.USE_NULL_MOVE = saved
