"""Stage-wise Stockfish annotation of the diagnostic games.

Every position in every game is scored once at a cheap node budget. Any move
whose centipawn loss at that budget is at least ``--refine-at`` is then
re-scored -- both the position before it and the position after it -- at a
deeper budget, so the turning points that drive the conclusions rest on the
better number while the bulk of quiet moves do not pay for it.

Centipawn loss of a move is ``best_cp_before - cp_after`` from the mover's
side, using the deeper of the two budgets wherever it was computed.

Terminal positions are scored locally: the oracle returns no line for a
position with no legal moves, and the outcome is known anyway. Parallelism is
the oracle module's thread pool -- one engine per thread -- because a process
pool on Windows is an order of magnitude slower for this job, which is how the
first version of this script ran for ten hours.

    uv run python -m tools.postmortem.annotate --games <jsonl> --out <jsonl>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess

from tools.corpus.oracle import MATE_CP, label_many


def terminal_label(board: chess.Board) -> dict | None:
    """Score a position with no legal moves without asking the oracle."""
    if board.is_checkmate():
        # Side to move is mated: worst score for them, from white's view.
        cp_white = -MATE_CP if board.turn == chess.WHITE else MATE_CP
        return {"cp_white": cp_white, "best": None, "mate": 0, "nodes": 0, "wdl_white": None}
    if not any(board.legal_moves) or board.is_insufficient_material():
        return {"cp_white": 0, "best": None, "mate": None, "nodes": 0, "wdl_white": None}
    return None


def score(fens: list[str], nodes: int, workers: int) -> dict[str, dict]:
    labels: dict[str, dict] = {}
    todo: list[str] = []
    for fen in fens:
        t = terminal_label(chess.Board(fen))
        if t is not None:
            labels[fen] = t
        else:
            todo.append(fen)
    print(f"  {len(fens)} positions: {len(fens) - len(todo)} terminal, {len(todo)} to the oracle at {nodes} nodes", flush=True)
    for fen, label in zip(todo, label_many(todo, nodes, workers=workers, progress=True), strict=True):
        labels[fen] = {
            "cp_white": label.cp_white, "best": label.best, "mate": label.mate, "nodes": nodes,
            "wdl_white": list(label.wdl_white) if label.wdl_white else None,
        }
    return labels


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cheap", type=int, default=200_000)
    parser.add_argument("--deep", type=int, default=1_000_000)
    parser.add_argument("--refine-at", type=int, default=50)
    parser.add_argument("--workers", type=int, default=8)
    arguments = parser.parse_args()

    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    fens: set[str] = set()
    for g in games:
        for m in g["moves"]:
            fens.add(m["fen"])
        fens.add(g["final_fen"])
    fen_list = sorted(fens)
    print(f"{len(games)} games; cheap pass", flush=True)
    labels = score(fen_list, arguments.cheap, arguments.workers)

    def cp_for(fen: str, white: bool) -> int:
        cp = labels[fen]["cp_white"]
        return cp if white else -cp

    # Deep pass: before/after any move whose cheap-pass loss reaches the
    # threshold, plus the last two moves of every game so the final mistake of
    # a decisive game is always refined.
    refine: set[str] = set()
    for g in games:
        ms = g["moves"]
        for i, m in enumerate(ms):
            after = ms[i + 1]["fen"] if i + 1 < len(ms) else g["final_fen"]
            white = m["turn"] == "w"
            loss = cp_for(m["fen"], white) - cp_for(after, white)
            if loss >= arguments.refine_at or i >= len(ms) - 2:
                refine.add(m["fen"])
                refine.add(after)
    print("deep pass", flush=True)
    labels.update(score(sorted(refine), arguments.deep, arguments.workers))

    with arguments.out.open("w", encoding="utf-8") as fh:
        for g in games:
            ms = g["moves"]
            for i, m in enumerate(ms):
                after = ms[i + 1]["fen"] if i + 1 < len(ms) else g["final_fen"]
                white = m["turn"] == "w"
                m["sf_cp_white_before"] = labels[m["fen"]]["cp_white"]
                m["sf_cp_white_after"] = labels[after]["cp_white"]
                m["sf_best"] = labels[m["fen"]]["best"]
                m["sf_nodes"] = labels[m["fen"]]["nodes"]
                m["cp_loss"] = max(0, cp_for(m["fen"], white) - cp_for(after, white))
                m["sf_wdl_white_before"] = labels[m["fen"]]["wdl_white"]
            g["sf_final_cp_white"] = labels[g["final_fen"]]["cp_white"]
            fh.write(json.dumps(g) + "\n")
    print(f"annotated games written to {arguments.out}")


if __name__ == "__main__":
    main()
