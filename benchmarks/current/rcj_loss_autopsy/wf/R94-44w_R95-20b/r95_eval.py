import sys, json
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/wf/R94-44w_R95-20b')
from evalhelp import *
import chess.pgn

FEN = "1r2r1k1/pp3pp1/3b1qp1/2p5/1nP1B3/4N1PP/P2PPP2/RQ3RK1 b - - 0 20"
root = chess.Board(FEN)

def bview(b):  # black-positive
    return -white_static(b)

print("static (black view): root", bview(root), " material W,B", material(root))
for u in ["f6e6", "f6d4"]:
    b = root.copy(); b.push_uci(u)
    h3def = [chess.square_name(s) for s in b.attackers(chess.WHITE, chess.H3)]
    print(f"  after {u}: {bview(b)}  h3 attacked by B: {[chess.square_name(s) for s in b.attackers(chess.BLACK, chess.H3)]} defended by W: {h3def}")

lines = {
    "played PV (SF)": ["f6e6","a2a3","e6e4","b1e4","e8e4","a3b4","c5b4","a1a7"],
    "best PV (SF) + recapture Bxc3": ["f6d4","e4f3","d6e5","b1b3","d4d2","f1d1","d2c3","b3c3","e5c3"],
}
for label, pv in lines.items():
    b, s = play(FEN, pv)
    print(f"\n{label}: {s}")
    print(f"  static(black) {bview(b)}  material W,B {material(b)}  phase {phase_of(b)}")
    print("  B pawns", pawn_feats(b, chess.BLACK), " W pawns", pawn_feats(b, chess.WHITE))
    print("  rooks", rook_report(b))
    ph, terms = piece_terms(b)
    tot_b = sum(t[4] for t in terms if t[0].islower()); tot_w = sum(t[4] for t in terms if t[0].isupper())
    print(f"  tapered PST+material sums: white {tot_w:.0f}, black {-tot_b:.0f}")
    print("  per piece (sym, sq, mg, eg, tapered white-view):")
    for t in terms:
        if t[0].lower() != 'k':
            print("    ", t)

# game positions after the error: static vs SF
bundle = json.load(open('C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/R95-20b.json'))
sf = {m['move_number']: m for m in bundle['all_rcj_moves']}
g = chess.pgn.read_game(open(bundle['pgn_path'].replace('\\', '/')))
b = g.board()
print("\nmove | RC-J static (black) | SF best_cp | played | loss | B pawns | W pawns | material W,B")
for mv in g.mainline_moves():
    if b.turn == chess.BLACK and 17 <= b.fullmove_number <= 45:
        n = b.fullmove_number
        e = sf.get(n, {})
        print(f"{n:>4} | {bview(b):>6} | {e.get('best_cp')!s:>6} | {b.san(mv):>6} | {e.get('loss_cp')!s:>4} | {pawn_feats(b, chess.BLACK)} | {pawn_feats(b, chess.WHITE)} | {material(b)}")
    b.push(mv)

# where did black's b-pawns go?
b = g.board(); ev = []
for mv in g.mainline_moves():
    if b.is_capture(mv):
        cap = b.piece_at(mv.to_square)
        if cap and cap.piece_type == chess.PAWN and not cap.color:
            ev.append(f"{b.fullmove_number}{'.' if b.turn else '...'}{b.san(mv)} takes black pawn {chess.square_name(mv.to_square)}")
    b.push(mv)
print("\nWhite captures of black pawns:", ev)
