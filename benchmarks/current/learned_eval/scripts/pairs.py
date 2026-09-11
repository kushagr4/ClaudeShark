"""Pairwise move-ranking test (DESIGN.md section 6.4) and the RC-J real-loss holdout.

  build : choose up to 800 test positions; candidates = Stockfish best, the game move, one seeded
          random legal move; write root-restricted (searchmoves) labelling tasks
  score : after sf_label.py has labelled those tasks, score every pair with |dE| >= 0.05 under
          E0 and E1 (static and quiescence-resolved), bootstrap by test group; then the holdout

    pairs.py build DATA_DIR LABELS.jsonl
    sf_label.py DATA_DIR/pairs/pair_tasks.jsonl DATA_DIR/pairs/pair_labels.jsonl --nodes N --workers 10
    pairs.py score DATA_DIR LABELS.jsonl WEIGHTS.json OUT_DIR
"""
import argparse
import collections
import json
import os
import random
import sys

import chess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
AUTOPSY = os.path.join(ROOT, "benchmarks/current/rcj_loss_autopsy/data")
N_ROOTS = 800
MIN_DE = 0.05


def build(a):
    d = os.path.join(a.data, "pairs")
    os.makedirs(d, exist_ok=True)
    pool = [json.loads(l) for l in open(os.path.join(a.data, "pool.jsonl"), encoding="utf-8")]
    labels = {r["pid"]: r for r in map(json.loads, open(a.labels, encoding="utf-8"))}
    test = [r for r in pool if r["split"] == "test" and r["pid"] in labels and labels[r["pid"]]["bestmove"]]
    random.Random(20260911).shuffle(test)
    roots = []
    for r in test[:N_ROOTS]:
        b = chess.Board(r["fen"])
        best = labels[r["pid"]]["bestmove"]
        cands = {"best": best}
        if r.get("next_move") and r["next_move"] != best:
            cands["game"] = r["next_move"]
        legal = sorted(m.uci() for m in b.legal_moves if m.uci() not in cands.values())
        if legal:
            cands["random"] = random.Random(f"20260911|{r['pid']}").choice(legal)
        if len(cands) >= 2:
            roots.append(dict(pid=r["pid"], fen=r["fen"], group=r["group"], family=r["family"], cands=cands))
    with open(os.path.join(d, "roots.json"), "w", encoding="utf-8") as fh:
        json.dump(roots, fh)
    n = 0
    with open(os.path.join(d, "pair_tasks.jsonl"), "w", encoding="utf-8") as fh:
        for r in roots:
            for u in sorted(set(r["cands"].values())):
                fh.write(json.dumps(dict(pid=f"{r['pid']}:{u}", fen=r["fen"], searchmoves=[u])) + "\n")
                n += 1
    print(json.dumps(dict(roots=len(roots), tasks=n)))


def quiet_move(b, u):
    m = chess.Move.from_uci(u)
    return not b.is_capture(m) and m.promotion is None and not b.gives_check(m)


def acc(items, key):
    return float(np.mean([it[key] for it in items])) if items else None


def boot(items, groups_of, rng, key_a, key_b, n=1000):
    by = collections.defaultdict(list)
    for it in items:
        by[groups_of(it)].append(it)
    keys = sorted(by)
    diffs = []
    for _ in range(n):
        pick = rng.integers(0, len(keys), len(keys))
        sel = [it for k in pick for it in by[keys[k]]]
        diffs.append(np.mean([it[key_a] for it in sel]) - np.mean([it[key_b] for it in sel]))
    return dict(point=acc(items, key_a) - acc(items, key_b), lo=float(np.percentile(diffs, 2.5)),
                hi=float(np.percentile(diffs, 97.5)), groups=len(keys))


def correct(va, vb, ea, eb):
    """True when the evaluator orders the moves as Stockfish does; a tie is an error."""
    if va == vb:
        return False
    return (va > vb) == (ea > eb)


