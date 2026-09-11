"""One engine, one process: search a list of positions and record the chosen move.

    python search_probe.py ENGINE_DIR POSITIONS.jsonl OUT.jsonl (--budget-ms N | --clock | --depth-key KEY)

POSITIONS rows: {"id", "fen", optional "clock_ms", optional depth under KEY}. Every search starts
from a fresh table (new_game). --budget-ms uses a fixed budget; --clock uses the production clock
path with the row's clock_ms (competition-like); --depth-key searches to the row's fixed depth.
"""
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
eng, pos_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.abspath(eng))

import chess  # noqa: E402
import cs_fast  # noqa: E402

assert os.path.dirname(os.path.abspath(cs_fast.__file__)) == os.path.abspath(eng), cs_fast.__file__
mode = sys.argv[4]
arg = sys.argv[5] if len(sys.argv) > 5 else None
cs_fast.warm_up()
s = cs_fast.Searcher()
with open(pos_path, encoding="utf-8") as fh, open(out_path, "w", encoding="utf-8") as out:
    for line in fh:
        p = json.loads(line)
        board = chess.Board(p["fen"])
        s.new_game()
        t = time.perf_counter()
        if mode == "--budget-ms":
            mv, info = s.search(board, 0, fixed_budget_ms=float(arg))
        elif mode == "--clock":
            mv, info = s.search(board, int(p["clock_ms"]))
        else:
            mv, info = s.search(board, 0, max_depth=int(p[arg]))
        out.write(json.dumps(dict(id=p["id"], move=mv.uci() if mv else None, score=info.score, depth=info.depth,
                                  nodes=info.nodes, seconds=round(time.perf_counter() - t, 3))) + "\n")
        out.flush()
