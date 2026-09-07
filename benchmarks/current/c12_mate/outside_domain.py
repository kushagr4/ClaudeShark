"""Outside-domain proof: the candidate must be behaviourally identical to RC-F
on every position of the competition-like corpus.

Compares root move, root score and node count at a fixed depth, so any
difference is a real behavioural change and not timing noise.
"""
import subprocess, os, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LANE = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PY = r"C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
DEPTH = int(sys.argv[1]) if len(sys.argv) > 1 else 8

CODE = '''
import sys, json, chess
sys.path.insert(0, r"%s")
import cs_fast, cs_core
rows = [json.loads(l) for l in open(r"%s", encoding="utf-8")]
fens = [r["fen"] for r in rows if "fen" in r]
s = cs_fast.Searcher(); cs_fast.warm_up()
out = []
nonzero = 0
B, O, M, S, U = cs_core.new_board_arrays()
for fen in fens:
    b = chess.Board(fen)
    cs_core.load_board(b, B, O, M, S)
    if hasattr(cs_core, "mop_up_bonus") and int(cs_core.mop_up_bonus(B)) != 0:
        nonzero += 1
    s.new_game()
    mv, i = s.search(b, 0, max_depth=%d)
    out.append([fen, mv.uci(), int(i.score), int(i.nodes)])
print("JSON" + json.dumps({"rows": out, "nonzero_bonus": nonzero}))
'''

CORPUS = os.path.join(LANE, "corpus", "competition_like_v1.jsonl")
res = {}
for name, path in (("RC-F", os.path.join(LANE, "champions", "rc_f")), ("C11", LANE)):
    r = subprocess.run([PY, "-c", CODE % (path, CORPUS, DEPTH)], capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith("JSON")]
    if not line:
        print(f"{name} FAILED:\n{r.stderr[-1500:]}")
        raise SystemExit(1)
    res[name] = json.loads(line[0][4:])

a, c = res["RC-F"]["rows"], res["C11"]["rows"]
assert len(a) == len(c)
move_diff = [(x[0], x[1], y[1]) for x, y in zip(a, c) if x[1] != y[1]]
score_diff = [(x[0], x[2], y[2]) for x, y in zip(a, c) if x[2] != y[2]]
node_diff = [(x[0], x[3], y[3]) for x, y in zip(a, c) if x[3] != y[3]]

print(f"corpus positions            : {len(a)} (fixed depth {DEPTH})")
print(f"positions where the gate fires (candidate): {res['C11']['nonzero_bonus']}")
print(f"positions where the gate fires (RC-F, no term): {res['RC-F']['nonzero_bonus']}")
print(f"ROOT MOVE CHANGES           : {len(move_diff)} / {len(a)}")
print(f"ROOT SCORE CHANGES          : {len(score_diff)} / {len(a)}")
print(f"NODE COUNT DIFFERENCES      : {len(node_diff)} / {len(a)}")
for d in move_diff[:10]:
    print("   MOVE ", d)
for d in score_diff[:10]:
    print("   SCORE", d)
for d in node_diff[:10]:
    print("   NODES", d)
na, nc = sum(x[3] for x in a), sum(y[3] for y in c)
print(f"total nodes RC-F {na:,} vs C11 {nc:,} ({100*(nc-na)/na:+.4f}%)")
print("VERDICT: " + ("PASS" if not move_diff and not score_diff else "FAIL"))
