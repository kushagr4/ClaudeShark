"""One authoritative record per ClaudeShark rated game, with its evidence sources.

Merges everything the repository knows about each rated game into a single
row and says, field by field, where each fact came from. Inferred and
confirmed information are never silently merged: every row carries
``colour_source``, ``result_source``, ``metadata_source`` and ``oracle_source``,
and every independent source is cross-checked against the others.

Inputs, all optional except the ingested games:

* ``corpus/daily/games/rated15.jsonl`` -- moves, clocks and results parsed from
  the anonymised PGNs (``tools.daily.ingest``).
* ``corpus/daily/colours.json`` -- our colour per game with its evidence.
* ``analysis/refresh_<date>/claudeshark_team_games.json`` -- the public team
  page: round, opponent, opening, match id, our colour and result.
* ``corpus/daily/logs/round*.log`` -- the dashboard's direct match logs where
  the user downloaded them: init time, per-move spend, clock left, slowest move.
* ``corpus/daily/games/rated15_annotated.jsonl`` -- Stockfish annotation
  (``tools.postmortem.annotate``): cp loss per move.
* ``corpus/daily/rated15_report.jsonl`` -- snapshot answers per critical
  position (``tools.daily.report``): what rated-v1 / V2.1 / V2.2a play and score.
* ``corpus/daily/rated_classes.json`` -- hand-written mechanism classification.

    uv run python -m tools.daily.dataset --out corpus/daily/rated_games.json
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import statistics
from pathlib import Path

import chess

LOG_ROW = re.compile(r"^\s+(\d+)\s+(\S+)\s+([\d.]+) s\s+([\d.]+) s", re.M)
SERIOUS = 100
BLUNDER = 300
SCORE_GAP = 200  # engine root at least this far from the oracle: wrong score


def round_of(name: str) -> int:
    return int(re.match(r"round(\d+)", name).group(1))


def parse_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    def field(label: str) -> str | None:
        m = re.search(rf"^\s+{re.escape(label)}\s{{2,}}(.+?)\s*$", text, re.M)
        return m.group(1) if m else None

    rows = [(int(a), b, float(c), float(d)) for a, b, c, d in LOG_ROW.findall(text)]
    return {
        "match_id": field("Match ID"), "colour": field("Colour"), "opponent": field("Opponent"),
        "opening": field("Opening"), "moved_first": field("You moved"), "finished_utc": field("Finished"),
        "init_ready": field("Ready in"), "init_budget": field("Budget"),
        "time_used": field("Time used"), "slowest": field("Slowest"), "left_at_end": field("Left at end"),
        "result_line": next((line.strip() for line in text.splitlines()
                             if re.match(r"^\s+(Won|Lost|Drawn)", line)), None),
        "moves": rows,
    }


def describe(x: dict | None) -> str:
    if not x:
        return "none"
    return f"{x['move']} {x['san']} -{x['cp_loss']}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, default=Path("corpus/daily/games/rated15.jsonl"))
    parser.add_argument("--colours", type=Path, default=Path("corpus/daily/colours.json"))
    parser.add_argument("--team-games", type=Path,
                        default=Path("analysis/refresh_2026-09-05/claudeshark_team_games.json"))
    parser.add_argument("--logs", type=Path, default=Path("corpus/daily/logs"))
    parser.add_argument("--annotated", type=Path, default=Path("corpus/daily/games/rated15_annotated.jsonl"))
    parser.add_argument("--report", type=Path, default=Path("corpus/daily/rated15_report.jsonl"))
    parser.add_argument("--classes", type=Path, default=Path("corpus/daily/rated_classes.json"))
    parser.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()

    games = {}
    for line in a.games.open(encoding="utf-8"):
        g = json.loads(line)
        games[g["game"]] = g
    colours = json.loads(a.colours.read_text(encoding="utf-8"))
    team = {}
    if a.team_games.exists():
        for t in json.loads(a.team_games.read_text(encoding="utf-8")):
            team[int(t["round"].split()[-1])] = t
    logs = {}
    for p in glob.glob(str(a.logs / "round*.log")):
        logs[round_of(Path(p).name)] = parse_log(Path(p))
    annotated = {}
    if a.annotated.exists():
        for line in a.annotated.open(encoding="utf-8"):
            g = json.loads(line)
            annotated[g["game"]] = g
    report: dict[str, list[dict]] = {}
    if a.report.exists():
        for line in a.report.open(encoding="utf-8"):
            r = json.loads(line)
            report.setdefault(r["game"], []).append(r)
    classes = json.loads(a.classes.read_text(encoding="utf-8")) if a.classes.exists() else {}

    rows = []
    for name, g in sorted(games.items(), key=lambda kv: round_of(kv[0])):
        r = round_of(name)
        c = colours.get(name, {})
        cs = c.get("colour")
        t = team.get(r)
        log = logs.get(r)
        board = chess.Board(g["start_fen"])
        mine = [m for m in g["moves"] if m["turn"] == cs]
        spends = [m["spent"] for m in mine if m["spent"] is not None]
        pgn_result = g["result"]
        if cs is None:
            ours = None
        elif pgn_result == "1/2-1/2":
            ours = "draw"
        else:
            ours = "win" if (pgn_result == "1-0") == (cs == "w") else "loss"
        row = {
            "round": r, "game": name,
            "match_id": (t or {}).get("game_id") or (log or {}).get("match_id"),
            "opponent": (t or {}).get("opponent_name") or (log or {}).get("opponent") or c.get("opponent"),
            "our_colour": {"w": "white", "b": "black"}.get(cs),
            "result_for_us": ours, "pgn_result": pgn_result, "termination": g["termination"],
            "start_fen": g["start_fen"], "side_to_move_at_start": "white" if board.turn else "black",
            "opening": (t or {}).get("opening") or (log or {}).get("opening"),
            "plies": g["plies"], "our_moves": len(mine),
            "time_used_s": round(120 + 0.5 * len(mine) - mine[-1]["clock"], 1) if mine else None,
            "time_remaining_s": mine[-1]["clock"] if mine else None,
            "slowest_think_s": max(spends) if spends else None,
            "mean_think_s": round(statistics.mean(spends), 2) if spends else None,
            "instant_moves": sum(s <= 0.1 for s in spends),
            "log_init_ready": (log or {}).get("init_ready"),
            "log_time_used": (log or {}).get("time_used"),
            "log_slowest": (log or {}).get("slowest"),
            "log_left_at_end": (log or {}).get("left_at_end"),
            "log_finished_utc": (log or {}).get("finished_utc"),
            "colour_source": c.get("colour_source", "unknown"),
            "result_source": "PGN result tag" + (" + public team page" if t else "") + (" + direct log" if log else ""),
            "metadata_source": ", ".join(
                s for s, ok in (("public team page", bool(t)), ("direct match log", bool(log)),
                                ("anonymised PGN", True)) if ok),
            "oracle_source": None,
        }
        checks = []
        if t and cs:
            checks.append(("team page colour", t["our_colour"] == row["our_colour"]))
            checks.append(("team page result", t["result"] == ours))
        if log and cs:
            checks.append(("log colour", (log["colour"] or "").lower() == row["our_colour"]))
            if log["result_line"]:
                lr = {"Won": "win", "Lost": "loss", "Drawn": "draw"}[log["result_line"].split()[0]]
                checks.append(("log result", lr == ours))
            if log["match_id"] and t:
                checks.append(("match id", log["match_id"] == t["game_id"]))
        row["cross_checks"] = dict(checks)
        row["consistent"] = all(v for _, v in checks) if checks else None

        ann = annotated.get(name)
        if ann and cs:
            row["oracle_source"] = "Stockfish via tools.postmortem.annotate (200k nodes, refined at 1M where loss >= 50)"
            my = [m for m in ann["moves"] if m["turn"] == cs and abs(m["sf_cp_white_before"]) < 9000]
            losses = [{"move": m["fullmove"], "san": m["san"], "cp_loss": m["cp_loss"],
                       "sf_before": m["sf_cp_white_before"] if cs == "w" else -m["sf_cp_white_before"]}
                      for m in my]
            row["first_serious_error"] = next((x for x in losses if x["cp_loss"] >= SERIOUS), None)
            row["largest_cp_loss"] = max(losses, key=lambda x: x["cp_loss"]) if losses else None
            row["errors_ge_100"] = sum(x["cp_loss"] >= SERIOUS for x in losses)
            row["errors_ge_300"] = sum(x["cp_loss"] >= BLUNDER for x in losses)
            theirs = [m for m in ann["moves"] if m["turn"] != cs and abs(m["sf_cp_white_before"]) < 9000]
            row["opponent_errors_ge_100"] = sum(m["cp_loss"] >= SERIOUS for m in theirs)
            row["opponent_errors_ge_300"] = sum(m["cp_loss"] >= BLUNDER for m in theirs)
            trail = [(m["fullmove"], m["san"], m["sf_cp_white_before"] if cs == "w" else -m["sf_cp_white_before"])
                     for m in ann["moves"] if m["turn"] == cs]
            row["first_at_plus_300"] = next(({"move": f, "san": s, "sf": v} for f, s, v in trail if 300 <= v < 9000), None)
            row["first_at_minus_300"] = next(({"move": f, "san": s, "sf": v} for f, s, v in trail if -9000 < v <= -300), None)
            row["max_advantage_reached"] = max((v for _, _, v in trail if v < 9000), default=None)
            row["min_advantage_reached"] = min((v for _, _, v in trail if v > -9000), default=None)
        rep = report.get(name)
        if rep:
            mine_rep = [x for x in rep if x["mine"] and "V2.1 king-pawn" in x]
            gaps = [{"move": x["fullmove"], "san": x["san"], "v21_root": x["V2.1 king-pawn"]["score"],
                     "sf": x["sf_before"], "gap": abs(x["V2.1 king-pawn"]["score"] - x["sf_before"]),
                     "loss": x["cp_loss"]} for x in mine_rep]
            row["largest_score_disagreement"] = max(gaps, key=lambda d: d["gap"], default=None)
            row["correct_move_wrong_score"] = sum(1 for d in gaps if d["loss"] < 50 and d["gap"] >= SCORE_GAP)
            row["wrong_move_wrong_score"] = sum(1 for d in gaps if d["loss"] >= SERIOUS and d["gap"] >= SCORE_GAP)
            row["wrong_move_right_score"] = sum(1 for d in gaps if d["loss"] >= SERIOUS and d["gap"] < SCORE_GAP)
            critical = [x for x in rep if x["mine"] and "rated-v1" in x and x["cp_loss"] >= 50]
            row["critical_positions_examined"] = len(critical)
            row["v21_differs_from_ratedv1_at_critical"] = sum(
                1 for x in critical if x["rated-v1"]["move"] != x["V2.1 king-pawn"]["move"])
        cls = classes.get(name, {})
        row["mechanism"] = cls.get("mechanism")
        row["king_pawn_materially_activated"] = cls.get("king_pawn_activated")
        row["classification_source"] = cls.get("source")
        rows.append(row)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    header = (f"{'R':>2} {'colour':<6} {'result':<5} {'opponent':<28} {'term':<20} {'moves':>5} {'used':>6} "
              f"{'left':>6} {'slow':>5} {'>=100':>5} {'>=300':>5} {'first serious':<18} {'largest':<18} "
              f"{'consistent':<10} colour_source")
    lines = [header]
    for r in rows:
        lines.append(
            f"{r['round']:>2} {r['our_colour'] or '?':<6} {r['result_for_us'] or '?':<5} "
            f"{(r['opponent'] or '?')[:28]:<28} {r['termination'][:20]:<20} {r['our_moves']:>5} "
            f"{r['time_used_s']!s:>6} {r['time_remaining_s']!s:>6} {r['slowest_think_s']!s:>5} "
            f"{r.get('errors_ge_100', '-')!s:>5} {r.get('errors_ge_300', '-')!s:>5} "
            f"{describe(r.get('first_serious_error')):<18} {describe(r.get('largest_cp_loss')):<18} "
            f"{r['consistent']!s:<10} {r['colour_source']}")
    a.out.with_suffix(".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines).encode("ascii", "replace").decode())


if __name__ == "__main__":
    main()
