import sys
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/wf/R94-44w_R95-20b')
from evalhelp import *

FEN = "8/1r2pk2/p2p4/P2P1p2/P1p3p1/2P3P1/rb1B1PK1/1R1R4 w - - 4 44"
root = chess.Board(FEN)
b = root.copy(); b.push_uci("d1h1")
print("After Rh1: d2 defended by W:", [chess.square_name(s) for s in b.attackers(chess.WHITE, chess.D2)])
print("After Rh1, Black bishop moves that unmask Ra2->d2 and Rb7->b1:",
      [b.san(m) for m in b.legal_moves if m.from_square == chess.B2])
lines = {
    "Rh1 Ba3 Rxb7 Rxd2 (W wins R for B)": ["d1h1", "b2a3", "b1b7", "a2d2"],
    "Rh1 Ba3 Be3 (B defended, b1 held by Rh1)": ["d1h1", "b2a3", "d2e3"],
    "Rh1 Kf6 (quiet)": ["d1h1", "f7f6"],
    "Bc1 Kf6 (quiet)": ["d2c1", "f7f6"],
    "Bc1 Kf6 Re1 Rb3 (B rook in)": ["d2c1", "f7f6", "d1e1", "b7b3"],
    "Bc1 Kf6 Kg1 Rb3 (game)": ["d2c1", "f7f6", "g2g1", "b7b3"],
    "game to 47...Rxb2 (trade into R ending)": ["d2c1","f7f6","g2g1","b7b3","b1b2","a2b2","c1b2","b3b2"],
}
for label, pv in lines.items():
    bb, s = play(FEN, pv)
    print(f"{label:44s} | {s:40s} | static(white) {white_static(bb):>5} | material {material(bb)} | rooks {rook_report(bb)}")
