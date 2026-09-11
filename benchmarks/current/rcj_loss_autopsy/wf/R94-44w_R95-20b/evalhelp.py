"""Shared helpers: interpreted PeSTO reference evaluator only. numba is blocked."""
import sys
sys.modules['numba'] = None  # any 'import numba' now raises ImportError
sys.path.insert(0, 'C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27')
import chess
import cs_terms
import cs_eval
from cs_constants import MG_WHITE, EG_WHITE, MG_BLACK, EG_BLACK, TOTAL_PHASE

print("registry terms:", sorted(cs_terms.BY_NAME), " env-default active:", sorted(cs_eval.ACTIVE_TERMS))
cs_eval.set_terms({'mopup'})  # RC-J ships PeSTO + bishop pair + tempo + mop-up only
print("now active:", sorted(cs_eval.ACTIVE_TERMS))

def phase_of(b):
    p = (b.knights | b.bishops).bit_count() + 2 * b.rooks.bit_count() + 4 * b.queens.bit_count()
    return min(p, TOTAL_PHASE)

def taper(mg, eg, ph):
    return (mg * ph + eg * (TOTAL_PHASE - ph)) / TOTAL_PHASE

def white_static(b):
    """RC-J reference eval, white-positive (strip tempo/side)."""
    s = cs_eval.evaluate_reference(b)
    s -= cs_eval.TEMPO
    return s if b.turn == chess.WHITE else -s

def piece_terms(b):
    ph = phase_of(b)
    out = []
    for sq, pc in sorted(b.piece_map().items()):
        if pc.color:
            mg, eg = MG_WHITE[pc.piece_type][sq], EG_WHITE[pc.piece_type][sq]
        else:
            mg, eg = -MG_BLACK[pc.piece_type][sq], -EG_BLACK[pc.piece_type][sq]
        out.append((pc.symbol(), chess.square_name(sq), mg, eg, round(taper(mg, eg, ph), 1)))
    return ph, out

def pawn_feats(b, colour):
    pawns = b.pieces(chess.PAWN, colour)
    files = [chess.square_file(s) for s in pawns]
    iso = sum(1 for s in pawns if not any(chess.square_file(t) in (chess.square_file(s) - 1, chess.square_file(s) + 1) for t in pawns))
    dbl = sum(files.count(f) - 1 for f in set(files))
    return {'pawns': len(pawns), 'isolated': iso, 'doubled': dbl}

def material(b):
    v = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9}
    w = sum(v[p.piece_type] for p in b.piece_map().values() if p.color and p.piece_type in v)
    k = sum(v[p.piece_type] for p in b.piece_map().values() if not p.color and p.piece_type in v)
    return w, k

def file_state(b, f):
    wp = any(chess.square_file(s) == f for s in b.pieces(chess.PAWN, chess.WHITE))
    bp = any(chess.square_file(s) == f for s in b.pieces(chess.PAWN, chess.BLACK))
    return 'open' if not wp and not bp else ('half-open(W)' if not wp else ('half-open(B)' if not bp else 'closed'))

def rook_report(b):
    rows = []
    for colour in (chess.WHITE, chess.BLACK):
        for sq in b.pieces(chess.ROOK, colour):
            mob = bin(int(b.attacks_mask(sq)) & ~int(b.occupied_co[colour])).count('1')
            rows.append((('W' if colour else 'B') + 'R' + chess.square_name(sq), file_state(b, chess.square_file(sq)), 'moves', mob))
    return rows

def play(fen, ucis):
    b = chess.Board(fen)
    san = []
    for u in ucis:
        m = chess.Move.from_uci(u)
        san.append(b.san(m))
        b.push(m)
    return b, ' '.join(san)
