"""Causal gate: round 54 move 103 with the live carried search state.

Replays the real game through the searcher exactly as the agent ran it, then
searches move 103 on the real remaining clock. Reports the move, the claimed
mate distance, the completed depth, the nodes, the time and the line the table
holds, and checks whether the chosen move actually keeps the mate.

usage: causal.py <build_dir> <label>
"""
import sys, os

BUILD = sys.argv[1]
LABEL = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(BUILD)
sys.path.insert(0, BUILD)

import chess, chess.pgn
import cs_core as core
import cs_fast

PGN = r"C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/live/pgn/aichessathon-round-54-nakamura.pgn"
BOUND = {core.BOUND_EXACT: "EXACT", core.BOUND_LOWER: "LOWER", core.BOUND_UPPER: "UPPER"}
DRAWING = "c5f5"       # the move played in the live game, which drew


def mate_plies(sc):
    if sc > core.MATE_BOUND:
        return core.MATE_SCORE - sc
    if sc < -core.MATE_BOUND:
        return core.MATE_SCORE + sc
    return None


def walk_pv(s, board, limit=30):
    b = board.copy()
    line = []
    for _ in range(limit):
        core.load_board(b, s.B, s.O, s.M, s.S)
        e = int(core.tt_probe(s.TK, s.TV, int(s.S[4])))
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
            return line, True
        if b.is_game_over(claim_draw=False):
            break
    return line, False


game = chess.pgn.read_game(open(PGN, encoding="utf-8", errors="replace"))
s = cs_fast.Searcher()
cs_fast.warm_up()
s.new_game()
board = game.board()
node = game
clock = 120.0
while node.variations:
    node = node.variations[0]
    if board.turn == chess.WHITE:
        if board.fullmove_number == 103:
            break
        s.search(board, int(clock * 1000))
        c = node.clock()
        if c is not None:
            clock = c
    board.push(node.move)

print(f"=== {LABEL}  round 54 move 103, carried state")
print(f"    {board.fen()}   clock {clock:.1f}s   history keys {len(s._game_keys)}")
mates = []
for mv in sorted(board.legal_moves, key=lambda m: m.uci()):
    b2 = board.copy()
    san = b2.san(mv)
    b2.push(mv)
    core.load_board(b2, s.B, s.O, s.M, s.S)
    e = int(core.tt_probe(s.TK, s.TV, int(s.S[4])))
    if e >= 0:
        adj = int(core.score_from_tt(int(core.tt_score(e)), 1))
        if abs(adj) > core.MATE_BOUND:
            mates.append(f"{san} d{int(core.tt_depth(e))} "
                         f"{BOUND.get(int(core.tt_bound(e)),'?')} mate_in {mate_plies(-adj)}")
print(f"    table already holds mate scores for: {', '.join(mates) if mates else 'none'}")

mv, info = s.search(board.copy(), int(clock * 1000))
line, ends_mate = walk_pv(s, board)
played_uci = mv.uci()
print(f"    MOVE            {board.san(mv)} ({played_uci})")
print(f"    SCORE           {info.score:+d}   mate_in {mate_plies(info.score)}")
print(f"    COMPLETED DEPTH {info.depth}")
print(f"    NODES           {info.nodes:,}")
print(f"    TIME            {info.elapsed_ms:.1f} ms   (budget {info.budget_ms:.0f} ms)")
print(f"    PV              {' '.join(line) if line else '(none)'}")
print(f"    PV ENDS MATE    {ends_mate}")
print(f"    EARLY STOP      {'yes' if info.depth < 60 and abs(info.score) > core.MATE_BOUND else 'n/a'}"
      f"   claim verifiable at completed depth: "
      f"{mate_plies(info.score) is not None and mate_plies(info.score) <= info.depth}")
print(f"    PLAYS THE LIVE DRAWING MOVE Rf5? {'YES  <-- live failure reproduced' if played_uci == DRAWING else 'no'}")
