"""Move quality of ClaudeShark on a labelled suite, judged by the oracle.

For every position the engine searches (fixed depth, or a fixed budget), and
the oracle then scores the position *after* the engine's move and after its
own best move, at the same node count. The loss is the difference, from the
side to move. Scoring both children the same way, rather than comparing the
engine's child against the root label, keeps the two numbers on one scale.

What is kept per position: the engine's move, score, depth, nodes and PV; the
static evaluation of the root; the oracle's best move, its score, the score
after the engine's move, the centipawn loss and the change in expected score
(from WDL). Metrics are then broken down by phase, structural tag and opening
family, because the question is *where* the engine goes wrong.

    uv run python -m tools.corpus.analyse --suite corpus\\competition_like_v1.jsonl ^
        --depth 6 --nodes 1000000 --workers 8 --out corpus\\analysis_cl_v1_d6.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import chess

from tools.corpus.oracle import MATE_CP, Label, Oracle, expected_score, label_many, read_jsonl

SERIOUS_CP = 100
CATASTROPHIC_CP = 300
WINSOR_CP = 500

_ENGINE_DIR: str | None = None


def _init_engine(engine_dir: str | None) -> None:
    global _ENGINE_DIR
    _ENGINE_DIR = engine_dir
    if engine_dir:
        sys.path.insert(0, engine_dir)


def principal_variation(searcher: Any, board: chess.Board, limit: int) -> list[str]:
    """Follow transposition-table moves from the root, guarding against cycles."""
    pv: list[str] = []
    seen: set[int] = set()
    board = board.copy()
    while len(pv) < limit:
        key = hash(board._transposition_key())
        if key in seen:
            break
        seen.add(key)
        entry = searcher.tt.probe(key)
        if entry is None or entry[4] is None or entry[4] not in board.legal_moves:
            break
        pv.append(entry[4].uci())
        board.push(entry[4])
    return pv


def search_position(task: tuple[str, int, int]) -> dict[str, Any]:
    """Run the engine on one position. Importable so a process pool can call it."""
    if _ENGINE_DIR and _ENGINE_DIR not in sys.path:
        sys.path.insert(0, _ENGINE_DIR)
    from cs_eval import evaluate
    from cs_search import Searcher

    fen, depth, ms = task
    board = chess.Board(fen)
    searcher = Searcher()
    started = time.perf_counter()
    if depth:
        move, info = searcher.search(board, 0, max_depth=depth)
    else:
        move, info = searcher.search(board, 0, fixed_budget_ms=ms)
    elapsed = time.perf_counter() - started
    return {
        "fen": fen,
        "move": move.uci() if move else None,
        "score": info.score,
        "depth": info.depth,
        "nodes": info.nodes,
        "qnodes": info.qnodes,
        "elapsed_ms": round(elapsed * 1000, 1),
        "static_eval": evaluate(chess.Board(fen)),
        "pv": principal_variation(searcher, chess.Board(fen), max(1, info.depth)),
    }


def child_fen(fen: str, move: str) -> str:
    board = chess.Board(fen)
    board.push_uci(move)
    return board.fen()


def stm_score_of_child(label: Label) -> int:
    """Score of the parent's side to move, from a child label (negate)."""
    return -label.cp_stm


