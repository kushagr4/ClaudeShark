"""Gate 2 summary for the mop-up candidate: match statistics and the targeted metric.

Alongside W/D/L with the paired cluster bootstrap and the termination mix,
this answers the question the experiment was built to answer: in every game
where a bare-king ending -- the activation domain -- actually arose, which
side was the attacker, and did it win? Compared for the candidate and the
baseline as attacker.

    uv run python -m tools.mopup.gate2 --games <gate2_fixed_depth.jsonl> --out <txt>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import chess

from cs_mopup import mop_up
from tools.stats import summarise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    stats = summarise([(int(g["cluster"]), g["cand_score"]) for g in games])
    lines = ["== GATE 2: 200 fixed-depth paired games, v0_7_mopup (candidate) vs v0_5_2_correctness ==", "",
             f"+{stats.wins} ={stats.draws} -{stats.losses}  score {stats.score:.1%}  Elo {stats.elo:+.0f}",
             f"naive 95% CI {stats.naive_low:+.0f} .. {stats.naive_high:+.0f}   paired cluster bootstrap {stats.boot_low:+.0f} .. {stats.boot_high:+.0f}  ({stats.clusters} clusters)",
             f"terminations: {dict(Counter(g['termination'] for g in games))}",
             f"failures (no_move / ply_cap): {sum(1 for g in games if g['termination'] in ('no_move', 'ply_cap'))}", ""]
    # Targeted metric: bare-king endings that arose, by attacker.
    lines.append("== ELEMENTARY WON-ENDING CONVERSION (bare-king positions that arose in play) ==")
    rows = {"cand": [], "base": []}
    for g in games:
        first = next((m for m in g["moves"] if mop_up(chess.Board(m["fen"])) != 0), None)
        if first is None:
            continue
        board = chess.Board(first["fen"])
        term = mop_up(board)
        attacker_is_white = term > 0
        attacker = "cand" if attacker_is_white == g["cand_white"] else "base"
        score = g["cand_score"] if attacker == "cand" else 1.0 - g["cand_score"]
        rows[attacker].append((g["cluster"], g["cand_white"], first["ply"], g["plies"] - first["ply"], g["termination"], score))
    for side in ("cand", "base"):
        r = rows[side]
        if not r:
            lines.append(f"  {side} as attacker: no bare-king endings arose")
            continue
        won = sum(1 for x in r if x[5] == 1.0)
        lines.append(f"  {side} as attacker: {len(r)} games reached a bare-king ending -> won {won}/{len(r)} "
                     f"({won / len(r):.0%}); terminations {dict(Counter(x[4] for x in r))}; "
                     f"mean plies from entering the domain to the end {sum(x[3] for x in r) / len(r):.1f}")
        for c, cw, ply, rest, term, sc in sorted(r):
            lines.append(f"     cluster {c:>3} cand {'W' if cw else 'B'} entered at ply {ply:>3}, {rest:>3} more plies, {term:<22} attacker score {sc}")
    lines.append("")
    lines.append("reading: 'cand as attacker' games are where the term was live; 'base as attacker' games are the")
    lines.append("control -- the same endings reached by the engine without the term.")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
