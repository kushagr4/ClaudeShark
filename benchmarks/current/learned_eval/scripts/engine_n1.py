"""Build scratch copies of RC-J with incremental N1 inference (DESIGN_N1.md section 10).

Never touches the repository's runtime files. Every build differs from RC-J only by:
  * `make_move` also records the moved piece in the unused `U[ply, 7]`;
  * `evaluate(B, S)` becomes `evaluate(B, S, U, NNA, NNK)`;
  * `NNA` (int32, N1_ROWS x 256) and `NNK` (int64, STACK) are threaded through search_root /
    negamax / quiescence and allocated by cs_fast.Searcher;
  * `search_root` seeds the accumulator at ply 0 (one rebuild per root search), so every lazy
    catch-up ends at a valid row and search never rebuilds from the bitboards otherwise.
NNA rows: 0..STACK-1 per-ply accumulators; STACK activations scratch; STACK+1 counters
(0 evaluate calls, 1 rebuilds, 2 catch-up steps, 3 shadow sink, 4 verify mismatches, 5 audit
samples, 6 audit stride, 7 root seeds); STACK+2 verify scratch; STACK+3.. audit samples.
Expected in search: rebuilds == root seeds (no rebuild other than the root seed).

Modes:
  real          evaluate = E0 + N1q                         (the candidate)
  shadow_cost   N1q computed and stored, evaluate = E0      (per-node cost on RC-J's identical tree)
  shadow_verify N1q computed, the incremental row compared with a rebuild at every call, evaluate = E0
  audit         real, plus every 64th evaluate call's position sampled for the magnitude audit

    python engine_n1.py OUT_DIR WEIGHTS.npz MODE          (zero weights: WEIGHTS = --zero)
"""
import os
import re
import shutil
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
RUNTIME = ["agent.py"] + sorted(f for f in os.listdir(ROOT) if f.startswith("cs_") and f.endswith(".py"))
AUDIT_SAMPLES = 20000
AUDIT_STRIDE = 64

MAKE_OLD = "    flags = move >> 15\n    piece = M[fr]\n    key = S[4] ^ ep_key_term(B, S)\n"
MAKE_NEW = "    flags = move >> 15\n    piece = M[fr]\n    U[ply, 7] = piece\n    key = S[4] ^ ep_key_term(B, S)\n"
ROOT_OLD = "    best_move = ROOT[0]\n    PATH[0] = S[4]\n"
ROOT_NEW = "    best_move = ROOT[0]\n    PATH[0] = S[4]\n    n1_seed_root(B, S, NNA, NNK)\n"
EVAL_TAIL_OLD = "    if S[0] == 0:\n        return score + TEMPO\n    return -score + TEMPO\n"
EVAL_TAILS = {
    "real": "    nn = n1_eval(B, S, U, NNA, NNK)\n    if S[0] == 0:\n        return score + TEMPO + nn\n"
            "    return -score + TEMPO + nn\n",
    "audit": "    nn = n1_eval(B, S, U, NNA, NNK)\n    n1_audit(B, S, NNA, nn, score)\n    if S[0] == 0:\n"
             "        return score + TEMPO + nn\n    return -score + TEMPO + nn\n",
    "shadow_cost": "    NNA[N1_CTRL, 3] = n1_eval(B, S, U, NNA, NNK)\n    if S[0] == 0:\n        return score + TEMPO\n"
                   "    return -score + TEMPO\n",
    "shadow_verify": "    n1_eval(B, S, U, NNA, NNK)\n    n1_verify(B, S, NNA)\n    if S[0] == 0:\n"
                     "        return score + TEMPO\n    return -score + TEMPO\n",
}
FAST_ALLOC_OLD = "        self.GAINS = np.zeros(40, dtype=np.int64)\n"
FAST_ALLOC_NEW = ("        self.GAINS = np.zeros(40, dtype=np.int64)\n"
                  "        self.NNA = np.zeros((core.N1_ROWS, 256), dtype=np.int32)\n"
                  "        self.NNK = np.zeros(core.STACK, dtype=np.int64)\n")

