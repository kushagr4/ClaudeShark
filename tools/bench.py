"""Search benchmark: fixed time per position across the FEN suite.

Reports the numbers that actually predict strength -- depth reached, nodes per
second, transposition hit rate -- so a change can be attributed to speed, to
ordering, or to neither. Run it before and after any search change; run the
arena to find out whether the change was worth Elo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chess

from tools.positions import BALANCED_OPENINGS


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the search over the FEN suite.")
    parser.add_argument("--ms", type=int, default=2_000, help="fixed search budget per position")
    parser.add_argument(
        "--depth",
        type=int,
        default=0,
        help="search to a fixed depth instead of a fixed time; node counts are "
        "then deterministic, which is what pruning comparisons need",
    )
    parser.add_argument("--positions", type=int, default=0, help="0 means the whole suite")
    parser.add_argument("--fresh-tt", action="store_true", help="new table per position")
    parser.add_argument(
        "--engine",
        type=Path,
        default=None,
        help="benchmark a frozen champion directory instead of the working tree",
    )
    arguments = parser.parse_args()

    # The engine modules are imported here, not at module scope, so that a
    # champion directory can be put in front of the working tree on sys.path.
    if arguments.engine:
        sys.path.insert(0, str(arguments.engine.resolve()))
    from cs_search import Searcher
    from cs_tt import mate_in

    print(f"engine: {arguments.engine or 'working tree'}")

    fens = BALANCED_OPENINGS
    if arguments.positions:
        fens = fens[: arguments.positions]

    searcher = Searcher()
    total_nodes = 0
    total_q = 0
    total_ms = 0.0
    total_depth = 0
    total_probes = 0
    total_hits = 0

    print(f"{'position':<10} {'depth':>5} {'score':>8} {'nodes':>9} {'q%':>4} "
          f"{'ms':>7} {'knps':>6} {'tt%':>5}  move")
    for index, fen in enumerate(fens):
        if arguments.fresh_tt:
            searcher = Searcher()
        else:
            searcher.new_game()
        if arguments.depth:
            move, info = searcher.search(chess.Board(fen), 0, max_depth=arguments.depth)
        else:
            move, info = searcher.search(chess.Board(fen), 0, fixed_budget_ms=arguments.ms)

        mate = mate_in(info.score)
        score = f"#{mate}" if mate is not None else f"{info.score / 100:+.2f}"
        q_share = 100.0 * info.qnodes / info.nodes if info.nodes else 0.0
        tt_rate = 100.0 * info.tt_hits / info.tt_probes if info.tt_probes else 0.0
        print(
            f"{index:<10} {info.depth:>5} {score:>8} {info.nodes:>9} {q_share:>3.0f}% "
            f"{info.elapsed_ms:>7.0f} {info.nps / 1000:>6.1f} {tt_rate:>4.0f}%  {move}"
        )

        total_nodes += info.nodes
        total_q += info.qnodes
        total_ms += info.elapsed_ms
        total_depth += info.depth
        total_probes += info.tt_probes
        total_hits += info.tt_hits

    count = len(fens)
    limit = f"fixed depth {arguments.depth}" if arguments.depth else f"{arguments.ms} ms"
    print(
        f"\n{count} positions at {limit}\n"
        f"  average depth   {total_depth / count:.2f}\n"
        f"  total nodes     {total_nodes:,} "
        f"({100.0 * total_q / max(1, total_nodes):.0f}% quiescence)\n"
        f"  nodes/second    {total_nodes / (total_ms / 1000.0):,.0f}\n"
        f"  tt hit rate     {100.0 * total_hits / max(1, total_probes):.1f}%\n"
        f"  time in search  {total_ms / 1000.0:.1f}s"
    )


if __name__ == "__main__":
    main()
