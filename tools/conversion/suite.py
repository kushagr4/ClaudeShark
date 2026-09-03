"""Conversion regression suite: build it from real self-play, and run an engine on it.

Every position comes from a retained fixed-depth self-play game with the move
history intact, so each record carries its game, cluster, colour and ply, the
Stockfish score and best move at a fixed node budget, and the production
engine's depth-6 choice and loss at the time the suite was built.

Sources, chosen to cover the failure modes the audit measured rather than to
be numerous:

    first_error   the first serious error of a failed conversion from +200
    missed_mate   the largest-loss move of a failed conversion, where a mate
                  was on the board and missed
    blind         a winning position (Stockfish >= +300) the engine's root
                  score put under +100 -- the largest gaps
    defence       the first serious error of a failed defence from -200
    control       the +300 crossing of a conversion that succeeded

The split is by cluster parity so the two halves come from different games:
even clusters are *diagnostic* (look at these, fix against these), odd
clusters are *validation* (never tuned against). It is a regression tool and
says nothing about Elo; the fixed-depth paired game set does that.

    uv run python -m tools.conversion.suite build --episodes ... --games ... --out corpus/conversion_regression_v1.jsonl
    uv run python -m tools.conversion.suite run --suite ... --engine <dir> --depth 6
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import chess

from tools.conversion.first_error import classify
from tools.corpus.oracle import Oracle
from tools.postmortem.play import Engine


def own(m: dict) -> int:
    return m["sf_cp_white_before"] if m["turn"] == "w" else -m["sf_cp_white_before"]


def build(arguments: argparse.Namespace) -> None:
    games = {(g["cluster"], g["cand_white"]): g for g in
             (json.loads(line) for line in arguments.games.open(encoding="utf-8"))}
    episodes = [json.loads(line) for line in arguments.episodes.open(encoding="utf-8")]
    prod = [e for e in episodes if e["engine"] == "v0.5.2 production"]
    ladder = {}
    if arguments.ladder and arguments.ladder.exists():
        for row in json.loads(arguments.ladder.read_text(encoding="utf-8")):
            ladder[row["fen"]] = row["verdict"]

    picks: list[dict] = []
    seen: set[str] = set()

    def add(fen, source, e, extra):
        if fen in seen:
            return
        seen.add(fen)
        picks.append({"fen": fen, "source": source, "cluster": e["cluster"], "cand_white": e["cand_white"],
                      "colour": e["colour"], "episode_threshold": e["threshold"], "result": e["result"], **extra})

    for e in prod:
        if e["threshold"] == 200 and e["result"] < 1.0:
            f = e["first_serious_error"]
            if f:
                add(f["fen"], "first_error", e, {"ply": f["ply"], "played": f["move"], "loss_at_build": f["cp_loss"],
                                                  "standing": f["standing_before"]})
            c = e["collapse"]
            if c and c["standing_before"] >= 9000:
                add(c["fen"], "missed_mate", e, {"ply": c["ply"], "played": c["move"], "loss_at_build": c["cp_loss"],
                                                  "standing": c["standing_before"]})
        if e["threshold"] == -200 and e["result"] == 0.0:
            f = e["first_serious_error"]
            if f:
                add(f["fen"], "defence", e, {"ply": f["ply"], "played": f["move"], "loss_at_build": f["cp_loss"],
                                              "standing": f["standing_before"]})
    # Blind winning positions: largest Stockfish-vs-root gaps.
    blind = []
    for (cl, cw), g in games.items():
        for m in g["moves"]:
            if m["mover"] == "base" and 300 <= own(m) < 9000 and m["score_stm"] < 100:
                blind.append((own(m) - m["score_stm"], m, cl, cw))
    blind.sort(key=lambda r: -r[0])
    for _gap, m, cl, cw in blind[:arguments.blind]:
        e = {"cluster": cl, "cand_white": cw, "colour": "white" if m["turn"] == "w" else "black",
             "threshold": 300, "result": None}
        add(m["fen"], "blind", e, {"ply": m["ply"], "played": m["move"], "loss_at_build": m["cp_loss"],
                                   "standing": own(m), "root_at_build": m["score_stm"]})
    # Controls: successful conversions' +300 crossing.
    ok = [e for e in prod if e["threshold"] == 300 and e["result"] == 1.0]
    for e in ok[:arguments.controls]:
        add(e["fen"], "control", e, {"ply": e["ply"], "played": None, "loss_at_build": None, "standing": e["sf_cp"]})

    rows = []
    with Oracle() as oracle:
        for i, p in enumerate(picks):
            board = chess.Board(p["fen"])
            label = oracle.analyse(p["fen"], arguments.nodes)
            cat = None
            if p["played"]:
                cat = classify(board, p["played"], label.best, p["loss_at_build"] or 0, label)
            rows.append({
                "id": f"cv-{i:03d}", **p,
                "sf_cp_stm": label.cp_stm, "sf_wdl_stm": list(label.wdl_stm) if label.wdl_stm else None,
                "sf_best": label.best, "sf_mate": label.mate, "nodes": arguments.nodes,
                "category": cat, "depth_verdict": ladder.get(p["fen"]),
                "role": "diagnostic" if int(p["cluster"]) % 2 == 0 else "validation",
                "provenance": "fixed-depth self-play, corpus/postmortem/games/annotated.jsonl",
            })
    body = "\n".join(json.dumps(r) for r in rows)
    header = {"record": "header", "suite": "conversion_regression", "version": "v1",
              "size": len(rows), "nodes": arguments.nodes,
              "sources": dict(Counter(r["source"] for r in rows)),
              "roles": dict(Counter(r["role"] for r in rows)),
              "hash": hashlib.sha256(body.encode()).hexdigest()[:16]}
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    with arguments.out.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(header) + "\n")
        fh.write(body + "\n")
    print(json.dumps(header, indent=1))
    print(f"categories: {dict(Counter(r['category'] for r in rows))}")
    print(f"depth verdicts: {dict(Counter(r['depth_verdict'] for r in rows))}")


def run(arguments: argparse.Namespace) -> None:
    rows = [json.loads(line) for line in arguments.suite.open(encoding="utf-8")]
    header, rows = rows[0], rows[1:]
    engine = Engine(arguments.engine, arguments.depth)
    results = []
    try:
        with Oracle() as oracle:
            for r in rows:
                engine.ask("new")
                reply = engine.ask(f"go {r['fen']}")
                child = oracle.score_after(r["fen"], reply["move"], header["nodes"])
                loss = max(0, r["sf_cp_stm"] + child.cp_stm)
                results.append({**r, "move": reply["move"], "root": reply["score"], "loss": loss})
    finally:
        engine.close()
    out = [f"== CONVERSION REGRESSION SUITE {header['version']} ({header['size']} positions, hash {header['hash']}) "
           f"engine {arguments.engine} depth {arguments.depth} ==", ""]
    out.append(f"{'role':<11} {'source':<12} {'n':>3} {'robust':>7} {'serious':>8} {'catast':>7} {'agree':>6}")
    by = defaultdict(list)
    for r in results:
        by[(r["role"], r["source"])].append(r)
        by[(r["role"], "ALL")].append(r)
    for (role, src), rs in sorted(by.items()):
        n = len(rs)
        out.append(f"{role:<11} {src:<12} {n:>3} {sum(min(r['loss'], 500) for r in rs) / n:>7.1f} "
                   f"{sum(r['loss'] >= 100 for r in rs) / n:>8.1%} {sum(r['loss'] >= 300 for r in rs) / n:>7.1%} "
                   f"{sum(r['move'] == r['sf_best'] for r in rs) / n:>6.1%}")
    text = "\n".join(out)
    print(text)
    if arguments.out:
        arguments.out.write_text(text + "\n", encoding="utf-8")
        arguments.out.with_suffix(".jsonl").write_text(
            "\n".join(json.dumps(r) for r in results) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--episodes", type=Path, required=True)
    b.add_argument("--games", type=Path, required=True)
    b.add_argument("--ladder", type=Path, default=None)
    b.add_argument("--blind", type=int, default=15)
    b.add_argument("--controls", type=int, default=10)
    b.add_argument("--nodes", type=int, default=1_000_000)
    b.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("run")
    r.add_argument("--suite", type=Path, required=True)
    r.add_argument("--engine", type=Path, required=True)
    r.add_argument("--depth", type=int, default=6)
    r.add_argument("--out", type=Path, default=None)
    arguments = parser.parse_args()
    (build if arguments.cmd == "build" else run)(arguments)


if __name__ == "__main__":
    main()
