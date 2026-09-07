"""Deterministic conversion playout: strong side searched, defender fixed.

The defender is a fixed rule, not an engine, so the only thing that varies
between builds is the strong side's conversion skill. Fixed search depth makes
each run reproducible; no wall-clock budget is involved.

usage: playout.py <build_dir> <fen> <label> <depth> [max_plies]
"""
import sys, os

BUILD = sys.argv[1]
FEN = sys.argv[2]
LABEL = sys.argv[3]
DEPTH = int(sys.argv[4])
MAXPLY = int(sys.argv[5]) if len(sys.argv) > 5 else 120
sys.path.insert(0, BUILD)

import chess
import cs_fast


def cheb(a, b):
    return max(abs(chess.square_file(a) - chess.square_file(b)),
               abs(chess.square_rank(a) - chess.square_rank(b)))


def centrality(sq):
    f, r = chess.square_file(sq), chess.square_rank(sq)
    return min(f, 7 - f) + min(r, 7 - r)


def defender_move(board, strong):
    """Run from the strong king, stay central, break ties by UCI order."""
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


s = cs_fast.Searcher()
cs_fast.warm_up()
s.new_game()
b = chess.Board(FEN)
assert b.is_valid(), f"invalid fixture {FEN}"
strong = b.turn
plies = 0
first_mate_claim = None
while plies < MAXPLY and not b.is_game_over(claim_draw=True):
    if b.turn == strong:
        mv, info = s.search(b, 0, max_depth=DEPTH)
        if abs(info.score) > 29000 and first_mate_claim is None:
            first_mate_claim = plies
    else:
        mv = defender_move(b, strong)
    if mv is None:
        break
    b.push(mv)
    plies += 1
oc = b.outcome(claim_draw=True)
term = oc.termination.name if oc else "NO_PROGRESS"
won = bool(oc and oc.termination == chess.Termination.CHECKMATE and oc.winner == strong)
print(f"RESULT {LABEL} build={os.path.basename(BUILD)} depth={DEPTH} "
      f"{'MATE' if won else 'FAIL'} plies={plies} term={term} "
      f"first_mate_claim={first_mate_claim} final={b.fen()}")
