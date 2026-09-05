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
from collections.abc import Iterable
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
from cs_ordering import Heuristics, order_captures, order_moves, staged_moves, update_history
from cs_see import see
from cs_time import CHECK_INTERVAL, TimeManager
from cs_tt import TranspositionTable, score_from_tt, score_to_tt

# Every environment variable this module reads, with its shipping default.
# Populated by _flag() at import, so it cannot drift from the flags that
# actually exist. tools/arena.py builds its sanitisation and provenance list
# from this rather than from a hand-maintained copy, which had already fallen
# one flag behind: CS_SEE_KEEP_CHECKS took effect while matches recorded
# "effective: {}".
DECLARED_FLAGS: dict[str, bool] = {}


def _flag(name: str, default: bool) -> bool:
    """Read an experiment flag from the environment, and register it.

    These exist so a single code base can be run as any of the search variants
    an A/B needs, instead of maintaining hand-edited copies that drift. Every
    default is the shipping behaviour, so an agent started with no environment
    set is the production engine. They are read once at import, never per node.
    """
    DECLARED_FLAGS[name] = default
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"", "0", "false", "no", "off"}


# Registered like any other flag so provenance covers it. Note this also makes
# CLAUDESHARK_DEBUG=0 mean off, where previously any non-empty value was on.
DEBUG = _flag("CLAUDESHARK_DEBUG", False)


USE_PVS = _flag("CS_PVS", True)
USE_NULL_MOVE = _flag("CS_NMP", True)
USE_LMR = _flag("CS_LMR", True)
# Skip reductions on checking moves and en-passant captures.
#
# Measured: on 40 positions (24 quiet, 16 sharp) at fixed depth this changes the
# chosen move in exactly zero of them, and costs 0.6% more nodes at equal depth.
# So this is not an Elo claim -- it is a robustness one. Reducing a forcing move
# is the classic way a selective search walks past a tactic, the failure is rare
# enough that a 40-position suite cannot sample it, and the measured price for
# removing it is negligible. Kept on for that asymmetry, not for a benchmark.
LMR_SAFE = _flag("CS_LMR_SAFE", True)
# What a transposition-table entry may do at a **PV node**. Non-PV nodes always
# take every kind of cutoff; only the wide-window case is in question.
#
#   "all"   every bound cuts -- what v0.2 through v0.5.1 shipped, and the cause
#           of the Qf8 failure documented at the probe site
#   "exact" only an EXACT score cuts; LOWER and UPPER are used for ordering only
#   "none"  no score cutoff at all at PV nodes; the stored move still orders
#
# "exact" is the default: it removes the unsound bounds while keeping the
# information that was actually proven. See benchmarks/current for the
# measurement.
def _policy(name: str, default: str, allowed: tuple[str, ...]) -> str:
    DECLARED_FLAGS.setdefault(name, False)
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}, got {raw!r}")
    return value


TT_PV_POLICY = _policy("CS_TT_PV_POLICY", "exact", ("all", "exact", "none"))


def _int_var(name: str, default: int) -> int:
    """An integer experiment knob, registered like a flag so the arena records it."""
    DECLARED_FLAGS.setdefault(name, False)
    raw = os.environ.get(name)
    if raw is None:
        return default
    return int(raw.strip())


# Late-move reduction schedule. The shipped values are the ones every
# measurement in benchmarks/ was made with; the knobs exist so a variant can
# be run from this code base rather than from an edited copy.
#   LMR_START:     first move index (0-based, after ordering) that may be reduced
#   LMR_R2_INDEX/LMR_R2_DEPTH: from this index at this depth the reduction is 2
#   LMR_R3_INDEX/LMR_R3_DEPTH: the same for a reduction of 3; 0 disables it
LMR_START = _int_var("CS_LMR_START", 3)
LMR_R2_INDEX = _int_var("CS_LMR_R2_INDEX", 6)
LMR_R2_DEPTH = _int_var("CS_LMR_R2_DEPTH", 6)
LMR_R3_INDEX = _int_var("CS_LMR_R3_INDEX", 0)
LMR_R3_DEPTH = _int_var("CS_LMR_R3_DEPTH", 0)

