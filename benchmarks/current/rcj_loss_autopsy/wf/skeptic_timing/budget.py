"""Read-only: soft budget, START_FRACTION threshold (0.45 shipped vs 0.50 C22), live think estimate,
cold ladder timings, and a result-category (E) view of each ladder move. No engine is imported."""
import json, chess
A = "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy"
INC, OVH, RES, SH = 500.0, 40.0, 200.0, 0.75
live_delta = {"R79-12w":1.69,"R81-10b":1.79,"R83-20w":1.56,"R88-17b":1.61,"R91-13w":1.71,"R92-9b":3.45,"R94-44w":1.00,
 "R95-20b":1.14,"R98-25w":2.24,"R99-25b":2.57,"R101-29b":1.01,"R102-10w":2.71,"R103-25w":3.98,"R105-16b":1.59,
 "R81-8bs":2.715,"R94-33ws":1.60,"R94-35ws":1.41,"R101-52bs":1.06,"R101-57bs":1.25,"R101-61bs":1.13}
def phase(b):
    p = 0
    for pt, w in ((chess.KNIGHT,1),(chess.BISHOP,1),(chess.ROOK,2),(chess.QUEEN,4)):
        p += w * (len(b.pieces(pt, True)) + len(b.pieces(pt, False)))
    return min(p, 24)
def cat(E): return "W" if E >= 0.75 else "L" if E <= 0.25 else "D"
rep = {r["id"]: r for r in json.load(open(f"{A}/repair.json", encoding="utf-8"))}
lad = {r["id"]: r for f in ("ladder.json","ladder_sup.json") for r in json.load(open(f"{A}/{f}", encoding="utf-8"))}
ver = {r["id"]: r for f in ("verify.json","verify_sup.json") for r in json.load(open(f"{A}/{f}", encoding="utf-8"))}
print(f"{'id':10s} ph clk   soft  thr45 thr50 cold_s live_think  d  ladder seconds (d,d+1,d+2) ratio(d+1/d)  | E: best/live -> ladder moves (cat)")
for pid, L in lad.items():
    b = chess.Board(L["fen"]); ph = phase(b); clk = L["timed"]["clock_in_ms"]
    usable = clk - OVH - RES; mtg = 26 if ph > 8 else 20
    soft = usable / mtg + min(INC, usable) * SH; hard = min(usable * 0.33, soft * 3)
    soft = min(soft, hard)
    v = ver[pid]; best = v["best"]["E"]; live = v["moves"][L["played"]]["E"]
    secs = [x["seconds"] for x in L["ladder"]]
    lt = live_delta[pid] + INC/1000 - OVH/1000
    Es = [(x["move"], v["moves"].get(x["move"], {}).get("E")) for x in L["ladder"]]
    es = " ".join(f"{m}:{e}({cat(e)})" for m, e in Es)
    print(f"{pid:10s} {ph:2d} {clk/1000:5.1f} {soft/1000:5.2f} {0.45*soft/1000:5.2f} {0.50*soft/1000:5.2f} {L['timed']['seconds']:5.2f} {lt:6.2f}     {L['timed']['depth']:2d} "
          f"{secs}  {secs[1]/secs[0]:4.2f}  | {best}({cat(best)})/{live}({cat(live)}) -> {es}  cls={rep[pid]['cls']}")
