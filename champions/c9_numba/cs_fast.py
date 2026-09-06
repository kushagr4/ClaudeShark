"""Searcher driving the compiled core in ``cs_core``.

Same public surface as ``cs_search.Searcher`` -- ``search(board, time_left_ms,
fixed_budget_ms=None, max_depth=None)`` returning ``(move, SearchInfo)`` and
``new_game()`` -- so the agent, the arena, the benchmark, the tactics suite and
the clock ladder run unchanged. The root policy is C5's: iterative deepening,
aspiration windows from depth 4, root moves re-ordered by their scores after
every completed iteration, a fully searched root move committed on abort, the
C5 time allocator. Everything below the root runs in ``cs_core``.

The first search after import compiles the kernels (measured in
``benchmarks/current/2026-09-06-c9-numba-core-prereg.md``); ``warm_up()`` does
that during the platform's initialisation budget.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

import chess
import numpy as np

import cs_core as core
from cs_time import TimeManager

MAX_DEPTH = 64
ASPIRATION_MIN_DEPTH = 4
ASPIRATION_DELTA = 30
ASPIRATION_MAX_DELTA = 800
GAME_KEYS = 1024

# Compilation happens on the first search of the process. It is done before
# the clock for that search is opened, so a benchmark's first position and
# the agent's first move are never charged for it.
_COMPILED = False


@dataclass
class SearchInfo:
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
    unstable_iterations: int = 0
    researches: int = 0
    pv: list[str] = field(default_factory=list)


class _TableStats:
    """What tools read off ``searcher.tt``: probe and hit counters."""

    __slots__ = ("hits", "probes")

    def __init__(self) -> None:
        self.probes = 0
        self.hits = 0


class Searcher:
    """Owns everything that survives between moves: the table, heuristics, clock."""

    def __init__(self, tt_bits: int | None = None) -> None:
        del tt_bits  # the compiled table has a fixed size (cs_core.TT_BITS)
        self.TK = np.zeros(1 << core.TT_BITS, dtype=np.int64)
        self.TV = np.zeros(1 << core.TT_BITS, dtype=np.int64)
        self.KILL = np.zeros(2 * core.STACK, dtype=np.int64)
        self.HIST = np.zeros(8192, dtype=np.int64)
        self.B, self.O, self.M, self.S, self.U = core.new_board_arrays()
        self.MLS = np.zeros((core.STACK, core.MAX_MOVES), dtype=np.int64)
        self.MSS = np.zeros((core.STACK, core.MAX_MOVES), dtype=np.int64)
        self.PATH = np.zeros(core.STACK, dtype=np.int64)
        self.GK = np.zeros(GAME_KEYS, dtype=np.int64)
        self.CTL = np.zeros(16, dtype=np.int64)
        self.TCTL = np.zeros(2, dtype=np.float64)
        self.GAINS = np.zeros(40, dtype=np.int64)
        self.ROOT = np.zeros(core.MAX_MOVES, dtype=np.int64)
        self.RS = np.zeros(core.MAX_MOVES, dtype=np.int64)
        self.time = TimeManager()
        self.tt = _TableStats()
        self.nodes = 0
        self.qnodes = 0
        self.cutoffs = 0
        self.researches = 0
        self._game_keys: list[int] = []

    def new_game(self) -> None:
        self.TK.fill(0)
        self.TV.fill(0)
        self.KILL.fill(0)
        self.HIST.fill(0)
        self._game_keys.clear()
        self.CTL[10] = 0

    # ------------------------------------------------------------------ root

    def search(
        self,
        board: chess.Board,
        time_left_ms: int,
        fixed_budget_ms: float | None = None,
        max_depth: int | None = None,
    ) -> tuple[chess.Move | None, SearchInfo]:
        info = SearchInfo()
        legal = list(board.legal_moves)
        if not legal:
            return None, info
        if not _COMPILED:
            warm_up()

        timer = self.time
        if max_depth is not None:
            timer.begin_fixed(3_600_000.0)
        elif fixed_budget_ms is None:
            timer.begin(time_left_ms, _phase_of(board))
        else:
            timer.begin_fixed(fixed_budget_ms)
        info.budget_ms = timer.soft_ms

        if len(legal) == 1:
            info.depth = 0
            return legal[0], info

        B, O, M, S, U = self.B, self.O, self.M, self.S, self.U
        core.load_board(board, B, O, M, S)
        CTL = self.CTL
        CTL[:10] = 0
        # Halve history between moves (C5's Heuristics.age).
        self.HIST >>= 1
        self.TCTL[0] = timer._started + timer.hard_ms / 1000.0

        root_key = int(S[4])
        if root_key not in self._game_keys:
            if len(self._game_keys) < GAME_KEYS:
                self._game_keys.append(root_key)
                self.GK[len(self._game_keys) - 1] = root_key
        CTL[10] = len(self._game_keys)

        # Root moves in python-chess order, scored and sorted like C5's order_moves.
        ROOT, RS = self.ROOT, self.RS
        nroot = len(legal)
        for i, move in enumerate(legal):
            ROOT[i] = core.encode_move(board, move)
        entry = core.tt_probe(self.TK, self.TV, root_key)
        ttm = core.tt_move(entry) if entry >= 0 else 0
        ML = self.MLS[0]
        MS = self.MSS[0]
        ML[:nroot] = ROOT[:nroot]
        core.score_moves(B, O, M, S, ML, MS, nroot, ttm, self.KILL[0], self.KILL[1],
                         self.HIST, self.GAINS)
        order = sorted(range(nroot), key=lambda i: -int(MS[i]))
        root_moves = [int(ROOT[i]) for i in order]

        best_move = root_moves[0]
        best_score = 0
        depth_limit = MAX_DEPTH if max_depth is None else max_depth
        for depth in range(1, depth_limit + 1):
            CTL[5] = 0
            CTL[9] = depth
            score, move, ordered = self._search_root_aspirated(depth, root_moves, best_score)
            if CTL[0]:
                info.aborted = True
                if CTL[5] != 0:
                    best_move = int(CTL[5])
                    best_score = int(CTL[6])
                    info.depth = depth
                break

            previous_move, previous_score = best_move, best_score
            best_move, best_score, root_moves = move, score, ordered
            info.depth = depth

            if abs(best_score) > core.MATE_BOUND:
                break
            if depth > 1 and (
                best_move != previous_move or abs(best_score - previous_score) >= 50
            ):
                info.unstable_iterations += 1
            if max_depth is None and not timer.should_start_iteration():
                break

        if info.depth >= 1 and board.halfmove_clock < core.TT_HALFMOVE_LIMIT:
            core.tt_store(
                self.TK, self.TV, root_key, info.depth, core.score_to_tt(best_score, 0),
                core.BOUND_LOWER if info.aborted else core.BOUND_EXACT, best_move,
            )

        info.score = best_score
        info.nodes = self.nodes = int(CTL[2])
        info.qnodes = self.qnodes = int(CTL[3])
        info.cutoffs = self.cutoffs = int(CTL[4])
        info.researches = self.researches
        info.elapsed_ms = timer.elapsed_ms()
        info.nps = int(info.nodes * 1000.0 / info.elapsed_ms) if info.elapsed_ms > 0 else 0
        info.tt_probes = self.tt.probes = int(CTL[7])
        info.tt_hits = self.tt.hits = int(CTL[8])
        return core.move_to_chess(best_move), info

    def _search_root(
        self, depth: int, root_moves: list[int], alpha: int = -core.INFINITY,
        beta: int = core.INFINITY,
    ) -> tuple[int, int, list[int]]:
        ROOT, RS = self.ROOT, self.RS
        n = len(root_moves)
        for i, move in enumerate(root_moves):
            ROOT[i] = move
        score, move = core.search_root(
            self.B, self.O, self.M, self.S, self.U, self.MLS, self.MSS, self.PATH, self.GK,
            self.TK, self.TV, self.KILL, self.HIST, self.CTL, self.TCTL, self.GAINS,
            ROOT, RS, n, depth, alpha, beta,
        )
        if self.CTL[0]:
            return int(score), int(move), root_moves
        order = sorted(range(n), key=lambda i: -int(RS[i]))
        return int(score), int(move), [root_moves[i] for i in order]

    def _search_root_aspirated(
        self, depth: int, root_moves: list[int], previous: int
    ) -> tuple[int, int, list[int]]:
        if depth < ASPIRATION_MIN_DEPTH or abs(previous) > core.MATE_BOUND:
            return self._search_root(depth, root_moves)
        delta = ASPIRATION_DELTA
        alpha = previous - delta
        beta = previous + delta
        while True:
            score, move, ordered = self._search_root(depth, root_moves, alpha, beta)
            if self.CTL[0]:
                return score, move, root_moves
            if alpha < score < beta:
                return score, move, ordered
            self.researches += 1
            if score <= alpha:
                beta = (alpha + beta) // 2
                alpha = score - delta
            else:
                beta = score + delta
            delta += delta
            if delta > ASPIRATION_MAX_DELTA:
                return self._search_root(depth, root_moves)


def _phase_of(board: chess.Board) -> int:
    phase = (
        (board.knights | board.bishops).bit_count()
        + 2 * board.rooks.bit_count()
        + 4 * board.queens.bit_count()
    )
    return phase if phase < core.TOTAL_PHASE else core.TOTAL_PHASE


def warm_up(verbose: bool = False) -> float:
    """Compile every kernel by running short searches. Returns seconds taken."""
    from time import perf_counter

    global _COMPILED
    if _COMPILED:
        return 0.0
    _COMPILED = True
    started = perf_counter()
    searcher = Searcher()
    for fen, depth in (
        (chess.STARTING_FEN, 4),
        ("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4", 4),
        ("8/2k5/8/8/3P4/8/5K2/8 w - - 0 1", 6),
        ("4k3/8/8/8/8/8/4P3/4K2R w K - 0 1", 5),
        ("q5k1/6R1/8/8/8/8/8/6K1 b - - 98 80", 3),
    ):
        searcher.search(chess.Board(fen), 0, max_depth=depth)
    taken = perf_counter() - started
    if verbose:
        print(f"cs_fast warm-up {taken:.1f}s", file=sys.stderr)
    return taken
