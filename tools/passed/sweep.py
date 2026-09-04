"""Choose the passed-pawn tables once, from a predefined family, on the diagnostic half only.

Each member of the family is a pair of monotonic rank curves. For each one a
scratch copy of the engine is built with the flag on and those tables, and
run at fixed depth on the *diagnostic* rows of the blind-win regression
suite. Two things are measured:

* move quality -- Stockfish loss of the chosen move, by row and with each
  source-game cluster weighted equally;
* the static gap at the end of Stockfish's own line -- the number the audit
  found, recomputed with the candidate's static, so the report can say how
  much of the missing information the term supplies before any search.

The validation half is never read here. Selection is by cluster-weighted
robust loss on the diagnostic half, with the smaller table preferred when
two are within a few centipawns of each other.

    uv run python -m tools.passed.sweep --scratch <dir> --out corpus/passed/02_sweep.txt
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

import chess

from tools.postmortem.play import Engine

ROOT = Path(__file__).resolve().parents[2]
ENGINE_FILES = ("agent.py", "cs_constants.py", "cs_eval.py", "cs_king.py", "cs_kingpawn.py", "cs_mopup.py", "cs_passed.py",
                "cs_ordering.py", "cs_search.py", "cs_see.py", "cs_terms.py", "cs_time.py", "cs_tt.py")

# The whole family, fixed before any of it was run. Index = relative rank.
FAMILY: dict[str, tuple[tuple[int, ...], tuple[int, ...]]] = {
    "off": ((0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
    "A_small": ((0, 0, 2, 4, 8, 16, 28, 0), (0, 4, 8, 16, 32, 56, 88, 0)),
    "B_medium": ((0, 0, 4, 8, 14, 26, 44, 0), (0, 6, 12, 24, 48, 84, 132, 0)),
    "C_large": ((0, 0, 6, 12, 20, 36, 60, 0), (0, 8, 16, 32, 64, 112, 176, 0)),
    "L_linear": ((0, 0, 5, 10, 15, 20, 25, 0), (0, 15, 30, 45, 60, 75, 90, 0)),
}


def build_variant(mg: tuple[int, ...], eg: tuple[int, ...], where: Path, flag_on: bool = True) -> Path:
    where.mkdir(parents=True, exist_ok=True)
    for name in ENGINE_FILES:
        shutil.copy2(ROOT / name, where / name)
    module = where / "cs_passed.py"
    src = module.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    replaced = 0
    for i, line in enumerate(lines):
        if line.startswith("PASSED_MG = "):
            lines[i] = f"PASSED_MG = {mg}\n"
            replaced += 1
        elif line.startswith("PASSED_EG = "):
            lines[i] = f"PASSED_EG = {eg}\n"
            replaced += 1
    assert replaced == 2, "table lines not found"
    module.write_text("".join(lines), encoding="utf-8")
    if flag_on:
        e = where / "cs_terms.py"
        src = e.read_text(encoding="utf-8")
        old = '"passed": False,'
        assert old in src
        e.write_text(src.replace(old, '"passed": True,', 1), encoding="utf-8")
    return where


def pv_end(fen: str, pv: list[str]) -> str:
    board = chess.Board(fen)
    for uci in pv:
        board.push_uci(uci)
    return board.fen()


def static_gap(engine_dir: Path, rows: list[dict]) -> list[dict]:
    """Candidate static at the end of Stockfish's line, from the episode mover's side."""
    engine = Engine(engine_dir, 1)
    out = []
    try:
        for r in rows:
            end = pv_end(r["fen"], r["pv"])
            white_at_start = r["fen"].split()[1] == "w"
            white_at_end = end.split()[1] == "w"
            s = engine.ask(f"static {end}")["static"]  # white's view
            mine = s if white_at_start else -s
            r0 = engine.ask(f"static {r['fen']}")["static"]
            out.append({"id": r["id"], "cluster": r["cluster"], "end_fen": end, "static_at_pv_end": mine,
                        "static_at_root": r0 if white_at_start else -r0,
                        "sf_at_pv_end": r["sf_at_pv_end"], "gap": min(r["sf_at_pv_end"], 2000) - mine,
                        "gap_at_build": min(r["sf_at_pv_end"], 2000) - r["static_at_pv_end"],
                        "end_turn_white": white_at_end})
    finally:
        engine.close()
    return out


def run_variant(name: str, tables: tuple[tuple[int, ...], tuple[int, ...]], arguments: argparse.Namespace) -> dict:
    engine = build_variant(tables[0], tables[1], arguments.scratch / f"passed_{name}", flag_on=name != "off")
    out = arguments.out.parent / f"sweep_{name}.txt"
    subprocess.run([sys.executable, "-m", "tools.blindwin.run", "--suite", str(arguments.suite), "--engine", str(engine),
                    "--depth", str(arguments.depth), "--role", "diagnostic", "--out", str(out)],
                   check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
    results = [json.loads(line) for line in out.with_suffix(".jsonl").open(encoding="utf-8")]
    gaps = static_gap(engine, results)
    (arguments.out.parent / f"sweep_{name}_gap.json").write_text(json.dumps(gaps, indent=1), encoding="utf-8")
    return {"name": name, "mg": tables[0], "eg": tables[1], "results": results, "gaps": gaps}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--suite", type=Path, default=Path("corpus/blindwin_regression_v1.jsonl"))
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--members", default=",".join(FAMILY))
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    names = [n for n in arguments.members.split(",") if n]
    with ThreadPoolExecutor(max_workers=arguments.workers) as pool:
        variants = list(pool.map(lambda n: run_variant(n, FAMILY[n], arguments), names))

    lines = [f"== PASSED-PAWN TABLE SWEEP on the DIAGNOSTIC half of the blind-win suite (depth {arguments.depth}) ==",
             "family fixed in advance; validation half not read. robust = mean loss winsorised at 500; cl-rob weights each source game equally.",
             "gap = Stockfish minus candidate static at the end of Stockfish's PV (the audit's discriminator), mean over rows / over clusters.", "",
             f"{'member':<10} {'n':>3} {'clus':>4} {'robust':>7} {'cl-rob':>7} {'serious':>8} {'catast':>7} {'agree':>6} {'root':>6} {'root<100':>8} | {'gap rows':>8} {'gap clus':>8} {'closed':>7} {'EG@7':>5} {'MG@7':>5}"]
    table = []
    for v in variants:
        rs, gs = v["results"], v["gaps"]
        n = len(rs)
        clusters: dict[int, list[dict]] = {}
        for r in rs:
            clusters.setdefault(int(r["cluster"]), []).append(r)
        cl_rob = statistics.mean(statistics.mean(min(x["loss"], 500) for x in c) for c in clusters.values())
        gclusters: dict[int, list[dict]] = {}
        for g in gs:
            gclusters.setdefault(int(g["cluster"]), []).append(g)
        gap_rows = statistics.mean(g["gap"] for g in gs)
        gap_cl = statistics.mean(statistics.mean(x["gap"] for x in c) for c in gclusters.values())
        gap_build = statistics.mean(g["gap_at_build"] for g in gs)
        closed = 1 - gap_rows / gap_build if gap_build else 0.0
        row = {"member": v["name"], "n": n, "clusters": len(clusters), "robust": sum(min(r["loss"], 500) for r in rs) / n,
               "cluster_robust": cl_rob, "serious": sum(r["loss"] >= 100 for r in rs) / n,
               "catastrophic": sum(r["loss"] >= 300 for r in rs) / n, "agree": sum(r["move"] == r["sf_best"] for r in rs) / n,
               "root": statistics.mean(r["root"] for r in rs), "root_under_100": sum(r["root"] < 100 for r in rs),
               "gap_rows": gap_rows, "gap_clusters": gap_cl, "gap_at_build": gap_build, "closed": closed,
               "mg": v["mg"], "eg": v["eg"]}
        table.append(row)
        lines.append(f"{row['member']:<10} {n:>3} {row['clusters']:>4} {row['robust']:>7.1f} {cl_rob:>7.1f} {row['serious']:>8.1%} {row['catastrophic']:>7.1%} "
                     f"{row['agree']:>6.1%} {row['root']:>+6.0f} {row['root_under_100']:>5}/{n:<2} | {gap_rows:>+8.0f} {gap_cl:>+8.0f} {closed:>7.0%} {v['eg'][6]:>5} {v['mg'][6]:>5}")
    lines.append("")
    lines.append("per-row moves, member by member (loss; * = matches Stockfish's best):")
    ids = [r["id"] for r in variants[0]["results"]]
    lines.append(f"  {'id':<7} {'cl':>3} {'mech':<20} " + " ".join(f"{v['name']:>12}" for v in variants))
    for i, rid in enumerate(ids):
        cells = []
        for v in variants:
            r = v["results"][i]
            cells.append(f"{r['move']}{'*' if r['move'] == r['sf_best'] else ' '} {min(r['loss'], 999):>4}")
        r0 = variants[0]["results"][i]
        lines.append(f"  {rid:<7} {r0['cluster']:>3} {r0['mechanism']:<20} " + " ".join(f"{c:>12}" for c in cells))
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(table, indent=1), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
