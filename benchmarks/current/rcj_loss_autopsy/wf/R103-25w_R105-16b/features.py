"""Read-only feature probe (python-chess + pure-Python reference evaluator; no search)."""
import sys
sys.path.insert(0, "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27")
import chess
import cs_eval
from cs_constants import MG_WHITE, EG_WHITE, MG_BLACK, EG_BLACK, TOTAL_PHASE, BISHOP_PAIR_MG, BISHOP_PAIR_EG, TEMPO

print("active terms at import:", sorted(cs_eval.ACTIVE_TERMS))
cs_eval.set_terms([])  # pure PeSTO+material+bishop pair+tempo (mop-up is 0 in these positions anyway)
print("BISHOP_PAIR mg/eg", BISHOP_PAIR_MG, BISHOP_PAIR_EG, "TEMPO", TEMPO, "TOTAL_PHASE", TOTAL_PHASE)

PH = {chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 1, chess.ROOK: 2, chess.QUEEN: 4, chess.KING: 0}


def phase(b):
    p = sum(PH[pc.piece_type] for pc in b.piece_map().values())
    return min(p, TOTAL_PHASE)


def pst(b, sq, color, pt):
    mg = (MG_WHITE if color else MG_BLACK)[pt][sq]
    eg = (EG_WHITE if color else EG_BLACK)[pt][sq]
    return mg, eg


def tapered(b, mg, eg):
    ph = phase(b)
    return (mg * ph + eg * (TOTAL_PHASE - ph)) / TOTAL_PHASE


def ev(b, pov):
    """evaluate_reference is side-to-move relative; convert to pov colour."""
    s = cs_eval.evaluate_reference(b)
    return s if b.turn == pov else -s


def mob(b, color):
    """pseudo-legal non-pawn moves per piece for colour (turn-independent)."""
    bb = b.copy()
    bb.turn = color
    bb.ep_square = None
    out = {}
    for m in bb.pseudo_legal_moves:
        pc = bb.piece_at(m.from_square)
        if pc.piece_type in (chess.PAWN, chess.KING):
            continue
        k = pc.symbol() + chess.square_name(m.from_square)
        out[k] = out.get(k, 0) + 1
    for sq, pc in bb.piece_map().items():
        if pc.color == color and pc.piece_type not in (chess.PAWN, chess.KING):
            out.setdefault(pc.symbol() + chess.square_name(sq), 0)
    return out


def walk(fen, ucis, pov, label):
    b = chess.Board(fen)
    print(f"--- {label}")
    print(f"  root eval(pov)={ev(b, pov)}")
    for i, u in enumerate(ucis):
        m = chess.Move.from_uci(u)
        san = b.san(m)
        b.push(m)
        wm, bm = mob(b, chess.WHITE), mob(b, chess.BLACK)
        print(f"  ply{i+1} {san:7s} eval(pov)={ev(b, pov):5d} phase={phase(b)} "
              f"mobW={sum(wm.values())} mobB={sum(bm.values())}")
    print("  final W mob:", mob(b, chess.WHITE))
    print("  final B mob:", mob(b, chess.BLACK))
    return b


# ---------------- R103-25w (RC-J = White) ----------------
F1 = "r5k1/4pp1p/3p2pQ/3P4/1q6/r2bPBPP/5PK1/2R1R3 w - - 5 25"
b = chess.Board(F1)
print("\n========== R103-25w  phase", phase(b))
for s in ["h6", "f4", "h4", "d4", "e3"]:
    sq = chess.parse_square(s)
    mg, eg = pst(b, sq, chess.WHITE, chess.QUEEN)
    print(f"  W queen on {s}: mg={mg} eg={eg} tapered={tapered(b, mg, eg):.1f}")
for u in ["e1d1", "h6f4", "h6h4"]:
    bb = b.copy(); bb.push(chess.Move.from_uci(u))
    print(f"  after {u}: eval(White pov)={ev(bb, chess.WHITE)}  mobW={sum(mob(bb, True).values())} mobB={sum(mob(bb, False).values())}")
    print("     W mob", mob(bb, True))
    print("     B mob", mob(bb, False))
