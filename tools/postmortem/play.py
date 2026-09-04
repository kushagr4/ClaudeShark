"""Paired fixed-depth diagnostic games between two snapshots.

This is **not** a rerun of the arena. The arena games were played on a clock
and their move lists were not retained; these are deterministic depth-limited
games from the same 100 starting positions, both colours, with every move,
both engines' search scores, both engines' static evaluations of every
position and the pruning counters recorded. Their purpose is reconstruction
and diagnosis, and their score is reported only as a check that the
phenomenon reproduces at fixed depth -- which itself separates evaluation
effects from clock effects.

    uv run python -m tools.postmortem.play --cand <dir> --base <dir> --depth 6 --workers 5
"""

from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import chess

from harness.referee import DRAW_CLAIM_MODES, game_outcome
from tools.matchlock import own

WORKER = Path(__file__).with_name("worker.py")


class Engine:
    def __init__(self, directory: Path, depth: int) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, str(WORKER), str(directory), str(depth)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def ask(self, line: str) -> dict:
        assert self.proc.stdin and self.proc.stdout
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.ask("quit")
        self.proc.kill()


def play_one(args: tuple) -> dict:
    cand_dir, base_dir, depth, cluster, fen, cand_white, ply_cap, draw_claim = args
    cand = Engine(Path(cand_dir), depth)
    base = Engine(Path(base_dir), depth)
    cand.ask("new")
    base.ask("new")
    board = chess.Board(fen)
    plies = []
    termination = "ply_cap"
    try:
        while len(plies) < ply_cap:
            outcome = game_outcome(board, draw_claim)
            if outcome is not None:
                termination = outcome.termination.name.lower()
                break
            mover_is_cand = (board.turn == chess.WHITE) == cand_white
            mover, other = (cand, base) if mover_is_cand else (base, cand)
            fen_before = board.fen()
            reply = mover.ask(f"go {fen_before}")
            other_static = other.ask(f"static {fen_before}")["static"]
            move = reply["move"]
            if move is None:
                termination = "no_move"
                break
            rec = {
                "ply": len(plies),
                "fen": fen_before,
                "mover": "cand" if mover_is_cand else "base",
                "move": move,
                "turn": "w" if board.turn else "b",
                "score_stm": reply["score"],
                "cand_static": reply["static"] if mover_is_cand else other_static,
                "base_static": other_static if mover_is_cand else reply["static"],
            }
            for k, v in reply.items():
                if k.startswith("c_") or k in (
                    "nodes",
                    "qnodes",
                    "researches",
                    "tt_hits",
                    "tt_probes",
                    "cutoffs",
                ):
                    rec[k] = v
            plies.append(rec)
            board.push_uci(move)
    finally:
        cand.close()
        base.close()
    finish = game_outcome(board, draw_claim)
    result = finish.result() if finish is not None else "1/2-1/2"
    if result == "1-0":
        cand_score = 1.0 if cand_white else 0.0
    elif result == "0-1":
        cand_score = 0.0 if cand_white else 1.0
    else:
        cand_score = 0.5
    return {
        "cluster": cluster,
        "start_fen": fen,
        "cand_white": cand_white,
        "depth": depth,
        "draw_claim": draw_claim,
        "result": result,
        "cand_score": cand_score,
        "termination": termination,
        "plies": len(plies),
        "final_fen": board.fen(),
        "moves": plies,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cand", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--pairs", type=Path, default=Path("corpus/postmortem/pairs.json"))
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--ply-cap", type=int, default=300)
    parser.add_argument(
        "--out", type=Path, default=Path("corpus/postmortem/games/fixed_depth.jsonl")
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--draw-claim", choices=DRAW_CLAIM_MODES, default="auto")
    parser.add_argument(
        "--force-unlock",
        action="store_true",
        help="take over an output path whose recorded owner process is dead; refuses while it lives",
    )
    arguments = parser.parse_args()

    pairs = json.load(arguments.pairs.open())
    if arguments.limit:
        pairs = pairs[: arguments.limit]
    tasks = []
    for p in pairs:
        for cand_white in (True, False):
            tasks.append(
                (
                    str(arguments.cand),
                    str(arguments.base),
                    arguments.depth,
                    p["cluster"],
                    p["fen"],
                    cand_white,
                    arguments.ply_cap,
                    arguments.draw_claim,
                )
            )
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    done = 0
    score = 0.0
    # Ownership is taken before the output is opened, because the failure this
    # guards against is a second match truncating a file the first is still
    # writing. Two independent runs against one path have happened twice in this
    # project; the first corrupted a JSONL that had to be discarded.
    with (
        own(arguments.out, sys.argv, force=arguments.force_unlock),
        arguments.out.open("w", encoding="utf-8") as fh,
        ProcessPoolExecutor(max_workers=arguments.workers) as pool,
    ):
        futures = [pool.submit(play_one, t) for t in tasks]
        for fut in as_completed(futures):
            game = fut.result()
            fh.write(json.dumps(game) + "\n")
            fh.flush()
            done += 1
            score += game["cand_score"]
            print(
                f"[{done:>3}/{len(tasks)}] cluster {game['cluster']:>3} "
                f"{'cW' if game['cand_white'] else 'cB'} {game['result']:<7} "
                f"{game['termination']:<22} {game['plies']:>3} plies   "
                f"running cand score {score / done:.1%}",
                flush=True,
            )
    print(f"fixed-depth diagnostic set: {done} games, candidate score {score / done:.1%}")


if __name__ == "__main__":
    main()