# Backwards compatibility: CS_TT_PV_CUTOFF=0 was the escape hatch that first
# revealed the defect, and existing records refer to it. It still forces "none".
if not _flag("CS_TT_PV_CUTOFF", True):
    TT_PV_POLICY = "none"
# Measured at fixed depth over 24 positions: -2.8% nodes at depth 7, -2.4% at
# depth 8, with 23 of 24 root moves unchanged (the one that moved matched the
# unpruned reference's preference). Small, consistent, and contained.
USE_ASPIRATION = _flag("CS_ASPIRATION", True)

# Static exchange evaluation, in two independent places so each can be measured
# on its own.
#   _QS:    skip captures that lose material outright in quiescence
#   _ORDER: sort losing captures below killers instead of above every quiet move
#
# Measured at fixed depth 6 over 24 positions: quiescence pruning alone is
# -10.3% nodes, ordering alone -5.6%, both -14.9%, and the quiescence share of
# the tree falls from 53% to 47% -- which is the mechanism, since the pruned
# nodes are the recapture subtrees behind losing captures. Both together take
# 16.8% less wall clock at the same depth, so SEE's per-call cost is repaid
# several times over, and they buy +0.41 ply at a 900 ms budget and +0.34 at
# 4500 ms. Move quality is unchanged: 1.5cp average loss before, 1.9cp after,
# zero blunders either way, tactical suite 16/16.
USE_SEE_QS = _flag("CS_SEE_QS", True)
USE_SEE_ORDER = _flag("CS_SEE_ORDER", True)
# Exempt checking captures from SEE pruning in quiescence.
#
# Measured: 20.7% of negative-SEE captures over 4011 samples give check, so the
# exposure is real rather than hypothetical. Enabling costs 1.9% more nodes at
# fixed depth (1,674,285 -> 1,705,479) and leaves the tactical suite at 16/16.
# Like LMR_SAFE this is a robustness argument, not a measured Elo gain: a
# sacrifice that forces a reply is precisely the move a material-only heuristic
# misjudges, and the price for not guessing is small.
SEE_KEEP_CHECKS = _flag("CS_SEE_KEEP_CHECKS", True)
# Staged move generation at interior nodes: the table move, then the captures
# that are not losing, then the killers are produced from masked generation
# before the full legal list is built and sorted. Most interior nodes cut off
# on their first move, so the full sort is usually never paid for. Measured
# 2026-09-05 (benchmarks/current/2026-09-05-c1-staged-move-picker.md): +17%
# nodes per second with 0 of 42 root moves changed at fixed depth, and +59 Elo
# (paired bootstrap +25..+93) over 226 games against rated-v1 at the
# competition clock on the organiser's own start positions.
USE_STAGED_MOVES = _flag("CS_STAGED_MOVES", True)

MAX_DEPTH = 64
# Quiescence is bounded by its own ply counter as well as by delta pruning, so a
# forcing sequence cannot run away in a tactical position.
QS_MAX_PLY = 10
# A capture has to plausibly get within this of alpha to be worth searching.
DELTA_MARGIN = 200

# Aspiration windows. Below ASPIRATION_MIN_DEPTH the iterations are so cheap
# that a re-search costs more than the window saves.
ASPIRATION_MIN_DEPTH = 4
ASPIRATION_DELTA = 30
ASPIRATION_MAX_DELTA = 800

# Above this halfmove clock the transposition table is bypassed for scores,
# because the fifty-move rule can then reach into the subtree and the key does
# not distinguish the counter. 80 leaves a 20-ply margin, comfortably more than
# the depth this engine reaches plus its quiescence tail.
TT_HALFMOVE_LIMIT = 80

_CHECK_MASK = CHECK_INTERVAL - 1
_NULL_MOVE = chess.Move.null()
_QUEEN = chess.QUEEN
_RANK_7 = chess.BB_RANK_7
_RANK_2 = chess.BB_RANK_2


def _see_losing(board: chess.Board, move: chess.Move) -> bool:
    return see(board, move) < 0


