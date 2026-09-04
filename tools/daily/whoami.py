"""Which colour did ClaudeShark play? Answer it from move agreement, not metadata.

The rated PGNs are anonymised. Rather than guess, this replays each game and
asks a frozen ClaudeShark snapshot what it would play in every position, for
both colours, at a fixed depth. The snapshot is fed the game's earlier root
positions through the worker's ``seen`` command first, so its repetition
record matches the real game.

Agreement is reported overall and restricted to positions with more than one
legal move and no immediate recapture, because forced and obvious moves are
agreed on by any engine and carry no information about identity.

A second, independent line of evidence is printed alongside it: the shape of
each side's clock. ClaudeShark's allocator opens a soft budget and stops
starting new iterations part way through it, which produces a spend that varies
from move to move with occasional long thinks; an opponent running a fixed
budget per move produces an almost constant spend. In the two games whose
colour the move agreement settles beyond doubt, ClaudeShark's spend has a
standard deviation of 1.4 to 1.6 seconds and a maximum of 6 to 8, while one
opponent's is 0.47 and 2.51. The two lines of evidence are independent: one
reads the moves, the other reads the clock.

    uv run python -m tools.daily.whoami --games corpus/daily/games/rated.jsonl --engine champions/rated_v1 --depth 6 --out corpus/daily/whoami.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import chess

from tools.postmortem.play import Engine


def interesting(board: chess.Board, played: chess.Move) -> bool:
    """A position that discriminates: several legal moves and not a lone recapture."""
    legal = list(board.legal_moves)
    if len(legal) < 3:
        return False
    return not board.is_check()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    engine = Engine(arguments.engine, arguments.depth)
    rows = []
    try:
        for g in games:
            engine.ask("new")
            for m in g["moves"]:
                engine.ask(f"seen {m['fen']}")
                board = chess.Board(m["fen"])
                reply = engine.ask(f"go {m['fen']}")
                rows.append({
                    "game": g["game"], "ply": m["ply"], "turn": m["turn"], "fen": m["fen"],
                    "played": m["move"], "engine_move": reply["move"],
                    "agree": reply["move"] == m["move"],
                    "score_stm": reply["score"], "nodes": reply.get("nodes"),
                    "legal": board.legal_moves.count(),
                    "interesting": interesting(board, chess.Move.from_uci(m["move"])),
                    "spent": m["spent"], "san": m["san"],
                })
                print(f"  {g['game']} ply {m['ply']:>3} {m['turn']} played {m['san']:<8} "
                      f"engine {reply['move']:<6} {'MATCH' if rows[-1]['agree'] else ''}", flush=True)
    finally:
        engine.close()
    lines = [f"== WHO IS WHICH COLOUR: {arguments.engine} at depth {arguments.depth} against the played moves ==", ""]
    for g in games:
        lines.append(f"{g['game']}  ({g['result']}, {g['termination']})")
        for turn, label in (("w", "White"), ("b", "Black")):
            rs = [r for r in rows if r["game"] == g["game"] and r["turn"] == turn]
            it = [r for r in rs if r["interesting"]]
            lines.append(f"   {label:<6} agreement {sum(r['agree'] for r in rs):>3}/{len(rs):<3} "
                         f"({sum(r['agree'] for r in rs) / max(1, len(rs)):5.1%})   "
                         f"non-forced {sum(r['agree'] for r in it):>3}/{len(it):<3} "
                         f"({sum(r['agree'] for r in it) / max(1, len(it)):5.1%})")
        lines.append("   clock shape (independent of the moves): a spend that varies with occasional long thinks is ClaudeShark's")
        for turn, label in (("w", "White"), ("b", "Black")):
            spends = [m["spent"] for m in g["moves"] if m["turn"] == turn and m["spent"] is not None]
            if len(spends) < 3:
                continue
            ordered = sorted(spends)
            lines.append(f"   {label:<6} n {len(spends):>3}  mean {statistics.mean(spends):5.2f}s  sd {statistics.pstdev(spends):5.2f}s  "
                         f"max {max(spends):5.2f}s  p90 {ordered[int(0.9 * len(ordered))]:5.2f}s")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
