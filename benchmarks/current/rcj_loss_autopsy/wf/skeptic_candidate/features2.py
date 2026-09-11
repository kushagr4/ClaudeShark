"""Specific-feature test for the two narrow candidate features the agents named.

  rookfile: own rooks on open (+2) / half-open (+1) files minus the opponent's.
  blockedB: own bishops with <=2 pseudo-legal moves (a 'bad/blocked bishop'
            count) minus the opponent's.
Measured from the mover's POV after the move and at the end of each Stockfish
PV (played_pv / best_pv from the scan), for buckets GOOD / BAD / FLIP within
the 14 lost games. The sign that would help is: best line better on the feature.
No engines.
"""
import json, glob, sys
import chess

A = 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/'
rows = [json.loads(l) for l in open(A + 'scan_all.jsonl')]
decisive = {}
for f in glob.glob(A + 'bundles/*.json'):
    b = json.load(open(f))
    decisive[(b['round'], b['decisive']['move_number'])] = b['position_id']


def rookfile(b, c):
    s = 0
    for sq in b.pieces(chess.ROOK, c):
        f = chess.square_file(sq)
        mask = chess.BB_FILES[f]
        own = b.pieces_mask(chess.PAWN, c) & mask
        opp = b.pieces_mask(chess.PAWN, not c) & mask
        if not own and not opp:
            s += 2
        elif not own:
            s += 1
    return s


def blocked_bishops(b, c):
    bb = b.copy(stack=False); bb.turn = c; bb.ep_square = None
    cnt = {}
    for mv in bb.pseudo_legal_moves:
        p = bb.piece_at(mv.from_square)
        if p.piece_type == chess.BISHOP:
            cnt[mv.from_square] = cnt.get(mv.from_square, 0) + 1
    return sum(1 for sq in bb.pieces(chess.BISHOP, c) if cnt.get(sq, 0) <= 2)


def score(b, me):
    return (rookfile(b, me) - rookfile(b, not me),
            -(blocked_bishops(b, me) - blocked_bishops(b, not me)))  # higher = better for mover


def line(fen, pv):
    b = chess.Board(fen); me = b.turn
    out = []
    for i, u in enumerate(pv):
        try:
            b.push(chess.Move.from_uci(u))
        except Exception:
            break
        if i == 0:
            out.append(score(b, me))
    out.append(score(b, me))
    return out[0], out[-1]


B = {'GOOD': [], 'BAD': [], 'FLIP': []}
for r in rows:
    if r['same_move'] or r['cat_best'] == 'loss':
        continue
    if not r.get('best_pv') or not r.get('played_pv'):
        continue
    key = (r['round'], r['move_number'])
    pa, pe = line(r['fen'], r['played_pv'])
    ba, be = line(r['fen'], r['best_pv'])
    rec = dict(id=decisive.get(key, f"R{r['round']}-{r['move_number']}"),
               rf_after=ba[0] - pa[0], rf_end=be[0] - pe[0],
               bb_after=ba[1] - pa[1], bb_end=be[1] - pe[1])
    k = 'FLIP' if key in decisive else ('GOOD' if r['loss_cp'] <= 30 else ('BAD' if r['loss_cp'] >= 40 else None))
    if k:
        B[k].append(rec)

for k, L in B.items():
    n = len(L)
    def fr(key):
        pos = sum(1 for x in L if x[key] > 0); neg = sum(1 for x in L if x[key] < 0)
        return f"{key}: best+ {pos}/{n} best- {neg}/{n}"
    print(f"{k:4s} n={n:2d} | " + ' | '.join(fr(x) for x in ('rf_after', 'rf_end', 'bb_after', 'bb_end')))
print()
for x in B['FLIP']:
    print(x)
