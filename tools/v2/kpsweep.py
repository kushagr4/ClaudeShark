"""Choose the king-to-pawn table once, from three predefined families, on diagnostic halves only.

For each family a scratch engine is built with the term on and that table,
and run on the diagnostic rows of the V2 calibration set (static, root
quiescence, depth-6 root, oracle loss of the chosen move) and on the
diagnostic half of the blind-win suite. The validation halves are never
read here. Selection follows the brief's priority: blind-win error down,
false-win error down, recognised draws stable, recognised wins stable,
depth-6 move quality, cost; a family that improves one failure class at
the expense of the other, or that rescales every endgame, is out.

    uv run python -m tools.v2.kpsweep --scratch <dir> --out corpus/v2/kp/02_sweep.txt
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_FILES = ("agent.py", "cs_constants.py", "cs_drawish.py", "cs_eval.py", "cs_king.py", "cs_kingpawn.py", "cs_mopup.py",
                "cs_passed.py", "cs_ordering.py", "cs_search.py", "cs_see.py", "cs_terms.py", "cs_time.py", "cs_tt.py")

# Fixed before any of it was run. Index = Chebyshev distance 1..7; zero beyond four.
FAMILY: dict[str, tuple[int, ...]] = {
    "off": (0, 0, 0, 0, 0, 0, 0, 0),
    "SMALL": (0, 24, 18, 12, 6, 0, 0, 0),
    "MEDIUM": (0, 48, 36, 24, 12, 0, 0, 0),
    "LARGE": (0, 80, 60, 40, 20, 0, 0, 0),
}
CLASSES = ("blind_win", "false_win", "recognised_win", "recognised_draw", "losing", "control_middle", "control_tactic")


def build_variant(table: tuple[int, ...], where: Path, on: bool) -> Path:
    where.mkdir(parents=True, exist_ok=True)
    for name in ENGINE_FILES:
        shutil.copy2(ROOT / name, where / name)
    m = where / "cs_kingpawn.py"
    src = m.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    hit = [i for i, line in enumerate(lines) if line.startswith("KING_PAWN_EG = ")]
    assert len(hit) == 1
    lines[hit[0]] = f"KING_PAWN_EG = {table}\n"
    m.write_text("".join(lines), encoding="utf-8")
    if on:
        t = where / "cs_terms.py"
        src = t.read_text(encoding="utf-8")
        assert '"king_pawn": False,' in src
        t.write_text(src.replace('"king_pawn": False,', '"king_pawn": True,', 1), encoding="utf-8")
    return where


def clamp(v: int) -> int:
    return min(max(v, -2000), 2000)


def run_variant(name: str, arguments: argparse.Namespace) -> dict:
    engine = build_variant(FAMILY[name], arguments.scratch / f"kp_{name}", on=name != "off")
    out_dir = arguments.out.parent
    cal = out_dir / f"sweep_{name}_calibration.txt"
    subprocess.run([sys.executable, "-m", "tools.v2.suite", "--suite", str(arguments.suite), "--engine", str(engine),
                    "--depth", str(arguments.depth), "--role", "diagnostic", "--out", str(cal)],
                   check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
    bw = out_dir / f"sweep_{name}_blindwin.txt"
    subprocess.run([sys.executable, "-m", "tools.blindwin.run", "--suite", str(arguments.blindwin), "--engine", str(engine),
                    "--depth", str(arguments.depth), "--role", "diagnostic", "--out", str(bw)],
                   check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
    return {"name": name, "table": FAMILY[name],
            "calibration": [json.loads(line) for line in cal.with_suffix(".jsonl").open(encoding="utf-8")],
            "blindwin": [json.loads(line) for line in bw.with_suffix(".jsonl").open(encoding="utf-8")]}


def by_traj(rows: list[dict], key) -> float:
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["trajectory"], []).append(key(r))
    return statistics.mean(statistics.mean(g) for g in groups.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--suite", type=Path, default=Path("corpus/v2/endgame_calibration_v1.jsonl"))
    parser.add_argument("--blindwin", type=Path, default=Path("corpus/blindwin_regression_v1.jsonl"))
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--members", default=",".join(FAMILY))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    names = [n for n in arguments.members.split(",") if n]
    with ThreadPoolExecutor(max_workers=arguments.workers) as pool:
        variants = list(pool.map(lambda n: run_variant(n, arguments), names))

    lines = [f"== KING-TO-PAWN TABLE SWEEP on the DIAGNOSTIC halves (depth {arguments.depth}); validation halves not read ==",
             "families fixed in advance. SF clamped +-2000. MAE = mean |x - SF|; 'below' = mean(SF - x) on blind wins; 'above' = mean(x - SF) on false wins;",
             "'traj' figures weight each source game equally. loss = oracle cp given up by the depth-6 move, winsorised at 500.", ""]
    summary = []
    for v in variants:
        rows = v["calibration"]
        rec = {"name": v["name"], "table": v["table"]}
        block = [f"-- {v['name']}  table {v['table']}"]
        block.append(f"   {'class':<16} {'n':>3} {'traj':>4} | {'static MAE':>10} {'qs MAE':>7} {'root MAE':>8} | {'static':>7} {'qs':>7} {'root':>7} | {'loss':>5} {'serious':>7} {'agree':>6} | extra")
        for cls in CLASSES:
            rs = [r for r in rows if r["class"] == cls]
            if not rs:
                continue
            sf = [clamp(r["sf_cp"]) for r in rs]
            maes = {c: statistics.mean(abs(r[c] - s) for r, s in zip(rs, sf, strict=True)) for c in ("static", "qs", "root")}
            means = {c: statistics.mean(r[c] for r in rs) for c in ("static", "qs", "root")}
            loss = statistics.mean(min(r["loss"], 500) for r in rs)
            serious = sum(r["loss"] >= 100 for r in rs) / len(rs)
            agree = sum(r["move"] == r["sf_best"] for r in rs) / len(rs)
            extra = ""
            if cls == "blind_win":
                extra = f"below(static/qs/root) {statistics.mean(s - r['static'] for r, s in zip(rs, sf, strict=True)):+.0f}/{statistics.mean(s - r['qs'] for r, s in zip(rs, sf, strict=True)):+.0f}/{statistics.mean(s - r['root'] for r, s in zip(rs, sf, strict=True)):+.0f}; root<100 {sum(r['root'] < 100 for r in rs)}/{len(rs)}; by traj below(static) {by_traj(rs, lambda r: clamp(r['sf_cp']) - r['static']):+.0f}"
            elif cls == "false_win":
                extra = f"above(static/qs/root) {statistics.mean(r['static'] - s for r, s in zip(rs, sf, strict=True)):+.0f}/{statistics.mean(r['qs'] - s for r, s in zip(rs, sf, strict=True)):+.0f}/{statistics.mean(r['root'] - s for r, s in zip(rs, sf, strict=True)):+.0f}; root>=200 {sum(r['root'] >= 200 for r in rs)}/{len(rs)}; by traj above(static) {by_traj(rs, lambda r: r['static'] - clamp(r['sf_cp'])):+.0f}"
            elif cls == "recognised_draw":
                extra = f"static inflation >= +150: {sum(r['static'] >= 150 for r in rs)}; root >= +150: {sum(r['root'] >= 150 for r in rs)}"
            elif cls == "recognised_win":
                extra = f"root deflated below +200: {sum(r['root'] < 200 for r in rs)}"
            elif cls == "losing":
                extra = f"root above -100 (distortion): {sum(r['root'] > -100 for r in rs)}"
            rec[cls] = {"n": len(rs), "mae": maes, "mean": means, "loss": loss, "serious": serious, "agree": agree}
            block.append(f"   {cls:<16} {len(rs):>3} {len({r['trajectory'] for r in rs}):>4} | {maes['static']:>10.0f} {maes['qs']:>7.0f} {maes['root']:>8.0f} | {means['static']:>+7.0f} {means['qs']:>+7.0f} {means['root']:>+7.0f} | {loss:>5.0f} {serious:>7.0%} {agree:>6.0%} | {extra}")
        bw = v["blindwin"]
        rec["blindwin_suite"] = {"robust": statistics.mean(min(r["loss"], 500) for r in bw), "serious": sum(r["loss"] >= 100 for r in bw) / len(bw),
                                 "root_under_100": sum(r["root"] < 100 for r in bw), "n": len(bw)}
        block.append(f"   blind-win suite diagnostic: {len(bw)} rows, robust loss {rec['blindwin_suite']['robust']:.1f}, serious {rec['blindwin_suite']['serious']:.0%}, root<100 {rec['blindwin_suite']['root_under_100']}/{len(bw)}")
        lines.extend(block)
        lines.append("")
        summary.append(rec)
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
