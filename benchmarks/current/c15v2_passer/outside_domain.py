"""Behavioural comparison of two builds over the competition-like corpus.

Root move, root score and node count at a fixed depth, so every difference is a
real change of search shape rather than timing noise. C15-v2 deliberately
changes the tree, so the question is not whether anything moves but whether
exactly the same positions move as under C15.

usage: outside_domain.py <baseline_dir> <candidate_dir> [depth] [out.json]
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LANE = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PY = r"C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"

BASE = sys.argv[1]
CAND = sys.argv[2]
DEPTH = int(sys.argv[3]) if len(sys.argv) > 3 else 8
OUT = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "outside_domain.json")

CODE = '''
import sys, json, chess
sys.path.insert(0, r"%s")
import cs_fast, cs_core
rows = [json.loads(l) for l in open(r"%s", encoding="utf-8")]
fens = [r["fen"] for r in rows if "fen" in r]
s = cs_fast.Searcher(); cs_fast.warm_up()
out = []
for fen in fens:
    b = chess.Board(fen)
    s.new_game()
    mv, i = s.search(b, 0, max_depth=%d)
    out.append([fen, mv.uci(), int(i.score), int(i.nodes)])
print("JSON" + json.dumps(out))
'''

CORPUS = os.path.join(LANE, "corpus", "competition_like_v1.jsonl")
res = {}
for name, path in (("base", BASE), ("cand", CAND)):
    r = subprocess.run([PY, "-c", CODE % (path, CORPUS, DEPTH)], capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith("JSON")]
    if not line:
        print(f"{name} FAILED:\n{r.stderr[-2000:]}")
        raise SystemExit(1)
    res[name] = json.loads(line[0][4:])

a, c = res["base"], res["cand"]
assert len(a) == len(c)
move_diff = [(x[0], x[1], y[1]) for x, y in zip(a, c) if x[1] != y[1]]
score_diff = [(x[0], x[2], y[2]) for x, y in zip(a, c) if x[2] != y[2]]
node_diff = [(x[0], x[3], y[3]) for x, y in zip(a, c) if x[3] != y[3]]

print(f"corpus positions      : {len(a)} (fixed depth {DEPTH})")
print(f"baseline              : {BASE}")
print(f"candidate             : {CAND}")
print(f"ROOT MOVE CHANGES     : {len(move_diff)} / {len(a)}")
print(f"ROOT SCORE CHANGES    : {len(score_diff)} / {len(a)}")
print(f"NODE COUNT DIFFERENCES: {len(node_diff)} / {len(a)}")
for d in move_diff:
    print("   MOVE ", d)
na, nc = sum(x[3] for x in a), sum(y[3] for y in c)
print(f"total nodes {na:,} vs {nc:,} ({100*(nc-na)/na:+.4f}%)")
json.dump(dict(base=BASE, cand=CAND, depth=DEPTH, rows_base=a, rows_cand=c,
               move_diff=move_diff, score_diff=score_diff), open(OUT, "w"))
print(f"wrote {OUT}")
