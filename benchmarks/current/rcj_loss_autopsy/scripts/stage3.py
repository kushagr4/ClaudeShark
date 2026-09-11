"""Supplementary depth test: >=100cp result-flip errors made while RC-J was not yet lost.
Same two steps as stage2 (RC-J cold ladder d..d+2 with own values, then Stockfish 10M
verification of played, best and every RC-J choice). One heavy step at a time."""
import json, os, subprocess, sys, time
A = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable
def step(n, args):
    print(f"STAGE {n} start {time.strftime('%H:%M:%S')}", flush=True)
    if subprocess.run([PY] + args, cwd=A).returncode != 0:
        print(f"PIPELINE FAILED at {n}", flush=True); sys.exit(1)
    print(f"STAGE {n} done {time.strftime('%H:%M:%S')}", flush=True)
step("sup-ladder", ["rcj_ladder.py", "--positions", "positions_sup100.json", "--extra", "2", "--max-seconds", "45", "--out", "ladder_sup.json"])
pos = json.load(open(os.path.join(A, "positions_sup100.json"), encoding="utf-8"))
lad = {r["id"]: r for r in json.load(open(os.path.join(A, "ladder_sup.json"), encoding="utf-8"))}
ver = [dict(id=p["id"], fen=p["fen"], played=p["played"], best=p["reference"],
            extra=sorted({lad[p["id"]]["timed"]["move"]} | {x["move"] for x in lad[p["id"]]["ladder"]})) for p in pos]
json.dump(ver, open(os.path.join(A, "verify_sup_positions.json"), "w", encoding="utf-8"), indent=1)
step("sup-verify", ["sf_verify.py", "--positions", "verify_sup_positions.json", "--nodes", "10000000", "--out", "verify_sup.json"])
print("PIPELINE DONE", flush=True)
