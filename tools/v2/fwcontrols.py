"""Synthetic controls for exact-rule candidates: how often is a material family actually won?

For each family a fixed-seed sample of random legal positions is labelled
by the oracle, and V2.1's static and depth-6 root are recorded beside the
label. The share of wins in the family bounds the false-positive rate of
any rule that would score the family as drawn; the share of draws V2.1
calls +300 is the false-win rate the rule could remove.

    uv run python -m tools.v2.fwcontrols --out corpus/v2/fw/04_synthetic_controls.txt
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle
from tools.postmortem.play import Engine

FAMILIES = {
    "KRB-KR": ([(chess.ROOK, chess.WHITE), (chess.BISHOP, chess.WHITE), (chess.ROOK, chess.BLACK)], []),
    "KRN-KR": ([(chess.ROOK, chess.WHITE), (chess.KNIGHT, chess.WHITE), (chess.ROOK, chess.BLACK)], []),
    "KB-KR": ([(chess.BISHOP, chess.WHITE), (chess.ROOK, chess.BLACK)], []),
    "KBP(rook pawn)-K": ([(chess.BISHOP, chess.WHITE)], [("rook", chess.WHITE)]),
    "KBP(other pawn)-K": ([(chess.BISHOP, chess.WHITE)], [("centre", chess.WHITE)]),
    "KNP-K": ([(chess.KNIGHT, chess.WHITE)], [("any", chess.WHITE)]),
    "KP-K": ([], [("any", chess.WHITE)]),
    "KRP-KR": ([(chess.ROOK, chess.WHITE), (chess.ROOK, chess.BLACK)], [("any", chess.WHITE)]),
    "KRPP-KRP": ([(chess.ROOK, chess.WHITE), (chess.ROOK, chess.BLACK)], [("any", chess.WHITE), ("any", chess.WHITE), ("any", chess.BLACK)]),
    "OCB, one pawn up": ([("ocb", None)], [("any", chess.WHITE), ("any", chess.WHITE), ("any", chess.BLACK)]),
    "OCB, two pawns up": ([("ocb", None)], [("any", chess.WHITE), ("any", chess.WHITE), ("any", chess.WHITE), ("any", chess.BLACK)]),
    "KQ-KP(7th)": ([(chess.QUEEN, chess.WHITE)], [("seventh", chess.BLACK)]),
}


def sample(name: str, pieces, pawns, rng: random.Random) -> chess.Board | None:
    board = chess.Board(None)
    used: set[int] = set()

    def put(piece: chess.Piece, squares: list[int]) -> bool:
        rng.shuffle(squares)
        for sq in squares:
            if sq not in used:
                board.set_piece_at(sq, piece)
                used.add(sq)
                return True
        return False

    put(chess.Piece(chess.KING, chess.WHITE), list(range(64)))
    put(chess.Piece(chess.KING, chess.BLACK), list(range(64)))
    for kind, colour in pieces:
        if kind == "ocb":
            light = [s for s in range(64) if chess.BB_SQUARES[s] & chess.BB_LIGHT_SQUARES]
            dark = [s for s in range(64) if chess.BB_SQUARES[s] & chess.BB_DARK_SQUARES]
            a, b = (light, dark) if rng.random() < 0.5 else (dark, light)
            put(chess.Piece(chess.BISHOP, chess.WHITE), a)
            put(chess.Piece(chess.BISHOP, chess.BLACK), b)
        else:
            put(chess.Piece(kind, colour), list(range(64)))
    for kind, colour in pawns:
        if kind == "rook":
            squares = [chess.square(f, r) for f in (0, 7) for r in range(1, 7)]
        elif kind == "centre":
            squares = [chess.square(f, r) for f in range(1, 7) for r in range(1, 7)]
        elif kind == "seventh":
            squares = [chess.square(f, 1) for f in range(8)]  # black pawn on its seventh
        else:
            squares = [chess.square(f, r) for f in range(8) for r in range(1, 7)]
        put(chess.Piece(chess.PAWN, colour), squares)
    board.turn = rng.choice((chess.WHITE, chess.BLACK))
    if not board.is_valid() or board.is_game_over():
        return None
    return board


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--each", type=int, default=40)
    parser.add_argument("--nodes", type=int, default=300_000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    rng = random.Random(20260904)
    engine = Engine(Path("champions/v2_1_kingpawn"), 6)
    rows = []
    lines = [f"== SYNTHETIC CONTROLS: {arguments.each} random legal positions per family, oracle {arguments.nodes} nodes, V2.1 static and depth-6 root ==",
             "scores from White's side (the side with the extra material). win = SF >= +300, draw = |SF| <= 60.", "",
             f"{'family':<20} {'n':>3} {'wins':>5} {'draws':>6} {'V2.1 static on draws':>21} {'V2.1 root on draws':>19} {'draws V2.1 calls >= +200':>25} {'wins V2.1 calls < +150':>23}"]
    try:
        with Oracle() as oracle:
            for name, (pieces, pawns) in FAMILIES.items():
                made = []
                tries = 0
                while len(made) < arguments.each and tries < 5000:
                    tries += 1
                    b = sample(name, pieces, pawns, rng)
                    if b is not None:
                        made.append(b)
                fam_rows = []
                for b in made:
                    fen = b.fen()
                    label = oracle.analyse(fen, arguments.nodes)
                    sf_white = label.cp_white
                    engine.ask("new")
                    g = engine.ask(f"go {fen}")
                    root_white = g["score"] if b.turn else -g["score"]
                    fam_rows.append({"family": name, "fen": fen, "sf_white": sf_white, "sf_mate": label.mate, "v21_static_white": g["static"], "v21_root_white": root_white})
                rows.extend(fam_rows)
                wins = [r for r in fam_rows if r["sf_white"] >= 300]
                draws = [r for r in fam_rows if abs(r["sf_white"]) <= 60]
                lines.append(f"{name:<20} {len(fam_rows):>3} {len(wins):>5} {len(draws):>6} "
                             f"{(sum(r['v21_static_white'] for r in draws) / len(draws)) if draws else 0:>+21.0f} {(sum(r['v21_root_white'] for r in draws) / len(draws)) if draws else 0:>+19.0f} "
                             f"{sum(r['v21_root_white'] >= 200 for r in draws):>10}/{len(draws):<14} {sum(r['v21_root_white'] < 150 for r in wins):>10}/{len(wins):<12}")
                print(lines[-1], flush=True)
    finally:
        engine.close()
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
