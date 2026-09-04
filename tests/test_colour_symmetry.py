"""Colour symmetry of the engine, not only of the evaluator.

A position and its colour reflection -- mirrored vertically with the colours
swapped, castling rights and the en-passant square carried across -- are the
same position with the roles exchanged. Anything the engine reports from the
side to move's point of view must therefore be identical for the two, and the
best move must be the mirrored move.

Two of those three hold exactly and are asserted here: the static evaluation
and the quiescence score. The third does not, and the reason is recorded rather
than hidden. ``python-chess`` generates moves in square-index order, so
mirroring reorders moves that the ordering heuristics score equally; with
late-move reductions, null-move pruning and a transposition table a different
order produces a different tree, and a fixed-depth search can therefore return
a different score and occasionally a different move. The audit in
``benchmarks/current/2026-09-04-colour-asymmetry-audit.md`` measured this over
600 mirrored pairs at depth 5: static and quiescence agreed 600/600, the root
score agreed 555/600 and the best move 567/600, and the divergence has no
direction (mean root difference -0.03 cp in favour of the Black-to-move copy,
sign split 27 against 18). What is asserted here is therefore the invariant
that must hold exactly, plus the weaker property that matters for safety --
the search returns a legal move on both members of every pair.

Fixtures deliberately include castling rights, en passant, a promotion race, a
pawnless ending and a position in check, because those are the indexings most
likely to break under a mirror.
"""

from __future__ import annotations

import chess
import pytest

from cs_constants import INFINITY
from cs_eval import evaluate
from cs_search import Searcher

PAIRS = [
    ("opening, all castling rights", chess.STARTING_FEN),
    ("castling rights, white to move",
     "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 6 5"),
    ("castling rights, black to move",
     "rnbqkb1r/pp2pppp/2p2n2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R b KQkq - 2 5"),
    ("en passant available", "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 4"),
    ("en passant, black to move", "rnbqkbnr/pppp1ppp/8/8/3pP3/5N2/PPP2PPP/RNBQKB1R b KQkq e3 0 4"),
    ("promotion race", "8/1P4k1/8/8/8/8/6p1/6K1 w - - 0 1"),
    ("pawnless rook and bishop against rook", "3k4/4R3/8/5K2/4B3/8/4r3/8 w - - 0 1"),
    ("king and pawn ending", "8/5k2/7p/5p2/3K1P2/4P3/8/8 b - - 1 62"),
    ("in check, two legal replies", "8/8/8/8/8/5k2/7q/6K1 w - - 0 1"),
    ("checkmate, no legal reply", "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"),
    ("middlegame, no castling rights",
     "r4rk1/1pp2ppp/p1np1n2/2b1p1B1/2B1P3/2NP1N2/PPP2PPP/R4RK1 w - - 0 11"),
    ("queenless middlegame", "r4rk1/pp3ppp/2n1bn2/2pp4/3P4/2P1PN2/PP1N1PPP/R4RK1 b - - 0 12"),
    ("bare king mating gradient", "8/8/8/4k3/8/8/4KQ2/8 w - - 0 1"),
]


def mirror_move(move: chess.Move) -> chess.Move:
    return chess.Move(
        chess.square_mirror(move.from_square),
        chess.square_mirror(move.to_square),
        move.promotion,
    )


@pytest.mark.parametrize(("name", "fen"), PAIRS)
def test_static_evaluation_is_identical_under_colour_reflection(name: str, fen: str) -> None:
    """From the side to move's point of view the two positions are the same one."""
    board = chess.Board(fen)
    assert evaluate(board) == evaluate(board.mirror()), name


@pytest.mark.parametrize(("name", "fen"), PAIRS)
def test_quiescence_is_identical_under_colour_reflection(name: str, fen: str) -> None:
    board = chess.Board(fen)
    ours = Searcher(tt_bits=14)._quiescence(board, -INFINITY, INFINITY, 0, 0)
    theirs = Searcher(tt_bits=14)._quiescence(board.mirror(), -INFINITY, INFINITY, 0, 0)
    assert ours == theirs, name


@pytest.mark.parametrize(("name", "fen"), PAIRS)
def test_mirrored_legal_moves_match_and_the_search_returns_one(name: str, fen: str) -> None:
    """Safety, not agreement: whatever the ordering does, both members stay legal."""
    board = chess.Board(fen)
    mirrored = board.mirror()
    ours_mirrored = {mirror_move(m).uci() for m in board.legal_moves}
    assert ours_mirrored == {m.uci() for m in mirrored.legal_moves}, name
    # A real budget, not zero: a zero clock puts the time manager in its panic
    # path, where returning nothing at all is legitimate. ``max_depth`` is what
    # keeps this fast.
    ours, _ = Searcher(tt_bits=14).search(board, 5_000, max_depth=3)
    theirs, _ = Searcher(tt_bits=14).search(mirrored, 5_000, max_depth=3)
    if board.is_checkmate():
        # No legal reply exists on either member; returning nothing is correct.
        assert ours is None and theirs is None, name
        return
    assert ours in board.legal_moves, name
    assert theirs in mirrored.legal_moves, name


def test_the_evaluator_has_no_colour_preference_over_a_random_sample() -> None:
    """Exactness over many positions, which the twelve fixtures above cannot give.

    Random legal play reaches castling, en passant and promotions on its own;
    the point of the sample is volume, and the assertion is the same exact
    identity rather than a tolerance.
    """
    import random

    rng = random.Random(20260904)
    checked = 0
    for _ in range(60):
        board = chess.Board()
        for _ in range(rng.randint(1, 80)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
            if board.is_game_over():
                break
            assert evaluate(board) == evaluate(board.mirror()), board.fen()
            checked += 1
    assert checked > 500
