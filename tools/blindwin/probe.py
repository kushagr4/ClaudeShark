"""Search probe on blind episodes: static, quiescence, root, and pruning counters.

Every blind episode position and a matched control set of *seen* winning
positions (same Stockfish band, root >= +300) are given to the instrumented
production engine. Three numbers per position -- the static, the root
quiescence score, and the depth-6 root score -- say where the win goes
missing: if quiescence already lifts a low static, the tactical layer sees
it; if the root does, the search does; if none of them do, nothing in the
engine can. Pruning counters per node are compared across the two sets so a
search-side cause would show as a difference the evaluation cannot explain.

    uv run python -m tools.blindwin.probe --engine <instrumented dir> --episodes ... --games ... --out ...
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from tools.postmortem.play import Engine

COUNTERS = ("nodes", "qnodes", "researches", "c_null_tries", "c_null_cuts", "c_lmr_reduced",
            "c_lmr_research", "c_delta_pruned", "c_see_pruned", "tt_hits", "tt_probes")


def own(m: dict) -> int:
    return m["sf_cp_white_before"] if m["turn"] == "w" else -m["sf_cp_white_before"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--games", type=Path, nargs="+", required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    episodes = [json.loads(line) for line in arguments.episodes.open(encoding="utf-8")]
    seen = []
    for path in arguments.games:
        for g in (json.loads(line) for line in path.open(encoding="utf-8")):
            for m in g["moves"]:
                if m["mover"] == "base" and 300 <= own(m) < 9000 and m["score_stm"] >= 300:
                    seen.append(m["fen"])
    rng = random.Random(11)
    control = rng.sample(seen, min(len(episodes), len(seen)))

    engine = Engine(arguments.engine, arguments.depth)
    rows: dict[str, list[dict]] = {"blind": [], "seen": []}
    try:
        for label, fens in (("blind", [e["fen"] for e in episodes]), ("seen", control)):
            for fen in fens:
                engine.ask("new")
                q = engine.ask(f"qs {fen}")
                r = engine.ask(f"go {fen}")
                white = fen.split()[1] == "w"
                sign = 1 if white else -1
                rows[label].append({"fen": fen, "static": sign * r["static"], "qs": sign * q["qs"],
                                    "root": r["score"], **{k: r.get(k, 0) for k in COUNTERS}})
    finally:
        engine.close()

    for e, r in zip(episodes, rows["blind"], strict=True):
        r["mechanism"] = e["mechanism"]
        r["hb"] = e["horizon_or_blind"].split(" ")[0]
        r["sf"] = e["sf_cp_1m"]

    lines = [f"== SEARCH PROBE: {len(rows['blind'])} blind episodes vs {len(rows['seen'])} seen winning positions (production, depth {arguments.depth}) ==", ""]
    lines.append("where the win goes missing (blind episodes): mean static -> quiescence -> root, against Stockfish")
    b = rows["blind"]
    lines.append(f"  static {statistics.mean(r['static'] for r in b):+.0f}   qsearch {statistics.mean(r['qs'] for r in b):+.0f}   root {statistics.mean(r['root'] for r in b):+.0f}   Stockfish {statistics.mean(min(r['sf'], 2000) for r in b):+.0f}")
    lines.append(f"  quiescence lifts the static by >= 100 in {sum(r['qs'] - r['static'] >= 100 for r in b)}/{len(b)}; the root lifts quiescence by >= 100 in {sum(r['root'] - r['qs'] >= 100 for r in b)}/{len(b)}")
    lines.append(f"  static < 0 in {sum(r['static'] < 0 for r in b)}/{len(b)}; root < 0 in {sum(r['root'] < 0 for r in b)}/{len(b)}")
    lines.append("")
    lines.append("by mechanism (blind episodes):")
    lines.append(f"  {'mechanism':<22} {'n':>3} {'static':>7} {'qs':>7} {'root':>7} {'SF':>7}")
    by = defaultdict(list)
    for r in b:
        by[r["mechanism"]].append(r)
    for k, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"  {k:<22} {len(rs):>3} {statistics.mean(r['static'] for r in rs):>+7.0f} {statistics.mean(r['qs'] for r in rs):>+7.0f} {statistics.mean(r['root'] for r in rs):>+7.0f} {statistics.mean(min(r['sf'], 2000) for r in rs):>+7.0f}")
    lines.append("")
    lines.append("pruning per node, blind vs seen (a search-side cause would show here):")
    lines.append(f"  {'metric':<28} {'blind':>10} {'seen':>10} {'ratio':>7}")

    def rate(rs, key, per=None):
        return statistics.mean(r[key] / max(1, r[per]) if per else r[key] for r in rs)

    for key, per in (("nodes", None), ("qnodes", "nodes"), ("researches", None), ("c_null_tries", "nodes"),
                     ("c_null_cuts", "c_null_tries"), ("c_lmr_reduced", "nodes"), ("c_lmr_research", "c_lmr_reduced"),
                     ("c_delta_pruned", "qnodes"), ("c_see_pruned", "qnodes"), ("tt_hits", "tt_probes")):
        x, y = rate(rows["blind"], key, per), rate(rows["seen"], key, per)
        lines.append(f"  {key + ('/' + per if per else ''):<28} {x:>10.4f} {y:>10.4f} {(x / y if y else float('nan')):>7.2f}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
