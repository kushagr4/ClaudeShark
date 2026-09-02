"""Profile the search over a few suite positions.

Answers one question: is the engine limited by move generation, by evaluation,
by ordering, or by its own bookkeeping? Optimise what this says, not what seems
likely.

    uv run python -m tools.profile_search --ms 3000 --positions 6
"""

from __future__ import annotations

import argparse
import cProfile
import pstats

import chess

from cs_search import Searcher
from tools.positions import BALANCED_OPENINGS


def run(budget_ms: int, count: int) -> None:
    searcher = Searcher()
    for fen in BALANCED_OPENINGS[:count]:
        searcher.new_game()
        searcher.search(chess.Board(fen), 0, fixed_budget_ms=budget_ms)


def main() -> None:
    parser = argparse.ArgumentParser(description="cProfile the search.")
    parser.add_argument("--ms", type=int, default=3_000)
    parser.add_argument("--positions", type=int, default=6)
    parser.add_argument("--rows", type=int, default=25)
    arguments = parser.parse_args()

    profiler = cProfile.Profile()
    profiler.enable()
    run(arguments.ms, arguments.positions)
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.sort_stats("tottime").print_stats(arguments.rows)


if __name__ == "__main__":
    main()
