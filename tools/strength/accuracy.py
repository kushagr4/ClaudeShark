"""CLAUDESHARK_ACCURACY_V1: per-game accuracy of our moves in an annotated match.

Definition frozen in benchmarks/current/ACCURACY_STANDARD.md. Input is the
games schema after `tools.postmortem.annotate` with an `agent_colour` field
(`tools.strength.convert` writes it). Output: a per-game table (JSONL and
Markdown) and the distribution statistics the standard requires.

    uv run python -m tools.strength.accuracy --games <annotated.jsonl> --out <acc.jsonl>
        --report <acc.md>
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

CLAMP = 1000
VERSION = "CLAUDESHARK_ACCURACY_V1"


def win_pct(cp: float) -> float:
    return 50.0 + 50.0 * (2.0 / (1.0 + math.exp(-0.00368208 * cp)) - 1.0)


def move_accuracy(cp_before: float, cp_after: float) -> float:
    before = max(-CLAMP, min(CLAMP, cp_before))
    after = max(-CLAMP, min(CLAMP, cp_after))
    value = 103.1668 * math.exp(-0.04354 * (win_pct(before) - win_pct(after))) - 3.1669
    return max(0.0, min(100.0, value))


def state(cp: float) -> str:
    if cp >= 150:
        return "win"
    if cp <= -150:
        return "loss"
    return "draw"


def game_accuracy(game: dict) -> dict:
    colour = game["agent_colour"]
    white = colour == "w"
    accs: list[float] = []
    losses: list[int] = []
    e50 = e100 = e300 = flips = 0
    audited = 0
    max_loss = 0
    for m in game["moves"]:
        if m["turn"] != colour:
            continue
        before = m["sf_cp_white_before"] if white else -m["sf_cp_white_before"]
        after = m["sf_cp_white_after"] if white else -m["sf_cp_white_after"]
        accs.append(move_accuracy(before, after))
        loss = int(m["cp_loss"])
        losses.append(min(loss, CLAMP))
        if abs(before) < 800:
            audited += 1
            max_loss = max(max_loss, loss)
            if loss >= 50:
                e50 += 1
            if loss >= 100:
                e100 += 1
                if state(before) != state(after) and state(after) != "win":
                    flips += 1
            if loss >= 300:
                e300 += 1
    return {
        "game": game["game"], "result": game.get("agent_score"), "colour": colour,
        "moves": len(accs), "accuracy": round(statistics.mean(accs), 2) if accs else None,
        "acpl": round(statistics.mean(losses), 1) if losses else None,
        "max_loss": max_loss, "audited": audited, "e50": e50, "e100": e100, "e300": e300,
        "flips": flips, "termination": game.get("termination"), "plies": game.get("plies"),
    }


def summarise(rows: list[dict]) -> dict:
    accs = sorted(r["accuracy"] for r in rows if r["accuracy"] is not None)
    n = len(accs)
    audited = sum(r["audited"] for r in rows) or 1
    return {
        "version": VERSION, "games": n,
        "mean": round(statistics.mean(accs), 2), "median": round(statistics.median(accs), 2),
        "min": round(accs[0], 2), "p10": round(accs[max(0, int(0.1 * (n - 1)))], 2),
        "ge_99_5": sum(a >= 99.5 for a in accs), "lt_99_5": sum(a < 99.5 for a in accs),
        "lt_99": sum(a < 99.0 for a in accs), "lt_98": sum(a < 98.0 for a in accs),
        "rate_50": round(100.0 * sum(r["e50"] for r in rows) / audited, 2),
        "rate_100": round(100.0 * sum(r["e100"] for r in rows) / audited, 2),
        "rate_300": round(100.0 * sum(r["e300"] for r in rows) / audited, 2),
        "flips": sum(r["flips"] for r in rows),
        "acpl": round(statistics.mean(r["acpl"] for r in rows if r["acpl"] is not None), 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--label", default="")
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8") if line.strip()]
    rows = [game_accuracy(g) for g in games]
    summary = summarise(rows)
    with arguments.out.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"record": "summary", **summary}) + "\n")
        for r in rows:
            handle.write(json.dumps(r) + "\n")
    lines = [
        f"# {VERSION} — {arguments.label or arguments.games.name}",
        "",
        f"games {summary['games']}; **mean {summary['mean']}**, median {summary['median']}, "
        f"**minimum {summary['min']}**, p10 {summary['p10']}; games >= 99.5: {summary['ge_99_5']}, "
        f"< 99.5: {summary['lt_99_5']}, < 99.0: {summary['lt_99']}, < 98.0: {summary['lt_98']}; "
        f">= 50 cp {summary['rate_50']}%, >= 100 cp {summary['rate_100']}%, >= 300 cp "
        f"{summary['rate_300']}% of audited moves; result-flipping errors {summary['flips']}; "
        f"ACPL_V1 {summary['acpl']}",
        "",
        "| game | result | col | moves | accuracy | acpl | max loss | >=50 | >=100 | >=300 | "
        "flips | termination |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda x: (x["accuracy"] if x["accuracy"] is not None else 0)):
        lines.append(
            f"| {r['game'][-4:]} | {r['result']} | {r['colour']} | {r['moves']} | "
            f"{r['accuracy']} | {r['acpl']} | {r['max_loss']} | {r['e50']} | {r['e100']} | "
            f"{r['e300']} | {r['flips']} | {r['termination']} |"
        )
    arguments.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(lines[2])
    print(f"written {arguments.out} and {arguments.report}")


if __name__ == "__main__":
    main()
