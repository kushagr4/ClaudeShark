"""Same-position search comparison: candidate and baseline on identical FENs.

The game records only show each engine searching its own turns. To compare
pruning behaviour fairly both instrumented engines are run on the *same*
positions at the same fixed depth -- by default every position in which the
candidate made a serious error in the diagnostic games, plus a matched sample
of positions in which it did not. Counters are reported per node so that the
comparison is about the shape of the tree, not its size.

    uv run python -m tools.postmortem.probe --cand <dir> --base <dir> --games <annotated.jsonl>
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

from tools.postmortem.play import Engine

COUNTERS = (
    "c_null_tries",
    "c_null_cuts",
    "c_lmr_reduced",
    "c_lmr_research",
    "c_asp_low",
    "c_asp_high",
    "c_delta_pruned",
    "c_see_pruned",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cand", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--sample", type=int, default=120)
    parser.add_argument("--out", type=Path, default=Path("corpus/postmortem/07_search_probe.txt"))
    arguments = parser.parse_args()

    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    errors = [m for g in games for m in g["moves"] if m["mover"] == "cand" and m["cp_loss"] >= 100]
    quiet = [m for g in games for m in g["moves"] if m["mover"] == "cand" and m["cp_loss"] <= 10]
    rng = random.Random(7)
    err_fens = [m["fen"] for m in rng.sample(errors, min(arguments.sample, len(errors)))]
    quiet_fens = [m["fen"] for m in rng.sample(quiet, min(arguments.sample, len(quiet)))]

    cand = Engine(arguments.cand, arguments.depth)
    base = Engine(arguments.base, arguments.depth)
    out = [
        f"== SAME-POSITION SEARCH PROBE (depth {arguments.depth}) ==",
        f"candidate serious-error positions: {len(err_fens)}; quiet control positions: {len(quiet_fens)}",
        "",
    ]
    for label, fens in (
        ("candidate-error positions", err_fens),
        ("quiet control positions", quiet_fens),
    ):
        rows = {"cand": [], "base": []}
        same_move = 0
        for fen in fens:
            cand.ask("new")
            base.ask("new")
            rc = cand.ask(f"go {fen}")
            rb = base.ask(f"go {fen}")
            rows["cand"].append(rc)
            rows["base"].append(rb)
            same_move += rc["move"] == rb["move"]
        out.append(f"-- {label}: same root move {same_move}/{len(fens)}")
        out.append(f"{'metric':<26} {'cand':>10} {'base':>10} {'ratio':>7}")

        def agg(key, per=None, rows=rows):
            vals = {}
            for s in ("cand", "base"):
                v = [r[key] / max(1, r[per]) for r in rows[s]] if per else [r[key] for r in rows[s]]
                vals[s] = statistics.mean(v)
            ratio = vals["cand"] / vals["base"] if vals["base"] else float("nan")
            out.append(
                f"{key + ('/' + per if per else ''):<26} {vals['cand']:>10.3f} {vals['base']:>10.3f} {ratio:>7.2f}"
            )

        agg("nodes")
        agg("qnodes")
        agg("qnodes", "nodes")
        agg("researches")
        agg("c_asp_low")
        agg("c_asp_high")
        agg("c_null_tries", "nodes")
        agg("c_null_cuts", "c_null_tries")
        agg("c_lmr_reduced", "nodes")
        agg("c_lmr_research", "c_lmr_reduced")
        agg("c_delta_pruned", "qnodes")
        agg("c_see_pruned", "qnodes")
        agg("tt_hits", "tt_probes")
        out.append("")
    cand.close()
    base.close()
    text = "\n".join(out)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
