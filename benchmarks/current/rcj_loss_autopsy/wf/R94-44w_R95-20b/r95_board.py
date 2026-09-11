import chess

FEN = "1r2r1k1/pp3pp1/3b1qp1/2p5/1nP1B3/4N1PP/P2PPP2/RQ3RK1 b - - 0 20"
b = chess.Board(FEN)
print(b)
print()

def sqs(board, sq, colour):
    return [chess.square_name(s) for s in board.attackers(colour, sq)]

print("e4 bishop: W defenders", sqs(b, chess.E4, chess.WHITE), " B attackers", sqs(b, chess.E4, chess.BLACK))
print("b4 knight: B defenders", sqs(b, chess.B4, chess.BLACK), " W attackers", sqs(b, chess.B4, chess.WHITE))
print("d2 pawn: W defenders", sqs(b, chess.D2, chess.WHITE))
print("a1 rook: W defenders", sqs(b, chess.A1, chess.WHITE))

for label, uci in [("played Qe6", "f6e6"), ("SF best Qd4", "f6d4")]:
    bb = b.copy()
    bb.push_uci(uci)
    print(f"\n=== after {label} ===")
    print(bb)
    print("  e4 B attackers:", sqs(bb, chess.E4, chess.BLACK), " W defenders:", sqs(bb, chess.E4, chess.WHITE))
    print("  a1 B attackers:", sqs(bb, chess.A1, chess.BLACK))
    print("  e3 B attackers:", sqs(bb, chess.E3, chess.BLACK))
    print("  c4 B attackers:", sqs(bb, chess.C4, chess.BLACK), " W defenders:", sqs(bb, chess.C4, chess.WHITE))
    print("  d2 B attackers:", sqs(bb, chess.D2, chess.BLACK))

for label, pv in [("SF best PV", ["f6d4","e4f3","d6e5","b1b3","d4d2","f1d1","d2c3","b3c3"]),
                  ("SF played PV", ["f6e6","a2a3","e6e4","b1e4","e8e4","a3b4","c5b4","a1a7"])]:
    bb = b.copy()
    san = []
    for u in pv:
        m = chess.Move.from_uci(u)
        san.append(bb.san(m))
        bb.push(m)
    print(f"\n{label}: {' '.join(san)}")
    print(bb)
    vals = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3, chess.ROOK:5, chess.QUEEN:9}
    w = sum(vals[p.piece_type] for p in bb.piece_map().values() if p.color and p.piece_type in vals)
    k = sum(vals[p.piece_type] for p in bb.piece_map().values() if not p.color and p.piece_type in vals)
    print("  material W", w, "B", k, "(B-W =", k - w, ")")
    print("  black pawns:", sorted(chess.square_name(s) for s in bb.pieces(chess.PAWN, chess.BLACK)))
    print("  white pawns:", sorted(chess.square_name(s) for s in bb.pieces(chess.PAWN, chess.WHITE)))
    # legal recapture check at end of best PV
    if label == "SF best PV":
        print("  Black recaptures available on c3:", [bb.san(m) for m in bb.legal_moves if m.to_square == chess.C3])

# what does Qe6 threaten if White ignores it? try a quiet White move, then Qxe4 exchange
bb = b.copy(); bb.push_uci("f6e6")
print("\nAfter Qe6, White replies and whether Black's Qxe4 wins a piece:")
for reply in ["a2a3", "e4d3", "e4f3", "e4g2", "e4d5", "f2f3"]:
    t = bb.copy()
    m = chess.Move.from_uci(reply)
    if m not in t.legal_moves:
        print("  ", reply, "illegal"); continue
    s = t.san(m); t.push(m)
    caps = [t.san(x) for x in t.legal_moves if t.is_capture(x)]
    print(f"   {s}: Black captures {caps}")
