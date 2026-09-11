"""Deterministic depth-repair classification (frozen before reading any ladder result).

Every move is judged by the Stockfish 10M-node verification from the SAME root, with
loss_cp relative to that root's best move:
  GOOD  = verified loss <= 30 cp            BAD = verified loss >= 40 cp
  (30-40 cp is GREY; a grey move never counts as a repair.)
Per position, using RC-J's cold ladder at the reconstructed depth d, d+1, d+2:
  CONFIRMED error   : the live move is BAD at 10M nodes (otherwise NOT CONFIRMED)
  STATE-DEPENDENT   : cold RC-J at the recorded clock does NOT play the live move
  REPAIRED BY DEPTH : the move at d is BAD, the move at the deepest completed depth is
                      GOOD, and every depth after the first GOOD one stays GOOD
  NOT REPAIRED      : every ladder depth plays a BAD move
  UNSTABLE          : any other pattern (bad->good->bad, grey moves, state-dependent)
  UNKNOWN           : a needed verification is missing or bound-only
Also reported: whether +1 ply alone (d+1) is GOOD -- the quantity C22's +0.26 mean
completed ply could at best buy.
"""
import json, sys
A = sys.argv[1]
GOOD, BAD = 30, 40
def load(name):
    try: return json.load(open(f"{A}/{name}", encoding="utf-8"))
    except FileNotFoundError: return []
rows = []
for lad_f, ver_f, tag in (("ladder.json", "verify.json", "decisive"), ("ladder_sup.json", "verify_sup.json", "supplementary")):
    ver = {v["id"]: v for v in load(ver_f)}
    for r in load(lad_f):
        v = ver.get(r["id"])
        if not v:
            rows.append(dict(id=r["id"], set=tag, cls="UNKNOWN", why="no verification")); continue
        def loss(u):
            m = v["moves"].get(u)
            if not m: return None, None
            return m["loss_cp"], m["bound"]
        live_loss, live_b = loss(r["played"])
        lad = [(x["depth"], x["move"], *loss(x["move"])) for x in r["ladder"]]
        state_dep = not r["reproduces_live"]
        tag_move = lambda l: None if l is None else ("GOOD" if l <= GOOD else "BAD" if l >= BAD else "GREY")
        seq = [tag_move(l) for _, _, l, _ in lad]
        inexact = any(b not in (None, "exact") for _, _, _, b in lad) or live_b not in (None, "exact")
        confirmed = live_loss is not None and live_loss >= BAD
        if any(s is None for s in seq) or live_loss is None: cls = "UNKNOWN"
        elif state_dep: cls = "UNSTABLE"
        elif all(s == "BAD" for s in seq): cls = "NOT REPAIRED"
        elif seq[0] == "BAD" and seq[-1] == "GOOD" and all(s == "GOOD" for s in seq[seq.index("GOOD"):]): cls = "REPAIRED BY DEPTH"
        else: cls = "UNSTABLE"
        plus1 = seq[1] if len(seq) > 1 else None
        rows.append(dict(id=r["id"], set=tag, cls=cls, confirmed=confirmed, live_loss_10M=live_loss, state_dependent=state_dep,
                         cold_timed=r["timed"], ladder=[dict(depth=d, move=m, loss_10M=l, bound=b, tag=t) for (d, m, l, b), t in zip(lad, seq)],
                         plus1_good=plus1 == "GOOD", inexact=inexact, rcj_values=r.get("rcj_values"),
                         sf_best_10M=v["best"]))
json.dump(rows, open(f"{A}/repair.json", "w", encoding="utf-8"), indent=1)
print(f"{'id':11s} {'set':13s} {'class':18s} conf live10M cold  ladder(depth:move:loss10M:tag)                     +1 RC-J own(played/ref)")
for x in rows:
    if "ladder" not in x: print(f"{x['id']:11s} {x['set']:13s} {x['cls']}"); continue
    lad = " ".join(f"{l['depth']}:{l['move']}:{l['loss_10M']}:{l['tag'][0]}" for l in x["ladder"])
    rv = x["rcj_values"] or {}
    print(f"{x['id']:11s} {x['set']:13s} {x['cls']:18s} {'Y' if x['confirmed'] else 'N':4s} {x['live_loss_10M']!s:6s} "
          f"{'live' if not x['state_dependent'] else 'DIFF':4s}  {lad:50s} {'Y' if x['plus1_good'] else 'N'}  {rv.get('played')}/{rv.get('reference')}")
from collections import Counter
for s in ("decisive", "supplementary"):
    c = Counter(x["cls"] for x in rows if x["set"] == s)
    print(f"{s}: {dict(c)}  confirmed {sum(1 for x in rows if x['set']==s and x.get('confirmed'))}  +1-ply GOOD {sum(1 for x in rows if x['set']==s and x.get('plus1_good'))}")
