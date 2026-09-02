"""Iterative-deepening negamax with alpha-beta, a transposition table and
quiescence search.

Control flow worth knowing about:

* The board is rebuilt from the FEN on every ``search`` call, and a timeout is
  signalled by raising :class:`SearchAbort` from wherever the search happens to
  be. Nothing unwinds the move stack on the way out -- the aborted board is
  simply discarded. That keeps ``try``/``finally`` out of the hot loop entirely.
* A legal fallback move is chosen before any expensive work starts, so there is
  always something legal to return.
* A root move that has been *fully* searched at the current depth and improved
  alpha is committed even if the iteration is later aborted. Its score came from
  a complete search with a valid window, so it is at least as trustworthy as the
  previous iteration's answer.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

import chess

from cs_constants import (
    BOUND_EXACT,
    BOUND_LOWER,
    BOUND_UPPER,
    DRAW_SCORE,
    INFINITY,
    MATE_BOUND,
    MATE_SCORE,
    MAX_PLY,
    PIECE_VALUE,
    TOTAL_PHASE,
)
from cs_eval import evaluate, is_material_draw
from cs_ordering import Heuristics, order_captures, order_moves, update_history
from cs_time import CHECK_INTERVAL, TimeManager
from cs_tt import TranspositionTable, score_from_tt, score_to_tt

DEBUG = bool(os.environ.get("CLAUDESHARK_DEBUG"))

MAX_DEPTH = 64
# Quiescence is bounded by its own ply counter as well as by delta pruning, so a
# forcing sequence cannot run away in a tactical position.
QS_MAX_PLY = 10
# A capture has to plausibly get within this of alpha to be worth searching.
DELTA_MARGIN = 200

_CHECK_MASK = CHECK_INTERVAL - 1
_NULL_MOVE = chess.Move.null()
_QUEEN = chess.QUEEN
_RANK_7 = chess.BB_RANK_7
_RANK_2 = chess.BB_RANK_2


class SearchAbort(Exception):
    """Raised when the hard deadline passes mid-search."""


@dataclass
class SearchInfo:
    """Per-move telemetry. Cheap to fill; only printed when CLAUDESHARK_DEBUG is set."""

    depth: int = 0
    score: int = 0
    nodes: int = 0
    qnodes: int = 0
    elapsed_ms: float = 0.0
    nps: int = 0
    tt_probes: int = 0
    tt_hits: int = 0
    cutoffs: int = 0
    aborted: bool = False
    budget_ms: float = 0.0
    pv: list[str] = field(default_factory=list)


class Searcher:
    """Owns everything that survives between moves: the TT, heuristics and clock."""

    def __init__(self, tt_bits: int | None = None) -> None:
        self.tt = TranspositionTable() if tt_bits is None else TranspositionTable(tt_bits)
        self.heuristics = Heuristics()
        self.time = TimeManager()
        self.nodes = 0
        self.qnodes = 0
        self.cutoffs = 0
        self._path: list[int] = [0] * (MAX_PLY + 8)
        # Positions we have been handed before, so we can see a repetition the
        # referee would claim as a draw. We only see our own turns, which covers
        # the shuffling case that matters.
        self._game_counts: dict[int, int] = {}
        self._partial_move: chess.Move | None = None
        self._partial_score = 0

    def new_game(self) -> None:
        self.tt.clear()
        self.heuristics.clear()
        self._game_counts.clear()

    # ------------------------------------------------------------------ root

    def search(
        self,
        board: chess.Board,
        time_left_ms: int,
        fixed_budget_ms: float | None = None,
    ) -> tuple[chess.Move | None, SearchInfo]:
        """Pick a move. ``fixed_budget_ms`` overrides clock-based allocation and
        exists for benchmarking; the agent never passes it."""
        info = SearchInfo()

        legal = list(board.legal_moves)
        if not legal:
            return None, info

        timer = self.time
        if fixed_budget_ms is None:
            timer.observe(time_left_ms)
            timer.begin(time_left_ms, _phase_of(board))
        else:
            timer.begin_fixed(fixed_budget_ms)
        info.budget_ms = timer.soft_ms

        best_move = legal[0]  # legal fallback before any expensive work
        if len(legal) == 1:
            timer.record_spend()
            info.depth = 0
            return best_move, info

        self.nodes = 0
        self.qnodes = 0
        self.cutoffs = 0
        self.tt.reset_stats()
        self.heuristics.age()

        root_key = hash(board._transposition_key())
        self._game_counts[root_key] = self._game_counts.get(root_key, 0) + 1
        self._path[0] = root_key

        entry = self.tt.probe(root_key)
        root_moves = order_moves(board, legal, entry[4] if entry else None, 0, self.heuristics)

        best_score = 0

        for depth in range(1, MAX_DEPTH + 1):
            self._partial_move = None
            try:
                score, move, ordered = self._search_root(board, depth, root_moves)
            except SearchAbort:
                info.aborted = True
                # Commit a root move that completed at this depth and beat alpha.
                if self._partial_move is not None:
                    best_move = self._partial_move
                    best_score = self._partial_score
                    info.depth = depth
                break

            best_move, best_score, root_moves = move, score, ordered
            info.depth = depth

            if abs(best_score) > MATE_BOUND:
                break  # a forced mate is not going to be improved on
            if timer.soft_expired():
                break
            # Each extra ply costs roughly 2-4x the last. If we are already
            # halfway through the budget the next iteration cannot finish, and
            # an aborted iteration is mostly wasted work.
            if timer.soft_fraction_used() > 0.45:
                break

        # An aborted iteration only proves the committed move is at least this
        # good, so it goes in as a lower bound rather than an exact score.
        self.tt.store(
            root_key,
            info.depth,
            score_to_tt(best_score, 0),
            BOUND_LOWER if info.aborted else BOUND_EXACT,
            best_move,
        )
        timer.record_spend()

        info.score = best_score
        info.nodes = self.nodes
        info.qnodes = self.qnodes
        info.cutoffs = self.cutoffs
        info.elapsed_ms = timer.elapsed_ms()
        info.nps = int(self.nodes * 1000.0 / info.elapsed_ms) if info.elapsed_ms > 0 else 0
        info.tt_probes = self.tt.probes
        info.tt_hits = self.tt.hits
        if DEBUG:
            print(
                f"depth {info.depth} score {info.score} nodes {info.nodes} "
                f"({info.qnodes} q) {info.elapsed_ms:.0f}ms nps {info.nps} "
                f"budget {info.budget_ms:.0f}ms tt {info.tt_hits}/{info.tt_probes} "
                f"cut {info.cutoffs}{' ABORT' if info.aborted else ''} best {best_move}",
                file=sys.stderr,
            )
        return best_move, info

    def _search_root(
        self, board: chess.Board, depth: int, root_moves: list[chess.Move]
    ) -> tuple[int, chess.Move, list[chess.Move]]:
        alpha = -INFINITY
        best_score = -INFINITY
        best_move = root_moves[0]
        scored: list[tuple[int, chess.Move]] = []

        push = board.push
        pop = board.pop

        for move in root_moves:
            push(move)
            score = -self._negamax(board, depth - 1, -INFINITY, -alpha, 1)
            pop()

            scored.append((score, move))
            if score > best_score:
                best_score = score
                best_move = move
                self._partial_move = move
                self._partial_score = score
                if score > alpha:
                    alpha = score

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return best_score, best_move, [pair[1] for pair in scored]

    # ------------------------------------------------------------------ tree

    def _negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        self.nodes += 1
        if not (self.nodes & _CHECK_MASK) and self.time.hard_expired():
            raise SearchAbort

        # Draw detection before anything expensive.
        if board.halfmove_clock >= 100 or is_material_draw(board):
            return DRAW_SCORE

        key = hash(board._transposition_key())

        # Repetition: a position seen earlier on this line, or one the game has
        # already visited, is scored as a draw. Only same-side-to-move plies can
        # repeat, hence the stride of two.
        path = self._path
        index = ply - 2
        limit = ply - board.halfmove_clock
        if limit < 0:
            limit = 0
        while index >= limit:
            if path[index] == key:
                return DRAW_SCORE
            index -= 2
        if key in self._game_counts:
            return DRAW_SCORE
        path[ply] = key

        tt = self.tt
        tt.probes += 1
        entry = tt.probe(key)
        tt_move: chess.Move | None = None
        if entry is not None:
            tt.hits += 1
            _, entry_depth, entry_score, entry_bound, tt_move = entry
            if entry_depth >= depth:
                score = score_from_tt(entry_score, ply)
                if entry_bound == BOUND_EXACT:
                    return score
                if entry_bound == BOUND_LOWER:
                    if score >= beta:
                        return score
                elif score <= alpha:
                    return score

        if depth <= 0:
            return self._quiescence(board, alpha, beta, ply, 0)

        if ply >= MAX_PLY - 2:
            return evaluate(board)

        in_check = board.is_check()

        # Null-move pruning: hand the opponent a free move and see whether the
        # position still fails high. If it does, the real move list will too, so
        # the whole subtree can be skipped. Restricted to non-PV nodes, and
        # disabled in check and when the side to move has only pawns, because
        # that is where zugzwang makes "passing" a bad assumption.
        if (
            not in_check
            and depth >= 3
            and beta - alpha == 1
            and board.occupied_co[board.turn] & ~(board.pawns | board.kings)
        ):
            reduction = 3 if depth > 6 else 2
            push_null = board.push
            push_null(_NULL_MOVE)
            null_score = -self._negamax(board, depth - 1 - reduction, -beta, -beta + 1, ply + 1)
            board.pop()
            if null_score >= beta:
                # A mate score proved by a null move is not a real mate.
                return beta if null_score > MATE_BOUND else null_score

        moves = list(board.legal_moves)
        if not moves:
            # Mate scores count from the root so that shorter mates score higher.
            return -MATE_SCORE + ply if in_check else DRAW_SCORE

        moves = order_moves(board, moves, tt_move, ply, self.heuristics)

        original_alpha = alpha
        best_score = -INFINITY
        best_move: chess.Move | None = None
        push = board.push
        pop = board.pop
        child_depth = depth - 1
        child_ply = ply + 1

        them = board.occupied_co[not board.turn]
        killers = self.heuristics.killers
        killer_index = ply * 2
        killer_a = killers[killer_index]
        killer_b = killers[killer_index + 1]
        can_reduce = depth >= 3 and not in_check

        for move_index, move in enumerate(moves):
            push(move)
            if move_index == 0:
                score = -self._negamax(board, child_depth, -beta, -alpha, child_ply)
            else:
                # Late move reductions: ordering already put the plausible moves
                # first, so a quiet move this far down the list is searched
                # shallower on the assumption it will not beat alpha. If it does
                # anyway, it is re-searched at full depth, so the reduction costs
                # accuracy only when it was right to be sceptical.
                reduction = 0
                if (
                    can_reduce
                    and move_index >= 3
                    and not (1 << move.to_square) & them
                    and not move.promotion
                    and move != killer_a
                    and move != killer_b
                ):
                    reduction = 2 if (move_index >= 6 and depth >= 6) else 1
                    if reduction > child_depth - 1:
                        reduction = child_depth - 1

                # Principal variation search: every move after the first gets a
                # null-window probe, which is much cheaper than a full window.
                score = -self._negamax(
                    board, child_depth - reduction, -alpha - 1, -alpha, child_ply
                )
                if reduction and score > alpha:
                    score = -self._negamax(board, child_depth, -alpha - 1, -alpha, child_ply)
                if alpha < score < beta:
                    score = -self._negamax(board, child_depth, -beta, -alpha, child_ply)
            pop()

            if score > best_score:
                best_score = score
                best_move = move
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        self.cutoffs += 1
                        if not board.is_capture(move) and not move.promotion:
                            self.heuristics.store_killer(ply, move)
                            update_history(self.heuristics, board.turn, move, depth)
                        break

        if best_score >= beta:
            bound = BOUND_LOWER
        elif best_score > original_alpha:
            bound = BOUND_EXACT
        else:
            bound = BOUND_UPPER
        tt.store(key, depth, score_to_tt(best_score, ply), bound, best_move)
        return best_score

    # ----------------------------------------------------------- quiescence

    def _quiescence(
        self, board: chess.Board, alpha: int, beta: int, ply: int, qply: int
    ) -> int:
        self.nodes += 1
        self.qnodes += 1
        if not (self.nodes & _CHECK_MASK) and self.time.hard_expired():
            raise SearchAbort

        if qply >= QS_MAX_PLY or ply >= MAX_PLY - 2:
            return evaluate(board)

        in_check = board.is_check()

        if in_check:
            # No stand-pat while in check: the position is not quiet by
            # definition and every evasion has to be considered.
            moves = list(board.legal_moves)
            if not moves:
                return -MATE_SCORE + ply
            moves = order_captures(board, moves)
            best_score = -INFINITY
            stand_pat = -INFINITY
        else:
            stand_pat = evaluate(board)
            if stand_pat >= beta:
                return stand_pat
            if stand_pat > alpha:
                alpha = stand_pat
            best_score = stand_pat
            moves = _tactical_moves(board)
            if not moves:
                return stand_pat
            moves = order_captures(board, moves)

        piece_type_at = board.piece_type_at
        push = board.push
        pop = board.pop
        child_ply = ply + 1
        child_qply = qply + 1

        for move in moves:
            if not in_check:
                # Delta pruning: if winning the target piece outright still
                # leaves us far below alpha, the capture cannot rescue the node.
                victim = piece_type_at(move.to_square)
                gain = PIECE_VALUE[victim] if victim else PIECE_VALUE[chess.PAWN]
                if move.promotion == _QUEEN:
                    gain += PIECE_VALUE[_QUEEN]
                if stand_pat + gain + DELTA_MARGIN < alpha:
                    continue

            push(move)
            score = -self._quiescence(board, -beta, -alpha, child_ply, child_qply)
            pop()

            if score > best_score:
                best_score = score
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        self.cutoffs += 1
                        break

        return best_score


def _tactical_moves(board: chess.Board) -> list[chess.Move]:
    """Captures plus queen promotions -- the moves quiescence is allowed to make."""
    moves = list(board.generate_legal_captures())
    promotion_rank = _RANK_7 if board.turn else _RANK_2
    candidates = board.pawns & board.occupied_co[board.turn] & promotion_rank
    if candidates:
        for move in board.generate_legal_moves(candidates, ~board.occupied):
            if move.promotion == _QUEEN:
                moves.append(move)
    return moves


def _phase_of(board: chess.Board) -> int:
    phase = (
        (board.knights | board.bishops).bit_count()
        + 2 * board.rooks.bit_count()
        + 4 * board.queens.bit_count()
    )
    return phase if phase < TOTAL_PHASE else TOTAL_PHASE
