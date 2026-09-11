import chess
V = {1:1,2:3,3:3,4:5,5:9,6:0}
def mat(b):
    return sum(V[p.piece_type]*(1 if p.color else -1) for p in b.piece_map().values())
fen98 = "r7/2pqrp1k/p1np1npp/1p1b4/1P1P4/P1QBB2P/3N1PPK/2R1R3 w - - 5 25"
b = chess.Board(fen98); b.push_uci("d3c2"); b.push_uci("a8e8")
print("R98 after Bc2 Rae8, material", mat(b))
x = b.copy()
for u in ["e3f4", "e7e1", "c1e1", "e8e1"]:
    x.push_uci(u)
print("  Bf4 Rxe1+ Rxe1 Rxe1: material", mat(x), "(white view)")
y = chess.Board(fen98); y.push_uci("d2f1")
print("R98 after Nf1: e1 defenders", [chess.square_name(s) for s in y.attackers(chess.WHITE, chess.E1)],
      " e3 defenders", [chess.square_name(s) for s in y.attackers(chess.WHITE, chess.E3)])
z = chess.Board(fen98); z.push_uci("f2f3"); z.push_uci("a8e8"); z.push_uci("e3f2")
print("R98 after f3 Rae8 Bf2: e1 defenders", [chess.square_name(s) for s in z.attackers(chess.WHITE, chess.E1)])
fen99 = "2b3k1/1N3pb1/p1p2npp/P3p3/2P3P1/1Q3P2/1P2PB1P/2q2BK1 b - - 0 25"
c = chess.Board(fen99)
for u in ["e5e4","b7c5","e4f3","e2f3","f6d7"]:
    c.push_uci(u)
print("R99 after e4 Nc5 exf3 exf3 Nd7: b2 black attackers", [chess.square_name(s) for s in c.attackers(chess.BLACK, chess.B2)],
      " white defenders", [chess.square_name(s) for s in c.attackers(chess.WHITE, chess.B2)])
d = chess.Board(fen99); d.push_uci("c8e6"); d.push_uci("e2e4")
print("R99 after Be6 e4: black legal moves of Bg7", [d.san(m) for m in d.legal_moves if m.from_square == chess.G7],
      "; e5 pawn can advance?", any(m.from_square == chess.E5 for m in d.legal_moves))
