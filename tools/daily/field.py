"""Field-wide colour statistics from publicly scraped Chessathon games.

The colour question was previously answerable only from ClaudeShark's own three
rated games, which is n = 3 and settles nothing. A scrape of publicly visible
top-50 team pages provides a much larger sample, and this module reduces it to
the tables the question actually needs: how often each colour scores, what the
starting positions look like, and whether the result is explained by the rating
difference rather than by colour.

Everything here is read-only over data collected outside this module. Rows are
deduplicated by ``game_id`` because the same game appears once per top-50
participant. Games with no final result are dropped and counted separately.

    uv run python -m tools.daily.field --games analysis/top50_games.jsonl --out corpus/daily/field_colour.txt
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import chess


def wilson(successes: float, n: int) -> tuple[float, float]:
    """95% Wilson interval on a score in [0, 1]; draws count as half a success."""
    if n == 0:
        return 0.0, 1.0
    z = 1.959963985
    p = successes / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, centre - spread), min(1.0, centre + spread)


def elo(score: float) -> float:
    score = min(max(score, 1e-9), 1 - 1e-9)
    return -400.0 * math.log10(1.0 / score - 1.0)


def outcome(row: dict) -> str | None:
    """'w', 'b' or 'd' from the most reliable field available."""
    winner = row.get("winner_colour")
    if winner in ("white", "black"):
        return winner[0]
    result = row.get("canonical_result") or ""
    if result == "1-0":
        return "w"
    if result == "0-1":
        return "b"
    if result and result not in ("*", "init"):
        return "d"
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    raw = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    unique = {r["game_id"]: r for r in raw}
    rows = []
    dropped = 0
    for r in unique.values():
        o = outcome(r)
        if o is None or r.get("termination") == "init":
            dropped += 1
            continue
        rows.append({**r, "outcome": o})
    white_points = sum(1.0 if r["outcome"] == "w" else 0.5 if r["outcome"] == "d" else 0.0 for r in rows)
    n = len(rows)
    low, high = wilson(white_points, n)

    lines = [f"== FIELD-WIDE COLOUR STATISTICS: {len(raw)} scraped rows, {len(unique)} unique games, "
             f"{n} with a result ({dropped} dropped) ==",
             f"Source: {arguments.games}. Read-only; results, starting positions and ratings are taken as recorded.", ""]
    counts = Counter(r["outcome"] for r in rows)
    lines.append("== OVERALL ==")
    lines.append(f"   WHITE +{counts['w']} ={counts['d']} -{counts['b']}   n={n}   "
                 f"White scores {white_points / n:.1%}   Elo {elo(white_points / n):+.0f}   "
                 f"95% Wilson {low:.1%}..{high:.1%}")
    lines.append(f"   BLACK +{counts['b']} ={counts['d']} -{counts['w']}   Black scores {1 - white_points / n:.1%}")
    lines.append("   A field-wide Black advantage would show as a White score materially below 50%.")
    lines.append("")

    lines.append("== STARTING POSITIONS ==")
    stm = Counter(r["starting_fen"].split()[1] for r in rows if r.get("starting_fen"))
    lines.append(f"   side to move in the start FEN: {dict(stm)}")
    for side in ("b", "w"):
        subset = [r for r in rows if r.get("starting_fen", " ").split()[1] == side]
        if not subset:
            continue
        points = sum(1.0 if r["outcome"] == "w" else 0.5 if r["outcome"] == "d" else 0.0 for r in subset)
        lo, hi = wilson(points, len(subset))
        lines.append(f"   start FEN with {'Black' if side == 'b' else 'White'} to move: n={len(subset):>4}  "
                     f"White scores {points / len(subset):6.1%}  95% Wilson {lo:.1%}..{hi:.1%}")
    moves = Counter()
    for r in rows:
        fen = r.get("starting_fen")
        if fen:
            with_board = chess.Board(fen)
            moves[with_board.fullmove_number] += 1
    lines.append(f"   full-move number of the start position: {dict(sorted(moves.items()))}")
    lines.append("")

    lines.append("== IS IT THE RATING RATHER THAN THE COLOUR? ==")
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        try:
            dr = int(r["white"]["rating"]) - int(r["black"]["rating"])
        except (KeyError, TypeError, ValueError):
            continue
        key = ("White rated 100+ higher" if dr >= 100 else
               "White rated 25-99 higher" if dr >= 25 else
               "within 25 points     " if dr > -25 else
               "Black rated 25-99 higher" if dr > -100 else
               "Black rated 100+ higher")
        buckets[key].append(r)
        r["rating_gap"] = dr
    order = ["White rated 100+ higher", "White rated 25-99 higher", "within 25 points     ",
             "Black rated 25-99 higher", "Black rated 100+ higher"]
    for key in order:
        subset = buckets.get(key, [])
        if not subset:
            continue
        points = sum(1.0 if r["outcome"] == "w" else 0.5 if r["outcome"] == "d" else 0.0 for r in subset)
        lo, hi = wilson(points, len(subset))
        lines.append(f"   {key:<26} n={len(subset):>4}  White scores {points / len(subset):6.1%}  95% Wilson {lo:.1%}..{hi:.1%}")
    rated = [r for r in rows if "rating_gap" in r]
    if rated:
        mean_gap = sum(r["rating_gap"] for r in rated) / len(rated)
        lines.append(f"   mean rating gap (White minus Black) over {len(rated)} games: {mean_gap:+.1f}")
        lines.append("   A pool in which White is on average the lower-rated side would produce a")
        lines.append("   colour effect that is really a pairing effect.")
    lines.append("")

    lines.append("== BY ROUND ==")
    for rnd in sorted({r.get("round", "?") for r in rows}):
        subset = [r for r in rows if r.get("round") == rnd]
        points = sum(1.0 if r["outcome"] == "w" else 0.5 if r["outcome"] == "d" else 0.0 for r in subset)
        lines.append(f"   {rnd:<12} n={len(subset):>4}  White scores {points / len(subset):6.1%}")
    lines.append("")
    lines.append("== TERMINATIONS ==")
    lines.append(f"   {dict(Counter(r.get('termination') for r in rows))}")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
