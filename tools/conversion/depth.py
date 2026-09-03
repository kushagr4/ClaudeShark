"""Depth scaling of conversion failures: search/horizon or evaluation?

For each collapse position -- the move that lost the advantage in a failed
conversion -- the production engine is run at a ladder of fixed depths and
every chosen move is scored by Stockfish against the position's best move.

The classification is the point:

    A  fixed by +1 ply           horizon, cheap
    B  fixed by +2 plies         horizon
    C  needs substantially more  horizon, expensive
    D  persists at the top depth evaluation (or a deeper horizon than we can buy)
    E  unstable / oscillating    the engine's score is not converging

"Fixed" means the chosen move's Stockfish loss falls under `--fixed-at` cp.
The engine's own game-level repetition record is not replayed here: these are
mid-game positions where a repetition is not the issue, and a fresh searcher
keeps the ladder comparable across depths.

    uv run python -m tools.conversion.depth --engine <dir> --cases <json> --out <txt>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from tools.corpus.oracle import Oracle
from tools.postmortem.play import Engine


def classify(losses: list[int], depths: list[int], fixed_at: int) -> str:
    base = losses[0]
    if base < fixed_at:
        return "-"  # not an error at the base depth; nothing to fix
    fixed = [d for d, v in zip(depths, losses, strict=True) if v < fixed_at]
    if not fixed:
        return "D persists"
    first = fixed[0] - depths[0]
    # Once fixed, does it stay fixed?
    after = [v for d, v in zip(depths, losses, strict=True) if d >= fixed[0]]
    if any(v >= fixed_at for v in after):
        return "E unstable"
    if first == 1:
        return "A +1 ply"
    if first == 2:
        return "B +2 plies"
    return "C deeper"


def main() -> None:
    parser = argparse.ArgumentParser(description="Depth ladder over conversion failures.")
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--depths", default="6,7,8,9,10")
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--fixed-at", type=int, default=50)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    depths = [int(d) for d in arguments.depths.split(",")]
    cases = json.loads(arguments.cases.read_text(encoding="utf-8"))
    engines = {d: Engine(arguments.engine, d) for d in depths}
    rows = []
    lines = [f"== DEPTH LADDER over {len(cases)} conversion-failure positions (production, depths {depths}) ==",
             f"loss = Stockfish cp given up by the chosen move at {arguments.nodes} nodes; 'fixed' = loss < {arguments.fixed_at}", ""]
    try:
        with Oracle() as oracle:
            for i, case in enumerate(cases, start=1):
                fen = case["fen"]
                best = oracle.analyse(fen, arguments.nodes)
                cache: dict[str, int] = {}
                chosen, scores, losses, nodes = [], [], [], []
                for d in depths:
                    e = engines[d]
                    e.ask("new")
                    r = e.ask(f"go {fen}")
                    mv = r["move"]
                    if mv not in cache:
                        child = oracle.score_after(fen, mv, arguments.nodes)
                        cache[mv] = max(0, best.cp_stm + child.cp_stm)
                    chosen.append(mv)
                    scores.append(r["score"])
                    losses.append(cache[mv])
                    nodes.append(r["nodes"])
                verdict = classify(losses, depths, arguments.fixed_at)
                row = {**case, "sf_best": best.best, "sf_cp_stm": best.cp_stm,
                       "depths": depths, "moves": chosen, "engine_scores": scores,
                       "losses": losses, "nodes": nodes, "verdict": verdict}
                rows.append(row)
                lines.append(f"-- [{i}] cluster {case.get('cluster')} {case.get('label', '')}")
                lines.append(f"   {fen}")
                lines.append(f"   Stockfish {best.cp_stm:+} best {best.best}   verdict: {verdict}")
                lines.append(f"   {'depth':>6} {'move':<7} {'score':>7} {'loss':>6} {'nodes':>10}")
                for d, mv, sc, lo, nd in zip(depths, chosen, scores, losses, nodes, strict=True):
                    lines.append(f"   {d:>6} {mv:<7} {sc:>+7} {lo:>6} {nd:>10,}")
                print(lines[-len(depths) - 4], lines[-len(depths) - 2], flush=True)
    finally:
        for e in engines.values():
            e.close()
    lines += ["", f"verdicts: {dict(Counter(r['verdict'] for r in rows))}"]
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("\n".join(lines[-2:]))


if __name__ == "__main__":
    main()
