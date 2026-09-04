"""How much information does a paired match actually contain?

A paired fixed-depth match plays every start position twice with the colours
swapped. When the two engines are deterministic and nearly identical, both
games of a pair are frequently the *same game*, and then the candidate scores
1 in one and 0 in the other: a cluster whose per-cluster mean is exactly 0.5
has told us nothing, however many wins and losses it contributed to the
headline. The V2.2a low-material match looked like +38 =125 -37 over 200 games
and was, on inspection, one informative start position out of a hundred.

This reports, for any paired corpus: the number of clusters whose pair was not
mirror-identical, the distribution of per-cluster means, how many cluster-units
of advantage the result rests on, the leave-one-cluster-out range of the Elo
estimate, and how many of the best clusters have to be removed before the
estimate reaches zero. Those last two are the direct answer to "is this driven
by a few starting positions".

    uv run python -m tools.daily.clusters --games corpus/v2/kp/games/gate2_fixed_depth.jsonl --out corpus/daily/cluster_evidence.txt
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def elo(score: float) -> float:
    score = min(max(score, 1e-9), 1 - 1e-9)
    return -400.0 * math.log10(1.0 / score - 1.0)


def describe(name: str, games: list[dict]) -> list[str]:
    grouped: dict[int, list[float]] = defaultdict(list)
    for g in games:
        grouped[int(g["cluster"])].append(g["cand_score"])
    per = {c: sum(v) / len(v) for c, v in grouped.items()}
    total = sum(len(v) for v in grouped.values())
    score = sum(x for v in grouped.values() for x in v) / total
    informative = [c for c, v in per.items() if v != 0.5]
    lines = [f"{name}",
             f"   {total} games, {len(grouped)} clusters, score {score:.4f}, Elo {elo(score):+.1f}",
             f"   clusters whose pair was NOT mirror-identical: {len(informative)} of {len(grouped)}",
             f"   per-cluster mean distribution: {dict(sorted(Counter(per.values()).items()))}",
             f"   net cluster-units above 0.5: {sum(v - 0.5 for v in per.values()):+.2f}"]
    if not informative:
        lines.append("   the match contains no information about the difference between the two engines")
        return lines
    loo = sorted(
        (elo(sum(x for k, v in grouped.items() if k != c for x in v)
             / sum(len(v) for k, v in grouped.items() if k != c)), c)
        for c in grouped
    )
    lines.append(f"   leave-one-cluster-out Elo: {loo[0][0]:+.1f} (dropping cluster {loo[0][1]}) .. {loo[-1][0]:+.1f} (dropping cluster {loo[-1][1]})")
    order = sorted(per, key=lambda c: -per[c])
    removed: list[int] = []
    for c in order:
        kept = [x for k, v in grouped.items() if k not in removed for x in v]
        if not kept or elo(sum(kept) / len(kept)) <= 0:
            break
        removed.append(c)
    if elo(score) > 0:
        lines.append(f"   the {len(removed)} best clusters must be removed before the estimate reaches zero: {removed}")
    else:
        lines.append("   the estimate is already at or below zero")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    lines = ["== HOW MUCH INFORMATION IS IN EACH PAIRED MATCH ==",
             "A cluster whose two games are mirror images of each other contributes a win and a loss and no information.", ""]
    for path in arguments.games:
        if not path.exists():
            lines.append(f"{path}: MISSING")
            continue
        games = [json.loads(line) for line in path.open(encoding="utf-8")]
        lines += describe(str(path), games)
        lines.append("")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
