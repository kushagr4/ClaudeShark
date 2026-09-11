import chess
for fen,lines in [
 ("r4rk1/pp2ppb1/1q1p2pp/2pPn2P/6b1/P2P2P1/1PP1NPB1/R1BQ1RK1 w - - 1 13",
  {"played":"f2f4 e5d7 h5g6 c5c4 d3d4 f7g6 a3a4 d7f6".split(),"best":"f2f3 g4d7 h5g6 e5g6 a3a4 e7e5 a4a5 b6c7".split()}),
 ("r1bq1rk1/1p1pppbp/p1n2np1/2P5/3N4/2N3P1/PP2PPBP/R1BQ1RK1 b - - 0 9",
  {"played":"e7e5 d4c2 b7b6 c5b6 d8b6 c1e3 b6d8 a1c1".split(),"best":"f8e8 c1f4 f6h5 f4e3 h5f6 d1a4 f6g4 d4c6".split()}),
]:
    b=chess.Board(fen); print(b); print(fen)
    for name,pv in lines.items():
        bb=b.copy(); sans=[]
        for u in pv:
            m=chess.Move.from_uci(u); sans.append(bb.san(m)); bb.push(m)
        print(name, " ".join(sans)); print(bb); print(bb.fen()); print()
