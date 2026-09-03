"""Does the engine search less carefully when it is already winning?

Positions from the annotated self-play games are binned by the *engine's own*
static evaluation of the position (so the bins reflect what the search sees,
not what Stockfish knows) and the instrumented production engine searches each
one at a fixed depth. Per-node rates of every pruning mechanism are compared
across the bins, together with the principal-variation length the search
actually reports.

Bins are matched on phase so a difference between "winning" and "level" is not
just a difference between endgames and middlegames.

    uv run python -m tools.conversion.search_bins --engine <dir> --games <annotated.jsonl>
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

import chess

from tools.corpus.structure import analyse_structure
from tools.postmortem.play import Engine

BINS = (("|eval| < 100", lambda v: abs(v) < 100),
        ("+100..+299", lambda v: 100 <= v < 300),
        ("+300..+599", lambda v: 300 <= v < 600),
        (">= +600", lambda v: v >= 600),
        ("-100..-299", lambda v: -300 < v <= -100),
        ("<= -300", lambda v: v <= -300))

RATES = (("nodes", None), ("qnodes", "nodes"), ("cutoffs", "nodes"),
         ("c_null_tries", "nodes"), ("c_null_cuts", "c_null_tries"),
         ("c_lmr_reduced", "nodes"), ("c_lmr_research", "c_lmr_reduced"),
         ("c_delta_pruned", "qnodes"), ("c_see_pruned", "qnodes"),
         ("researches", None), ("tt_hits", "tt_probes"), ("pv_len", None))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--per-bin", type=int, default=80)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    # Production is 'base' in the retained set; its own static eval from the
    # side to move is what the search starts from.
    pool = defaultdict(list)
    for g in games:
        for m in g["moves"]:
            if abs(m["sf_cp_white_before"]) >= 9000:
                continue
            own = m["base_static"] if m["turn"] == "w" else -m["base_static"]
            phase = analyse_structure(chess.Board(m["fen"])).phase
            for name, test in BINS:
                if test(own):
                    pool[(name, phase)].append(m["fen"])
    rng = random.Random(3)
    engine = Engine(arguments.engine, arguments.depth)
    lines = [f"== SEARCH BEHAVIOUR BY THE ENGINE'S OWN STATIC EVAL (production, depth {arguments.depth}) ==",
             "rates are per node / per parent count; pv_len is the reported principal variation length", ""]
    results = {}
    try:
        for phase in ("middlegame", "endgame"):
            lines.append(f"-- phase: {phase}")
            header = f"{'bin':<14} {'n':>4} " + " ".join(f"{k + ('/' + p if p else ''):>18}" for k, p in RATES)
            lines.append(header)
            for name, _ in BINS:
                fens = pool.get((name, phase), [])
                if len(fens) < 10:
                    continue
                sample = rng.sample(fens, min(arguments.per_bin, len(fens)))
                agg = defaultdict(list)
                for fen in sample:
                    engine.ask("new")
                    r = engine.ask(f"go {fen}")
                    r["pv_len"] = len(r.get("pv", []))
                    for k, p in RATES:
                        v = r.get(k, 0)
                        agg[k + ("/" + p if p else "")].append(v / max(1, r.get(p, 1)) if p else v)
                row = {k: statistics.mean(v) for k, v in agg.items()}
                results[(phase, name)] = row
                lines.append(f"{name:<14} {len(sample):>4} " + " ".join(f"{row[k + ('/' + p if p else '')]:>18.4f}" for k, p in RATES))
            lines.append("")
    finally:
        engine.close()
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
