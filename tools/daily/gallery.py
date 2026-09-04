"""The positions the engine reads most wrongly, as a handoff gallery.

Selected from every ply of the annotated corpora on the size of the
disagreement between the engine's depth-6 root and the oracle, from the mover's
point of view, with one position kept per source cluster so that a single game
cannot fill the list. Positions whose oracle score is a mate are excluded: the
interesting cases are evaluation failures, not missed mates.

Each row carries what a reviewer needs to reproduce and argue with it: the FEN,
the oracle score and its preferred move, the engine's root and static scores
and its move, the phase, and a structural label from the same feature set the
attribution report uses.

    uv run python -m tools.daily.gallery --count 20 --out corpus/daily/failure_gallery.txt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess

from tools.daily.attribute import CORPORA, features, phase_of


def label(board: chess.Board) -> str:
    f = features(board)
    parts = []
    if f["their passers"]:
        parts.append(f"enemy passers {f['their passers']} (best rank {f['their best passer rank'] + 1})")
    if f["our passers"]:
        parts.append(f"own passers {f['our passers']} (best rank {f['our best passer rank'] + 1})")
    if f["our king inside their passer's square"] is False:
        parts.append("our king outside the square of an enemy passer")
    if f["opposite-coloured bishops"]:
        parts.append("opposite bishops")
    if f["pawns on one wing only"]:
        parts.append("pawns on one wing")
    if f["rook behind our own passer"]:
        parts.append("rook behind our passer")
    if not board.pawns:
        parts.append("pawnless")
    return "; ".join(parts) or "no structural flag"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--clamp", type=int, default=2000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    rows = []
    for path in CORPORA:
        p = Path(path)
        if not p.exists():
            continue
        for line in p.open(encoding="utf-8"):
            g = json.loads(line)
            for m in g["moves"]:
                sf_white = m.get("sf_cp_white_before")
                if sf_white is None or abs(sf_white) > arguments.clamp:
                    continue
                # A root at a mate score is the engine finding a forced mate the
                # node-limited oracle did not report. That is the engine being
                # right, not a failure, so it does not belong in this gallery.
                if abs(m["score_stm"]) > 9000:
                    continue
                field = "cand_static" if m["mover"] == "cand" else "base_static"
                if m.get(field) is None:
                    continue
                board = chess.Board(m["fen"])
                white = board.turn == chess.WHITE
                sf = sf_white if white else -sf_white
                rows.append({
                    "corpus": path, "cluster": int(g["cluster"]), "fen": m["fen"],
                    "sf": sf, "sf_best": m["sf_best"], "root": m["score_stm"],
                    "static": m[field] if white else -m[field], "move": m["move"],
                    "phase": phase_of(board), "gap": abs(m["score_stm"] - sf),
                    "label": label(board),
                })
    rows.sort(key=lambda r: -r["gap"])
    seen: set[tuple[str, int]] = set()
    kept = []
    for r in rows:
        key = (r["corpus"], r["cluster"])
        if key in seen:
            continue
        seen.add(key)
        kept.append(r)
        if len(kept) >= arguments.count:
            break
    lines = [f"== FAILURE GALLERY: the {len(kept)} widest engine-oracle disagreements, one per source cluster ==",
             "Scores are from the mover's point of view. 'gap' is the depth-6 root minus the oracle.", ""]
    for i, r in enumerate(kept, start=1):
        direction = "too optimistic" if r["root"] > r["sf"] else "too pessimistic"
        lines.append(f"{i:>2}. gap {r['root'] - r['sf']:+6} ({direction})   phase {r['phase']:>2}")
        lines.append(f"    {r['fen']}")
        lines.append(f"    oracle {r['sf']:>+6} (prefers {r['sf_best']})   engine root {r['root']:>+6} static {r['static']:>+6} (played {r['move']})")
        lines.append(f"    structure: {r['label']}")
        lines.append(f"    source: {r['corpus']} cluster {r['cluster']}")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(kept, indent=1) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