walk(F1, ["e1d1", "b4b2", "g3g4", "a3a2", "h6h4", "d3c2", "d1f1", "f7f6"], chess.WHITE, "R103 played PV")
walk(F1, ["h6f4", "b4b2", "f4d4", "b2d4", "e3d4", "a8a7", "c1c8", "g8g7"], chess.WHITE, "R103 best PV")
# the game continuation
walk(F1, ["e1d1", "b4b2", "e3e4", "a3a2", "h6e3", "a8a3", "e3e1"], chess.WHITE, "R103 actual game 25..28")
# Black rooks/queen on White's 2nd rank in played PV end vs best PV end
# black heavy pieces on rank 2:
for label, ucis in [("played", ["e1d1", "b4b2", "g3g4", "a3a2", "h6h4", "d3c2", "d1f1", "f7f6"]),
                    ("best", ["h6f4", "b4b2", "f4d4", "b2d4", "e3d4", "a8a7", "c1c8", "g8g7"])]:
    bb = chess.Board(F1)
    for u in ucis:
        bb.push(chess.Move.from_uci(u))
    inv = [chess.square_name(s) + bb.piece_at(s).symbol() for s in chess.SquareSet(chess.BB_RANK_2)
           if bb.piece_at(s) and bb.piece_at(s).color == chess.BLACK]
    wq = [chess.square_name(s) for s in bb.pieces(chess.QUEEN, chess.WHITE)]
    print(f"  {label} pv_end: black pieces on rank 2: {inv}; white queen: {wq}")

# ---------------- R105-16b (RC-J = Black) ----------------
F2 = "r1bq1r1k/1p1p2bp/p5p1/3Bpp2/N1P5/4Q1P1/PP2PP1P/R4RK1 b - - 3 16"
b = chess.Board(F2)
print("\n========== R105-16b  phase", phase(b))
for u in ["a8b8", "d7d6"]:
    bb = b.copy(); bb.push(chess.Move.from_uci(u))
    print(f"  after {u}: eval(Black pov)={ev(bb, chess.BLACK)}  mobW={sum(mob(bb, True).values())} mobB={sum(mob(bb, False).values())}")
    print("     B mob", mob(bb, False))
    # knight fork squares
    nb6 = chess.Move.from_uci("a4b6")
    print("     Nb6 legal:", nb6 in bb.legal_moves, " Qa7 legal:", chess.Move.from_uci("e3a7") in bb.legal_moves)
walk(F2, ["a8b8", "e3a7", "d8c7", "c4c5", "e5e4", "f1d1", "f5f4", "d5e4"], chess.BLACK, "R105 played PV")
walk(F2, ["d7d6", "a4b6", "a8b8", "b6c8", "b8c8", "b2b4", "e5e4", "a1b1"], chess.BLACK, "R105 best PV")
# bishop-pair cost of the d6 line: position after d6 Nb6 Rb8 Nxc8 Rxc8 vs same with pair notionally kept
bb = chess.Board(F2)
for u in ["d7d6", "a4b6", "a8b8", "b6c8", "b8c8"]:
    bb.push(chess.Move.from_uci(u))
print("  after d6 Nb6 Rb8 Nxc8 Rxc8: eval(Black pov)", ev(bb, chess.BLACK), " phase", phase(bb),
      " bishop-pair tapered value", round(tapered(bb, BISHOP_PAIR_MG, BISHOP_PAIR_EG), 1))
# PST of black bishop c8 vs pieces
for s in ["c8"]:
    mg, eg = pst(b, chess.parse_square(s), chess.BLACK, chess.BISHOP)
    print(f"  B bishop on {s}: mg={mg} eg={eg}")
for s in ["a4", "b6", "c5"]:
    mg, eg = pst(b, chess.parse_square(s), chess.WHITE, chess.KNIGHT)
    print(f"  W knight on {s}: mg={mg} eg={eg}")
for s in ["e3", "a7"]:
    mg, eg = pst(b, chess.parse_square(s), chess.WHITE, chess.QUEEN)
    print(f"  W queen on {s}: mg={mg} eg={eg} tapered={tapered(b, mg, eg):.1f}")
# actual game continuation to move 19
walk(F2, ["a8b8", "e3a7", "d8c7", "a4c5", "f8f6", "a1b1", "e5e4"], chess.BLACK, "R105 actual game 16..19")
