"""Convert an arena match (JSONL + PGN) into the games schema the post-mortem tools read.

`tools.postmortem.annotate` and the error audit consume the schema that
`tools.daily.ingest` produces from rated PGNs: one record per game with a
`moves` list of (ply, fen, turn, move, san, clock, spent). An arena match
carries the same information across its per-game JSONL records and the PGN
written at the end, plus which colour ClaudeShark had. When the arena record
carries a per-ply `clock_trace`, each move gets its real think time and clock;
older records without it leave those fields null.

    uv run python -m tools.strength.convert --jsonl <match.jsonl> --out <games.jsonl>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess
import chess.pgn


def convert(match_path: Path, out_path: Path) -> int:
    rows = [json.loads(line) for line in match_path.open(encoding="utf-8") if line.strip()]
    header = rows[0]
    games = [r for r in rows if r.get("record") == "game"]
    pgn_file = header.get("pgn_file")
    pgn_path = Path(pgn_file) if pgn_file else match_path.with_suffix(".pgn")
    pgn_games: list[chess.pgn.Game] = []
    with pgn_path.open(encoding="utf-8") as handle:
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break
            pgn_games.append(game)
    if len(pgn_games) != len(games):
        raise SystemExit(f"{len(pgn_games)} PGN games but {len(games)} records in {match_path}")

    written = 0
    with out_path.open("w", encoding="utf-8") as out:
        for record in games:
            pgn = pgn_games[record["pgn_index"]]
            board = chess.Board(record["start_fen"])
            trace = {int(t[0]): t for t in record.get("clock_trace", [])}
            moves = []
            for ply, move in enumerate(pgn.mainline_moves(), start=1):
                entry = trace.get(ply)
                moves.append({
                    "ply": ply,
                    "fen": board.fen(),
                    "turn": "w" if board.turn else "b",
                    "move": move.uci(),
                    "san": board.san(move),
                    "fullmove": board.fullmove_number,
                    "clock": round(entry[3] / 1000.0, 3) if entry else None,
                    "spent": round(entry[2] / 1000.0, 3) if entry else None,
                })
                board.push(move)
            out.write(json.dumps({
                "game": f"{record['match_id']}-g{record['game_index']:03d}",
                "source": str(match_path),
                "match_id": record["match_id"],
                "game_index": record["game_index"],
                "start_fen": record["start_fen"],
                "cluster": record["cluster"],
                "agent_colour": "w" if record["agent_is_white"] else "b",
                "agent_score": record["agent_score"],
                "result": pgn.headers.get("Result", "*"),
                "termination": record["termination"],
                "white_header": pgn.headers.get("White", "?"),
                "black_header": pgn.headers.get("Black", "?"),
                "increment": header.get("increment_ms", 500) / 1000.0,
                "inferred_increment": None,
                "plies": len(moves),
                "final_fen": board.fen(),
                "moves": moves,
            }) + "\n")
            written += 1
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    count = convert(arguments.jsonl, arguments.out)
    print(f"{count} games written to {arguments.out}")


if __name__ == "__main__":
    main()
