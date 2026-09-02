"""Calibrate the existing benchmark corpus (v2) against the reference oracle.

Every position in ``tools/positions.py`` -- the 24 ``BALANCED_OPENINGS`` and
the 18 ``SHARP_POSITIONS`` -- gets a reference evaluation, WDL, best move and
principal variation, plus its structural labels. Nothing is deleted or
reordered: the old suite stays exactly as it is, versioned, so historical
arena records remain reproducible. This is the first time any of these
positions has carried a label from anything other than the engine under test.

    uv run python -m tools.corpus.calibrate_legacy --nodes 4000000 --workers 8

Writes ``corpus/legacy_v2_calibration.jsonl`` (one record per position) and
``corpus/legacy_v2_calibration.md`` (the table).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle, expected_score, label_many
from tools.corpus.structure import analyse_structure
from tools.positions import BALANCED_OPENINGS, CORPUS_VERSION, SHARP_POSITIONS, corpus_hash

OUT_JSONL = Path("corpus/legacy_v2_calibration.jsonl")
OUT_MD = Path("corpus/legacy_v2_calibration.md")

# Bands used throughout the calibration discussion, in centipawns (white POV).
BANDS = (25, 50, 75, 100)


def classify(cp_white: int, second_gap: int | None) -> str:
    """Coarse verdict for the table. ``second_gap`` is best-minus-second in cp."""
    magnitude = abs(cp_white)
    if second_gap is not None and second_gap >= 150:
        return "tactically forced"
    if magnitude <= 50:
        return "near-equal"
    if magnitude <= 150:
        return "moderate edge"
    if magnitude <= 300:
        return "clear advantage"
    return "decisive"


def main() -> None:
    parser = argparse.ArgumentParser(description="Reference-label the legacy corpus.")
    parser.add_argument("--nodes", type=int, default=4_000_000)
    parser.add_argument("--multipv", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    arguments = parser.parse_args()

    suites = [("balanced", i, f) for i, f in enumerate(BALANCED_OPENINGS)] + [
        ("sharp", i, f) for i, f in enumerate(SHARP_POSITIONS)
    ]
    fens = [fen for _, _, fen in suites]

    with Oracle() as oracle:
        provenance = oracle.provenance()
    started = time.perf_counter()
    labels = label_many(fens, arguments.nodes, arguments.multipv, arguments.workers, progress=True)
    elapsed = time.perf_counter() - started

    rows = []
    for (suite, index, fen), label in zip(suites, labels, strict=True):
        structure = analyse_structure(chess.Board(fen))
        second_gap = None
        if len(label.lines) >= 2:
            second_gap = label.lines[0].cp - label.lines[1].cp
        rows.append({
            "suite": suite,
            "index": index,
            "fen": fen,
            "reference": label.to_json(),
            "second_gap_cp": second_gap,
            "expected_score_white": expected_score(label.wdl_white),
            "verdict": classify(label.cp_white, second_gap),
            "structure": structure.as_json(),
        })

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "record": "header",
            "corpus_version": CORPUS_VERSION,
            "corpus_hash": corpus_hash(),
            "oracle": provenance,
            "nodes": arguments.nodes,
            "multipv": arguments.multipv,
            "seconds": round(elapsed, 1),
        }) + "\n")
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")

    balanced = [r for r in rows if r["suite"] == "balanced"]
    lines = [
        "# Legacy corpus v2: reference calibration",
        "",
        f"Oracle: **{provenance['engine']}**, single thread, hash cleared per position, "
        f"fixed **{arguments.nodes:,} nodes**, multipv {arguments.multipv}. "
        f"Binary SHA-256 `{provenance['binary_sha256'][:16]}...`. "
        f"Corpus v{CORPUS_VERSION} (`{corpus_hash()}`). {elapsed:.0f} s.",
        "",
        "Scores are centipawns from White's point of view. WDL is per mille from White's "
        "point of view. `gap` is the oracle's best line minus its second line, from the "
        "side to move, so a large gap means one move dominates.",
        "",
        "| suite | # | eval | W/D/L | E[score] | best | gap | phase | mat | verdict | tags | fen |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        ref = row["reference"]
        wdl = ref["wdl_white"]
        wdl_text = f"{wdl[0]}/{wdl[1]}/{wdl[2]}" if wdl else "-"
        es = row["expected_score_white"]
        es_text = f"{es:.2f}" if es is not None else "-"
        st = row["structure"]
        gap = row["second_gap_cp"]
        lines.append(
            f"| {row['suite']} | {row['index']} | {ref['cp_white'] / 100:+.2f} | {wdl_text} | "
            f"{es_text} | {ref['best']} | {gap if gap is not None else '-'} | {st['phase']} | "
            f"{st['material_diff']:+d} | {row['verdict']} | "
            f"{', '.join(t for t in st['tags'] if t not in ('open_file', 'semi_open_file'))} | "
            f"`{row['fen']}` |"
        )

    lines += ["", "## Band sensitivity, BALANCED_OPENINGS (24)", "",
              "| band (cp) | inside | outside |", "|---|---|---|"]
    for band in BANDS:
        inside = sum(1 for r in balanced if abs(r["reference"]["cp_white"]) <= band)
        lines.append(f"| +/-{band} | {inside} | {len(balanced) - inside} |")
    lines += ["", "## Verdicts", ""]
    for suite_name in ("balanced", "sharp"):
        counts: dict[str, int] = {}
        for r in rows:
            if r["suite"] == suite_name:
                counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        lines.append(f"* **{suite_name}**: " + ", ".join(
            f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])))
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwritten {OUT_JSONL} and {OUT_MD}")


if __name__ == "__main__":
    main()
