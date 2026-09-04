"""The V2.2 false-win gallery: one representative row per mechanism and material family, as a regression set.

    uv run python -m tools.v2.fwgallery --mechanisms corpus/v2/fw/03_mechanisms.jsonl --out corpus/v2/fw/falsewin_gallery_v1.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

REASONS = {
    "rook + minor vs rook": "a bishop or knight beside a rook does not beat a lone rook without pawns; the evaluator counts the minor at full value",
    "opposite-coloured bishops": "the extra pawn or pawns cannot pass a bishop that guards the other colour; material and pawn tables both count them",
    "rook ending, extra pawn(s) not enough": "a rook ending a pawn or two up with the defender's rook active and the pawns held; material plus advanced-pawn tables",
    "search/horizon rather than static": "the static is near level; the depth-6 search inflates the root, usually through a pawn it believes will promote",
    "wrong rook pawn": "bishop of the wrong colour for the rook pawn's queening corner; the defending king sits in the corner",
    "extra pawn but blockaded": "the extra pawn is held by the defending king or a piece in front of it",
    "defender king blockade (pawn ending)": "pawn ending where the defending king holds every passer",
    "queen perpetual resources": "queen against a pawn on the seventh: the fortress draws by stalemate and perpetual resources",
    "insufficient / effectively drawn material": "the material cannot win against a bare king or a single pawn",
    "no material edge: geometry over-credited": "no material edge at all; the advanced-pawn tables carry the whole score",
    "other": "a lone minor or the exchange with a pawn or two on the board, counted at full value where it cannot win",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mechanisms", type=Path, required=True)
    parser.add_argument("--per-mechanism", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    rows = [json.loads(line) for line in arguments.mechanisms.open(encoding="utf-8")]
    picks = []
    for mech in sorted({r["mechanism"] for r in rows}):
        rs = sorted((r for r in rows if r["mechanism"] == mech), key=lambda r: -r["v21_root"])
        seen_fam: set[str] = set()
        seen_traj: set[str] = set()
        for r in rs:
            if r["family"] in seen_fam or r["trajectory"] in seen_traj:
                continue
            picks.append(r)
            seen_fam.add(r["family"])
            seen_traj.add(r["trajectory"])
            if sum(1 for p in picks if p["mechanism"] == mech) >= arguments.per_mechanism:
                break
    out = []
    for i, r in enumerate(sorted(picks, key=lambda r: (r["mechanism"], -r["v21_root"]))):
        out.append({"id": f"fwg-{i:03d}", "fen": r["fen"], "family": r["family"], "signature": r["signature"], "side": r["side"],
                    "sf_cp": r["sf_cp"], "sf_best": r["sf_best"], "v1_static": r["v1_static"], "v1_root": r["v1_root"],
                    "v21_static": r["v21_static"], "v21_root": r["v21_root"], "v21_move": r["v21_move"],
                    "decomposition_stm": r["decomposition_stm"], "pawns_remain": r["pawns_remain"], "king_pawn_active": r["king_pawn_active"],
                    "mechanism": r["mechanism"], "attribution": r["attribution"], "critical_reason": REASONS.get(r["mechanism"], ""),
                    "trajectory": r["trajectory"], "source": r["source"], "nodes": r["nodes"]})
    body = "\n".join(json.dumps(r) for r in out)
    header = {"record": "header", "suite": "falsewin_gallery", "version": "v1", "size": len(out),
              "mechanisms": dict(Counter(r["mechanism"] for r in out)), "hash": hashlib.sha256(body.encode()).hexdigest()[:16],
              "reading": "every row is a position Stockfish calls level (|cp| <= 60 at 1M nodes) that V2.1's depth-6 root calls >= +150"}
    arguments.out.write_text(json.dumps(header) + "\n" + body + "\n", encoding="utf-8")
    lines = [f"== V2.2 FALSE-WIN GALLERY: {len(out)} positions, hash {header['hash']} ==", ""]
    for r in out:
        d = r["decomposition_stm"]
        lines.append(f"{r['id']}  {r['mechanism']}  [{r['attribution']}]")
        lines.append(f"   {r['fen']}")
        lines.append(f"   {r['family']:<22} SF {r['sf_cp']:>+4} best {r['sf_best']:<6} V1 {r['v1_static']:>+4}/{r['v1_root']:>+4}  V2.1 {r['v21_static']:>+4}/{r['v21_root']:>+4} ({r['v21_move']})  material {d['material']:>+4} tables {d['pst']:>+4} king-pawn {d['king_pawn']:>+3}")
        lines.append(f"   {r['critical_reason']}")
    text = "\n".join(lines)
    arguments.out.with_suffix(".txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
