"""Why did the engine get a position wrong: search, pruning, time or evaluation?

Takes the positions an ``analyse.py`` run scored as serious errors and, for
each, asks a sequence of questions whose answers separate the causes:

* **depth ladder** -- does the move become good with one or two more plies
  (a plain search shortfall), only with several more (horizon), or never?
* **feature off** -- at the same depth, does turning off null-move, late move
  reductions, quiescence SEE pruning, delta pruning or aspiration windows fix
  it? Then the pruning is what walked past the answer.
* **more time** -- does a competition-scale budget fix it?
* **static preference** -- does the static evaluator itself prefer the child
  after the engine's move to the child after the oracle's, when the oracle
  says the opposite? Combined with "never fixed", that is an evaluation error.

Each move the ladder produces is scored by the oracle, so "fixed" means the
loss fell under a threshold, not merely that the move changed.

    uv run python -m tools.corpus.diagnose --analysis corpus\\analysis_cl_v1_d6.jsonl ^
        --min-loss 100 --max-depth 9 --ms 4500 --workers 6 --out corpus\\diagnosis_cl_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import chess

from tools.corpus.analyse import child_fen
from tools.corpus.oracle import Oracle, label_many, read_jsonl

FIXED_CP = 50  # a move is "fixed" when its loss falls to this or below

# (name, attribute on cs_search, value that turns the feature off)
FEATURE_OFF: tuple[tuple[str, str, Any], ...] = (
    ("nmp_off", "USE_NULL_MOVE", False),
    ("lmr_off", "USE_LMR", False),
    ("see_qs_off", "USE_SEE_QS", False),
    ("aspiration_off", "USE_ASPIRATION", False),
    ("tt_pv_cutoff_off", "TT_PV_POLICY", "none"),
    ("delta_off", "DELTA_MARGIN", 100_000),
)

_ENGINE_DIR: str | None = None


def _init(engine_dir: str | None) -> None:
    global _ENGINE_DIR
    _ENGINE_DIR = engine_dir
    if engine_dir and engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)


def _search(fen: str, depth: int = 0, ms: int = 0) -> tuple[str | None, int, float]:
    from cs_search import Searcher

    board = chess.Board(fen)
    started = time.perf_counter()
    if depth:
        move, info = Searcher().search(board, 0, max_depth=depth)
    else:
        move, info = Searcher().search(board, 0, fixed_budget_ms=ms)
    return (move.uci() if move else None), info.score, time.perf_counter() - started


def probe(task: tuple[str, int, int, int, float]) -> dict[str, Any]:
    """Every engine-side question for one position, in one worker."""
    if _ENGINE_DIR and _ENGINE_DIR not in sys.path:
        sys.path.insert(0, _ENGINE_DIR)
    import cs_search
    from cs_eval import evaluate

    fen, base_depth, max_depth, ms, ladder_budget_s = task
    result: dict[str, Any] = {"fen": fen, "ladder": {}, "features": {}, "timed": None}

    spent = 0.0
    for depth in range(max(1, base_depth - 2), max_depth + 1):
        move, score, seconds = _search(fen, depth=depth)
        result["ladder"][str(depth)] = {"move": move, "score": score, "seconds": round(seconds, 1)}
        spent += seconds
        if spent > ladder_budget_s:
            break

    if ms:
        move, score, seconds = _search(fen, ms=ms)
        result["timed"] = {"move": move, "score": score, "seconds": round(seconds, 1), "ms": ms}

    for name, attribute, value in FEATURE_OFF:
        original = getattr(cs_search, attribute)
        setattr(cs_search, attribute, value)
        try:
            move, score, _ = _search(fen, depth=base_depth)
        finally:
            setattr(cs_search, attribute, original)
        result["features"][name] = {"move": move, "score": score}

    # Static preference between two children is filled in by the caller once
    # it knows which moves to compare; here we only expose the evaluator.
    result["static_root"] = evaluate(chess.Board(fen))
    return result


def static_child_score(fen: str, move: str) -> int:
    """Static evaluation of the child, from the root side to move."""
    from cs_eval import evaluate

    board = chess.Board(fen)
    board.push_uci(move)
    return -evaluate(board)


def classify(entry: dict[str, Any], base_depth: int) -> str:
    """Name the most specific cause the evidence supports."""
    ladder = entry["ladder_loss"]
    fixed_depths = sorted(
        int(d) for d, loss in ladder.items() if loss is not None and loss <= FIXED_CP
    )
    deeper_fixed = [d for d in fixed_depths if d > base_depth]
    pruning_fixes = [name for name, loss in entry["feature_loss"].items()
                     if loss is not None and loss <= FIXED_CP]
    timed_fixed = entry.get("timed_loss") is not None and entry["timed_loss"] <= FIXED_CP
    static_wrong = entry.get("static_prefers_engine_move")

    if pruning_fixes and not (deeper_fixed and deeper_fixed[0] <= base_depth + 1):
        return "pruning"
    if deeper_fixed:
        if deeper_fixed[0] <= base_depth + 2:
            return "search_depth"
        return "horizon"
    if timed_fixed:
        return "time"
    if static_wrong:
        return "evaluation"
    return "unresolved"


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose serious errors from an analysis run.")
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--min-loss", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=9)
    parser.add_argument("--ms", type=int, default=4500)
    parser.add_argument("--ladder-seconds", type=float, default=240.0,
                        help="stop climbing the ladder once a position has used this much time")
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--engine", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    records = read_jsonl(arguments.analysis)
    header = next((r for r in records if r.get("record") == "header"), {})
    base_depth = int(header.get("depth") or 6)
    rows = [
        r for r in records
        if r.get("record") != "header" and r["cp_loss"] >= arguments.min_loss
    ]
    rows.sort(key=lambda r: -r["cp_loss"])
    if arguments.limit:
        rows = rows[: arguments.limit]
    print(f"{len(rows)} positions with loss >= {arguments.min_loss} at depth {base_depth}")
    engine_dir = str(arguments.engine.resolve()) if arguments.engine else None

    tasks = [(r["fen"], base_depth, arguments.max_depth, arguments.ms, arguments.ladder_seconds)
             for r in rows]
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=arguments.workers, initializer=_init,
                             initargs=(engine_dir,)) as pool:
        probes = list(pool.map(probe, tasks, chunksize=1))
    print(f"engine probes done in {time.perf_counter() - started:.0f} s", flush=True)

    # Score every distinct child the probes produced, once.
    wanted: dict[str, None] = {}
    for row, entry in zip(rows, probes, strict=True):
        moves = {row["reference_best"], row["engine"]["move"]}
        moves |= {v["move"] for v in entry["ladder"].values()}
        moves |= {v["move"] for v in entry["features"].values()}
        if entry["timed"]:
            moves.add(entry["timed"]["move"])
        for move in moves:
            if move:
                wanted.setdefault(child_fen(row["fen"], move), None)
    fens = list(wanted)
    print(f"oracle: {len(fens)} child positions", flush=True)
    with Oracle() as oracle:
        provenance = oracle.provenance()
    labels = dict(zip(fens, label_many(fens, arguments.nodes, 1, arguments.workers, progress=True),
                      strict=True))

    _init(engine_dir)
    out = []
    for row, entry in zip(rows, probes, strict=True):
        fen = row["fen"]
        best = row["reference_best"]
        best_cp = -labels[child_fen(fen, best)].cp_stm

        def loss_of(move: str | None, fen: str = fen, best_cp: int = best_cp) -> int | None:
            if not move:
                return None
            return max(0, best_cp - (-labels[child_fen(fen, move)].cp_stm))

        entry["ladder_loss"] = {d: loss_of(v["move"]) for d, v in entry["ladder"].items()}
        entry["feature_loss"] = {n: loss_of(v["move"]) for n, v in entry["features"].items()}
        entry["timed_loss"] = loss_of(entry["timed"]["move"]) if entry["timed"] else None
        engine_move = row["engine"]["move"]
        entry["static_best_child"] = static_child_score(fen, best)
        entry["static_engine_child"] = static_child_score(fen, engine_move) if engine_move else None
        entry["static_prefers_engine_move"] = (
            entry["static_engine_child"] is not None
            and entry["static_engine_child"] > entry["static_best_child"]
        )
        entry["id"] = row.get("id")
        entry["family"] = row.get("family")
        entry["tags"] = (row.get("structure") or {}).get("tags", [])
        entry["cp_loss"] = row["cp_loss"]
        entry["engine_move"] = engine_move
        entry["reference_best"] = best
        entry["cause"] = classify(entry, base_depth)
        out.append(entry)

    with arguments.out.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "record": "header", "analysis": str(arguments.analysis), "base_depth": base_depth,
            "max_depth": arguments.max_depth, "ms": arguments.ms, "min_loss": arguments.min_loss,
            "oracle": provenance, "nodes": arguments.nodes, "fixed_cp": FIXED_CP,
            "positions": len(out),
        }) + "\n")
        for entry in out:
            handle.write(json.dumps(entry, separators=(",", ":")) + "\n")

    causes = Counter(e["cause"] for e in out)
    lines = [f"# Diagnosis of {len(out)} serious errors (loss >= {arguments.min_loss} cp at depth "
             f"{base_depth})", "",
             f"Fixed means the oracle-scored loss of the new move is <= {FIXED_CP} cp. "
             f"Ladder from depth {max(1, base_depth - 2)} to {arguments.max_depth}; timed "
             f"search {arguments.ms} ms; feature-off variants at depth {base_depth}.", "",
             "| cause | count |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in causes.most_common()]
    tag_cause: dict[str, Counter[str]] = {}
    for e in out:
        for tag in e["tags"]:
            if tag in ("open_file", "semi_open_file"):
                continue
            tag_cause.setdefault(tag, Counter())[e["cause"]] += 1
    lines += ["", "## Cause by structural tag (tags with >= 3 errors)", "",
              "| tag | errors | pruning | search_depth | horizon | time | evaluation | "
              "unresolved |", "|---|---|---|---|---|---|---|---|"]
    for tag, counter in sorted(tag_cause.items(), key=lambda kv: -sum(kv[1].values())):
        total = sum(counter.values())
        if total < 3:
            continue
        lines.append(f"| {tag} | {total} | " + " | ".join(
            str(counter.get(c, 0)) for c in
            ("pruning", "search_depth", "horizon", "time", "evaluation", "unresolved")) + " |")
    lines += ["", "## Every position", "",
              "| id | loss | engine | best | cause | ladder losses | features fixed | timed loss | "
              "static prefers engine move | fen |", "|---|---|---|---|---|---|---|---|---|---|"]
    for e in out:
        ladder = ", ".join(f"d{d}:{loss if loss is not None else '?'}"
                           for d, loss in e["ladder_loss"].items())
        fixed = ", ".join(n for n, loss in e["feature_loss"].items()
                          if loss is not None and loss <= FIXED_CP) or "-"
        lines.append(
            f"| {e['id']} | {e['cp_loss']} | {e['engine_move']} | {e['reference_best']} | "
            f"**{e['cause']}** | {ladder} | {fixed} | {e['timed_loss']} | "
            f"{'yes' if e['static_prefers_engine_move'] else 'no'} | `{e['fen']}` |"
        )
    text = "\n".join(lines) + "\n"
    arguments.out.with_suffix(".md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
