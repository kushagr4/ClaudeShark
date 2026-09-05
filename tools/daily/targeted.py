"""Targeted comparison of two frozen engines and the oracle on a few positions.

For each FEN, every engine directory is run in its own process (so a frozen
snapshot keeps its own modules) at a fixed budget and, optionally, a fixed
depth, and the oracle scores the position and the position after each
engine's move at the same node count. Output is one table per position: the
moves, the engines' root and static scores, and the oracle's centipawn loss
for each move. Built for post-mortems of single rated games, not for Elo.

    uv run python -m tools.daily.targeted --fen "<fen>" --label "R17 48.Qxe5" \
        --engine champions/rated_v1 --engine champions/rc_b --ms 2500 --depth 8
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle

WORKER = r"""
import sys, json, time
sys.path.insert(0, sys.argv[1])
import chess
from cs_search import Searcher
from cs_eval import evaluate
fen, ms, depth = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
out = {}
s = Searcher()
board = chess.Board(fen)
out["static"] = evaluate(board)
if ms:
    move, info = s.search(chess.Board(fen), 0, fixed_budget_ms=ms)
    out["timed"] = {"move": move.uci() if move else None, "score": info.score, "depth": info.depth,
                    "nodes": info.nodes, "ms": round(info.elapsed_ms), "pv": info.pv[:6]}
if depth:
    s = Searcher()
    move, info = s.search(chess.Board(fen), 0, max_depth=depth)
    out["fixed"] = {"move": move.uci() if move else None, "score": info.score, "depth": info.depth,
                    "nodes": info.nodes, "pv": info.pv[:6]}
print(json.dumps(out))
"""


def run_engine(directory: Path, fen: str, ms: int, depth: int) -> dict:
    result = subprocess.run(
        [sys.executable, "-c", WORKER, str(directory.resolve()), fen, str(ms), str(depth)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fen", action="append", required=True)
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--engine", action="append", type=Path, required=True)
    parser.add_argument("--ms", type=int, default=2500)
    parser.add_argument("--depth", type=int, default=0)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    labels = args.label + [""] * (len(args.fen) - len(args.label))
    records = []
    with Oracle() as oracle:
        for fen, label in zip(args.fen, labels, strict=True):
            board = chess.Board(fen)
            root = oracle.analyse(fen, args.nodes, multipv=2)
            row = {"label": label, "fen": fen, "oracle_best": root.best, "oracle_cp_stm": root.cp_stm,
                   "oracle_lines": [(ln.move, ln.cp) for ln in root.lines], "engines": {}}
            for directory in args.engine:
                res = run_engine(directory, fen, args.ms, args.depth)
                for kind in ("timed", "fixed"):
                    if kind in res and res[kind]["move"]:
                        after = oracle.score_after(fen, res[kind]["move"], args.nodes)
                        best_after = oracle.score_after(fen, root.best, args.nodes)
                        # loss from the mover's side: best child minus our child, both as the mover sees them
                        res[kind]["oracle_cp_after"] = -after.cp_stm
                        res[kind]["cp_loss"] = (-best_after.cp_stm) - (-after.cp_stm)
                row["engines"][directory.name] = res
            records.append(row)
            print(f"\n== {label or fen} ==  side to move: {'White' if board.turn else 'Black'}")
            print(f"  oracle: best {root.best} cp {root.cp_stm:+} (stm)   second: {row['oracle_lines'][1] if len(row['oracle_lines']) > 1 else '-'}")
            for name, res in row["engines"].items():
                for kind in ("timed", "fixed"):
                    if kind in res:
                        r = res[kind]
                        print(f"  {name:12s} {kind:5s} {r['move']:6s} score {r['score']:+5d} static {res['static']:+5d} "
                              f"depth {r['depth']:2d} nodes {r['nodes']:8d}  oracle after {r['oracle_cp_after']:+5d}  loss {r['cp_loss']:+5d}  pv {' '.join(r['pv'])}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("a", encoding="utf-8") as handle:
            for row in records:
                handle.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
