"""Speed of E1 against RC-J's evaluator (DESIGN.md section 7). Run on an otherwise idle machine.

  1. static-evaluation throughput in a compiled loop over test positions: E0 alone, E0 + E1;
  2. scratch copies of RC-J whose cs_core.evaluate adds the E1 correction (weights compiled in as
     constants): a zero-weight copy must reproduce RC-J's fixed-depth node count exactly (plumbing
     control); the real-weight copy gives the search nodes-per-second ratio;
  3. each engine in its own process, alternated, fixed depth 10 and a 1,000 ms budget per position.

Nothing here touches the repository's runtime files; the scratch engines live under OUT_DIR.

    speed.py DATA_DIR WEIGHTS.json OUT_DIR [--rounds 2]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

import chess
import numpy as np
from numba import njit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import features as F  # noqa: E402

C = F.C
ROOT = F.ROOT
RUNTIME = ["agent.py"] + sorted(f for f in os.listdir(ROOT) if f.startswith("cs_") and f.endswith(".py"))
OLD_TAIL = "    if S[0] == 0:\n        return score + TEMPO\n    return -score + TEMPO\n"
NEW_TAIL = ("    c = np.int64(np.rint(e1_correction(B, S[0], E1_W)))\n"
            "    if S[0] == 0:\n        return score + TEMPO + c\n    return -score + TEMPO + c\n")


@njit(cache=False)
def loop_e0(BB, SS, reps):
    s = 0
    for _ in range(reps):
        for n in range(BB.shape[0]):
            s += C.evaluate(BB[n], SS[n])
    return s


@njit(cache=False)
def loop_e1(BB, SS, W, reps):
    s = 0
    for _ in range(reps):
        for n in range(BB.shape[0]):
            s += C.evaluate(BB[n], SS[n]) + np.int64(np.rint(F.e1_correction(BB[n], SS[n, 0], W)))
    return s


def make_engine(dst, W):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in RUNTIME:
        shutil.copy2(os.path.join(ROOT, f), os.path.join(dst, f))
    path = os.path.join(dst, "cs_core.py")
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    assert text.count(OLD_TAIL) == 1
    text = text.replace(OLD_TAIL, NEW_TAIL)
    text += "\n\n# ---- E1 learned correction (scratch speed build) ----\n" + F.runtime_source()
    text += "\nE1_W = np.array(" + repr([float(v) for v in W]) + ", dtype=np.float64)\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def probe(eng, mode, arg):
    out = subprocess.run([sys.executable, os.path.join(HERE, "speed_probe.py"), eng, mode, str(arg)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("weights")
    ap.add_argument("out")
    ap.add_argument("--rounds", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    W = np.array(json.load(open(a.weights, encoding="utf-8"))["W"], dtype=np.float64)
    res = dict(weights=a.weights)

    pool = [json.loads(l) for l in open(os.path.join(a.data, "pool.jsonl"), encoding="utf-8")]
    test = [chess.Board(r["fen"]) for r in pool if r["split"] == "test"]
    BB, SS, _ = F.arrays_from_boards(test)
    loop_e0(BB, SS, 1)
    loop_e1(BB, SS, W, 1)
    reps = 200
    best0 = best1 = 1e9
    for _ in range(5):
        t = time.perf_counter()
        loop_e0(BB, SS, reps)
        best0 = min(best0, time.perf_counter() - t)
        t = time.perf_counter()
        loop_e1(BB, SS, W, reps)
        best1 = min(best1, time.perf_counter() - t)
    n = reps * len(test)
    res["static"] = dict(positions=len(test), evals=n, e0_ns=round(best0 / n * 1e9, 1),
                         e1_ns=round(best1 / n * 1e9, 1), e1_over_e0=round(best1 / best0, 2),
                         e0_evals_per_s=round(n / best0), e1_evals_per_s=round(n / best1))
    print(json.dumps(res["static"]), flush=True)

    engines = {"rcj": ROOT, "e1": os.path.join(a.out, "engine_e1"), "e1_zero": os.path.join(a.out, "engine_e1_zero")}
    make_engine(engines["e1"], W)
    make_engine(engines["e1_zero"], np.zeros_like(W))
    runs = []
    for rnd in range(a.rounds):
        for name in ("rcj", "e1", "e1_zero"):
            for mode, arg in (("depth", 10), ("budget", 1000)):
                r = probe(engines[name], mode, arg)
                r.update(name=name, round=rnd)
                runs.append(r)
                print(json.dumps({k: r[k] for k in ("name", "round", "mode", "nodes", "nps", "mean_depth",
                                                    "compile_s")}), flush=True)
    res["runs"] = runs
    summ = {}
    for name in engines:
        for mode in ("depth", "budget"):
            rs = [r for r in runs if r["name"] == name and r["mode"] == mode]
            summ[f"{name}_{mode}"] = dict(nodes=[r["nodes"] for r in rs], nps_mean=round(np.mean([r["nps"] for r in rs])),
                                          mean_depth=round(float(np.mean([r["mean_depth"] for r in rs])), 3),
                                          compile_s=[r["compile_s"] for r in rs])
    base_nps = summ["rcj_depth"]["nps_mean"]
    summ["e1_nps_ratio_depth"] = round(summ["e1_depth"]["nps_mean"] / base_nps, 3)
    summ["e1_zero_nps_ratio_depth"] = round(summ["e1_zero_depth"]["nps_mean"] / base_nps, 3)
    summ["e1_nps_ratio_budget"] = round(summ["e1_budget"]["nps_mean"] / summ["rcj_budget"]["nps_mean"], 3)
    summ["zero_weight_nodes_identical"] = summ["e1_zero_depth"]["nodes"] == summ["rcj_depth"]["nodes"]
    summ["zero_weight_moves_identical"] = all(
        r0["moves"] == r1["moves"] for r0 in runs if r0["name"] == "rcj" and r0["mode"] == "depth"
        for r1 in runs if r1["name"] == "e1_zero" and r1["mode"] == "depth")
    res["summary"] = summ
    with open(os.path.join(a.out, "speed.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
