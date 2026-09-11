"""N1 search-speed measurement (DESIGN_N1.md section 10). Idle machine only.

Blocks, each 5 ABBA rounds of separate processes on the 24 balanced openings:
  N  null control: RC-J against RC-J at 1,000 ms (median per-round ratio must be within +/-2%;
     otherwise the whole measurement is void and repeated once)
  S  shadow cost: RC-J against the shadow_cost N1 build at depth 10 (identical tree)
  R  real N1q: RC-J against the real N1 build at 1,000 ms per position
Per-round ratio = (B1 + B2) / (A1 + A2) of NPS in an A B B A round. NPS cost = 1 - the minimum
per-round ratio, the worse of S and R; medians are reported. Completed depth excludes partial
iterations (speed_probe.py).

    speed_n1.py SHADOW_ENGINE REAL_ENGINE OUT_JSON
"""
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ROUNDS = 5


def probe(eng, mode, arg):
    out = subprocess.run([sys.executable, os.path.join(HERE, "speed_probe.py"), eng, mode, str(arg)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def block(name, a, b, mode, arg, log):
    runs, ratios = [], []
    for rnd in range(ROUNDS):
        seq = [("A", a), ("B", b), ("B", b), ("A", a)]
        got = []
        for tag, eng in seq:
            r = probe(eng, mode, arg)
            r.update(block=name, round=rnd, side=tag)
            runs.append(r)
            got.append(r)
            log(json.dumps({k: r[k] for k in ("block", "round", "side", "mode", "nodes", "nps", "mean_depth",
                                               "partial_iterations", "compile_s")}))
        na = got[0]["nps"] + got[3]["nps"]
        nb = got[1]["nps"] + got[2]["nps"]
        ratios.append(nb / na)
    return runs, ratios


def band(cost):
    if cost > 0.30:
        return "automatic rejection (>30%)"
    if cost > 0.20:
        return "rejected in this stage (>20%)"
    if cost > 0.15:
        return "15-20%: needs exceptional evidence"
    if cost > 0.10:
        return "10-15%: needs strong evidence"
    return "<=10%: desirable"


def measure(shadow, real, log):
    res = {}
    for name, b, mode, arg in (("N", ROOT, "budget", 1000), ("S", shadow, "depth", 10), ("R", real, "budget", 1000)):
        runs, ratios = block(name, ROOT, b, mode, arg, log)
        a_runs = [r for r in runs if r["side"] == "A"]
        b_runs = [r for r in runs if r["side"] == "B"]
        res[name] = dict(ratios=ratios, median=float(np.median(ratios)), min=float(min(ratios)), max=float(max(ratios)),
                         A_mean_depth=float(np.mean([r["mean_depth"] for r in a_runs])),
                         B_mean_depth=float(np.mean([r["mean_depth"] for r in b_runs])),
                         A_partial=sum(r["partial_iterations"] for r in a_runs), B_partial=sum(r["partial_iterations"] for r in b_runs),
                         A_researches=sum(r["researches"] for r in a_runs), B_researches=sum(r["researches"] for r in b_runs),
                         A_unstable=sum(r["unstable_iterations"] for r in a_runs), B_unstable=sum(r["unstable_iterations"] for r in b_runs),
                         A_compile=[r["compile_s"] for r in a_runs], B_compile=[r["compile_s"] for r in b_runs],
                         B_counters=[r["n1_counters"] for r in b_runs], B_nodes=sorted({r["nodes"] for r in b_runs}),
                         A_nodes=sorted({r["nodes"] for r in a_runs}), runs=runs)
    res["null_ok"] = abs(res["N"]["median"] - 1) <= 0.02
    return res


def main():
    shadow, real, out = sys.argv[1], sys.argv[2], sys.argv[3]
    lines = []

    def log(s):
        print(s, flush=True)
        lines.append(s)

    impl = {n: hashlib.sha256(open(os.path.join(p, "cs_core.py"), "rb").read()).hexdigest() for n, p in
            (("shadow", shadow), ("real", real))}
    impl["engine_n1.py"] = hashlib.sha256(open(os.path.join(HERE, "engine_n1.py"), "rb").read()).hexdigest()
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    first = measure(shadow, real, log)
    attempts = [first]
    if not first["null_ok"]:
        log("null control outside +/-2%: measurement void, repeating once")
        attempts.append(measure(shadow, real, log))
    use = attempts[-1]
    cost_s = 1 - use["S"]["min"]
    cost_r = 1 - use["R"]["min"]
    cost = max(cost_s, cost_r)
    summ = dict(started=started, implementation_sha256=impl, attempts=len(attempts), null_ok=use["null_ok"],
                null_median=use["N"]["median"], shadow_cost_min_ratio=use["S"]["min"], shadow_cost_median=use["S"]["median"],
                real_min_ratio=use["R"]["min"], real_median=use["R"]["median"], nps_cost=cost,
                nps_cost_median_based=max(1 - use["S"]["median"], 1 - use["R"]["median"]), band=band(cost),
                depth_loss_1000ms=use["R"]["A_mean_depth"] - use["R"]["B_mean_depth"],
                shadow_nodes_identical=use["S"]["B_nodes"] == use["S"]["A_nodes"],
                real_researches=dict(rcj=use["R"]["A_researches"], n1=use["R"]["B_researches"]),
                real_unstable=dict(rcj=use["R"]["A_unstable"], n1=use["R"]["B_unstable"]),
                compile_s=dict(rcj=use["R"]["A_compile"], n1=use["R"]["B_compile"]))
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(dict(summary=summ, attempts=attempts), fh, indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
