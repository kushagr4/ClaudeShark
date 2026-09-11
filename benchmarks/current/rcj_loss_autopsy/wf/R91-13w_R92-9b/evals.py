import sys, importlib.abc
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name.split('.')[0] in ('numba','cs_core','cs_fast','cs_fast_trace','cs_search'):
            raise ImportError('blocked '+name)
        return None
sys.meta_path.insert(0, Block())
sys.path.insert(0,'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess, cs_eval, cs_king
print("active terms", sorted(cs_eval.ACTIVE_TERMS))
def mat(b):
    v={1:1,2:3,3:3,4:5,5:9}
    return sum(v[p.piece_type]*(1 if p.color else -1) for p in b.piece_map().values() if p.piece_type!=6)
def ev(b, pov):  # static from pov colour
    s=cs_eval.evaluate(b); return s if b.turn==pov else -s
def ks(b, pov):
    v=cs_king.king_safety_mg_reference(b); return v if pov==chess.WHITE else -v
# R91
root=chess.Board("r4rk1/pp2ppb1/1q1p2pp/2pPn2P/6b1/P2P2P1/1PP1NPB1/R1BQ1RK1 w - - 1 13")
print("R91 root static(W)", ev(root,chess.WHITE))
for m in ["f2f4","f2f3"]:
    print(" pst_delta",m,cs_eval.pst_delta(root,chess.Move.from_uci(m)))
    b=root.copy(); b.push_uci(m); print(" after",m,"static(W)",ev(b,chess.WHITE),"ks_mg(W)",ks(b,chess.WHITE))
game="f4 Nd7 hxg6 fxg6 Be3 Qxb2 Rb1 Qxa3 Rxb7 Rfb8 Rxb8+ Rxb8 Qe1 Kh7 Qf2 Nf6 Rc1 e6 dxe6 Bxe6".split()
sf={14:-110,15:-123,16:-165,17:-219,18:-252,19:-261,20:-254,21:-280,22:-248}
g=root.copy(); mv=13
for i,s in enumerate(game):
    g.push_san(s)
    if i%2==1:
        mv+=1
        print(f" before W move {mv}: mat(W-B)={mat(g)} static(W)={ev(g,chess.WHITE)} ks_mg(W)={ks(g,chess.WHITE)} SF_best_cp={sf.get(mv)}")
# R92
r=chess.Board("r1bq1rk1/1p1pppbp/p1n2np1/2P5/3N4/2N3P1/PP2PPBP/R1BQ1RK1 b - - 0 9")
print("R92 root static(B)", ev(r,chess.BLACK))
for m in ["e7e5","f8e8","h7h6"]:
    # pst_delta is white-positive packed; decode mg/eg
    d=cs_eval.pst_delta(r,chess.Move.from_uci(m)); eg=d&0xFFFF; eg=eg-0x10000 if eg>=0x8000 else eg; mg=(d-eg)>>16
    b=r.copy(); b.push_uci(m); print(" after",m,"static(B)",ev(b,chess.BLACK),"pst_delta(white-pos) mg",mg,"eg",eg)
game2="e5 Nc2 b5 Bg5 h6 Bxf6 Qxf6 Ne3 Rb8 Ne4 Qe6 Nd6".split()
sf2={10:-125,11:-172,12:-163,13:-150,14:-146,15:-152}
g=r.copy(); mv=9
for i,s in enumerate(game2):
    g.push_san(s)
    if i%2==1:
        mv+=1; print(f" before B move {mv}: mat(W-B)={mat(g)} static(B)={ev(g,chess.BLACK)} SF_best_cp={sf2.get(mv)}")
# PST value of white knight on d6 vs e4 (mg,eg), from reference tables
for sq in ["d6","e4","c2","e3"]:
    s=chess.parse_square(sq); print(" W knight PST",sq, cs_eval.MG_WHITE[chess.KNIGHT][s], cs_eval.EG_WHITE[chess.KNIGHT][s])
print("numba loaded?", 'numba' in sys.modules)
