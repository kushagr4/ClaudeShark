"""Bound a term on adversarial positions: what two engines say, statically and at depth, against the oracle.

    uv run python -m tools.v2.adversarial --cases corpus/v2/adversarial_kingpawn.json --base champions/rated_v1 --cand <dir> --out <txt>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle
from tools.postmortem.play import Engine
from tools.v2.suite import loss_after


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--cand", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    cases = json.loads(arguments.cases.read_text(encoding="utf-8"))
    base = Engine(arguments.base, arguments.depth)
    cand = Engine(arguments.cand, arguments.depth)
    lines = [f"== ADVERSARIAL CASES: {arguments.base} (base) vs {arguments.cand} (cand), depth {arguments.depth}, oracle {arguments.nodes} nodes ==",
             "all scores from the side to move; loss = Stockfish cp given up by the engine's move", ""]
    rows = []
    try:
        with Oracle() as oracle:
            for c in cases:
                fen = c["fen"]
                white = chess.Board(fen).turn == chess.WHITE
                label = oracle.analyse(fen, arguments.nodes)
                out = {"name": c["name"], "fen": fen, "motif": c["motif"], "sf": label.cp_stm, "sf_mate": label.mate, "sf_best": label.best}
                for name, e in (("base", base), ("cand", cand)):
                    e.ask("new")
                    r = e.ask(f"go {fen}")
                    out[name] = {"static": r["static"] if white else -r["static"], "root": r["score"], "move": r["move"],
                                 "loss": loss_after(oracle, fen, r["move"], arguments.nodes, label.cp_stm)}
                rows.append(out)
                lines.append(f"-- {c['name']}: {c['motif']}")
                lines.append(f"   {fen}")
                lines.append(f"   Stockfish {label.cp_stm:+} (mate {label.mate}) best {label.best}")
                for name in ("base", "cand"):
                    x = out[name]
                    lines.append(f"   {name}: static {x['static']:+5}  root {x['root']:+5}  move {x['move']:<6} loss {x['loss']}")
    finally:
        base.close()
        cand.close()
    text = "\n".join(lines)
    print(text)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(rows, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