def run(
    rows: list[dict[str, Any]], depth: int, ms: int, nodes: int, workers: int,
    engine_dir: str | None, progress: bool = True,
) -> list[dict[str, Any]]:
    tasks = [(row["fen"], depth, ms) for row in rows]
    started = time.perf_counter()
    # A timed search measures the machine too, so keep --workers small (a
    # handful on a twelve-core laptop) when --ms is used.
    if workers > 1:
        with ProcessPoolExecutor(
            max_workers=workers, initializer=_init_engine, initargs=(engine_dir,)
        ) as pool:
            searched = list(pool.map(search_position, tasks, chunksize=2))
    else:
        _init_engine(engine_dir)
        searched = []
        for index, task in enumerate(tasks, 1):
            searched.append(search_position(task))
            if progress and index % 20 == 0:
                print(f"  searched {index}/{len(tasks)}", flush=True)
    search_seconds = time.perf_counter() - started
    if progress:
        print(f"engine: {len(tasks)} positions in {search_seconds:.0f} s", flush=True)

    # Oracle: score every child the comparison needs, once each.
    wanted: dict[str, None] = {}
    for row, result in zip(rows, searched, strict=True):
        best = row["reference"]["best"]
        wanted.setdefault(child_fen(row["fen"], best), None)
        if result["move"]:
            wanted.setdefault(child_fen(row["fen"], result["move"]), None)
    fens = list(wanted)
    if progress:
        print(f"oracle: {len(fens)} child positions at {nodes:,} nodes", flush=True)
    labels = dict(zip(fens, label_many(fens, nodes, 1, workers, progress=progress), strict=True))

    out = []
    for row, result in zip(rows, searched, strict=True):
        reference = row["reference"]
        best = reference["best"]
        best_child = labels[child_fen(row["fen"], best)]
        best_cp = stm_score_of_child(best_child)
        if result["move"]:
            our_child = labels[child_fen(row["fen"], result["move"])]
            our_cp = stm_score_of_child(our_child)
            our_wdl = our_child.wdl_stm
        else:
            our_cp = -MATE_CP
            our_wdl = None
        loss = max(0, best_cp - our_cp)
        # Expected score for the side to move, from the WDL of each child
        # (which is from the child's side to move, hence 1 - E).
        best_e = expected_score(best_child.wdl_stm)
        our_e = expected_score(our_wdl)
        e_loss = None
        if best_e is not None and our_e is not None:
            e_loss = max(0.0, (1 - best_e) - (1 - our_e))
        out.append({
            "id": row.get("id"),
            "fen": row["fen"],
            "family": row.get("family"),
            "structure": row.get("structure"),
            "engine": result,
            "reference_best": best,
            "reference_cp_stm": reference.get("cp_white") if row["fen"].split()[1] == "w"
            else -reference["cp_white"] if reference.get("cp_white") is not None else None,
            "best_child_cp_stm": best_cp,
            "our_child_cp_stm": our_cp,
            "cp_loss": loss,
            "expected_score_loss": e_loss,
            "agree": result["move"] == best,
            "within_25": loss <= 25,
            "serious": loss >= SERIOUS_CP,
            "catastrophic": loss >= CATASTROPHIC_CP,
            "mate_involved": abs(best_cp) >= MATE_CP or abs(our_cp) >= MATE_CP,
        })
    return out


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    losses = [r["cp_loss"] for r in rows]
    winsorised = [min(WINSOR_CP, loss) for loss in losses]
    ordered = sorted(losses)
    e_losses = [r["expected_score_loss"] for r in rows if r["expected_score_loss"] is not None]

    def percentile(p: float) -> float:
        index = min(len(ordered) - 1, round(p * (len(ordered) - 1)))
        return float(ordered[index])

    return {
        "n": len(rows),
        "agree": sum(1 for r in rows if r["agree"]) / len(rows),
        "within_25": sum(1 for r in rows if r["within_25"]) / len(rows),
        "median_loss": statistics.median(losses),
        "robust_mean_loss": sum(winsorised) / len(winsorised),
        "p90_loss": percentile(0.90),
        "p95_loss": percentile(0.95),
        "serious_rate": sum(1 for r in rows if r["serious"]) / len(rows),
        "catastrophic_rate": sum(1 for r in rows if r["catastrophic"]) / len(rows),
        "mean_e_loss": (sum(e_losses) / len(e_losses)) if e_losses else None,
    }


def _row(name: str, m: dict[str, Any]) -> str:
    if not m.get("n"):
        return f"| {name} | 0 | | | | | | | | |"
    e = f"{m['mean_e_loss']:.3f}" if m.get("mean_e_loss") is not None else "-"
    return (
        f"| {name} | {m['n']} | {m['agree'] * 100:.0f}% | {m['within_25'] * 100:.0f}% | "
        f"{m['median_loss']:.0f} | {m['robust_mean_loss']:.0f} | {m['p90_loss']:.0f} | "
        f"{m['p95_loss']:.0f} | {m['serious_rate'] * 100:.0f}% | "
        f"{m['catastrophic_rate'] * 100:.1f}% | {e} |"
    )


HEADER = ("| group | n | agree | <=25cp | median | robust mean | p90 | p95 | >=100cp | >=300cp "
          "| E-loss |\n|---|---|---|---|---|---|---|---|---|---|---|")


