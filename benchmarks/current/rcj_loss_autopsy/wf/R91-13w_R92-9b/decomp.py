import sys, importlib.abc
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name.split('.')[0] in ('numba','cs_core','cs_fast','cs_fast_trace','cs_search'):
            raise ImportError('blocked '+name)
        return None
sys.meta_path.insert(0, Block())
sys.path.insert(0,'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess, cs_eval, cs_terms
names=[t.name for t in cs_terms.TERMS]; print("terms:",names)
def phase(b):
    p=(b.knights|b.bishops).bit_count()+2*b.rooks.bit_count()+4*b.queens.bit_count(); return min(p,cs_eval.TOTAL_PHASE)
def piece_contrib(b):
    ph=phase(b); T=cs_eval.TOTAL_PHASE; out=[]
    for sq,p in b.piece_map().items():
        if p.color: mg=cs_eval.MG_WHITE[p.piece_type][sq]; eg=cs_eval.EG_WHITE[p.piece_type][sq]; sgn=1
        else: mg=cs_eval.MG_BLACK[p.piece_type][sq]; eg=cs_eval.EG_BLACK[p.piece_type][sq]; sgn=-1
        tap=(mg*ph+eg*(T-ph))/T
        out.append((p.symbol()+chess.square_name(sq), round(sgn*tap)))
    return out
base_val={1:(82,94),2:(337,281),3:(365,297),4:(477,512),5:(1025,936),6:(0,0)}  # PeSTO base (for info only)
def terms(b,pov):
    res={}
    cs_eval.set_terms([]); base=cs_eval.evaluate(b)
    for n in names:
        cs_eval.set_terms([n]); v=cs_eval.evaluate(b)-base; res[n]= v if b.turn==pov else -v
    cs_eval.set_terms([]); return res
def show(label,b,pov):
    s=cs_eval.evaluate(b); s= s if b.turn==pov else -s
    print("==",label,"static(pov)",s,"phase",phase(b)); print(b)
    print("  unshipped terms (pov cp):",terms(b,pov))
    pc=piece_contrib(b)
    # positional part = taper(PST) - taper(base material) per piece
    ph=phase(b); T=cs_eval.TOTAL_PHASE
    pos=[]
    for name,v in pc:
        pt=chess.Piece.from_symbol(name[0]).piece_type; mg,eg=base_val[pt]; bm=(mg*ph+eg*(T-ph))/T
        sgn=1 if name[0].isupper() else -1
        pos.append((name, round(v - sgn*bm)))
    pos.sort(key=lambda x:-abs(x[1]))
    print("  per-piece positional (white-positive, table minus PeSTO base):",pos[:16])
    print("  white pos sum",sum(v for n,v in pos if n[0].isupper()),"black pos sum",sum(v for n,v in pos if n[0].islower()))
root=chess.Board("r4rk1/pp2ppb1/1q1p2pp/2pPn2P/6b1/P2P2P1/1PP1NPB1/R1BQ1RK1 w - - 1 13")
game="f4 Nd7 hxg6 fxg6 Be3 Qxb2 Rb1 Qxa3 Rxb7 Rfb8 Rxb8+ Rxb8 Qe1 Kh7 Qf2 Nf6 Rc1 e6 dxe6 Bxe6".split()
g=root.copy(); mv=13
for i,s in enumerate(game):
    g.push_san(s)
    if i%2==1:
        mv+=1
        if mv in (16,19,22): show(f"R91 before W move {mv}",g,chess.WHITE)
for pv,lab in [("f2f4 e5d7 h5g6 c5c4 d3d4 f7g6 a3a4 d7f6","R91 SF played pv_end"),("f2f3 g4d7 h5g6 e5g6 a3a4 e7e5 a4a5 b6c7","R91 SF best pv_end")]:
    b=root.copy(); [b.push_uci(u) for u in pv.split()]; show(lab,b,chess.WHITE)
r=chess.Board("r1bq1rk1/1p1pppbp/p1n2np1/2P5/3N4/2N3P1/PP2PPBP/R1BQ1RK1 b - - 0 9")
for m in ["e7e5","f8e8"]:
    b=r.copy(); b.push_uci(m); show("R92 after "+m,b,chess.BLACK)
g=r.copy(); mv=9
for i,s in enumerate("e5 Nc2 b5 Bg5 h6 Bxf6 Qxf6 Ne3 Rb8 Ne4 Qe6 Nd6".split()):
    g.push_san(s)
    if i%2==1:
        mv+=1
        if mv in (10,15): show(f"R92 before B move {mv}",g,chess.BLACK)
print("numba loaded?", 'numba' in sys.modules)
