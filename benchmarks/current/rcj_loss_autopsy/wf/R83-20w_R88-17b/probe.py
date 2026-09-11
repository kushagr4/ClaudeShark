import sys, json
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess, chess.pgn
import cs_eval
from cs_constants import MG_BLACK, EG_BLACK, MG_WHITE, EG_WHITE

S = chess.parse_square
def pst(color, pt, sq):
    if color == chess.BLACK:
        return MG_BLACK[pt][S(sq)], EG_BLACK[pt][S(sq)]
    return MG_WHITE[pt][S(sq)], EG_WHITE[pt][S(sq)]

print("== (a) R88 PST decomposition (black pieces, material included)")
for pt, a, b in [(chess.KNIGHT, 'f4', 'e6'), (chess.KNIGHT, 'f4', 'h5'), (chess.ROOK, 'a8', 'c8'), (chess.ROOK, 'a8', 'b8'), (chess.KNIGHT, 'f6', 'h5'), (chess.KNIGHT, 'e6', 'c5')]:
    print(chess.piece_name(pt), a, pst(chess.BLACK, pt, a), b, pst(chess.BLACK, pt, b))
print("white knight g3", pst(chess.WHITE, chess.KNIGHT, 'g3'), "f5", pst(chess.WHITE, chess.KNIGHT, 'f5'), "h1", pst(chess.WHITE, chess.KNIGHT, 'h1'))
print("white rook e1", pst(chess.WHITE, chess.ROOK, 'e1'), "a1", pst(chess.WHITE, chess.ROOK, 'a1'), "d7", pst(chess.WHITE, chess.ROOK, 'd7'), "d2", pst(chess.WHITE, chess.ROOK, 'd2'))
print("black rook e2", pst(chess.BLACK, chess.ROOK, 'e2'), "c2", pst(chess.BLACK, chess.ROOK, 'c2'), "e8", pst(chess.BLACK, chess.ROOK, 'e8'))
print("white bishop f2", pst(chess.WHITE, chess.BISHOP, 'f2'), "d2", pst(chess.WHITE, chess.BISHOP, 'd2'), "e3", pst(chess.WHITE, chess.BISHOP, 'e3'))
b = chess.Board('r3r1k1/1ppq1ppp/1b1p1nb1/pP2p3/P1BPPn2/1QP2NNP/R4PP1/2B1R1K1 b - - 8 17')
ph = (b.knights | b.bishops).bit_count() + 2 * b.rooks.bit_count() + 4 * b.queens.bit_count()
print("R88 phase", ph, "/24")

def wpov(bd):
    e = cs_eval.evaluate(bd)
    return e if bd.turn == chess.WHITE else -e

def terms_delta(bd):
    out = {}
    base = wpov(bd)
    for t in ['king_safety', 'passed', 'king_pawn', 'low_material']:
        cs_eval.set_terms([t]); out[t] = wpov(bd) - base
    cs_eval.set_terms([])
    return base, out

def mob(bd, color):
    x = bd.copy(stack=False); x.turn = color
    return sum(1 for m in x.pseudo_legal_moves if x.piece_at(m.from_square).piece_type != chess.PAWN)

print("\n== (b) R83 game continuation: white-POV static + unshipped term deltas (white POV)")
B = json.load(open('C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/R83-20w.json'))
sfmap = {m['move_number']: m for m in B['all_rcj_moves']}
g = chess.pgn.read_game(open(B['pgn_path']))
bd = g.board()
for mv in g.mainline_moves():
    if bd.turn == chess.WHITE and 20 <= bd.fullmove_number <= 30:
        base, td = terms_delta(bd)
        m = sfmap[bd.fullmove_number]
        print(f"move {bd.fullmove_number} root: SF_best_cp={m['best_cp']:+5d} RCJ_static(W)={base:+4d} mobW={mob(bd,True)} mobB={mob(bd,False)} terms={td} played={m['san']} loss={m['loss_cp']}")
    bd.push(mv)

print("\n== (d) R83 a4/c2 after Bf2 Bd7 vs Bd2 Bd7")
f83 = B['decisive']['fen']
for first in ['e3f2', 'e3d2']:
    x = chess.Board(f83); x.push_uci(first); x.push_uci('c8d7')
    for sq in ['a4', 'c2', 'c3', 'f4', 'g5', 'e1', 'e8']:
        s = S(sq)
        print(first, "Bd7", sq, "W-att", [chess.square_name(q) for q in x.attackers(chess.WHITE, s)], "B-att", [chess.square_name(q) for q in x.attackers(chess.BLACK, s)])
    print(x)
    print()
x = chess.Board(f83)
for u in ['e3f2', 'c8d7', 'e1a1', 'h5h4', 'g3h1', 'e8e2']:
    x.push_uci(u)
print("after 22.Nh1 Re2: Nh1 legal moves:", [x.san(m) for m in x.legal_moves if m.from_square == S('h1')] if x.turn else 'n/a')
x.turn = chess.WHITE
print("Nh1 pseudo-legal:", [chess.square_name(m.to_square) for m in x.pseudo_legal_moves if m.from_square == S('h1')])
print(x)

print("\n== (c) R88 PV ends: control of d-file entry squares, knight f4 status")
B2 = json.load(open('C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/R88-17b.json'))
f88 = B2['decisive']['fen']
for label, pv in [('played', B2['decisive']['sf_played_pv']), ('best', B2['decisive']['sf_best_pv'])]:
    x = chess.Board(f88)
    for u in pv:
        x.push_uci(u)
    print(label, "PV end, turn", 'W' if x.turn else 'B')
    print(x)
    for sq in ['d7', 'd6', 'd3', 'd5', 'f5', 'f4', 'c5', 'e4', 'a4']:
        s = S(sq)
        print(" ", sq, x.piece_at(s), "W-att", [chess.square_name(q) for q in x.attackers(chess.WHITE, s)], "B-att", [chess.square_name(q) for q in x.attackers(chess.BLACK, s)])
    base, td = terms_delta(x)
    print("  static W-POV", base, "terms(W-POV)", td)
# after Rac8 dxe5 dxe5 Kh2: g3 threat on Nf4
x = chess.Board(f88)
for u in ['a8c8', 'd4e5', 'd6e5', 'g1h2']:
    x.push_uci(u)
x.push(chess.Move.null())
print("after Rac8 dxe5 dxe5 Kh2 (+null): is g3 legal for white:", chess.Move.from_uci('g2g3') in x.legal_moves)
x.pop()
print("Nf4 retreat squares (black to move):", [x.san(m) for m in x.legal_moves if m.from_square == S('f4')])
# after Ne6 dxe5 Nc5: queen attacked?
x = chess.Board(f88)
for u in ['f4e6', 'd4e5', 'e6c5']:
    x.push_uci(u)
print("after Ne6 dxe5 Nc5: Qb3 attacked by", [chess.square_name(q) for q in x.attackers(chess.BLACK, S('b3'))], "; c5 attacks", [chess.square_name(q) for q in x.attacks(S('c5'))])
# game move 11 context: RC-J Nf4 at move 11 was a 67cp error
