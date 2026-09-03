"""Compare two root-suite analyses position by position: what changed, and how it scored.

Gate 1's root suite is reported as aggregate move quality; this puts the two
runs side by side so a change can be attributed. It lists every position
whose move differs, with the loss under each engine, and splits the
aggregate by phase and by whether the side to move has a passed pawn, which
is the only place the passed-pawn term can act.

    uv run python -m tools.passed.compare_root --base corpus/analysis_cl_v1_d6.jsonl --cand corpus/passed/analysis_cl_v1_d6_passed.jsonl --out <txt>
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

import chess

from cs_passed import passed_pawn_mask


def load(path: Path) -> tuple[dict, dict[str, dict]]:
    rows = [json.loads(line) for line in path.open(encoding="utf-8")]
    return rows[0], {r["fen"]: r for r in rows[1:]}


def robust(rs: list[dict]) -> float:
    return statistics.mean(min(r["cp_loss"], 500) for r in rs) if rs else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--cand", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    bh, base = load(arguments.base)
    ch, cand = load(arguments.cand)
    assert set(base) == set(cand), "the two analyses cover different positions"
    fens = sorted(base, key=lambda f: base[f]["id"])

    def group_key(fen: str) -> tuple[str, str]:
        board = chess.Board(fen)
        mover_has = passed_pawn_mask(board, board.turn) != 0
        other_has = passed_pawn_mask(board, not board.turn) != 0
        return base[fen]["structure"]["phase"], ("mover has passer" if mover_has else "other has passer" if other_has else "no passers")

    lines = [f"== ROOT SUITE COMPARISON: {arguments.base.name} (base, {bh.get('engine')}) vs {arguments.cand.name} (cand, {ch.get('engine')}) ==",
             f"suite {bh.get('suite_hash')} / {ch.get('suite_hash')}, depth {bh.get('depth')} / {ch.get('depth')}, {len(fens)} positions", ""]
    changed = [f for f in fens if base[f]["engine"]["move"] != cand[f]["engine"]["move"]]
    lines.append(f"moves changed: {len(changed)} of {len(fens)}")
    for name, rows in (("base", base), ("cand", cand)):
        rs = list(rows.values())
        lines.append(f"  {name}: agree {sum(r['agree'] for r in rs) / len(rs):.1%}  within 25 {sum(r['within_25'] for r in rs) / len(rs):.1%}  "
                     f"robust {robust(rs):.1f}  serious {sum(r['serious'] for r in rs) / len(rs):.1%}  catastrophic {sum(r['catastrophic'] for r in rs) / len(rs):.1%}  "
                     f"nodes {sum(r['engine']['nodes'] for r in rs):,}")
    lines.append("")
    lines.append("by phase and passer presence at the root (n, base robust -> cand robust, base serious -> cand serious, moves changed):")
    by: dict[tuple[str, str], list[str]] = defaultdict(list)
    for f in fens:
        by[group_key(f)].append(f)
    for key, fs in sorted(by.items()):
        b = [base[f] for f in fs]
        c = [cand[f] for f in fs]
        lines.append(f"  {key[0]:<11} {key[1]:<17} n {len(fs):>3}  robust {robust(b):>6.1f} -> {robust(c):>6.1f}  "
                     f"serious {sum(r['serious'] for r in b) / len(b):>5.1%} -> {sum(r['serious'] for r in c) / len(c):>5.1%}  "
                     f"changed {sum(1 for f in fs if f in changed):>2}")
    lines.append("")
    lines.append("changed positions (loss under base -> cand; negative delta = candidate better):")
    deltas = []
    for f in changed:
        b, c = base[f], cand[f]
        d = min(c["cp_loss"], 500) - min(b["cp_loss"], 500)
        deltas.append(d)
        lines.append(f"  {b['id']:<7} {b['structure']['phase']:<11} {b['engine']['move']:<6} {b['cp_loss']:>5} -> {c['engine']['move']:<6} {c['cp_loss']:>5}  delta {d:>+5}  root {b['engine']['score']:>+5} -> {c['engine']['score']:>+5}  {f}")
    if deltas:
        lines.append(f"  net over changed positions: {sum(deltas):+} cp (mean {statistics.mean(deltas):+.1f}); better {sum(d < 0 for d in deltas)}, worse {sum(d > 0 for d in deltas)}, same {sum(d == 0 for d in deltas)}")
    text = "\n".join(lines)
    print(text)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
