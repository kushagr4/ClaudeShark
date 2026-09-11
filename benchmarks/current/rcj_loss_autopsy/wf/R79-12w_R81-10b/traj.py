"""Read-only trajectory/feature inspection. No engines, no search."""
import io, json, sys
import chess, chess.pgn
sys.path.insert(0, "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27")
import cs_eval  # interpreted PeSTO evaluator (reference path only)

B = "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/"
VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

print("active packed refs:", [getattr(f, "__name__", f) for f in cs_eval._PACKED_REFERENCE])
print("active post refs  :", [getattr(f, "__name__", f) for f in cs_eval._POST_REFERENCE])


def mat(b):
    return sum(VAL[p.piece_type] * (1 if p.color else -1) for p in b.piece_map().values())


def static(b, rcj_white):
    s = cs_eval.evaluate_reference(b)  # side-to-move POV
    white_pov = s if b.turn == chess.WHITE else -s
    return white_pov if rcj_white else -white_pov


def space(b, color):
    """Stockfish-classical-like space: own-half squares on files c-f, ranks 2-4
    (relative), not occupied by own pawn, not attacked by enemy pawn; +1 more if
    behind an own pawn (within 3 squares). Plus a queenside variant on files a-d."""
    enemy = not color
    epawn_att = chess.SquareSet()
    for sq in b.pieces(chess.PAWN, enemy):
        epawn_att |= b.attacks(sq)
    own_pawns = b.pieces(chess.PAWN, color)
    res = {}
    for name, files in (("center_c-f", range(2, 6)), ("queenside_a-d", range(0, 4))):
        cnt = 0
        for f in files:
            for rr in (1, 2, 3):
                r = rr if color == chess.WHITE else 7 - rr
                sq = chess.square(f, r)
                if sq in own_pawns or sq in epawn_att:
                    continue
                cnt += 1
                # behind own pawn?
                step = 8 if color == chess.WHITE else -8
                for k in (1, 2, 3):
                    s2 = sq + step * k
                    if 0 <= s2 < 64 and s2 in own_pawns:
                        cnt += 1
                        break
        res[name] = cnt
    return res


def pawn_files(b, color, files):
    return sum(1 for sq in b.pieces(chess.PAWN, color) if chess.square_file(sq) in files)


def mob(b, color):
    bb = b.copy(stack=False)
    bb.turn = color
    return sum(1 for m in bb.pseudo_legal_moves if bb.piece_type_at(m.from_square) != chess.PAWN)


def report(tag, b, rcj_white):
    c = chess.WHITE if rcj_white else chess.BLACK
    print(f"  {tag:34s} mat(RCJ)={mat(b)*(1 if rcj_white else -1):+d}  static(RCJ)={static(b, rcj_white):+4d}  "
          f"space own={space(b, c)} opp={space(b, not c)}  mob own/opp={mob(b, c)}/{mob(b, not c)}  "
          f"QS pawns a-c own/opp={pawn_files(b, c, range(0,3))}/{pawn_files(b, not c, range(0,3))}")


def game_traj(pid):
    d = json.load(open(B + pid + ".json"))
    rcj_white = d["rcj_colour"] == "white"
    g = chess.pgn.read_game(open(d["pgn_path"].replace("\\", "/")))
    sfb = {m["move_number"]: m for m in d["all_rcj_moves"]}
    b = g.board()
    print("=" * 100, pid, "RC-J", d["rcj_colour"])
    rows = []
    for node in g.mainline():
        mv = node.move
        mover_rcj = (b.turn == chess.WHITE) == rcj_white
        mn = b.fullmove_number
        if mover_rcj and mn in sfb:
            e = sfb[mn]
            before = static(b, rcj_white)
            san = b.san(mv)
            b.push(mv)
            rows.append((mn, san, e["best"], e["loss_cp"], e["best_cp"], e["E_best"], mat(b) * (1 if rcj_white else -1), before, static(b, rcj_white)))
        else:
            b.push(mv)
        if mn > 22:
            break
    print(" mv  san     sfbest  loss  SFbest_cp  E_best  mat_after  RCJstatic_before  RCJstatic_after")
    for r in rows:
        print(f" {r[0]:3d} {r[1]:7s} {r[2]:6s} {r[3]:5d} {r[4]:9d} {r[5]:7.2f} {r[6]:+9d} {r[7]:+16d} {r[8]:+15d}")
    return d, rcj_white


def pv_board(fen, pv, n=None):
    b = chess.Board(fen)
    for u in pv[: n if n is not None else len(pv)]:
        b.push_uci(u)
    return b