def rules_outcome(board: chess.Board, in_check: bool, ply: int) -> int | None:
    """The score the *rules* force on this position, or None if play continues.

    One policy, used identically by `_negamax` and `_quiescence`, because the
    two disagreeing is exactly how this went wrong twice.

    The ordering is the substance:

    * **Checkmate outranks every draw.** A position with an exhausted halfmove
      counter that is also mate is a win, not a draw. An early version got this
      backwards and scored a forced mate as 0.
    * **A claimable fifty-move draw applies even when the side to move is in
      check.** The repair for the bug above over-corrected into `not in_check`,
      which conflates "in check" with "checkmated". Being in check and having a
      legal move does not defeat the claim: python-chess agrees, reporting
      `can_claim_fifty_moves() == True` and a `FIFTY_MOVES` outcome for
      `q5k1/6R1/8/8/8/8/8/6K1 b - - 100 80`, where this engine returned +928.

    * **The threshold is 99, not 100.** The referee ends the game with
      `board.outcome(claim_draw=True)`, which claims through
      `can_claim_fifty_moves()`. That is already true at a halfmove clock of 99
      whenever some legal move does not reset the counter, because the claim may
      be made for the move about to be played. Verified against python-chess:

          clock 98: can_claim=False  outcome=None
          clock 99: can_claim=True   outcome=FIFTY_MOVES
          clock 100: can_claim=True  outcome=FIFTY_MOVES

      A `>= 100` test therefore scores as winning a position the referee has
      already drawn.

    Everything expensive is gated behind `clock >= 99`, which is vanishingly
    rare, so the common path costs one integer comparison.

    Insufficient material needs no mate test: a position that cannot be mated
    by any sequence cannot already be mate.
    """
    if board.halfmove_clock >= 99:
        # Checkmate outranks the claim, and python-chess agrees: is_fifty_moves()
        # is false without a legal move, so a mated position is not a draw.
        if not any(board.generate_legal_moves()):
            return -MATE_SCORE + ply if in_check else DRAW_SCORE
        # Delegated rather than reimplemented: at clock 99 the claim depends on
        # whether a non-zeroing move exists and on the position after it, and
        # getting that subtly wrong is exactly the failure being repaired.
        if board.can_claim_fifty_moves():
            return DRAW_SCORE
    if is_material_draw(board):
        return DRAW_SCORE
    return None


_KNIGHT_ATTACKS = chess.BB_KNIGHT_ATTACKS
_PAWN_ATTACKS = chess.BB_PAWN_ATTACKS


def _has_legal_move(board: chess.Board) -> bool:
    """True if the side to move, **which must not be in check**, has a legal move.

    The quiescence stand-pat exits have to know whether a position is stalemate,
    and ``any(board.generate_legal_moves())`` answers that at the cost of
    python-chess's full generator set-up on every call. Out of check the rule is
    simpler: a piece that is not pinned can go anywhere it attacks, a pinned
    piece is the only one that needs the ray test. So this looks for one move by
    an unpinned knight, slider or pawn, which nearly every position has, and
    falls back to the full generator only when it finds none. The fallback
    keeps it exact: the answer is identical to the generator's on every
    position (tests/test_has_legal_move.py), so the search tree is unchanged.
    """
    us = board.turn
    own = board.occupied_co[us]
    king = board.king(us)
    if king is None:
        return any(board.generate_legal_moves())
    blockers = board._slider_blockers(king)
    free = own & ~blockers
    not_own = ~own
    knights = board.knights & free
    while knights:
        square = knights.bit_length() - 1
        if _KNIGHT_ATTACKS[square] & not_own:
            return True
        knights ^= 1 << square
    pawns = board.pawns & free
    if pawns:
        occupied = board.occupied
        if (pawns << 8 if us else pawns >> 8) & ~occupied:
            return True
        them = board.occupied_co[not us]
        pawn_attacks = _PAWN_ATTACKS[us]
        scan = pawns
        while scan:
            square = scan.bit_length() - 1
            if pawn_attacks[square] & them:
                return True
            scan ^= 1 << square
    sliders = (board.bishops | board.rooks | board.queens) & free
    attacks_mask = board.attacks_mask
    while sliders:
        square = sliders.bit_length() - 1
        if attacks_mask(square) & not_own:
            return True
        sliders ^= 1 << square
    return any(board.generate_legal_moves())


