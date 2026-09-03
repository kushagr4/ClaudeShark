"""Search-level cost of the passed-pawn term: fixed-depth nodes, time and NPS, flag off and on.

The evaluator micro-benchmark repeats the same 42 positions, so with the
pawn-structure cache it measures a cache-hot call and flatters the term.
This runs a real depth-limited search from each of the same positions with
the flag off and then on, in separate processes so the flag is read at
import, and reports node counts, elapsed time and nodes per second. The node
counts differ because the evaluation differs; NPS is the cost.

    uv run python -m tools.passed.cost --depth 6 --out corpus/passed/03_cost.txt
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CHILD = r"""
import json, sys, time
sys.setrecursionlimit(10_000)
import chess
from cs_search import Searcher
from tools.positions import BALANCED_OPENINGS, SHARP_POSITIONS
import cs_passed
depth = int(sys.argv[1])
searcher = Searcher()
searcher.new_game()
nodes = 0
started = time.perf_counter()
for fen in BALANCED_OPENINGS + SHARP_POSITIONS:
    searcher.new_game()
    move, info = searcher.search(chess.Board(fen), 600_000, max_depth=depth)
    nodes += info.nodes
elapsed = time.perf_counter() - started
print(json.dumps({"nodes": nodes, "elapsed": elapsed, "nps": nodes / elapsed, "cache_entries": len(cs_passed._CACHE)}))
"""


def run(flag: str, depth: int) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("CS_")}
    env["CS_EVAL_PASSED"] = flag
    out = subprocess.run([sys.executable, "-c", CHILD, str(depth)], cwd=ROOT, env=env,
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    lines = [f"== SEARCH COST of the passed-pawn term: depth {arguments.depth}, 42 bench positions, {arguments.repeats} repeats each ==", "",
             f"{'flag':<5} {'run':>3} {'nodes':>12} {'seconds':>9} {'NPS':>9} {'cache':>7}"]
    best: dict[str, float] = {}
    for flag in ("0", "1"):
        for i in range(arguments.repeats):
            r = run(flag, arguments.depth)
            best[flag] = max(best.get(flag, 0.0), r["nps"])
            lines.append(f"{flag:<5} {i + 1:>3} {r['nodes']:>12,} {r['elapsed']:>9.2f} {r['nps']:>9,.0f} {r['cache_entries']:>7}")
    lines.append("")
    lines.append(f"best NPS off {best['0']:,.0f}, on {best['1']:,.0f}: the term costs {1 - best['1'] / best['0']:.1%} of search throughput")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
