"""Measure one registry term: cost, activation, contribution, and its effect on the calibration set.

Everything a term must report before it earns a game:

* evaluator throughput with the term off and on (cache-hot micro-benchmark);
* depth-6 search on the bench positions with the term off and on, in
  separate processes so the flag is read at import: nodes, seconds, NPS;
* activation frequency -- the share of positions on which the term is
  non-zero -- and the distribution of its contribution, on the calibration
  set and on every position of a retained game file;
* the static-only calibration report with the term off and on, so the two
  failure classes can be read side by side with the classes that must not move.

    uv run python -m tools.v2.termbench --term passed --out corpus/v2/termbench_passed.txt
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import chess

import cs_eval
import cs_terms
from tools.positions import BALANCED_OPENINGS, SHARP_POSITIONS
from tools.v2.suite import CLASSES, clamp

ROOT = Path(__file__).resolve().parents[2]

SEARCH_CHILD = r"""
import json, sys, time
sys.setrecursionlimit(10_000)
import chess
from cs_search import Searcher
from tools.positions import BALANCED_OPENINGS, SHARP_POSITIONS
depth = int(sys.argv[1])
nodes = 0
started = time.perf_counter()
for fen in BALANCED_OPENINGS + SHARP_POSITIONS:
    s = Searcher(); s.new_game()
    move, info = s.search(chess.Board(fen), 600_000, max_depth=depth)
    nodes += info.nodes
elapsed = time.perf_counter() - started
print(json.dumps({"nodes": nodes, "elapsed": elapsed, "nps": nodes / elapsed}))
"""


def eval_rate(boards: list[chess.Board], repeats: int) -> float:
    for b in boards:
        cs_eval.evaluate(b)
    started = perf_counter()
    for _ in range(repeats):
        for b in boards:
            cs_eval.evaluate(b)
    return repeats * len(boards) / (perf_counter() - started)


def search_cost(term: str, depth: int) -> tuple[dict, dict]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("CS_")}
    off = subprocess.run([sys.executable, "-c", SEARCH_CHILD, str(depth)], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    env["CS_EVAL_TERMS"] = term
    on = subprocess.run([sys.executable, "-c", SEARCH_CHILD, str(depth)], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    return json.loads(off.stdout.strip().splitlines()[-1]), json.loads(on.stdout.strip().splitlines()[-1])


def contribution(term: cs_terms.Term, board: chess.Board) -> int:
    """The term's value in centipawns from White's side, tapered as the evaluator would."""
    if term.stage == "post":
        return term.fast(board)
    mg, eg = cs_terms.unpack(term.fast(board))
    phase = min(24, (board.knights | board.bishops).bit_count() + 2 * board.rooks.bit_count() + 4 * board.queens.bit_count())
    return (mg * phase + eg * (24 - phase)) // 24


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--term", required=True)
    parser.add_argument("--suite", type=Path, default=Path("corpus/v2/endgame_calibration_v1.jsonl"))
    parser.add_argument("--games", type=Path, default=Path("corpus/passed/games/gate2_fixed_depth.jsonl"))
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--repeats", type=int, default=200)
    parser.add_argument("--no-search", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    term = cs_terms.BY_NAME[arguments.term]
    lines = [f"== TERM BENCH: {term.name} (stage {term.stage}, flag {term.flag}) ==", ""]

    bench = [chess.Board(f) for f in BALANCED_OPENINGS + SHARP_POSITIONS]
    cs_eval.set_terms(())
    off = eval_rate(bench, arguments.repeats)
    cs_eval.set_terms((term.name,))
    on = eval_rate(bench, arguments.repeats)
    cs_eval.set_terms(())
    lines.append(f"evaluator, 42 bench positions cache-hot: off {off:,.0f}/s ({1e6 / off:.2f} us), on {on:,.0f}/s ({1e6 / on:.2f} us), cost {1 - on / off:+.1%}")
    if not arguments.no_search:
        a, b = search_cost(term.name, arguments.depth)
        lines.append(f"depth-{arguments.depth} search, same positions: off {a['nodes']:,} nodes {a['nps']:,.0f} NPS; on {b['nodes']:,} nodes {b['nps']:,.0f} NPS; NPS cost {1 - b['nps'] / a['nps']:+.1%}")
    lines.append("")

    for label, boards in (("calibration set", [chess.Board(json.loads(line)["fen"]) for line in arguments.suite.open(encoding="utf-8") if '"record": "header"' not in line] if arguments.suite.exists() else []),
                          ("retained games, every position", [chess.Board(m["fen"]) for g in map(json.loads, arguments.games.open(encoding="utf-8")) for m in g["moves"]] if arguments.games.exists() else [])):
        if not boards:
            continue
        vals = [contribution(term, b) for b in boards]
        active = [v for v in vals if v]
        lines.append(f"{label}: {len(boards)} positions, active on {len(active) / len(boards):.1%}; |contribution| when active mean {statistics.mean(abs(v) for v in active) if active else 0:.1f} cp, max {max((abs(v) for v in active), default=0)}")

    if arguments.suite.exists():
        rows = [json.loads(line) for line in arguments.suite.open(encoding="utf-8")][1:]
        lines.append("")
        lines.append("static vs Stockfish by class, term off -> on (below = SF - static for wins; above = static - SF for level positions; MAE = mean |static - SF|):")
        lines.append(f"  {'class':<16} {'n':>4} {'off static':>10} {'on static':>10} {'off MAE':>8} {'on MAE':>7} {'moved':>6} {'active':>7}")
        for cls in CLASSES:
            rs = [r for r in rows if r["class"] == cls]
            if not rs:
                continue
            offs, ons, sfs = [], [], []
            for r in rs:
                board = chess.Board(r["fen"])
                sign = 1 if board.turn else -1
                cs_eval.set_terms(())
                o = sign * (cs_eval.evaluate(board) - cs_eval.TEMPO)
                cs_eval.set_terms((term.name,))
                n = sign * (cs_eval.evaluate(board) - cs_eval.TEMPO)
                cs_eval.set_terms(())
                offs.append(o)
                ons.append(n)
                sfs.append(clamp(r["sf_cp"]))
            moved = sum(1 for o, n in zip(offs, ons, strict=True) if o != n)
            lines.append(f"  {cls:<16} {len(rs):>4} {statistics.mean(offs):>+10.0f} {statistics.mean(ons):>+10.0f} "
                         f"{statistics.mean(abs(o - s) for o, s in zip(offs, sfs, strict=True)):>8.0f} {statistics.mean(abs(n - s) for n, s in zip(ons, sfs, strict=True)):>7.0f} {moved:>6} {moved / len(rs):>7.0%}")
    text = "\n".join(lines)
    print(text)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
