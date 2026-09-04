"""Static versus search on the false-win corpus: does the wrong confidence start at evaluation or grow with depth?

For every row V2.1 is asked for its static, root quiescence and the root
at depths 4, 6 and 8; one row per trajectory (the highest depth-6 root) is
also searched to depth 10. Rated V1 is asked at depth 8 for the residual
comparison. Each trajectory is then classified:

    STATIC          the static already stands >= +150 above Stockfish
    SEARCH-INFLATED the static is under +150 and the deeper roots climb
    SEARCH-CORRECTABLE the root at the deepest depth searched falls under +100
    MIXED           anything else

    uv run python -m tools.v2.fwladder --corpus corpus/v2/fw/falsewin_corpus_v1.jsonl --out corpus/v2/fw/02_ladder.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from tools.postmortem.play import Engine


def classify(row: dict, deepest_key: str) -> str:
    static = row["v21_static"]
    roots = [row["v21_root_d4"], row["v21_root_d6"], row["v21_root_d8"]]
    if row.get("v21_root_d10") is not None:
        roots.append(row["v21_root_d10"])
    if roots[-1] < 100:
        return "SEARCH-CORRECTABLE"
    if static >= 150:
        return "STATIC"
    if roots[-1] >= static + 100:
        return "SEARCH-INFLATED"
    return "MIXED"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--depth10", action="store_true", help="also search one row per trajectory to depth 10")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    rows = [json.loads(line) for line in arguments.corpus.open(encoding="utf-8")][1:]
    representative = {}
    for r in sorted(rows, key=lambda r: -r["v21_root"]):
        representative.setdefault(r["trajectory"], r["id"])
    engines = {d: Engine(Path("champions/v2_1_kingpawn"), d) for d in (4, 6, 8, 10)}
    v1_8 = Engine(Path("champions/rated_v1"), 8)
    try:
        for i, r in enumerate(rows, start=1):
            for d in (4, 6, 8):
                engines[d].ask("new")
                r[f"v21_root_d{d}"] = engines[d].ask(f"go {r['fen']}")["score"]
            v1_8.ask("new")
            r["v1_root_d8"] = v1_8.ask(f"go {r['fen']}")["score"]
            if arguments.depth10 and representative[r["trajectory"]] == r["id"]:
                engines[10].ask("new")
                g = engines[10].ask(f"go {r['fen']}")
                r["v21_root_d10"] = g["score"]
                r["v21_nodes_d10"] = g["nodes"]
            print(f"  [{i}/{len(rows)}] {r['id']} static {r['v21_static']:+} d4 {r['v21_root_d4']:+} d6 {r['v21_root_d6']:+} d8 {r['v21_root_d8']:+} d10 {r.get('v21_root_d10', '-')}", flush=True)
    finally:
        for e in engines.values():
            e.close()
        v1_8.close()
    for r in rows:
        r["ladder_class"] = classify(r, "v21_root_d10")
    by_traj: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_traj[r["trajectory"]].append(r)
    traj_class = {t: Counter(r["ladder_class"] for r in rs).most_common(1)[0][0] for t, rs in by_traj.items()}
    lines = [f"== STATIC VS SEARCH on the false-win corpus: {len(rows)} rows, {len(by_traj)} trajectories (V2.1; rated V1 at depth 8 for comparison) ==", "",
             f"means: SF {statistics.mean(r['sf_cp'] for r in rows):+.0f}  V2.1 static {statistics.mean(r['v21_static'] for r in rows):+.0f}  qs {statistics.mean(r['v21_qs'] for r in rows):+.0f}  "
             f"d4 {statistics.mean(r['v21_root_d4'] for r in rows):+.0f}  d6 {statistics.mean(r['v21_root_d6'] for r in rows):+.0f}  d8 {statistics.mean(r['v21_root_d8'] for r in rows):+.0f}  "
             f"d10 {statistics.mean(r['v21_root_d10'] for r in rows if r.get('v21_root_d10') is not None):+.0f} ({sum(1 for r in rows if r.get('v21_root_d10') is not None)} rows)  | V1 d8 {statistics.mean(r['v1_root_d8'] for r in rows):+.0f}",
             f"classification by trajectory: {dict(Counter(traj_class.values()))}", f"classification by row: {dict(Counter(r['ladder_class'] for r in rows))}", ""]
    lines.append(f"{'id':<7} {'traj':<26} {'sig':<14} {'SF':>4} {'static':>7} {'qs':>6} {'d4':>6} {'d6':>6} {'d8':>6} {'d10':>6} {'V1 d8':>6} {'class':<18}")
    for r in sorted(rows, key=lambda r: (r["ladder_class"], -r["v21_root_d8"])):
        d10 = f"{r['v21_root_d10']:+6}" if r.get("v21_root_d10") is not None else "     -"
        lines.append(f"{r['id']:<7} {r['trajectory']:<26} {r['signature']:<14} {r['sf_cp']:>+4} {r['v21_static']:>+7} {r['v21_qs']:>+6} {r['v21_root_d4']:>+6} {r['v21_root_d6']:>+6} {r['v21_root_d8']:>+6} {d10} {r['v1_root_d8']:>+6} {r['ladder_class']:<18}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
