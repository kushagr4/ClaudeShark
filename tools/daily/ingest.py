"""Convert a rated Chessathon PGN into the games schema the post-mortem tools read.

The rated PGNs are anonymised: White and Black are "?" and there is no engine
name, so this module records only what the file actually states -- the start
FEN, the moves, the result, the termination and the per-move clock -- and
leaves the question of which colour ClaudeShark played to
``tools.daily.whoami``, which answers it from move agreement rather than
metadata.

Time spent on a move is reconstructed as ``clock_before - clock_after +
increment``, where the increment is inferred as the largest single clock gain
observed in the game rounded to a tenth of a second, and the first move of
each colour has no measurable spend because no earlier clock exists.

    uv run python -m tools.daily.ingest --pgn corpus/daily/round1.pgn --out corpus/daily/games/round1.jsonl
"""

from __future__ import annotations

import argparse
import io
import itertools
import json
import re
from pathlib import Path

import chess
import chess.pgn

CLOCK = re.compile(r"\[%clk\s+(\d+):(\d+):([\d.]+)\]")


def clock_seconds(comment: str) -> float | None:
    m = CLOCK.search(comment or "")
    if not m:
        return None
    h, mm, ss = m.groups()
    return int(h) * 3600 + int(mm) * 60 + float(ss)


def convert(path: Path, name: str) -> dict:
    game = chess.pgn.read_game(io.StringIO(path.read_text(encoding="utf-8")))
    if game is None:
        raise SystemExit(f"no game in {path}")
    board = game.board()
    start_fen = board.fen()
    rows = []
    for ply, node in enumerate(game.mainline(), start=1):
        move = node.move
        rows.append({
            "ply": ply,
            "fen": board.fen(),
            "turn": "w" if board.turn == chess.WHITE else "b",
            "move": move.uci(),
            "san": board.san(move),
            "clock": clock_seconds(node.comment),
            "fullmove": board.fullmove_number,
        })
        board.push(move)
    # Increment: the largest clock gain seen for either colour, to a tenth.
    gains = []
    for colour in ("w", "b"):
        seq = [r["clock"] for r in rows if r["turn"] == colour and r["clock"] is not None]
        gains += [b - a for a, b in itertools.pairwise(seq) if b > a]
    increment = round(max(gains), 1) if gains else 0.0
    prev = {}
    for r in rows:
        before = prev.get(r["turn"])
        r["spent"] = None if before is None or r["clock"] is None else round(before - r["clock"] + increment, 3)
        prev[r["turn"]] = r["clock"]
    return {
        "game": name,
        "source": str(path),
        "start_fen": start_fen,
        "result": game.headers.get("Result", "*"),
        "termination": game.headers.get("Termination", ""),
        "white_header": game.headers.get("White", "?"),
        "black_header": game.headers.get("Black", "?"),
        "increment": increment,
        "plies": len(rows),
        "final_fen": board.fen(),
        "moves": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    games = [convert(p, p.stem) for p in arguments.pgn]
    with arguments.out.open("w", encoding="utf-8") as fh:
        for g in games:
            fh.write(json.dumps(g) + "\n")
    for g in games:
        w = [r["spent"] for r in g["moves"] if r["turn"] == "w" and r["spent"] is not None]
        b = [r["spent"] for r in g["moves"] if r["turn"] == "b" and r["spent"] is not None]
        print(f"{g['game']}: {g['plies']} plies, result {g['result']}, termination {g['termination']}, "
              f"increment {g['increment']}s")
        print(f"   start {g['start_fen']}")
        print(f"   white spend: n={len(w)} mean {sum(w) / max(1, len(w)):.2f}s max {max(w or [0]):.2f}s")
        print(f"   black spend: n={len(b)} mean {sum(b) / max(1, len(b)):.2f}s max {max(b or [0]):.2f}s")
    print(f"written to {arguments.out}")


if __name__ == "__main__":
    main()
