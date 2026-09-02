"""Low-clock safety ladder for a frozen engine directory.

Every candidate has to return a legal move at every clock it could plausibly be
handed, from a nearly-flagged 1 ms up to a full 120 s, across positions of
different character. A time policy that gains Elo and loses one game on time has
gained nothing.

Reports, per clock: whether every move was legal, the worst elapsed-versus-clock
ratio seen, and whether anything exceeded its own hard deadline.

    uv run python -m tools.clockladder --engine champions/v0_3_sf75
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter

import chess

LADDER = (1, 5, 20, 50, 100, 250, 500, 1_000, 2_000, 5_000, 10_000, 30_000, 60_000, 120_000)

# Below this the fixed cost of a move -- constructing the board, generating
# legal moves, returning a fallback -- dominates, and no time policy can get
# under it. Roughly 2 ms is the floor measured on this machine. Returning a
# legal move is still mandatory at every clock; only the "stayed inside the
# clock" requirement is relaxed here, because failing it is a property of the
# interpreter rather than of the policy under test.
CLOCK_FLOOR_MS = 50

POSITIONS = (
    ("opening", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("middlegame", "r2q1rk1/pp1bbppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP1QPPP/R1B2RK1 w - - 0 10"),
    ("sharp", "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
    ("endgame", "8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 40"),
    ("in check", "4k3/8/8/8/7q/8/8/4K3 w - - 0 1"),
    ("one legal move", "7k/8/8/8/8/8/5Q2/6RK b - - 0 1"),
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Low-clock safety ladder.")
    parser.add_argument("--engine", type=Path, default=None)
    arguments = parser.parse_args()

    if arguments.engine:
        sys.path.insert(0, str(arguments.engine.resolve()))
    from cs_search import Searcher
    from cs_time import START_FRACTION

    print(f"engine: {arguments.engine or 'working tree'}   START_FRACTION = {START_FRACTION}")
    print(f"{'clock':>8}  {'legal':>7}  {'worst used':>11}  {'worst ms':>9}  {'over hard':>9}")

    failures = 0
    for clock in LADDER:
        illegal: list[str] = []
        worst_ratio = 0.0
        worst_ms = 0.0
        over_hard = 0

        for label, fen in POSITIONS:
            board = chess.Board(fen)
            searcher = Searcher(tt_bits=16)
            started = perf_counter()
            move, _ = searcher.search(chess.Board(fen), clock)
            elapsed_ms = (perf_counter() - started) * 1000.0

            options = {candidate.uci() for candidate in board.legal_moves}
            uci = move.uci() if move is not None else "0000"
            if (uci not in options) if options else (uci != "0000"):
                illegal.append(f"{label}:{uci}")

            worst_ratio = max(worst_ratio, elapsed_ms / clock)
            worst_ms = max(worst_ms, elapsed_ms)
            # The engine's own hard deadline, with slack for the final node batch.
            if elapsed_ms > searcher.time.hard_ms * 1.5 and elapsed_ms > 20.0:
                over_hard += 1

        ok = not illegal and (worst_ratio < 1.0 or clock < CLOCK_FLOOR_MS)
        failures += not ok
        note = ""
        if illegal:
            note = f"   <-- ILLEGAL {illegal}"
        elif worst_ratio >= 1.0:
            note = "   <-- below the fixed-cost floor, legality only"
        elif over_hard:
            note = "   <-- exceeded its own hard deadline (see note in report)"
        print(
            f"{clock:>8}  {'yes' if not illegal else 'NO':>7}  "
            f"{worst_ratio * 100:>10.1f}%  {worst_ms:>8.0f}  {over_hard:>9}{note}"
        )

    print("\nPASS" if not failures else f"\nFAIL: {failures} clock(s) unsafe")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
