"""RC-J real-loss holdout for N1 (DESIGN_N1.md section 12). Run LAST, after every other result is on
file; nothing is retrained or re-selected afterwards.

    holdout_n1.py prepare DATA_DIR RESULTS_N1_DIR N1_ENGINE   static + quiescence pairwise; cold replays
    sf_label.py DATA_DIR/holdout/sf_tasks.jsonl DATA_DIR/holdout/sf_labels.jsonl --nodes 10000000 --hash 256 ...
    holdout_n1.py score DATA_DIR RESULTS_N1_DIR

Ground truth as in the autopsy: Stockfish's 10M-node values in rcj_loss_autopsy/data/verify*.json;
a move is GOOD at <= 30 cp loss and BAD at >= 40 cp; WDL categories win >= 0.75, loss <= 0.25.
Replays: RC-J and N1 cold (fresh table) at the recorded clock (production timing path, not
deterministic) and at the autopsy's timed depth (deterministic).
"""
import json
import os
import subprocess
import sys

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
AUT = os.path.join(ROOT, "benchmarks/current/rcj_loss_autopsy/data")
MATE_CP = 100000
CAP = 1500


def load_holdout():
    ver = {v["id"]: v for f in ("verify.json", "verify_sup.json") for v in json.load(open(os.path.join(AUT, f)))}
    pos = {p["id"]: p for f in ("positions.json", "positions_sup100.json") for p in json.load(open(os.path.join(AUT, f)))}
    rep = {r["id"]: r for r in json.load(open(os.path.join(AUT, "repair.json")))}
    rows = []
    for hid, v in ver.items():
        r = rep.get(hid)
        if not r or not r.get("confirmed"):
            continue
        rows.append(dict(id=hid, set=r["set"], cls=r["cls"], state_dependent=r["state_dependent"], fen=v["fen"],
                         played=pos[hid]["played"], best=v["best"]["move"], best_cp=v["best"]["cp"],
                         best_mate=v["best"]["mate"], best_E=v["best"]["E"], known=v["moves"],
                         clock_ms=int(pos[hid].get("clock_in_ms") or 120000), depth=int(r["cold_timed"]["depth"])))
    rows.sort(key=lambda h: (h["set"] != "decisive", h["id"]))
    return rows


def cpv(cp, mate):
    v = MATE_CP * (1 if mate > 0 else -1) if mate is not None else cp
    return max(-CAP, min(CAP, v))


def preconditions(res_dir):
    """The holdout is last: every other result must already be on file; their hashes are recorded."""
    import hashlib
    need = ["freeze.json", "test_gates.json", "magnitude_audit.json", "speed_n1.json"]
    gates = json.load(open(os.path.join(res_dir, "test_gates.json"), encoding="utf-8"))
    audit = json.load(open(os.path.join(res_dir, "magnitude_audit.json"), encoding="utf-8"))
    speed = json.load(open(os.path.join(res_dir, "speed_n1.json"), encoding="utf-8"))["summary"]
    if gates["static_pass"] and audit["passed"] and speed["nps_cost"] <= 0.20:
        need.append("regression_corpus.json")
    missing = [n for n in need if not os.path.exists(os.path.join(res_dir, n))]
    assert not missing, f"holdout refused: missing {missing}"
    return {n: hashlib.sha256(open(os.path.join(res_dir, n), "rb").read()).hexdigest() for n in need}


