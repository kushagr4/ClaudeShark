"""Read-only. Would START_FRACTION 0.50 (C22) start one more iteration than 0.45 at each position, on the
cold timeline? An extra iteration starts only if the depth-d iteration completes inside
[0.45*soft, 0.50*soft). It then completes only if cumulative d+1 time < hard (3*soft cap).
Also: could ANY start fraction (1.0) reach the GOOD depth? Timings are the autopsy machine's cold ladder."""
import json, chess
A = "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/autopsy"
lad = {r["id"]: r for f in ("ladder.json","ladder_sup.json") for r in json.load(open(f"{A}/{f}", encoding="utf-8"))}
rep = {r["id"]: r for r in json.load(open(f"{A}/repair.json", encoding="utf-8"))}
ver = {r["id"]: r for f in ("verify.json","verify_sup.json") for r in json.load(open(f"{A}/{f}", encoding="utf-8"))}
def phase(b):
    return min(24, sum(w*(len(b.pieces(p,True))+len(b.pieces(p,False))) for p,w in ((2,1),(3,1),(4,2),(5,4))))
cnt = dict(trig=0, n=0)
for pid, L in lad.items():
    r = rep[pid]
    if not r.get("confirmed"): continue
    b = chess.Board(L["fen"]); clk = L["timed"]["clock_in_ms"]; usable = clk-240
    soft = usable/(26 if phase(b) > 8 else 20) + min(500, usable)*0.75; hard = min(usable*0.33, 3*soft); soft = min(soft, hard)
    t = [x["seconds"]*1000 for x in L["ladder"]]; td = L["timed"]["seconds"]*1000
    trig = 0.45*soft <= td < 0.50*soft
    good_idx = [i for i, x in enumerate(r["ladder"]) if x["tag"] == "GOOD"]
    first_good = good_idx[0] if good_idx else None
    reach = "n/a"
    if first_good:  # can the GOOD depth be reached at all? needs depth (first_good-1) to finish before soft*SF and first_good to finish before hard
        prev_done = t[first_good-1]; fin = t[first_good]
        reach = f"needs d+{first_good}: prev iter done {prev_done/1000:.2f}s vs soft {soft/1000:.2f}s (SF=1.0 start {'OK' if prev_done < soft else 'NO'}), finish {fin/1000:.2f}s vs hard {hard/1000:.2f}s ({'OK' if fin < hard else 'ABORTED'})"
    cnt["n"] += 1; cnt["trig"] += trig
    nxt = r["ladder"][1]
    print(f"{pid:10s} set={r['set'][:3]} td={td/1000:5.2f} window=[{0.45*soft/1000:.2f},{0.50*soft/1000:.2f}) C22_extra_iter={'YES' if trig else 'no ':3s} "
          f"-> d+1 move {nxt['move']} {nxt['tag']} (E {ver[pid]['moves'].get(nxt['move'],{}).get('E')}) | {reach}")
print(cnt)
