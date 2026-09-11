"""Base-rate control for the two correlates the agents leaned on.

Within the 14 lost games only (no W/D games were scanned), compare Stockfish's
best move against RC-J's played move on:
  * own pseudo-legal non-pawn mobility after the move (incl. king),
  * count of own non-pawn, non-king pieces with <=1 pseudo-legal move (trapped),
  * RC-J PeSTO static eval after the move, mover's POV (tempo-neutral diff).
Buckets: GOOD (different move, loss<=30, not yet lost), BAD (loss>=40, not yet
lost), FLIP (the 14 frozen decisive positions). No engines; python-chess plus
the interpreted evaluator only.
"""
import json, sys, statistics as st
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess
import cs_eval
cs_eval.set_terms(['mopup'])

A = 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/'
rows = [json.loads(l) for l in open(A + 'scan_all.jsonl')]
dec = {(r['round'], r['move_number']) for r in []}
import glob
decisive = {}
for f in glob.glob(A + 'bundles/*.json'):
    b = json.load(open(f))
    decisive[(b['round'], b['decisive']['move_number'])] = b['position_id']


def mob(board, colour):
    b = board.copy(stack=False)
    b.turn = colour
    b.ep_square = None
    n = 0
    per = {}
    for mv in b.pseudo_legal_moves:
        p = b.piece_at(mv.from_square)
        if p.piece_type == chess.PAWN:
            continue
        n += 1
        per[mv.from_square] = per.get(mv.from_square, 0) + 1
    trapped = 0
    for sq, p in b.piece_map().items():
        if p.color == colour and p.piece_type not in (chess.PAWN, chess.KING):
            if per.get(sq, 0) <= 1:
                trapped += 1
    return n, trapped


def feats(fen, uci):
    b = chess.Board(fen)
    me = b.turn
    b.push(chess.Move.from_uci(uci))
    m_own, tr = mob(b, me)
    m_opp, _ = mob(b, not me)
    static = -cs_eval.evaluate(b)  # mover's POV (+ constant tempo offset)
    return m_own, m_opp, tr, static


buckets = {'GOOD': [], 'BAD': [], 'FLIP': []}
for r in rows:
    if r['same_move'] or r['cat_best'] == 'loss':
        continue
    key = (r['round'], r['move_number'])
    try:
        p = feats(r['fen'], r['played'])
        q = feats(r['fen'], r['best'])
    except Exception as e:
        continue
    rec = dict(id=f"R{r['round']}-{r['move_number']}", game=r['round'], loss=r['loss_cp'],
               d_own=q[0] - p[0], d_net=(q[0] - q[1]) - (p[0] - p[1]), d_trap=q[2] - p[2],
               d_static=q[3] - p[3])
    if key in decisive:
        buckets['FLIP'].append(rec)
    elif r['loss_cp'] <= 30:
        buckets['GOOD'].append(rec)
    elif r['loss_cp'] >= 40:
        buckets['BAD'].append(rec)


def summ(name, L):
    if not L:
        print(name, 'empty'); return
    n = len(L)
    f = lambda k, c: sum(1 for x in L if c(x[k])) / n
    print(f"{name:5s} n={n:3d} games={len({x['game'] for x in L}):2d} | "
          f"best own-mob higher {f('d_own', lambda v: v > 0):.2f} (mean {st.mean(x['d_own'] for x in L):+.2f}) | "
          f"best net-mob higher {f('d_net', lambda v: v > 0):.2f} (mean {st.mean(x['d_net'] for x in L):+.2f}) | "
          f"best fewer trapped {f('d_trap', lambda v: v < 0):.2f} more {f('d_trap', lambda v: v > 0):.2f} | "
          f"PeSTO prefers played {f('d_static', lambda v: v < 0):.2f} (mean {st.mean(x['d_static'] for x in L):+.1f}, median {st.median(x['d_static'] for x in L):+.0f})")


for k in ('GOOD', 'BAD', 'FLIP'):
    summ(k, buckets[k])
print()
for x in sorted(buckets['FLIP'], key=lambda x: x['game']):
    print(decisive[(x['game'], int(x['id'].split('-')[1]))], x)
json.dump(buckets, open(A + 'wf/skeptic_candidate/control_out.json', 'w'), indent=1)
