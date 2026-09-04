"""Does a deeper search repair the decision? Asked of specific positions.

The rated-game questions "would deeper rated-v1 search repair the critical
decision", "does V2.1 repair it" and "does the current V2 champion repair it"
are answered here rather than guessed. Each named snapshot is run at several
fixed depths on each position, and the move it chooses is scored by the oracle,
so a repair means the oracle likes the new move better -- not merely that the
move changed or that the engine's own score went up.

Positions come from a JSON list of ``{"label", "fen", "played", "sf_best"}``
so the same tool serves the rated games, the failure gallery and any future
set.

    uv run python -m tools.daily.deeper --positions corpus/daily/rated_errors.json --out corpus/daily/deeper.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import chess

from tools.corpus.oracle import MATE_CP, label_many
from tools.postmortem.play import Engine

SNAPSHOTS = {
    "rated-v1": "champions/rated_v1",
    "V2.1 king-pawn": "champions/v2_1_kingpawn",
    "V2.2a low-material": "champions/v2_2a_low_material",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--positions", type=Path, required=True)
    parser.add_argument("--depths", type=int, nargs="+", default=[6, 7, 8])
    parser.add_argument("--nodes", type=int, default=2_000_000)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    positions = json.loads(arguments.positions.read_text(encoding="utf-8"))

    for name, path in SNAPSHOTS.items():
        for depth in arguments.depths:
            engine = Engine(Path(path), depth)
            try:
                for r in positions:
                    engine.ask("new")
                    reply = engine.ask(f"go {r['fen']}")
                    r[f"{name} d{depth}"] = {"move": reply["move"], "score": reply["score"], "nodes": reply.get("nodes")}
            finally:
                engine.close()
            print(f"  {name} depth {depth} done", flush=True)

    keys: dict[tuple[str, str], None] = {}
    for r in positions:
        for name in SNAPSHOTS:
            for depth in arguments.depths:
                move = r[f"{name} d{depth}"]["move"]
                if move:
                    keys[(r["fen"], move)] = None
        for field in ("played", "sf_best"):
            if r.get(field):
                keys[(r["fen"], r[field])] = None
    pairs = list(keys)
    after = []
    for fen, move in pairs:
        board = chess.Board(fen)
        board.push_uci(move)
        after.append(board.fen())
    print(f"scoring {len(after)} resulting positions at {arguments.nodes} nodes", flush=True)
    labels = label_many(after, arguments.nodes, workers=arguments.workers, progress=True)
    value: dict[tuple[str, str], int] = {}
    for (fen, move), label in zip(pairs, labels, strict=True):
        white = chess.Board(fen).turn == chess.WHITE
        value[(fen, move)] = max(-MATE_CP, min(MATE_CP, label.cp_white if white else -label.cp_white))

    lines = [f"== DOES DEEPER SEARCH REPAIR IT? {len(positions)} positions, oracle at {arguments.nodes} nodes ==",
             "'value' is the oracle score after the chosen move, from the mover's point of view. Higher is better;",
             "the 'oracle move' column is the ceiling and the 'played' column is what actually happened.", ""]
    header = f"   {'position':<34} {'played':>8} {'oracle':>8}"
    for name in SNAPSHOTS:
        for depth in arguments.depths:
            header += f" | {name[:9]} d{depth}"
    lines.append(header)
    for r in positions:
        line = f"   {r['label'][:34]:<34} {value[(r['fen'], r['played'])]:>+8} {value[(r['fen'], r['sf_best'])]:>+8}"
        for name in SNAPSHOTS:
            for depth in arguments.depths:
                move = r[f"{name} d{depth}"]["move"]
                line += f" | {move or '-':<5}{value.get((r['fen'], move), 0):>+6}"
        lines.append(line)
    lines.append("")
    lines.append("means over the sample:")
    lines.append(f"   {'played':<28} {statistics.mean(value[(r['fen'], r['played'])] for r in positions):>+8.0f}")
    lines.append(f"   {'oracle first choice':<28} {statistics.mean(value[(r['fen'], r['sf_best'])] for r in positions):>+8.0f}")
    for name in SNAPSHOTS:
        for depth in arguments.depths:
            vals = [value[(r["fen"], r[f"{name} d{depth}"]["move"])] for r in positions if r[f"{name} d{depth}"]["move"]]
            repaired = sum(1 for r in positions
                           if r[f"{name} d{depth}"]["move"]
                           and value[(r["fen"], r[f"{name} d{depth}"]["move"])] - value[(r["fen"], r["played"])] >= 100)
            lines.append(f"   {name + ' depth ' + str(depth):<28} {statistics.mean(vals):>+8.0f}   repairs (>= +100 over the played move) {repaired} of {len(positions)}")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in positions) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
