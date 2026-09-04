"""Per-game analysis of the real rated games, with each snapshot's answer to the critical decisions.

Reads the Stockfish-annotated rated games and the colour attribution
established by ``tools.daily.whoami``, then reports for each game the first
inaccuracy, the first serious error, the largest error, the point the game
turned, and every position where ClaudeShark lost at least ``--threshold``
centipawns. For each of those positions every named snapshot is asked what it
plays at a fixed depth and what it scores, which is what answers "does V2.1
repair this decision" without guessing.

Blind wins and false wins are read the same way as the internal corpora:
Stockfish at least +300 for the side to move while the engine's own root is
under +100 is a blind win; the engine's root at least +150 while Stockfish is
within 60 of level is a false win.

    uv run python -m tools.daily.report --games corpus/daily/games/rated_annotated.jsonl --colours corpus/daily/colours.json --out corpus/daily/rated_report.txt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.postmortem.play import Engine

SNAPSHOTS = {
    "rated-v1": "champions/rated_v1",
    "V2.1 king-pawn": "champions/v2_1_kingpawn",
    "V2.2a low-material": "champions/v2_2a_low_material",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--colours", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--threshold", type=int, default=50)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    colours = json.loads(arguments.colours.read_text(encoding="utf-8"))
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]

    engines = {name: Engine(Path(path), arguments.depth) for name, path in SNAPSHOTS.items()}
    rows = []
    try:
        for g in games:
            cs = colours[g["game"]]["colour"]
            for e in engines.values():
                e.ask("new")
            for m in g["moves"]:
                mine = m["turn"] == cs
                white = m["turn"] == "w"
                sf_before = m["sf_cp_white_before"] if white else -m["sf_cp_white_before"]
                for e in engines.values():
                    e.ask(f"seen {m['fen']}")
                row = {
                    "game": g["game"], "ply": m["ply"], "fullmove": m["fullmove"], "turn": m["turn"],
                    "mine": mine, "san": m["san"], "move": m["move"], "spent": m["spent"],
                    "sf_before": sf_before, "sf_best": m["sf_best"], "cp_loss": m["cp_loss"],
                }
                if mine and abs(sf_before) < 9000:
                    for name, e in engines.items():
                        reply = e.ask(f"go {m['fen']}")
                        row[name] = {"move": reply["move"], "score": reply["score"],
                                     "static": reply["static"] if white else -reply["static"]}
                rows.append(row)
                print(f"  {g['game']} ply {m['ply']}", flush=True)
    finally:
        for e in engines.values():
            e.close()

    lines = ["== REAL RATED GAMES: PER-MOVE ANALYSIS ==",
             f"Colour attribution from tools.daily.whoami (move agreement), snapshots at depth {arguments.depth}.", ""]
    for g in games:
        cs = colours[g["game"]]["colour"]
        info = colours[g["game"]]
        mine = [r for r in rows if r["game"] == g["game"] and r["mine"]]
        theirs = [r for r in rows if r["game"] == g["game"] and not r["mine"]]
        won = (g["result"] == "1-0") == (cs == "w")
        lines.append("=" * 96)
        lines.append(f"{g['game']}   ClaudeShark played {'White' if cs == 'w' else 'Black'}   result {g['result']} "
                     f"({'WIN' if won else 'LOSS'} for ClaudeShark)   termination {g['termination']}")
        lines.append(f"   attribution: {info['evidence']}")
        lines.append(f"   start FEN  {g['start_fen']}")
        lines.append(f"   increment {g['increment']}s; ClaudeShark spend mean "
                     f"{sum(r['spent'] for r in mine if r['spent'] is not None) / max(1, sum(r['spent'] is not None for r in mine)):.2f}s "
                     f"max {max([r['spent'] for r in mine if r['spent'] is not None] or [0]):.2f}s; "
                     f"opponent mean {sum(r['spent'] for r in theirs if r['spent'] is not None) / max(1, sum(r['spent'] is not None for r in theirs)):.2f}s "
                     f"max {max([r['spent'] for r in theirs if r['spent'] is not None] or [0]):.2f}s")
        losses = [r for r in mine if r["cp_loss"] >= arguments.threshold and abs(r["sf_before"]) < 9000]
        first_inacc = next((r for r in mine if r["cp_loss"] >= 50), None)
        first_serious = next((r for r in mine if r["cp_loss"] >= 100), None)
        largest = max(mine, key=lambda r: r["cp_loss"]) if mine else None
        lost_at = next((r for r in mine if r["sf_before"] <= -300), None)
        hard_at = next((r for r in mine if r["sf_before"] <= -100), None)
        for label, r in (("first inaccuracy (>=50)", first_inacc), ("first serious error (>=100)", first_serious),
                         ("largest error", largest), ("first position at -100 or worse", hard_at),
                         ("first position at -300 or worse", lost_at)):
            if r is None:
                lines.append(f"   {label:<32} none")
            else:
                lines.append(f"   {label:<32} move {r['fullmove']} {r['san']:<8} (ply {r['ply']}) "
                             f"SF before {r['sf_before']:+5} loss {r['cp_loss']:>5}  Stockfish preferred {r['sf_best']}")
        blind = [r for r in mine if r["sf_before"] >= 300 and abs(r["sf_before"]) < 9000 and r.get("rated-v1", {}).get("score", 0) < 100]
        false = [r for r in mine if abs(r["sf_before"]) <= 60 and r.get("rated-v1", {}).get("score", -999) >= 150]
        lines.append(f"   blind-win positions (SF >= +300, rated-v1 root < +100): {len(blind)}")
        lines.append(f"   false-win positions (|SF| <= 60, rated-v1 root >= +150): {len(false)}")
        lines.append("")
        lines.append(f"   ClaudeShark decisions costing at least {arguments.threshold} cp, and what each snapshot plays there:")
        header = f"      {'mv':>3} {'san':<8} {'spent':>6} {'SF':>6} {'loss':>5} {'SF best':<7}"
        for name in SNAPSHOTS:
            header += f" | {name:<18}"
        lines.append(header)
        for r in losses:
            line = f"      {r['fullmove']:>3} {r['san']:<8} {r['spent']!s:>6} {r['sf_before']:>+6} {r['cp_loss']:>5} {r['sf_best']!s:<7}"
            for name in SNAPSHOTS:
                d = r.get(name)
                if d is None:
                    line += f" | {'-':<18}"
                else:
                    agree = "=" if d["move"] == r["move"] else ("*" if d["move"] == r["sf_best"] else " ")
                    line += f" | {d['move']:<5}{agree} {d['score']:>+5} st{d['static']:>+5}"
            lines.append(line)
        lines.append("      '=' the snapshot plays the move actually played; '*' it plays Stockfish's move instead.")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
