"""Profile and micro-benchmark ``evaluate()``.

Evaluation is the largest hot path we actually own -- move generation and
make/unmake belong to python-chess -- so it is the one place where our own code
is the bottleneck. This measures raw evaluation throughput on a spread of
positions rather than a single one, because the cost is proportional to the
number of pieces on the board and a benchmark run only from the initial
position would flatter any change that helps sparse boards.

    uv run python -m tools.profile_eval
    uv run python -m tools.profile_eval --profile
"""

from __future__ import annotations

import argparse
import cProfile
import pstats
from time import perf_counter

import chess

from cs_eval import evaluate
from tools.positions import BALANCED_OPENINGS, SHARP_POSITIONS


def boards() -> list[chess.Board]:
    return [chess.Board(fen) for fen in BALANCED_OPENINGS + SHARP_POSITIONS]


def throughput(repeats: int) -> float:
    """Evaluations per second, averaged over the whole position spread."""
    positions = boards()
    # Warm up so the first-call overhead is not part of the measurement.
    for board in positions:
        evaluate(board)

    started = perf_counter()
    for _ in range(repeats):
        for board in positions:
            evaluate(board)
    elapsed = perf_counter() - started
    return (repeats * len(positions)) / elapsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the evaluator.")
    parser.add_argument("--repeats", type=int, default=400)
    parser.add_argument("--profile", action="store_true", help="cProfile instead of timing")
    parser.add_argument("--rows", type=int, default=12)
    arguments = parser.parse_args()

    if arguments.profile:
        positions = boards()
        profiler = cProfile.Profile()
        profiler.enable()
        for _ in range(arguments.repeats):
            for board in positions:
                evaluate(board)
        profiler.disable()
        pstats.Stats(profiler).sort_stats("tottime").print_stats(arguments.rows)
        return

    rate = throughput(arguments.repeats)
    positions = boards()
    pieces = sum(bin(board.occupied).count("1") for board in positions) / len(positions)
    print(f"positions      {len(positions)} ({pieces:.1f} pieces on average)")
    print(f"evaluations/s  {rate:,.0f}")
    print(f"microseconds   {1e6 / rate:.2f} per evaluation")


if __name__ == "__main__":
    main()
