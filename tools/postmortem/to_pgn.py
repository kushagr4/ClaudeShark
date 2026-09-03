"""Export a fixed-depth game set (JSONL with full move lists) as a PGN file.

The JSONL written by `tools.postmortem.play` already retains every move, so
the PGN is a derived view: one game per record, headers carrying the cluster,
the candidate's colour, the fixed depth and the draw-claim mode, so a game can
be found from either file.

    uv run python -m tools.postmortem.to_pgn --games <jsonl> --out <pgn> --cand-name X --base-name Y
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess
import chess.pgn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cand-name", default="candidate")
    parser.add_argument("--base-name", default="baseline")
    parser.add_argument("--event", default="fixed-depth paired self-play")
    arguments = parser.parse_args()

    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    with arguments.out.open("w", encoding="utf-8") as fh:
        for index, g in enumerate(games):
            board = chess.Board(g["start_fen"])
            game = chess.pgn.Game()
            game.setup(board)
            game.headers["Event"] = arguments.event
            game.headers["Round"] = str(index)
            game.headers["Cluster"] = str(g["cluster"])
            game.headers["White"] = arguments.cand_name if g["cand_white"] else arguments.base_name
            game.headers["Black"] = arguments.base_name if g["cand_white"] else arguments.cand_name
            game.headers["Depth"] = str(g.get("depth", ""))
            game.headers["DrawClaim"] = str(g.get("draw_claim", ""))
            game.headers["Termination"] = g["termination"]
            game.headers["Result"] = g["result"]
            node = game
            for m in g["moves"]:
                node = node.add_variation(chess.Move.from_uci(m["move"]))
            fh.write(str(game) + "\n\n")
    print(f"{len(games)} games written to {arguments.out}")


if __name__ == "__main__":
    main()
