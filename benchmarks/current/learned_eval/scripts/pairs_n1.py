"""N1 move-ranking pairs (DESIGN_N1.md section 3): build roots for one split from its 1M-node
labels, and score pairs under a given evaluator mode.

    pairs_n1.py build DATA_DIR SPLIT LABELS_1M.jsonl N_ROOTS
    sf_label.py DATA_DIR/pairs/SPLIT_pair_tasks.jsonl DATA_DIR/pairs/SPLIT_pair_labels.jsonl --nodes 1000000 ...
"""
import json
import os
import random
import sys

import chess

MIN_DE = 0.05
MIN_DCP = 30
CAP = 1500


def cp_of(lab):
    if lab["mate"] is not None:
        return CAP if lab["mate"] > 0 else -CAP
    return max(-CAP, min(CAP, lab["cp"]))


def build(data, split, labels_path, n_roots, out_dir):
    d = out_dir
    os.makedirs(d, exist_ok=True)
    labels = {r["pid"]: r for r in map(json.loads, open(labels_path, encoding="utf-8"))}
    rows = [json.loads(l) for l in open(os.path.join(data, "pool.jsonl"), encoding="utf-8")]
    rows = [r for r in rows if r["split"] == split and r["pid"] in labels and labels[r["pid"]]["bestmove"]]
    random.Random(f"N1-20260911|pairs|{split}").shuffle(rows)
    roots = []
    for r in rows[:n_roots]:
        b = chess.Board(r["fen"])
        best = labels[r["pid"]]["bestmove"]
        cands = {"best": best}
        if r.get("next_move") and r["next_move"] != best:
            cands["game"] = r["next_move"]
        legal = sorted(m.uci() for m in b.legal_moves if m.uci() not in cands.values())
        if legal:
            cands["random"] = random.Random(f"N1-20260911|{r['pid']}").choice(legal)
        if len(cands) >= 2:
            roots.append(dict(pid=r["pid"], fen=r["fen"], group=r["group"], family=r["family"],
                              root_E=labels[r["pid"]]["E"], cands=cands))
    with open(os.path.join(d, f"{split}_roots.json"), "w", encoding="utf-8") as fh:
        json.dump(roots, fh)
    n = 0
    with open(os.path.join(d, f"{split}_pair_tasks.jsonl"), "w", encoding="utf-8") as fh:
        for r in roots:
            for u in sorted(set(r["cands"].values())):
                fh.write(json.dumps(dict(pid=f"{r['pid']}:{u}", fen=r["fen"], searchmoves=[u])) + "\n")
                n += 1
    print(json.dumps(dict(split=split, roots=len(roots), tasks=n)))


def load(pairs_dir, split):
    d = pairs_dir
    roots = json.load(open(os.path.join(d, f"{split}_roots.json"), encoding="utf-8"))
    plab = {r["pid"]: r for r in map(json.loads, open(os.path.join(d, f"{split}_pair_labels.jsonl"), encoding="utf-8"))}
    return roots, plab


def quiet_move(b, u):
    m = chess.Move.from_uci(u)
    return not b.is_capture(m) and m.promotion is None and not b.gives_check(m)


def correct(va, vb, ea, eb):
    """True when the evaluator orders the two moves as Stockfish does; a tie is an error."""
    if va == vb:
        return False
    return (va > vb) == (ea > eb)


def score(roots, plab, scorer, modes):
    """-> list of pair items with per-mode static/quiescence correctness."""
    items = []
    for r in roots:
        b = chess.Board(r["fen"])
        ucis = sorted(set(r["cands"].values()))
        E = {u: plab[f"{r['pid']}:{u}"]["E"] for u in ucis}
        if any(v is None for v in E.values()):
            continue
        CP = {u: cp_of(plab[f"{r['pid']}:{u}"]) for u in ucis}
        V = {m: scorer.moves(b, ucis, m) for m in modes}
        role = {u: k for k, u in r["cands"].items()}
        for i in range(len(ucis)):
            for j in range(i + 1, len(ucis)):
                u, v = ucis[i], ucis[j]
                de, dcp = E[u] - E[v], CP[u] - CP[v]
                if abs(de) < MIN_DE and abs(dcp) < MIN_DCP:
                    continue
                if de * dcp < 0 or (de == 0 and dcp == 0):
                    continue  # Stockfish's two scales disagree on the order: not a test item
                u_better = de > 0 or (de == 0 and dcp > 0)
                it = dict(root=r["pid"], group=r["group"], family=r["family"], root_E=r["root_E"],
                          dE=abs(de), dcp=abs(dcp), kind="-".join(sorted((role[u], role[v]))),
                          quiet=quiet_move(b, u) and quiet_move(b, v))
                for m in modes:
                    it[f"static{m}"] = V[m][u][0] != V[m][v][0] and (V[m][u][0] > V[m][v][0]) == u_better
                    it[f"qs{m}"] = V[m][u][1] != V[m][v][1] and (V[m][u][1] > V[m][v][1]) == u_better
                items.append(it)
    return items


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), sys.argv[6])
