"""N1 reference implementation (DESIGN_N1.md sections 5 and 8): feature indices, quantisation and
exact numpy forward passes. Depends only on numpy and python-chess, so the engine correctness test
can import it inside a process whose cs_core is the incremental engine under test.

Feature index for perspective p (0 = White's view, 1 = Black's view) of a piece of type t (1..6):
    (0 if the piece belongs to p else 384) + (t - 1) * 64 + (square if p == 0 else square ^ 56)
The side to move's perspective comes first in the head input, so the network is colour-symmetric.
"""
import json

import chess
import numpy as np

N_IN, N_ACC, N_H2 = 768, 128, 32
PAD = N_IN  # padding index (an all-zero embedding row) for batched training
QA, QB = 255, 64
OUT_DEN = QA * QB


def feature_index(persp, piece_is_white, ptype, sq):
    own = piece_is_white == (persp == 0)
    return (0 if own else 384) + (ptype - 1) * 64 + (sq if persp == 0 else sq ^ 56)


def board_features(board):
    """-> (side-to-move perspective indices, opponent perspective indices)."""
    w, b = [], []
    for sq, pc in board.piece_map().items():
        w.append(feature_index(0, pc.color, pc.piece_type, sq))
        b.append(feature_index(1, pc.color, pc.piece_type, sq))
    return (w, b) if board.turn == chess.WHITE else (b, w)


def batch_features(boards):
    xs = np.full((len(boards), 32), PAD, dtype=np.int64)
    xo = np.full((len(boards), 32), PAD, dtype=np.int64)
    for i, bd in enumerate(boards):
        s, o = board_features(bd)
        xs[i, :len(s)] = s
        xo[i, :len(o)] = o
    return xs, xo


def quantise(fl):
    """Float parameters {W1 (768,128), b1 (128), W2 (32,256), b2 (32), w3 (32), b3 ()} -> int arrays."""
    return dict(
        W1q=np.clip(np.rint(fl["W1"] * QA), -32767, 32767).astype(np.int16),
        b1q=np.rint(fl["b1"] * QA).astype(np.int32),
        W2q=np.clip(np.rint(fl["W2"] * QB), -127, 127).astype(np.int8),
        b2q=np.rint(fl["b2"] * QA * QB).astype(np.int32),
        w3q=np.rint(fl["w3"] * QB).astype(np.int32),
        b3q=np.array([np.rint(float(fl["b3"]) * QA * QB)], dtype=np.int64),
    )


def trunc_div(num, den):
    q = abs(num) // den
    return q if num >= 0 else -q


def quant_forward_cp(stm_idx, opp_idx, Q):
    """Exact integer forward pass of N1q; returns the correction in centipawns (side to move)."""
    a_s = Q["b1q"].astype(np.int64) + Q["W1q"][list(stm_idx)].astype(np.int64).sum(0)
    a_o = Q["b1q"].astype(np.int64) + Q["W1q"][list(opp_idx)].astype(np.int64).sum(0)
    h1 = np.clip(np.concatenate([a_s, a_o]), 0, QA)
    z2 = Q["b2q"].astype(np.int64) + Q["W2q"].astype(np.int64) @ h1
    h2 = np.clip(z2 // QB, 0, QA)
    out = int(Q["b3q"][0]) + int((Q["w3q"].astype(np.int64) * h2).sum())
    return trunc_div(100 * out, OUT_DEN)


def float_forward_cp(stm_idx, opp_idx, fl):
    a_s = fl["b1"] + fl["W1"][list(stm_idx)].sum(0)
    a_o = fl["b1"] + fl["W1"][list(opp_idx)].sum(0)
    h1 = np.clip(np.concatenate([a_s, a_o]), 0.0, 1.0)
    h2 = np.clip(fl["W2"] @ h1 + fl["b2"], 0.0, 1.0)
    return 100.0 * (float(fl["w3"] @ h2) + float(fl["b3"]))


def save(path, fl, Q, meta):
    np.savez(path, **{k: v for k, v in fl.items()}, **Q)
    with open(str(path).replace(".npz", ".json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)


def load(path):
    z = np.load(path)
    fl = {k: z[k] for k in ("W1", "b1", "W2", "b2", "w3", "b3")}
    Q = {k: z[k] for k in ("W1q", "b1q", "W2q", "b2q", "w3q", "b3q")}
    return fl, Q
