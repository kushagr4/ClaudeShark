"""Controlled search ablations on the positions the engine actually got wrong.

The root-cause map's largest single blind-win mechanism is "tactical/horizon",
and the feature attribution found that the biggest residuals against the oracle
belong to positions whose *root* score departs while their *static* score does
not -- the signature of a search problem rather than a missing evaluation term.
Before adding an extension, this establishes which component is responsible, or
whether any is.

A stratified sample of positions where the mover lost at least ``--threshold``
centipawns is replayed under several configurations of the same frozen engine:
the baseline, deeper searches, and each selective mechanism disabled one at a
time through its declared environment flag. Every chosen move is then scored by
the oracle, so configurations are compared on the quality of the move they
produce, not on whether they happen to agree with Stockfish's first choice.

    uv run python -m tools.daily.searchaudit --engine champions/v2_1_kingpawn --out corpus/daily/search_audit.txt
"""

from __future__ import annotations

import argparse
import contextlib
import json
import random
import statistics
import subprocess
import sys
from pathlib import Path

import chess

from tools.corpus.oracle import MATE_CP, Oracle, label_many

WORKER = Path(__file__).resolve().parent.parent / "postmortem" / "worker.py"

CORPORA = (
    "corpus/postmortem/games/annotated.jsonl",
    "corpus/v2/kp/games/gate2_annotated.jsonl",
    "corpus/passed/games/gate2_annotated.jsonl",
    "corpus/mopup/games/gate2_annotated.jsonl",
)

# name -> (extra depth, environment overrides)
CONFIGS: dict[str, tuple[int, dict[str, str]]] = {
    "baseline d6": (0, {}),
    "depth 7": (1, {}),
    "depth 8": (2, {}),
    "no null move": (0, {"CS_NMP": "0"}),
    "no late-move reductions": (0, {"CS_LMR": "0"}),
    "no aspiration window": (0, {"CS_ASPIRATION": "0"}),
    "no quiescence SEE pruning": (0, {"CS_SEE_QS": "0"}),
    "no PVS": (0, {"CS_PVS": "0"}),
    "no TT cutoff on PV nodes": (0, {"CS_TT_PV_CUTOFF": "0"}),
}


