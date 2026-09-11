"""Sample evaluate call sites from an `audit` N1 build (DESIGN_N1.md section 10 magnitude audit).

Searches the 24 balanced openings to depth 10 and the given validation roots to depth 8, each from
a fresh table, then dumps the sampled rows (every 64th evaluate call) with phase, side to move,
the N1q correction f and E0's white-view score.

    python audit_probe.py AUDIT_ENGINE_DIR ROOTS.json OUT.json
"""
import json
import os
import sys

eng, roots_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.abspath(eng))

import chess  # noqa: E402
import cs_core as C  # noqa: E402
import cs_fast  # noqa: E402
from tools.positions import BALANCED_OPENINGS  # noqa: E402

assert os.path.dirname(os.path.abspath(C.__file__)) == os.path.abspath(eng)
cs_fast.warm_up()
s = cs_fast.Searcher()
s.NNA[C.N1_CTRL, :8] = 0
jobs = [(f, 10) for f in BALANCED_OPENINGS] + [(f, 8) for f in json.load(open(roots_path, encoding="utf-8"))]
for fen, depth in jobs:
    s.new_game()
    s.search(chess.Board(fen), 0, max_depth=depth)
n = int(s.NNA[C.N1_CTRL, 5])
rows = []
for i in range(n):
    r = s.NNA[C.N1_AUDIT0 + i]
    bb = [0] * 13
    for c in range(1, 13):
        lo, hi = int(r[2 * c]) & 0xFFFFFFFF, int(r[2 * c + 1])
        bb[c] = (hi << 32) | lo
    phase = min(24, sum(bin(bb[c] & 0xFFFFFFFFFFFFFFFF).count("1") * w
                        for c, w in ((2, 1), (8, 1), (3, 1), (9, 1), (4, 2), (10, 2), (5, 4), (11, 4))))
    rows.append(dict(stm=int(r[0]), f=int(r[1]), e0_white=int(r[26]), phase=phase))
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(dict(evaluate_calls=int(s.NNA[C.N1_CTRL, 0]), sampled=n, rows=rows), fh)
print(json.dumps(dict(evaluate_calls=int(s.NNA[C.N1_CTRL, 0]), sampled=n)))
