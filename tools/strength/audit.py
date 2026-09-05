"""Large-error audit of ClaudeShark's own moves in an annotated match.

Input: the games schema after `tools.postmortem.annotate` (every move carries
`cp_loss`, `sf_best`, `sf_cp_white_before/after`). Only ClaudeShark's moves
are audited. Each is binned (<50, 50-99, 100-299, >=300 cp); every move
losing at least 100 cp is a SELF-INFLICTED error and is worked up:

* the engine is replayed on the position at the game's think budget (the
  recorded spend when the record has it, else --ms) for root score, depth,
  PV, static and quiescence scores;
* it is replayed again at a longer budget (--deep-ms) to ask whether more
  depth repairs the move, and the repaired move is scored by the oracle so
  "repair" means the deeper move loses under 100 cp, not merely "differs";
* a fixed-depth ladder finds the minimum depth at which the error move is
  no longer chosen.

The mechanism column is deliberately left for a person: the numbers here are
the evidence for that classification, not the classification.

    uv run python -m tools.strength.audit --games <annotated.jsonl> --engine champions/rc_c \
        --out <errors.jsonl> --report <report.md>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import chess

from tools.corpus.oracle import label_many

MATE_CP = 10_000
WORKER = r"""
import sys, json
sys.path.insert(0, sys.argv[1])
import chess
from cs_search import Searcher
from cs_constants import INFINITY
from cs_eval import evaluate
fen, ms, deep_ms, depths = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), json.loads(sys.argv[5])
out = {}
board = chess.Board(fen)
out["static"] = evaluate(board)
try:
    out["qsearch"] = Searcher(tt_bits=14)._quiescence(chess.Board(fen), -INFINITY, INFINITY, 0, 0)
except Exception as failure:
    out["qsearch"] = None
    out["qsearch_error"] = repr(failure)
def run(budget=None, depth=None):
    s = Searcher()
    if budget is not None:
        move, info = s.search(chess.Board(fen), 0, fixed_budget_ms=budget)
    else:
        move, info = s.search(chess.Board(fen), 0, max_depth=depth)
    return {"move": move.uci() if move else None, "score": info.score, "depth": info.depth,
            "nodes": info.nodes, "ms": round(info.elapsed_ms), "pv": info.pv[:8]}
