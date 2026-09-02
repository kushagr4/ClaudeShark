"""Compare how two engines *spend* a clock, not how fast they search.

A fixed-budget benchmark cannot see a time-management regression: it hands both
engines the same budget by construction. This hands them a realistic clock and
measures what they choose to do with it -- time actually spent per move, depth
reached, and how much of the allocation was used.

An engine that leaves half its allocation unspent is throwing away depth, and
that will not show up anywhere else in the test suite.

    uv run python -m tools.clocksim --engine champions/v0_2 --clock 20000
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from time import perf_counter

import chess

from tools.positions import BALANCED_OPENINGS


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure clock usage per move.")
    parser.add_argument("--engine", type=Path, default=None)
    parser.add_argument("--clock", type=int, default=20_000, help="clock handed to each search")
    parser.add_argument("--increment", type=int, default=200)
    arguments = parser.parse_args()

    if arguments.engine:
        sys.path.insert(0, str(arguments.engine.resolve()))
    from cs_search import Searcher

    spends: list[float] = []
    depths: list[int] = []
    budgets: list[float] = []

    for fen in BALANCED_OPENINGS:
        searcher = Searcher()
        started = perf_counter()
        _, info = searcher.search(chess.Board(fen), arguments.clock)
        spends.append((perf_counter() - started) * 1000.0)
        depths.append(info.depth)
        budgets.append(info.budget_ms)

    used = [
        100.0 * spend / budget if budget else 0.0
        for spend, budget in zip(spends, budgets, strict=True)
    ]

    print(f"engine        {arguments.engine or 'working tree'}")
    print(f"clock         {arguments.clock} ms")
    print(f"soft budget   {statistics.mean(budgets):8.1f} ms average")
    print(f"time spent    {statistics.mean(spends):8.1f} ms average "
          f"(median {statistics.median(spends):.0f})")
    print(f"budget used   {statistics.mean(used):8.1f}% average")
    print(f"depth         {statistics.mean(depths):8.2f} average "
          f"(min {min(depths)}, max {max(depths)})")
    print(f"total spent   {sum(spends) / 1000.0:8.1f} s over {len(spends)} moves")


if __name__ == "__main__":
    main()
