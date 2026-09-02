"""Exact decomposition of the production evaluator into tunable components.

For every labelled position this extracts the pieces the evaluator is built
from -- material counts, raw piece-square sums, bishop pair, tempo, phase -- and
proves that recombining them with the production constants reproduces
`cs_eval.evaluate` to the centipawn on every position. Nothing downstream is
trusted until that proof passes, because a tuner that fits a *reconstruction*
of the evaluator rather than the evaluator itself would be tuning the wrong
function.

Also extracted, for the quiet-subset and hanging-piece diagnoses: the engine's
own depth-1 (quiescence-resolved) and depth-3 scores, whether the side to move
is in check, whether the oracle's best move is a capture or promotion, and the
oracle's gap between its best and second-best lines.

Everything is cached to an .npz keyed on the labelled file, so the expensive
part runs once.

    uv run python -m tools.tune.features --labelled corpus/candidates_labelled.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import chess
import numpy as np

from cs_constants import (
    _EG_TABLES,
    _EG_VALUE,
    _MG_TABLES,
    _MG_VALUE,
    BISHOP_PAIR_EG,
    BISHOP_PAIR_MG,
    TEMPO,
    TOTAL_PHASE,
)
from cs_eval import evaluate
from tools.corpus.eval_residuals import FEATURES, feature_vector

PIECES = (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
PIECE_NAMES = ("pawn", "knight", "bishop", "rook", "queen")

MG_VALUE = np.array([_MG_VALUE[p] for p in PIECES], dtype=float)
EG_VALUE = np.array([_EG_VALUE[p] for p in PIECES], dtype=float)

CACHE_DIR = Path("corpus/tune")


def _raw_pst_sums(board: chess.Board) -> tuple[np.ndarray, np.ndarray]:
    """Piece-square sums per piece type from the *raw* PeSTO tables.

    White reads the printed table at ``sq ^ 56``, black at ``sq``, exactly as
    `cs_constants._build` does, but without the material value folded in.
    The king is included as a sixth entry so its PST is accounted for.
    """
    mg = np.zeros(6)
    eg = np.zeros(6)
    for index, piece in enumerate((*PIECES, chess.KING)):
        mg_table = _MG_TABLES[piece]
        eg_table = _EG_TABLES[piece]
        assert mg_table is not None and eg_table is not None
        for square in board.pieces(piece, chess.WHITE):
            mg[index] += mg_table[square ^ 56]
            eg[index] += eg_table[square ^ 56]
        for square in board.pieces(piece, chess.BLACK):
            mg[index] -= mg_table[square]
            eg[index] -= eg_table[square]
    return mg, eg


def decompose(board: chess.Board) -> dict[str, np.ndarray | int | float]:
    counts = np.array(
        [len(board.pieces(p, chess.WHITE)) - len(board.pieces(p, chess.BLACK)) for p in PIECES],
        dtype=float,
    )
    pst_mg, pst_eg = _raw_pst_sums(board)
    pair = int(len(board.pieces(chess.BISHOP, chess.WHITE)) > 1) - int(
        len(board.pieces(chess.BISHOP, chess.BLACK)) > 1
    )
    phase = min(
        TOTAL_PHASE,
        chess.popcount(board.knights | board.bishops)
        + 2 * chess.popcount(board.rooks)
        + 4 * chess.popcount(board.queens),
    )
    stm = 1 if board.turn == chess.WHITE else -1
    return {
        "counts": counts,
        "pst_mg": pst_mg,
        "pst_eg": pst_eg,
        "pair": pair,
        "phase": phase,
        "stm": stm,
    }


def reconstruct_white_pov(
    counts: np.ndarray,
    pst_mg: np.ndarray,
    pst_eg: np.ndarray,
    pair: int,
    phase: int,
    stm: int,
    mg_value: np.ndarray = MG_VALUE,
    eg_value: np.ndarray = EG_VALUE,
    exact: bool = True,
) -> float:
    """Recombine components with the production formula, white's point of view.

    ``exact=True`` reproduces the integer truncation the engine performs;
    ``exact=False`` is the continuous form used for fitting (differs by < 1 cp).
    """
    mg_total = float(counts @ mg_value) + float(pst_mg.sum()) + pair * BISHOP_PAIR_MG
    eg_total = float(counts @ eg_value) + float(pst_eg.sum()) + pair * BISHOP_PAIR_EG
    total = mg_total * phase + eg_total * (TOTAL_PHASE - phase)
    if exact:
        t = round(total)
        score = t // TOTAL_PHASE if t >= 0 else -((-t) // TOTAL_PHASE)
    else:
        score = total / TOTAL_PHASE
    return score + stm * TEMPO


def engine_depth_scores(fen: str, depths: tuple[int, ...]) -> list[int]:
    """Engine scores at fixed depths, white POV, fresh searcher each time."""
    from cs_search import Searcher

    board = chess.Board(fen)
    sign = 1 if board.turn == chess.WHITE else -1
    out = []
    for depth in depths:
        _, info = Searcher(tt_bits=16).search(chess.Board(fen), 0, max_depth=depth)
        out.append(sign * info.score)
    return out


def build(labelled: Path, depths: tuple[int, ...] = (1, 3), limit: int = 0) -> Path:
    rows = []
    with labelled.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record") == "header":
                continue
            rows.append(record)
    if limit:
        rows = rows[:limit]

    n = len(rows)
    counts = np.zeros((n, 5))
    pst_mg = np.zeros((n, 6))
    pst_eg = np.zeros((n, 6))
    pair = np.zeros(n)
    phase = np.zeros(n)
    stm = np.zeros(n)
    static = np.zeros(n)
    recon = np.zeros(n)
    depth_scores = np.zeros((n, len(depths)))
    oracle_cp = np.zeros(n)
    oracle_es = np.zeros(n)  # expected score from WDL, white POV
    mate = np.zeros(n, dtype=bool)
    in_check = np.zeros(n, dtype=bool)
    best_capture = np.zeros(n, dtype=bool)
    gap = np.zeros(n)
    hanging = np.zeros(n)  # white minus black hanging pieces, from the residual tool
    residual_feats = np.zeros((n, 2 * len(FEATURES)))
    game_ids: list[str] = []
    fens: list[str] = []
    families: list[str] = []
    tags: list[str] = []
    mismatches = 0

    for index, row in enumerate(rows):
        board = chess.Board(row["fen"])
        parts = decompose(board)
        counts[index] = parts["counts"]
        pst_mg[index] = parts["pst_mg"]
        pst_eg[index] = parts["pst_eg"]
        pair[index] = parts["pair"]
        phase[index] = parts["phase"]
        stm[index] = parts["stm"]

        sign = parts["stm"]
        static[index] = sign * evaluate(board)
        recon[index] = reconstruct_white_pov(
            parts["counts"], parts["pst_mg"], parts["pst_eg"], parts["pair"],
            parts["phase"], parts["stm"], exact=True,
        )
        if int(static[index]) != int(recon[index]):
            mismatches += 1
            if mismatches <= 3:
                print(f"MISMATCH {row['fen']} static={static[index]} recon={recon[index]}")

        depth_scores[index] = engine_depth_scores(row["fen"], depths)

        ref = row["reference"]
        oracle_cp[index] = ref["cp_white"]
        w, d, _l = ref["wdl_white"]
        oracle_es[index] = (w + d / 2.0) / 1000.0
        mate[index] = ref.get("mate") is not None
        in_check[index] = board.is_check()
        best = chess.Move.from_uci(ref["best"])
        best_capture[index] = board.is_capture(best) or best.promotion is not None
        gap[index] = ref.get("second_gap_cp", 0) or 0
        vec, _ = feature_vector(board)
        residual_feats[index] = vec
        hanging[index] = vec[FEATURES.index("hanging_pieces")] + vec[
            len(FEATURES) + FEATURES.index("hanging_pieces")
        ]

        game_ids.append(row["game_id"])
        fens.append(row["fen"])
        families.append(row.get("family", ""))
        tags.append("|".join(row["structure"]["tags"]))
        if (index + 1) % 500 == 0:
            print(f"  {index + 1}/{n}", flush=True)

    print(f"equivalence: {n - mismatches}/{n} positions reproduce evaluate() exactly")
    if mismatches:
        raise SystemExit("decomposition does not reproduce the evaluator; refusing to cache")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = CACHE_DIR / f"{labelled.stem}.features.npz"
    np.savez_compressed(
        out,
        counts=counts, pst_mg=pst_mg, pst_eg=pst_eg, pair=pair, phase=phase, stm=stm,
        static=static, depth_scores=depth_scores, depths=np.array(depths),
        oracle_cp=oracle_cp, oracle_es=oracle_es, mate=mate, in_check=in_check,
        best_capture=best_capture, gap=gap, hanging=hanging,
        residual_feats=residual_feats, residual_names=np.array(FEATURES),
        game_ids=np.array(game_ids), fens=np.array(fens), families=np.array(families),
        tags=np.array(tags),
    )
    print(f"cached {n} positions to {out}")
    return out


def load(labelled: Path) -> dict[str, np.ndarray]:
    path = CACHE_DIR / f"{labelled.stem}.features.npz"
    if not path.exists():
        raise SystemExit(f"{path} missing; run tools.tune.features first")
    data = np.load(path, allow_pickle=False)
    return {k: data[k] for k in data.files}


def main() -> None:
    parser = argparse.ArgumentParser(description="Decompose the evaluator over a labelled pool.")
    parser.add_argument("--labelled", type=Path, default=Path("corpus/candidates_labelled.jsonl"))
    parser.add_argument("--depths", type=int, nargs="+", default=[1, 3])
    parser.add_argument("--limit", type=int, default=0)
    arguments = parser.parse_args()
    build(arguments.labelled, tuple(arguments.depths), arguments.limit)


if __name__ == "__main__":
    sys.exit(main())
