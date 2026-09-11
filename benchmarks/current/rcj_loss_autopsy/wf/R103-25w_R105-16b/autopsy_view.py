import chess, chess.pgn, json, sys

B = "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/"


def show_line(fen, uci_list, label):
    b = chess.Board(fen)
    sans = []
    for u in uci_list:
        m = chess.Move.from_uci(u)
        if m not in b.legal_moves:
            sans.append("ILLEGAL(" + u + ")")
            break
        sans.append(b.san(m))
        b.push(m)
    print(label, " ".join(sans))
    print(b)
    print(b.fen())
    print()
    return b


def attackers_report(b, sq_names):
    for s in sq_names:
        sq = chess.parse_square(s)
        w = [chess.square_name(x) for x in b.attackers(chess.WHITE, sq)]
        bl = [chess.square_name(x) for x in b.attackers(chess.BLACK, sq)]
        print(f"  {s}: piece={b.piece_at(sq)} W-att={w} B-att={bl}")


for pid in ["R103-25w", "R105-16b"]:
    d = json.load(open(B + pid + ".json"))
    fen = d["decisive"]["fen"]
    print("=" * 70)
    print(pid, d["decisive"]["san"], "best", d["decisive"]["sf_best_scan"])
    b = chess.Board(fen)
    print(b)
    print("legal:", len(list(b.legal_moves)))
    show_line(fen, d["decisive"]["sf_best_pv"], "BEST PV:")
    show_line(fen, d["decisive"]["sf_played_pv"], "PLAYED PV:")

# game replay: print board at prior move for both
for pid in ["R103-25w", "R105-16b"]:
    d = json.load(open(B + pid + ".json"))
    g = chess.pgn.read_game(open(d["pgn_path"].replace("\\", "/")))
    b = g.board()
    print("=" * 70, pid)
    for node in g.mainline():
        mv = node.move
        n = b.fullmove_number
        side = "w" if b.turn else "b"
        if (pid == "R103-25w" and 20 <= n <= 27) or (pid == "R105-16b" and 10 <= n <= 18):
            print(f"{n}{'.' if side=='w' else '...'} {b.san(mv)}   FEN before: {b.fen()}")
        b.push(mv)
