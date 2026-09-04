"""Repeated organiser starting positions as natural experiments.

The competition reuses starting positions: 114 distinct FENs across 143 public
games, with 23 used more than once. When two engines are handed the same
position and diverge, the divergence is a controlled comparison in a way that
self-play is not -- same start, different player, observable result.

The question asked here is deliberately narrow. It is **not** "what heuristic
does that bot use", which cannot be answered from moves and would be guesswork
dressed as analysis. It is "what chess capability separates the line the
stronger side took from the line ClaudeShark takes".

Two phases, because the second is expensive and the first is free:

    parse   group the games by exact start FEN, find the first ply where the
            games of a family diverge, and rank the families by how much is
            riding on that divergence. No engine, no oracle.
    score   for the ranked families, ask the oracle what it prefers at the
            divergence and ask a ClaudeShark snapshot what it would play, then
            classify ClaudeShark's disagreement as a move error, a score error,
            both or neither.

Hypothesis formation is restricted to the diagnostic split by default, so the
validation and holdout families stay unexamined.

    uv run python -m tools.daily.samefen parse --games analysis/top50_games.jsonl --split corpus/daily/splits/competition_diagnostic_fens.txt --out corpus/daily/samefen_families.txt
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter
from pathlib import Path

import chess
import chess.pgn


def mainline(row: dict) -> list[chess.Move]:
    game = chess.pgn.read_game(io.StringIO(row.get("pgn") or ""))
    return list(game.mainline_moves()) if game else []


def team(row: dict, colour: str) -> dict:
    side = row.get(colour) or {}
    return {"name": side.get("team_name"), "rank": side.get("rank"), "rating": side.get("rating")}


def score_for(row: dict, colour: str) -> float:
    winner = row.get("winner_colour")
    if winner not in ("white", "black"):
        return 0.5
    return 1.0 if winner == colour else 0.0


def first_divergence(games: list[dict]) -> tuple[int, dict[str, list[str]]]:
    """The first ply at which not every game of the family plays the same move."""
    lines = {g["game_id"]: mainline(g) for g in games}
    depth = min((len(v) for v in lines.values()), default=0)
    for ply in range(depth):
        chosen = {gid: moves[ply].uci() for gid, moves in lines.items()}
        if len(set(chosen.values())) > 1:
            grouped: dict[str, list[str]] = {}
            for gid, move in chosen.items():
                grouped.setdefault(move, []).append(gid)
            return ply, grouped
    return -1, {}


def parse(arguments: argparse.Namespace) -> None:
    rows = {r["game_id"]: r for r in (json.loads(line) for line in arguments.games.open(encoding="utf-8"))}
    allowed: set[str] | None = None
    if arguments.split:
        allowed = {line.strip() for line in arguments.split.read_text(encoding="utf-8").splitlines() if line.strip()}
    families: dict[str, list[dict]] = {}
    for r in rows.values():
        fen = r.get("starting_fen")
        if not fen or not mainline(r):
            continue
        if allowed is not None and fen not in allowed:
            continue
        families.setdefault(fen, []).append(r)
    repeated = {f: gs for f, gs in families.items() if len(gs) > 1}

    entries = []
    for fen, games in repeated.items():
        ply, grouped = first_divergence(games)
        board = chess.Board(fen)
        outcomes = Counter(g.get("winner_colour") for g in games)
        ratings = [t["rating"] for g in games for t in (team(g, "white"), team(g, "black")) if t["rating"]]
        # Research value: outcomes that differ are worth more than outcomes that
        # agree, an early divergence is worth more than a late one, and more
        # games in the family is worth more than fewer.
        value = (len(games)
                 + (3 if len(outcomes) > 1 else 0)
                 + (2 if ply >= 0 and ply < 6 else 1 if ply >= 0 else 0)
                 + (2 if len(grouped) >= 3 else 0))
        entries.append({
            "fen": fen, "games": len(games), "value": value,
            "side_to_move": "w" if board.turn == chess.WHITE else "b",
            "fullmove": board.fullmove_number,
            "outcomes": dict(outcomes),
            "divergence_ply": ply,
            "divergence_moves": {m: len(v) for m, v in grouped.items()},
            "max_rating": max(ratings) if ratings else None,
            "min_rating": min(ratings) if ratings else None,
            "detail": [{
                "game_id": g["game_id"],
                "white": team(g, "white"), "black": team(g, "black"),
                "result": g.get("canonical_result"), "winner": g.get("winner_colour"),
                "first_move": mainline(g)[0].uci() if mainline(g) else None,
                "divergence_move": mainline(g)[ply].uci() if ply >= 0 and len(mainline(g)) > ply else None,
                "plies": len(mainline(g)),
                "termination": g.get("termination"),
            } for g in games],
        })
    entries.sort(key=lambda e: (-e["value"], -e["games"]))

    lines = ["== REPEATED ORGANISER START POSITIONS AS NATURAL EXPERIMENTS ==",
             f"source {arguments.games}"
             + (f", restricted to {arguments.split.name}" if arguments.split else ", whole population"),
             f"{len(families)} families with moves, {len(repeated)} used more than once, "
             f"covering {sum(len(g) for g in repeated.values())} games", ""]
    for i, e in enumerate(entries, start=1):
        lines.append(f"{i:>2}. value {e['value']:>2}  {e['games']} games  outcomes {e['outcomes']}  "
                     f"start move {e['fullmove']} {'White' if e['side_to_move'] == 'w' else 'Black'} to move")
        lines.append(f"    {e['fen']}")
        if e["divergence_ply"] >= 0:
            lines.append(f"    first divergence at ply {e['divergence_ply'] + 1}: {e['divergence_moves']}")
        else:
            lines.append("    the games never diverge inside their common length")
        for d in e["detail"]:
            lines.append(f"      {d['white']['name']} ({d['white']['rating']}) vs {d['black']['name']} ({d['black']['rating']})"
                         f"  {d['result']}  {d['plies']} plies  {d['termination']}"
                         f"  first {d['first_move']}  at divergence {d['divergence_move']}")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(entries, indent=1) + "\n", encoding="utf-8")
    # Team names are user-chosen and some contain emoji; the file is UTF-8
    # either way, but a Windows console in cp1252 cannot print them.
    encoding = sys.stdout.encoding or "utf-8"
    print(text.encode(encoding, errors="replace").decode(encoding))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)
    p = sub.add_parser("parse", help="group and rank repeated-FEN families; no engine or oracle")
    p.add_argument("--games", type=Path, required=True)
    p.add_argument("--split", type=Path, default=None, help="restrict to the FEN list of one split")
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=parse)
    arguments = parser.parse_args()
    arguments.func(arguments)


if __name__ == "__main__":
    main()
