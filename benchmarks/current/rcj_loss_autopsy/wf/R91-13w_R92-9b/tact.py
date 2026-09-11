import chess
N=chess.square_name
def att(b,sq):
    w=[N(s)+b.piece_at(s).symbol() for s in b.attackers(chess.WHITE,sq)]
    k=[N(s)+b.piece_at(s).symbol() for s in b.attackers(chess.BLACK,sq)]
    return f"{N(sq)}: W{w} B{k}"
root=chess.Board("r4rk1/pp2ppb1/1q1p2pp/2pPn2P/6b1/P2P2P1/1PP1NPB1/R1BQ1RK1 w - - 1 13")
for first in ["f2f4","f2f3"]:
    b=root.copy(); b.push_uci(first)
    print("== after",first)
    for s in ["b2","e5","g4","e2","g3","d3","f2","e3"]: print(" ",att(b,chess.parse_square(s)))
    # black candidate replies: check which give check / what c5c4 does
    for rep in ["e5d7","g4d7","c5c4","b6b2","g7b2"]:
        m=chess.Move.from_uci(rep)
        if m in b.legal_moves:
            bb=b.copy(); san=bb.san(m); bb.push(m); print("  reply",san,"check" if bb.is_check() else "", "| b2", att(bb,chess.B2))
        else: print("  reply",rep,"illegal")
# f4 Nd7 then white options: does c4+ come with check?
b=root.copy(); b.push_uci("f2f4"); b.push_uci("e5d7")
print("== after f4 Nd7, white legal:", len(list(b.legal_moves)))
print(att(b,chess.B2)); 
bb=b.copy(); bb.push(chess.Move.null()); 
print("black threats if white passes: c4 gives check?", end=" "); x=bb.copy(); x.push_uci("c5c4"); print(x.is_check())
# game line
g=root.copy()
for u in "f4 Nd7 hxg6 fxg6 Be3 Qxb2 Rb1 Qxa3 Rxb7 Rfb8 Rxb8+ Rxb8".split(): g.push_san(u)
print("game after 18...Rxb8:"); print(g); print(g.fen())
def mat(b):
    v={1:1,2:3,3:3,4:5,5:9}
    return sum(v[p.piece_type]*(1 if p.color else -1) for p in b.piece_map().values() if p.piece_type!=6)
print("material (W-B) root", mat(root), "after 18...Rxb8", mat(g))
print()
# R92
r=chess.Board("r1bq1rk1/1p1pppbp/p1n2np1/2P5/3N4/2N3P1/PP2PPBP/R1BQ1RK1 b - - 0 9")
for first in ["e7e5","f8e8","h7h6"]:
    b=r.copy(); b.push_uci(first); print("== R92 after",first)
    for s in ["d6","d5","b6","d7"]:
        sq=chess.parse_square(s); print("  ",att(b,sq), "pawn-controlled by black:", any(b.piece_at(a) and b.piece_at(a).piece_type==1 for a in b.attackers(chess.BLACK,sq)))
g=r.copy()
for u in "e5 Nc2 b5 Bg5 h6 Bxf6 Qxf6 Ne3 Rb8 Ne4 Qe6 Nd6".split(): g.push_san(u)
print("R92 game after 15.Nd6:"); print(g); print(g.fen()); print(att(g,chess.D6)); print("d7 pawn attackers", att(g,chess.D7))
