"""Gate 1 for the low-material term: rerun every audited position with the actual candidate engine.

Reads the two audit files (the reference families and the six siblings),
asks the candidate for its static and depth-6 root on each position, and
reports per family and overall: false wins removed (draws V2.1 scored >=
+150 that the candidate scores under +150), genuine wins under +100 and
under +200, strategic wins under +100, losses the minor side still reads
above -100, and the mean drawn root. Columns for V2.1 come from the audit
files themselves.

    uv run python -m tools.v2.lowmat_gate --engine champions/v2_2a_low_material --out corpus/v2/fw/lowmat/03_gate1_rerun.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

from tools.postmortem.play import Engine

AUDIT_FILES = ("corpus/v2/fw/krminor/01_report.jsonl", "corpus/v2/fw/lowmat/01_report.jsonl")
ORDER = ("KRB-KR", "KRN-KR", "KR-KB", "KR-KN", "KB-KP", "KN-KP", "KB-KPP", "KN-KPP")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    rows = []
    for path in AUDIT_FILES:
        with Path(path).open(encoding="utf-8") as fh:
            rows.extend(json.loads(line) for line in fh)
    engine = Engine(arguments.engine, arguments.depth)
    try:
        for i, r in enumerate(rows, start=1):
            white_to_move = r["fen"].split()[1] == "w"
            sign = 1 if white_to_move == r["strong_white"] else -1
            engine.ask("new")
            g = engine.ask(f"go {r['fen']}")
            r["cand_root"] = sign * g["score"]
            r["cand_static"] = g["static"] if r["strong_white"] else -g["static"]
            if i % 100 == 0:
                print(f"  {i}/{len(rows)}", flush=True)
    finally:
        engine.close()
    lines = [f"== GATE 1 RERUN: {len(rows)} audited positions, {arguments.engine} at depth {arguments.depth}, against V2.1's recorded scores ==",
             "strong side's view; false win = draw with V2.1 depth-6 root >= +150; 'removed' = candidate root < +150", ""]
    lines.append(f"   {'family':<8} {'draws':>5} {'FW':>4} {'removed':>8} {'draw d6 V2.1':>12} {'cand':>6} {'wins':>4} {'<100':>5} {'<200':>5} {'strat':>5} {'strat<100':>9} {'losses':>6} {'>-100 V2.1':>10} {'cand':>5}")
    totals = defaultdict(int)
    by = defaultdict(list)
    for r in rows:
        by[r["family"]].append(r)
    for fam in ORDER:
        rs = by.get(fam, [])
        if not rs:
            continue
        draws = [r for r in rs if r["label"] == "draw"]
        fw = [r for r in draws if r["false_win"]]
        wins = [r for r in rs if r["label"] == "win"]
        strat = [r for r in wins if not r["tactical"]]
        losses = [r for r in rs if r["label"] == "loss"]
        removed = sum(r["cand_root"] < 150 for r in fw)
        w100 = sum(r["cand_root"] < 100 for r in wins)
        w200 = sum(r["cand_root"] < 200 for r in wins)
        s100 = sum(r["cand_root"] < 100 for r in strat)
        l_v21 = sum(r["v21_d6"] > -100 for r in losses)
        l_cand = sum(r["cand_root"] > -100 for r in losses)
        for k, v in (("draws", len(draws)), ("fw", len(fw)), ("removed", removed), ("wins", len(wins)), ("w100", w100), ("w200", w200), ("strat", len(strat)), ("s100", s100), ("losses", len(losses)), ("l_v21", l_v21), ("l_cand", l_cand)):
            totals[k] += v
        lines.append(f"   {fam:<8} {len(draws):>5} {len(fw):>4} {removed:>4}/{len(fw):<3} {statistics.mean(r['v21_d6'] for r in draws) if draws else 0:>+12.0f} {statistics.mean(r['cand_root'] for r in draws) if draws else 0:>+6.0f} {len(wins):>4} {w100:>5} {w200:>5} {len(strat):>5} {s100:>9} {len(losses):>6} {l_v21:>10} {l_cand:>5}")
    lines.append(f"   {'ALL':<8} {totals['draws']:>5} {totals['fw']:>4} {totals['removed']:>4}/{totals['fw']:<3} {'':>12} {'':>6} {totals['wins']:>4} {totals['w100']:>5} {totals['w200']:>5} {totals['strat']:>5} {totals['s100']:>9} {totals['losses']:>6} {totals['l_v21']:>10} {totals['l_cand']:>5}")
    lines.append("")
    verdict = totals["removed"] >= 400 and totals["w100"] == 0 and totals["s100"] == 0
    lines.append(f"targets: false wins removed >= 400/429 -> {totals['removed']}/{totals['fw']}; wins under +100 = 0 -> {totals['w100']}; strategic wins under +100 = 0 -> {totals['s100']}; VERDICT {'PASS' if verdict else 'FAIL'}")
    lines.append("")
    lines.append("wins the candidate scores under +200 (all tactical unless marked):")
    for r in sorted((r for r in rows if r["label"] == "win" and r["cand_root"] < 200), key=lambda r: r["cand_root"]):
        lines.append(f"   {r['family']:<8} {'STRATEGIC' if not r['tactical'] else 'tactical':<9} SF {r['sf_strong']:>+5} mate {r['sf_mate_strong']}  V2.1 d6 {r['v21_d6']:>+5}  cand d6 {r['cand_root']:>+5}  {r['fen']}")
    lines.append("")
    lines.append("false wins the candidate leaves at or above +150:")
    for r in sorted((r for r in rows if r["false_win"] and r["cand_root"] >= 150), key=lambda r: -r["cand_root"]):
        lines.append(f"   {r['family']:<8} SF {r['sf_strong']:>+4}  V2.1 d6 {r['v21_d6']:>+5}  cand static {r['cand_static']:>+5} d6 {r['cand_root']:>+5}  {r['fen']}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
