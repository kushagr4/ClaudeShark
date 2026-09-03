"""Make counter-instrumented scratch copies of two engine snapshots.

The v0.6 post-mortem needs to know how often each pruning mechanism fires in
the candidate against the baseline. Production keeps no such counters, so this
copies each snapshot to a scratch directory and patches ``cs_search.py`` with
pure counters -- no control flow changes -- at the null-move, LMR, aspiration
and quiescence pruning sites. The patched engine must search exactly the same
tree; ``verify`` proves it by comparing depth-6 node counts with the original.

    uv run python -m tools.postmortem.instrument --out <scratch>
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SNAPSHOTS = {
    "baseline": Path("champions/v0_5_2_correctness"),
    "scale": Path("champions/v0_6_material_scale"),
}

COUNTERS = (
    "c_null_tries",
    "c_null_cuts",
    "c_lmr_reduced",
    "c_lmr_research",
    "c_asp_low",
    "c_asp_high",
    "c_delta_pruned",
    "c_see_pruned",
    "c_qs_standpat",
)

# (old, new, expected occurrences)
PATCHES = [
    (
        "        self.researches = 0\n",
        "        self.researches = 0\n" + "".join(f"        self.{c} = 0\n" for c in COUNTERS),
        2,
    ),
    (
        "            self.researches += 1\n            if score <= alpha:\n",
        "            self.researches += 1\n            if score <= alpha:\n"
        "                self.c_asp_low += 1\n",
        1,
    ),
    (
        "            else:\n                beta = score + delta\n",
        "            else:\n                self.c_asp_high += 1\n                beta = score + delta\n",
        1,
    ),
    (
        "            null_score = -self._negamax(\n",
        "            self.c_null_tries += 1\n            null_score = -self._negamax(\n",
        1,
    ),
    (
        "            if null_score >= beta:\n",
        "            if null_score >= beta:\n                self.c_null_cuts += 1\n",
        1,
    ),
    (
        "            if move_index == 0:\n                score = -self._negamax(board, child_depth, -beta, -alpha, child_ply)\n",
        "            if reduction:\n                self.c_lmr_reduced += 1\n"
        "            if move_index == 0:\n                score = -self._negamax(board, child_depth, -beta, -alpha, child_ply)\n",
        1,
    ),
    (
        "                if reduction and score > alpha:\n",
        "                if reduction and score > alpha:\n                    self.c_lmr_research += 1\n",
        2,
    ),
    (
        "                if stand_pat + gain + DELTA_MARGIN < alpha:\n                    continue\n",
        "                if stand_pat + gain + DELTA_MARGIN < alpha:\n"
        "                    self.c_delta_pruned += 1\n                    continue\n",
        1,
    ),
    (
        "            if losing_capture and not board.is_check():\n                pop()\n                continue\n",
        "            if losing_capture and not board.is_check():\n                pop()\n"
        "                self.c_see_pruned += 1\n                continue\n",
        1,
    ),
]


def patch(src: str) -> str:
    for old, new, expected in PATCHES:
        n = src.count(old)
        if n != expected:
            raise SystemExit(f"patch site found {n} times, expected {expected}:\n{old}")
        src = src.replace(old, new)
    return src


def build(out: Path) -> dict[str, Path]:
    built = {}
    for name, snap in SNAPSHOTS.items():
        dest = out / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(snap, dest, ignore=shutil.ignore_patterns("__pycache__"))
        path = dest / "cs_search.py"
        path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
        built[name] = dest
    return built


PROBE = """
import sys, json, chess
sys.path.insert(0, sys.argv[1])
from cs_search import Searcher
fens = ["r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
        "8/2r4k/2pq2p1/2Rp1r1p/p3pP1P/P3P1Q1/1P4PK/2R5 w - - 2 37",
        "6R1/8/3k4/pp1p2pB/1n5b/4K2P/8/8 w - - 0 40"]
out = []
for f in fens:
    s = Searcher(); s.new_game()
    m, info = s.search(chess.Board(f), 60000, max_depth=6)
    out.append((m.uci(), info.nodes))
print(json.dumps(out))
"""


def verify(built: dict[str, Path]) -> None:
    for name, dest in built.items():
        a = subprocess.run(
            [sys.executable, "-c", PROBE, str(SNAPSHOTS[name])],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        b = subprocess.run(
            [sys.executable, "-c", PROBE, str(dest)], capture_output=True, text=True, check=True
        ).stdout.strip()
        status = "identical" if a == b else "MISMATCH"
        print(f"{name:<9} original {a}\n{'':<9} patched  {b}   -> {status}")
        if a != b:
            raise SystemExit("instrumentation changed the search")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    built = build(arguments.out)
    verify(built)
    print("instrumented engines:", {k: str(v) for k, v in built.items()})


if __name__ == "__main__":
    main()
