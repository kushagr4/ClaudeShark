"""Mechanism, attribution and candidate-feature screen for the false-win corpus.

Every row gets a mechanism label (read off the material and the geometry),
an attribution of where the wrong score comes from (material value, piece
geometry, king position, search, or a combination) from the decomposition
of V2.1's static, and a set of candidate offline features that say whether
a given rule would fire on it. Counts are by independent trajectory.
Controls -- genuinely winning positions with the same material family --
are read from the calibration runs and the Gate 2 games, and every
candidate feature is also fired on them: a feature that fires on the wins
it must not touch is a false positive.

    uv run python -m tools.v2.fwmech --corpus corpus/v2/fw/falsewin_corpus_v1.jsonl --out corpus/v2/fw/03_mechanisms.txt
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import chess

from cs_passed import passed_pawn_mask
from tools.v2.calibration import signature

MINORS = {chess.BISHOP, chess.KNIGHT}


def cheb(a: int, b: int) -> int:
    return max(abs(chess.square_file(a) - chess.square_file(b)), abs(chess.square_rank(a) - chess.square_rank(b)))


def material_family(board: chess.Board, us: bool) -> str:
    """A coarse family: what the stronger side has beyond the weaker side, ignoring which colour."""
    def counts(colour: bool) -> dict[int, int]:
        return {pt: len(board.pieces(pt, colour)) for pt in chess.PIECE_TYPES}
    a, b = counts(us), counts(not us)
    non_pawn = lambda c: c[chess.QUEEN] * 9 + c[chess.ROOK] * 5 + (c[chess.BISHOP] + c[chess.KNIGHT]) * 3  # noqa: E731
    if non_pawn(a) < non_pawn(b) or (non_pawn(a) == non_pawn(b) and a[chess.PAWN] < b[chess.PAWN]):
        a, b = b, a
    pieces_a = "".join(k * n for k, n in (("Q", a[chess.QUEEN]), ("R", a[chess.ROOK]), ("B", a[chess.BISHOP]), ("N", a[chess.KNIGHT])))
    pieces_b = "".join(k * n for k, n in (("Q", b[chess.QUEEN]), ("R", b[chess.ROOK]), ("B", b[chess.BISHOP]), ("N", b[chess.KNIGHT])))
    return f"K{pieces_a}+{a[chess.PAWN]}P v K{pieces_b}+{b[chess.PAWN]}P"


def geometry(board: chess.Board, us: bool) -> dict:
    them = not us
    our_pieces = board.occupied_co[us] & ~board.pawns & ~board.kings
    their_pieces = board.occupied_co[them] & ~board.pawns & ~board.kings
    our_passers = passed_pawn_mask(board, us)
    their_king = board.king(them)
    our_king = board.king(us)
    ours_bishops = board.pieces_mask(chess.BISHOP, us)
    theirs_bishops = board.pieces_mask(chess.BISHOP, them)
    g = {
        "pawnless": board.pawns == 0,
        "our_pawns": len(board.pieces(chess.PAWN, us)), "their_pawns": len(board.pieces(chess.PAWN, them)),
        "our_non_pawn": our_pieces.bit_count(), "their_non_pawn": their_pieces.bit_count(),
        "opposite_bishops": bool(ours_bishops) and bool(theirs_bishops) and (board.queens | board.rooks | board.knights) == 0
        and bool(ours_bishops & chess.BB_LIGHT_SQUARES) != bool(theirs_bishops & chess.BB_LIGHT_SQUARES),
        "wrong_rook_pawn": False, "defender_king_in_front": False, "all_passers_blockaded": False, "rook_pawn_only": False,
        "their_king_to_our_passer_promo": None,
    }
    # Wrong rook pawn: our only pawn(s) are rook pawns, our only piece is a bishop that does not control the corner,
    # and the defending king is within one square of that corner (or can reach it before us, approximated by distance <= 2).
    our_pawn_squares = list(board.pieces(chess.PAWN, us))
    files = {chess.square_file(s) for s in our_pawn_squares}
    if our_pawn_squares and files <= {0, 7} and their_king is not None:
        g["rook_pawn_only"] = True
        corners = {chess.square(f, 7 if us else 0) for f in files}
        pieces_ok = our_pieces == ours_bishops and ours_bishops.bit_count() <= 1
        if pieces_ok:
            for corner in corners:
                corner_light = bool(chess.BB_SQUARES[corner] & chess.BB_LIGHT_SQUARES)
                bishop_light = bool(ours_bishops & chess.BB_LIGHT_SQUARES) if ours_bishops else None
                if (ours_bishops == 0 or bishop_light != corner_light) and cheb(their_king, corner) <= 2 and (our_king is None or cheb(their_king, corner) <= cheb(our_king, corner)):
                    g["wrong_rook_pawn"] = True
    # Defender king in front of our passers / all passers blockaded.
    if our_passers:
        blockaded = 0
        promo_dists = []
        for sq in chess.scan_forward(our_passers):
            front = chess.square(chess.square_file(sq), chess.square_rank(sq) + (1 if us else -1))
            piece = board.piece_at(front) if 0 <= front < 64 else None
            promo = chess.square(chess.square_file(sq), 7 if us else 0)
            if their_king is not None:
                promo_dists.append(cheb(their_king, promo))
                if (piece is not None and piece.color == them) or cheb(their_king, promo) <= 1 or (their_king == front):
                    blockaded += 1
        g["all_passers_blockaded"] = blockaded == our_passers.bit_count()
        g["defender_king_in_front"] = their_king is not None and any(
            chess.square_file(their_king) == chess.square_file(sq) and ((chess.square_rank(their_king) > chess.square_rank(sq)) == us)
            for sq in chess.scan_forward(our_passers))
        g["their_king_to_our_passer_promo"] = min(promo_dists) if promo_dists else None
    return g


def mechanism(row: dict, g: dict) -> str:
    board = chess.Board(row["fen"])
    us = board.turn
    fam = material_family(board, us)
    if row["v21_static"] < 100 and row["v21_root"] >= 150:
        return "search/horizon rather than static"
    if g["pawnless"]:
        if fam.startswith("KRB+0P v KR") or fam.startswith("KRN+0P v KR"):
            return "rook + minor vs rook"
        if fam in ("KB+0P v K+0P", "KN+0P v K+0P") or fam.startswith("KB+0P v KR") or fam.startswith("KN+0P v KR") or fam.startswith("KR+0P v KB") or fam.startswith("KR+0P v KN"):
            return "insufficient / effectively drawn material"
        return "pawnless low-material ending"
    if g["wrong_rook_pawn"]:
        return "wrong rook pawn"
    if g["opposite_bishops"]:
        return "opposite-coloured bishops"
    if g["our_non_pawn"] == 0 and g["their_non_pawn"] == 0 and g["all_passers_blockaded"]:
        return "defender king blockade (pawn ending)"
    if g["all_passers_blockaded"] and row["material_stm"] >= 1:
        return "extra pawn but blockaded"
    if board.queens and (board.occupied & ~board.pawns & ~board.kings & ~board.queens) == 0:
        return "queen perpetual resources"
    rooks_only = (board.queens | board.bishops | board.knights) == 0 and board.rooks
    if rooks_only and row["material_stm"] >= 1:
        return "rook ending, extra pawn(s) not enough"
    if row["material_stm"] <= 0:
        return "no material edge: geometry over-credited"
    if fam.endswith("v K+0P") and g["their_non_pawn"] == 0 and g["our_non_pawn"] <= 1 and g["our_pawns"] <= 1:
        return "insufficient / effectively drawn material"
    return "other"


def attribution(row: dict) -> str:
    d = row["decomposition_stm"]
    static, root = row["v21_static"], row["v21_root"]
    if static < 100 and root >= 150:
        return "D search"
    material, pst, kp = d["material"], d["pst"], d["king_pawn"]
    parts = {"A material": material, "B piece geometry (tables)": pst, "C king position (king-pawn term)": kp}
    top = max(parts, key=lambda k: parts[k])
    if parts[top] >= 0.7 * max(1, static):
        return top
    if material >= 100 and pst >= 100:
        return "E combination (material + tables)"
    return "E combination"


def candidate_features(board: chess.Board, us: bool, g: dict, row: dict) -> dict[str, bool]:
    fam = material_family(board, us)
    rooks_only = (board.queens | board.bishops | board.knights) == 0 and bool(board.rooks)
    return {
        "material_signature_draw_scaling (pawnless, edge <= minor)": g["pawnless"] and row["material_stm"] > 0 and row["material_stm"] <= 3,
        "rook_plus_minor_vs_rook": g["pawnless"] and (fam.startswith("KRB+0P v KR") or fam.startswith("KRN+0P v KR")),
        "wrong_rook_pawn_exact": g["wrong_rook_pawn"],
        "opposite_bishop_scaling": g["opposite_bishops"],
        "low_material_conversion_scaling (<=1 pawn edge, no pieces up)": row["material_stm"] in (1,) and g["our_non_pawn"] == g["their_non_pawn"],
        "defender_king_blockade (all passers held)": bool(passed_pawn_mask(board, us)) and g["all_passers_blockaded"],
        "insufficient_winning_material (minor or lone pawn vs bare)": fam in ("KB+0P v K+0P", "KN+0P v K+0P", "KB+1P v K+0P", "KN+1P v K+0P", "K+1P v K+0P"),
        "rook_ending_pawn_up_scaling": rooks_only and row["material_stm"] == 1,
    }


def load_controls() -> list[dict]:
    """Genuinely winning positions (Stockfish >= +300) with V2.1's root, from the calibration runs and Gate 2 games."""
    out = []

    def read(path: str) -> list[dict]:
        with Path(path).open(encoding="utf-8") as fh:
            return [json.loads(line) for line in fh]

    for path in ("corpus/v2/kp/04_validation_candidate.jsonl", "corpus/v2/kp/sweep_MEDIUM_calibration.jsonl"):
        for r in read(path):
            if r["sf_cp"] >= 300 and r["class"] in ("recognised_win", "blind_win"):
                out.append({"fen": r["fen"], "trajectory": r["trajectory"], "sf": r["sf_cp"], "root": r["root"], "static": r["static"]})
    for source, path in (("gate2_v1", "corpus/v2/kp/games/gate2_annotated.jsonl"), ("gate2_passed", "corpus/v2/kp/games/secondary_vs_passed_annotated.jsonl")):
        for g in read(path):
            for m in g["moves"]:
                if m["mover"] != "cand" or m.get("sf_cp_white_before") is None:
                    continue
                white = m["turn"] == "w"
                sf = m["sf_cp_white_before"] if white else -m["sf_cp_white_before"]
                if 300 <= sf < 5000:
                    st = m["cand_static"] if white else -m["cand_static"]
                    out.append({"fen": m["fen"], "trajectory": f"{source}:{g['cluster']}:{'cW' if g['cand_white'] else 'cB'}", "sf": sf, "root": m["score_stm"], "static": st})
    seen = {}
    for r in out:
        seen.setdefault(r["fen"], r)
    return list(seen.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    rows = [json.loads(line) for line in arguments.corpus.open(encoding="utf-8")][1:]
    for r in rows:
        board = chess.Board(r["fen"])
        us = board.turn
        g = geometry(board, us)
        r["geometry"] = g
        r["family"] = material_family(board, us)
        r["mechanism"] = mechanism(r, g)
        r["attribution"] = attribution(r)
        r["features"] = candidate_features(board, us, g, r)
    traj = defaultdict(list)
    for r in rows:
        traj[r["trajectory"]].append(r)
    n_traj = len(traj)
    lines = [f"== FALSE-WIN MECHANISMS: {len(rows)} rows, {n_traj} trajectories (counts by trajectory; a trajectory counts once per label) ==", ""]

    def by_traj(key):
        c: dict[str, set] = defaultdict(set)
        for r in rows:
            c[r[key]].add(r["trajectory"])
        return sorted(((k, len(v)) for k, v in c.items()), key=lambda kv: -kv[1])
    lines.append("-- mechanism")
    for k, n in by_traj("mechanism"):
        rs = [r for r in rows if r["mechanism"] == k]
        lines.append(f"   {k:<44} {n:>3} traj {len(rs):>3} rows  V2.1 static {sum(r['v21_static'] for r in rs) / len(rs):>+5.0f} root {sum(r['v21_root'] for r in rs) / len(rs):>+5.0f}  V1 root {sum(r['v1_root'] for r in rs) / len(rs):>+5.0f}  pawnless {sum(r['geometry']['pawnless'] for r in rs)}")
    lines.append("")
    lines.append("-- attribution (where V2.1's static score comes from)")
    for k, n in by_traj("attribution"):
        rs = [r for r in rows if r["attribution"] == k]
        means = {key: sum(r["decomposition_stm"][key] for r in rs) / len(rs) for key in ("material", "pst", "king_pawn")}
        lines.append(f"   {k:<44} {n:>3} traj {len(rs):>3} rows  material {means['material']:>+5.0f} tables {means['pst']:>+5.0f} king-pawn {means['king_pawn']:>+4.0f}  static {sum(r['v21_static'] for r in rs) / len(rs):>+5.0f} root {sum(r['v21_root'] for r in rs) / len(rs):>+5.0f}")
    lines.append("")
    lines.append("-- mechanism x attribution (trajectories)")
    cross: dict[tuple, set] = defaultdict(set)
    for r in rows:
        cross[(r["mechanism"], r["attribution"])].add(r["trajectory"])
    for (m, a), ts in sorted(cross.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"   {m:<44} {a:<36} {len(ts):>3}")
    lines.append("")
    lines.append("-- material family (trajectories)")
    fam: dict[str, set] = defaultdict(set)
    for r in rows:
        fam[r["family"]].add(r["trajectory"])
    for k, ts in sorted(fam.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"   {k:<24} {len(ts):>3}")
    lines.append("")
    lines.append("-- pawnless rows")
    for r in [r for r in rows if r["geometry"]["pawnless"]]:
        d = r["decomposition_stm"]
        lines.append(f"   {r['id']} {r['signature']:<12} SF {r['sf_cp']:>+4}  V1 {r['v1_static']:>+4}/{r['v1_root']:>+4}  V2.1 {r['v21_static']:>+4}/{r['v21_root']:>+4}  material {d['material']:>+4} tables {d['pst']:>+4}  {r['mechanism']}  {r['fen']}")
    lines.append("")

    controls = load_controls()
    for c in controls:
        board = chess.Board(c["fen"])
        us = board.turn
        g = geometry(board, us)
        fake = {"material_stm": None, "signature": signature(board)}
        st = 0
        # material from the side to move, coarse
        vals = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
        st = sum(vals[p.piece_type] * (1 if p.color == us else -1) for p in board.piece_map().values() if p.piece_type != chess.KING)
        fake["material_stm"] = st
        c["features"] = candidate_features(board, us, g, fake)
        c["family"] = material_family(board, us)
    lines.append(f"== CANDIDATE FEATURE SCREEN: false-win trajectories reached vs genuine-win controls reached ({len(controls)} control positions, {len({c['trajectory'] for c in controls})} trajectories, Stockfish >= +300, V2.1 root) ==")
    lines.append(f"   {'feature':<64} {'FW traj':>7} {'FW rows':>7} {'FW static':>9} {'ctrl traj':>9} {'ctrl rows':>9} {'ctrl root':>9}")
    names = list(rows[0]["features"])
    for name in names:
        fw = [r for r in rows if r["features"][name]]
        ct = [c for c in controls if c["features"][name]]
        lines.append(f"   {name:<64} {len({r['trajectory'] for r in fw}):>7} {len(fw):>7} {sum(r['v21_static'] for r in fw) / len(fw) if fw else 0:>+9.0f} "
                     f"{len({c['trajectory'] for c in ct}):>9} {len(ct):>9} {sum(c['root'] for c in ct) / len(ct) if ct else 0:>+9.0f}")
    lines.append("")
    lines.append("-- control positions by family, with the share V2.1 scores >= +300 at the root")
    cf: dict[str, list] = defaultdict(list)
    for c in controls:
        cf[c["family"]].append(c)
    for k, cs in sorted(cf.items(), key=lambda kv: -len(kv[1]))[:20]:
        lines.append(f"   {k:<24} {len(cs):>4} rows  SF {sum(c['sf'] for c in cs) / len(cs):>+6.0f}  V2.1 root {sum(c['root'] for c in cs) / len(cs):>+6.0f}  root >= 300: {sum(c['root'] >= 300 for c in cs) / len(cs):.0%}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    (arguments.out.parent / "controls.jsonl").write_text("\n".join(json.dumps(c) for c in controls) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
