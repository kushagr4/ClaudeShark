"""Control: does a uniform evaluator scale change how the engine plays?

Scaling every evaluation term by the same factor cannot change which move a
static comparison prefers -- argmax is scale-invariant. But the search's own
margins are absolute centipawn constants: the aspiration window, the delta
pruning margin, the futility-style thresholds. They do not scale with the
evaluation, so a uniform scale silently makes every one of them *relatively
tighter*.

If a uniform scale moves move quality on the external suite, the cause is
search-margin calibration and not evaluation. This measures that, so the
material-scale result can be attributed correctly. Nothing here is a playing
candidate and no margin is tuned.

    uv run python -m tools.tune.wholescale --scale 1.47
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

from tools.tune.simulate import ENGINE_FILES, ROOT, summarise


def whole_scaled_engine(s: float, where: Path) -> Path:
    """Copy the engine and scale every evaluation constant by s.

    Material values, both piece-square table families, the bishop pair and the
    tempo bonus -- everything `evaluate` sums. Search margins are deliberately
    left alone: they are the point of the control.
    """
    where.mkdir(parents=True, exist_ok=True)
    for name in ENGINE_FILES:
        shutil.copy2(ROOT / name, where / name)
    path = where / "cs_constants.py"
    src = path.read_text(encoding="utf-8")

    def scale_tuple(match: re.Match[str]) -> str:
        head, body = match.group(1), match.group(2)
        values = [round(int(v.strip()) * s) for v in body.split(",") if v.strip()]
        return f"{head} = ({', '.join(str(v) for v in values)})"

    # The two material tuples and every piece-square table are plain int tuples.
    src, n = re.subn(
        r"^(_(?:MG|EG)_(?:VALUE|PAWN|KNIGHT|BISHOP|ROOK|QUEEN|KING)) = \(([^)]*)\)$",
        scale_tuple, src, flags=re.M | re.S,
    )
    if n < 14:
        raise SystemExit(f"expected 14 scaled tuples, patched {n}")
    for name in ("BISHOP_PAIR_MG", "BISHOP_PAIR_EG", "TEMPO"):
        src, k = re.subn(
            rf"^{name} = (\d+)$",
            lambda m, _n=name: f"{_n} = {round(int(m.group(1)) * s)}",
            src, flags=re.M,
        )
        if k != 1:
            raise SystemExit(f"could not scale {name}")
    path.write_text(src, encoding="utf-8")
    return where


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Whole-evaluator scale control.")
    parser.add_argument("--scale", type=float, default=1.47)
    parser.add_argument("--suite", type=Path, default=Path("corpus/competition_like_v1.jsonl"))
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--baseline", type=Path,
                        default=Path("corpus/analysis_cl_v1_d6_ksoff.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("corpus/tune/wholescale.md"))
    arguments = parser.parse_args()

    scratch = Path(tempfile.mkdtemp(prefix="cs_wholescale_"))
    engine = whole_scaled_engine(arguments.scale, scratch / "engine")
    analysis = scratch / "analysis.jsonl"
    subprocess.run(
        [sys.executable, "-m", "tools.corpus.analyse", "--suite", str(arguments.suite),
         "--depth", str(arguments.depth), "--engine", str(engine), "--out", str(analysis)],
        check=True, cwd=ROOT,
    )

    base = summarise(arguments.baseline)
    cand = summarise(analysis)
    out = [f"# Control: whole-evaluator scale x{arguments.scale}", "",
           "Every evaluation constant scaled -- material, both piece-square table "
           "families, bishop pair, tempo. Search margins deliberately unchanged.", "",
           "A uniform scale is statically decision-invariant, so anything that moves "
           "here is search-margin calibration, not evaluation.", "",
           f"| metric | current | uniform x{arguments.scale:.2f} | delta |",
           "|---|---|---|---|"]
    for key, fmt in (("agree", "{:.1%}"), ("le25", "{:.1%}"), ("le50", "{:.1%}"),
                     ("robust", "{:.1f}"), ("serious", "{:.1%}"),
                     ("catastrophic", "{:.1%}")):
        a, b = base[key], cand[key]
        out.append(f"| {key} | {fmt.format(a)} | {fmt.format(b)} | {fmt.format(b - a)} |")

    changed = [f for f in base["by_fen"]
               if f in cand["by_fen"] and base["by_fen"][f][0] != cand["by_fen"][f][0]]
    better = sum(1 for f in changed if cand["by_fen"][f][1] < base["by_fen"][f][1] - 10)
    worse = sum(1 for f in changed if cand["by_fen"][f][1] > base["by_fen"][f][1] + 10)
    out += ["", f"moves changed: {len(changed)}/{base['n']} "
                f"(better by >10cp: {better}, worse: {worse}, "
                f"neutral: {len(changed) - better - worse})", "",
            "If this is near zero the search margins are not materially miscalibrated "
            "at this scale, and the material-scale result can be read as evaluation."]

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    shutil.copy2(analysis, arguments.out.parent / "wholescale_analysis.jsonl")
    print("\n".join(out))
    json.dump({"scale": arguments.scale, "changed": len(changed),
               "better": better, "worse": worse},
              (arguments.out.parent / "wholescale.json").open("w"))
    shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
