"""Replay positions with two engines at a realistic clock and oracle-score both moves.

Gate 1 for a search or time-management candidate: each FEN is searched by the
baseline directory and by the candidate directory through the normal clock
allocator (``search(board, time_left_ms)``), so time-policy changes take
effect exactly as in a game. The resulting positions are scored by the oracle
and each move's centipawn loss is reported, with depth, time used and whether
the candidate extended.

    uv run python -m tools.strength.replay_compare --baseline champions/rc_c --candidate . \
        --fens targets.txt --clock-ms 60000 --out result.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import chess

from tools.corpus.oracle import label_many

WORKER = r"""
import sys, json
sys.path.insert(0, sys.argv[1])
import chess
from cs_search import Searcher
fen, clock = sys.argv[2], int(sys.argv[3])
s = Searcher()
move, info = s.search(chess.Board(fen), clock)
print(json.dumps({"move": move.uci() if move else None, "score": info.score, "depth": info.depth,
                  "nodes": info.nodes, "ms": round(info.elapsed_ms),
                  "extended": bool(getattr(info, "extended", False)),
                  "unstable": info.unstable_iterations, "pv": info.pv[:6]}))
"""


def run(engine: Path, fen: str, clock_ms: int, env: dict[str, str]) -> dict:
    result = subprocess.run(
        [sys.executable, "-c", WORKER, str(engine.resolve()), fen, str(clock_ms)],
        capture_output=True, text=True, check=True, env=env,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--fens", type=Path, required=True, help="one FEN per line, '#' comments")
    parser.add_argument("--clock-ms", type=int, default=60_000)
    parser.add_argument("--set-env", action="append", default=[],
                        help="NAME=value for the candidate only")
    parser.add_argument("--oracle-nodes", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=3,
                        help="each job runs two timed searches; keep the machine unloaded")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    fens = [line.strip() for line in arguments.fens.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]
    base_env = {k: v for k, v in os.environ.items() if not k.startswith("CS_")}
    cand_env = dict(base_env)
    for item in arguments.set_env:
        name, _, value = item.partition("=")
        cand_env[name] = value

    def work(fen: str) -> dict:
        a = run(arguments.baseline, fen, arguments.clock_ms, base_env)
        b = run(arguments.candidate, fen, arguments.clock_ms, cand_env)
        return {"fen": fen, "baseline": a, "candidate": b}

    with ThreadPoolExecutor(max_workers=arguments.workers) as pool:
        rows = list(pool.map(work, fens))

    # Oracle: the position itself and the position after each engine's move.
    positions: set[str] = set()
    after: dict[tuple[str, str], str] = {}
    for r in rows:
        board = chess.Board(r["fen"])
        positions.add(r["fen"])
        for mv in {r["baseline"]["move"], r["candidate"]["move"]}:
            if mv and (r["fen"], mv) not in after:
                b = board.copy()
                b.push(chess.Move.from_uci(mv))
                after[(r["fen"], mv)] = b.fen()
                positions.add(b.fen())
    unique = sorted(positions)
    labels = {}
    for fen, label in zip(unique, label_many(unique, arguments.oracle_nodes,
                                              workers=6, progress=True), strict=True):
        labels[fen] = label.cp_white

    def loss(r: dict, mv: str | None) -> int | None:
        if not mv:
            return None
        white = chess.Board(r["fen"]).turn == chess.WHITE
        before = labels[r["fen"]] if white else -labels[r["fen"]]
        cp_after = labels[after[(r["fen"], mv)]]
        cp_after = cp_after if white else -cp_after
        return max(0, before - cp_after)

    with arguments.out.open("w", encoding="utf-8") as handle:
        for r in rows:
            r["baseline_loss"] = loss(r, r["baseline"]["move"])
            r["candidate_loss"] = loss(r, r["candidate"]["move"])
            handle.write(json.dumps(r) + "\n")

    n = len(rows)
    b100 = sum(1 for r in rows if (r["baseline_loss"] or 0) >= 100)
    c100 = sum(1 for r in rows if (r["candidate_loss"] or 0) >= 100)
    repaired = sum(1 for r in rows if (r["baseline_loss"] or 0) >= 100 and (r["candidate_loss"] or 0) < 100)
    broken = sum(1 for r in rows if (r["baseline_loss"] or 0) < 100 and (r["candidate_loss"] or 0) >= 100)
    ext = sum(1 for r in rows if r["candidate"]["extended"])
    tb = sum(r["baseline"]["ms"] for r in rows) / n
    tc = sum(r["candidate"]["ms"] for r in rows) / n
    db = sum(r["baseline"]["depth"] for r in rows) / n
    dc = sum(r["candidate"]["depth"] for r in rows) / n
    print(f"{n} positions at clock {arguments.clock_ms} ms")
    print(f"  >=100 cp losses: baseline {b100}, candidate {c100}; repaired {repaired}, broken {broken}")
    print(f"  candidate extended on {ext} ({100 * ext / n:.0f}%)")
    print(f"  mean ms: baseline {tb:.0f}, candidate {tc:.0f} ({100 * (tc / tb - 1):+.0f}%)")
    print(f"  mean depth: baseline {db:.2f}, candidate {dc:.2f}")
    print(f"  mean loss: baseline {sum(r['baseline_loss'] or 0 for r in rows) / n:.1f}, "
          f"candidate {sum(r['candidate_loss'] or 0 for r in rows) / n:.1f}")


if __name__ == "__main__":
    main()
