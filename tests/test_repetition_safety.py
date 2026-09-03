"""Repetition safety: the properties any change to draw handling must keep.

The 2026-09-03 repetition audit examined 127 repetition draws and found the
current heuristic sound: relaxing it made the engine repeat *more*, and in no
case did a relaxed policy avoid a repetition the current one took while
winning. Production was therefore left alone.

That makes these tests regression protection rather than a specification of
something new. They pin the behaviour that made the audit come out the way it
did, so the next attempt to touch repetition handling has to confront them.

The central property is that **no draw contempt term is needed**. Scoring a
repetition as `DRAW_SCORE` (zero) is automatically correct from both sides,
because alpha-beta compares it against the position's real score: zero is
worse than a winning score, so a winning engine avoids the repetition, and
better than a losing score, so a losing engine steers into it. The two
synthetic tests below are the same rook endgame from either side, and they show
exactly that asymmetry falling out of one unsigned constant.

Positions marked "audited" are real decisions taken from the fixed-depth
diagnostic set; see `benchmarks/current/2026-09-03-repetition-audit.md`.
"""

from __future__ import annotations

import chess

from cs_constants import MATE_SCORE
from cs_search import Searcher, rules_outcome

# The same rook endgame from either side: White is winning, Black is lost.
WON_FOR_WHITE = "6k1/8/8/8/8/8/8/R5K1 w - - 0 1"
LOST_FOR_BLACK = "6k1/8/8/8/8/8/8/R5K1 b - - 0 1"

# audited: cluster 10, Black is -316 by Stockfish and holds with perpetual check.
PERPETUAL_WHEN_LOSING = "6k1/6pp/1p1p1p2/1P1P1P2/2P1K3/R7/7P/5r2 b - - 9 46"
# audited: cluster 11, a genuinely equal queen endgame that repeated.
EQUAL_AND_REPEATING = "8/6k1/1Pq2p1p/p7/8/5K2/6P1/1Q6 w - - 17 52"


def searched(fen: str, seen: list[str] | None = None, depth: int = 6):
    """Search `fen` with `seen` child positions already recorded for the game."""
    searcher = Searcher()
    searcher.new_game()
    for uci in seen or []:
        board = chess.Board(fen)
        board.push_uci(uci)
        key = hash(board._transposition_key())
        searcher._game_counts[key] = searcher._game_counts.get(key, 0) + 1
    move, info = searcher.search(chess.Board(fen), 60_000, max_depth=depth)
    assert move is not None
    return move.uci(), info


def test_the_losing_side_takes_a_repetition_draw() -> None:
    """Zero beats being a rook down, so the repetition is chosen."""
    plain, plain_info = searched(LOST_FOR_BLACK)
    assert plain_info.score < -300, "the position should look lost without the draw"

    repeat, repeat_info = searched(LOST_FOR_BLACK, seen=[plain])
    assert repeat == plain, "the drawing move is still the one it wants"
    assert repeat_info.score == 0, "and it is now scored as the draw it is"


def test_the_winning_side_declines_a_repetition_draw() -> None:
    """Zero is worse than winning, so the repetition is avoided -- no contempt term."""
    plain, plain_info = searched(WON_FOR_WHITE)
    assert plain_info.score > 300

    avoid, avoid_info = searched(WON_FOR_WHITE, seen=[plain])
    assert avoid != plain, "it must not walk into the repetition while winning"
    assert avoid_info.score > 300, "and it must still be winning after avoiding it"


def test_a_forced_perpetual_is_accepted_when_losing() -> None:
    """audited: Stockfish says -316 for Black; the engine holds with checks."""
    move, info = searched(PERPETUAL_WHEN_LOSING)
    board = chess.Board(PERPETUAL_WHEN_LOSING)
    board.push_uci(move)
    assert board.is_check(), "the holding resource here is a check"
    assert info.score > -200, "the engine should not think it is simply lost"

    repeat, repeat_info = searched(PERPETUAL_WHEN_LOSING, seen=[move])
    assert repeat == move
    assert repeat_info.score == 0


def test_a_genuinely_equal_repeated_position_scores_as_a_draw() -> None:
    """audited: an equal queen endgame. Repeating here is correct chess."""
    _, info = searched(EQUAL_AND_REPEATING)
    assert abs(info.score) < 150


def test_the_search_terminates_when_every_move_only_shuffles() -> None:
    """The path scan, not the game record, is what stops a cycle searching forever."""
    _, info = searched("4k3/8/8/8/8/8/8/4K3 w - - 0 1", depth=8)
    assert info.nodes < 500_000
    assert info.depth == 8


def test_a_claimable_fifty_move_draw_scores_zero_inside_the_search() -> None:
    """The rule the referee will claim, applied by the one shared policy function.

    Asserted on `rules_outcome` rather than on a root search: at the root the
    referee has already ended the game, so the root score is moot. What matters
    is that a node *inside* the tree scores this as the draw it is, which is the
    regression the fifty-move repair was about.
    """
    board = chess.Board("q5k1/6R1/8/8/8/8/8/6K1 b - - 100 80")
    assert board.can_claim_fifty_moves()
    assert rules_outcome(board, board.is_check(), ply=4) == 0


def test_checkmate_still_outranks_a_claimable_fifty_move_draw() -> None:
    """The over-correction that scored a forced mate as 0 must stay fixed."""
    board = chess.Board("6Rk/6R1/8/8/8/8/8/6K1 b - - 100 80")
    assert board.is_checkmate()
    assert rules_outcome(board, in_check=True, ply=4) == -MATE_SCORE + 4


def test_a_recorded_repetition_does_not_leak_into_the_next_game() -> None:
    searcher = Searcher()
    searcher.new_game()
    board = chess.Board(WON_FOR_WHITE)
    board.push_uci("a1a7")
    searcher._game_counts[hash(board._transposition_key())] = 1
    searcher.new_game()
    assert searcher._game_counts == {}
    move, info = searcher.search(chess.Board(WON_FOR_WHITE), 60_000, max_depth=6)
    assert move is not None and info.score > 300


def test_the_repetition_record_survives_across_moves_of_one_game() -> None:
    """It is what lets the engine see a draw the referee would claim."""
    searcher = Searcher()
    searcher.new_game()
    first, _ = searcher.search(chess.Board(WON_FOR_WHITE), 60_000, max_depth=4)
    assert first is not None
    assert len(searcher._game_counts) == 1, "the root position was recorded"
    searcher.search(chess.Board(LOST_FOR_BLACK), 60_000, max_depth=4)
    assert len(searcher._game_counts) == 2


def test_repetition_scoring_does_not_corrupt_a_later_fresh_search() -> None:
    """A drawn score must not be written to the table under a plain position key."""
    searcher = Searcher()
    searcher.new_game()
    board = chess.Board(WON_FOR_WHITE)
    board.push_uci("a1a7")
    searcher._game_counts[hash(board._transposition_key())] = 1
    searcher.search(chess.Board(WON_FOR_WHITE), 60_000, max_depth=6)

    fresh = Searcher()
    fresh.new_game()
    move, info = fresh.search(board.copy(stack=False), 60_000, max_depth=6)
    assert move is not None
    assert info.score < -300, "Black is a rook down here and it is Black to move"
