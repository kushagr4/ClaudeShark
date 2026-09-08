"""One build, one process, three measurements.

Numba compiles per process and the modules cannot be swapped inside one, so
every build is measured in its own interpreter and the driver alternates them.
Each process reports:

  asm    instruction count and stack traffic of the compiled move loop
  depth  fixed depth 10 over the suite: node count is deterministic, so the
         time is a pure speed measurement and the nodes prove tree identity
  time   fixed 2000 ms over the suite: the competition-shaped number

usage: probe.py <build_dir>
"""
import json
import os
import sys
import time

BUILD = sys.argv[1]
LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/c15v2"

sys.path.insert(0, LANE)
sys.path.insert(0, BUILD)

import chess  # noqa: E402
import cs_fast  # noqa: E402
import cs_core  # noqa: E402
from tools.positions import BALANCED_OPENINGS  # noqa: E402

assert os.path.dirname(cs_core.__file__).replace("\\", "/").endswith(
    os.path.basename(BUILD)), cs_core.__file__

cs_fast.warm_up()

asm = {}
for name in ("negamax", "quiescence", "make_move"):
    text = "".join(getattr(cs_core, name).inspect_asm().values())
    lines = [ln.strip() for ln in text.splitlines()
             if ln.strip() and not ln.strip().startswith((".", "#"))]
    asm[name] = dict(
        insns=len(lines),
        # Anything addressed off rsp in the body is stack traffic: spilled
        # values the register allocator could not keep in registers.
        stack_ops=sum(1 for ln in lines if "(%rsp)" in ln or "rsp)" in ln),
    )


def run(mode, arg):
    searcher = cs_fast.Searcher()
    nodes = 0
    elapsed = 0.0
    depth_sum = 0
    for fen in BALANCED_OPENINGS:
        searcher.new_game()
        board = chess.Board(fen)
        t0 = time.perf_counter()
        if mode == "depth":
            _, info = searcher.search(board, 0, max_depth=arg)
        else:
            _, info = searcher.search(board, arg)
        elapsed += time.perf_counter() - t0
        nodes += info.nodes
        depth_sum += info.depth
    return dict(nodes=nodes, seconds=round(elapsed, 3), nps=int(nodes / elapsed),
                depth_sum=depth_sum)


print("JSON" + json.dumps(dict(build=os.path.basename(BUILD), asm=asm,
                               depth10=run("depth", 10), ms2000=run("time", 2000))))
