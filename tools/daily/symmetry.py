"""Colour symmetry of the WHOLE ENGINE, not just the evaluator.

For a position P, the colour-reflected position P' (vertical mirror plus a
colour swap, with castling rights and the en-passant square carried across)
is the same position with the roles exchanged. Everything the engine reports
from the side to move's point of view must therefore be identical for P and
P', and the best move must be the mirror of the best move.

Five things are checked at increasing depth of the machinery:

    static      the tapered evaluation
    qsearch     the leaf evaluation once captures are resolved
    root        a fixed-depth search score
    move        the best move, mirrored
    nodes       the node count of that search

A difference in the static score is an evaluator bug. A difference in the
root score or the node count with an identical static and qsearch score is a
search bug -- ordering, killers, history, the transposition table, null move,
late-move reductions or aspiration -- and the report names the first stage
that diverges so the attribution is not guessed.

    uv run python -m tools.daily.symmetry --engine champions/rated_v1 --depth 5 --out corpus/daily/symmetry_rated_v1.txt
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

import chess

from tools.postmortem.play import Engine

SOURCES = (
    "corpus/v2/endgame_calibration_v1.jsonl",
    "corpus/competition_like_v1.jsonl",
    "corpus/postmortem/games/fixed_depth.jsonl",
    "corpus/v2/fw/lowmat/01_report.jsonl",
    "corpus/selfplay_positions_v1.jsonl",
    "corpus/stress_test_v1.jsonl",
)


def mirror_move(move: chess.Move) -> chess.Move:
    return chess.Move(chess.square_mirror(move.from_square), chess.square_mirror(move.to_square), move.promotion)


def harvest(limit: int, seed: int) -> list[str]:
    """FENs from the retained corpora plus random-play positions, deduplicated."""
    rng = random.Random(seed)
    fens: list[str] = []
    seen: set[str] = set()

    def add(fen: str) -> None:
        board = chess.Board(fen)
        if board.is_game_over() or not any(board.legal_moves):
            return
        parts = fen.split()
        key = " ".join([board.board_fen(), parts[1], parts[2], parts[3]])
        if key in seen:
            return
        seen.add(key)
        fens.append(board.fen())

    for path in SOURCES:
        p = Path(path)
        if not p.exists():
            continue
        for line in p.open(encoding="utf-8"):
            row = json.loads(line)
            if isinstance(row.get("fen"), str):
                add(row["fen"])
            for m in row.get("moves", [])[:400]:
                if isinstance(m, dict) and isinstance(m.get("fen"), str):
                    add(m["fen"])
    rng.shuffle(fens)
    fens = fens[: max(0, limit - limit // 3)]
    # Random-play positions, to reach openings, castling rights, en passant and promotions.
    guard = 0
    while len(fens) < limit and guard < 20000:
        guard += 1
        board = chess.Board()
        for _ in range(rng.randint(1, 90)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
            if rng.random() < 0.10:
                add(board.fen())
    return fens[:limit]


def features(board: chess.Board) -> list[str]:
    out = []
    if board.castling_rights:
        out.append("castling")
    if board.ep_square is not None:
        out.append("ep")
    if board.is_check():
        out.append("check")
    if board.pawns & (chess.BB_RANK_2 | chess.BB_RANK_7):
        out.append("promotable")
    if not board.pawns:
        out.append("pawnless")
    if chess.popcount(board.occupied) <= 8:
        out.append("few-pieces")
    return out or ["plain"]


STAGES = ("static_ok", "qs_ok", "root_ok", "move_ok", "nodes_ok")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--positions", type=int, default=600)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    fens = harvest(arguments.positions, arguments.seed)
    print(f"{len(fens)} positions", flush=True)
    engine = Engine(arguments.engine, arguments.depth)
    rows = []
    try:
        for i, fen in enumerate(fens, start=1):
            board = chess.Board(fen)
            mirrored = board.mirror()
            r = {"fen": fen, "mirror": mirrored.fen(), "features": features(board)}
            for key, field in (("static", "static"), ("qs", "qs")):
                a = engine.ask(f"{key if key != 'static' else 'static'} {fen}")[field]
                b = engine.ask(f"{key} {mirrored.fen()}")[field]
                # Both are reported from white's point of view, so the mirrored
                # position's number must be the negation.
                r[key + "_a"], r[key + "_b"] = a, b
                r[key + "_ok"] = a == -b
            engine.ask("new")
            ga = engine.ask(f"go {fen}")
            engine.ask("new")
            gb = engine.ask(f"go {mirrored.fen()}")
            r["root_a"], r["root_b"] = ga["score"], gb["score"]  # side to move's view: must be equal
            r["root_ok"] = ga["score"] == gb["score"]
            r["move_a"], r["move_b"] = ga["move"], gb["move"]
            r["move_ok"] = (ga["move"] is not None and gb["move"] is not None
                            and mirror_move(chess.Move.from_uci(ga["move"])).uci() == gb["move"])
            r["nodes_a"], r["nodes_b"] = ga.get("nodes"), gb.get("nodes")
            r["nodes_ok"] = ga.get("nodes") == gb.get("nodes")
            rows.append(r)
            if i % 25 == 0:
                bad = sum(not all(x[s] for s in STAGES) for x in rows)
                print(f"  {i}/{len(fens)}  divergent so far {bad}", flush=True)
    finally:
        engine.close()

    lines = [f"== ENGINE COLOUR SYMMETRY: {arguments.engine}, depth {arguments.depth}, {len(rows)} mirrored position pairs ==",
             "P' is P mirrored vertically with the colours swapped. static and qsearch are white's view and must negate;",
             "the root score is the side to move's view and must be equal; the best move must be the mirrored move.", ""]
    for stage in STAGES:
        bad = [r for r in rows if not r[stage]]
        lines.append(f"   {stage.replace('_ok', ''):<8} agree {len(rows) - len(bad):>4}/{len(rows)}   divergent {len(bad)}")
    first_bad = Counter()
    for r in rows:
        for stage in STAGES:
            if not r[stage]:
                first_bad[stage.replace("_ok", "")] += 1
                break
    lines.append("")
    lines.append(f"first stage to diverge, per position: {dict(first_bad) or 'none: every stage agreed on every position'}")
    feature_bad = Counter()
    feature_all = Counter()
    for r in rows:
        ok = all(r[s] for s in STAGES)
        for f in r["features"]:
            feature_all[f] += 1
            if not ok:
                feature_bad[f] += 1
    lines.append("")
    lines.append("by position feature (divergent / seen):")
    for f in sorted(feature_all):
        lines.append(f"   {f:<12} {feature_bad[f]:>4}/{feature_all[f]}")
    lines.append("")
    lines.append("first 25 divergent positions:")
    for r in [x for x in rows if not all(x[s] for s in STAGES)][:25]:
        lines.append(f"   {[s.replace('_ok', '') for s in STAGES if not r[s]]}  static {r['static_a']:+6}/{r['static_b']:+6}  qs {r['qs_a']:+6}/{r['qs_b']:+6}  root {r['root_a']:+6}/{r['root_b']:+6}  move {r['move_a']}/{r['move_b']}  nodes {r['nodes_a']}/{r['nodes_b']}")
        lines.append(f"      P  {r['fen']}")
        lines.append(f"      P' {r['mirror']}")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
