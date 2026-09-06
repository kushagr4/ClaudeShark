"""Does root instability mark the positions where ClaudeShark errs?

For each FEN the engine is searched at fixed depths (default 5,6,7,8) with a
fresh table, and the best move and score at each depth are recorded. A
position is "unstable at depth d" when the best move at d differs from the
one at d-1 or the root score moved by at least --jump cp. Run it on the
audited error positions and on matched non-error positions from the same
games; if instability is far more common at the errors, a time extension
triggered by instability is aimed at the right positions.

    uv run python -m tools.strength.instability_probe --engine champions/rc_c \
        --errors <errors.jsonl> --games <annotated.jsonl> --out <probe.jsonl>
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WORKER = r"""
import sys, json
sys.path.insert(0, sys.argv[1])
import chess
from cs_search import Searcher
fen, depths = sys.argv[2], json.loads(sys.argv[3])
out = []
for d in depths:
    s = Searcher()
    move, info = s.search(chess.Board(fen), 0, max_depth=d)
    out.append({"depth": d, "move": move.uci() if move else None, "score": info.score,
                "nodes": info.nodes, "ms": round(info.elapsed_ms)})
print(json.dumps(out))
"""


def ladder(engine: Path, fen: str, depths: list[int]) -> list[dict]:
    result = subprocess.run(
        [sys.executable, "-c", WORKER, str(engine.resolve()), fen, json.dumps(depths)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def unstable_flags(rows: list[dict], jump: int) -> list[bool]:
    flags = []
    for previous, current in zip(rows, rows[1:], strict=False):
        flags.append(current["move"] != previous["move"]
                     or abs(current["score"] - previous["score"]) >= jump)
    return flags


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--errors", type=Path, required=True)
    parser.add_argument("--games", type=Path, required=True,
                        help="annotated games, for negatives")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--depths", default="5,6,7,8")
    parser.add_argument("--jump", type=int, default=50)
    parser.add_argument("--negatives", type=int, default=120)
    parser.add_argument("--max-errors", type=int, default=120)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20260906)
    arguments = parser.parse_args()
    depths = [int(d) for d in arguments.depths.split(",")]

    errors = [json.loads(line) for line in arguments.errors.open(encoding="utf-8")]
    errors = [e for e in errors if "timed" in e][: arguments.max_errors]
    error_fens = {e["fen"] for e in errors}
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    pool = []
    for g in games:
        for m in g["moves"]:
            if m["turn"] != g["agent_colour"] or m["fen"] in error_fens:
                continue
            white = m["turn"] == "w"
            before = m["sf_cp_white_before"] if white else -m["sf_cp_white_before"]
            if int(m["cp_loss"]) < 30 and abs(before) < 800 and m["ply"] > 4:
                pool.append(m["fen"])
    rng = random.Random(arguments.seed)
    negatives = rng.sample(pool, min(arguments.negatives, len(pool)))

    jobs = [("error", e["fen"]) for e in errors] + [("negative", f) for f in negatives]
    print(f"{len(errors)} error positions, {len(negatives)} matched negatives, depths {depths}",
          flush=True)

    def work(job: tuple[str, str]) -> dict:
        kind, fen = job
        rows = ladder(arguments.engine, fen, depths)
        return {"kind": kind, "fen": fen, "ladder": rows,
                "unstable": unstable_flags(rows, arguments.jump)}

    with ThreadPoolExecutor(max_workers=arguments.workers) as executor:
        results = list(executor.map(work, jobs))
    with arguments.out.open("w", encoding="utf-8") as handle:
        for r in results:
            handle.write(json.dumps(r) + "\n")

    for kind in ("error", "negative"):
        rows = [r for r in results if r["kind"] == kind]
        if not rows:
            continue
        n = len(rows)
        any_unstable = sum(1 for r in rows if any(r["unstable"]))
        last = sum(1 for r in rows if r["unstable"][-1])
        by_step = [sum(1 for r in rows if r["unstable"][i]) for i in range(len(depths) - 1)]
        print(f"{kind:9s} n={n:3d}  unstable at any step {any_unstable} "
              f"({100 * any_unstable / n:.0f}%)  at the last step "
              f"({depths[-2]}->{depths[-1]}) {last} ({100 * last / n:.0f}%)  per step {by_step}")


if __name__ == "__main__":
    main()
