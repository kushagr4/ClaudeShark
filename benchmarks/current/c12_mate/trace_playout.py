"""Where does a mate claim stop being executable?

Plays the strong side from a live position against the fixed defender and, at
every move, records the claimed mate distance, the completed root depth, the
node count, and whether the claimed line is still legal and still ends in mate.
A claim whose distance fails to fall while moves are being played is the
signature of the defect.

usage: trace_playout.py <build_dir> <fen> <label> <depth> [max_plies]
"""
import sys, os

BUILD = sys.argv[1]
FEN = sys.argv[2]
LABEL = sys.argv[3]
DEPTH = int(sys.argv[4])
MAXPLY = int(sys.argv[5]) if len(sys.argv) > 5 else 60
sys.path.insert(0, BUILD)

import chess
import cs_core as core
import cs_fast

BOUND = {core.BOUND_EXACT: "EXACT", core.BOUND_LOWER: "LOWER", core.BOUND_UPPER: "UPPER"}


def mate_dist(score):
    if score > core.MATE_BOUND:
        return core.MATE_SCORE - score
    if score < -core.MATE_BOUND:
        return -(core.MATE_SCORE + score)
    return None


def cheb(a, b):
    return max(abs(chess.square_file(a) - chess.square_file(b)),
               abs(chess.square_rank(a) - chess.square_rank(b)))


def centrality(sq):
    f, r = chess.square_file(sq), chess.square_rank(sq)
    return min(f, 7 - f) + min(r, 7 - r)


def defender_move(board, strong):
    sk = board.king(strong)
    best = None
    for m in sorted(board.legal_moves, key=lambda x: x.uci()):
        board.push(m)
        wk = board.king(not strong)
        key = (cheb(wk, sk), centrality(wk))
        board.pop()
        if best is None or key > best[0]:
            best = (key, m)
    return best[1]


def probe_child(s, board, mv):
    b = board.copy()
    b.push(mv)
    core.load_board(b, s.B, s.O, s.M, s.S)
    e = int(core.tt_probe(s.TK, s.TV, int(s.S[4])))
    if e < 0:
        return None
    return (int(core.tt_depth(e)), BOUND.get(int(core.tt_bound(e)), "?"),
            int(core.score_from_tt(int(core.tt_score(e)), 1)))


def walk_pv(s, board, limit=30):
    b = board.copy()
    line = []
    seen_history = False
    for _ in range(limit):
        core.load_board(b, s.B, s.O, s.M, s.S)
        k = int(s.S[4])
        if k in s._game_keys and line:
            seen_history = True
        e = int(core.tt_probe(s.TK, s.TV, k))
        if e < 0 or not core.tt_move(e):
            break
        try:
            mv = chess.Move.from_uci(core.move_to_uci(int(core.tt_move(e))))
        except ValueError:
            break
        if mv not in b.legal_moves:
            line.append("ILLEGAL")
            break
        line.append(b.san(mv))
        b.push(mv)
        if b.is_checkmate():
            return line, True, seen_history
        if b.is_game_over(claim_draw=False):
            break
    return line, False, seen_history


s = cs_fast.Searcher()
cs_fast.warm_up()
s.new_game()
b = chess.Board(FEN)
strong = b.turn
print(f"=== {LABEL} build={os.path.basename(BUILD)} fixed depth {DEPTH}")
print(f"    {FEN}")
print(f"  {'ply':>3} {'move':7s} {'score':>7s} {'mate':>5s} {'d':>2} {'nodes':>8s} "
      f"{'PVmate':6s} {'PVhist':6s}  claimed line")
plies = 0
while plies < MAXPLY and not b.is_game_over(claim_draw=True):
    if b.turn == strong:
        core.load_board(b, s.B, s.O, s.M, s.S)
        k = int(s.S[4])
        if k not in s._game_keys and len(s._game_keys) < cs_fast.GAME_KEYS:
            s._game_keys.append(k)
            s.GK[len(s._game_keys) - 1] = k
        s.CTL[10] = len(s._game_keys)
        mv, info = s.search(b, 0, max_depth=DEPTH)
        md = mate_dist(info.score)
        line, ends_mate, hist = walk_pv(s, b)
        print(f"  {plies:3d} {b.san(mv):7s} {info.score:+7d} {str(md):>5s} {info.depth:2d} "
              f"{info.nodes:>8,} {str(ends_mate):6s} {str(hist):6s}  {' '.join(line[:14])}")
    else:
        mv = defender_move(b, strong)
    b.push(mv)
    plies += 1
oc = b.outcome(claim_draw=True)
print(f"  RESULT {oc.termination.name if oc else 'NO_PROGRESS'} after {plies} plies")
