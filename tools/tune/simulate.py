"""Simulate a candidate material set without touching production.

Copies the engine into a scratch directory, rewrites only the two material
tuples in that copy's `cs_constants.py`, and runs the standard oracle-judged
move-quality analysis against it. Production files are never modified. The
copy is also timed, so the zero-runtime claim is verified rather than assumed.

    uv run python -m tools.tune.simulate --candidate "quiet (tol 30)"
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_FILES = ("agent.py", *(p.name for p in ROOT.glob("cs_*.py")))


def patched_engine(mg: list[int], eg: list[int], where: Path) -> Path:
    where.mkdir(parents=True, exist_ok=True)
    for name in ENGINE_FILES:
        shutil.copy2(ROOT / name, where / name)
    constants = where / "cs_constants.py"
    src = constants.read_text(encoding="utf-8")
    mg_line = f"_MG_VALUE = (0, {mg[0]}, {mg[1]}, {mg[2]}, {mg[3]}, {mg[4]}, 0)"
    eg_line = f"_EG_VALUE = (0, {eg[0]}, {eg[1]}, {eg[2]}, {eg[3]}, {eg[4]}, 0)"
    src, n1 = re.subn(r"^_MG_VALUE = \(.*\)$", mg_line, src, flags=re.M)
    src, n2 = re.subn(r"^_EG_VALUE = \(.*\)$", eg_line, src, flags=re.M)
    if n1 != 1 or n2 != 1:
        raise SystemExit("could not locate the material tuples in cs_constants.py")
    constants.write_text(src, encoding="utf-8")
    return where


def eval_throughput(engine_dir: Path) -> float:
    code = (
        "import sys, chess, random\n"
        f"sys.path.insert(0, {str(engine_dir)!r})\n"
        "from cs_eval import evaluate\n"
        "from time import perf_counter\n"
        "rng=random.Random(1); boards=[]\n"
        "for _ in range(60):\n"
        "    b=chess.Board()\n"
        "    for _ in range(rng.randint(10,60)):\n"
        "        m=list(b.legal_moves)\n"
        "        if not m: break\n"
        "        b.push(rng.choice(m))\n"
        "    boards.append(b)\n"
        "for b in boards: evaluate(b)\n"
        "t=perf_counter()\n"
        "for _ in range(400):\n"
        "    for b in boards: evaluate(b)\n"
        "print(400*len(boards)/(perf_counter()-t))\n"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       check=True, cwd=ROOT)
    return float(r.stdout.strip().splitlines()[-1])


def summarise(path: Path) -> dict:
    rows = [json.loads(line) for line in path.open(encoding="utf-8") if '"cp_loss"' in line]
    losses = [r["cp_loss"] for r in rows]
    w = [min(x, 500) for x in losses]
    return {
        "n": len(rows),
        "agree": sum(1 for r in rows if r["engine"]["move"] == r["reference_best"]) / len(rows),
        "le25": sum(1 for x in losses if x <= 25) / len(rows),
        "le50": sum(1 for x in losses if x <= 50) / len(rows),
        "robust": sum(w) / len(w),
        "serious": sum(1 for x in losses if x >= 100) / len(rows),
        "catastrophic": sum(1 for x in losses if x >= 300) / len(rows),
        "by_fen": {r["fen"]: (r["engine"]["move"], r["cp_loss"]) for r in rows},
    }


def main() -> None:
    # Windows consoles default to cp1252, which cannot print the Greek and
    # box characters in these tables; the files are always UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Move-quality simulation of a material candidate.")
    parser.add_argument("--candidate", default="quiet (tol 30)")
    parser.add_argument("--candidates", type=Path,
                        default=Path("corpus/tune/material_candidates.json"))
    parser.add_argument("--baseline", type=Path,
                        default=Path("corpus/analysis_cl_v1_d6_ksoff.jsonl"))
    parser.add_argument("--suite", type=Path, default=Path("corpus/competition_like_v1.jsonl"))
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--out", type=Path, default=Path("corpus/tune/simulate.md"))
    arguments = parser.parse_args()

    cands = json.loads(arguments.candidates.read_text(encoding="utf-8"))
    cand = cands[arguments.candidate]
    mg, eg = cand["mg"], cand["eg"]
    print(f"candidate {arguments.candidate!r}: MG {mg} EG {eg}")

    scratch = Path(tempfile.mkdtemp(prefix="cs_material_"))
    engine = patched_engine(mg, eg, scratch / "engine")
    baseline_dir = patched_engine(
        [82, 337, 365, 477, 1025], [94, 281, 297, 512, 936], scratch / "baseline"
    )

    print("timing evaluators...")
    t_base = eval_throughput(baseline_dir)
    t_cand = eval_throughput(engine)

    analysis = scratch / "analysis.jsonl"
    print("running oracle-judged analysis on the candidate...")
    subprocess.run(
        [sys.executable, "-m", "tools.corpus.analyse", "--suite", str(arguments.suite),
         "--depth", str(arguments.depth), "--engine", str(engine), "--out", str(analysis)],
        check=True, cwd=ROOT,
    )

    base = summarise(arguments.baseline)
    cand_s = summarise(analysis)
    out = [f"# Move-quality simulation: material candidate {arguments.candidate!r}", "",
           f"MG {mg}  EG {eg}", "(production MG [82, 337, 365, 477, 1025], "
           "EG [94, 281, 297, 512, 936])", "",
           "## Runtime", "",
           "| | evals/s |", "|---|---|",
           f"| production values | {t_base:,.0f} |", f"| candidate values | {t_cand:,.0f} |",
           f"| ratio | {t_cand / t_base:.3f} |", "",
           f"## {arguments.suite.name}, depth {arguments.depth}", "",
           "| metric | current | candidate | Δ |", "|---|---|---|---|"]
    for key, fmt in (("agree", "{:.1%}"), ("le25", "{:.1%}"), ("le50", "{:.1%}"),
                     ("robust", "{:.1f}"), ("serious", "{:.1%}"), ("catastrophic", "{:.1%}")):
        a, b = base[key], cand_s[key]
        out.append(f"| {key} | {fmt.format(a)} | {fmt.format(b)} | {fmt.format(b - a)} |")

    changed = [
        (f, base["by_fen"][f], cand_s["by_fen"][f]) for f in base["by_fen"]
        if f in cand_s["by_fen"] and base["by_fen"][f][0] != cand_s["by_fen"][f][0]
    ]
    better = sum(1 for _, (_, la), (_, lb) in changed if lb < la - 10)
    worse = sum(1 for _, (_, la), (_, lb) in changed if lb > la + 10)
    out += ["", f"moves changed: {len(changed)}/{base['n']}  "
                f"(better by >10cp: {better}, worse: {worse}, "
                f"neutral: {len(changed) - better - worse})"]

    # The seven persistent evaluation failures
    diag = Path("corpus/diagnosis_cl_v1.jsonl")
    if diag.exists():
        ev = [json.loads(line) for line in diag.open(encoding="utf-8") if '"cause"' in line]
        ev = [r for r in ev if r["cause"] == "evaluation"]
        out += ["", "## The seven persistent evaluation failures", "",
                "| id | current move / loss | candidate move / loss | oracle |",
                "|---|---|---|---|"]
        for r in ev:
            f = r["fen"]
            if f in base["by_fen"] and f in cand_s["by_fen"]:
                (ma, la), (mb, lb) = base["by_fen"][f], cand_s["by_fen"][f]
                out.append(f"| {r['id']} | {ma} / {la} | {mb} / {lb} | {r['reference_best']} |")

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    # Name the record after --out so two candidates never collide.
    shutil.copy2(analysis, arguments.out.with_suffix(".analysis.jsonl"))
    print("\n".join(out))
    shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
