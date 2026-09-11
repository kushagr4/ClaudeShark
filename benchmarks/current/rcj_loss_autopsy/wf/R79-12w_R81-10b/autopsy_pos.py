import json, chess
B = "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy/bundles/"

def line(fen, uci_list):
    b = chess.Board(fen)
    out = []
    for u in uci_list:
        m = chess.Move.from_uci(u)
        out.append(b.san(m))
        b.push(m)
    return " ".join(out), b

for pid in ["R79-12w", "R81-10b"]:
    d = json.load(open(B + pid + ".json"))
    dec = d["decisive"]
    b = chess.Board(dec["fen"])
    print("=" * 60, pid)
    print(b)
    print(dec["fen"])
    s, bb = line(dec["fen"], dec["sf_best_pv"])
    print("SF best PV :", s)
    print(bb, "\n", bb.fen())
    s, bb = line(dec["fen"], dec["sf_played_pv"])
    print("played PV  :", s)
    print(bb, "\n", bb.fen())