def no_legal_move_score(board: chess.Board, in_check: bool, ply: int) -> int | None:
    """Checkmate or stalemate score, or None if a legal move exists.

    Used at the points that would otherwise return a static evaluation -- the
    quiescence depth cap and the ply ceiling -- because a terminal position must
    never be scored by the evaluator. `any()` stops at the first legal move, so
    only genuinely terminal positions pay for a full generation.
    """
    if any(board.generate_legal_moves()):
        return None
    return -MATE_SCORE + ply if in_check else DRAW_SCORE


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
    unstable_iterations: int = 0
    researches: int = 0
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
        self.researches = 0
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
        max_depth: int | None = None,
    ) -> tuple[chess.Move | None, SearchInfo]:
        """Pick a move.

        ``fixed_budget_ms`` overrides clock-based allocation and ``max_depth``
        stops after a given iteration. Both exist for benchmarking; the agent
        passes neither. A fixed-depth search is deterministic in node count,
        which is what makes it the right instrument for comparing pruning
        changes -- a time-limited search measures the machine as much as the
        engine.
        """
        info = SearchInfo()

        legal = list(board.legal_moves)
        if not legal:
            return None, info

        timer = self.time
        if max_depth is not None:
            # Effectively unlimited, so the depth limit is the only stop.
            timer.begin_fixed(3_600_000.0)
        elif fixed_budget_ms is None:
            timer.begin(time_left_ms, _phase_of(board))
        else:
            timer.begin_fixed(fixed_budget_ms)
        info.budget_ms = timer.soft_ms

        best_move = legal[0]  # legal fallback before any expensive work
        if len(legal) == 1:
            info.depth = 0
            return best_move, info

        self.nodes = 0
        self.qnodes = 0
        self.cutoffs = 0
        self.researches = 0
        self.tt.reset_stats()
        self.heuristics.age()

        root_key = hash(board._transposition_key())
        self._game_counts[root_key] = self._game_counts.get(root_key, 0) + 1
        self._path[0] = root_key

        entry = self.tt.probe(root_key)
        root_moves = order_moves(board, legal, entry[4] if entry else None, 0, self.heuristics)

        best_score = 0

        depth_limit = MAX_DEPTH if max_depth is None else max_depth
        for depth in range(1, depth_limit + 1):
            self._partial_move = None
            try:
                score, move, ordered = self._search_root_aspirated(
                    board, depth, root_moves, best_score
                )
            except SearchAbort:
                info.aborted = True
                # Commit a root move that completed at this depth and beat alpha.
                if self._partial_move is not None:
                    best_move = self._partial_move
                    best_score = self._partial_score
                    info.depth = depth
                break

            previous_move, previous_score = best_move, best_score
            best_move, best_score, root_moves = move, score, ordered
            info.depth = depth

            if abs(best_score) > MATE_BOUND:
                break  # a forced mate is not going to be improved on

            # Recorded as telemetry only. Root instability is a plausible signal
            # for spending more time, but a version that acted on it was removed
            # for want of evidence -- see the note in cs_time.py.
            if depth > 1 and (
                best_move != previous_move or abs(best_score - previous_score) >= 50
            ):
                info.unstable_iterations += 1

            if max_depth is None and not timer.should_start_iteration():
                break

        # An aborted iteration only proves the committed move is at least this
        # good, so it goes in as a lower bound rather than an exact score.
        #
        # Only stored if an iteration actually completed. If depth 1 was aborted
        # before any root move finished, best_move is the untested legal
        # fallback and best_score is a placeholder zero; writing that would
        # poison the table with a fabricated entry that a later transposition
        # could read back as fact.
        #
        # Also gated on the halfmove clock, exactly like the interior stores.
        # This store previously ignored the limit, which left the very
        # contamination path the limit exists to close: a root searched near the
        # fifty-move boundary wrote a rule-influenced score under a key that
        # does not record the counter.
        if info.depth >= 1 and board.halfmove_clock < TT_HALFMOVE_LIMIT:
            self.tt.store(
                root_key,
                info.depth,
                score_to_tt(best_score, 0),
                BOUND_LOWER if info.aborted else BOUND_EXACT,
                best_move,
            )

        info.score = best_score
        info.nodes = self.nodes
        info.qnodes = self.qnodes
        info.cutoffs = self.cutoffs
        info.researches = self.researches
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
        self,
        board: chess.Board,
        depth: int,
        root_moves: list[chess.Move],
        alpha: int = -INFINITY,
        beta: int = INFINITY,
    ) -> tuple[int, chess.Move, list[chess.Move]]:
        # On an aborted iteration the caller may commit the best move found so
        # far. That is only sound for a move whose score genuinely exceeded the
        # window floor: on a fail-low every move returns an upper bound and the
        # maximum of those bounds means nothing.
        #
        # Gating on the *original* alpha rather than on "is this a full window"
        # matters. An earlier version refused every partial from an aspirated
        # iteration, which silently removed a v0.2 behaviour -- committing an
        # improvement found before the clock ran out -- from every iteration at
        # depth 4 and above. Fixed-depth benchmarks cannot see that, because
        # they never run out of time.
        original_alpha = alpha
        best_score = -INFINITY
        best_move = root_moves[0]
        scored: list[tuple[int, chess.Move]] = []

        push = board.push
        pop = board.pop

        for move in root_moves:
            push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, 1)
            pop()

            scored.append((score, move))
            if score > best_score:
                best_score = score
                best_move = move
                if score > original_alpha:
                    self._partial_move = move
                    self._partial_score = score
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        break  # fails high; the caller widens and re-searches

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return best_score, best_move, [pair[1] for pair in scored]

    def _search_root_aspirated(
        self, board: chess.Board, depth: int, root_moves: list[chess.Move], previous: int
    ) -> tuple[int, chess.Move, list[chess.Move]]:
        """Root search inside a narrow window centred on the previous score.

        Most iterations return a score close to the last one, so searching a
        narrow window prunes far more and costs nothing when the guess holds.
        When it does not, the search fails low or high and has to be repeated
        with a wider window -- which is why the window widens geometrically and
        gives up to a full window rather than creeping outward.
        """
        if not USE_ASPIRATION or depth < ASPIRATION_MIN_DEPTH or abs(previous) > MATE_BOUND:
            return self._search_root(board, depth, root_moves)

        delta = ASPIRATION_DELTA
        alpha = previous - delta
        beta = previous + delta

        while True:
            score, move, ordered = self._search_root(board, depth, root_moves, alpha, beta)
            if alpha < score < beta:
                return score, move, ordered

            self.researches += 1
            if score <= alpha:
                # Fail low: the position is worse than we thought. Drop alpha and
                # relax beta toward the middle so the re-search is not immediately
                # a fail high as well.
                beta = (alpha + beta) // 2
                alpha = score - delta
            else:
                beta = score + delta

            delta += delta
            if delta > ASPIRATION_MAX_DELTA:
                return self._search_root(board, depth, root_moves)

    # ------------------------------------------------------------------ tree

    def _negamax(
        self,
        board: chess.Board,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
        allow_null: bool = True,
    ) -> int:
        self.nodes += 1
        if not (self.nodes & _CHECK_MASK) and self.time.hard_expired():
            raise SearchAbort

        # Rules-forced outcomes, before anything expensive. is_check() is only
        # paid on the vanishingly rare nodes where the counter is near its limit.
        forced = rules_outcome(
            board, board.halfmove_clock >= 99 and board.is_check(), ply
        )
        if forced is not None:
            return forced

        key = hash(board._transposition_key())

        # Repetition. This is a **heuristic, not the FIDE rule**, and the
        # distinction matters: FIDE draws on the third occurrence of a position,
        # while this scores a draw on the second -- once it reappears on the
        # current line, or once it reappears having already been a position the
        # engine was asked about this game.
        #
        # That is the usual engine convention, on the reasoning that a position
        # reachable twice can generally be forced to a third. The failure mode
        # is real though: a winning line whose only path revisits an earlier
        # position gets scored 0 and avoided. See tests/test_repetition.py,
        # which documents the behaviour rather than asserting a rule.
        #
        # Only same-side-to-move plies can repeat, hence the stride of two.
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

        # The transposition key describes the placement, side to move, castling
        # rights and en-passant square -- but not the fifty-move counter. Two
        # positions identical in every other way, one at clock 5 and one at
        # clock 96, share a key, and their true scores differ because one of
        # them is about to be drawn by rule.
        #
        # Demonstrated, not theoretical: searching a won rook endgame at clock
        # 96 and then the same position at clock 0 through the same table
        # returned 0 instead of +542.
        #
        # Putting the counter in the key would make every clock value a
        # separate entry and gut the hit rate. Instead the table is bypassed
        # entirely -- no score cutoff, no store -- once the counter is high
        # enough for the rule to reach into the subtree. Below the limit the
        # rule cannot fire within any depth this engine searches, so entries
        # made there are clean; above it, nothing is written and nothing stale
        # is trusted. The stored move is still used for ordering, which cannot
        # be unsound.
        tt_usable = board.halfmove_clock < TT_HALFMOVE_LIMIT

        tt = self.tt
        tt.probes += 1
        entry = tt.probe(key)
        tt_move: chess.Move | None = None
        if entry is not None:
            tt.hits += 1
            _, entry_depth, entry_score, entry_bound, tt_move = entry
            if not tt_usable:
                entry_depth = -1  # keep the move for ordering, discard the score
            # The stored move is always usable for ordering. The stored *score*
            # is a different matter, and the rule differs by node type.
            #
            # At a **non-PV node** the window is null, so every bound is
            # actionable and all three kinds cut.
            #
            # At a **PV node** only an EXACT score may cut. A LOWER or UPPER
            # bound is a statement about some *other* window, and acting on it
            # here is what produced this engine's worst known tactical failure:
            #
            #   1r4k1/5p1p/5PpQ/3Bp3/2Pb4/qP3R2/7P/7K b - - 0 1
            #
            # Qf8 is the only move that holds (Stockfish 18, 4M nodes: -26 cp,
            # WDL 6/945/49; every alternative loses, second best -586). The
            # search played Qa1+ at -939 instead, at every depth from 6 to 10.
            #
            # The mechanism is a fail-high cascade between aspiration and the
            # table. Each aspiration re-search widens the root window, the Qf8
            # child fails high against its own beta, a LOWER bound is stored at
            # that value, and the next re-search reads it back and returns a
            # still larger number. The score chased the window upward -- 7, 31,
            # 100, 212, 464, 939 -- so the root concluded its only saving move
            # was its worst. EXACT entries in the same subtree were correct
            # throughout; only the bound entries lied.
            #
            # Restricting PV cutoffs to EXACT keeps the genuinely valuable
            # information -- a score proven inside a real window at sufficient
            # depth -- and discards only the bounds that were never proven here.
            if entry_depth >= depth:
                non_pv = beta - alpha == 1
                score = score_from_tt(entry_score, ply)
                if entry_bound == BOUND_EXACT:
                    if non_pv or TT_PV_POLICY != "none":
                        return score
                elif non_pv or TT_PV_POLICY == "all":
                    if entry_bound == BOUND_LOWER:
                        if score >= beta:
                            return score
                    elif score <= alpha:
                        return score

        if depth <= 0:
            return self._quiescence(board, alpha, beta, ply, 0)

        if ply >= MAX_PLY - 2:
            # Same rule as the quiescence cap: a static score must never
            # pre-empt a terminal position, even at the ply ceiling.
            terminal = no_legal_move_score(board, board.is_check(), ply)
            return terminal if terminal is not None else evaluate(board)

        in_check = board.is_check()

        # Null-move pruning: hand the opponent a free move and see whether the
        # position still fails high. If it does, the real move list will too, so
        # the whole subtree can be skipped. Restricted to non-PV nodes, and
        # disabled in check and when the side to move has only pawns, because
        # that is where zugzwang makes "passing" a bad assumption.
        if (
            USE_NULL_MOVE
            and allow_null
            and not in_check
            and depth >= 3
            and beta - alpha == 1
            and board.occupied_co[board.turn] & ~(board.pawns | board.kings)
        ):
            reduction = 3 if depth > 6 else 2
            push_null = board.push
            push_null(_NULL_MOVE)
            # allow_null=False: the child searches a null window, so it would
            # otherwise satisfy the non-PV condition and pass again immediately.
            # Two nulls in a row means neither side has moved, which proves
            # nothing about the position and wastes the subtree. Measured before
            # the fix: 1125 lines containing consecutive nulls at depth 10.
            null_score = -self._negamax(
                board, depth - 1 - reduction, -beta, -beta + 1, ply + 1, False
            )
            board.pop()
            if null_score >= beta:
                # A mate score proved by a null move is not a real mate.
                return beta if null_score > MATE_BOUND else null_score

        see_losing = _see_losing if USE_SEE_ORDER else None
        moves: Iterable[chess.Move]
        if USE_STAGED_MOVES and not (
            board.pawns & board.occupied_co[board.turn] & (_RANK_7 if board.turn else _RANK_2)
        ):
            # Lazy: the head of the ordering comes from masked generation and
            # the full list is only built if the search asks for the tail. A
            # side with a pawn on its seventh rank has promotions, whose
            # ordering the picker does not reproduce, so it takes the sort.
            moves = staged_moves(board, tt_move, ply, self.heuristics, see_losing)
        else:
            legal = list(board.legal_moves)
            if not legal:
                # Mate scores count from the root so that shorter mates score
                # higher.
                return -MATE_SCORE + ply if in_check else DRAW_SCORE
            moves = order_moves(board, legal, tt_move, ply, self.heuristics, see_losing)

        original_alpha = alpha
        best_score = -INFINITY
        best_move: chess.Move | None = None
        push = board.push
        pop = board.pop
        child_depth = depth - 1
        child_ply = ply + 1

        them = board.occupied_co[not board.turn]
        ep_square = board.ep_square
        pawns = board.pawns
        killers = self.heuristics.killers
        killer_index = ply * 2
        killer_a = killers[killer_index]
        killer_b = killers[killer_index + 1]
        can_reduce = USE_LMR and depth >= 3 and not in_check
        move_index = -1

        for move_index, move in enumerate(moves):
            # Late move reductions: ordering already put the plausible moves
            # first, so a quiet move this far down the list is searched
            # shallower on the assumption it will not beat alpha. If it does
            # anyway, it is re-searched at full depth, so the reduction costs
            # accuracy only when it was right to be sceptical.
            #
            # Decided before the push so the pre-move board can be inspected;
            # the one test that needs the post-move board (does this move give
            # check?) happens just after it.
            reduction = 0
            if (
                move_index >= LMR_START
                and can_reduce
                and not (1 << move.to_square) & them
                and not move.promotion
                and move != killer_a
                and move != killer_b
                and not (
                    LMR_SAFE
                    # An en-passant capture leaves the target square empty, so
                    # the plain occupancy test above calls it a quiet move.
                    and move.to_square == ep_square
                    and (1 << move.from_square) & pawns
                )
            ):
                if LMR_R3_INDEX and move_index >= LMR_R3_INDEX and depth >= LMR_R3_DEPTH:
                    reduction = 3
                elif move_index >= LMR_R2_INDEX and depth >= LMR_R2_DEPTH:
                    reduction = 2
                else:
                    reduction = 1
                if reduction > child_depth - 1:
                    reduction = child_depth - 1

            push(move)

            # A move that gives check is forcing, and reducing it is how a
            # selective search walks into tactics. board.is_check() here asks
            # whether the side now to move -- the opponent -- is in check.
            if reduction and LMR_SAFE and board.is_check():
                reduction = 0

            if move_index == 0:
                score = -self._negamax(board, child_depth, -beta, -alpha, child_ply)
            elif USE_PVS:
                # Principal variation search: every move after the first gets a
                # null-window probe, which is much cheaper than a full window.
                score = -self._negamax(
                    board, child_depth - reduction, -alpha - 1, -alpha, child_ply
                )
                if reduction and score > alpha:
                    score = -self._negamax(board, child_depth, -alpha - 1, -alpha, child_ply)
                if alpha < score < beta:
                    score = -self._negamax(board, child_depth, -beta, -alpha, child_ply)
            else:
                score = -self._negamax(
                    board, child_depth - reduction, -beta, -alpha, child_ply
                )
                if reduction and score > alpha:
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

        if move_index < 0:
            # The staged picker produced nothing: no legal move exists.
            return -MATE_SCORE + ply if in_check else DRAW_SCORE

        if best_score >= beta:
            bound = BOUND_LOWER
        elif best_score > original_alpha:
            bound = BOUND_EXACT
        else:
            bound = BOUND_UPPER
        if tt_usable:
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

        in_check = board.is_check()

        # Rules first, before any cap, stand-pat or static exit can pre-empt
        # them. See rules_outcome() for why the ordering is what it is.
        forced = rules_outcome(board, in_check, ply)
        if forced is not None:
            return forced

        at_cap = qply >= QS_MAX_PLY or ply >= MAX_PLY - 2

        if in_check:
            # No stand-pat while in check: the position is not quiet by
            # definition and every evasion has to be considered.
            moves = list(board.legal_moves)
            if not moves:
                return -MATE_SCORE + ply
            if at_cap:
                return evaluate(board)
            moves = order_captures(board, moves)
            best_score = -INFINITY
            stand_pat = -INFINITY
        else:
            if at_cap:
                # The cap used to return a static score without ever asking
                # whether the position was terminal, so a stalemate reached at
                # exactly qply == QS_MAX_PLY scored -990 while the same position
                # one ply earlier scored 0.
                terminal = no_legal_move_score(board, in_check, ply)
                if terminal is not None:
                    return terminal
                return evaluate(board)

            stand_pat = evaluate(board)

            # Both exits below return a static score, and both are wrong if the
            # position is stalemate. `_has_legal_move` finds one move by an
            # unpinned piece without python-chess's generator set-up, and only
            # a position with none pays for the full generation. An earlier
            # attempt hoisted the full capture list above the beta cutoff
            # instead, which was also correct but cost 30% of nodes/second,
            # because listing every capture is far dearer than finding one
            # legal move.
            if stand_pat >= beta:
                if _has_legal_move(board):
                    return stand_pat
                return DRAW_SCORE
            if stand_pat > alpha:
                alpha = stand_pat
            best_score = stand_pat
            moves = _tactical_moves(board)
            if not moves:
                if _has_legal_move(board):
                    return stand_pat
                return DRAW_SCORE
            moves = order_captures(board, moves)

        piece_type_at = board.piece_type_at
        push = board.push
        pop = board.pop
        child_ply = ply + 1
        child_qply = qply + 1

        for move in moves:
            losing_capture = False
            if not in_check:
                # Delta pruning: if winning the target piece outright still
                # leaves us far below alpha, the capture cannot rescue the node.
                victim = piece_type_at(move.to_square)
                gain = PIECE_VALUE[victim] if victim else PIECE_VALUE[chess.PAWN]
                if move.promotion == _QUEEN:
                    gain += PIECE_VALUE[_QUEEN]
                if stand_pat + gain + DELTA_MARGIN < alpha:
                    continue
                # A capture that loses material outright is very rarely the
                # move that rescues a quiescence node, and each one drags a
                # whole recapture subtree behind it.
                losing_capture = USE_SEE_QS and see(board, move) < 0
                if losing_capture and not SEE_KEEP_CHECKS:
                    continue

            push(move)
            # Measured: 20.7% of negative-SEE captures give check. A sacrifice
            # that forces a reply is exactly the move a material heuristic
            # misjudges, so SEE_KEEP_CHECKS searches it anyway. is_check() is
            # only reached for captures SEE already condemned, so the cost falls
            # on a small minority of moves.
            if losing_capture and not board.is_check():
                pop()
                continue
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
