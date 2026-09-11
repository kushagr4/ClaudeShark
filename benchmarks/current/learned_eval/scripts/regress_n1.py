"""Regression corpus (DESIGN_N1.md section 11): run only after static PASS, a magnitude-audit pass
and an NPS cost <= 20%.

    regress_n1.py prepare DATA_DIR RESULTS_N1_DIR N1_ENGINE   800 seeded labelled test positions; RC-J and N1
                                                              each in their own process (budget 1000 ms,
                                                              RC-J first; fixed depth 8, N1 first)
    sf_label.py DATA/test_sealed/regress/sf_tasks.jsonl DATA/test_sealed/regress/sf_labels.jsonl --nodes 1000000 ...
    regress_n1.py score DATA_DIR RESULTS_N1_DIR

Scoring: where the moves differ, both are scored by a root-restricted 1M-node search from the same
root. Improved if dE >= +0.05, worsened if dE <= -0.05; cp buckets on Stockfish's cp of N1's move
minus RC-J's (clipped +/-1500): >= 50, >= 100, >= 300. Pass (dE bucket and >= 100 cp bucket, and the
dE bucket on balanced roots): improved >= worsened and one-sided binomial p(worsened > improved)
>= 0.10. The >= 300 bucket is report-only when it has fewer than 10 items.
"""
import json
import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
N = 800
CAP = 1500


def binom_tail(k, n):
    """P(X >= k) for X ~ Binomial(n, 0.5)."""
    if n == 0:
        return 1.0
    return sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n


def preconditions(res):
    gates = json.load(open(os.path.join(res, "test_gates.json"), encoding="utf-8"))
    audit = json.load(open(os.path.join(res, "magnitude_audit.json"), encoding="utf-8"))
    speed = json.load(open(os.path.join(res, "speed_n1.json"), encoding="utf-8"))["summary"]
    ok = gates["static_pass"] and audit["passed"] and speed["nps_cost"] <= 0.20
    return ok, dict(static_pass=gates["static_pass"], audit=audit["passed"], nps_cost=speed["nps_cost"])


def prepare(data, res, n1_engine):
    ok, why = preconditions(res)
    assert ok, f"section 11 not permitted: {why}"
    d = os.path.join(data, "test_sealed", "regress")
    os.makedirs(d, exist_ok=True)
    labels = {json.loads(l)["pid"]: json.loads(l) for l in open(os.path.join(data, "test_sealed", "labels_test_1m.jsonl"), encoding="utf-8")}
    rows = [json.loads(l) for l in open(os.path.join(data, "pool.jsonl"), encoding="utf-8")]
    test = [r for r in rows if r["split"] == "test" and r["pid"] in labels and labels[r["pid"]]["E"] is not None]
    random.Random("N1-20260911|regress").shuffle(test)
    with open(os.path.join(d, "positions.jsonl"), "w", encoding="utf-8") as fh:
        for r in test[:N]:
            fh.write(json.dumps(dict(id=r["pid"], fen=r["fen"], group=r["group"], root_E=labels[r["pid"]]["E"], depth=8)) + "\n")
    for name, eng, extra in (("rcj_budget", ROOT, ["--budget-ms", "1000"]), ("n1_budget", n1_engine, ["--budget-ms", "1000"]),
                             ("n1_depth8", n1_engine, ["--depth-key", "depth"]), ("rcj_depth8", ROOT, ["--depth-key", "depth"])):
        subprocess.run([sys.executable, os.path.join(HERE, "search_probe.py"), eng, os.path.join(d, "positions.jsonl"),
                        os.path.join(d, f"moves_{name}.jsonl"), *extra], check=True)
    pos = {p["id"]: p for p in map(json.loads, open(os.path.join(d, "positions.jsonl"), encoding="utf-8"))}
    tasks = set()
    for mode in ("budget", "depth8"):
        a = {r["id"]: r for r in map(json.loads, open(os.path.join(d, f"moves_rcj_{mode}.jsonl"), encoding="utf-8"))}
        b = {r["id"]: r for r in map(json.loads, open(os.path.join(d, f"moves_n1_{mode}.jsonl"), encoding="utf-8"))}
        for pid in pos:
            if a[pid]["move"] != b[pid]["move"]:
                tasks.add((pid, a[pid]["move"]))
                tasks.add((pid, b[pid]["move"]))
    with open(os.path.join(d, "sf_tasks.jsonl"), "w", encoding="utf-8") as fh:
        for pid, mv in sorted(tasks):
            fh.write(json.dumps(dict(pid=f"{pid}:{mv}", fen=pos[pid]["fen"], searchmoves=[mv])) + "\n")
    print(json.dumps(dict(positions=len(pos), sf_tasks=len(tasks))))


