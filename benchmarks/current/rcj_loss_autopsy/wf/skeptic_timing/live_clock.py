"""Read-only: live clock spent on each decisive / supplementary move, from PGN [%clk] comments."""
import json, re, glob, os, sys
import chess.pgn
A = "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy"
rep = {r["id"]: r for r in json.load(open(f"{A}/repair.json", encoding="utf-8"))}
def clk(c):
    m = re.search(r"\[%clk\s+(\d+):(\d+):(\d+(?:\.\d+)?)\]", c or "")
    return None if not m else int(m[1])*3600+int(m[2])*60+float(m[3])
for f in sorted(glob.glob(f"{A}/bundles/*.json")):
    b = json.load(open(f, encoding="utf-8"))
    pid = b["position_id"]; col = b["rcj_colour"]
    g = chess.pgn.read_game(open(b["pgn_path"], encoding="utf-8", errors="replace"))
    hdr = dict(g.headers)
    # collect (move_number, colour, clock_after) for every node
    prev = {True: None, False: None}; rows = {}
    board = g.board(); node = g
    while node.variations:
        nxt = node.variations[0]
        turn = board.turn; mn = board.fullmove_number
        c = clk(nxt.comment)
        rows[(mn, turn)] = (prev[turn], c, nxt.comment[:80])
        prev[turn] = c
        board.push(nxt.move); node = nxt
    want = [(pid, b["decisive"]["move_number"])]
    for s in b.get("supplementary_serious_errors_depth_tested", []) or []:
        sid = s.get("id") or s.get("position_id")
        if sid: want.append((sid, s.get("move_number")))
    for sid, mn in want:
        if mn is None:
            m = re.match(r"R\d+-(\d+)", sid); mn = int(m[1])
        t = col == "white"
        before, after, com = rows.get((mn, t), (None, None, ""))
        r = rep.get(sid, {})
        ct = r.get("cold_timed", {})
        spent = None if before is None or after is None else round(before - after, 2)
        print(f"{sid:10s} tc={hdr.get('TimeControl','?'):8s} clk_before={before} clk_after={after} live_spent={spent} "
              f"| cold: clk_in={ct.get('clock_in_ms')} d={ct.get('depth')} sec={ct.get('seconds')} move={ct.get('move')} repro={not r.get('state_dependent')} | comment={com!r}")
