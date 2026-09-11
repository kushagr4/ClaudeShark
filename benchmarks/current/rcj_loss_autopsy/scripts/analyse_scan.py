"""Locate the FIRST decisive RC-J error in each loss from the isolated Stockfish scan.

Frozen before reading the table (the gradual rule was added after R79 showed that a
decline can cross a category boundary between moves rather than within one):
  * category from Stockfish's WDL expectation E, RC-J's view: win E>=0.75,
    loss E<=0.25, otherwise draw.
  * RESULT FLIP: an RC-J move whose played-move category is below the best-move
    category from the same root.
  * FIRST DECISIVE (kind FLIP): the earliest flip after which RC-J's best-play
    category at every later RC-J turn stays below the pre-flip category.
  * GRADUAL: no flip qualifies. The decisive move is the RC-J move with the largest
    expected-score drop dE among turns where RC-J was not yet lost; lower confidence.
  * every >=100 cp error made while RC-J was not yet lost is listed in order.
Severity: loss_cp = best_cp - played_cp from one root (0 if the played move is the
engine's own choice).
"""
import collections, json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
out_path = sys.argv[2] if len(sys.argv) > 2 else None
rank = {"loss": 0, "draw": 1, "win": 2}
G = collections.defaultdict(list)
for r in rows: G[r["round"]].append(r)
res = []
for rnd, rs in sorted(G.items()):
    rs.sort(key=lambda r: r["move_number"])
    first, kind = None, "FLIP"
    for i, r in enumerate(rs):
        if r["flip"] and all(rank[x["cat_best"]] < rank[r["cat_best"]] for x in rs[i + 1:] if x["cat_best"]):
            first = r; break
    if first is None:
        kind = "GRADUAL"
        live = [r for r in rs if r["cat_best"] != "loss" and r["dE"] is not None]
        first = max(live, key=lambda r: r["dE"]) if live else max(rs, key=lambda r: r["loss_cp"])
    traj = "".join({"win": "W", "draw": "=", "loss": "L", None: "?"}[r["cat_best"]] for r in rs)
    bands = dict(ge50=sum(r["loss_cp"] >= 50 for r in rs), ge100=sum(r["loss_cp"] >= 100 for r in rs),
                 ge300=sum(r["loss_cp"] >= 300 for r in rs), flips=sum(r["flip"] for r in rs))
    prelost = [r for r in rs if r["cat_best"] != "loss" and r["loss_cp"] >= 100]
    worst = max(rs, key=lambda r: r["loss_cp"])
    inexact = sum(r["best_bound"] != "exact" or r["played_bound"] != "exact" for r in rs)
    res.append(dict(round=rnd, game=rs[0]["game"], side=rs[0]["side"], moves=len(rs), kind=kind, decisive=first,
                    worst=worst, prelost_ge100=prelost, bands=bands, trajectory=traj, inexact_rows=inexact))
    d = first
    print(f"R{rnd} {rs[0]['side']:5s} {len(rs):3d} moves  >=50:{bands['ge50']:2d} >=100:{bands['ge100']:2d} "
          f">=300:{bands['ge300']:2d} flips:{bands['flips']:2d} inexact:{inexact}  traj {traj[:60]}")
    print(f"     {kind:8s} m{d['move_number']:>3} {d['san']:7s} {d['played']}  best {d['best']}  loss {d['loss_cp']:4d}cp  "
          f"dE {d['dE']:.2f}  E {d['best_E']:.2f}->{d['played_E']:.2f}  cp {d['best_cp']:+d}/{d['played_cp']:+d}  clk {d['clock_in_s']}")
    for r in prelost:
        print(f"       >=100cp while not lost: m{r['move_number']:>3} {r['san']:7s} loss {r['loss_cp']:4d} dE {r['dE']:.2f} {r['cat_best']}->{r['cat_played']}")
    print(f"       worst overall: m{worst['move_number']} {worst['san']} {worst['loss_cp']}cp ({worst['cat_best']}->{worst['cat_played']})")
if out_path:
    json.dump(res, open(out_path, "w", encoding="utf-8"), indent=1)