N1_RUNTIME = '''

# ---- N1 incremental evaluation (scratch build, DESIGN_N1.md section 10) ----
import os as _n1_os

_n1_z = np.load(_n1_os.path.join(_n1_os.path.dirname(_n1_os.path.abspath(__file__)), "n1_weights.npz"))
N1_W1 = np.ascontiguousarray(_n1_z["W1q"])
N1_B1 = np.ascontiguousarray(_n1_z["b1q"])
N1_W2 = np.ascontiguousarray(_n1_z["W2q"])
N1_B2 = np.ascontiguousarray(_n1_z["b2q"])
N1_W3 = np.ascontiguousarray(_n1_z["w3q"])
N1_B3 = int(_n1_z["b3q"][0])
N1_SCRATCH = STACK
N1_CTRL = STACK + 1
N1_VERIFY = STACK + 2
N1_AUDIT0 = STACK + 3
N1_AUDIT_N = __AUDIT_N__
N1_AUDIT_STRIDE = __AUDIT_STRIDE__
N1_ROWS = STACK + 3 + N1_AUDIT_N


@njit(cache=False)
def n1_add(NNA, row, c, sq, sign):
    col = 0 if c <= 6 else 1
    t = c - 1 - 6 * col
    iw = (0 if col == 0 else 384) + t * 64 + sq
    ib = (0 if col == 1 else 384) + t * 64 + (sq ^ 56)
    if sign > 0:
        for k in range(128):
            NNA[row, k] += N1_W1[iw, k]
        for k in range(128):
            NNA[row, 128 + k] += N1_W1[ib, k]
    else:
        for k in range(128):
            NNA[row, k] -= N1_W1[iw, k]
        for k in range(128):
            NNA[row, 128 + k] -= N1_W1[ib, k]


@njit(cache=False)
def n1_rebuild(B, NNA, row):
    for k in range(128):
        NNA[row, k] = N1_B1[k]
        NNA[row, 128 + k] = N1_B1[k]
    for c in range(1, 13):
        bb = B[c]
        while bb:
            sq = lsb(bb)
            bb &= bb - 1
            n1_add(NNA, row, c, sq, 1)


@njit(cache=False)
def n1_refresh(B, NNA, row):
    n1_rebuild(B, NNA, row)
    NNA[N1_CTRL, 1] += 1


@njit(cache=False)
def n1_seed_root(B, S, NNA, NNK):
    NNA[N1_CTRL, 7] += 1
    n1_refresh(B, NNA, S[6])
    NNK[S[6]] = S[4]


@njit(cache=False)
def n1_apply(U, NNA, i):
    """Row i from row i - 1 through the move recorded at U[i - 1]."""
    NNA[N1_CTRL, 2] += 1
    for k in range(256):
        NNA[i, k] = NNA[i - 1, k]
    move = U[i - 1, 6]
    if move == 0:
        return
    fr = move & 63
    to = (move >> 6) & 63
    promo = (move >> 12) & 7
    flags = move >> 15
    piece = U[i - 1, 7]
    captured = U[i - 1, 0]
    side = 0 if piece <= 6 else 1
    n1_add(NNA, i, piece, fr, -1)
    n1_add(NNA, i, promo + 6 * side if promo else piece, to, 1)
    if captured:
        if flags & FLAG_EP:
            cap_sq = to - 8 if side == 0 else to + 8
        else:
            cap_sq = to
        n1_add(NNA, i, captured, cap_sq, -1)
    if flags & FLAG_CASTLE:
        if to == 6:
            rf, rt = 7, 5
        elif to == 2:
            rf, rt = 0, 3
        elif to == 62:
            rf, rt = 63, 61
        else:
            rf, rt = 56, 59
        rook = 4 + 6 * side
        n1_add(NNA, i, rook, rf, -1)
        n1_add(NNA, i, rook, rt, 1)


@njit(cache=False)
def n1_ensure(B, S, U, NNA, NNK):
    ply = S[6]
    if NNK[ply] == S[4]:
        return ply
    j = ply - 1
    while j >= 0 and NNK[j] != U[j, 4]:
        j -= 1
    if j < 0:
        n1_refresh(B, NNA, ply)
    else:
        for i in range(j + 1, ply + 1):
            n1_apply(U, NNA, i)
            if i < ply:
                NNK[i] = U[i, 4]
    NNK[ply] = S[4]
    return ply


@njit(cache=False)
def n1_eval(B, S, U, NNA, NNK):
    NNA[N1_CTRL, 0] += 1
    row = n1_ensure(B, S, U, NNA, NNK)
    so = 128 * S[0]
    oo = 128 - so
    sc = N1_SCRATCH
    for k in range(128):
        a = NNA[row, so + k]
        NNA[sc, k] = 0 if a < 0 else (255 if a > 255 else a)
        a = NNA[row, oo + k]
        NNA[sc, 128 + k] = 0 if a < 0 else (255 if a > 255 else a)
    out = np.int64(N1_B3)
    for j in range(32):
        z = np.int32(0)
        for i in range(256):
            z += NNA[sc, i] * np.int32(N1_W2[j, i])
        z += N1_B2[j]
        h = z // 64
        if h < 0:
            h = 0
        elif h > 255:
            h = 255
        out += np.int64(h) * N1_W3[j]
    num = 100 * out
    q = (num if num >= 0 else -num) // 16320
    return q if num >= 0 else -q


@njit(cache=False)
def n1_verify(B, S, NNA):
    n1_rebuild(B, NNA, N1_VERIFY)
    ply = S[6]
    for k in range(256):
        if NNA[ply, k] != NNA[N1_VERIFY, k]:
            NNA[N1_CTRL, 4] += 1
            return


@njit(cache=False)
def n1_audit(B, S, NNA, nn, white_score):
    NNA[N1_CTRL, 6] += 1
    if NNA[N1_CTRL, 6] % N1_AUDIT_STRIDE != 0 or NNA[N1_CTRL, 5] >= N1_AUDIT_N:
        return
    r = N1_AUDIT0 + NNA[N1_CTRL, 5]
    NNA[N1_CTRL, 5] += 1
    for c in range(1, 13):
        b = B[c]
        NNA[r, 2 * c] = np.int32(b & 0xFFFFFFFF)
        NNA[r, 2 * c + 1] = np.int32(b >> 32)
    NNA[r, 0] = S[0]
    NNA[r, 1] = nn
    NNA[r, 26] = white_score
    NNA[r, 27] = S[1]
    NNA[r, 28] = S[2]
    NNA[r, 29] = S[3]
'''


