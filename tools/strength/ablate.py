"""Which pruning mechanism is responsible for an error? Fixed-depth ablation.

Each FEN is searched at a fixed depth by the same engine directory under
several environment configurations (the shipped one and one switch off at a
time), the chosen moves are oracle-scored, and the report says for each
configuration how many of the positions it repairs (loss < 100 cp) and at
what node cost. Fixed depth keeps the comparison deterministic; the
question is "does this mechanism cause the wrong move at this depth", not
"is it worth its time".

    uv run python -m tools.strength.ablate --engine champions/c5_rfp --fens targets.txt --depth 8 \
        --config base= --config rfp=CS_RFP=0 --config nmp=CS_NMP=0 --out ablate.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import chess

from tools.corpus.oracle import label_many

WORKER = r"""
import sys, json
sys.path.insert(0, sys.argv[1])
import chess
from cs_search import Searcher
fen, depth = sys.argv[2], int(sys.argv[3])
s = Searcher()
move, info = s.search(chess.Board(fen), 0, max_depth=depth)
print(json.dumps({"move": move.uci() if move else None, "score": info.score, "depth": info.depth,
                  "nodes": info.nodes, "pv": info.pv[:6]}))
"""


def run(engine: Path, fen: str, depth: int, env: dict[str, str]) -> dict:
    result = subprocess.run(
        [sys.executable, "-c", WORKER, str(engine.resolve()), fen, str(depth)],
        capture_output=True, text=True, check=True, env=env,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--fens", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--config", action="append", default=[],
                        help="name=VAR=value[,VAR=value]; 'base=' is the shipped configuration")
    parser.add_argument("--oracle-nodes", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    fens = [line.strip() for line in arguments.fens.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]
    base_env = {k: v for k, v in os.environ.items() if not k.startswith("CS_")}
    configs: dict[str, dict[str, str]] = {}
    for item in arguments.config or ["base="]:
        name, _, spec = item.partition("=")
        env = dict(base_env)
        for pair in spec.split(","):
            if pair:
                var, _, value = pair.partition("=")
                env[var] = value
        configs[name] = env

    jobs = [(name, fen) for fen in fens for name in configs]

    def work(job: tuple[str, str]) -> tuple[str, str, dict]:
        name, fen = job
        return name, fen, run(arguments.engine, fen, arguments.depth, configs[name])

    with ThreadPoolExecutor(max_workers=arguments.workers) as pool:
        results = list(pool.map(work, jobs))

    by: dict[str, dict[str, dict]] = {fen: {} for fen in fens}
    for name, fen, r in results:
        by[fen][name] = r

    positions: set[str] = set(fens)
    after: dict[tuple[str, str], str] = {}
    for fen in fens:
        board = chess.Board(fen)
        for r in by[fen].values():
            mv = r["move"]
            if mv and (fen, mv) not in after:
                b = board.copy()
                b.push(chess.Move.from_uci(mv))
                after[(fen, mv)] = b.fen()
                positions.add(b.fen())
    unique = sorted(positions)
    labels = {}
    for fen, label in zip(unique, label_many(unique, arguments.oracle_nodes, workers=6,
                                              progress=True), strict=True):
        labels[fen] = label.cp_white

    def loss(fen: str, mv: str | None) -> int | None:
        if not mv:
            return None
        white = chess.Board(fen).turn == chess.WHITE
        before = labels[fen] if white else -labels[fen]
        cp_after = labels[after[(fen, mv)]]
        cp_after = cp_after if white else -cp_after
        return max(0, before - cp_after)

    with arguments.out.open("w", encoding="utf-8") as handle:
        for fen in fens:
            row = {"fen": fen, "depth": arguments.depth}
            for name, r in by[fen].items():
                r["loss"] = loss(fen, r["move"])
                row[name] = r
            handle.write(json.dumps(row) + "\n")

    n = len(fens)
    base_bad: set[str] = set()
    if "base" in configs:
        base_bad = {fen for fen in fens if (by[fen]["base"]["loss"] or 0) >= 100}
    print(f"{n} positions at depth {arguments.depth}; base >= 100 cp on {len(base_bad)}")
    for name in configs:
        bad = sum(1 for fen in fens if (by[fen][name]["loss"] or 0) >= 100)
        repaired = sum(1 for fen in base_bad if (by[fen][name]["loss"] or 0) < 100)
        broken = sum(1 for fen in fens
                     if fen not in base_bad and (by[fen][name]["loss"] or 0) >= 100)
        nodes = sum(by[fen][name]["nodes"] for fen in fens)
        base_nodes = sum(by[fen]["base"]["nodes"] for fen in fens) if "base" in configs else nodes
        print(f"  {name:10s} >= 100 cp: {bad:3d}  repaired {repaired:3d}  broken {broken:3d}  "
              f"nodes {nodes:,} ({100.0 * (nodes / base_nodes - 1):+.0f}%)")


if __name__ == "__main__":
    main()
