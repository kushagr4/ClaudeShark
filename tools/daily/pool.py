"""Build a competition-like start pool: near-level opening positions with Black to move.

Every competition start position observed so far -- the two rated games and the
two smoke games in the submission's own build log -- is an opening position
after White's sixth to eighth move, with **Black to move**, and Stockfish
scores all four within 40 centipawns of level. This module generates a larger
pool with the same profile so that "does ClaudeShark do badly as White from
these" can be asked with more than four positions.

Lines are grown by asking the oracle for its top moves and choosing at random
among those within ``--spread`` centipawns of the best, which produces varied
but sane openings without shipping or consulting a book. A candidate is kept
when it is Black to move, the full-move number is in range, and the deep score
is within ``--level`` centipawns of zero.

The oracle is used offline to label positions, which the competition permits;
nothing generated here is shipped inside the submission.

    uv run python -m tools.daily.pool --count 60 --out corpus/daily/pool/competition_like_pairs.json
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--min-move", type=int, default=6)
    parser.add_argument("--max-move", type=int, default=9)
    parser.add_argument("--level", type=int, default=40, help="keep |cp(white)| <= this")
    parser.add_argument("--spread", type=int, default=35, help="random choice among moves within this of best")
    parser.add_argument("--multipv", type=int, default=5)
    parser.add_argument("--walk-nodes", type=int, default=150_000)
    parser.add_argument("--score-nodes", type=int, default=2_000_000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    rng = random.Random(arguments.seed)
    kept: dict[str, dict] = {}
    tried = 0
    oracle = Oracle()
    print(f"oracle {oracle.name}", flush=True)
    try:
        while len(kept) < arguments.count and tried < arguments.count * 12:
            tried += 1
            board = chess.Board()
            # Grow a line until Black is to move at a full-move number in range.
            while not (board.turn == chess.BLACK and arguments.min_move <= board.fullmove_number <= arguments.max_move):
                if board.fullmove_number > arguments.max_move or board.is_game_over():
                    break
                label = oracle.analyse(board.fen(), arguments.walk_nodes, multipv=arguments.multipv)
                best = label.lines[0].cp
                choices = [line.move for line in label.lines if best - line.cp <= arguments.spread]
                board.push_uci(rng.choice(choices))
            if board.turn != chess.BLACK or not (arguments.min_move <= board.fullmove_number <= arguments.max_move):
                continue
            fen = board.fen()
            if fen in kept:
                continue
            deep = oracle.analyse(fen, arguments.score_nodes)
            if abs(deep.cp_white) > arguments.level:
                continue
            kept[fen] = {
                "id": f"cp-{len(kept):03d}", "cluster": len(kept), "fen": fen,
                "fullmove": board.fullmove_number, "sf_cp_white": deep.cp_white,
                "sf_best": deep.best, "sf_wdl_white": list(deep.wdl_white) if deep.wdl_white else None,
                "sf_nodes": arguments.score_nodes, "phase": "opening",
            }
            print(f"  [{len(kept):>3}/{arguments.count}] move {board.fullmove_number} cp(white) {deep.cp_white:+4}  {fen}", flush=True)
        provenance = oracle.provenance()
    finally:
        oracle.close()
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    rows = list(kept.values())
    arguments.out.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    arguments.out.with_name(arguments.out.stem + "_provenance.json").write_text(
        json.dumps({"provenance": provenance, "arguments": {k: str(v) for k, v in vars(arguments).items()},
                    "lines_tried": tried, "kept": len(rows)}, indent=1) + "\n", encoding="utf-8")
    cps = [r["sf_cp_white"] for r in rows]
    print(f"{len(rows)} positions kept from {tried} lines; cp(white) mean {sum(cps) / max(1, len(cps)):+.1f} "
          f"min {min(cps)} max {max(cps)}; written to {arguments.out}")


if __name__ == "__main__":
    main()
