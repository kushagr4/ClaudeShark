"""One engine, one process: fixed-depth or fixed-budget search over the 24 balanced openings.

Numba compiles per process, so every engine (and every CS_NNUE setting) is measured in its own
subprocess. The NNUE setting is whatever the environment says when this process starts. Completed
depth never counts a partial iteration. When the engine has the NNUE compiled in, its accumulator
counters (evaluations, rebuilds, catch-up steps, verify mismatches, root seeds) are summed.

    python probe.py ENGINE_DIR depth 10
    python probe.py ENGINE_DIR budget 1000
    python probe.py ENGINE_DIR selfplay 5        (60 plies at fixed depth, no new_game in between)
"""

from __future__ import annotations

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
assert os.path.dirname(os.path.abspath(cs_core.__file__)) == os.path.abspath(eng), cs_core.__file__
t0 = time.perf_counter()
cs_fast.warm_up()
compile_s = time.perf_counter() - t0
s = cs_fast.Searcher()
nnue = bool(getattr(cs_core, "NNUE_ENABLED", False))
counters = dict(evaluate_calls=0, rebuilds=0, catch_up_steps=0, verify_mismatches=0, root_seeds=0)


def take_counters() -> None:
    if not hasattr(s, "NNA"):
        return
    c = s.NNA[cs_core.N1_CTRL]
    counters["evaluate_calls"] += int(c[0])
    counters["rebuilds"] += int(c[1])
    counters["catch_up_steps"] += int(c[2])
    counters["verify_mismatches"] += int(c[4])
    counters["root_seeds"] += int(c[7])
    c[:8] = 0


nodes, seconds, researches, unstable = 0, 0.0, 0, 0
completed, partial, moves = [], [], []
if mode == "selfplay":
    s.new_game()
    board = chess.Board(BALANCED_OPENINGS[0])
    while len(moves) < 60 and not board.is_game_over(claim_draw=True):
        t = time.perf_counter()
        mv, info = s.search(board, 0, max_depth=arg)
        seconds += time.perf_counter() - t
        nodes += info.nodes
        moves.append(mv.uci())
        completed.append(info.depth)
        board.push(mv)
        take_counters()
else:
    for fen in BALANCED_OPENINGS:
        s.new_game()
        r0 = s.researches
        t = time.perf_counter()
        if mode == "depth":
            mv, info = s.search(chess.Board(fen), 0, max_depth=arg)
        else:
            mv, info = s.search(chess.Board(fen), 0, fixed_budget_ms=float(arg))
        seconds += time.perf_counter() - t
        nodes += info.nodes
        part = bool(info.aborted and s.CTL[5] != 0)
        partial.append(part)
        completed.append(info.depth - 1 if part else info.depth)
        moves.append(mv.uci() if mv else None)
        researches += s.researches - r0
        unstable += info.unstable_iterations
        take_counters()

print(
    json.dumps(
        dict(
            engine=os.path.abspath(eng),
            mode=mode,
            arg=arg,
            nnue=nnue,
            nnue_verify=bool(getattr(cs_core, "NNUE_VERIFY", False)),
            nodes=nodes,
            seconds=round(seconds, 3),
            nps=round(nodes / seconds) if seconds else 0,
            mean_depth=round(sum(completed) / len(completed), 3),
            partial_iterations=sum(partial),
            completed=completed,
            moves=moves,
            researches=researches,
            unstable_iterations=unstable,
            compile_s=round(compile_s, 1),
            counters=counters,
        )
    )
)
