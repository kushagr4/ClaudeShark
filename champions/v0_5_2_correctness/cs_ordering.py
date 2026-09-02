"""Move ordering.

Alpha-beta only pays for itself when the best move is searched first, so this is
the highest-leverage code in the engine after the search itself. The bands are:

    transposition move  >  queen promotions  >  captures (MVV-LVA)
                        >  killers  >  history-ranked quiet moves

Captures are all placed above killers. Separating winning from losing captures
needs static exchange evaluation, which is a Phase-10 experiment, not a v0.1
assumption.

Sorting is done on ``(score, move)`` pairs with an ``itemgetter`` key so the sort
never falls back to comparing ``chess.Move`` objects (which are not orderable)
and never calls back into Python during the sort itself.
"""

from __future__ import annotations

from collections.abc import Callable
from operator import itemgetter

import chess

from cs_constants import MAX_PLY, PIECE_VALUE

_first = itemgetter(0)

TT_BONUS = 2_000_000
PROMO_BONUS = 1_600_000
CAPTURE_BONUS = 1_000_000
KILLER_1 = 900_000
KILLER_2 = 899_000
# Captures that static exchange evaluation says lose material sort below the
# killers rather than above every quiet move. Only consulted when the ordering
# flag is on and the capture already looks suspicious.
LOSING_CAPTURE = 100_000
# History is clamped well below the killer band so ordering bands never overlap.
HISTORY_CAP = 800_000

_QUEEN = chess.QUEEN
_PAWN = chess.PAWN


class Heuristics:
    """Killer and history tables, sized once and reused for the whole game."""

    __slots__ = ("history", "killers")

    def __init__(self) -> None:
        # Two killers per ply, flattened: index ply * 2 + slot.
        self.killers: list[chess.Move | None] = [None] * (MAX_PLY * 2)
        # Indexed colour * 4096 + from_square * 64 + to_square.
        self.history: list[int] = [0] * 8192

    def clear(self) -> None:
        killers = self.killers
        for i in range(len(killers)):
            killers[i] = None
        history = self.history
        for i in range(8192):
            history[i] = 0

    def age(self) -> None:
        """Halve history between moves so old games stop dominating new ones."""
        history = self.history
        for i in range(8192):
            value = history[i]
            if value:
                history[i] = value >> 1

    def store_killer(self, ply: int, move: chess.Move) -> None:
        index = ply * 2
        killers = self.killers
        if killers[index] != move:
            killers[index + 1] = killers[index]
            killers[index] = move


def order_moves(
    board: chess.Board,
    moves: list[chess.Move],
    tt_move: chess.Move | None,
    ply: int,
    heuristics: Heuristics,
    see_losing: Callable[[chess.Board, chess.Move], bool] | None = None,
) -> list[chess.Move]:
    """Return ``moves`` sorted best-first. Mutates and returns a new list.

    ``see_losing``, when supplied, is consulted only for captures where the
    victim is worth less than the attacker -- the cases where the capture might
    be losing at all. Running a full exchange evaluation on every capture at
    every node costs more than the ordering gains.
    """
    if len(moves) < 2:
        return moves

    turn = board.turn
    them = board.occupied_co[not turn]
    ep_square = board.ep_square
    pawns = board.pawns
    piece_type_at = board.piece_type_at

    killers = heuristics.killers
    killer_index = ply * 2
    killer_1 = killers[killer_index]
    killer_2 = killers[killer_index + 1]

    history = heuristics.history
    history_base = 4096 if turn else 0

    scored: list[tuple[int, chess.Move]] = []
    append = scored.append

    for move in moves:
        if move == tt_move:
            append((TT_BONUS, move))
            continue

        to_square = move.to_square
        to_mask = 1 << to_square
        promotion = move.promotion

        if to_mask & them:
            # The square is occupied by the enemy, so both lookups hit; the
            # ``or _PAWN`` fallbacks only exist to keep the indexing total.
            victim = piece_type_at(to_square) or _PAWN
            attacker = piece_type_at(move.from_square) or _PAWN
            # MVV-LVA: most valuable victim first, cheapest attacker as the
            # tiebreak, so QxP sorts below PxQ.
            score = CAPTURE_BONUS + PIECE_VALUE[victim] * 16 - PIECE_VALUE[attacker]
            if promotion:
                score += PROMO_BONUS if promotion == _QUEEN else -PROMO_BONUS
            elif (
                see_losing is not None
                and PIECE_VALUE[victim] < PIECE_VALUE[attacker]
                and see_losing(board, move)
            ):
                score = LOSING_CAPTURE + PIECE_VALUE[victim] * 16 - PIECE_VALUE[attacker]
            append((score, move))
            continue

        if promotion:
            # Queen promotions are close to winning a queen; under-promotions
            # are almost always noise, so they sort below quiet moves.
            append((PROMO_BONUS if promotion == _QUEEN else 0, move))
            continue

        if to_square == ep_square and (1 << move.from_square) & pawns:
            append((CAPTURE_BONUS + PIECE_VALUE[_PAWN] * 16 - PIECE_VALUE[_PAWN], move))
            continue

        if move == killer_1:
            append((KILLER_1, move))
            continue
        if move == killer_2:
            append((KILLER_2, move))
            continue

        append((history[history_base + (move.from_square << 6) + to_square], move))

    scored.sort(key=_first, reverse=True)
    return [pair[1] for pair in scored]


def order_captures(board: chess.Board, moves: list[chess.Move]) -> list[chess.Move]:
    """MVV-LVA order for quiescence. No killers or history at these nodes."""
    if len(moves) < 2:
        return moves

    piece_type_at = board.piece_type_at
    scored: list[tuple[int, chess.Move]] = []
    append = scored.append

    for move in moves:
        victim = piece_type_at(move.to_square)
        # En passant leaves the target square empty; the victim is still a pawn.
        victim_value = PIECE_VALUE[victim] if victim else PIECE_VALUE[_PAWN]
        score = victim_value * 16 - PIECE_VALUE[piece_type_at(move.from_square) or _PAWN]
        if move.promotion == _QUEEN:
            score += PROMO_BONUS
        append((score, move))

    scored.sort(key=_first, reverse=True)
    return [pair[1] for pair in scored]


def update_history(
    heuristics: Heuristics, turn: chess.Color, move: chess.Move, depth: int
) -> None:
    """Reward a quiet move that caused a beta cutoff, weighted by depth."""
    history = heuristics.history
    index = (4096 if turn else 0) + (move.from_square << 6) + move.to_square
    value = history[index] + depth * depth
    if value > HISTORY_CAP:
        # Rescale the whole table rather than clamping one entry, so the
        # relative ordering information is preserved.
        for i in range(8192):
            history[i] >>= 1
        value >>= 1
    history[index] = value
