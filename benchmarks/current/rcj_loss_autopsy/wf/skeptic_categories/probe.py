import sys,json
sys.path.insert(0,"C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27")
import chess, cs_eval
from cs_constants import MG_WHITE, EG_WHITE, MG_BLACK, EG_BLACK, TOTAL_PHASE
cs_eval.set_terms([])
PH={1:0,2:1,3:1,4:2,5:4,6:0}
def phase(b): return min(sum(PH[p.piece_type] for p in b.piece_map().values()),TOTAL_PHASE)
def pieces(b,color):
    ph=phase(b); out=[]
    for sq,p in b.piece_map().items():
        if p.color!=color or p.piece_type==1: continue
        mg=(MG_WHITE if color else MG_BLACK)[p.piece_type][sq]; eg=(EG_WHITE if color else EG_BLACK)[p.piece_type][sq]
        out.append((p.symbol()+chess.square_name(sq),round((mg*ph+eg*(24-ph))/24,1)))
    return sorted(out)
def ev(b,pov):
    s=cs_eval.evaluate_reference(b); return s if b.turn==pov else -s
def mob(b,color):
    bb=b.copy(); bb.turn=color; bb.ep_square=None; out={}
    for m in bb.pseudo_legal_moves:
        p=bb.piece_at(m.from_square)
        if p.piece_type==1: continue
        k=p.symbol()+chess.square_name(m.from_square); out[k]=out.get(k,0)+1
    return out
def leaf(pid,which):
    d=json.load(open(f'bundles/{pid}.json')); dc=d['decisive']
    b=chess.Board(dc['fen']); pv=dc['sf_played_pv' if which=='played' else 'sf_best_pv']
    for u in pv: b.push_uci(u)
    return b,d
col=lambda d: chess.WHITE if d['rcj_colour']=='white' else chess.BLACK
print('--- R88 leaves (Black RC-J)')
for w in ('played','best'):
    b,d=leaf('R88-17b',w); c=col(d)
    print(w,b.fen(),'phase',phase(b),'static',ev(b,c))
    print('  black',pieces(b,chess.BLACK)); print('  white',pieces(b,chess.WHITE))
    print('  mobW',sum(mob(b,chess.WHITE).values()),mob(b,chess.WHITE)); print('  mobB',sum(mob(b,chess.BLACK).values()),mob(b,chess.BLACK))
print('--- R81 leaves')
for w in ('played','best'):
    b,d=leaf('R81-10b',w)
    print(w,b.fen(),'Wk',chess.square_name(b.king(chess.WHITE)),'Bk',chess.square_name(b.king(chess.BLACK)),'queens',len(b.pieces(5,1)),len(b.pieces(5,0)),'castleB',b.has_castling_rights(chess.BLACK),'static(B)',ev(b,chess.BLACK))
    print('  attackers on Bk zone by W:',sum(len(b.attackers(chess.WHITE,s)) for s in chess.SquareSet(chess.BB_KING_ATTACKS[b.king(chess.BLACK)])))
print('--- R105 played PV mobility per ply (Black)')
d=json.load(open('bundles/R105-16b.json')); b=chess.Board(d['decisive']['fen'])
for i,u in enumerate(['START']+d['decisive']['sf_played_pv']):
    if u!='START': b.push_uci(u)
    m=mob(b,chess.BLACK); print(i,u,'Btot',sum(m.values()),'Bc8',m.get('bc8',0),'Rb8',m.get('rb8',0),'static(B)',ev(b,chess.BLACK))
b2=chess.Board(d['decisive']['fen'])
for u in d['decisive']['sf_best_pv']: b2.push_uci(u)
m=mob(b2,chess.BLACK); print('best leaf Btot',sum(m.values()),m,'static(B)',ev(b2,chess.BLACK))
print('--- R79 best leaf')
b,d=leaf('R79-12w','best'); print(b.fen(),'turn',b.turn,'hanging-check: attackers of c6 W',len(b.attackers(1,chess.C6)),'def B',len(b.attackers(0,chess.C6)),'static(W)',ev(b,chess.WHITE))
b,d=leaf('R79-12w','played'); print('played leaf',b.fen(),'static(W)',ev(b,chess.WHITE))
