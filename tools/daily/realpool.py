"""Build a start-position pool from the starting FENs the competition actually used.

The synthesised competition-profile pool in ``tools/daily/pool.py`` was built to
match the profile of the five start positions known at the time. A scrape of
publicly visible top-50 team pages supplies the real thing: the exact starting
positions of 143 rated games. Those are a better distribution B for the
two-distribution promotion rule than anything generated, because they are not a
model of the organisers' pool -- they are a sample of it.

Only the starting positions are taken. Nobody's moves are used, and ClaudeShark's
own rated games stay out of the pool entirely so that they remain holdout
evidence: a start FEN is dropped if it matches one of ours.

Each retained FEN is scored by the oracle so the pool's evaluation distribution
can be compared with the synthesised one and with the five known competition
positions.

    uv run python -m tools.daily.realpool --games analysis/top50_games.jsonl --out corpus/daily/pool/competition_actual_pairs.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle

# ClaudeShark's own rated starts, excluded so those games stay holdout evidence.
OURS = {
    "rnbqk2r/p3nppp/1p2p3/2ppP3/P2P4/2P2N2/2P2PPP/R1BQKB1R b KQkq - 0 8",
    "rn1qkbnr/pp2pppp/2p3b1/8/3P4/4B1N1/PPP2PPP/R2QKBNR b KQkq - 4 6",
    "rnbqk2r/ppp2ppp/3b4/3p4/2PPn3/5N2/PP2BPPP/RNBQK2R b KQkq - 0 7",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0, help="0 keeps every distinct position")
    parser.add_argument("--nodes", type=int, default=2_000_000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    raw = {r["game_id"]: r for r in (json.loads(line) for line in arguments.games.open(encoding="utf-8"))}
    uses = Counter()
    for r in raw.values():
        fen = r.get("starting_fen")
        if fen:
            uses[fen] += 1
    excluded = sum(uses[f] for f in OURS if f in uses)
    positions = [f for f in uses if f not in OURS]
    positions.sort(key=lambda f: (-uses[f], f))
    if arguments.limit:
        positions = positions[: arguments.limit]
    print(f"{len(raw)} games, {len(uses)} distinct starting FENs, "
          f"{len(positions)} kept ({excluded} game(s) on ClaudeShark's own starts excluded)", flush=True)

    oracle = Oracle()
    rows = []
    try:
        for i, fen in enumerate(positions):
            label = oracle.analyse(fen, arguments.nodes)
            board = chess.Board(fen)
            rows.append({
                "id": f"ca-{i:03d}", "cluster": 9000 + i, "fen": fen,
                "uses_in_scrape": uses[fen], "fullmove": board.fullmove_number,
                "side_to_move": "w" if board.turn == chess.WHITE else "b",
                "sf_cp_white": label.cp_white, "sf_best": label.best,
                "sf_wdl_white": list(label.wdl_white) if label.wdl_white else None,
                "sf_nodes": arguments.nodes, "phase": "opening",
            })
            if (i + 1) % 20 == 0:
                print(f"   scored {i + 1}/{len(positions)}", flush=True)
        provenance = oracle.provenance()
    finally:
        oracle.close()
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    arguments.out.with_name(arguments.out.stem + "_provenance.json").write_text(
        json.dumps({"provenance": provenance, "source": str(arguments.games),
                    "distinct_positions": len(uses), "kept": len(rows),
                    "excluded_our_own_starts": sorted(OURS)}, indent=1) + "\n", encoding="utf-8")
    cps = [r["sf_cp_white"] for r in rows]
    stm = Counter(r["side_to_move"] for r in rows)
    moves = Counter(r["fullmove"] for r in rows)
    print(f"{len(rows)} positions written to {arguments.out}")
    print(f"   side to move: {dict(stm)}")
    print(f"   full-move number: {dict(sorted(moves.items()))}")
    print(f"   oracle cp(white): mean {sum(cps) / len(cps):+.1f}  min {min(cps)}  max {max(cps)}  "
          f"|cp| <= 40 on {sum(1 for c in cps if abs(c) <= 40)} of {len(cps)}")


if __name__ == "__main__":
    main()
