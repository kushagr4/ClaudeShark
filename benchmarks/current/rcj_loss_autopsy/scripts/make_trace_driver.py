"""Generate cs_fast_trace.py: RC-J's driver with a completed-iteration trace.

Diagnostic only. Every line added runs BETWEEN iterations or after the search,
so it cannot change what the tree does, and the generated file drives the
**shipped** cs_core -- no counters, no instrumented core, nothing from C20.

The discipline Codex's harness specification insists on is implemented here and
is the reason this file exists rather than a print statement:

* an iteration counts as COMPLETED only when `CTL[0]` is clear after
  `_search_root_aspirated` returns. `SearchInfo.depth` equalling the attempted
  depth is not sufficient, because the driver assigns it from a partial
  commit too;
* an aborted attempt is recorded separately, with its partial move and score
  from `CTL[5]`/`CTL[6]`, and never enters the completed list;
* aspiration re-searches belong to the cost of the iteration that owns them,
  not to a new depth.

    make_trace_driver.py            regenerate
    make_trace_driver.py --check    verify the committed copy
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "cs_fast.py")
DST = os.path.join(ROOT, "cs_fast_trace.py")

HEADER = '''"""RC-J's driver plus a completed-iteration trace. GENERATED, diagnostic only.

Drives the shipped cs_core unchanged. Everything added records state between
iterations; nothing reads a recorded value back, so the search is RC-J's.
"""

'''

PATCHES = [
    # --- fields on the info record -------------------------------------
    ("    researches: int = 0\n    pv: list[str] = field(default_factory=list)\n",
     "    researches: int = 0\n"
     "    pv: list[str] = field(default_factory=list)\n"
     "    # --- diagnostic trace, never read by the search ---\n"
     "    stop_reason: str = \"\"\n"
     "    soft_ms: float = 0.0\n"
     "    hard_ms: float = 0.0\n"
     "    start_threshold_ms: float = 0.0\n"
     "    panic: bool = False\n"
     "    clock_ms: float = 0.0\n"
     "    attempted_depth: int = 0\n"
     "    completed_depth: int = 0\n"
     "    completed_move: str = \"\"\n"
     "    completed_score: int = 0\n"
     "    returned_source: str = \"\"\n"
     "    iterations: list = field(default_factory=list)\n"
     "    aborted_attempt: dict = field(default_factory=dict)\n"),

    # --- budget snapshot ------------------------------------------------
    ("        info.budget_ms = timer.soft_ms\n",
     "        info.budget_ms = timer.soft_ms\n"
     "        info.soft_ms = timer.soft_ms\n"
     "        info.hard_ms = timer.hard_ms\n"
     "        info.start_threshold_ms = timer.soft_ms * START_FRACTION\n"
     "        info.panic = timer.panicking\n"
     "        info.clock_ms = float(time_left_ms)\n"),

    ("        if len(legal) == 1:\n            info.depth = 0\n            return legal[0], info\n",
     "        if len(legal) == 1:\n"
     "            info.depth = 0\n"
     "            info.stop_reason = \"SINGLE_LEGAL\"\n"
     "            info.returned_source = \"single legal move\"\n"
     "            return legal[0], info\n"),

    # --- the iterative-deepening loop -----------------------------------
    ("        for depth in range(1, depth_limit + 1):\n"
     "            CTL[5] = 0\n"
     "            CTL[9] = depth\n"
     "            score, move, ordered = self._search_root_aspirated(depth, root_moves, best_score)\n"
     "            if CTL[0]:\n"
     "                info.aborted = True\n",
     "        for depth in range(1, depth_limit + 1):\n"
     "            info.attempted_depth = depth\n"
     "            _n0, _q0, _t0 = int(CTL[2]), int(CTL[3]), timer.elapsed_ms()\n"
     "            _r0 = self.researches\n"
     "            _roots_in = [core.move_to_uci(m) for m in root_moves]\n"
     "            CTL[5] = 0\n"
     "            CTL[9] = depth\n"
     "            score, move, ordered = self._search_root_aspirated(depth, root_moves, best_score)\n"
     "            if CTL[0]:\n"
     "                # An ABORTED attempt. Never a completed depth, whatever\n"
     "                # SearchInfo.depth ends up saying.\n"
     "                info.aborted_attempt = dict(\n"
     "                    attempted_depth=depth, completed=False,\n"
     "                    partial_move=(core.move_to_uci(int(CTL[5])) if CTL[5] else None),\n"
     "                    partial_score=(int(CTL[6]) if CTL[5] else None),\n"
     "                    nodes_delta=int(CTL[2]) - _n0,\n"
     "                    ms=timer.elapsed_ms() - _t0,\n"
     "                    aspiration_researches=self.researches - _r0)\n"
     "                info.stop_reason = \"HARD_LIMIT\"\n"
     "                info.aborted = True\n"),

    ("            previous_move, previous_score = best_move, best_score\n"
     "            best_move, best_score, root_moves = move, score, ordered\n"
     "            info.depth = depth\n",
     "            previous_move, previous_score = best_move, best_score\n"
     "            best_move, best_score, root_moves = move, score, ordered\n"
     "            info.depth = depth\n"
     "            _t1 = timer.elapsed_ms()\n"
     "            info.completed_depth = depth\n"
     "            info.completed_move = core.move_to_uci(int(move))\n"
     "            info.completed_score = int(score)\n"
     "            info.iterations.append(dict(\n"
     "                attempted_depth=depth, completed=True,\n"
     "                searched_best_uci=core.move_to_uci(int(move)), score_cp_stm=int(score),\n"
     "                nodes_cumulative=int(CTL[2]), nodes_delta=int(CTL[2]) - _n0,\n"
     "                qnodes_delta=int(CTL[3]) - _q0,\n"
     "                elapsed_cumulative_ms=_t1, duration_ms=_t1 - _t0,\n"
     "                aspiration_researches=self.researches - _r0,\n"
     "                roots_in=_roots_in[:8],\n"
     "                roots_out=[core.move_to_uci(m) for m in ordered[:8]],\n"
     "                move_changed=(int(move) != int(previous_move)) if depth > 1 else None))\n"),

    ("                if core.MATE_SCORE - abs(best_score) <= depth:\n                    break\n",
     "                if core.MATE_SCORE - abs(best_score) <= depth:\n"
     "                    info.stop_reason = \"MATE_PROVEN\"\n"
     "                    break\n"),

    ("            if max_depth is None and not timer.should_start_iteration():\n"
     "                break\n",
     "            if max_depth is None and not timer.should_start_iteration():\n"
     "                info.stop_reason = \"PANIC\" if timer.panicking else \"SOFT_START_FRACTION\"\n"
     "                break\n"),

    ("        if info.depth >= 1 and board.halfmove_clock < core.TT_HALFMOVE_LIMIT:\n",
     "        if not info.stop_reason:\n"
     "            info.stop_reason = \"MAX_DEPTH\"\n"
     "        if info.depth >= 1 and board.halfmove_clock < core.TT_HALFMOVE_LIMIT:\n"),

    # --- how the returned move was arrived at ---------------------------
    ("        if drawing and best_score < 0:\n"
     "            best_move = drawing[0]\n"
     "            info.score = best_score = 0\n",
     "        info.returned_source = (\"partial commit\" if info.aborted else\n"
     "                                \"completed iteration\")\n"
     "        if drawing and best_score < 0:\n"
     "            info.returned_source = \"repetition fallback\"\n"
     "            best_move = drawing[0]\n"
     "            info.score = best_score = 0\n"),
]


def build() -> str:
    text = open(SRC, encoding="utf-8").read()
    for anchor, replacement in PATCHES:
        found = text.count(anchor)
        if found != 1:
            raise SystemExit(f"anchor occurs {found} times, expected 1:\n{anchor[:200]!r}")
        text = text.replace(anchor, replacement)
    text = text.replace("from cs_time import TimeManager",
                        "from cs_time import START_FRACTION, TimeManager", 1)
    close = text.index('"""', text.index('"""') + 3) + 3
    return HEADER + text[close:].lstrip("\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    produced = build()
    if args.check:
        current = open(DST, encoding="utf-8").read() if os.path.exists(DST) else ""
        if current != produced:
            print("cs_fast_trace.py is stale", file=sys.stderr)
            raise SystemExit(2)
        print("cs_fast_trace.py matches its generator")
        return
    with open(DST, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(produced)
    print(f"wrote {DST} ({len(PATCHES)} anchored patches)")


if __name__ == "__main__":
    main()
