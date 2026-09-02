"""Red-team the PV transposition-cutoff policy across a calibrated suite.

Compares the three policies at fixed depth over every position in a suite and
reports each move difference with the oracle's verdict on both moves, so a
divergence can be called a fix, a regression or a wash rather than just a
difference.

    uv run python -m tools.ttpv_redteam --corpus corpus/competition_like_v1.jsonl --depth 6
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess

import cs_search
from cs_search import Searcher
from tools.corpus.suite import load_suite

POLICIES = ("all", "exact", "none")


def run(fen: str, depth: int, policy: str) -> tuple[str, int, int]:
    cs_search.TT_PV_POLICY = policy
    move, info = Searcher(tt_bits=18).search(chess.Board(fen), 0, max_depth=depth)
    return (move.uci() if move else "none"), info.score, info.nodes


def main() -> None:
    parser = argparse.ArgumentParser(description="PV TT-cutoff policy red team.")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--out", type=Path, default=None)
    arguments = parser.parse_args()

    header, fens = load_suite(arguments.corpus)
    labels: dict[str, dict] = {}
    with arguments.corpus.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if "fen" in record:
                labels[record["fen"]] = record

    print(f"suite {arguments.corpus} : {len(fens)} positions, depth {arguments.depth}")
    print(f"  header: {header.get('suite')} {header.get('version')} "
          f"hash={header.get('hash')} oracle={header.get('oracle', {}).get('engine')}")

    baseline = "all"
    rows: list[dict] = []
    for index, fen in enumerate(fens):
        results = {p: run(fen, arguments.depth, p) for p in POLICIES}
        differing = {p for p in POLICIES if results[p][0] != results[baseline][0]}
        if differing:
            label = labels.get(fen, {})
            reference = label.get("reference", {})
            structure = label.get("structure", {})
            rows.append({
                "index": index,
                "fen": fen,
                "results": {p: results[p] for p in POLICIES},
                "oracle_best": reference.get("best"),
                "oracle_cp": reference.get("cp_white"),
                "structures": structure.get("tags"),
            })
        if (index + 1) % 40 == 0:
            print(f"  ...{index + 1}/{len(fens)}, {len(rows)} divergences", flush=True)

    cs_search.TT_PV_POLICY = "exact"

    print(f"\npositions where a policy changes the move: {len(rows)}/{len(fens)}\n")
    for row in rows:
        print(f"  [{row['index']}] {row['fen']}")
        for policy in POLICIES:
            move, score, nodes = row["results"][policy]
            mark = "  <-- oracle best" if move == row["oracle_best"] else ""
            print(f"      {policy:<6} {move:<6} {score:>7}  {nodes:>9,} nodes{mark}")
        print(f"      oracle: {row['oracle_best']} at {row['oracle_cp']} cp")
        if row["structures"]:
            print(f"      structures: {', '.join(row['structures'][:6])}")
        print()

    if arguments.out:
        arguments.out.write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
        )
        print(f"records written to {arguments.out}")


if __name__ == "__main__":
    main()