def score(a):
    import evalkit
    d = os.path.join(a.data, "pairs")
    W = np.array(json.load(open(a.weights, encoding="utf-8"))["W"], dtype=np.float64)
    sc = evalkit.Scorer(W)
    roots = json.load(open(os.path.join(d, "roots.json"), encoding="utf-8"))
    plab = {r["pid"]: r for r in map(json.loads, open(os.path.join(d, "pair_labels.jsonl"), encoding="utf-8"))}
    items = []
    for r in roots:
        b = chess.Board(r["fen"])
        ucis = sorted(set(r["cands"].values()))
        E = {u: plab[f"{r['pid']}:{u}"]["E"] for u in ucis}
        if any(v is None for v in E.values()):
            continue
        V = sc.values(b, ucis)
        role = {u: k for k, u in r["cands"].items()}
        for i in range(len(ucis)):
            for j in range(i + 1, len(ucis)):
                u, v = ucis[i], ucis[j]
                if abs(E[u] - E[v]) < MIN_DE:
                    continue
                it = dict(root=r["pid"], group=r["group"], family=r["family"], dE=abs(E[u] - E[v]),
                          kind="-".join(sorted((role[u], role[v]))),
                          quiet=quiet_move(b, u) and quiet_move(b, v))
                for k in ("static0", "static1", "qs0", "qs1"):
                    it[k] = correct(V[u][k], V[v][k], E[u], E[v])
                items.append(it)
    rng = np.random.default_rng(20260911)
    res = dict(pairs=len(items), roots=len({it["root"] for it in items}), min_dE=MIN_DE, subsets={})
    subsets = {"all": items, "quiet_pairs": [it for it in items if it["quiet"]],
               "dE>=0.15": [it for it in items if it["dE"] >= 0.15]}
    for kind in sorted({it["kind"] for it in items}):
        subsets["kind_" + kind] = [it for it in items if it["kind"] == kind]
    for fam in ("TWIC", "PUBLIC", "VS_SF", "SELFPLAY"):
        subsets["family_" + fam] = [it for it in items if it["family"] == fam]
    for name, its in subsets.items():
        if not its:
            continue
        res["subsets"][name] = dict(
            n=len(its), static_E0=acc(its, "static0"), static_E1=acc(its, "static1"),
            qs_E0=acc(its, "qs0"), qs_E1=acc(its, "qs1"),
            qs_diff=boot(its, lambda it: it["group"], rng, "qs1", "qs0"),
            static_diff=boot(its, lambda it: it["group"], rng, "static1", "static0"))

    # RC-J real-loss holdout: Stockfish 10M best vs RC-J's played move, E from verify*.json.
    ver = {v["id"]: v for f in ("verify.json", "verify_sup.json") for v in json.load(open(os.path.join(AUTOPSY, f)))}
    pos = {p["id"]: p for f in ("positions.json", "positions_sup100.json") for p in json.load(open(os.path.join(AUTOPSY, f)))}
    rep = {r["id"]: r for r in json.load(open(os.path.join(AUTOPSY, "repair.json")))}
    hold = []
    for hid, v in ver.items():
        if not rep.get(hid, {}).get("confirmed"):
            continue
        b = chess.Board(v["fen"])
        played, bestm = pos[hid]["played"], v["best"]["move"]
        e_best, e_played = v["best"]["E"], v["moves"][played]["E"]
        V = sc.values(b, [bestm, played])
        row = dict(id=hid, set=rep[hid]["set"], cls=rep[hid]["cls"], state_dependent=rep[hid]["state_dependent"],
                   fen=v["fen"], best=bestm, played=played, E_best=e_best, E_played=e_played,
                   loss_cp=v["moves"][played]["loss_cp"], quiet=quiet_move(b, bestm) and quiet_move(b, played))
        for k in ("static0", "static1", "qs0", "qs1"):
            row[k] = correct(V[bestm][k], V[played][k], e_best, e_played)
            row[k + "_margin"] = V[bestm][k] - V[played][k]
        hold.append(row)
    hold.sort(key=lambda r: (r["set"] != "decisive", r["id"]))
    for name, sel in (("decisive14", [h for h in hold if h["set"] == "decisive"]), ("serious19", hold)):
        res[name] = dict(n=len(sel), **{k: int(sum(h[k] for h in sel)) for k in ("static0", "static1", "qs0", "qs1")})
    res["holdout_rows"] = hold
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "pairwise_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "holdout_rows"}, indent=1))
    for h in hold:
        print(f"{h['id']:10s} {h['set']:13s} {h['cls']:18s} best {h['best']} played {h['played']} "
              f"static E0 {h['static0']!s:5} E1 {h['static1']!s:5} | qs E0 {h['qs0']!s:5} E1 {h['qs1']!s:5} "
              f"| qs margin E0 {h['qs0_margin']:+5d} E1 {h['qs1_margin']:+5d}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("build", "score"))
    ap.add_argument("data")
    ap.add_argument("labels")
    ap.add_argument("weights", nargs="?")
    ap.add_argument("out", nargs="?")
    a = ap.parse_args()
    build(a) if a.mode == "build" else score(a)


if __name__ == "__main__":
    main()
