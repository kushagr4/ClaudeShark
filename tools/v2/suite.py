"""Run an engine on the V2 endgame calibration set and score it in both directions.

Static-only mode scores every position's static evaluation against
Stockfish (fast, for screening a term); full mode also asks for the root
quiescence score and the fixed-depth root and the oracle loss of the chosen
move. The headline numbers are per class, because the set exists to punish
two opposite mistakes: a blind win is scored by how far the engine is *below*
Stockfish, a false win by how far it is *above*, and the recognised classes
and controls must not move.

    uv run python -m tools.v2.suite --suite corpus/v2/endgame_calibration_v1.jsonl --engine <dir> --static-only --out <txt>
    uv run python -m tools.v2.suite --suite ... --engine <dir> --depth 6 --out <txt>
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle
from tools.postmortem.play import Engine

CLASSES = ("blind_win", "false_win", "recognised_win", "recognised_draw", "losing", "control_middle", "control_tactic")


def clamp(v: int) -> int:
    return min(max(v, -2000), 2000)


def loss_after(oracle: Oracle, fen: str, move: str, nodes: int, sf_cp: int) -> int:
    """Oracle loss of a move, with terminal children scored by the rules rather than the engine."""
    board = chess.Board(fen)
    board.push_uci(move)
    if board.is_checkmate():
        child = -10000  # the side to move after the move is mated
    elif board.is_game_over():
        child = 0
    else:
        child = oracle.score_after(fen, move, nodes).cp_stm
    return max(0, sf_cp + child)


def run(suite: Path, engine_dir: Path, depth: int, static_only: bool, role: str) -> tuple[dict, list[dict]]:
    rows = [json.loads(line) for line in suite.open(encoding="utf-8")]
    header, rows = rows[0], rows[1:]
    if role != "all":
        rows = [r for r in rows if r["role"] == role]
    engine = Engine(engine_dir, depth)
    out = []
    try:
        oracle = None if static_only else Oracle()
        try:
            for r in rows:
                white = r["fen"].split()[1] == "w"
                engine.ask("new")
                s = engine.ask(f"static {r['fen']}")["static"]
                rec = {**r, "static": s if white else -s}
                if not static_only:
                    q = engine.ask(f"qs {r['fen']}")
                    engine.ask("new")
                    g = engine.ask(f"go {r['fen']}")
                    rec.update({"qs": q["qs"] if white else -q["qs"], "root": g["score"], "move": g["move"],
                                "loss": loss_after(oracle, r["fen"], g["move"], r.get("nodes", 1_000_000), r["sf_cp"]),
                                "nodes_used": g["nodes"]})
                out.append(rec)
        finally:
            if oracle is not None:
                oracle.close()
    finally:
        engine.close()
    return header, out


def report(header: dict, rows: list[dict], engine: str, static_only: bool) -> str:
    lines = [f"== V2 ENDGAME CALIBRATION SUITE {header['version']} ({len(rows)} positions, hash {header['hash']}) engine {engine} ==",
             "SF = Stockfish from the side to move (clamped +-2000); 'below' = mean(SF - x) where the win is real; 'above' = mean(x - SF) where the position is level",
             "MAE = mean |x - SF|; a term is good when blind_win 'below' falls, false_win 'above' falls, and the recognised classes and controls do not move", ""]
    cols = ["static"] + ([] if static_only else ["qs", "root"])
    lines.append(f"  {'class':<16} {'n':>4} {'traj':>4} {'SF':>6} " + " ".join(f"{c:>7} {c + ' MAE':>10}" for c in cols) + ("" if static_only else f" {'loss':>6} {'serious':>8} {'agree':>6}"))
    for cls in CLASSES:
        rs = [r for r in rows if r["class"] == cls]
        if not rs:
            continue
        sf = [clamp(r["sf_cp"]) for r in rs]
        cells = []
        for c in cols:
            xs = [r[c] for r in rs]
            cells.append(f"{statistics.mean(xs):>+7.0f} {statistics.mean(abs(x - s) for x, s in zip(xs, sf, strict=True)):>10.0f}")
        extra = ""
        if not static_only:
            extra = f" {statistics.mean(min(r['loss'], 500) for r in rs):>6.0f} {sum(r['loss'] >= 100 for r in rs) / len(rs):>8.0%} {sum(r['move'] == r['sf_best'] for r in rs) / len(rs):>6.0%}"
        lines.append(f"  {cls:<16} {len(rs):>4} {len({r['trajectory'] for r in rs}):>4} {statistics.mean(sf):>+6.0f} " + " ".join(cells) + extra)
    lines.append("")
    for c in cols:
        blind = [r for r in rows if r["class"] == "blind_win"]
        false = [r for r in rows if r["class"] == "false_win"]
        if blind and false:
            below = statistics.mean(clamp(r["sf_cp"]) - r[c] for r in blind)
            above = statistics.mean(r[c] - clamp(r["sf_cp"]) for r in false)
            lines.append(f"  {c}: blind wins sit {below:+.0f} below Stockfish; false wins sit {above:+.0f} above; "
                         f"blind rows with {c} < +100: {sum(r[c] < 100 for r in blind)}/{len(blind)}; false rows with {c} >= +200: {sum(r[c] >= 200 for r in false)}/{len(false)}")
    by_role: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_role[r["role"]].append(r)
    lines.append("")
    for role, rs in sorted(by_role.items()):
        blind = [r for r in rs if r["class"] == "blind_win"]
        false = [r for r in rs if r["class"] == "false_win"]
        if blind and false:
            lines.append(f"  {role}: static blind-below {statistics.mean(clamp(r['sf_cp']) - r['static'] for r in blind):+.0f} ({len(blind)}), false-above {statistics.mean(r['static'] - clamp(r['sf_cp']) for r in false):+.0f} ({len(false)})")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--role", choices=("all", "diagnostic", "validation"), default="all")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    header, rows = run(arguments.suite, arguments.engine, arguments.depth, arguments.static_only, arguments.role)
    text = report(header, rows, str(arguments.engine), arguments.static_only)
    print(text)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
