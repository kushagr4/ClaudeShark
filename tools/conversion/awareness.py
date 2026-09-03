"""Does the engine know it is winning? Root score against Stockfish standing.

For every production move in the retained games the search's root score is
compared with Stockfish's standing for the same side. The gap matters more than
the static evaluation's, because the root score is what actually chooses the
move: an engine whose search says +10 in a position Stockfish scores +500 is
not "failing to convert" -- it does not know there is anything to convert.

    uv run python -m tools.conversion.awareness --games <annotated.jsonl> --out <txt>
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import chess

from tools.corpus.structure import analyse_structure


def own(m: dict) -> int:
    return m["sf_cp_white_before"] if m["turn"] == "w" else -m["sf_cp_white_before"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    out = ["== DOES THE ENGINE KNOW IT IS WINNING? (production root score vs Stockfish, mover = production) ==", ""]
    bands = (("+100..+299", 100, 300), ("+300..+599", 300, 600), ("+600..+999", 600, 1000), (">= +1000 (incl. mates)", 1000, 10**6))
    out.append(f"{'Stockfish band':<24} {'n':>5} {'mean SF':>8} {'mean root':>10} {'mean static':>12} {'root<100':>9} {'root<0':>7} {'serious%':>9} {'serious% | root<100':>20} {'serious% | root>=300':>21}")
    per_phase: dict = defaultdict(lambda: defaultdict(list))
    for label, lo, hi in bands:
        rows = []
        for g in games:
            for m in g["moves"]:
                if m["mover"] != "base":
                    continue
                v = own(m)
                if lo <= v < hi:
                    st = m["base_static"] if m["turn"] == "w" else -m["base_static"]
                    rows.append((v, m["score_stm"], st, m["cp_loss"], m["fen"]))
        if not rows:
            continue
        n = len(rows)
        low = [r for r in rows if r[1] < 100]
        high = [r for r in rows if r[1] >= 300]
        out.append(f"{label:<24} {n:>5} {statistics.mean(min(r[0], 2000) for r in rows):>+8.0f} "
                   f"{statistics.mean(min(r[1], 2000) for r in rows):>+10.0f} {statistics.mean(r[2] for r in rows):>+12.0f} "
                   f"{len(low) / n:>9.1%} {sum(1 for r in rows if r[1] < 0) / n:>7.1%} "
                   f"{sum(1 for r in rows if r[3] >= 100) / n:>9.1%} "
                   f"{(sum(1 for r in low if r[3] >= 100) / len(low) if low else 0):>20.1%} "
                   f"{(sum(1 for r in high if r[3] >= 100) / len(high) if high else 0):>21.1%}")
        for r in rows:
            ph = analyse_structure(chess.Board(r[4])).phase
            per_phase[label][ph].append(r)
    out.append("")
    out.append("root score < 100 while Stockfish >= +300, by phase:")
    for label, _, _ in bands[1:]:
        for ph, rows in per_phase[label].items():
            if len(rows) >= 10:
                out.append(f"  {label:<24} {ph:<11} n={len(rows):>4}  root<100 {sum(1 for r in rows if r[1] < 100) / len(rows):.1%}  "
                           f"serious {sum(1 for r in rows if r[3] >= 100) / len(rows):.1%}")
    out.append("")
    out.append("reading: 'root<100' is the share of objectively winning positions in which the search itself")
    out.append("reports no advantage worth converting. The two right-hand columns show whether serious errors")
    out.append("concentrate in those blind positions or are spread across positions the engine does see as won.")
    # Static vs root disagreement direction in winning positions
    disagree = Counter()
    for g in games:
        for m in g["moves"]:
            if m["mover"] != "base" or not 300 <= own(m) < 9000:
                continue
            st = m["base_static"] if m["turn"] == "w" else -m["base_static"]
            key = ("static>=200" if st >= 200 else "static<200") + " & " + ("root>=200" if m["score_stm"] >= 200 else "root<200")
            disagree[key] += 1
    out.append("")
    out.append(f"static vs root when Stockfish >= +300: {dict(disagree)}")
    text = "\n".join(out)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
