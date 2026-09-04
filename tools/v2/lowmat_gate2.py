"""Gate 2 causal metrics for the low-material term: what happened in the games that reached a family.

Alongside W/D/L with the paired cluster bootstrap: every annotated
position in one of the eight families, which engine held the surplus,
each engine's own root there against Stockfish (false-win evaluations),
the same positions rescored by the other engine at the same depth, the
weaker side's draw rate and the stronger side's win rate in those games,
and first serious errors overall and in-family.

    uv run python -m tools.v2.lowmat_gate2 --games <annotated.jsonl> --cand champions/v2_2a_low_material --base champions/v2_1_kingpawn --out <txt>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import chess

from tools.postmortem.play import Engine
from tools.stats import summarise
from tools.v2.krminor import family_of as ref_family_of
from tools.v2.lowmat import family_of as sib_family_of


def family(board: chess.Board):
    return sib_family_of(board) or ref_family_of(board)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--cand", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--cand-name", default="v2_2a_low_material")
    parser.add_argument("--base-name", default="v2_1_kingpawn")
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    stats = summarise([(int(g["cluster"]), g["cand_score"]) for g in games])
    lines = [f"== GATE 2: {len(games)} fixed-depth paired games, {arguments.cand_name} (candidate) vs {arguments.base_name} ==", "",
             f"+{stats.wins} ={stats.draws} -{stats.losses}  score {stats.score:.1%}  Elo {stats.elo:+.0f}",
             f"naive 95% CI {stats.naive_low:+.0f} .. {stats.naive_high:+.0f}   paired cluster bootstrap {stats.boot_low:+.0f} .. {stats.boot_high:+.0f}  ({stats.clusters} clusters)",
             f"terminations: {dict(Counter(g['termination'] for g in games))}", ""]

    in_family = []
    first_serious = Counter()
    for g in games:
        seen = {"cand": False, "base": False}
        for m in g["moves"]:
            if m.get("cp_loss") is not None and m["cp_loss"] >= 100 and not seen[m["mover"]]:
                seen[m["mover"]] = True
                first_serious[m["mover"]] += 1
            board = chess.Board(m["fen"])
            fam = family(board)
            if fam is None or m.get("sf_cp_white_before") is None:
                continue
            white = m["turn"] == "w"
            sf_mover = m["sf_cp_white_before"] if white else -m["sf_cp_white_before"]
            mover_is_strong = board.turn == fam[1]
            strong_engine = m["mover"] if mover_is_strong else ("base" if m["mover"] == "cand" else "cand")
            in_family.append({"cluster": g["cluster"], "cand_white": g["cand_white"], "ply": m["ply"], "fen": m["fen"], "family": fam[0],
                              "mover": m["mover"], "mover_is_strong": mover_is_strong, "strong_engine": strong_engine,
                              "root_mover": m["score_stm"], "sf_mover": sf_mover, "sf_strong": sf_mover if mover_is_strong else -sf_mover,
                              "cp_loss": m.get("cp_loss"), "cand_score": g["cand_score"], "termination": g["termination"]})
    games_reached = {(r["cluster"], r["cand_white"]) for r in in_family}
    lines.append(f"== IN-FAMILY EXPOSURE: {len(in_family)} annotated positions in {len(games_reached)} games; families {dict(Counter(r['family'] for r in in_family))} ==")
    lines.append(f"first serious errors: cand {first_serious['cand']}, base {first_serious['base']} games")
    lines.append("")
    # Rescoring by the other engine.
    engines = {"cand": Engine(arguments.cand, arguments.depth), "base": Engine(arguments.base, arguments.depth)}
    try:
        for r in in_family:
            for name, e in engines.items():
                e.ask("new")
                r[f"root_{name}"] = e.ask(f"go {r['fen']}")["score"]  # side to move's view
    finally:
        for e in engines.values():
            e.close()
    lines.append("== FALSE-WIN EVALUATIONS IN FAMILY (side to move holds the surplus, Stockfish within 60, root >= +150) ==")
    strong_rows = [r for r in in_family if r["mover_is_strong"] and abs(r["sf_mover"]) <= 60]
    for name, label in (("cand", arguments.cand_name), ("base", arguments.base_name)):
        fw = sum(r[f"root_{name}"] >= 150 for r in strong_rows)
        lines.append(f"   {label:<20} scores {fw} of {len(strong_rows)} level in-family positions >= +150 (mean root {sum(r[f'root_{name}'] for r in strong_rows) / max(1, len(strong_rows)):+.0f})")
    lines.append(f"   as played: cand's own false-win moves {sum(1 for r in strong_rows if r['mover'] == 'cand' and r['root_mover'] >= 150)} of {sum(1 for r in strong_rows if r['mover'] == 'cand')}, base's {sum(1 for r in strong_rows if r['mover'] == 'base' and r['root_mover'] >= 150)} of {sum(1 for r in strong_rows if r['mover'] == 'base')}")
    lines.append("")
    lines.append("== GENUINE WINS IN FAMILY (Stockfish >= +300 for the surplus side): both engines' roots ==")
    won_rows = [r for r in in_family if r["mover_is_strong"] and r["sf_mover"] >= 300]
    for name, label in (("cand", arguments.cand_name), ("base", arguments.base_name)):
        lines.append(f"   {label:<20} root < +100 on {sum(r[f'root_{name}'] < 100 for r in won_rows)} of {len(won_rows)} won in-family positions (mean {sum(r[f'root_{name}'] for r in won_rows) / max(1, len(won_rows)):+.0f})")
    lines.append("")
    lines.append("== RESULTS OF THE GAMES THAT REACHED A FAMILY (score for the engine holding the surplus at first entry) ==")
    per_game = {}
    for r in in_family:
        per_game.setdefault((r["cluster"], r["cand_white"]), r)
    tally = defaultdict(Counter)
    for (cluster, cw), r in per_game.items():
        strong = r["strong_engine"]
        score = r["cand_score"] if strong == "cand" else 1.0 - r["cand_score"]
        tally[strong][score] += 1
        lines.append(f"   cluster {cluster:>3} {'cW' if cw else 'cB'}  {r['family']:<7} surplus held by {strong:<4}  SF for the surplus side at entry {r['sf_strong']:>+5}  result for it {score}  ({r['termination']})")
    for strong, label in (("cand", arguments.cand_name), ("base", arguments.base_name)):
        c = tally[strong]
        n = sum(c.values())
        lines.append(f"   {label} held the surplus in {n} games: won {c[1.0]}, drew {c[0.5]}, lost {c[0.0]}")
    weak = defaultdict(Counter)
    for r in per_game.values():
        weak_engine = "base" if r["strong_engine"] == "cand" else "cand"
        score = r["cand_score"] if weak_engine == "cand" else 1.0 - r["cand_score"]
        weak[weak_engine][score] += 1
    for engine_name, label in (("cand", arguments.cand_name), ("base", arguments.base_name)):
        c = weak[engine_name]
        n = sum(c.values())
        lines.append(f"   {label} was the weaker side in {n} games: held (draw or better) {c[0.5] + c[1.0]}, lost {c[0.0]}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in in_family) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