# ---------------------------------------------------------------- R79-12w
d, rw = game_traj("R79-12w")
fen = d["decisive"]["fen"]
root = chess.Board(fen)
print("\nR79 feature comparison (RC-J = white)")
report("root (before 12.)", root, rw)
report("after 12.Nb3", pv_board(fen, ["d2b3"]), rw)
report("after 12.Nb3 c4", pv_board(fen, ["d2b3", "c5c4"]), rw)
report("after 12.Rd1", pv_board(fen, ["f1d1"]), rw)
report("played pv_end", pv_board(fen, d["decisive"]["sf_played_pv"]), rw)
report("best pv_end", pv_board(fen, d["decisive"]["sf_best_pv"]), rw)
# can white recover the pawn at best pv_end?
be = pv_board(fen, d["decisive"]["sf_best_pv"])
print("  best pv_end FEN", be.fen(), "turn", "W" if be.turn else "B")
for sqn in ("c6", "d5", "g6", "b7"):
    sq = chess.parse_square(sqn)
    print(f"   {sqn}: piece={be.piece_at(sq)} W-attackers={[chess.square_name(s) for s in be.attackers(chess.WHITE, sq)]} "
          f"B-defenders={[chess.square_name(s) for s in be.attackers(chess.BLACK, sq)]}")
print("   Bf4 attacked by:", [chess.square_name(s) for s in be.attackers(chess.BLACK, chess.F4)])
# c4 square before/after: who controls it; after Nb3 does c4 hit the knight?
nb3 = pv_board(fen, ["d2b3"])
print("  after Nb3: Nb3 attacks", [chess.square_name(s) for s in nb3.attacks(chess.B3)],
      "| c5 defenders", [chess.square_name(s) for s in nb3.attackers(chess.BLACK, chess.C5)],
      "| a5 defenders", [chess.square_name(s) for s in nb3.attackers(chess.BLACK, chess.A5)])
c4 = pv_board(fen, ["d2b3", "c5c4"])
print("  after Nb3 c4: c4 pawn attacks", [chess.square_name(s) for s in c4.attacks(chess.C4)],
      "| c4 defenders", [chess.square_name(s) for s in c4.attackers(chess.BLACK, chess.C4)],
      "| Nb3 legal retreats", [c4.san(m) for m in c4.legal_moves if m.from_square == chess.B3])
# actual game position after 17...b4 and 23...b3
g = chess.pgn.read_game(open(d["pgn_path"].replace("\\", "/")))
b = g.board()
for node in g.mainline():
    b.push(node.move)
    tag = f"{b.fullmove_number - (0 if b.turn == chess.BLACK else 1)}{'.' if b.turn == chess.BLACK else '...'}{node.san()}"
    if node.san() in ("b4", "b3", "c4") or (b.fullmove_number in (19, 24) and b.turn == chess.WHITE):
        report("game after " + node.san() + f" (fm {b.fullmove_number})", b, rw)
    if b.fullmove_number > 25:
        break

# ---------------------------------------------------------------- R81-10b
d, rw = game_traj("R81-10b")
fen = d["decisive"]["fen"]
print("\nR81 feature comparison (RC-J = black)")
root = chess.Board(fen)
report("root (before 10...)", root, rw)
report("after 10...h6", pv_board(fen, ["h7h6"]), rw)
report("after 10...d5", pv_board(fen, ["d6d5"]), rw)
report("played pv_end", pv_board(fen, d["decisive"]["sf_played_pv"]), rw)
report("best pv_end", pv_board(fen, d["decisive"]["sf_best_pv"]), rw)
# the d5 tactic: after d5 exd5 Nxd5, what is on the g5-e7 diagonal and the d-file
t = pv_board(fen, ["d6d5", "e4d5", "f6d5"])
print("  after d5 exd5 Nxd5:", t.fen())
print("   Bg5 attacked by", [chess.square_name(s) for s in t.attackers(chess.BLACK, chess.G5)],
      "defended by", [chess.square_name(s) for s in t.attackers(chess.WHITE, chess.G5)])
print("   Nd5 attacks", [chess.square_name(s) for s in t.attacks(chess.D5)])
print("   Qd2 attacked by (x-ray if Nd5 moves):", [chess.square_name(s) for s in t.attackers(chess.BLACK, chess.D2)])
t2 = pv_board(fen, ["d6d5", "e4d5", "f6d5", "g5e7", "d5e7"])
print("   after Bxe7 Ndxe7: Qd2 attacked by", [chess.square_name(s) for s in t2.attackers(chess.BLACK, chess.D2)],
      "white in check?", t2.is_check(), "turn", "W" if t2.turn else "B")
# played-line: g4 vs Bh5 and the h6 hook
p = pv_board(fen, ["h7h6"])
print("  after h6: squares g5 attacked by black pawns?", chess.G5 in p.attacks(chess.H6),
      "| Bh5 retreat squares", [p.san(m) for m in p.legal_moves if m.from_square == chess.H5])
# queens on/off in each pv_end
for nm, pv in (("played", d["decisive"]["sf_played_pv"]), ("best", d["decisive"]["sf_best_pv"])):
    e = pv_board(fen, pv)
    print(f"  {nm} pv_end queens W/B = {len(e.pieces(chess.QUEEN, True))}/{len(e.pieces(chess.QUEEN, False))}, "
          f"white king {chess.square_name(e.king(True))}, black king {chess.square_name(e.king(False))}")
