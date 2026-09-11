import sys, json
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/wf/R94-44w_R95-20b')
from evalhelp import *
import chess.pgn

FEN = "8/1r2pk2/p2p4/P2P1p2/P1p3p1/2P3P1/rb1B1PK1/1R1R4 w - - 4 44"
root = chess.Board(FEN)
ph = phase_of(root)
print("phase", ph, "/", TOTAL_PHASE)
print("files:", {chess.FILE_NAMES[f]: file_state(root, f) for f in range(8)})

# PST cost of each candidate move (moving piece only), tapered, white view
for name, pt, a, bsq in [("rook d1->h1", chess.ROOK, chess.D1, chess.H1), ("bishop d2->c1", chess.BISHOP, chess.D2, chess.C1)]:
    dmg = MG_WHITE[pt][bsq] - MG_WHITE[pt][a]
    deg = EG_WHITE[pt][bsq] - EG_WHITE[pt][a]
    print(f"PST {name}: mg {MG_WHITE[pt][a]}->{MG_WHITE[pt][bsq]} (d{dmg}), eg {EG_WHITE[pt][a]}->{EG_WHITE[pt][bsq]} (d{deg}), tapered d{taper(dmg, deg, ph):.1f}")
print("rook mg PST rank 1 a..h:", [MG_WHITE[chess.ROOK][s] for s in range(8)])
print("rook eg PST rank 1 a..h:", [EG_WHITE[chess.ROOK][s] for s in range(8)])

print("\nstatic (white view): root", white_static(root))
for u in ["d2c1", "d1h1"]:
    b = root.copy(); b.push_uci(u)
    print(f"  after {u}: {white_static(b)}   rooks {rook_report(b)}")

for label, pv in [("SF best PV", ["d1h1","f7f6","b1e1","b2a1","e1e6","f6f7","d2e1","a2c2"]),
                  ("SF played PV", ["d2c1","f7f6","d1e1","b7b3","c1d2","b2a1","e1e6","f6f7"])]:
    b, s = play(FEN, pv)
    print(f"\n{label}: {s}\n  static(white) {white_static(b)}  rooks {rook_report(b)}")
    print("  W pawns", pawn_feats(b, chess.WHITE), " B pawns", pawn_feats(b, chess.BLACK))

# game continuation: static eval vs SF best_cp at every RC-J (white) move 44..56
bundle = json.load(open('C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/R94-44w.json'))
sf = {m['move_number']: m for m in bundle['all_rcj_moves']}
g = chess.pgn.read_game(open(bundle['pgn_path'].replace('\\', '/')))
b = g.board()
print("\nmove | RC-J static (white) | SF best_cp | played | loss | W pawns | B king sq | material W,B")
for mv in g.mainline_moves():
    if b.turn == chess.WHITE and 42 <= b.fullmove_number <= 56:
        n = b.fullmove_number
        e = sf.get(n, {})
        bk = chess.square_name(b.king(chess.BLACK))
        print(f"{n:>4} | {white_static(b):>6} | {e.get('best_cp')!s:>6} | {b.san(mv):>6} | {e.get('loss_cp')!s:>4} | {pawn_feats(b, chess.WHITE)} | {bk} | {material(b)}")
    b.push(mv)

# rook shuffle count 33..43
b = g.board(); shuffles = []
for mv in g.mainline_moves():
    if b.turn == chess.WHITE and 33 <= b.fullmove_number <= 44 and b.piece_type_at(mv.from_square) == chess.ROOK:
        shuffles.append(f"{b.fullmove_number}.{b.san(mv)}")
    b.push(mv)
print("\nWhite rook moves 33-44:", shuffles)
