"""Play whole games on the real 120 s + 0.5 s clock and record how time is spent.

Fixed-budget benchmarks hand the engine a budget; this watches it choose one,
move after move, on a clock that depletes. It is the only instrument here that
can see time-management pathologies: front-loading, leaving the clock unspent at
the end, emergency mode firing when it should not, or an increment accounting
error that only compounds over fifty moves.

The clock arithmetic is the referee's: subtract the wall time we measured around
the call, then credit the increment.

    uv run python -m tools.gamesim --games 2
    uv run python -m tools.gamesim --games 1 --base-ms 120000 --csv game.csv
"""

from __future__ import annotations

import argparse
import csv
import statistics
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import chess

from cs_search import Searcher
from cs_time import PANIC_MS
from tools.positions import BALANCED_OPENINGS


@dataclass
class Ply:
    game: int
    ply: int
    side: str
    clock_before_ms: float
    soft_ms: float
    hard_ms: float
    spent_ms: float
    depth: int
    unstable: int
    nodes: int
    panic: bool
    clock_after_ms: float


def play(game_index: int, fen: str, base_ms: int, increment_ms: int, ply_cap: int) -> list[Ply]:
    board = chess.Board(fen)
    searchers = {chess.WHITE: Searcher(), chess.BLACK: Searcher()}
    clocks = {chess.WHITE: float(base_ms), chess.BLACK: float(base_ms)}
    rows: list[Ply] = []

    while len(board.move_stack) < ply_cap and not board.is_game_over(claim_draw=True):
        mover = board.turn
        searcher = searchers[mover]
        before = clocks[mover]

        started = perf_counter()
        move, info = searcher.search(chess.Board(board.fen()), int(before))
        spent = (perf_counter() - started) * 1000.0

        if move is None:
            break
        clocks[mover] -= spent
        rows.append(
            Ply(
                game=game_index,
                ply=len(board.move_stack),
                side="white" if mover else "black",
                clock_before_ms=before,
                soft_ms=info.budget_ms,
                hard_ms=searcher.time.hard_ms,
                spent_ms=spent,
                depth=info.depth,
                unstable=info.unstable_iterations,
                nodes=info.nodes,
                panic=before <= PANIC_MS,
                clock_after_ms=clocks[mover],
            )
        )
        if clocks[mover] <= 0.0:
            print(f"  FLAG: {rows[-1].side} at ply {rows[-1].ply}")
            break
        clocks[mover] += increment_ms
        board.push(move)

    return rows


def report(rows: list[Ply], base_ms: int) -> None:
    if not rows:
        print("no plies recorded")
        return

    spent = [row.spent_ms for row in rows]
    used = [100.0 * row.spent_ms / row.soft_ms if row.soft_ms else 0.0 for row in rows]
    overruns = [row for row in rows if row.spent_ms > row.hard_ms * 1.15]
    panics = [row for row in rows if row.panic]
    lowest = min(row.clock_after_ms for row in rows)

    # Split the game in half to expose front-loading.
    half = len(rows) // 2 or 1
    first, second = rows[:half], rows[half:]

    print(f"\nplies              {len(rows)}")
    print(f"time per move      mean {statistics.mean(spent):7.0f} ms   "
          f"median {statistics.median(spent):7.0f} ms   max {max(spent):7.0f} ms")
    print(f"soft budget used   mean {statistics.mean(used):7.1f}%")
    print(f"depth              mean {statistics.mean(r.depth for r in rows):7.2f}   "
          f"min {min(r.depth for r in rows)}   max {max(r.depth for r in rows)}")
    print(f"first half / second   {statistics.mean(r.spent_ms for r in first):.0f} ms  vs  "
          f"{statistics.mean(r.spent_ms for r in second):.0f} ms per move")
    print(f"lowest clock       {lowest:,.0f} ms of {base_ms:,} "
          f"({100.0 * lowest / base_ms:.1f}% remaining at the worst point)")
    print(f"hard-deadline overruns  {len(overruns)}")
    print(f"panic-mode plies        {len(panics)}")
    if overruns:
        for row in overruns[:5]:
            print(f"  ply {row.ply} {row.side}: spent {row.spent_ms:.0f} ms "
                  f"of a {row.hard_ms:.0f} ms hard deadline")


def main() -> None:
    parser = argparse.ArgumentParser(description="Full-game clock behaviour.")
    parser.add_argument("--games", type=int, default=2)
    parser.add_argument("--base-ms", type=int, default=120_000)
    parser.add_argument("--increment-ms", type=int, default=500)
    parser.add_argument("--ply-cap", type=int, default=200)
    parser.add_argument("--csv", type=Path, default=None)
    arguments = parser.parse_args()

    rows: list[Ply] = []
    for index in range(arguments.games):
        fen = BALANCED_OPENINGS[index % len(BALANCED_OPENINGS)]
        print(f"game {index + 1}/{arguments.games} from {fen}", flush=True)
        rows += play(index, fen, arguments.base_ms, arguments.increment_ms, arguments.ply_cap)

    report(rows, arguments.base_ms)

    if arguments.csv:
        with arguments.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["game", "ply", "side", "clock_before_ms", "soft_ms", "hard_ms",
                 "spent_ms", "depth", "unstable", "nodes", "panic", "clock_after_ms"]
            )
            for row in rows:
                writer.writerow(
                    [row.game, row.ply, row.side, f"{row.clock_before_ms:.0f}",
                     f"{row.soft_ms:.0f}", f"{row.hard_ms:.0f}", f"{row.spent_ms:.0f}",
                     row.depth, row.unstable, row.nodes, int(row.panic),
                     f"{row.clock_after_ms:.0f}"]
                )
        print(f"\nper-ply detail written to {arguments.csv}")


if __name__ == "__main__":
    main()
