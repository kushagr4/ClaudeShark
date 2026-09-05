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

from collections.abc import Callable, Iterator
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


_BB_ALL = chess.BB_ALL
_ray = chess.ray


def legal_captures(board: chess.Board, in_check: bool) -> Iterator[chess.Move]:
    """The moves ``board.generate_legal_captures()`` yields, in the same order.

    python-chess sets up every legal-move generator by finding the king, its
    pinned pieces and its checkers, and then asks ``_is_safe`` about every
    pseudo-legal move. Out of check the checkers scan is wasted and the safety
    question has a short answer: a capture is legal unless a pinned piece
    leaves its pin ray or the king steps onto an attacked square. This does
    that inline for the two capture sites that already know they are not in
    check; in check it defers to python-chess, whose evasion generator has its
    own order. En passant is rare and has its own discovered-check case, so it
    is left to python-chess as well. tests/test_legal_captures.py holds the
    sequence equal to the library's on random positions.
    """
    if in_check:
        yield from board.generate_legal_captures()
        return
    us = board.turn
    king = board.king(us)
    if king is None:
        yield from board.generate_legal_captures()
        return
    blockers = board._slider_blockers(king)
    them = board.occupied_co[not us]
    king_mask = 1 << king
    is_attacked_by = board.is_attacked_by
    for move in board.generate_pseudo_legal_moves(_BB_ALL, them):
        from_mask = 1 << move.from_square
        if from_mask & blockers:
            if not _ray(move.from_square, move.to_square) & king_mask:
                continue
        elif from_mask == king_mask and is_attacked_by(not us, move.to_square):
            continue
        yield move
    if board.ep_square is not None:
        yield from board.generate_legal_ep()


def staged_moves(
    board: chess.Board,
    tt_move: chess.Move | None,
    ply: int,
    heuristics: Heuristics,
    see_losing: Callable[[chess.Board, chess.Move], bool] | None = None,
    in_check: bool = True,
) -> Iterator[chess.Move]:
    """Yield the moves ``order_moves`` would return, in the same order, lazily.

    Most interior nodes cut off on their first move, so generating and sorting
    every legal move before searching any of them is mostly wasted. This
    produces the head of the ordering -- the transposition move, then the
    captures that are not losing, then the killers -- from cheap masked
    generation, and only when the search asks for more does it build the full
    list and hand over the rest in ``order_moves``' own order.

    The head is exactly the prefix of ``order_moves``' output, because every
    head score (2,000,000 for the table move, at least 1,000,700 for a capture
    that is not losing, 900,000 and 899,000 for the killers) exceeds every
    tail score (history is capped at 800,000, losing captures sit near
    100,000, under-promotions at or below 0), and the relative order inside
    each head band is the same stable sort over the same generation order.

    ``in_check`` lets the capture stage skip python-chess's checkers scan;
    pass True when unknown, which is always correct.

    **Only valid when the side to move has no pawn on its seventh rank.**
    Promotions score above the table move (queen-promotion captures) or
    between it and the captures (queen-promotion pushes), and under-promotion
    pushes tie with zero-history quiet moves, so a position with promotions
    available goes through the full sort instead. The caller checks this.
    """
    them = board.occupied_co[not board.turn]
    piece_type_at = board.piece_type_at
    ep_square = board.ep_square
    done: list[chess.Move] = []

    if tt_move is not None and board.is_legal(tt_move):
        yield tt_move
        done.append(tt_move)

    winning: list[tuple[int, chess.Move]] = []
    for move in legal_captures(board, in_check):
        if move == tt_move:
            continue
        to_square = move.to_square
        if (1 << to_square) & them:
            victim = piece_type_at(to_square) or _PAWN
            attacker = piece_type_at(move.from_square) or _PAWN
            if (
                see_losing is not None
                and PIECE_VALUE[victim] < PIECE_VALUE[attacker]
                and see_losing(board, move)
            ):
                continue  # a losing capture: it belongs in the tail
            score = CAPTURE_BONUS + PIECE_VALUE[victim] * 16 - PIECE_VALUE[attacker]
        else:
            # En passant: the target square is empty, the victim is a pawn.
            score = CAPTURE_BONUS + PIECE_VALUE[_PAWN] * 16 - PIECE_VALUE[_PAWN]
        winning.append((score, move))
    if winning:
        winning.sort(key=_first, reverse=True)
        for _, move in winning:
            yield move
            done.append(move)

    killers = heuristics.killers
    killer_1 = killers[ply * 2]
    killer_2 = killers[ply * 2 + 1]
    pawns = board.pawns
    for killer in (killer_1, killer_2):
        if killer is None or killer == tt_move:
            continue
        if killer is killer_2 and killer == killer_1:
            continue
        if (1 << killer.to_square) & them:
            continue  # a capture here; already produced or deferred above
        if killer.to_square == ep_square and (1 << killer.from_square) & pawns:
            continue
        if killer.promotion:
            continue
        if board.is_legal(killer):
            yield killer
            done.append(killer)

    moves = list(board.legal_moves)
    if len(moves) <= len(done):
        return
    seen = set(done)
    for move in order_moves(board, moves, tt_move, ply, heuristics, see_losing):
        if move in seen:
            continue
        yield move
