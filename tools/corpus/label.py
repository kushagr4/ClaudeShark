"""Attach reference labels to a candidate pool.

Reads the JSONL written by ``extract.py``, labels every position with the
oracle at a fixed node count, and writes the same rows back with a
``reference`` block (score, WDL, best move, PV, multipv lines) and the gap
between the best and second-best line. Existing labels in the output file are
reused, so an interrupted run resumes rather than restarts.

    uv run python -m tools.corpus.label --in corpus\\candidates.jsonl ^
        --out corpus\\candidates_labelled.jsonl --nodes 1000000 --multipv 2 --workers 8
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from tools.corpus.oracle import Label, Oracle, expected_score, label_many, read_jsonl


def load_existing(path: Path, nodes: int, multipv: int) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    existing: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        if row.get("record") == "header":
            continue
        reference = row.get("reference")
        if not reference or reference.get("nodes") != nodes:
            continue
        if len(reference.get("lines", [])) >= multipv:
            existing[row["fen"]] = reference
    return existing


def attach(row: dict[str, Any], label: Label) -> dict[str, Any]:
    reference = label.to_json()
    out = dict(row)
    out["reference"] = reference
    out["cp_white"] = label.cp_white
    out["expected_score_white"] = expected_score(label.wdl_white)
    out["second_gap_cp"] = (
        label.lines[0].cp - label.lines[1].cp if len(label.lines) >= 2 else None
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Reference-label a candidate pool.")
    parser.add_argument("--in", dest="source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--multipv", type=int, default=2)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--chunk", type=int, default=200, help="rewrite the output this often")
    arguments = parser.parse_args()

    rows = [r for r in read_jsonl(arguments.source) if r.get("record") != "header"]
    existing = load_existing(arguments.out, arguments.nodes, arguments.multipv)
    todo = [r["fen"] for r in rows if r["fen"] not in existing]
    print(f"{len(rows)} candidates, {len(existing)} already labelled, {len(todo)} to do")

    with Oracle() as oracle:
        provenance = oracle.provenance()
    started = time.perf_counter()

    def write_out(seconds: float) -> None:
        # Rows without a label yet are written without one, so an interrupted
        # run leaves a file the next run can resume from.
        with arguments.out.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "record": "header",
                "source": str(arguments.source),
                "oracle": provenance,
                "nodes": arguments.nodes,
                "multipv": arguments.multipv,
                "positions": len(rows),
                "labelled": len(existing),
                "seconds_this_run": round(seconds, 1),
            }) + "\n")
            for row in rows:
                reference = existing.get(row["fen"])
                record = attach(row, Label.from_json(reference)) if reference else dict(row)
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")

    for start in range(0, len(todo), arguments.chunk):
        chunk = todo[start:start + arguments.chunk]
        fresh = label_many(chunk, arguments.nodes, arguments.multipv, arguments.workers)
        for fen, label in zip(chunk, fresh, strict=True):
            existing[fen] = label.to_json()
        write_out(time.perf_counter() - started)
        print(f"  labelled {min(len(todo), start + len(chunk))}/{len(todo)} "
              f"({time.perf_counter() - started:.0f} s)", flush=True)
    write_out(time.perf_counter() - started)
    print(f"labelled {len(todo)} in {time.perf_counter() - started:.0f} s -> {arguments.out}")


if __name__ == "__main__":
    main()
