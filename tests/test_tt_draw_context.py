"""Transposition-table draw-context regression tests.

The key describes placement, side to move, castling rights and en passant. It
does **not** describe the fifty-move counter, so a position at clock 5 and the
same position at clock 96 share an entry while having genuinely different
scores -- one of them is about to be drawn by rule.

This was demonstrated rather than assumed: searching a won rook endgame at
clock 96 and then the same position at clock 0 through one table returned 0
instead of +542.
"""

from __future__ import annotations

import chess

from cs_search import TT_HALFMOVE_LIMIT, Searcher

WON_ROOK_ENDGAME = "8/8/6k1/8/8/6K1/8/R7 w - - {clock} {move}"


def test_the_key_really_does_ignore_the_fifty_move_counter() -> None:
    """State the underlying fact the fix works around."""
    low = chess.Board(WON_ROOK_ENDGAME.format(clock=0, move=1))
    high = chess.Board(WON_ROOK_ENDGAME.format(clock=96, move=90))
    assert low._transposition_key() == high._transposition_key()
    assert hash(low._transposition_key()) == hash(high._transposition_key())


def test_a_near_fifty_move_search_does_not_poison_a_fresh_position() -> None:
    """The reproduction, as a regression test.

    Search the near-drawn version first so its scores would populate the table,
    then the fresh version through the same searcher. It must match what a
    clean table produces.
    """
    stale = WON_ROOK_ENDGAME.format(clock=96, move=90)
    fresh = WON_ROOK_ENDGAME.format(clock=0, move=1)

    shared = Searcher(tt_bits=16)
    shared.search(chess.Board(stale), 0, max_depth=6)
    _, contaminated = shared.search(chess.Board(fresh), 0, max_depth=6)

    clean = Searcher(tt_bits=16)
    _, reference = clean.search(chess.Board(fresh), 0, max_depth=6)

    assert contaminated.score == reference.score, (
        f"table poisoned by the near-fifty-move search: "
        f"{contaminated.score} via a shared table vs {reference.score} clean"
    )
    assert reference.score > 300, "fixture should be a winning rook endgame"


def test_a_high_clock_position_is_still_scored_as_drawish() -> None:
    """Bypassing the table must not make the fifty-move rule invisible."""
    stale = WON_ROOK_ENDGAME.format(clock=96, move=90)
    _, info = Searcher(tt_bits=16).search(chess.Board(stale), 0, max_depth=6)
    assert abs(info.score) < 100, f"expected a drawish score near the limit, got {info.score}"


def test_limit_leaves_a_real_margin() -> None:
    """The bypass only helps if it triggers before the rule can reach a leaf."""
    assert TT_HALFMOVE_LIMIT <= 80
    assert 100 - TT_HALFMOVE_LIMIT >= 20


def test_ordinary_positions_still_use_the_table() -> None:
    """The bypass must be rare, or it would cost most of the table's value."""
    searcher = Searcher(tt_bits=16)
    searcher.search(chess.Board(), 0, max_depth=6)
    assert searcher.tt.hits > 0, "the table stopped being used at all"
