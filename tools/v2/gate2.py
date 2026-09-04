"""Gate 2 summary for a V2 candidate: match statistics and the endgame metrics the experiment is about.

Beyond W/D/L with the paired cluster bootstrap: how often each engine
found itself in a blind win (Stockfish >= +300, own root < +100) or a false
win (own root >= +200, Stockfish level), conversion from +200 and +500 and
defence from -200, conversion split by the kind of ending that arose (pawn
ending, rook ending, low material), first-serious-error rates and the
repetition outcomes.

    uv run python -m tools.v2.gate2 --games <annotated.jsonl> --cand-name v2_1_kingpawn --base-name rated_v1 --out <txt>
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import chess

from tools.stats import summarise


def mover_cp(m: dict, key: str) -> int | None:
    v = m.get(key)
    if v is None:
        return None
    return v if m["turn"] == "w" else -v


def ending_kind(board: chess.Board) -> str:
    non_pawn = (board.occupied & ~board.pawns & ~board.kings).bit_count()
    if non_pawn == 0 and board.pawns:
        return "pawn ending"
    if (board.queens | board.bishops | board.knights) == 0 and board.rooks:
        return "rook ending"
    if non_pawn <= 2:
        return "low material"
    return "other"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--cand-name", default="candidate")
    parser.add_argument("--base-name", default="baseline")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    stats = summarise([(int(g["cluster"]), g["cand_score"]) for g in games])
    lines = [f"== GATE 2: {len(games)} fixed-depth paired games, {arguments.cand_name} (candidate) vs {arguments.base_name} ==", "",
             f"+{stats.wins} ={stats.draws} -{stats.losses}  score {stats.score:.1%}  Elo {stats.elo:+.0f}",
             f"naive 95% CI {stats.naive_low:+.0f} .. {stats.naive_high:+.0f}   paired cluster bootstrap {stats.boot_low:+.0f} .. {stats.boot_high:+.0f}  ({stats.clusters} clusters)",
             f"terminations: {dict(Counter(g['termination'] for g in games))}",
             f"as white: cand {sum(g['cand_score'] for g in games if g['cand_white']) / max(1, sum(1 for g in games if g['cand_white'])):.1%}, "
             f"as black: cand {sum(g['cand_score'] for g in games if not g['cand_white']) / max(1, sum(1 for g in games if not g['cand_white'])):.1%}", ""]

    # Per-move evaluation classes and errors.
    counts: dict[str, Counter] = {"cand": Counter(), "base": Counter()}
    losses: dict[str, list[int]] = {"cand": [], "base": []}
    first_serious: Counter = Counter()
    conv: dict[str, dict[str, list[float]]] = {"cand": defaultdict(list), "base": defaultdict(list)}
    for g in games:
        seen_first = {"cand": False, "base": False}
        thresholds: dict[str, set] = {"cand": set(), "base": set()}
        for m in g["moves"]:
            side = m["mover"]
            sf = mover_cp(m, "sf_cp_white_before")
            if sf is None:
                continue
            root = m["score_stm"]
            counts[side]["moves"] += 1
            if sf >= 300 and root < 100:
                counts[side]["blind_win"] += 1
            if root >= 200 and abs(sf) <= 50:
                counts[side]["false_win"] += 1
            if m.get("cp_loss") is not None:
                losses[side].append(min(m["cp_loss"], 500))
                if m["cp_loss"] >= 100 and not seen_first[side]:
                    seen_first[side] = True
                    first_serious[side] += 1
            score = g["cand_score"] if side == "cand" else 1.0 - g["cand_score"]
            board = chess.Board(m["fen"])
            kind = ending_kind(board)
            for label, cond in (("ahead +200", sf >= 200), ("ahead +500", sf >= 500), ("behind -200", sf <= -200)):
                key = (label,)
                if cond and key not in thresholds[side]:
                    thresholds[side].add(key)
                    conv[side][label].append(score)
            if sf >= 200 and (kind, "ahead") not in thresholds[side]:
                thresholds[side].add((kind, "ahead"))
                conv[side][f"ahead +200 in {kind}"].append(score)
    lines.append("== EVALUATION CLASSES IN PLAY (share of the engine's own moves) ==")
    for side, name in (("cand", arguments.cand_name), ("base", arguments.base_name)):
        c = counts[side]
        lines.append(f"  {name:<18} moves {c['moves']:>5}  blind-win {c['blind_win']:>4} ({c['blind_win'] / max(1, c['moves']):.1%})  false-win {c['false_win']:>4} ({c['false_win'] / max(1, c['moves']):.1%})  "
                     f"robust loss {statistics.mean(losses[side]) if losses[side] else 0:.1f}  serious {sum(v >= 100 for v in losses[side]) / max(1, len(losses[side])):.1%}  games with a first serious error {first_serious[side]}")
    lines.append("")
    lines.append("== CONVERSION AND DEFENCE (first time the threshold is reached; won / drew / lost from that side) ==")
    labels = ["ahead +200", "ahead +500", "behind -200", "ahead +200 in pawn ending", "ahead +200 in rook ending", "ahead +200 in low material", "ahead +200 in other"]
    lines.append(f"  {'situation':<30} {'cand n':>7} {'won':>6} {'drew':>6} {'lost':>6} | {'base n':>7} {'won':>6} {'drew':>6} {'lost':>6}")
    for label in labels:
        cells = []
        for side in ("cand", "base"):
            xs = conv[side].get(label, [])
            n = len(xs)
            if label.startswith("behind"):
                won = sum(x >= 0.5 for x in xs) / max(1, n)  # held
                drew = sum(x == 0.5 for x in xs) / max(1, n)
                lost = sum(x == 0.0 for x in xs) / max(1, n)
            else:
                won = sum(x == 1.0 for x in xs) / max(1, n)
                drew = sum(x == 0.5 for x in xs) / max(1, n)
                lost = sum(x == 0.0 for x in xs) / max(1, n)
            cells.append(f"{n:>7} {won:>6.0%} {drew:>6.0%} {lost:>6.0%}")
        lines.append(f"  {label:<30} " + " | ".join(cells) + ("   (won = held: draw or win)" if label.startswith("behind") else ""))
    lines.append("")
    reps = [g for g in games if g["termination"] == "threefold_repetition"]
    lines.append(f"== REPETITION OUTCOMES: {len(reps)} of {len(games)} games ==")
    for side, name in (("cand", arguments.cand_name), ("base", arguments.base_name)):
        ahead = 0
        for g in reps:
            last = [m for m in g["moves"] if m["mover"] == side and m.get("sf_cp_white_before") is not None]
            if last and mover_cp(last[-1], "sf_cp_white_before") >= 200:
                ahead += 1
        lines.append(f"  {name}: repetition while Stockfish had it >= +200 at its last annotated move: {ahead}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