class Worker:
    """One engine process at a fixed depth, with environment overrides applied."""

    def __init__(self, directory: Path, depth: int, env: dict[str, str]) -> None:
        import os

        environment = dict(os.environ)
        environment.update(env)
        self.proc = subprocess.Popen(
            [sys.executable, str(WORKER), str(directory), str(depth)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
            env=environment,
        )

    def ask(self, line: str) -> dict:
        assert self.proc.stdin and self.proc.stdout
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.ask("quit")
        self.proc.kill()


def sample(threshold: int, limit: int, seed: int, clamp: int) -> list[dict]:
    rows = []
    for path in CORPORA:
        p = Path(path)
        if not p.exists():
            continue
        for line in p.open(encoding="utf-8"):
            g = json.loads(line)
            for m in g["moves"]:
                sf_white = m.get("sf_cp_white_before")
                if sf_white is None or m.get("cp_loss") is None:
                    continue
                board = chess.Board(m["fen"])
                white = board.turn == chess.WHITE
                sf = sf_white if white else -sf_white
                if abs(sf) > clamp or m["cp_loss"] < threshold:
                    continue
                rows.append({"fen": m["fen"], "played": m["move"], "sf_before": sf,
                             "sf_best": m["sf_best"], "cp_loss": m["cp_loss"], "source": path})
    rng = random.Random(seed)
    rng.shuffle(rows)
    seen: set[str] = set()
    out = []
    for r in rows:
        if r["fen"] in seen:
            continue
        seen.add(r["fen"])
        out.append(r)
        if len(out) >= limit:
            break
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--threshold", type=int, default=200)
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--clamp", type=int, default=800)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    positions = sample(arguments.threshold, arguments.limit, arguments.seed, arguments.clamp)
    print(f"{len(positions)} error positions (mover lost >= {arguments.threshold} cp, |oracle| <= {arguments.clamp})", flush=True)

    for name, (extra, env) in CONFIGS.items():
        worker = Worker(arguments.engine, arguments.depth + extra, env)
        try:
            for i, r in enumerate(positions, start=1):
                worker.ask("new")
                reply = worker.ask(f"go {r['fen']}")
                r[name] = {"move": reply["move"], "score": reply["score"], "nodes": reply.get("nodes")}
                if i % 40 == 0:
                    print(f"   {name}: {i}/{len(positions)}", flush=True)
        finally:
            worker.close()
        print(f"  {name} done", flush=True)

    # Score every distinct (position, chosen move) with the oracle once.
    wanted: dict[tuple[str, str], None] = {}
    for r in positions:
        for name in CONFIGS:
            move = r[name]["move"]
            if move:
                wanted[(r["fen"], move)] = None
        wanted[(r["fen"], r["played"])] = None
        if r["sf_best"]:
            wanted[(r["fen"], r["sf_best"])] = None
    keys = list(wanted)
    after_fens = []
    for fen, move in keys:
        board = chess.Board(fen)
        board.push_uci(move)
        after_fens.append(board.fen())
    print(f"scoring {len(after_fens)} resulting positions at {arguments.nodes} nodes", flush=True)
    labels = label_many(after_fens, arguments.nodes, workers=arguments.workers, progress=True)
    value: dict[tuple[str, str], int] = {}
    for (fen, move), label in zip(keys, labels, strict=True):
        board = chess.Board(fen)
        mover_is_white = board.turn == chess.WHITE
        cp = label.cp_white if mover_is_white else -label.cp_white
        value[(fen, move)] = max(-MATE_CP, min(MATE_CP, cp))
    with Oracle() as oracle:
        provenance = oracle.provenance()

    lines = [f"== SEARCH ABLATION ON {len(positions)} ERROR POSITIONS: {arguments.engine} ==",
             f"Positions where the mover lost at least {arguments.threshold} cp with the oracle within {arguments.clamp} of level,",
             f"sampled from four annotated corpora. Every configuration's chosen move is scored by the oracle at {arguments.nodes} nodes;",
             "'value' is the oracle score of the position after that move, from the mover's point of view. Higher is better.", ""]
    played = statistics.mean(value[(r["fen"], r["played"])] for r in positions)
    best = statistics.mean(value[(r["fen"], r["sf_best"])] for r in positions if r["sf_best"])
    lines.append(f"   {'configuration':<28} {'mean value':>11} {'vs baseline':>12} {'= oracle move':>14} {'changed move':>13} {'mean nodes':>11}")
    baseline_value = None
    for name in CONFIGS:
        vals = [value[(r["fen"], r[name]["move"])] for r in positions if r[name]["move"]]
        mean = statistics.mean(vals)
        if baseline_value is None:
            baseline_value = mean
        agree = sum(1 for r in positions if r[name]["move"] == r["sf_best"])
        changed = sum(1 for r in positions if r[name]["move"] != r["baseline d6"]["move"])
        nodes = statistics.mean(r[name]["nodes"] or 0 for r in positions)
        lines.append(f"   {name:<28} {mean:>+11.0f} {mean - baseline_value:>+12.0f} {agree:>10}/{len(positions):<3} {changed:>13} {nodes:>11,.0f}")
    lines.append(f"   {'the move actually played':<28} {played:>+11.0f} {played - baseline_value:>+12.0f}")
    lines.append(f"   {'the oracle first choice':<28} {best:>+11.0f} {best - baseline_value:>+12.0f}   (the ceiling for this sample)")
    lines.append("")
    lines.append("A configuration only matters if its mean value moves toward the ceiling. Changing many moves while")
    lines.append("gaining nothing means the mechanism was not the cause of the error.")
    lines.append("")

    # Where does extra depth help, and where does it not?
    lines.append("== WHERE DEPTH HELPS: positions bucketed by how much depth 8 improves on depth 6 ==")
    gains = [(value[(r["fen"], r["depth 8"]["move"])] - value[(r["fen"], r["baseline d6"]["move"])], r) for r in positions]
    gains.sort(key=lambda pair: -pair[0])
    helped = [g for g, _ in gains if g >= 100]
    hurt = [g for g, _ in gains if g <= -100]
    lines.append(f"   depth 8 gains at least 100 cp on {len(helped)} of {len(positions)} positions, loses at least 100 on {len(hurt)}")
    lines.append(f"   mean gain {statistics.mean(g for g, _ in gains):+.0f} cp for {statistics.mean(r['depth 8']['nodes'] or 0 for r in positions) / max(1, statistics.mean(r['baseline d6']['nodes'] or 1 for r in positions)):.1f}x the nodes")
    lines.append("")
    lines.append("   the ten positions depth 8 repairs most:")
    for gain, r in gains[:10]:
        lines.append(f"      +{gain:>5} oracle {r['sf_before']:>+5}  d6 {r['baseline d6']['move']} -> d8 {r['depth 8']['move']} (oracle move {r['sf_best']})  {r['fen']}")
    lines.append("")
    lines.append("   the ten positions depth 8 damages most:")
    for gain, r in gains[-10:]:
        lines.append(f"      {gain:>+6} oracle {r['sf_before']:>+5}  d6 {r['baseline d6']['move']} -> d8 {r['depth 8']['move']} (oracle move {r['sf_best']})  {r['fen']}")
    lines.append("")
    lines.append(f"oracle provenance: {provenance['engine']}, {provenance['limit']}, options {provenance['options']}")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text(
        "\n".join(json.dumps({**r, "values": {name: value[(r["fen"], r[name]["move"])] for name in CONFIGS if r[name]["move"]}}) for r in positions) + "\n",
        encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
