import sys, importlib.abc
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name.split('.')[0] in ('numba','cs_core','cs_fast','cs_fast_trace','cs_search'): raise ImportError(name)
        return None
sys.meta_path.insert(0, Block())
sys.path.insert(0,'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess, cs_eval
root=chess.Board("r4rk1/pp2ppb1/1q1p2pp/2pPn2P/6b1/P2P2P1/1PP1NPB1/R1BQ1RK1 w - - 1 13")
def pmob(b,sq):
    return len(b.attacks(chess.parse_square(sq)) & ~b.occupied_co[b.piece_at(chess.parse_square(sq)).color])
for line in [["f2f4","e5d7"],["f2f3","g4d7"]]:
    b=root.copy(); [b.push_uci(u) for u in line]
    print(line, "Bg7 mob",pmob(b,"g7"),"Qb6 mob",pmob(b,"b6"),"b2 attackers B",len(b.attackers(chess.BLACK,chess.B2)),"defenders W",len(b.attackers(chess.WHITE,chess.B2)))
g=root.copy()
for s in "f4 Nd7 hxg6 fxg6 Be3 Qxb2 Rb1 Qxa3 Rxb7 Rfb8".split(): g.push_san(s)
ph=min((g.knights|g.bishops).bit_count()+2*g.rooks.bit_count()+4*g.queens.bit_count(),24)
sq=chess.B7; mg=cs_eval.MG_WHITE[chess.ROOK][sq]; eg=cs_eval.EG_WHITE[chess.ROOK][sq]
sq2=chess.B1; mg2=cs_eval.MG_WHITE[chess.ROOK][sq2]; eg2=cs_eval.EG_WHITE[chess.ROOK][sq2]
print("before W18 static(W)", cs_eval.evaluate(g), "Rb7 tapered", round((mg*ph+eg*(24-ph))/24), "vs Rb1", round((mg2*ph+eg2*(24-ph))/24))
print(g.fen())
