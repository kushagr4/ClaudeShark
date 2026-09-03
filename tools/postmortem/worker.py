"""Engine worker for the post-mortem: one snapshot, one process, fixed depth.

Line protocol on stdin/stdout. Every reply is one JSON line.

    new                      fresh Searcher (new game; transposition table cleared)
    go <fen>                 search at the fixed depth; move, score and counters
    static <fen>             the snapshot's own static evaluation, white's view
    quit

A fixed-depth search is deterministic, which is what makes the diagnostic games
reproducible and lets the pruning counters of two engines be compared on the
same tree budget rather than the same wall clock.
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    engine_dir, depth = sys.argv[1], int(sys.argv[2])
    sys.path.insert(0, engine_dir)
    import chess

    from cs_eval import evaluate
    from cs_search import Searcher

    sys.setrecursionlimit(10_000)
    searcher = Searcher()
    counters = [c for c in dir(searcher) if c.startswith("c_")]

    def white_pov(board: chess.Board) -> int:
        score = evaluate(board)
        return score if board.turn == chess.WHITE else -score

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        cmd, _, arg = line.partition(" ")
        if cmd == "quit":
            break
        if cmd == "seen":
            # Replay a root position the engine was handed earlier in its game,
            # without paying for the search. This reproduces the game-level
            # repetition record (`_game_counts`) exactly as the real game built
            # it, which is what makes "what would it play here?" a faithful
            # question rather than a fresh-searcher one.
            key = hash(chess.Board(arg)._transposition_key())
            searcher._game_counts[key] = searcher._game_counts.get(key, 0) + 1
            print(json.dumps({"ok": True, "seen": len(searcher._game_counts)}), flush=True)
            continue
        if cmd == "new":
            searcher = Searcher()
            searcher.new_game()
            print(json.dumps({"ok": True}), flush=True)
            continue
        board = chess.Board(arg)
        if cmd == "static":
            print(json.dumps({"static": white_pov(board)}), flush=True)
            continue
        if cmd == "go":
            move, info = searcher.search(board, 60_000, max_depth=depth)
            reply = {
                "move": move.uci() if move else None,
                "score": info.score,  # side to move
                "depth": info.depth,
                "nodes": info.nodes,
                "qnodes": info.qnodes,
                "researches": info.researches,
                "cutoffs": info.cutoffs,
                "tt_hits": info.tt_hits,
                "tt_probes": info.tt_probes,
                "static": white_pov(board),
                "pv": list(info.pv),
            }
            for c in counters:
                reply[c] = getattr(searcher, c)
            print(json.dumps(reply), flush=True)
            continue
        print(json.dumps({"error": f"unknown command {cmd}"}), flush=True)


if __name__ == "__main__":
    main()
