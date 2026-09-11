"""Label-budget stability run and its frozen decision rule (DESIGN.md section 4).

  1. choose 300 pool positions with a seeded shuffle (all splits; this measures label quality,
     not model quality, so no model is ever selected on it);
  2. label them at 50k, 100k, 200k, 400k and 1M nodes and at a 4M-node reference, one labeller
     run at a time;
  3. relabel 30 of them at the chosen budget into a second file and require identical records;
  4. write budget.json with throughput per budget and the chosen budget.

    .venv/Scripts/python.exe benchmarks/current/learned_eval/scripts/budget_pilot.py DATA_DIR [--workers 10]
"""
import argparse
import json
import os
import random
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUDGETS = [50_000, 100_000, 200_000, 400_000, 1_000_000]
REFERENCE = 4_000_000
N = 300


def cat(e):
    return 2 if e >= 0.75 else 0 if e <= 0.25 else 1


def spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def label(tasks, out, nodes, workers):
    t0 = time.perf_counter()
    subprocess.run([sys.executable, os.path.join(HERE, "sf_label.py"), tasks, out, "--nodes", str(nodes),
                    "--workers", str(workers), "--hash", "32"], check=True)
    return time.perf_counter() - t0


def load(path):
    return {r["pid"]: r for r in map(json.loads, open(path, encoding="utf-8"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()
    d = os.path.join(a.data, "budget")
    os.makedirs(d, exist_ok=True)
    pool = [json.loads(l) for l in open(os.path.join(a.data, "pool.jsonl"), encoding="utf-8")]
    random.Random(20260911).shuffle(pool)
    chosen = pool[:N]
    tasks = os.path.join(d, "stability_tasks.jsonl")
    with open(tasks, "w", encoding="utf-8") as fh:
        for r in chosen:
            fh.write(json.dumps(dict(pid=r["pid"], fen=r["fen"])) + "\n")

    wall = {}
    for nodes in BUDGETS + [REFERENCE]:
        print(f"BUDGET {nodes} start {time.strftime('%H:%M:%S')}", flush=True)
        wall[nodes] = label(tasks, os.path.join(d, f"stab_{nodes}.jsonl"), nodes, a.workers)
        print(f"BUDGET {nodes} done in {wall[nodes]:.1f}s", flush=True)

    ref = load(os.path.join(d, f"stab_{REFERENCE}.jsonl"))
    pids = [r["pid"] for r in chosen]
    e_ref = np.array([ref[p]["E"] for p in pids])
    rows = {}
    chosen_budget = None
    for nodes in BUDGETS:
        lab = load(os.path.join(d, f"stab_{nodes}.jsonl"))
        e = np.array([lab[p]["E"] for p in pids])
        mae = float(np.abs(e - e_ref).mean())
        agree = float(np.mean([cat(x) == cat(y) for x, y in zip(e, e_ref)]))
        rho = spearman(e, e_ref)
        best_same = float(np.mean([lab[p]["bestmove"] == ref[p]["bestmove"] for p in pids]))
        ok = mae <= 0.04 and agree >= 0.90 and rho >= 0.95
        rows[nodes] = dict(mean_abs_dE=round(mae, 4), median_abs_dE=round(float(np.median(np.abs(e - e_ref))), 4),
                           category_agreement=round(agree, 4), spearman=round(rho, 4),
                           bestmove_agreement=round(best_same, 4), qualifies=ok,
                           seconds=round(wall[nodes], 1), positions_per_s=round(N / wall[nodes], 2))
        if ok and chosen_budget is None:
            chosen_budget = nodes
    rule_met = chosen_budget is not None
    chosen_budget = chosen_budget or 1_000_000

    det_tasks = os.path.join(d, "determinism_tasks.jsonl")
    with open(det_tasks, "w", encoding="utf-8") as fh:
        for r in chosen[:30]:
            fh.write(json.dumps(dict(pid=r["pid"], fen=r["fen"])) + "\n")
    label(det_tasks, os.path.join(d, f"determinism_{chosen_budget}.jsonl"), chosen_budget, a.workers)
    first = load(os.path.join(d, f"stab_{chosen_budget}.jsonl"))
    again = load(os.path.join(d, f"determinism_{chosen_budget}.jsonl"))
    keys = ("bestmove", "cp", "mate", "wdl", "E", "depth", "nodes", "pv")
    mismatches = [p for p in again if any(again[p][k] != first[p][k] for k in keys)]

    out = dict(n=N, reference_nodes=REFERENCE, reference_seconds=round(wall[REFERENCE], 1), workers=a.workers,
               budgets=rows, chosen_nodes=chosen_budget, rule_met=rule_met,
               determinism=dict(positions=len(again), mismatches=len(mismatches), ids=mismatches))
    with open(os.path.join(d, "budget.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1), flush=True)
    print("BUDGET PILOT DONE", flush=True)


if __name__ == "__main__":
    main()
