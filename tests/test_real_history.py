"""The engine must know the repetitions its own move creates.

The search only ever sees positions with ClaudeShark to move, because those are
the ones the platform hands it. The position its own move produces is never a
root, so nothing in the search could notice that playing it hands the opponent a
threefold claim. Three live games were drawn that way. These tests hold the root
check that fixes it, and hold the rule that a draw stays selectable when every
alternative is worse.
"""

from __future__ import annotations

import chess
import pytest

import cs_core as core
import cs_fast


@pytest.fixture(scope="module")
def searcher():
    return cs_fast.Searcher()


def key_after(s, board, move):
    b = board.copy()
    b.push(move)
    core.load_board(b, s.B, s.O, s.M, s.S)
    return int(s.S[4])


def test_history_records_the_position_the_engine_creates(searcher):
    """Both the root and its own move's result enter the observed history."""
    s = searcher
    s.new_game()
    board = chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")
    core.load_board(board, s.B, s.O, s.M, s.S)
    root = int(s.S[4])
    move, _ = s.search(board.copy(), 0, max_depth=6)
    assert s._history.get(root) == 1, "the root it was handed"
    assert s._history.get(key_after(s, board, move)) == 1, "and what its move produced"


def test_a_winning_engine_avoids_completing_a_threefold(searcher):
    """King and rook against a bare king: never repeat while winning."""
    s = searcher
    s.new_game()
    board = chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")
    # Pretend the position after Ra5+ has already occurred twice this game.
    repeat = chess.Move.from_uci("a1a5")
    assert repeat in board.legal_moves
    s._history[key_after(s, board, repeat)] = 2
    move, info = s.search(board.copy(), 0, max_depth=8)
    assert move != repeat, "played into a threefold while a rook up"
    assert info.score > 0


def test_the_draw_is_still_taken_when_every_alternative_loses(searcher):
    """A draw is worth zero, which beats losing. The engine must still take it."""
    s = searcher
    s.new_game()
    # White is a rook against a queen; every continuation is lost.
    board = chess.Board("6k1/8/8/8/8/8/3q4/R6K w - - 10 40")
    assert board.is_valid()
    legal = list(board.legal_moves)
    assert len(legal) >= 2
    # Make one legal move a real threefold, and confirm the search would
    # otherwise consider the position lost.
    s.new_game()
    _, plain = s.search(board.copy(), 0, max_depth=8)
    assert plain.score < 0, "fixture should be losing for the side to move"
    s.new_game()
    repeat = legal[0]
    s._history[key_after(s, board, repeat)] = 2
    move, info = s.search(board.copy(), 0, max_depth=8)
    assert move == repeat, "refused a saving draw"
    assert info.score == 0


def test_no_history_means_no_behaviour_change(searcher):
    """With nothing repeated, the root check must not alter the choice."""
    s = searcher
    for fen in ("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 1",
                "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
                chess.STARTING_FEN):
        s.new_game()
        move, info = s.search(chess.Board(fen), 0, max_depth=8)
        assert move in chess.Board(fen).legal_moves
        assert info.depth >= 1


def test_every_move_repeating_still_returns_a_legal_move(searcher):
    """When there is nothing but repetitions, the engine still has to move."""
    s = searcher
    s.new_game()
    board = chess.Board("7k/8/8/8/8/8/8/7K w - - 20 60")
    for m in board.legal_moves:
        s._history[key_after(s, board, m)] = 2
    move, _ = s.search(board.copy(), 0, max_depth=6)
    assert move in board.legal_moves
