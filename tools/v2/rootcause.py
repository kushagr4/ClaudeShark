"""Root-cause map of the V2 calibration set: which piece of chess knowledge is missing, per trajectory.

For every failure row the position and Stockfish's line are read for the
mechanism behind the disagreement, and the labels are counted by independent
trajectory (source game) rather than by row, so a game that contributed two
positions counts once per mechanism.

Blind wins (Stockfish >= +300, V1 root < +100) are labelled by what the
winning line does: promote, win material, walk the king to the pawns, use
the rook, push a passer, break through in a pawn ending, or mate. False
wins (V1 root >= +200, Stockfish level) are labelled by what makes the
position drawn: a passer the defending king holds, a rook ending with an
extra pawn, opposite-coloured bishops, a wrong rook pawn, the defending
king already among the pawns, the "extra" being a piece-square illusion, or
insufficient mating material.

    uv run python -m tools.v2.rootcause --suite corpus/v2/endgame_calibration_v1.jsonl --out corpus/v2/02_rootcause.txt
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import chess

from cs_passed import passed_pawn_mask

MECHANISMS = ("king activity", "king-to-pawn coordination", "passed pawn", "blocked/stoppable passer",
              "pawn breakthrough", "opposition", "pawn race / tempo", "rook activity",
              "rook + passer coordination", "extra-pawn conversion", "mating gradient", "tactical/horizon",
              "opposite bishops / fortress", "wrong rook pawn", "PST illusion", "other")


def cheb(a: int, b: int) -> int:
    return max(abs(chess.square_file(a) - chess.square_file(b)), abs(chess.square_rank(a) - chess.square_rank(b)))


def rel_rank(sq: int, white: bool) -> int:
    return chess.square_rank(sq) if white else 7 - chess.square_rank(sq)


def walk(fen: str, pv: list[str]) -> dict:
    """What the line does: counts by mover for the side to move at the root."""
    board = chess.Board(fen)
    us = board.turn
    out = {"our_king_moves": 0, "our_rook_moves": 0, "our_pawn_moves": 0, "our_passer_pushes": 0, "promotions": 0,
           "captures_by_us": 0, "material_gain": 0, "checks_by_us": 0, "king_closer_to_pawns": 0, "plies": 0,
           "mate": False}
    king0 = board.king(us)
    pawns0 = board.pawns & ~board.occupied_co[us]
    d0 = min((cheb(king0, p) for p in chess.scan_forward(pawns0)), default=8) if king0 is not None else 8
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    for uci in pv:
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            break
        if move not in board.legal_moves:
            break
        mover = board.turn
        piece = board.piece_type_at(move.from_square)
        captured = board.piece_type_at(move.to_square)
        if board.is_en_passant(move):
            captured = chess.PAWN
        if mover == us:
            out["plies"] += 1
            if piece == chess.KING:
                out["our_king_moves"] += 1
            elif piece == chess.ROOK:
                out["our_rook_moves"] += 1
            elif piece == chess.PAWN:
                out["our_pawn_moves"] += 1
                if passed_pawn_mask(board, us) & (1 << move.from_square):
                    out["our_passer_pushes"] += 1
            if move.promotion:
                out["promotions"] += 1
            if captured:
                out["captures_by_us"] += 1
                out["material_gain"] += values.get(captured, 0)
            if board.gives_check(move):
                out["checks_by_us"] += 1
        elif captured:
            out["material_gain"] -= values.get(captured, 0)
        board.push(move)
        if board.is_checkmate():
            out["mate"] = True
    king1 = board.king(us)
    pawns1 = board.pawns & ~board.occupied_co[us]
    d1 = min((cheb(king1, p) for p in chess.scan_forward(pawns1)), default=8) if king1 is not None else 8
    out["king_closer_to_pawns"] = d0 - d1
    return out


def blind_mechanism(r: dict) -> str:
    board = chess.Board(r["fen"])
    us = board.turn
    them = not us
    w = walk(r["fen"], r.get("sf_pv") or r.get("pv_at_source") or [])
    ours = passed_pawn_mask(board, us)
    theirs = passed_pawn_mask(board, them)
    our_pieces = (board.occupied_co[us] & ~board.pawns & ~board.kings).bit_count()
    their_pieces = (board.occupied_co[them] & ~board.pawns & ~board.kings).bit_count()
    pawn_ending = our_pieces == 0 and their_pieces == 0
    if r.get("sf_mate") is not None or w["mate"]:
        return "mating gradient"
    if w["material_gain"] >= 3 or (w["captures_by_us"] >= 2 and w["material_gain"] >= 2):
        return "tactical/horizon"
    if w["promotions"] and (theirs or w["plies"] <= 4):
        return "pawn race / tempo"
    if w["promotions"] or (ours and w["our_passer_pushes"] >= 2):
        return "passed pawn"
    if pawn_ending and w["our_pawn_moves"] >= max(2, w["plies"] // 2) and w["our_king_moves"] <= 1:
        return "pawn breakthrough"
    if pawn_ending and w["our_king_moves"] >= 2 and w["king_closer_to_pawns"] <= 0 and w["our_pawn_moves"] <= 1:
        return "opposition"
    if w["our_king_moves"] >= 2 and w["king_closer_to_pawns"] >= 1:
        return "king-to-pawn coordination"
    if w["our_king_moves"] >= 2:
        return "king activity"
    if w["our_rook_moves"] >= 2 and ours:
        return "rook + passer coordination"
    if w["our_rook_moves"] >= 2:
        return "rook activity"
    if w["material_gain"] >= 1:
        return "extra-pawn conversion"
    return "other"


def false_mechanism(r: dict) -> str:
    board = chess.Board(r["fen"])
    us = board.turn
    them = not us
    ours = passed_pawn_mask(board, us)
    our_pieces = (board.occupied_co[us] & ~board.pawns & ~board.kings).bit_count()
    their_pieces = (board.occupied_co[them] & ~board.pawns & ~board.kings).bit_count()
    their_king = board.king(them)
    our_king = board.king(us)
    material = r["material_stm"]
    bishops_only = (board.queens | board.rooks | board.knights) == 0 and board.bishops
    if not board.pawns and material > 0:
        return "mating gradient"
    if bishops_only and board.pieces(chess.BISHOP, us) and board.pieces(chess.BISHOP, them):
        ours_light = bool(board.pieces(chess.BISHOP, us) & chess.BB_LIGHT_SQUARES)
        theirs_light = bool(board.pieces(chess.BISHOP, them) & chess.BB_LIGHT_SQUARES)
        if ours_light != theirs_light:
            return "opposite bishops / fortress"
    if ours and their_king is not None:
        for sq in chess.scan_forward(ours):
            promo = chess.square(chess.square_file(sq), 7 if us else 0)
            if chess.square_file(sq) in (0, 7) and cheb(their_king, promo) <= 1 and our_pieces <= 1:
                return "wrong rook pawn"
            steps = 7 - rel_rank(sq, us)
            if cheb(their_king, promo) <= steps and our_pieces == 0:
                return "blocked/stoppable passer"
            front = chess.square(chess.square_file(sq), chess.square_rank(sq) + (1 if us else -1))
            piece = board.piece_at(front)
            if piece is not None and piece.color == them:
                return "blocked/stoppable passer"
    rook_ending = (board.queens | board.bishops | board.knights) == 0 and board.rooks
    if rook_ending and material >= 1:
        return "extra-pawn conversion"
    if our_pieces == 0 and their_pieces == 0 and material >= 1:
        return "opposition"
    if material >= 1:
        return "extra-pawn conversion"
    if their_king is not None and our_king is not None:
        pawns = list(chess.scan_forward(board.pawns))
        if pawns and min(cheb(their_king, p) for p in pawns) <= min(cheb(our_king, p) for p in pawns):
            return "king activity"
    return "PST illusion"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    rows = [json.loads(line) for line in arguments.suite.open(encoding="utf-8")]
    header, rows = rows[0], rows[1:]
    for r in rows:
        if r["class"] == "blind_win":
            r["mechanism"] = blind_mechanism(r)
        elif r["class"] == "false_win":
            r["mechanism"] = false_mechanism(r)
        else:
            r["mechanism"] = None
    lines = [f"== ROOT-CAUSE MAP, V2 calibration set {header['hash']} ==",
             "counts are independent trajectories (source games); a trajectory with two rows of one mechanism counts once", ""]
    for cls in ("blind_win", "false_win"):
        rs = [r for r in rows if r["class"] == cls]
        traj = defaultdict(set)
        for r in rs:
            traj[r["mechanism"]].add(r["trajectory"])
        total_traj = len({r["trajectory"] for r in rs})
        lines.append(f"-- {cls}: {len(rs)} rows, {total_traj} trajectories")
        lines.append(f"   {'mechanism':<30} {'traj':>5} {'rows':>5} {'share':>6} {'mean SF':>8} {'mean V1 root':>13} {'mean V1 static':>15} {'pawn end':>8} {'rook end':>8}")
        for mech, ts in sorted(traj.items(), key=lambda kv: -len(kv[1])):
            mr = [r for r in rs if r["mechanism"] == mech]
            lines.append(f"   {mech:<30} {len(ts):>5} {len(mr):>5} {len(ts) / total_traj:>6.0%} "
                         f"{sum(min(max(r['sf_cp'], -2000), 2000) for r in mr) / len(mr):>+8.0f} {sum(r['v1_root'] for r in mr) / len(mr):>+13.0f} {sum(r['v1_static'] for r in mr) / len(mr):>+15.0f} "
                         f"{sum(r['pawn_ending'] for r in mr) / len(mr):>8.0%} {sum(r['rook_ending'] for r in mr) / len(mr):>8.0%}")
        lines.append("")
    lines.append("-- king geometry, failure classes vs recognised classes (means; distance = Chebyshev to nearest pawn of either colour)")
    lines.append(f"   {'class':<16} {'n':>4} {'our K->pawn':>11} {'their K->pawn':>13} {'our centre':>10} {'their centre':>12} {'material':>8} {'own passers':>11} {'their passers':>13}")
    for cls in ("blind_win", "false_win", "recognised_win", "recognised_draw", "losing"):
        rs = [r for r in rows if r["class"] == cls]
        if not rs:
            continue
        lines.append(f"   {cls:<16} {len(rs):>4} {sum(r['our_king_to_nearest_pawn'] for r in rs) / len(rs):>11.2f} {sum(r['their_king_to_nearest_pawn'] for r in rs) / len(rs):>13.2f} "
                     f"{sum(r['our_king_centre'] for r in rs) / len(rs):>10.2f} {sum(r['their_king_centre'] for r in rs) / len(rs):>12.2f} {sum(r['material_stm'] for r in rs) / len(rs):>+8.2f} "
                     f"{sum(r['our_passers'] for r in rs) / len(rs):>11.2f} {sum(r['their_passers'] for r in rs) / len(rs):>13.2f}")
    lines.append("")
    lines.append("-- examples, largest disagreement per mechanism")
    for cls in ("blind_win", "false_win"):
        rs = [r for r in rows if r["class"] == cls]
        by = defaultdict(list)
        for r in rs:
            by[r["mechanism"]].append(r)
        for mech, mr in sorted(by.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"   {cls} / {mech}")
            for r in sorted(mr, key=lambda r: -abs(min(max(r["sf_cp"], -2000), 2000) - r["v1_root"]))[:3]:
                lines.append(f"      {r['id']} {r['trajectory']:<22} SF {r['sf_cp']:>+5} best {r['sf_best']:<6} V1 static {r['v1_static']:>+5} qs {r['v1_qs']:>+5} root {r['v1_root']:>+5} ({r['v1_move']})  {r['signature']:<12} {r['fen']}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
