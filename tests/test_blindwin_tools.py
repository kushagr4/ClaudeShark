"""The blind-win audit tooling: passer detection and mechanism classification.

The audit's central table is built by these two functions, so they get pinned:
a passer is a pawn with no enemy pawn ahead on its file or the neighbours, and
a principal variation is classified by what it does -- a promotion, a material
gain, king moves -- with a quiet line left as the residual.
"""

from __future__ import annotations

import chess

from tools.blindwin.dataset import material, mechanism, passers

# Only the e5 pawn is passed: the a2 and a7 pawns face each other on the a-file.
PASSERS = "8/p7/8/4P3/8/8/P7/4K2k w - - 0 1"
# Two kings and a white pawn about to promote; Black to move cannot stop it.
RACE = "8/7P/8/8/8/8/k7/4K3 w - - 0 1"


def test_passers_are_found_for_each_colour() -> None:
    board = chess.Board(PASSERS)
    assert passers(board, chess.WHITE) == [chess.E5]
    assert passers(board, chess.BLACK) == []


def test_a_pawn_blocked_by_an_enemy_pawn_ahead_is_not_passed() -> None:
    board = chess.Board("8/4p3/8/4P3/8/8/8/4K2k w - - 0 1")
    assert passers(board, chess.WHITE) == []
    assert passers(board, chess.BLACK) == []


def test_material_is_from_the_given_side() -> None:
    board = chess.Board(PASSERS)
    assert material(board, chess.WHITE) == 1
    assert material(board, chess.BLACK) == -1


def test_promotion_in_the_line_is_a_promotion_race() -> None:
    board = chess.Board(RACE)
    kind, info = mechanism(board, ["h7h8q"], None)
    assert kind == "promotion race"
    assert info["promotions"] == 1


def test_a_mate_in_the_line_is_a_mating_net() -> None:
    board = chess.Board("6k1/8/6K1/8/8/8/8/7R w - - 0 1")
    kind, _ = mechanism(board, ["h1h8"], 1)
    assert kind == "mating net"


def test_a_quiet_line_is_the_residual() -> None:
    board = chess.Board(chess.STARTING_FEN)
    kind, info = mechanism(board, ["e2e4", "e7e5", "g1f3"], None)
    assert kind == "quiet / unresolved"
    assert info["material_gain"] == 0
