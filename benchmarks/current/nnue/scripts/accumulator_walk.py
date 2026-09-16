"""Exact make/unmake correctness of the engine's incremental NNUE accumulator.

Runs in a process started with CS_NNUE=1, so cs_core has the N1-U weights loaded. Random legal
walks, from hand-written special positions and from seeded random playouts, are biased so that en
passant, castling on both sides for both colours, promotions (underpromotions included), captures,
king moves and null moves all occur, with random unmakes and evaluations requested at random plies
(so the multi-ply lazy catch-up is exercised). After every evaluated transition:

  * the incremental accumulator row equals a from-scratch rebuild from the bitboards, exactly;
  * the compiled correction ``n1_eval`` equals an independent numpy forward pass, exactly;
  * ``evaluate_search`` equals ``evaluate`` plus that correction.

    CS_NNUE=1 python accumulator_walk.py [--walks 400] [--steps 40] [--seed 20260916]
                                         [--out result.json]

Exit status 0 when every check held.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import chess  # noqa: E402
import numpy as np  # noqa: E402

import cs_core as C  # noqa: E402, N812 (the learned_eval scripts' name)

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


def reference_cp(board: chess.Board, weights: dict) -> int:
    """N1-U's quantised forward pass written independently of the engine (numpy, int64)."""
    white, black = [], []
    for sq, piece in board.piece_map().items():
        t = piece.piece_type - 1
        white.append((0 if piece.color == chess.WHITE else 384) + t * 64 + sq)
        black.append((0 if piece.color == chess.BLACK else 384) + t * 64 + (sq ^ 56))
    stm, opp = (white, black) if board.turn == chess.WHITE else (black, white)
    w1 = weights["W1q"].astype(np.int64)
    b1 = weights["b1q"].astype(np.int64)
    h1 = np.clip(np.concatenate([b1 + w1[stm].sum(0), b1 + w1[opp].sum(0)]), 0, 255)
    h2 = np.clip(
        (weights["b2q"].astype(np.int64) + weights["W2q"].astype(np.int64) @ h1) // 64, 0, 255
    )
    out = int(weights["b3q"][0]) + int((weights["w3q"].astype(np.int64) * h2).sum())
    q = abs(100 * out) // 16320
    return q if out >= 0 else -q


def classify(board: chess.Board, mv: chess.Move) -> list[str]:
    cats = []
    if board.is_en_passant(mv):
        cats.append("en_passant")
    if board.is_castling(mv):
        side = "white" if board.turn else "black"
        cats.append(f"castle_{'king' if board.is_kingside_castling(mv) else 'queen'}side_{side}")
    if mv.promotion:
        cats.append("promotion_" + chess.piece_name(mv.promotion))
    if board.is_capture(mv):
        cats.append("capture")
    if board.piece_type_at(mv.from_square) == chess.KING:
        cats.append("king_move")
    return cats


def playout_starts(n: int, rng: random.Random) -> list[str]:
    out = []
    while len(out) < n:
        b = chess.Board()
        for _ in range(rng.randint(6, 70)):
            legal = list(b.legal_moves)
            if not legal:
                break
            b.push(rng.choice(legal))
        if not b.is_game_over(claim_draw=False):
            out.append(b.fen())
    return out


def run(walks: int, steps: int, seed: int) -> dict:
    assert C.NNUE_ENABLED, "run with CS_NNUE=1"
    with np.load(os.environ.get("CS_NNUE_WEIGHTS", "") or C.NNUE_WEIGHTS_DEFAULT) as z:
        weights = {k: z[k] for k in ("W1q", "b1q", "W2q", "b2q", "w3q", "b3q")}
    rng = random.Random(seed)
    starts = SPECIAL * 6 + playout_starts(walks, rng)
    B, O, M, S, U = C.new_board_arrays()  # noqa: N806, E741 (cs_core's board-array names)
    NNA = np.zeros((C.N1_ROWS, 256), dtype=np.int32)  # noqa: N806
    NNK = np.zeros(C.STACK, dtype=np.int64)  # noqa: N806
    REF = np.zeros((C.N1_ROWS, 256), dtype=np.int32)  # noqa: N806
    counts: collections.Counter[str] = collections.Counter()
    fails: list[dict] = []

    def check(board: chess.Board, tag: str) -> None:
        ply = int(S[6])
        before = NNK.copy()
        got = int(C.n1_eval(B, S, U, NNA, NNK))
        if sum(1 for i in range(ply + 1) if NNK[i] != before[i]) > 1:
            counts["multi_ply_catch_up"] += 1
        counts["evaluations"] += 1
        C.n1_rebuild(B, REF, 0)
        if not np.array_equal(NNA[ply], REF[0]):
            fails.append(dict(kind="accumulator", fen=board.fen(), tag=tag))
        want = reference_cp(board, weights)
        if got != want:
            fails.append(
                dict(kind="correction", fen=board.fen(), tag=tag, engine=got, reference=want)
            )
        full = int(C.evaluate_search(B, S, U, NNA, NNK))
        if full != int(C.evaluate(B, S)) + want:
            fails.append(
                dict(
                    kind="evaluate_search",
                    fen=board.fen(),
                    tag=tag,
                    engine=full,
                    expected=int(C.evaluate(B, S)) + want,
                )
            )

    for fen in starts:
        board = chess.Board(fen)
        C.load_board(board, B, O, M, S)
        kinds: list[str] = []
        check(board, "root")
        for _ in range(steps):
            legal = list(board.legal_moves)
            r = rng.random()
            if kinds and r < 0.15:
                if kinds.pop() == "n":
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
                special = [
                    m
                    for m in legal
                    if board.is_en_passant(m) or board.is_castling(m) or m.promotion
                ]
                captures = [m for m in legal if board.is_capture(m)]
                if special and rng.random() < 0.6:
                    mv = rng.choice(special)
                elif captures and rng.random() < 0.35:
                    mv = rng.choice(captures)
                else:
                    mv = rng.choice(legal)
                counts.update(classify(board, mv))
                C.make_move(B, O, M, S, U, C.encode_move(board, mv))
                board.push(mv)
                kinds.append("m")
                counts["moves"] += 1
                tag = mv.uci()
            counts["transitions"] += 1
            if rng.random() < 0.5:
                check(board, tag)
    return dict(
        walks=walks,
        steps=steps,
        seed=seed,
        starts=len(starts),
        counts=dict(sorted(counts.items())),
        failures=len(fails),
        first_failures=fails[:10],
        passed=not fails,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--walks", type=int, default=400)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260916)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    res = run(a.walks, a.steps, a.seed)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
    print(json.dumps(res))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
