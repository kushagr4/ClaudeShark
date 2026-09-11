import sys
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess
import cs_eval

print("active terms (env):", sorted(cs_eval.ACTIVE_TERMS))
cs_eval.set_terms(["mopup"])  # shipped RC-J: PeSTO + bishop pair + tempo + mop-up

def unpack(p):
    eg = p & 0xFFFF
    if eg >= 0x8000:
        eg -= 0x10000
    return (p - eg) >> 16, eg

def mover_static_after(board, uci):
    b = board.copy(); b.push_uci(uci)
    return -cs_eval.evaluate(b)  # from the mover's point of view

def sq_report(board, sqname):
    s = chess.parse_square(sqname)
    w = [chess.square_name(x) for x in board.attackers(chess.WHITE, s)]
    bl = [chess.square_name(x) for x in board.attackers(chess.BLACK, s)]
    return f"{sqname}: W attackers {w}  B attackers {bl}"

def pv_walk(fen, pv, label):
    b = chess.Board(fen)
    sans = []
    for u in pv:
        m = chess.Move.from_uci(u)
        sans.append(b.san(m)); b.push(m)
    print(f"  {label}: {' '.join(sans)}")
    print("   end FEN", b.fen(), " static(stm)", cs_eval.evaluate(b))
    return b

def analyse(fen, cands, pvs, squares):
    board = chess.Board(fen)
    print(board); print(fen)
    print("static at root (stm):", cs_eval.evaluate(board))
    for u in cands:
        m = chess.Move.from_uci(u)
        mg, eg = unpack(cs_eval.pst_delta(board, m))
        print(f"  {board.san(m):6s} {u}: static-after (mover view) {mover_static_after(board, u):5d}   pst_delta white-pos mg {mg:4d} eg {eg:4d}")
    for s in squares:
        print("  ", sq_report(board, s))
    for label, pv in pvs.items():
        pv_walk(fen, pv, label)

print("=" * 70, "\nR98-25w")
fen98 = "r7/2pqrp1k/p1np1npp/1p1b4/1P1P4/P1QBB2P/3N1PPK/2R1R3 w - - 5 25"
analyse(fen98, ["d3c2", "f2f3", "d2f1", "h2g1"],
        {"played": ["d3c2","a8e8","a3a4","c6a7","c3a3","d5b7","d2f1","f6d5"],
         "best":   ["f2f3","a8e8","e3f2","e7e1","f2e1","d7e6","e1h4","f6h5"]},
        ["e3", "e1", "d4", "b4", "g2", "e4", "g4", "d5"])
# After Bc2 Rae8: what hangs if Be3 moves off the e-file?
b = chess.Board(fen98); b.push_uci("d3c2"); b.push_uci("a8e8")
print("After Bc2 Rae8:"); print(b)
for s in ["e3", "e1", "d4", "b4"]:
    print("  ", sq_report(b, s))
print("  is Be3 pinned (absolute)?", b.is_pinned(chess.WHITE, chess.E3))
# e-file X-ray count: black major pieces on e-file
print("  black heavy pieces on e-file:", [chess.square_name(s) for s in chess.SquareSet(chess.BB_FILE_E) if b.piece_at(s) and b.piece_at(s).color == chess.BLACK])
print("  white pieces on e-file:", [chess.square_name(s)+str(b.piece_at(s)) for s in chess.SquareSet(chess.BB_FILE_E) if b.piece_at(s) and b.piece_at(s).color == chess.WHITE])

# Earlier moves 22-24: SF best was Nf3-g1 three times in a row; PST cost
print("\nR98 earlier moves (PST cost of SF's recurring Ng1 / f3 regroup):")
g = chess.Board("r1bq1rk1/pppp1ppp/2n2n2/1Bb5/3NP3/2P5/PP3PPP/RNBQ1RK1 w - - 3 8")
import re
pgn = open('C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/public_new/91a14b62-7ef1-4490-8997-249d1dcb949b.pgn').read()
import chess.pgn, io
game = chess.pgn.read_game(io.StringIO(pgn))
node = game
want = {22: ["b2b4", "f3g1"], 23: ["b1c3", "f3g1"], 24: ["f3d2", "f3g1"]}
for mv in game.mainline_moves():
    bd = node.board() if False else None
    break
board = game.board()
for mv in game.mainline_moves():
    if board.turn == chess.WHITE and board.fullmove_number in (22, 23, 24):
        played = mv.uci()
        cands = [played, "f3g1"]
        out = []
        for u in cands:
            m = chess.Move.from_uci(u)
            if m in board.legal_moves:
                mg, eg = unpack(cs_eval.pst_delta(board, m))
                out.append(f"{board.san(m)} static-after {mover_static_after(board, u)} pst mg {mg} eg {eg}")
        print(f"  move {board.fullmove_number}: " + " | ".join(out))
    board.push(mv)

print("=" * 70, "\nR99-25b")
fen99 = "2b3k1/1N3pb1/p1p2npp/P3p3/2P3P1/1Q3P2/1P2PB1P/2q2BK1 b - - 0 25"
analyse(fen99, ["c8e6", "e5e4"],
        {"played": ["c8e6","e2e4","h6h5","h2h3","f6h7","f2e3","c1e1","b3c3"],
         "best":   ["e5e4","b7c5","e4f3","e2f3","f6d7","c5e4","d7f8","f2e3"]},
        ["b7", "e4", "c4", "b2", "f1", "e5", "c5", "d6", "d8"])
b = chess.Board(fen99)
print("  Nb7 legal moves:", [b.san(m) for m in b.legal_moves if False])
bw = b.copy(); bw.turn = chess.WHITE
print("  Nb7 (white) pseudo moves:", [bw.san(m) for m in bw.legal_moves if m.from_square == chess.B7])
# Bg7 diagonal squares blocked?
print("  Bg7 attacks now:", [chess.square_name(s) for s in b.attacks(chess.G7)])
b2 = chess.Board(fen99); b2.push_uci("c8e6"); b2.push_uci("e2e4")
print("After Be6 e4: Bg7 attacks", [chess.square_name(s) for s in b2.attacks(chess.G7)], " Be6 attacks", [chess.square_name(s) for s in b2.attacks(chess.E6)])
print(" e5 pawn: W attackers", [chess.square_name(s) for s in b2.attackers(chess.WHITE, chess.E5)], "B defenders", [chess.square_name(s) for s in b2.attackers(chess.BLACK, chess.E5)])
b3 = chess.Board(fen99)
for u in ["e5e4","b7c5","e4f3","e2f3","f6d7"]:
    b3.push_uci(u)
print("After e4 Nc5 exf3 exf3 Nd7: Bg7 attacks", [chess.square_name(s) for s in b3.attacks(chess.G7)])
# static on PeSTO for the black pawn e5 vs e4 and bishop c8 vs e6
bb = chess.Board(fen99)
for u in ["c8e6", "e5e4"]:
    m = chess.Move.from_uci(u)
    mg, eg = unpack(cs_eval.pst_delta(bb, m))
    print(f"  {u} pst delta (white-positive) mg {mg} eg {eg}  -> black gain mg {-mg} eg {-eg}")