def zero_weights():
    return dict(W1q=np.zeros((768, 128), np.int16), b1q=np.zeros(128, np.int32), W2q=np.zeros((32, 256), np.int8),
                b2q=np.zeros(32, np.int32), w3q=np.zeros(32, np.int32), b3q=np.zeros(1, np.int64))


def build(dst, Q, mode="real"):
    assert mode in EVAL_TAILS
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in RUNTIME:
        shutil.copy2(os.path.join(ROOT, f), os.path.join(dst, f))
    core = open(os.path.join(dst, "cs_core.py"), encoding="utf-8").read().replace("\r\n", "\n")
    assert core.count(MAKE_OLD) == 1 and core.count(ROOT_OLD) == 1
    core = core.replace(MAKE_OLD, MAKE_NEW).replace(ROOT_OLD, ROOT_NEW)
    assert core.count("def evaluate(B, S):") == 1 and core.count(EVAL_TAIL_OLD) == 1
    core = core.replace("def evaluate(B, S):", "def evaluate(B, S, U, NNA, NNK):").replace(EVAL_TAIL_OLD, EVAL_TAILS[mode])
    n_calls = core.count("evaluate(B, S)")
    assert n_calls == 5, n_calls
    core = core.replace("evaluate(B, S)", "evaluate(B, S, U, NNA, NNK)")
    core, n_thread = re.subn(r"TCTL,(\s*)GAINS,", r"TCTL,\1GAINS, NNA, NNK,", core)
    assert n_thread == 11, n_thread
    core += N1_RUNTIME.replace("__AUDIT_N__", str(AUDIT_SAMPLES if mode == "audit" else 0)).replace(
        "__AUDIT_STRIDE__", str(AUDIT_STRIDE))
    with open(os.path.join(dst, "cs_core.py"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(core)
    fast = open(os.path.join(dst, "cs_fast.py"), encoding="utf-8").read().replace("\r\n", "\n")
    assert fast.count(FAST_ALLOC_OLD) == 1 and fast.count("self.TCTL, self.GAINS,") == 1
    fast = fast.replace(FAST_ALLOC_OLD, FAST_ALLOC_NEW).replace(
        "self.TCTL, self.GAINS,", "self.TCTL, self.GAINS, self.NNA, self.NNK,")
    with open(os.path.join(dst, "cs_fast.py"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(fast)
    np.savez(os.path.join(dst, "n1_weights.npz"), **Q)
    return dict(mode=mode, evaluate_calls=n_calls, threaded=n_thread)


if __name__ == "__main__":
    out, wpath, mode = sys.argv[1], sys.argv[2], sys.argv[3]
    if wpath == "--zero":
        Q = zero_weights()
    else:
        z = np.load(wpath)
        Q = {k: z[k] for k in ("W1q", "b1q", "W2q", "b2q", "w3q", "b3q")}
    print(build(out, Q, mode))
