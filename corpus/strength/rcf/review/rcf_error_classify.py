"""Classify RC-F's >=100 cp errors from tools.strength.audit output.

Extra-depth repair is read from the fixed-depth ladder relative to the depth
the timed replay reached (D): repaired at D+k when the ladder move at depth
D+k loses under 100 cp by the oracle. Mechanism classes are heuristic and
stated in the report.
"""
import json, sys, collections
import chess

path = sys.argv[1]
rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
print(f"errors: {len(rows)}; result-flipping: {sum(1 for r in rows if r.get('result_flipping'))}; "
      f"reproduced at game budget: {sum(1 for r in rows if r.get('timed_reproduces'))}")

def ladder_loss(r, d):
    ll = r.get("ladder_loss") or {}
    v = ll.get(str(d), ll.get(d))
    return v

rep = {1: [0, 0], 2: [0, 0], 3: [0, 0]}
classes = collections.Counter()
flips = collections.Counter()
detail = []
for r in rows:
    D = (r.get("timed") or {}).get("depth") or 0
    pieces = len(chess.Board(r["fen"]).piece_map())
    repaired_at = None
    for k in (1, 2, 3):
        v = ladder_loss(r, D + k)
        if v is None:
            continue
        rep[k][1] += 1
        if v < 100:
            rep[k][0] += 1
            if repaired_at is None:
                repaired_at = k
    deep = r.get("deep_repairs")
    before = r.get("oracle_before") or 0
    spent = r.get("spent") or 0
    static = r.get("static"); qs = r.get("qsearch")
    if not r.get("timed_reproduces"):
        cls = "ROOT INSTABILITY / TIME NOISE"
    elif pieces <= 8 and repaired_at is None and not deep:
        cls = "ENDGAME (knowledge)"
    elif before >= 300 and (r.get("state_before") == "win"):
        cls = "CONVERSION" if repaired_at is None else "TACTICAL HORIZON (+%d)" % repaired_at
    elif repaired_at is not None:
        cls = "TACTICAL HORIZON (+%d)" % repaired_at
    elif deep:
        cls = "SEARCH SHAPE (LMR/ORDERING: deep 10 s repairs, +3 does not)"
    elif spent < 0.8 and (r.get("clock") or 0) > 20:
        cls = "TIME (moved fast)"
    elif static is not None and qs is not None and abs(qs - static) >= 150:
        cls = "QSEARCH / EVALUATION (static-qsearch gap)"
    else:
        cls = "EVALUATION (no depth repairs)"
    classes[cls] += 1
    if r.get("result_flipping"):
        flips[cls] += 1
    detail.append((r["game"][-4:], r["ply"], r["colour"], r["san"], r["oracle_move"], r["cp_loss"], D, repaired_at, deep, pieces, cls))

print("\nextra-depth repair rate (errors reproduced at the game budget, ladder available):")
for k in (1, 2, 3):
    n, m = rep[k]
    print(f"  +{k}: {n}/{m} = {100*n/m if m else 0:.0f}%")
print("\nmechanism classes (count, result flips):")
for cls, n in classes.most_common():
    print(f"  {n:3d}  flips {flips[cls]:3d}  {cls}")
print("\n| game | ply | col | played | oracle | loss | replay depth | repaired at +k | deep repairs | pieces | class |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for d in sorted(detail, key=lambda x: -x[5])[:40]:
    print("| " + " | ".join(str(x) for x in d) + " |")
