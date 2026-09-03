"""Run an engine on the blind-win regression suite and report by role, mechanism and cluster.

The suite's rows are unique positions, so row statistics are unique-FEN
statistics; the cluster figures weight each source game equally so that a
game contributing three positions does not count three times. ``--role``
restricts the run to one half, which is how coefficients are chosen on the
diagnostic half without the validation half ever being read.

    uv run python -m tools.blindwin.run --suite corpus/blindwin_regression_v1.jsonl --engine <dir> --depth 6 --out <txt>
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

from tools.corpus.oracle import Oracle
from tools.postmortem.play import Engine


def summarise(rows: list[dict], title: str) -> list[str]:
    lines = [f"{title}", f"  {'group':<34} {'n':>3} {'clus':>4} {'robust':>7} {'cl-rob':>7} {'serious':>8} {'catast':>7} {'agree':>6} {'root':>6} {'droot':>6} {'root<100':>8}"]
    by: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        by[(r["role"], "ALL")].append(r)
        by[(r["role"], "mech " + r["mechanism"])].append(r)
        by[(r["role"], "hb " + r["horizon_or_blind"])].append(r)
    for (role, group), rs in sorted(by.items()):
        n = len(rs)
        clusters: dict[int, list[dict]] = defaultdict(list)
        for r in rs:
            clusters[int(r["cluster"])].append(r)
        cluster_robust = statistics.mean(statistics.mean(min(x["loss"], 500) for x in c) for c in clusters.values())
        lines.append(f"  {role + ' ' + group:<34} {n:>3} {len(clusters):>4} {sum(min(r['loss'], 500) for r in rs) / n:>7.1f} {cluster_robust:>7.1f} "
                     f"{sum(r['loss'] >= 100 for r in rs) / n:>8.1%} {sum(r['loss'] >= 300 for r in rs) / n:>7.1%} "
                     f"{sum(r['move'] == r['sf_best'] for r in rs) / n:>6.1%} {statistics.mean(r['root'] for r in rs):>+6.0f} "
                     f"{statistics.mean(r['root'] - r['root_at_build'] for r in rs):>+6.0f} {sum(r['root'] < 100 for r in rs):>5}/{n:<2}")
    return lines


def run(suite: Path, engine_dir: Path, depth: int, role: str) -> tuple[dict, list[dict]]:
    rows = [json.loads(line) for line in suite.open(encoding="utf-8")]
    header, rows = rows[0], rows[1:]
    if role != "all":
        rows = [r for r in rows if r["role"] == role]
    assert len({r["fen"] for r in rows}) == len(rows), "suite rows are unique positions"
    engine = Engine(engine_dir, depth)
    results = []
    try:
        with Oracle() as oracle:
            for r in rows:
                engine.ask("new")
                reply = engine.ask(f"go {r['fen']}")
                child = oracle.score_after(r["fen"], reply["move"], r.get("nodes", 1_000_000))
                loss = max(0, r["sf_cp_stm"] + child.cp_stm)
                white = r["fen"].split()[1] == "w"
                results.append({**r, "move": reply["move"], "root": reply["score"], "loss": loss,
                                "static": reply["static"] if white else -reply["static"], "nodes_used": reply["nodes"]})
    finally:
        engine.close()
    return header, results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--role", choices=("all", "diagnostic", "validation"), default="all")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    header, results = run(arguments.suite, arguments.engine, arguments.depth, arguments.role)
    lines = [f"== BLIND-WIN REGRESSION SUITE {header['version']} ({len(results)} positions of {header['size']}, hash {header['hash']}, role {arguments.role}) "
             f"engine {arguments.engine} depth {arguments.depth} ==", "",
             "loss = Stockfish cp given up by the chosen move; robust winsorises at 500; cl-rob = mean of per-cluster means;",
             "root = engine root score (side to move), droot = change since the suite was built; root<100 = still blind at the root", ""]
    lines += summarise(results, "by role, mechanism and horizon/blind verdict")
    text = "\n".join(lines)
    print(text)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in results) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
