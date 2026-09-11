"""One engine directory, one process: fixed-depth and fixed-budget search over BALANCED_OPENINGS.

Numba compiles per process, so every engine variant is measured in its own subprocess. Completed
depth never counts a partial iteration: when the clock stops an iteration after a root move was
committed (info.aborted with CTL[5] != 0), cs_fast reports that iteration's depth; here it is
recorded as partial and completed depth is one less. For N1 builds the accumulator counters
(evaluate calls, rebuilds, catch-up steps, verify mismatches) are recorded per position.

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
import cs_core  # noqa: E402
import cs_fast  # noqa: E402
from tools.positions import BALANCED_OPENINGS  # noqa: E402

assert os.path.dirname(os.path.abspath(cs_fast.__file__)) == os.path.abspath(eng), cs_fast.__file__
t0 = time.perf_counter()
cs_fast.warm_up()
compile_s = time.perf_counter() - t0
s = cs_fast.Searcher()
has_n1 = hasattr(s, "NNA")
nodes = 0
seconds = 0.0
reported, completed, partial, moves = [], [], [], []
researches = unstable = 0
counters = dict(evaluate_calls=0, rebuilds=0, catch_up_steps=0, verify_mismatches=0, root_searches=0)
for fen in BALANCED_OPENINGS:
    s.new_game()
    if has_n1:
        s.NNA[cs_core.N1_CTRL, :8] = 0
    r0 = s.researches
    t = time.perf_counter()
    if mode == "depth":
        mv, info = s.search(chess.Board(fen), 0, max_depth=arg)
    else:
        mv, info = s.search(chess.Board(fen), 0, fixed_budget_ms=float(arg))
    seconds += time.perf_counter() - t
    nodes += info.nodes
    part = bool(info.aborted and s.CTL[5] != 0)
    reported.append(info.depth)
    partial.append(part)
    completed.append(info.depth - 1 if part else info.depth)
    moves.append(mv.uci() if mv else None)
    researches += s.researches - r0
    unstable += info.unstable_iterations
    if has_n1:
        c = s.NNA[cs_core.N1_CTRL]
        counters["evaluate_calls"] += int(c[0])
        counters["rebuilds"] += int(c[1])
        counters["catch_up_steps"] += int(c[2])
        counters["verify_mismatches"] += int(c[4])
        counters["root_searches"] += int(c[7])
print(json.dumps(dict(engine=os.path.abspath(eng), mode=mode, arg=arg, nodes=nodes, seconds=round(seconds, 3),
                      nps=round(nodes / seconds), mean_depth=round(sum(completed) / len(completed), 3),
                      mean_reported_depth=round(sum(reported) / len(reported), 3), partial_iterations=sum(partial),
                      completed=completed, moves=moves, researches=researches, unstable_iterations=unstable,
                      compile_s=round(compile_s, 1), n1_counters=counters if has_n1 else None)))
