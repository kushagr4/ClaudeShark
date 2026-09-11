import chess

FEN = "8/1r2pk2/p2p4/P2P1p2/P1p3p1/2P3P1/rb1B1PK1/1R1R4 w - - 4 44"
b = chess.Board(FEN)
print(b)
print()

def defenders(board, sq, colour):
    return [chess.square_name(s) for s in board.attackers(colour, sq)]

print("Before Bc1: defenders of c3 (W):", defenders(b, chess.C3, chess.WHITE),
      " attackers of c3 (B):", defenders(b, chess.C3, chess.BLACK))
print("Before Bc1: attackers of b2 (W):", defenders(b, chess.B2, chess.WHITE),
      " defenders of b2 (B):", defenders(b, chess.B2, chess.BLACK))

for label, uci in [("played Bc1", "d2c1"), ("SF best Rh1", "d1h1")]:
    bb = b.copy()
    bb.push_uci(uci)
    print(f"\n=== after {label} ===")
    print(bb)
    print("  c3 W defenders:", defenders(bb, chess.C3, chess.WHITE),
          " B attackers:", defenders(bb, chess.C3, chess.BLACK))
    print("  d2 W defenders:", defenders(bb, chess.D2, chess.WHITE))
    print("  f2 W defenders:", defenders(bb, chess.F2, chess.WHITE),
          " B attackers:", defenders(bb, chess.F2, chess.BLACK))
    print("  b3 W control:", defenders(bb, chess.B3, chess.WHITE))
    # white piece mobility (non-pawn pseudo-legal), after a null move to count white's moves
    bb.push(chess.Move.null())
    wm = sum(1 for m in bb.pseudo_legal_moves if bb.piece_type_at(m.from_square) != chess.PAWN)
    bb.pop()
    print("  White non-pawn pseudo-legal moves:", wm)

# the SF PVs from the bundle
for label, pv in [("SF best PV", ["d1h1","f7f6","b1e1","b2a1","e1e6","f6f7","d2e1","a2c2"]),
                  ("SF played PV", ["d2c1","f7f6","d1e1","b7b3","c1d2","b2a1","e1e6","f6f7"])]:
    bb = b.copy()
    san = []
    for u in pv:
        m = chess.Move.from_uci(u)
        san.append(bb.san(m))
        bb.push(m)
    print(f"\n{label}: {' '.join(san)}")
    print(bb)

# the actual game continuation from move 44
game = ["d2c1","f7f6","g2g1","b7b3","b1b2","a2b2","c1b2","b3b2","d1d4","f6e5","d4c4","e5d5"]
bb = b.copy()
san = []
for u in game:
    m = chess.Move.from_uci(u)
    san.append(bb.san(m))
    bb.push(m)
print("\nGame 44..49:", " ".join(san))
print(bb)
print("Material W-B (P=1,N/B=3,R=5,Q=9):")
vals = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3, chess.ROOK:5, chess.QUEEN:9}
w = sum(vals[p.piece_type] for p in bb.piece_map().values() if p.color and p.piece_type in vals)
k = sum(vals[p.piece_type] for p in bb.piece_map().values() if not p.color and p.piece_type in vals)
print(" W", w, "B", k)
