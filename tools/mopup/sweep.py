"""Choose the two mop-up weights on real stuck positions, check them on synthetic ones.

For each (EDGE, PROXIMITY) pair a scratch copy of the engine is built with the
flag on and those constants, and production-vs-candidate is not the question
here: the candidate plays *both* sides from each starting position at a fixed
depth, and the measurement is whether the attacking side reaches mate, and in
how many plies. The six real positions from the audit are the diagnostic set
the weights are chosen on; the synthetic positions are drawn with a fixed seed
and never looked at during selection.

The smallest pair that mates every diagnostic position within the ply cap is
preferred, on the principle that the term should be as small as it can be while
still supplying a gradient.

    uv run python -m tools.mopup.sweep --out corpus/mopup/02_sweep.txt
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

import chess

ROOT = Path(__file__).resolve().parents[2]
ENGINE_FILES = ("agent.py", "cs_constants.py", "cs_drawish.py", "cs_eval.py", "cs_king.py", "cs_kingpawn.py", "cs_mopup.py",
                "cs_ordering.py", "cs_search.py", "cs_see.py", "cs_terms.py", "cs_time.py", "cs_tt.py")


def build_variant(edge: int, proximity: int, where: Path, flag_on: bool = True) -> Path:
    where.mkdir(parents=True, exist_ok=True)
    for name in ENGINE_FILES:
        shutil.copy2(ROOT / name, where / name)
    m = where / "cs_mopup.py"
    src = m.read_text(encoding="utf-8")
    src = src.replace("EDGE = 20\n", f"EDGE = {edge}\n", 1).replace("PROXIMITY = 10\n", f"PROXIMITY = {proximity}\n", 1)
    m.write_text(src, encoding="utf-8")
    if flag_on:
        e = where / "cs_terms.py"
        src = e.read_text(encoding="utf-8")
        old = '"mopup": False,'
        assert old in src
        e.write_text(src.replace(old, '"mopup": True,', 1), encoding="utf-8")
    return where


def synthetic_positions(n_each: int, seed: int) -> list[dict]:
    """Random legal in-domain positions: KQK, KRK, KRNK, KRBK, defender to move or not."""
    rng = random.Random(seed)
    out = []
    kinds = {"KQK": [chess.QUEEN], "KRK": [chess.ROOK], "KRNK": [chess.ROOK, chess.KNIGHT],
             "KRBK": [chess.ROOK, chess.BISHOP]}
    for kind, pieces in kinds.items():
        made = 0
        while made < n_each:
            board = chess.Board(None)
            squares = rng.sample(range(64), 2 + len(pieces))
            board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
            board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
            for sq, pt in zip(squares[2:], pieces, strict=True):
                board.set_piece_at(sq, chess.Piece(pt, chess.WHITE))
            board.turn = rng.choice((chess.WHITE, chess.BLACK))
            if not board.is_valid() or board.is_game_over():
                continue
            out.append({"cluster": 1000 + len(out), "fen": board.fen(), "kind": kind})
            made += 1
    return out


def play_set(engine: Path, pairs: Path, depth: int, ply_cap: int, out: Path, workers: int) -> list[dict]:
    subprocess.run([sys.executable, "-m", "tools.postmortem.play", "--cand", str(engine), "--base", str(engine),
                    "--pairs", str(pairs), "--depth", str(depth), "--workers", str(workers),
                    "--ply-cap", str(ply_cap), "--out", str(out)], check=True, cwd=ROOT,
                   stdout=subprocess.DEVNULL)
    return [json.loads(line) for line in out.open(encoding="utf-8")]


def summarise(games: list[dict]) -> dict:
    mates = [g for g in games if g["termination"] == "checkmate"]
    return {"games": len(games), "mated": len(mates),
            "mean_plies_to_mate": (sum(g["plies"] for g in mates) / len(mates)) if mates else None,
            "repetition": sum(1 for g in games if g["termination"] == "threefold_repetition"),
            "other": sum(1 for g in games if g["termination"] not in ("checkmate", "threefold_repetition"))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, default=Path("corpus/mopup/bare_king_pairs.json"))
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--ply-cap", type=int, default=120)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--synthetic-each", type=int, default=6)
    parser.add_argument("--grid", default="0:0,10:5,20:10,30:15,40:20")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    synth = synthetic_positions(arguments.synthetic_each, seed=20260903)
    synth_path = arguments.out.parent / "synthetic_pairs.json"
    synth_path.write_text(json.dumps(synth, indent=1), encoding="utf-8")
    lines = [f"== MOP-UP WEIGHT SWEEP (depth {arguments.depth}, ply cap {arguments.ply_cap}) ==",
             "diagnostic = the six real stuck positions (both colours); validation = synthetic in-domain positions",
             "", f"{'EDGE':>5} {'PROX':>5} | {'diag mated':>10} {'plies':>6} {'rep':>4} | {'valid mated':>11} {'plies':>6} {'rep':>4}"]
    results = []
    for pair in arguments.grid.split(","):
        edge, prox = (int(x) for x in pair.split(":"))
        engine = build_variant(edge, prox, arguments.scratch / f"mopup_e{edge}_p{prox}", flag_on=(edge or prox) > 0)
        d = summarise(play_set(engine, arguments.diagnostic, arguments.depth, arguments.ply_cap,
                               arguments.out.parent / f"games_diag_e{edge}_p{prox}.jsonl", arguments.workers))
        v = summarise(play_set(engine, synth_path, arguments.depth, arguments.ply_cap,
                               arguments.out.parent / f"games_valid_e{edge}_p{prox}.jsonl", arguments.workers))
        results.append({"edge": edge, "proximity": prox, "diagnostic": d, "validation": v})
        lines.append(f"{edge:>5} {prox:>5} | {d['mated']:>4}/{d['games']:<5} {(d['mean_plies_to_mate'] or 0):>6.1f} {d['repetition']:>4} | "
                     f"{v['mated']:>4}/{v['games']:<6} {(v['mean_plies_to_mate'] or 0):>6.1f} {v['repetition']:>4}")
        print(lines[-1], flush=True)
    arguments.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
