"""Does spending more clock actually produce better moves?

The SEE experiment reduced nodes, raised depth, and gained no Elo. That made one
question central: when a change buys more search, does the extra search change
the *move*, and is the new move better?

This measures it directly for time policies. Two frozen engines are handed the
same clock on the same positions. Where they choose differently, a reference
search -- deeper and less selective than either -- scores both moves, and the
difference is reported in centipawns.

Three outcomes are worth distinguishing, and this tool separates them:

* the policies **agree**: the extra time bought nothing, good or bad;
* they disagree and the slower one is **better**: time is converting to strength;
* they disagree and the slower one is **worse**: time is being spent on noise.

    uv run python -m tools.timequality --a champions/v0_3 --b champions/v0_3_sf60 --clock 20000
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import chess

import cs_search
from cs_search import Searcher
from tools.positions import BALANCED_OPENINGS, SHARP_POSITIONS

PROBE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import chess
from cs_search import Searcher

clock = int(sys.argv[2])
out = []
for fen in json.loads(sys.argv[3]):
    searcher = Searcher()
    move, info = searcher.search(chess.Board(fen), clock)
    out.append({"fen": fen, "move": move.uci() if move else None,
                "depth": info.depth, "nodes": info.nodes, "score": info.score})
print(json.dumps(out))
"""


def run_engine(directory: Path, clock: int, fens: tuple[str, ...]) -> list[dict]:
    completed = subprocess.run(
        [sys.executable, "-c", PROBE, str(directory.resolve()), str(clock), json.dumps(list(fens))],
        capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"{directory} failed:\n{completed.stderr[-800:]}")
    return json.loads(completed.stdout)


def reference_score(fen: str, move_uci: str, depth: int) -> int:
    """Score a move by searching the position after it with a strong reference.

    The reference runs PVS only -- score-exact -- with null-move and LMR off, so
    it is the least selective searcher available at an affordable cost.
    """
    board = chess.Board(fen)
    board.push(chess.Move.from_uci(move_uci))
    _, info = Searcher().search(board, 0, max_depth=depth)
    return -info.score


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two time policies by move quality.")
    parser.add_argument("--a", type=Path, required=True, help="baseline engine directory")
    parser.add_argument("--b", type=Path, required=True, help="candidate engine directory")
    parser.add_argument("--clock", type=int, default=20_000)
    parser.add_argument("--ref-depth", type=int, default=8)
    parser.add_argument("--suite", choices=("balanced", "sharp", "both"), default="both")
    arguments = parser.parse_args()

    if arguments.suite == "balanced":
        fens = BALANCED_OPENINGS
    elif arguments.suite == "sharp":
        fens = SHARP_POSITIONS
    else:
        fens = BALANCED_OPENINGS + SHARP_POSITIONS

    print(
        f"clock {arguments.clock} ms, {len(fens)} positions, "
        f"reference depth {arguments.ref_depth}"
    )
    left = run_engine(arguments.a, arguments.clock, fens)
    right = run_engine(arguments.b, arguments.clock, fens)

    # Reference runs in this process, least-selective settings.
    cs_search.USE_NULL_MOVE = False
    cs_search.USE_LMR = False
    cs_search.USE_SEE_QS = False
    cs_search.USE_SEE_ORDER = False

    agreed = 0
    better = worse = equal = 0
    total_delta = 0
    detail: list[str] = []

    for one, two in zip(left, right, strict=True):
        assert one["fen"] == two["fen"]
        if one["move"] == two["move"]:
            agreed += 1
            continue
        a_score = reference_score(one["fen"], one["move"], arguments.ref_depth)
        b_score = reference_score(two["fen"], two["move"], arguments.ref_depth)
        delta = b_score - a_score
        total_delta += delta
        if delta > 5:
            better += 1
        elif delta < -5:
            worse += 1
        else:
            equal += 1
        detail.append(
            f"  {one['fen'][:40]}...  A={one['move']}(d{one['depth']}) "
            f"B={two['move']}(d{two['depth']})  delta {delta:+d}cp"
        )

    disagreements = len(left) - agreed
    a_depth = sum(r["depth"] for r in left) / len(left)
    b_depth = sum(r["depth"] for r in right) / len(right)

    print(f"\nA = {arguments.a}   mean depth {a_depth:.2f}")
    print(f"B = {arguments.b}   mean depth {b_depth:.2f}   ({b_depth - a_depth:+.2f} ply)")
    print(f"\nagreed on {agreed}/{len(left)} positions")
    if disagreements:
        print(f"of the {disagreements} disagreements, by the reference:")
        print(f"  B better  {better}")
        print(f"  B worse   {worse}")
        print(f"  level     {equal}")
        per = total_delta / disagreements
        print(f"  net       {total_delta:+d} cp  ({per:+.1f} cp per disagreement)")
        for line in detail[:10]:
            print(line)


if __name__ == "__main__":
    main()
