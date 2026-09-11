"""Exact make/unmake correctness of the incremental N1 accumulator (DESIGN_N1.md section 10).

Runs inside a process whose cs_core is the scratch N1 engine (engine dir first on sys.path):

    python test_n1_engine.py ENGINE_DIR POOL.jsonl [--walks 250] [--steps 40] [--out result.json]

Random legal walks from pool positions and special positions, biased so that en passant,
castling (both sides, both colours), promotions (including underpromotions), captures, king moves
and null moves all occur; random unmakes; evaluation requested at random plies so multi-ply
lazy catch-up is exercised. After every evaluated transition:
  * the incremental accumulator row equals a fresh rebuild from the bitboards, exactly;
  * the compiled N1q correction equals the offline numpy forward pass (nn1.quant_forward_cp), exactly.
"""
import argparse
import collections
import json
import os
import random
import sys

ap = argparse.ArgumentParser()
ap.add_argument("engine")
ap.add_argument("pool")
ap.add_argument("--walks", type=int, default=250)
ap.add_argument("--steps", type=int, default=40)
ap.add_argument("--out")
a = ap.parse_args()
sys.path.insert(0, os.path.abspath(a.engine))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import chess  # noqa: E402
import numpy as np  # noqa: E402
import cs_core as C  # noqa: E402
import nn1  # noqa: E402

assert os.path.dirname(os.path.abspath(C.__file__)) == os.path.abspath(a.engine), C.__file__
z = np.load(os.path.join(a.engine, "n1_weights.npz"))
Q = {k: z[k] for k in ("W1q", "b1q", "W2q", "b2q", "w3q", "b3q")}

SPECIAL = [
    "r3k2r/pppq1ppp/2npbn2/4p3/4P3/2NPBN2/PPPQ1PPP/R3K2R w KQkq - 0 1",
    "r3k2r/pppq1ppp/2npbn2/4p3/4P3/2NPBN2/PPPQ1PPP/R3K2R b KQkq - 0 1",
    "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
    "rnbqkbnr/pp1ppppp/8/8/2pPP3/8/PPP2PPP/RNBQKBNR b KQkq d3 0 3",
    "8/P1P3kp/8/8/8/8/1p3p1K/8 w - - 0 1",
    "8/P1P3kp/8/8/8/8/1p3p1K/8 b - - 0 1",
    "1n2k3/P7/8/8/8/8/7p/4K1N1 w - - 0 1",
    "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",
    "r3k2r/8/8/8/8/8/8/4K3 b kq - 0 1",
    "4k3/8/8/2PpP3/8/8/8/4K3 w - d6 0 1",
    "4k3/8/8/8/1pPp4/8/8/4K3 b - c3 0 1",
    "rnbqkb1r/ppp1pppp/5n2/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3",
    "rnbqkbnr/pppp1ppp/8/8/3Pp3/5N2/PPP1PPPP/RNBQKB1R b KQkq d3 0 3",
]


def classify(board, mv):
    cats = []
    if board.is_en_passant(mv):
        cats.append("en_passant")
    if board.is_castling(mv):
        side = "white" if board.turn else "black"
        cats.append(f"castle_{'king' if board.is_kingside_castling(mv) else 'queen'}side_{side}")
    if mv.promotion:
        cats.append("promotion_" + chess.piece_name(mv.promotion))
        if board.is_capture(mv):
            cats.append("promotion_capture")
    if board.is_capture(mv):
        cats.append("capture")
    if board.piece_type_at(mv.from_square) == chess.KING:
        cats.append("king_move")
    return cats


def main():
    rng = random.Random(20260911)
    pool = [json.loads(l)["fen"] for l in open(a.pool, encoding="utf-8")]
    rng.shuffle(pool)
    starts = SPECIAL * 6 + pool[: a.walks]
    B, O, M, S, U = C.new_board_arrays()
    NNA = np.zeros((C.N1_ROWS, 256), dtype=np.int32)
    NNK = np.zeros(C.STACK, dtype=np.int64)
    REF = np.zeros((C.N1_ROWS, 256), dtype=np.int32)
    counts = collections.Counter()
    fails = []

    def check(board, tag):
        ply = int(S[6])
        before = NNK.copy()
        v = int(C.n1_eval(B, S, U, NNA, NNK))
        caught_up = int(sum(1 for i in range(ply + 1) if NNK[i] != before[i]))
        counts["evaluations"] += 1
        if caught_up > 1:
            counts["multi_ply_catch_up"] += 1
        C.n1_rebuild(B, REF, 0)
        if not np.array_equal(NNA[ply], REF[0]):
            fails.append(dict(kind="accumulator", fen=board.fen(), tag=tag))
        s_idx, o_idx = nn1.board_features(board)
        ref = nn1.quant_forward_cp(s_idx, o_idx, Q)
        if v != ref:
            fails.append(dict(kind="eval", fen=board.fen(), tag=tag, engine=v, reference=ref))
        full = int(C.evaluate(B, S, U, NNA, NNK))
        counts["full_evaluate_calls"] += 1
        return full

    for fen in starts:
        board = chess.Board(fen)
        C.load_board(board, B, O, M, S)
        kinds = []  # engine op per ply: "m" move, "n" null
        check(board, "root")
        for _ in range(a.steps):
            legal = list(board.legal_moves)
            r = rng.random()
            if kinds and r < 0.15:
                k = kinds.pop()
                if k == "n":
                    C.unmake_null(B, O, M, S, U)
                else:
                    C.unmake_move(B, O, M, S, U)
                board.pop()
                counts["unmake"] += 1
                tag = "unmake"
            elif not legal or int(S[6]) >= C.STACK - 4:
                break
            elif r < 0.20 and not board.is_check() and kinds[-1:] != ["n"]:
                C.make_null(B, O, M, S, U)
                board.push(chess.Move.null())
                kinds.append("n")
                counts["null_move"] += 1
                tag = "null"
            else:
                special = [m for m in legal if board.is_en_passant(m) or board.is_castling(m) or m.promotion]
                caps = [m for m in legal if board.is_capture(m)]
                if special and rng.random() < 0.6:
                    mv = rng.choice(special)
                elif caps and rng.random() < 0.35:
                    mv = rng.choice(caps)
                else:
                    mv = rng.choice(legal)
                for c in classify(board, mv):
                    counts[c] += 1
                C.make_move(B, O, M, S, U, C.encode_move(board, mv))
                board.push(mv)
                kinds.append("m")
                counts["moves"] += 1
                tag = mv.uci()
            counts["transitions"] += 1
            if rng.random() < 0.5:
                check(board, tag)
    res = dict(engine=os.path.abspath(a.engine), counts=dict(sorted(counts.items())), failures=len(fails),
               first_failures=fails[:10], passed=not fails)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))
    sys.exit(0 if not fails else 1)


main()
