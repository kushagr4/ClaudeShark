"""Which winning positions can the static evaluation not see?

"Blind" positions are those Stockfish scores at +300 or better for the
production engine while the engine's own root score is under +100. The
awareness table shows serious errors concentrate there, so the features that
distinguish blind winning positions from seen ones point at the missing
evaluation knowledge.

Compared: structural tags, imbalance, phase, piece counts, passed-pawn
geometry (rank of the most advanced passer, outside passers, whether the
opponent king is inside the passer's square), king activity in pawn endings,
and whether the win Stockfish sees is a promotion or a mate within its line.

    uv run python -m tools.conversion.blind --games <annotated.jsonl> --out <txt>
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

import chess

from tools.corpus.structure import analyse_structure

VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def own(m: dict) -> int:
    return m["sf_cp_white_before"] if m["turn"] == "w" else -m["sf_cp_white_before"]


def passers(board: chess.Board, colour: bool) -> list[int]:
    out = []
    for sq in board.pieces(chess.PAWN, colour):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        ahead = range(r + 1, 8) if colour else range(r - 1, -1, -1)
        blocked = False
        for rr in ahead:
            for ff in (f - 1, f, f + 1):
                if 0 <= ff < 8 and board.piece_at(chess.square(ff, rr)) == chess.Piece(chess.PAWN, not colour):
                    blocked = True
        if not blocked:
            out.append(sq)
    return out


def features(fen: str) -> dict:
    b = chess.Board(fen)
    us = b.turn
    st = analyse_structure(b)
    ours = passers(b, us)
    theirs = passers(b, not us)
    def advance(sq):
        r = chess.square_rank(sq)
        return r if us else 7 - r
    best = max((advance(s) for s in ours), default=-1)
    their_best = max((7 - chess.square_rank(s) if us else chess.square_rank(s) for s in theirs), default=-1)
    non_pawn = sum(1 for p in b.piece_map().values() if p.piece_type not in (chess.PAWN, chess.KING))
    our_king = b.king(us)
    their_king = b.king(not us)
    # Distance of the defending king to our most advanced passer's promotion square
    king_dist = None
    if ours:
        sq = max(ours, key=advance)
        promo = chess.square(chess.square_file(sq), 7 if us else 0)
        king_dist = chess.square_distance(their_king, promo)
    mat = sum(v * (len(b.pieces(p, us)) - len(b.pieces(p, not us))) for p, v in VALUES.items())
    return {
        "phase": st.phase, "tags": set(st.tags), "non_pawn": non_pawn, "pieces": len(b.piece_map()),
        "material": mat, "our_passers": len(ours), "our_best_passer_rank": best,
        "their_best_passer_rank": their_best, "def_king_to_promo": king_dist,
        "our_king_centrality": 3 - max(abs(chess.square_file(our_king) - 3.5), abs(chess.square_rank(our_king) - 3.5)) + 0.5,
        "pawn_ending": non_pawn == 0,
        "rook_ending": non_pawn > 0 and all(p.piece_type == chess.ROOK for p in b.piece_map().values() if p.piece_type not in (chess.PAWN, chess.KING)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    blind, seen = [], []
    for g in games:
        for m in g["moves"]:
            if m["mover"] != "base":
                continue
            v = own(m)
            if not 300 <= v < 9000:
                continue
            f = features(m["fen"])
            f["sf"] = v
            f["root"] = m["score_stm"]
            f["static"] = m["base_static"] if m["turn"] == "w" else -m["base_static"]
            f["loss"] = m["cp_loss"]
            f["fen"] = m["fen"]
            (blind if m["score_stm"] < 100 else seen).append(f)
    out = [f"== BLIND WINNING POSITIONS: Stockfish >= +300 for production; root < 100 ('blind', n={len(blind)}) vs root >= 100 ('seen', n={len(seen)}) ==", ""]
    def rate(rows, key):
        return statistics.mean(1.0 if r[key] else 0.0 for r in rows) if rows else 0
    def mean(rows, key):
        vals = [r[key] for r in rows if r[key] is not None]
        return statistics.mean(vals) if vals else float("nan")
    out.append(f"{'feature':<32} {'blind':>10} {'seen':>10}")
    for key in ("pawn_ending", "rook_ending"):
        out.append(f"{key:<32} {rate(blind, key):>10.1%} {rate(seen, key):>10.1%}")
    for key in ("material", "non_pawn", "pieces", "our_passers", "our_best_passer_rank", "their_best_passer_rank", "def_king_to_promo", "our_king_centrality", "static", "root", "sf", "loss"):
        out.append(f"{key:<32} {mean(blind, key):>10.1f} {mean(seen, key):>10.1f}")
    out.append(f"{'serious-error rate':<32} {statistics.mean(r['loss'] >= 100 for r in blind):>10.1%} {statistics.mean(r['loss'] >= 100 for r in seen):>10.1%}")
    out.append(f"{'phase endgame':<32} {rate([{'x': r['phase'] == 'endgame'} for r in blind], 'x'):>10.1%} {rate([{'x': r['phase'] == 'endgame'} for r in seen], 'x'):>10.1%}")
    out.append("")
    out.append("material balance distribution (pawn units, production's side):")
    cb = Counter(max(-3, min(6, r["material"])) for r in blind)
    cs = Counter(max(-3, min(6, r["material"])) for r in seen)
    out.append("  blind: " + ", ".join(f"{k:+d}: {cb[k] / len(blind):.0%}" for k in sorted(cb)))
    out.append("  seen:  " + ", ".join(f"{k:+d}: {cs[k] / len(seen):.0%}" for k in sorted(cs)))
    out.append("")
    out.append("structural tags enriched in blind positions (share blind vs seen, n_blind >= 15):")
    tb = Counter(t for r in blind for t in r["tags"])
    ts = Counter(t for r in seen for t in r["tags"])
    rows = []
    for t in set(tb) | set(ts):
        if tb[t] >= 15:
            rows.append((t, tb[t] / len(blind), ts[t] / len(seen)))
    for t, a, b in sorted(rows, key=lambda r: -(r[1] - r[2])):
        out.append(f"  {t:<28} blind {a:>6.1%}  seen {b:>6.1%}  diff {a - b:>+6.1%}")
    out.append("")
    out.append("blind positions where production is NOT ahead in material (the win is positional/technical):")
    out.append(f"  {sum(1 for r in blind if r['material'] <= 0)}/{len(blind)}  (seen: {sum(1 for r in seen if r['material'] <= 0)}/{len(seen)})")
    out.append("")
    out.append("examples of blind winning positions with the largest Stockfish-vs-root gap:")
    for r in sorted(blind, key=lambda r: -(r["sf"] - r["root"]))[:12]:
        out.append(f"  SF {r['sf']:>+5} root {r['root']:>+5} static {r['static']:>+5} mat {r['material']:+d} passer rank {r['our_best_passer_rank']} loss {r['loss']:>4}  {r['fen']}")
    text = "\n".join(out)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
