import sys, json, io
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess, chess.pgn
import cs_eval

B = 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/'

def st(b, side):
    v = cs_eval.evaluate(b)
    return v if b.turn == side else -v

def mob(b, side):
    bb = b.copy(); bb.turn = side
    return sum(1 for m in bb.pseudo_legal_moves if bb.piece_type_at(m.from_square) != chess.PAWN)

def mat(b, side):
    val = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9, 6: 0}
    s = 0
    for sq, p in b.piece_map().items():
        s += val[p.piece_type] * (1 if p.color == side else -1)
    return s

def line(fen, pv, side, label):
    b = chess.Board(fen)
    print(f'--- {label}')
    print(f'  ply0 static={st(b, side):+d} mat={mat(b, side):+d}')
    for i, u in enumerate(pv):
        m = chess.Move.from_uci(u)
        san = b.san(m)
        b.push(m)
        print(f'  ply{i+1} {san:7s} static={st(b, side):+d} mat={mat(b, side):+d} mob_own={mob(b, side)} mob_opp={mob(b, not side)}')
    return b

def hanging(b, side):
    out = []
    for sq, p in b.piece_map().items():
        if p.color == side and p.piece_type != chess.KING:
            att = len(b.attackers(not side, sq)); dfn = len(b.attackers(side, sq))
            if att:
                out.append(f'{chess.square_name(sq)}{p.symbol()} att={att} def={dfn}')
    return out

def game_boards(pgn_path):
    g = chess.pgn.read_game(open(pgn_path))
    b = g.board(); res = {}
    for node in g.mainline():
        res[(b.fullmove_number, b.turn)] = b.copy()
        b.push(node.move)
    return res

for pid in ['R101-29b', 'R102-10w']:
    d = json.load(open(B + pid + '.json'))
    side = chess.WHITE if d['rcj_colour'] == 'white' else chess.BLACK
    dec = d['decisive']
    print('=' * 70); print(pid, d['rcj_colour'])
    b0 = chess.Board(dec['fen'])
    print(b0)
    print('rcj hanging/attacked pieces:', hanging(b0, side))
    print('opp attacked pieces:', hanging(b0, not side))
    line(dec['fen'], dec['sf_played_pv'], side, 'SF played PV')
    line(dec['fen'], dec['sf_best_pv'], side, 'SF best PV')
    # per-move static along game vs SF best_cp
    gb = game_boards(d['pgn_path'].replace('\\', '/'))
    print('game: move san | rcj_static(before move, RC-J view) | SF best_cp | loss')
    for r in d['all_rcj_moves']:
        key = (r['move_number'], side)
        if key in gb:
            bb = gb[key]
            print(f"  {r['move_number']:3d} {r['san']:6s} static={st(bb, side):+5d} sf_best={r['best_cp']:+5d} loss={r['loss_cp']:4d} E={r['E_best']:.2f} {r['cat']}")
        if r['move_number'] > dec['move_number'] + 12 and pid == 'R102-10w':
            break
