import sys
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/wf/R94-44w_R95-20b')
from evalhelp import *

FEN = "1r2r1k1/pp3pp1/3b1qp1/2p5/1nP1B3/4N1PP/P2PPP2/RQ3RK1 b - - 0 20"
# hand-picked lines only (inspection, not search); black-view static at the final position
lines = {
    "Qe6 Bf3 Qxh3 (W retreats, B regains h3)": ["f6e6", "e4f3", "e6h3"],
    "Qe6 Bg2 (h3 held)": ["f6e6", "e4g2"],
    "Qe6 Bd3 Nxd3 exd3 (B trade)": ["f6e6", "e4d3", "b4d3", "e2d3"],
    "Qe6 Bd5 Nxd5 cxd5 Qxd5 (B regains)": ["f6e6", "e4d5", "b4d5", "c4d5", "e6d5"],
    "Qe6 a3 Nc6 Bf3 (B declines, stays -1)": ["f6e6", "a2a3", "b4c6", "e4f3"],
    "SF refutation to Rxa7": ["f6e6","a2a3","e6e4","b1e4","e8e4","a3b4","c5b4","a1a7"],
    "SF refutation + game's Bc5": ["f6e6","a2a3","e6e4","b1e4","e8e4","a3b4","c5b4","a1a7","d6c5"],
    "Qd4 Bf3 Be5 Qb3 Qxd2 (B regains d2)": ["f6d4","e4f3","d6e5","b1b3","d4d2"],
}
for label, pv in lines.items():
    b, s = play(FEN, pv)
    print(f"{label:48s} | {s:45s} | static(black) {-white_static(b):>5} | material W,B {material(b)} | B pawns {pawn_feats(b, chess.BLACK)}")