def cp_of(lab):
    if lab["mate"] is not None:
        return CAP if lab["mate"] > 0 else -CAP
    return max(-CAP, min(CAP, lab["cp"]))


def cat(e):
    return 2 if e >= 0.75 else 0 if e <= 0.25 else 1


def tally(rows):
    b = {k: dict(improved=0, worsened=0) for k in ("dE", "cp>=50", "cp>=100", "cp>=300")}
    for r in rows:
        if r["dE"] >= 0.05:
            b["dE"]["improved"] += 1
        elif r["dE"] <= -0.05:
            b["dE"]["worsened"] += 1
        for t in (50, 100, 300):
            if r["dcp"] >= t:
                b[f"cp>={t}"]["improved"] += 1
            elif r["dcp"] <= -t:
                b[f"cp>={t}"]["worsened"] += 1
    for v in b.values():
        n = v["improved"] + v["worsened"]
        v["p_worse"] = binom_tail(v["worsened"], n)
        v["p_better"] = binom_tail(v["improved"], n)
        v["pass"] = v["improved"] >= v["worsened"] and v["p_worse"] >= 0.10
    return b


def score(data, res):
    d = os.path.join(data, "test_sealed", "regress")
    pos = {p["id"]: p for p in map(json.loads, open(os.path.join(d, "positions.jsonl"), encoding="utf-8"))}
    lab = {r["pid"]: r for r in map(json.loads, open(os.path.join(d, "sf_labels.jsonl"), encoding="utf-8"))}
    out = {}
    for mode in ("budget", "depth8"):
        a = {r["id"]: r for r in map(json.loads, open(os.path.join(d, f"moves_rcj_{mode}.jsonl"), encoding="utf-8"))}
        b = {r["id"]: r for r in map(json.loads, open(os.path.join(d, f"moves_n1_{mode}.jsonl"), encoding="utf-8"))}
        rows, flips = [], dict(repaired=0, introduced=0)
        for pid, p in pos.items():
            ma, mb = a[pid]["move"], b[pid]["move"]
            if ma == mb:
                continue
            la, lb = lab[f"{pid}:{ma}"], lab[f"{pid}:{mb}"]
            rows.append(dict(id=pid, rcj=ma, n1=mb, dE=lb["E"] - la["E"], dcp=cp_of(lb) - cp_of(la),
                             balanced=abs(p["root_E"] - 0.5) < 0.10))
            if cat(lb["E"]) > cat(la["E"]):
                flips["repaired"] += 1
            elif cat(lb["E"]) < cat(la["E"]):
                flips["introduced"] += 1
        allb, balb = tally(rows), tally([r for r in rows if r["balanced"]])
        passed = allb["dE"]["pass"] and allb["cp>=100"]["pass"] and balb["dE"]["pass"]
        out[mode] = dict(differing=len(rows), same=len(pos) - len(rows), buckets=allb, balanced_buckets=balb,
                         flips=flips, passed=passed,
                         depth=dict(rcj=sum(r["depth"] for r in a.values()) / len(a), n1=sum(r["depth"] for r in b.values()) / len(b)),
                         rows=rows)
    out["passed"] = out["budget"]["passed"]
    out["strong_evidence_10_15"] = out["budget"]["buckets"]["cp>=100"]["p_better"] < 0.10 and \
        out["budget"]["buckets"]["cp>=100"]["improved"] > out["budget"]["buckets"]["cp>=100"]["worsened"]
    with open(os.path.join(res, "regression_corpus.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({m: {k: v for k, v in out[m].items() if k != "rows"} for m in ("budget", "depth8")}, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        score(sys.argv[2], sys.argv[3])
