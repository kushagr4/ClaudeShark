"""Swiss-oriented risk report for a timed arena match.

A 13-round Swiss over one locked build punishes a single catastrophic game far
more than it rewards a few Elo of mean strength. This reads the per-game
records a timed ``tools.arena`` match writes (with the clock summaries the
referee now traces) and reports the components separately, without inventing
a single "Swiss score":

* result and Elo with the paired cluster bootstrap and the informative-cluster
  count, exactly as every Gate 2 here reports them;
* failure terminations attributable to the agent: flag, crash, illegal, init;
* clock safety: the lowest clock the agent ever held, how many games dipped
  under 5 s and 10 s, the largest single think;
* the same for the opponent, so a comparison is symmetric;
* conversion: games the agent won by checkmate versus drew by repetition or
  adjudication, and the mean game length;
* population sensitivity: score as White and as Black, and by opening phase
  of the start position when the suite carries one.

    uv run python -m tools.daily.swissrisk --games corpus/daily/time/games/sf60_vs_ratedv1.jsonl --out corpus/daily/time/swissrisk_sf60.txt
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def elo(score: float) -> float:
    score = min(max(score, 1e-9), 1 - 1e-9)
    return -400.0 * math.log10(1.0 / score - 1.0)


def bootstrap(by_cluster: dict[int, list[float]], n: int = 20000, seed: int = 20260905) -> tuple[float, float]:
    keys = list(by_cluster)
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        vals: list[float] = []
        for _ in keys:
            vals += by_cluster[rng.choice(keys)]
        out.append(sum(vals) / len(vals))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n)]


def clock_block(name: str, games: list[dict], key: str) -> list[str]:
    mins = [g[key]["min_clock_ms"] for g in games if g.get(key) and g[key]["min_clock_ms"] is not None]
    maxs = [g[key]["max_spend_ms"] for g in games if g.get(key) and g[key]["max_spend_ms"] is not None]
    means = [g[key]["mean_spend_ms"] for g in games if g.get(key) and g[key]["mean_spend_ms"] is not None]
    finals = [g[key]["final_clock_ms"] for g in games if g.get(key) and g[key]["final_clock_ms"] is not None]
    if not mins:
        return [f"   {name}: no clock trace in these records"]
    return [
        f"   {name}: lowest clock ever held {min(mins) / 1000:.1f} s; games under 5 s: {sum(m < 5000 for m in mins)}, "
        f"under 10 s: {sum(m < 10000 for m in mins)}, under 20 s: {sum(m < 20000 for m in mins)}",
        f"   {name}: largest single think {max(maxs) / 1000:.1f} s; mean think {statistics.mean(means) / 1000:.2f} s; "
        f"median final clock {statistics.median(finals) / 1000:.1f} s",
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()

    header = None
    games = []
    for line in a.games.open(encoding="utf-8"):
        r = json.loads(line)
        if r.get("record") == "match_header":
            header = r
        elif r.get("record") == "game":
            games.append(r)
    if not games:
        raise SystemExit("no game records")

    by: dict[int, list[float]] = defaultdict(list)
    for g in games:
        by[g["cluster"]].append(g["agent_score"])
    scores = [g["agent_score"] for g in games]
    score = sum(scores) / len(scores)
    informative = [c for c, v in by.items() if sum(v) / len(v) != 0.5]
    lo, hi = bootstrap(by)
    loo = [elo(score)]
    if len(by) > 1:
        loo = []
        for c in by:
            vv = [x for k, v in by.items() if k != c for x in v]
            loo.append(elo(sum(vv) / len(vv)))

    lines = ["== SWISS RISK REPORT =="]
    if header:
        lines.append(f"{header['agent']} (snapshot {header['agent_snapshot']}) vs {header['opponent']} "
                     f"(snapshot {header['opponent_snapshot']}); {header['base_ms']} ms + {header['increment_ms']} ms; "
                     f"ply cap {header['ply_cap']}; draw claim {header['draw_claim']}; corpus {header.get('corpus_file')}")
    lines.append("")
    lines.append("-- strength (the usual Gate 2 numbers) --")
    lines.append(f"   games {len(games)}   clusters {len(by)}   informative clusters {len(informative)} ({len(informative) / len(by):.0%})")
    lines.append(f"   +{scores.count(1.0)} ={scores.count(0.5)} -{scores.count(0.0)}   score {score:.1%}   nominal Elo {elo(score):+.1f}")
    lines.append(f"   cluster bootstrap 95%: score {lo:.1%}..{hi:.1%}, Elo {elo(lo):+.1f}..{elo(hi):+.1f}")
    lines.append(f"   leave-one-cluster-out Elo {min(loo):+.1f}..{max(loo):+.1f}")
    hist = Counter(sum(v) / len(v) for v in by.values())
    lines.append(f"   cluster-mean histogram {dict(sorted(hist.items()))}")
    lines.append("")
    lines.append("-- failures attributable to each side --")
    agent_fail = Counter(g["termination"] for g in games if g["failed"] and g["agent_score"] == 0.0)
    opp_fail = Counter(g["termination"] for g in games if g["failed"] and g["agent_score"] == 1.0)
    lines.append(f"   agent: {dict(agent_fail) or 'none'}")
    lines.append(f"   opponent: {dict(opp_fail) or 'none'}")
    lines.append("")
    lines.append("-- clock safety --")
    lines += clock_block("agent", games, "agent_clock")
    lines += clock_block("opponent", games, "opponent_clock")
    lines.append("")
    lines.append("-- terminations and conversion --")
    term = Counter(g["termination"] for g in games)
    lines.append(f"   all terminations: {dict(term)}")
    won = Counter(g["termination"] for g in games if g["agent_score"] == 1.0)
    drew = Counter(g["termination"] for g in games if g["agent_score"] == 0.5)
    lost = Counter(g["termination"] for g in games if g["agent_score"] == 0.0)
    lines.append(f"   agent wins by: {dict(won) or 'none'}")
    lines.append(f"   draws by: {dict(drew) or 'none'}")
    lines.append(f"   agent losses by: {dict(lost) or 'none'}")
    plies = [g["plies"] for g in games]
    lines.append(f"   mean plies {statistics.mean(plies):.0f}, max {max(plies)}, games at the ply cap: {sum(g['termination'] == 'adjudication' for g in games)}")
    lines.append("")
    lines.append("-- population sensitivity --")
    for label, sel in (("agent as White", [g for g in games if g["agent_is_white"]]),
                       ("agent as Black", [g for g in games if not g["agent_is_white"]])):
        s = [g["agent_score"] for g in sel]
        if s:
            lines.append(f"   {label}: +{s.count(1.0)} ={s.count(0.5)} -{s.count(0.0)}  score {sum(s) / len(s):.1%}  Elo {elo(sum(s) / len(s)):+.1f}")
    lines.append("")
    lines.append("No single Swiss score is computed. Read the components: a candidate that gains Elo but adds a flag,")
    lines.append("a crash or a drop in the lowest clock has not earned a place in a 13-round locked-build Swiss.")
    text = "\n".join(lines)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
