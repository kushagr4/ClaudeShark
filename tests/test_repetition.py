"""What the repetition handling actually does.

These tests document behaviour rather than assert a rule, because the mechanism
is deliberately **not** the FIDE rule and the code used to describe itself as
though it were.

FIDE draws on the *third* occurrence of a position. This engine scores a
position as a draw on its *second* -- once it reappears on the current search
line, or once it reappears having already occurred in the game. That is the
common engine convention: if a position can be reached twice, the side that
wants the draw can usually force the third, so treating the second as drawn is
a good approximation and it stops the search wasting effort on cycles.

It is an approximation, and the failure mode is real: a winning line whose only
path revisits an earlier position is scored 0 and avoided. Two things bound the
damage. The engine only records positions it was *asked about*, which is every
other ply, so most repetitions are never seen at all. And the alternative --
tracking true threefold counts through the search — costs more than the rare
mistake, on the evidence available.

Recorded here so the behaviour is a documented choice rather than an accident.
"""

from __future__ import annotations

import chess

from cs_constants import INFINITY
from cs_search import Searcher

WON_ROOK_ENDGAME = "6k1/8/8/8/8/8/8/R5K1 w - - 0 1"


def test_a_position_the_game_has_visited_scores_as_a_draw_in_search() -> None:
    """Second occurrence, not third. This is the heuristic, stated plainly."""
    searcher = Searcher(tt_bits=16)
    # Searching a position records it as one the game has visited.
    _, info = searcher.search(chess.Board(WON_ROOK_ENDGAME), 0, max_depth=4)
    assert info.score > 300, "fixture should be winning for white"
    assert len(searcher._game_counts) == 1

    # Reaching that same position again *inside* a later search scores 0, even
    # though FIDE would need a third occurrence before anyone could claim.
    board = chess.Board(WON_ROOK_ENDGAME)
    score = searcher._negamax(board, 3, -INFINITY, INFINITY, 1)
    assert score == 0, f"expected the heuristic draw score, got {score}"


def test_a_fresh_searcher_does_not_see_a_repetition() -> None:
    """The record is per-game state, not a property of the position."""
    searcher = Searcher(tt_bits=16)
    board = chess.Board(WON_ROOK_ENDGAME)
    score = searcher._negamax(board, 3, -INFINITY, INFINITY, 1)
    assert score > 300, "an unvisited position must be scored on its merits"


def test_new_game_clears_the_visited_record() -> None:
    searcher = Searcher(tt_bits=16)
    searcher.search(chess.Board(WON_ROOK_ENDGAME), 0, max_depth=3)
    assert searcher._game_counts
    searcher.new_game()
    assert not searcher._game_counts

    board = chess.Board(WON_ROOK_ENDGAME)
    assert searcher._negamax(board, 3, -INFINITY, INFINITY, 1) > 300


def test_repetition_on_the_current_line_is_also_a_draw() -> None:
    """A position repeating within one search line scores 0 at the second visit.

    The halfmove clock has to be non-zero for this to be reachable at all: the
    scan is bounded by it, because a repetition cannot span an irreversible
    move. With a clock of 0 the scan is correctly skipped entirely.
    """
    reversible = "6k1/8/8/8/8/8/8/R5K1 w - - 10 20"
    searcher = Searcher(tt_bits=16)
    board = chess.Board(reversible)
    key = hash(board._transposition_key())
    # Pretend ply 1 already stood on this position; ply 3 should then see it.
    searcher._path[1] = key
    score = searcher._negamax(board, 2, -INFINITY, INFINITY, 3)
    assert score == 0


def test_the_path_scan_is_bounded_by_the_halfmove_clock() -> None:
    """No repetition can span an irreversible move, so the scan stops there."""
    fresh = "6k1/8/8/8/8/8/8/R5K1 w - - 0 1"
    searcher = Searcher(tt_bits=16)
    board = chess.Board(fresh)
    searcher._path[1] = hash(board._transposition_key())
    # Clock 0 means the scan never looks back, so this is scored on its merits.
    assert searcher._negamax(board, 2, -INFINITY, INFINITY, 3) > 300


def test_the_engine_still_wins_a_won_endgame_it_has_seen_before() -> None:
    """The bound on the damage: seeing a position once does not lose the game.

    The heuristic makes the engine avoid *returning* to a visited position, not
    avoid winning. From the same position it should still find a rook move that
    makes progress rather than shuffling into the scored-zero repeat.
    """
    searcher = Searcher(tt_bits=16)
    searcher.search(chess.Board(WON_ROOK_ENDGAME), 0, max_depth=4)
    move, info = searcher.search(chess.Board(WON_ROOK_ENDGAME), 0, max_depth=5)
    assert move is not None
    assert move in chess.Board(WON_ROOK_ENDGAME).legal_moves
    assert info.score > 300, f"visited position must still score as won, got {info.score}"
