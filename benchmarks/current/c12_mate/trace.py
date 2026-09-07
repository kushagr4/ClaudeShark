"""Root-cause trace for the round 54 mate-score failure.

Rebuilds the live search state, then reproduces the root iterative-deepening
loop by hand so every iteration, every transposition-table hit and every early
exit is visible. Also reconstructs the principal variation the engine claims
and checks whether following it actually reaches checkmate.

usage: trace.py <build_dir> <mode>
  mode: live93   replay the real game to move 93 and then play the engine's
                 own moves, which is where the bogus claims begin
        live103  replay the real game to move 103 with carried state
"""
import sys, os

BUILD = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else "live103"
sys.path.insert(0, BUILD)

import chess, chess.pgn
import cs_core as core
import cs_fast

PGN = r"C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/live/pgn/aichessathon-round-54-nakamura.pgn"
BOUND = {0: "?", core.BOUND_EXACT: "EXACT", core.BOUND_LOWER: "LOWER",
         core.BOUND_UPPER: "UPPER"}


def args(s):
    return (s.B, s.O, s.M, s.S, s.U, s.MLS, s.MSS, s.PATH, s.GK, s.TK, s.TV,
            s.KILL, s.HIST, s.CTL, s.TCTL, s.GAINS)


def key_of(s, board):
    core.load_board(board, s.B, s.O, s.M, s.S)
    return int(s.S[4])


def probe(s, board, ply):
    """What the table says about this position, denormalised for `ply`."""
    k = key_of(s, board)
    e = int(core.tt_probe(s.TK, s.TV, k))
    if e < 0:
        return None
    raw = int(core.tt_score(e))
    return dict(depth=int(core.tt_depth(e)), bound=BOUND.get(int(core.tt_bound(e)), "?"),
                raw=raw, adjusted=int(core.score_from_tt(raw, ply)),
                move=core.move_to_uci(int(core.tt_move(e))) if core.tt_move(e) else None)


def mate_dist(score):
    if score > core.MATE_BOUND:
        return core.MATE_SCORE - score
    if score < -core.MATE_BOUND:
        return -(core.MATE_SCORE + score)
    return None


def walk_pv(s, board, limit=24):
    """Follow the table's stored moves and report where the line actually goes."""
    b = board.copy()
    line = []
    for _ in range(limit):
        info = probe(s, b, 0)
        if not info or not info["move"]:
            break
        try:
            mv = chess.Move.from_uci(info["move"])
        except ValueError:
            break
        if mv not in b.legal_moves:
            line.append(f"{info['move']}(ILLEGAL)")
            break
        line.append(b.san(mv))
        b.push(mv)
        if b.is_game_over(claim_draw=False):
            break
    return line, b


def manual_id(s, board, max_depth=64, label=""):
    """cs_fast.search's root loop, printed iteration by iteration."""
    legal = list(board.legal_moves)
    core.load_board(board, s.B, s.O, s.M, s.S)
    s.CTL[:10] = 0
    s.HIST >>= 1
    s.TCTL[0] = 1e18
    root_key = int(s.S[4])
    if root_key not in s._game_keys and len(s._game_keys) < cs_fast.GAME_KEYS:
        s._game_keys.append(root_key)
        s.GK[len(s._game_keys) - 1] = root_key
    s.CTL[10] = len(s._game_keys)
    ROOT, RS = s.ROOT, s.RS
    n = len(legal)
    for i, mv in enumerate(legal):
        ROOT[i] = core.encode_move(board, mv)
    e = int(core.tt_probe(s.TK, s.TV, root_key))
    ttm = int(core.tt_move(e)) if e >= 0 else 0
    ML, MS = s.MLS[0], s.MSS[0]
    ML[:n] = ROOT[:n]
    core.score_moves(s.B, s.O, s.M, s.S, ML, MS, n, ttm, s.KILL[0], s.KILL[1], s.HIST, s.GAINS)
    order = sorted(range(n), key=lambda i: -int(MS[i]))
    root_moves = [int(ROOT[i]) for i in order]
    print(f"  root TT entry: {probe(s, board, 0)}")
    print(f"  {'d':>2} {'move':7s} {'score':>7s} {'mate_in':>7s} {'nodes':>9s}  note")
    best_move, best_score = root_moves[0], 0
    for depth in range(1, max_depth + 1):
        s.CTL[5] = 0
        s.CTL[9] = depth
        before = int(s.CTL[2])
        for i, mv in enumerate(root_moves):
            ROOT[i] = mv
        sc, mv = core.search_root(*args(s), ROOT, RS, len(root_moves), depth,
                                  -core.INFINITY, core.INFINITY)
        sc, mv = int(sc), int(mv)
        nodes = int(s.CTL[2]) - before
        best_move, best_score = mv, sc
        md = mate_dist(sc)
        note = ""
        if md is not None:
            note = f"MATE CLAIM in {md} plies; completed depth {depth}"
            if md > depth:
                note += "  <-- UNVERIFIABLE at this depth"
        print(f"  {depth:2d} {core.move_to_uci(mv):7s} {sc:+7d} {str(md):>7s} {nodes:>9,}  {note}")
        order = sorted(range(len(root_moves)), key=lambda i: -int(RS[i]))
        root_moves = [root_moves[i] for i in order]
        if abs(sc) > core.MATE_BOUND:
            print(f"  -> iterative deepening STOPS here (abs score > MATE_BOUND)")
            break
    return best_move, best_score


game = chess.pgn.read_game(open(PGN, encoding="utf-8", errors="replace"))
s = cs_fast.Searcher()
cs_fast.warm_up()
s.new_game()

target = 103 if MODE == "live103" else 93
board = game.board()
node = game
clock = 120.0
print(f"=== build {os.path.basename(BUILD)} mode {MODE}: replaying with carried state to move {target}")
while node.variations:
    node = node.variations[0]
    if board.turn == chess.WHITE:
        if board.fullmove_number == target:
            break
        s.search(board, int(clock * 1000))
        c = node.clock()
        if c is not None:
            clock = c
    board.push(node.move)

print(f"position: {board.fen()}")
print(f"game-history keys carried: {len(s._game_keys)}   clock {clock:.1f}s")
print(f"\n-- what the table already holds for each root move's child (ply 1) --")
for mv in sorted(board.legal_moves, key=lambda m: m.uci()):
    b2 = board.copy()
    san = b2.san(mv)
    b2.push(mv)
    info = probe(s, b2, 1)
    if info:
        md = mate_dist(info["adjusted"])
        print(f"   {san:7s} depth {info['depth']:2d} {info['bound']:5s} raw {info['raw']:+7d} "
              f"-> at ply1 {info['adjusted']:+7d} mate_in {md}")
print(f"\n-- root iterative deepening, replayed by hand --")
mv, sc = manual_id(s, board)
print(f"\n  chosen {core.move_to_uci(mv)} score {sc:+d} mate_in {mate_dist(sc)}")
line, endb = walk_pv(s, board)
print(f"  table PV: {' '.join(line) if line else '(none)'}")
print(f"  PV ends checkmate={endb.is_checkmate()} stalemate={endb.is_stalemate()} "
      f"after {len(line)} plies")
