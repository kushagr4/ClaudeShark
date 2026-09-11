"""Evidence dossier for each decisive position: what distinguishes the played line
from Stockfish's best line, measured rather than asserted. No engine search.

For the position after the played move and after the best move, and at the end of
each Stockfish PV (<= 8 plies, from the isolated scan), from RC-J's point of view:
  * material (P1 N3 B3 R5 Q9) and the material swing along each PV -> separates a
    tactical refutation (material changes hands within the line) from a quiet,
    positional one (it does not);
  * king-zone pressure: enemy attacks on the king's zone, and pawn-shield count;
  * mobility: pseudo-legal move counts for each side;
  * pawn structure: isolated, doubled, passed pawns and the most advanced passer;
  * RC-J's own static evaluation (PeSTO + bishop pair + tempo, interpreted twin of
    the shipped C5 evaluator) and, as counterfactuals only, the value of each
    UNSHIPPED registry term (king_safety, passed, king_pawn, low_material): does that
    term prefer the best line's endpoint to the played line's, and by how much?
"""
import json, sys
C27 = "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27"
sys.path.insert(0, C27)
import chess, cs_eval, cs_terms
VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}

def material(b, side):
    return sum(VAL[p.piece_type] * (1 if p.color == side else -1) for p in b.piece_map().values() if p.piece_type in VAL)

def king_zone(b, side):
    k = b.king(side)
    if k is None: return dict(attacks=0, shield=0)
    zone = chess.SquareSet(chess.BB_KING_ATTACKS[k]) | chess.SquareSet.from_square(k)
    attacks = sum(len(b.attackers(not side, sq)) for sq in zone)
    f, r = chess.square_file(k), chess.square_rank(k)
    step = 1 if side == chess.WHITE else -1
    shield = sum(1 for df in (-1, 0, 1) for dr in (1, 2)
                 if 0 <= f + df < 8 and 0 <= r + step * dr < 8
                 and b.piece_at(chess.square(f + df, r + step * dr)) == chess.Piece(chess.PAWN, side))
    return dict(attacks=attacks, shield=shield)

def mobility(b, side):
    c = b.copy(stack=False); c.turn = side
    return sum(1 for m in c.pseudo_legal_moves if c.piece_type_at(m.from_square) != chess.PAWN)

def pawns(b, side):
    own = b.pieces(chess.PAWN, side); opp = b.pieces(chess.PAWN, not side)
    files = [chess.square_file(s) for s in own]
    iso = sum(1 for s in own if not any(abs(chess.square_file(s) - f) == 1 for f in files))
    dbl = len(files) - len(set(files))
    passed, best = 0, 0
    for s in own:
        f, r = chess.square_file(s), chess.square_rank(s)
        ahead = [t for t in opp if abs(chess.square_file(t) - f) <= 1 and
                 ((chess.square_rank(t) > r) if side == chess.WHITE else (chess.square_rank(t) < r))]
        if not ahead:
            passed += 1; best = max(best, r if side == chess.WHITE else 7 - r)
    return dict(isolated=iso, doubled=dbl, passed=passed, best_passer_rank=best)

def features(b, side):
    return dict(material=material(b, side), king_own=king_zone(b, side), king_opp=king_zone(b, not side),
                mob_own=mobility(b, side), mob_opp=mobility(b, not side),
                pawns_own=pawns(b, side), pawns_opp=pawns(b, not side))

def static(b, side):
    """RC-J PeSTO static eval from `side`'s view, plus each unshipped term (White's view -> side's view)."""
    cs_eval.set_terms(())
    base = cs_eval.evaluate(b); base = base if b.turn == side else -base
    terms = {}
    for t in cs_terms.TERMS:
        v = t.reference(b)
        if t.stage == "packed":
            mg, eg = v
            ph = min(24, (len(b.pieces(chess.KNIGHT, 1)) + len(b.pieces(chess.KNIGHT, 0)) + len(b.pieces(chess.BISHOP, 1))
                         + len(b.pieces(chess.BISHOP, 0)) + 2 * (len(b.pieces(chess.ROOK, 1)) + len(b.pieces(chess.ROOK, 0)))
                         + 4 * (len(b.pieces(chess.QUEEN, 1)) + len(b.pieces(chess.QUEEN, 0)))))
            v = (mg * ph + eg * (24 - ph)) // 24
        terms[t.name] = v if side == chess.WHITE else -v
    return base, terms

def line(fen, pv, side):
    b = chess.Board(fen); mats = [material(b, side)]; pts = []
    for i, u in enumerate(pv[:8]):
        m = chess.Move.from_uci(u)
        if m not in b.legal_moves: break
        b.push(m); mats.append(material(b, side))
        if i == 0: pts.append(("after_move", b.copy()))
    pts.append(("pv_end", b.copy()))
    out = dict(material_path=mats, swing=mats[-1] - mats[0], plies=len(mats) - 1)
    for name, pb in pts:
        base, terms = static(pb, side)
        out[name] = dict(features=features(pb, side), rcj_static=base, unshipped_terms=terms)
    return out

def main():
    dec = json.load(open(sys.argv[1], encoding="utf-8")); res = []
    for g in dec:
        d = g["decisive"]; side = chess.WHITE if d["side"] == "white" else chess.BLACK
        rec = dict(round=g["round"], move_number=d["move_number"], san=d["san"], played=d["played"], best=d["best"],
                   loss_cp=d["loss_cp"], fen=d["fen"], played_line=line(d["fen"], d["played_pv"], side),
                   best_line=line(d["fen"], d["best_pv"], side))
        for where in ("after_move", "pv_end"):
            p, q = rec["played_line"][where], rec["best_line"][where]
            rec[f"term_pref_best_minus_played_{where}"] = {k: q["unshipped_terms"][k] - p["unshipped_terms"][k] for k in q["unshipped_terms"]}
            rec[f"rcj_static_best_minus_played_{where}"] = q["rcj_static"] - p["rcj_static"]
        res.append(rec)
        print(f"R{g['round']} m{d['move_number']} {d['san']}: swing played {rec['played_line']['swing']:+d} best {rec['best_line']['swing']:+d} | "
              f"RC-J static best-played after_move {rec['rcj_static_best_minus_played_after_move']:+d} pv_end {rec['rcj_static_best_minus_played_pv_end']:+d} | "
              f"terms@pv_end {rec['term_pref_best_minus_played_pv_end']}", flush=True)
    json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
main()
