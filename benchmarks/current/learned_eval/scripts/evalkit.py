"""Evaluator-agnostic move scoring for the pairwise tests.

`qsearch` is RC-J's compiled quiescence (cs_core.py:1164-1260) with the transposition table,
clock and repetition bookkeeping removed and the leaf evaluation made switchable: E0 is
cs_core.evaluate, E1 adds the learned correction. Both evaluators therefore see exactly the
same capture generation, ordering, delta pruning and SEE pruning, and differ only at the leaves.

A move's value is from the mover's point of view: minus the child's static evaluation, and minus
the child's quiescence value.
"""
import chess
import numpy as np
from numba import njit

import features as F

C = F.C
INF = C.INFINITY


@njit(cache=False)
def leaf_eval(B, S, W, use_w):
    e = C.evaluate(B, S)
    if use_w:
        e += np.int64(np.rint(F.correction(B, S[0], W)))
    return e


@njit(cache=False)
def qsearch(B, O, M, S, U, MLS, MSS, GAINS, W, use_w, alpha, beta, ply, qply):
    ML = MLS[ply]
    MS = MSS[ply]
    checked = C.in_check(B, O, S)
    at_cap = qply >= C.QS_MAX_PLY or ply >= C.MAX_PLY - 2
    if checked:
        n = C.gen_moves(B, O, M, S, ML, False)
        legal = 0
        for i in range(n):
            C.make_move(B, O, M, S, U, ML[i])
            ok = C.is_legal_after_make(B, O, S)
            C.unmake_move(B, O, M, S, U)
            if ok:
                ML[legal] = ML[i]
                legal += 1
        n = legal
        if n == 0:
            return -C.MATE_SCORE + ply
        if at_cap:
            return leaf_eval(B, S, W, use_w)
        C.score_captures(M, ML, MS, n)
        best = -INF
        stand = -INF
    else:
        if at_cap:
            if not C.has_legal_move(B, O, M, S, U, ML):
                return 0
            return leaf_eval(B, S, W, use_w)
        stand = leaf_eval(B, S, W, use_w)
        if stand >= beta:
            if C.has_legal_move(B, O, M, S, U, ML):
                return stand
            return 0
        if stand > alpha:
            alpha = stand
        best = stand
        n = C.gen_moves(B, O, M, S, ML, True)
        if n == 0:
            if C.has_legal_move(B, O, M, S, U, ML):
                return stand
            return 0
        C.score_captures(M, ML, MS, n)
    searched = 0
    for i in range(n):
        move = C.pick_next(ML, MS, n, i)
        losing = False
        if not checked:
            to = (move >> 6) & 63
            victim = M[to]
            vt = victim if victim <= 6 else victim - 6
            gain = C.PIECE_VALUE[vt] if victim else C.PIECE_VALUE[1]
            if ((move >> 12) & 7) == 5:
                gain += C.PIECE_VALUE[5]
            if stand + gain + C.DELTA_MARGIN < alpha:
                continue
            losing = C.see(B, O, M, S, move, GAINS) < 0
        C.make_move(B, O, M, S, U, move)
        if not C.is_legal_after_make(B, O, S):
            C.unmake_move(B, O, M, S, U)
            continue
        searched += 1
        if losing and not C.in_check(B, O, S):
            C.unmake_move(B, O, M, S, U)
            continue
        score = -qsearch(B, O, M, S, U, MLS, MSS, GAINS, W, use_w, -beta, -alpha, ply + 1, qply + 1)
        C.unmake_move(B, O, M, S, U)
        if score > best:
            best = score
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    break
    if searched == 0 and not checked:
        if not C.has_legal_move(B, O, M, S, U, ML):
            return 0
    return best


@njit(cache=False)
def _values(B, O, M, S, U, MLS, MSS, GAINS, W, moves, out):
    for i in range(moves.shape[0]):
        C.make_move(B, O, M, S, U, moves[i])
        s0 = C.evaluate(B, S)
        s1 = s0 + np.int64(np.rint(F.correction(B, S[0], W)))
        q0 = qsearch(B, O, M, S, U, MLS, MSS, GAINS, W, False, -INF, INF, 1, 0)
        q1 = qsearch(B, O, M, S, U, MLS, MSS, GAINS, W, True, -INF, INF, 1, 0)
        C.unmake_move(B, O, M, S, U)
        out[i, 0] = -s0
        out[i, 1] = -s1
        out[i, 2] = -q0
        out[i, 3] = -q1


class Scorer:
    """Scores candidate moves of a root position under E0 and E1 (weights W)."""

    def __init__(self, W):
        self.W = np.asarray(W, dtype=np.float64)
        self.B, self.O, self.M, self.S, self.U = C.new_board_arrays()
        self.MLS = np.zeros((C.STACK, C.MAX_MOVES), dtype=np.int64)
        self.MSS = np.zeros((C.STACK, C.MAX_MOVES), dtype=np.int64)
        self.GAINS = np.zeros(40, dtype=np.int64)

    def values(self, board, ucis):
        """-> {uci: dict(static0, static1, qs0, qs1)} from the mover's view. A move that ends
        the game is scored by the rules for every evaluator (mate +30000, stalemate 0)."""
        C.load_board(board, self.B, self.O, self.M, self.S)
        moves = np.array([C.encode_move(board, chess.Move.from_uci(u)) for u in ucis], dtype=np.int64)
        out = np.zeros((len(ucis), 4), dtype=np.int64)
        _values(self.B, self.O, self.M, self.S, self.U, self.MLS, self.MSS, self.GAINS, self.W, moves, out)
        res = {}
        for u, row in zip(ucis, out):
            child = board.copy(stack=False)
            child.push_uci(u)
            if child.is_checkmate():
                row = np.array([C.MATE_SCORE] * 4)
            elif child.is_stalemate():
                row = np.zeros(4, dtype=np.int64)
            res[u] = dict(static0=int(row[0]), static1=int(row[1]), qs0=int(row[2]), qs1=int(row[3]))
        return res
