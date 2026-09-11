"""One engine directory, one process: fixed-depth and fixed-budget search over BALANCED_OPENINGS.

Numba compiles per process, so every engine variant is measured in its own subprocess.

    python speed_probe.py ENGINE_DIR depth 10
    python speed_probe.py ENGINE_DIR budget 1000
"""
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
eng, mode, arg = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.abspath(eng))

import chess  # noqa: E402
import cs_fast  # noqa: E402
from tools.positions import BALANCED_OPENINGS  # noqa: E402

assert os.path.dirname(os.path.abspath(cs_fast.__file__)) == os.path.abspath(eng), cs_fast.__file__
t0 = time.perf_counter()
cs_fast.warm_up()
compile_s = time.perf_counter() - t0
s = cs_fast.Searcher()
nodes = 0
seconds = 0.0
depths, moves = [], []
for fen in BALANCED_OPENINGS:
    s.new_game()
    t = time.perf_counter()
    if mode == "depth":
        mv, info = s.search(chess.Board(fen), 0, max_depth=arg)
    else:
        mv, info = s.search(chess.Board(fen), 0, fixed_budget_ms=float(arg))
    seconds += time.perf_counter() - t
    nodes += info.nodes
    depths.append(info.depth)
    moves.append(mv.uci() if mv else None)
print(json.dumps(dict(engine=os.path.abspath(eng), mode=mode, arg=arg, nodes=nodes, seconds=round(seconds, 3),
                      nps=round(nodes / seconds), mean_depth=round(sum(depths) / len(depths), 3),
                      depths=depths, moves=moves, compile_s=round(compile_s, 1))))