def report(results: list[dict[str, Any]], title: str, settings: str) -> str:
    lines = [f"# {title}", "", settings, "",
             "Loss is centipawns from the side to move, oracle score after the oracle's best "
             "move minus oracle score after the engine's move, both at the same node count. "
             "Robust mean winsorises at 500 cp. E-loss is the drop in expected score from WDL.",
             "", "## Overall", "", HEADER, _row("all", metrics(results))]
    by_phase: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in results:
        structure = r.get("structure") or {}
        by_phase[structure.get("phase", "?")].append(r)
        for tag in structure.get("tags", []):
            by_tag[tag].append(r)
        by_family[r.get("family") or "?"].append(r)
    lines += ["", "## By phase", "", HEADER]
    lines += [_row(k, metrics(v)) for k, v in sorted(by_phase.items())]
    lines += ["", "## By structural tag (sorted by robust mean loss, n >= 8)", "", HEADER]
    tag_rows = [(k, metrics(v)) for k, v in by_tag.items() if len(v) >= 8]
    tag_rows.sort(key=lambda kv: -kv[1]["robust_mean_loss"])
    lines += [_row(k, m) for k, m in tag_rows]
    lines += ["", "## By opening family (n >= 4)", "", HEADER]
    fam_rows = [(k, metrics(v)) for k, v in by_family.items() if len(v) >= 4]
    fam_rows.sort(key=lambda kv: -kv[1]["robust_mean_loss"])
    lines += [_row(k, m) for k, m in fam_rows]
    worst = sorted(results, key=lambda r: -r["cp_loss"])[:25]
    lines += ["", "## Worst 25 positions", "",
              "| id | loss | engine | best | engine score | family | tags | fen |",
              "|---|---|---|---|---|---|---|---|"]
    for r in worst:
        tags = ", ".join(t for t in (r.get("structure") or {}).get("tags", [])
                         if t not in ("open_file", "semi_open_file"))
        lines.append(
            f"| {r.get('id')} | {r['cp_loss']} | {r['engine']['move']} | {r['reference_best']} | "
            f"{r['engine']['score']} | {r.get('family')} | {tags} | `{r['fen']}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Oracle-judged move quality on a suite.")
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6, help="fixed depth; 0 means use --ms")
    parser.add_argument("--ms", type=int, default=0, help="fixed budget per move")
    parser.add_argument("--nodes", type=int, default=1_000_000, help="oracle nodes per child")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--engine", type=Path, default=None, help="frozen snapshot directory")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    arguments = parser.parse_args()

    records = read_jsonl(arguments.suite)
    header = next((r for r in records if r.get("record") == "header"), {})
    rows = [r for r in records if r.get("record") != "header" and r.get("reference")]
    if arguments.limit:
        rows = rows[: arguments.limit]
    engine_dir = str(arguments.engine.resolve()) if arguments.engine else None
    with Oracle() as oracle:
        provenance = oracle.provenance()

    results = run(rows, arguments.depth, arguments.ms, arguments.nodes, arguments.workers,
                  engine_dir)
    limit = f"depth {arguments.depth}" if arguments.depth else f"{arguments.ms} ms"
    settings = (
        f"Engine: {arguments.engine or 'working tree'}, {limit}. Suite: {arguments.suite} "
        f"({header.get('suite')} {header.get('version')}, hash `{header.get('hash')}`, "
        f"{len(rows)} positions). Oracle: {provenance['engine']} at {arguments.nodes:,} nodes "
        f"per child, single thread."
    )
    with arguments.out.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "record": "header", "engine": str(arguments.engine or "working tree"),
            "depth": arguments.depth, "ms": arguments.ms, "oracle": provenance,
            "nodes": arguments.nodes, "suite": str(arguments.suite),
            "suite_hash": header.get("hash"), "positions": len(rows),
            "metrics": metrics(results),
        }) + "\n")
        for r in results:
            handle.write(json.dumps(r, separators=(",", ":")) + "\n")
    text = report(results, f"Move quality: {arguments.suite.stem} at {limit}", settings)
    arguments.out.with_suffix(".md").write_text(text, encoding="utf-8")
    print(text)
    print(f"written {arguments.out} and {arguments.out.with_suffix('.md')}")


if __name__ == "__main__":
    main()