out["timed"] = run(budget=ms)
out["deep"] = run(budget=deep_ms)
out["ladder"] = {str(d): run(depth=d) for d in depths}
print(json.dumps(out))
"""


def replay(engine: Path, fen: str, ms: int, deep_ms: int, depths: list[int]) -> dict:
    result = subprocess.run(
        [sys.executable, "-c", WORKER, str(engine.resolve()), fen, str(ms), str(deep_ms),
         json.dumps(depths)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def bin_of(loss: int) -> str:
    if loss < 50:
        return "<50"
    if loss < 100:
        return "50-99"
    if loss < 300:
        return "100-299"
    return ">=300"


def state(cp_mover: int) -> str:
    if cp_mover >= 150:
        return "win"
    if cp_mover <= -150:
        return "loss"
    return "draw"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--ms", type=int, default=2500,
                        help="replay budget when no spend was recorded")
    parser.add_argument("--deep-ms", type=int, default=10000)
    parser.add_argument("--depths", default="6,7,8,9")
    parser.add_argument("--oracle-nodes", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--max-replays", type=int, default=0, help="0 = every error")
    arguments = parser.parse_args()
    depths = [int(d) for d in arguments.depths.split(",") if d]

    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8") if line.strip()]
    bins: Counter[str] = Counter()
    total_loss = 0
    our_moves = 0
    errors: list[dict] = []
    per_game: dict[str, dict] = {}
    for g in games:
        ours = g["agent_colour"]
        info = per_game.setdefault(g["game"], {
            "score": g["agent_score"], "moves": 0, "e100": 0, "e300": 0, "cp": 0, "flip": 0,
        })
        moves = g["moves"]
        for m in moves:
            if m["turn"] != ours:
                continue
            white = m["turn"] == "w"
            before = m["sf_cp_white_before"] if white else -m["sf_cp_white_before"]
            after = m["sf_cp_white_after"] if white else -m["sf_cp_white_after"]
            if abs(before) >= 800:
                # Decided positions: a "loss" of 400 cp from +1500 changes
                # nothing and mate-score arithmetic is meaningless.
                continue
            loss = int(m["cp_loss"])
            our_moves += 1
            info["moves"] += 1
            bins[bin_of(loss)] += 1
            total_loss += loss
            if loss < 100:
                continue
            flipped = state(before) != state(after) and state(after) != "win"
            info["e100"] += 1
            info["cp"] += loss
            if loss >= 300:
                info["e300"] += 1
            if flipped:
                info["flip"] += 1
            errors.append({
                "game": g["game"], "ply": m["ply"], "fen": m["fen"], "colour": m["turn"],
                "engine_move": m["move"], "san": m["san"], "oracle_move": m["sf_best"],
                "cp_loss": loss, "oracle_before": before, "oracle_after": after,
                "state_before": state(before), "state_after": state(after),
                "result_flipping": flipped, "spent": m.get("spent"), "clock": m.get("clock"),
                "game_result_for_us": g["agent_score"],
                "oracle_nodes": m.get("sf_nodes"),
            })

    errors.sort(key=lambda e: -e["cp_loss"])
    todo = errors if not arguments.max_replays else errors[: arguments.max_replays]
    print(f"{our_moves} of our moves audited; {len(errors)} errors >= 100 cp; "
          f"replaying {len(todo)}", flush=True)

    # Engine replays, one subprocess per error, a few in parallel.
    from concurrent.futures import ThreadPoolExecutor

    def work(e: dict) -> dict:
        ms = int(e["spent"] * 1000) if e.get("spent") else arguments.ms
        ms = max(200, min(ms, 15_000))
        r = replay(arguments.engine, e["fen"], ms, arguments.deep_ms, depths)
        e["replay_ms"] = ms
        e["static"] = r["static"]
        e["qsearch"] = r["qsearch"]
        e["timed"] = r["timed"]
        e["deep"] = r["deep"]
        e["ladder"] = r["ladder"]
        return e

    with ThreadPoolExecutor(max_workers=arguments.workers) as pool:
        list(pool.map(work, todo))

    # Oracle-score the deeper move and the ladder moves so "repair" is measured.
    after_fens: dict[tuple[str, str], str] = {}
    for e in todo:
        board = chess.Board(e["fen"])
        for mv in {e["deep"]["move"], *(x["move"] for x in e["ladder"].values())}:
            if mv and (e["fen"], mv) not in after_fens:
                b = board.copy()
                b.push(chess.Move.from_uci(mv))
                after_fens[(e["fen"], mv)] = b.fen()
    unique = sorted(set(after_fens.values()))
    print(f"oracle scoring {len(unique)} post-move positions at {arguments.oracle_nodes} nodes",
          flush=True)
    labels = {}
    scored = label_many(unique, arguments.oracle_nodes, workers=arguments.workers, progress=True)
    for fen, label in zip(unique, scored, strict=True):
        labels[fen] = label.cp_white

    def loss_of(e: dict, mv: str | None) -> int | None:
        if not mv:
            return None
        fen_after = after_fens[(e["fen"], mv)]
        cp_after = labels[fen_after] if e["colour"] == "w" else -labels[fen_after]
        return max(0, e["oracle_before"] - cp_after)

    for e in todo:
        e["deep_loss"] = loss_of(e, e["deep"]["move"])
        e["deep_repairs"] = e["deep_loss"] is not None and e["deep_loss"] < 100
        e["ladder_loss"] = {d: loss_of(e, x["move"]) for d, x in e["ladder"].items()}
        repaired = [int(d) for d, lost in e["ladder_loss"].items()
                    if lost is not None and lost < 100]
        e["min_repair_depth"] = min(repaired) if repaired else None
        e["timed_reproduces"] = e["timed"]["move"] == e["engine_move"]
        e["mechanism"] = "UNCLASSIFIED"

    with arguments.out.open("w", encoding="utf-8") as fh:
        for e in errors:
            fh.write(json.dumps(e) + "\n")

    n = our_moves or 1
    losses = [g for g in per_game.values() if g["score"] == 0.0]
    e_in_losses = sum(g["e100"] for g in losses)
    lines = [
        f"# Large-error audit — {arguments.games.name}",
        "",
        f"engine {arguments.engine}; {len(games)} games; {our_moves} of our moves audited "
        f"(positions already beyond +/-800 cp excluded)",
        "",
        "| bin | moves | share |",
        "|---|---|---|",
    ]
    for b in ("<50", "50-99", "100-299", ">=300"):
        lines.append(f"| {b} | {bins[b]} | {100.0 * bins[b] / n:.1f}% |")
    e100 = bins["100-299"] + bins[">=300"]
    lines += [
        "",
        f"**>=100 cp self-inflicted error rate: {100.0 * e100 / n:.2f}% of moves** "
        f"({e100} errors); >=300 cp: {100.0 * bins['>=300'] / n:.2f}% ({bins['>=300']}); "
        f"average cp loss {total_loss / n:.1f}",
        f"games with at least one >=100 cp error: "
        f"{sum(1 for g in per_game.values() if g['e100'])} of {len(per_game)}; "
        f"result-flipping errors: {sum(g['flip'] for g in per_game.values())}; "
        f"errors per loss: {e_in_losses / max(1, len(losses)):.2f} over {len(losses)} losses",
        "",
        "## Every >=100 cp error (sorted by cp loss)",
        "",
        "| game | ply | col | played | oracle | loss | before→after | flip | spent s | "
        "replay depth/score | static | qsearch | deep(10 s) move/loss | min repair depth | "
        "mechanism |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for e in errors:
        t = e.get("timed", {})
        d = e.get("deep", {})
        lines.append(
            f"| {e['game'][-4:]} | {e['ply']} | {e['colour']} | {e['san']} | {e['oracle_move']} | "
            f"{e['cp_loss']} | {e['oracle_before']:+d}→{e['oracle_after']:+d} | "
            f"{'Y' if e['result_flipping'] else ''} | "
            f"{e['spent'] if e['spent'] is not None else '-'} | "
            f"{t.get('depth', '-')}/{t.get('score', '-')}"
            f"{'' if e.get('timed_reproduces', True) else ' (replay differs)'} | "
            f"{e.get('static', '-')} | {e.get('qsearch', '-')} | "
            f"{d.get('move', '-')}/{e.get('deep_loss', '-')} | {e.get('min_repair_depth', '-')} | "
            f"{e.get('mechanism', 'UNCLASSIFIED')} |"
        )
    arguments.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))
    print(f"errors written to {arguments.out}; report {arguments.report}")


if __name__ == "__main__":
    main()
