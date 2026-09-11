import sys, json
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess, chess.pgn
import cs_eval
from cs_drawish import low_material_reference

B = 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/'
VAL = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9, 6: 0}

def st(b, side):
    v = cs_eval.evaluate(b)
    return v if b.turn == side else -v

def mat(b, side):
    return sum(VAL[p.piece_type] * (1 if p.color == side else -1) for p in b.piece_map().values())

def sqinfo(b, name):
    sq = chess.parse_square(name)
    w = [chess.square_name(s) + b.piece_at(s).symbol() for s in b.attackers(chess.WHITE, sq)]
    k = [chess.square_name(s) + b.piece_at(s).symbol() for s in b.attackers(chess.BLACK, sq)]
    return f'{name}: {b.piece_at(sq)} white_att={w} black_att={k}'

def files(b):
    out = []
    for f in range(8):
        wp = any(b.piece_at(chess.square(f, r)) == chess.Piece(chess.PAWN, chess.WHITE) for r in range(8))
        bp = any(b.piece_at(chess.square(f, r)) == chess.Piece(chess.PAWN, chess.BLACK) for r in range(8))
        tag = 'open' if not wp and not bp else ('half-open(W)' if not wp else ('half-open(B)' if not bp else ''))
        if tag:
            out.append(chess.FILE_NAMES[f] + ':' + tag)
    return out

def bishop_colours(b):
    res = {}
    for c in (chess.WHITE, chess.BLACK):
        res['W' if c else 'B'] = ['light' if (chess.square_file(s) + chess.square_rank(s)) % 2 else 'dark' for s in b.pieces(chess.BISHOP, c)]
    return res

def game(pid):
    d = json.load(open(B + pid + '.json'))
    g = chess.pgn.read_game(open(d['pgn_path'].replace('\\', '/')))
    b = g.board(); boards = {}
    for node in g.mainline():
        boards[(b.fullmove_number, b.turn)] = b.copy()
        b.push(node.move)
    return d, boards

# ---------------- R101-29b
d, gb = game('R101-29b')
b = chess.Board(d['decisive']['fen'])
print('R101 m29 before:', sqinfo(b, 'f7'), '|', sqinfo(b, 'd6'), '|', sqinfo(b, 'd8'))
b.push_uci('f8d8')
print('R101 after Rfd8:', sqinfo(b, 'f7'))
# what does Bf6 add
b2 = chess.Board(d['decisive']['fen']); b2.push_uci('g7f6')
bf6 = [chess.square_name(s) for s in b2.attacks(chess.parse_square('f6'))]
b3 = chess.Board(d['decisive']['fen'])
bg7 = [chess.square_name(s) for s in b3.attacks(chess.parse_square('g7'))]
print('Bg7 attacks', bg7, '| Bf6 attacks', bf6)
m30 = gb[(30, chess.BLACK)]
print('R101 game position before move 30 (after 30.Bf1):'); print(m30)
print('  ', sqinfo(m30, 'f7'), 'files', files(m30))
m30b = m30.copy(); m30b.push_uci('d8f8'); print('  static after 30...Rf8 (SF best):', st(m30b, chess.BLACK))
m30c = m30.copy(); m30c.push_uci('c7a5'); print('  static after 30...Qa5 (played):', st(m30c, chess.BLACK))
m32 = gb[(32, chess.BLACK)]
print('R101 before 32 (after 32.Bc4):', sqinfo(m32, 'f7'))
for mv in (57, 61):
    pb = gb[(mv, chess.BLACK)]
    print(f'R101 move {mv} position (Black to move) FEN {pb.fen()}'); print(pb)
    print('  bishops', bishop_colours(pb), 'material(B view)', mat(pb, chess.BLACK), 'static', st(pb, chess.BLACK),
          'low_material_ref', low_material_reference(pb))
    for u in ([ 'b8a7', 'f7f6'] if mv == 57 else ['d6d6'][:0] + ['b8d6', 'g5g4', 'b8e5']):
        m = chess.Move.from_uci(u)
        if m in pb.legal_moves:
            c = pb.copy(); san = c.san(m); c.push(m)
            print(f'   child {san}: static(B view)={st(c, chess.BLACK):+d} mat={mat(c, chess.BLACK):+d}')
# 61...g4 follow-ups (no search: just the two natural pawn lines)
pb = gb[(61, chess.BLACK)]
for seq in (['g5g4', 'f3g4', 'f4f3'], ['g5g4', 'e6g4', 'g3g4'], ['b8d6', 'e6g4']):
    c = pb.copy(); sans = []
    ok = True
    for u in seq:
        m = chess.Move.from_uci(u)
        if m not in c.legal_moves:
            ok = False; break
        sans.append(c.san(m)); c.push(m)
    if ok:
        print('  line', ' '.join(sans), 'static(B view)', st(c, chess.BLACK), 'mat', mat(c, chess.BLACK), 'FEN', c.fen())

# ---------------- R102-10w
d, gb = game('R102-10w')
b = chess.Board(d['decisive']['fen'])
print('\nR102 m10 root:', sqinfo(b, 'h3'), '|', sqinfo(b, 'e5'), '| files', files(b))
for u in d['decisive']['sf_played_pv']:
    b.push_uci(u)
print('R102 after SF played PV (13...Qb6), White to move:'); print(b)
print('  ', sqinfo(b, 'b5'), '|', sqinfo(b, 'b2'), '|', sqinfo(b, 'e4'), '| files', files(b))
print('  bishops', bishop_colours(b))
saves = []
for m in b.legal_moves:
    c = b.copy(); san = c.san(m); c.push(m)
    bishop = [s for s in c.pieces(chess.BISHOP, chess.WHITE)]
    b_safe = all(not c.attackers(chess.BLACK, s) or c.attackers(chess.WHITE, s) for s in bishop) and len(bishop) == 1
    b2_safe = (not c.attackers(chess.BLACK, chess.B2)) or c.attackers(chess.WHITE, chess.B2) or c.piece_at(chess.B2) is None
    if b_safe and b2_safe:
        saves.append(san)
print('  White moves leaving bishop defended/unattacked AND b2 defended/unattacked:', saves)
b_d = chess.Board(d['decisive']['fen']); b_d.push_uci('b5e2')
print('R102 after 10.Be2:', sqinfo(b_d, 'h3'), '| f3', sqinfo(b_d, 'f3'))
print('R102 game material/file trajectory (RC-J=White):')
for mv in range(11, 31):
    k = (mv, chess.WHITE)
    if k in gb:
        pb = gb[k]
        print(f'  m{mv}: mat={mat(pb, chess.WHITE):+d} static={st(pb, chess.WHITE):+d} files={files(pb)} ')
