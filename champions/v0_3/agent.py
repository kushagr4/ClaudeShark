"""ClaudeShark -- AI Chessathon submission entry point.

The platform imports this module once (inside the 60 s initialisation budget)
and then calls :func:`get_move` for every one of our turns. The process stays
alive between calls, so the transposition table, the killer/history tables and
the inferred increment all persist across the game.

Everything below the entry point lives in the ``cs_*`` modules. They are kept at
the repository root on purpose: the official packager zips ``*.py`` from the
root, so a flat layout is packaged correctly with no extra flags, and the
``cs_`` prefix guarantees nothing shadows a standard-library module when the
submission directory is placed first on ``sys.path``.
"""

from __future__ import annotations

import sys

import chess

from cs_search import Searcher

sys.setrecursionlimit(10_000)

_searcher = Searcher()

# The platform starts a fresh process for every game, so in competition this
# never fires on anything but the first move. It is kept because the same module
# is reused across positions by the local tests and tools, where stale
# repetition history would otherwise leak from one position into the next.
# A clock that jumps up by more than the increment cannot be the same game.
_NEW_GAME_JUMP_MS = 5_000
_last_time_left: int | None = None


def get_move(fen: str, time_left_ms: int) -> str:
    """Return a legal move in UCI notation for ``fen``.

    Wrapped so that no failure inside the search can cost the game: a legal
    fallback move is picked before any search work begins and returned if
    anything at all goes wrong.
    """
    global _last_time_left

    board = chess.Board(fen)
    fallback = next(iter(board.legal_moves), None)
    if fallback is None:
        # No legal move exists; the referee will end the game on its own turn
        # check. Nothing legal can be returned, so return a null move.
        return "0000"

    if _last_time_left is None or time_left_ms > _last_time_left + _NEW_GAME_JUMP_MS:
        _searcher.new_game()
    _last_time_left = time_left_ms

    try:
        move, _ = _searcher.search(board, time_left_ms)
    except Exception:
        return fallback.uci()

    return (move or fallback).uci()


def _warm_up() -> None:
    """Touch every hot path once during the initialisation budget.

    python-chess builds its attack tables at import, and CPython has to create
    the code objects and inline caches for the search on first execution. Doing
    that here keeps it off the game clock.
    """
    warm = Searcher(tt_bits=12)
    for fen, budget in (
        (chess.STARTING_FEN, 3_000),
        ("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4", 3_000),
        ("8/2k5/8/8/3P4/8/5K2/8 w - - 0 1", 2_000),  # pawn ending, exercises the taper
        ("4k3/8/8/8/8/8/4P3/4K2R w K - 0 1", 2_000),  # castling and promotion paths
    ):
        warm.search(chess.Board(fen), budget)


_warm_up()