def prepare(data, res_dir, n1_engine):
    import nn1
    import nn1kit
    hashes = preconditions(res_dir)
    d = os.path.join(data, "holdout")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "preconditions.json"), "w", encoding="utf-8") as fh:
        json.dump(hashes, fh, indent=1)
    fl, Q = nn1.load(os.path.join(res_dir, "n1_weights.npz"))
    sc = nn1kit.NNScorer(fl=fl, Q=Q)
    rows = load_holdout()
    for h in rows:
        b = chess.Board(h["fen"])
        for mode, tag in ((0, "E0"), (2, "N1q")):
            V = sc.moves(b, [h["best"], h["played"]], mode)
            for k, name in ((0, "static"), (1, "qs")):
                va, vb = V[h["best"]][k], V[h["played"]][k]
                h[f"{name}_{tag}"] = va > vb
                h[f"{name}_{tag}_margin"] = va - vb
    with open(os.path.join(d, "positions.jsonl"), "w", encoding="utf-8") as fh:
        for h in rows:
            fh.write(json.dumps(dict(id=h["id"], fen=h["fen"], clock_ms=h["clock_ms"], depth=h["depth"])) + "\n")
    for name, eng in (("rcj", ROOT), ("n1", n1_engine)):
        for mode, extra in (("clock", ["--clock"]), ("depth", ["--depth-key", "depth"])):
            subprocess.run([sys.executable, os.path.join(HERE, "search_probe.py"), eng, os.path.join(d, "positions.jsonl"),
                            os.path.join(d, f"replay_{name}_{mode}.jsonl"), *extra], check=True)
    tasks = set()
    for name in ("rcj", "n1"):
        for mode in ("clock", "depth"):
            for r in map(json.loads, open(os.path.join(d, f"replay_{name}_{mode}.jsonl"), encoding="utf-8")):
                h = next(x for x in rows if x["id"] == r["id"])
                if r["move"] and r["move"] not in h["known"]:
                    tasks.add((h["id"], h["fen"], r["move"]))
    with open(os.path.join(d, "sf_tasks.jsonl"), "w", encoding="utf-8") as fh:
        for hid, fen, mv in sorted(tasks):
            fh.write(json.dumps(dict(pid=f"{hid}:{mv}", fen=fen, searchmoves=[mv])) + "\n")
    with open(os.path.join(d, "static.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
    print(json.dumps(dict(positions=len(rows), new_moves_to_label=len(tasks))))


def score(data, res_dir):
    d = os.path.join(data, "holdout")
    rows = json.load(open(os.path.join(d, "static.json"), encoding="utf-8"))
    lab = {}
    if os.path.exists(os.path.join(d, "sf_labels.jsonl")):
        lab = {r["pid"]: r for r in map(json.loads, open(os.path.join(d, "sf_labels.jsonl"), encoding="utf-8"))}
    cat = lambda e: 2 if e >= 0.75 else 0 if e <= 0.25 else 1  # noqa: E731
    out = dict(sets={}, rows=[])
    for h in rows:
        best = cpv(h["best_cp"], h["best_mate"])

        def value(mv):
            if mv in h["known"]:
                k = h["known"][mv]
                return cpv(k["cp"], k["mate"]), k["E"]
            k = lab[f"{h['id']}:{mv}"]
            return cpv(k["cp"], k["mate"]), k["E"]

        row = {k: h[k] for k in ("id", "set", "cls", "state_dependent", "played", "best", "static_E0", "static_N1q",
                                 "qs_E0", "qs_N1q", "qs_E0_margin", "qs_N1q_margin")}
        pcp, pE = value(h["played"])
        row["live_loss_cp"] = best - pcp
        for name in ("rcj", "n1"):
            for mode in ("clock", "depth"):
                r = next(x for x in map(json.loads, open(os.path.join(d, f"replay_{name}_{mode}.jsonl"), encoding="utf-8"))
                         if x["id"] == h["id"])
                c, e = value(r["move"])
                loss = best - c
                row[f"{name}_{mode}"] = dict(move=r["move"], depth=r["depth"], loss_cp=loss,
                                             tag="GOOD" if loss <= 30 else "BAD" if loss >= 40 else "GREY",
                                             E=e, flip=cat(e) < cat(h["best_E"]))
        out["rows"].append(row)
    for name, sel in (("decisive14", [r for r in out["rows"] if r["set"] == "decisive"]), ("serious19", out["rows"])):
        s = dict(n=len(sel))
        for k in ("static_E0", "static_N1q", "qs_E0", "qs_N1q"):
            s[k] = sum(1 for r in sel if r[k])
        for mode in ("clock", "depth"):
            rc = [r[f"rcj_{mode}"] for r in sel]
            n1 = [r[f"n1_{mode}"] for r in sel]
            s[mode] = dict(
                rcj_good=sum(x["tag"] == "GOOD" for x in rc), n1_good=sum(x["tag"] == "GOOD" for x in n1),
                repaired=sum(a["tag"] != "GOOD" and b["tag"] == "GOOD" for a, b in zip(rc, n1)),
                worsened=sum(a["tag"] == "GOOD" and b["tag"] != "GOOD" for a, b in zip(rc, n1)),
                flips_repaired=sum(a["flip"] and not b["flip"] for a, b in zip(rc, n1)),
                flips_introduced=sum(not a["flip"] and b["flip"] for a, b in zip(rc, n1)),
                ge100_repaired=sum(a["loss_cp"] >= 100 and b["loss_cp"] < 100 for a, b in zip(rc, n1)),
                ge100_introduced=sum(a["loss_cp"] < 100 and b["loss_cp"] >= 100 for a, b in zip(rc, n1)),
                ge300_repaired=sum(a["loss_cp"] >= 300 and b["loss_cp"] < 300 for a, b in zip(rc, n1)),
                ge300_introduced=sum(a["loss_cp"] < 300 and b["loss_cp"] >= 300 for a, b in zip(rc, n1)),
                state_dependent_rows=[r["id"] for r in sel if r["state_dependent"]])
        out["sets"][name] = s
    with open(os.path.join(res_dir, "holdout.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out["sets"], indent=1))
    for r in out["rows"]:
        print(f"{r['id']:10s} {r['set']:13s} qs E0 {r['qs_E0']!s:5} N1q {r['qs_N1q']!s:5} | clock rcj "
              f"{r['rcj_clock']['move']} {r['rcj_clock']['tag']:4s} n1 {r['n1_clock']['move']} {r['n1_clock']['tag']:4s} "
              f"| depth rcj {r['rcj_depth']['move']} {r['rcj_depth']['tag']:4s} n1 {r['n1_depth']['move']} "
              f"{r['n1_depth']['tag']}")


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        score(sys.argv[2], sys.argv[3])
