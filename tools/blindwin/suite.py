"""Blind-win regression suite: real positions the root search scores near zero and Stockfish calls won.

Built from the blind episodes with the oracle labels already attached. Each
record carries the source game, cluster, colour, ply, Stockfish score, WDL,
mate distance, best move and PV at the labelling budget, production's root,
static and PV-end static at build time, the mechanism read off the PV, the
horizon/blind verdict, and the depth-ladder verdict where the position was on
the ladder. Split by cluster parity into a diagnostic half and a validation
half that comes from different games and is never tuned against.

Stratified so that no mechanism dominates: at most ``--per-class`` per
mechanism, chosen by the largest Stockfish-vs-root gap.

    uv run python -m tools.blindwin.suite --episodes corpus/blindwin/03_gap.jsonl --out corpus/blindwin_regression_v1.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--ladder", type=Path, default=None)
    parser.add_argument("--per-class", type=int, default=14)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    episodes = [json.loads(line) for line in arguments.episodes.open(encoding="utf-8")]
    ladder = {}
    if arguments.ladder and arguments.ladder.exists():
        for row in json.loads(arguments.ladder.read_text(encoding="utf-8")):
            ladder[row["fen"]] = row["verdict"]

    by = defaultdict(list)
    seen = set()
    for e in sorted(episodes, key=lambda e: -(min(e["sf_cp_1m"], 2000) - e["root"])):
        if e["fen"] in seen:
            continue
        seen.add(e["fen"])
        by[e["mechanism"]].append(e)
    picks = []
    for es in by.values():
        picks.extend(es[: arguments.per_class])

    rows = []
    for i, e in enumerate(sorted(picks, key=lambda e: (e["mechanism"], e["cluster"]))):
        rows.append({
            "id": f"bw-{i:03d}", "fen": e["fen"], "source": e["source"], "cluster": e["cluster"],
            "colour": "white" if e["fen"].split()[1] == "w" else "black", "ply": e["ply"],
            "sf_cp_stm": e["sf_cp_1m"], "sf_wdl_stm": e["sf_wdl"], "sf_mate": e["sf_mate"],
            "sf_best": e["sf_best"], "pv": e["pv"], "nodes": 1_000_000,
            "root_at_build": e["root"], "static_at_build": e["static"], "played_at_build": e["move"],
            "loss_at_build": e["cp_loss"], "static_at_pv_end": e["static_at_pv_end"],
            "sf_at_pv_end": e["sf_at_pv_end"], "mechanism": e["mechanism"],
            "horizon_or_blind": e["horizon_or_blind"].split(" ")[0], "depth_verdict": ladder.get(e["fen"]),
            "phase": e["phase"], "tags": e["tags"], "material": e["material"],
            "role": "diagnostic" if int(e["cluster"]) % 2 == 0 else "validation",
            "provenance": "fixed-depth self-play, production to move; corpus/blindwin/episodes.jsonl",
        })
    body = "\n".join(json.dumps(r) for r in rows)
    header = {"record": "header", "suite": "blindwin_regression", "version": "v1", "size": len(rows),
              "selection": f"Stockfish >= +300, root < +100, top {arguments.per_class} per mechanism by gap",
              "mechanisms": dict(Counter(r["mechanism"] for r in rows)),
              "horizon_or_blind": dict(Counter(r["horizon_or_blind"] for r in rows)),
              "roles": dict(Counter(r["role"] for r in rows)),
              "hash": hashlib.sha256(body.encode()).hexdigest()[:16]}
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    with arguments.out.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(header) + "\n")
        fh.write(body + "\n")
    print(json.dumps(header, indent=1))


if __name__ == "__main__":
    main()
