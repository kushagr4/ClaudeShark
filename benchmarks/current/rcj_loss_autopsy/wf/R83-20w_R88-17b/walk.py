import sys, json
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess, chess.pgn
import cs_eval

print("ACTIVE_TERMS default:", sorted(cs_eval.ACTIVE_TERMS))

VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}

def mat(b):
    s = 0
    for pt, v in VAL.items():
        s += v * (len(b.pieces(pt, chess.WHITE)) - len(b.pieces(pt, chess.BLACK)))
    return s

def mob(b, color):
    bb = b.copy(stack=False)
    bb.turn = color
    n = 0
    for m in bb.pseudo_legal_moves:
        p = bb.piece_at(m.from_square)
        if p.piece_type != chess.PAWN:
            n += 1
    return n

def wpov(b):
    e = cs_eval.evaluate(b)
    return e if b.turn == chess.WHITE else -e

def line(fen, ucis, rcj_white, label):
    b = chess.Board(fen)
    print(f"--- {label}")
    for i, u in enumerate(ucis):
        m = chess.Move.from_uci(u)
        san = b.san(m)
        b.push(m)
        w = wpov(b)
        r = w if rcj_white else -w
        print(f"ply{i+1:2d} {san:7s} mat(W)={mat(b):+d} evalW={w:+5d} evalRCJ={r:+5d} mobW={mob(b,chess.WHITE):2d} mobB={mob(b,chess.BLACK):2d}")
    return b

B = json.load(open('C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/R83-20w.json'))
d = B['decisive']
line(d['fen'], d['sf_played_pv'], True, "R83 played PV")
line(d['fen'], d['sf_best_pv'], True, "R83 best PV")

B2 = json.load(open('C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/R88-17b.json'))
d2 = B2['decisive']
line(d2['fen'], d2['sf_played_pv'], False, "R88 played PV")
line(d2['fen'], d2['sf_best_pv'], False, "R88 best PV")

def game(pgn, start_fen, rcj_white, label, nplies):
    g = chess.pgn.read_game(open(pgn))
    b = g.board()
    found = False
    out = []
    for mv in g.mainline_moves():
        if not found and b.fen() == start_fen:
            found = True
        if found:
            out.append(mv.uci())
            if len(out) >= nplies:
                break
        b.push(mv)
    line(start_fen, out, rcj_white, label + " GAME")

game(B['pgn_path'], d['fen'], True, "R83", 22)
game(B2['pgn_path'], d2['fen'], False, "R88", 22)
