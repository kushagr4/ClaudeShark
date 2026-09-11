"""Offline compiled N1 scoring over RC-J's board arrays, for the pairwise and quiescence-resolved
tests only (never inside the engine, which uses the incremental accumulator of engine_n1.py).

`qs_nn` is RC-J's quiescence (same structure as evalkit.qsearch: capture generation, ordering,
delta and SEE pruning) with a switchable leaf: mode 0 = E0, 1 = E0 + float N1, 2 = E0 + N1q.
"""
import chess
import numpy as np
from numba import njit

import features as F
import nn1

C = F.C
INF = C.INFINITY


@njit(cache=False)
def _acc_q(B, W1, b1):
    acc = np.zeros((2, W1.shape[1]), dtype=np.int64)
    _fill(B, W1, b1, acc)
    return acc


@njit(cache=False)
def _acc_f(B, W1, b1):
    acc = np.zeros((2, W1.shape[1]), dtype=np.float64)
    _fill(B, W1, b1, acc)
    return acc


@njit(cache=False)
def _fill(B, W1, b1, acc):
    for p in range(2):
        for k in range(W1.shape[1]):
            acc[p, k] = b1[k]
    for c in range(1, 13):
        bb = B[c]
        col = 0 if c <= 6 else 1
        t = c - 1 - 6 * col
        while bb:
            sq = C.lsb(bb)
            bb &= bb - 1
            for p in range(2):
                idx = (0 if col == p else 384) + t * 64 + (sq if p == 0 else sq ^ 56)
                for k in range(W1.shape[1]):
                    acc[p, k] += W1[idx, k]


@njit(cache=False)
def nnq_cp(B, stm, W1q, b1q, W2q, b2q, w3q, b3q):
    acc = _acc_q(B, W1q, b1q)
    h1 = np.zeros(256, dtype=np.int64)
    for k in range(128):
        a = acc[stm, k]
        h1[k] = 0 if a < 0 else (255 if a > 255 else a)
        a = acc[1 - stm, k]
        h1[128 + k] = 0 if a < 0 else (255 if a > 255 else a)
    out = np.int64(b3q[0])
    for j in range(32):
        z = np.int64(b2q[j])
        for i in range(256):
            z += h1[i] * np.int64(W2q[j, i])
        h = z // 64
        h = 0 if h < 0 else (255 if h > 255 else h)
        out += h * np.int64(w3q[j])
    num = 100 * out
    q = (num if num >= 0 else -num) // 16320
    return q if num >= 0 else -q


@njit(cache=False)
def nnf_cp(B, stm, W1, b1, W2, b2, w3, b3):
    acc = _acc_f(B, W1, b1)
    h1 = np.zeros(256, dtype=np.float64)
    for k in range(128):
        h1[k] = min(max(acc[stm, k], 0.0), 1.0)
        h1[128 + k] = min(max(acc[1 - stm, k], 0.0), 1.0)
    out = np.float64(b3[0])
    for j in range(32):
        z = np.float64(b2[j])
        for i in range(256):
            z += h1[i] * W2[j, i]
        out += min(max(z, 0.0), 1.0) * w3[j]
    return 100.0 * out


@njit(cache=False)
def leaf(B, S, mode, FP, QP):
    e = C.evaluate(B, S)
    if mode == 1:
        e += np.int64(nnf_cp(B, S[0], FP[0], FP[1], FP[2], FP[3], FP[4], FP[5]))
    elif mode == 2:
        e += nnq_cp(B, S[0], QP[0], QP[1], QP[2], QP[3], QP[4], QP[5])
    return e


@njit(cache=False)
def qs_nn(B, O, M, S, U, MLS, MSS, GAINS, mode, FP, QP, alpha, beta, ply, qply):
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
            return leaf(B, S, mode, FP, QP)
        C.score_captures(M, ML, MS, n)
        best = -INF
        stand = -INF
    else:
        if at_cap:
            if not C.has_legal_move(B, O, M, S, U, ML):
                return 0
            return leaf(B, S, mode, FP, QP)
        stand = leaf(B, S, mode, FP, QP)
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
        score = -qs_nn(B, O, M, S, U, MLS, MSS, GAINS, mode, FP, QP, -beta, -alpha, ply + 1, qply + 1)
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


def params(fl=None, Q=None):
    """Numba argument tuples; unused sets get tiny dummies of the right dtype."""
    if fl is None:
        FP = (np.zeros((768, 128), np.float32), np.zeros(128, np.float32), np.zeros((32, 256), np.float32),
              np.zeros(32, np.float32), np.zeros(32, np.float32), np.zeros(1, np.float32))
    else:
        FP = (fl["W1"].astype(np.float32), fl["b1"].astype(np.float32), fl["W2"].astype(np.float32),
              fl["b2"].astype(np.float32), fl["w3"].astype(np.float32), np.array([fl["b3"]], np.float32).reshape(1))
    if Q is None:
        QP = (np.zeros((768, 128), np.int16), np.zeros(128, np.int32), np.zeros((32, 256), np.int8),
              np.zeros(32, np.int32), np.zeros(32, np.int32), np.zeros(1, np.int64))
    else:
        QP = (Q["W1q"], Q["b1q"], Q["W2q"], Q["b2q"], Q["w3q"], Q["b3q"])
    return FP, QP


class NNScorer:
    """Static and quiescence-resolved values under E0 (mode 0), float N1 (1) or N1q (2)."""

    def __init__(self, fl=None, Q=None):
        self.FP, self.QP = params(fl, Q)
        self.B, self.O, self.M, self.S, self.U = C.new_board_arrays()
        self.MLS = np.zeros((C.STACK, C.MAX_MOVES), dtype=np.int64)
        self.MSS = np.zeros((C.STACK, C.MAX_MOVES), dtype=np.int64)
        self.GAINS = np.zeros(40, dtype=np.int64)

    def root(self, board, mode):
        """(static, quiescence) score of the position itself, side to move's view."""
        C.load_board(board, self.B, self.O, self.M, self.S)
        st = int(leaf(self.B, self.S, mode, self.FP, self.QP))
        q = int(qs_nn(self.B, self.O, self.M, self.S, self.U, self.MLS, self.MSS, self.GAINS, mode,
                      self.FP, self.QP, -INF, INF, 0, 0))
        return st, q

    def moves(self, board, ucis, mode):
        """{uci: (static, quiescence)} from the mover's view; game-ending moves by the rules."""
        res = {}
        for u in ucis:
            child = board.copy(stack=False)
            child.push_uci(u)
            if child.is_checkmate():
                res[u] = (C.MATE_SCORE, C.MATE_SCORE)
            elif child.is_stalemate():
                res[u] = (0, 0)
            else:
                st, q = self.root(child, mode)
                res[u] = (-st, -q)
        return res
