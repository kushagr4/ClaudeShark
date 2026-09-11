"""Sequential autopsy pipeline: exactly one CPU-heavy step at a time.

  1. Stockfish scan of the R94+ losses (1M nodes; decisive positions are re-verified in step 5)
  2. decisive-error selection over all 14 losses (frozen rule in analyse_scan.py)
  3. RC-J cold depth ladder d..d+2 plus RC-J's own value of played vs reference
  4. (build) Stockfish verification set = played, best, and every move RC-J chose in step 3
  5. Stockfish re-verification at 10M nodes
  6. evidence dossier (no search)
Markers in stage2.log: 'STAGE <n> start', 'STAGE <n> done', 'PIPELINE DONE', 'PIPELINE FAILED'.
"""
import json, os, subprocess, sys, time
A = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
def step(n, args):
    print(f"STAGE {n} start {time.strftime('%H:%M:%S')}", flush=True)
    r = subprocess.run([PY] + args, cwd=A)
    if r.returncode != 0:
        print(f"PIPELINE FAILED at stage {n} (exit {r.returncode})", flush=True); sys.exit(1)
    print(f"STAGE {n} done {time.strftime('%H:%M:%S')}", flush=True)
try:
    if not os.path.exists(os.path.join(A, "scan_losses_new.jsonl")) or "--rescan" in sys.argv:
        step(1, ["sf_scan.py", "--public", os.path.join(A, "public_new"), "--min-round", "94", "--results", "L",
                 "--nodes", "1000000", "--out", "scan_losses_new.jsonl"])
    with open(os.path.join(A, "scan_all.jsonl"), "w", encoding="utf-8") as fh:
        for f in ("scan_losses.jsonl", "scan_losses_new.jsonl"):
            fh.write(open(os.path.join(A, f), encoding="utf-8").read())
    step(2, ["analyse_scan.py", "scan_all.jsonl", "decisive.json"])
    dec = json.load(open(os.path.join(A, "decisive.json"), encoding="utf-8"))
    pos = [dict(id=f"R{g['round']}-{g['decisive']['move_number']}{g['side'][0]}", fen=g["decisive"]["fen"],
                played=g["decisive"]["played"], reference=g["decisive"]["best"],
                clock_in_ms=int(g["decisive"]["clock_in_s"] * 1000) if g["decisive"]["clock_in_s"] else None) for g in dec]
    json.dump(pos, open(os.path.join(A, "positions.json"), "w", encoding="utf-8"), indent=1)
    step(3, ["rcj_ladder.py", "--positions", "positions.json", "--extra", "2", "--max-seconds", "45", "--out", "ladder.json"])
    lad = {r["id"]: r for r in json.load(open(os.path.join(A, "ladder.json"), encoding="utf-8"))}
    ver = [dict(id=p["id"], fen=p["fen"], played=p["played"], best=p["reference"],
                extra=sorted({lad[p["id"]]["timed"]["move"]} | {x["move"] for x in lad[p["id"]]["ladder"]})) for p in pos]
    json.dump(ver, open(os.path.join(A, "verify_positions.json"), "w", encoding="utf-8"), indent=1)
    step(5, ["sf_verify.py", "--positions", "verify_positions.json", "--nodes", "10000000", "--out", "verify.json"])
    step(6, ["dossier.py", "decisive.json", "dossier.json"])
    print("PIPELINE DONE", flush=True)
except SystemExit:
    raise
except Exception as e:
    print(f"PIPELINE FAILED: {e!r}", flush=True); sys.exit(1)
