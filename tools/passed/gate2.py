"""Gate 2 summary for the passed-pawn candidate: match statistics and the targeted metric.

Alongside W/D/L with the paired cluster bootstrap and the termination mix,
this answers the question the experiment was built to answer. The term can
only act where a passed pawn exists, so every annotated move is bucketed by
whether the mover had a passer, and how far advanced, and the Stockfish loss
of the candidate's moves is set beside the baseline's in each bucket. If the
term helps, the buckets with passers should improve and the bucket without
should not move.

    uv run python -m tools.passed.gate2 --games <gate2_annotated.jsonl> --out <txt>
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import chess

from cs_passed import passed_pawn_mask
from tools.stats import summarise


def best_rank(board: chess.Board, white: bool) -> int:
    ranks = [chess.square_rank(sq) if white else 7 - chess.square_rank(sq)
             for sq in chess.scan_forward(passed_pawn_mask(board, white))]
    return max(ranks) if ranks else -1


def bucket(rank: int) -> str:
    if rank < 0:
        return "no own passer"
    if rank <= 3:
        return "passer rank 2-4"
    if rank <= 5:
        return "passer rank 5-6"
    return "passer rank 7"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--cand-name", default="v0_8_passed")
    parser.add_argument("--base-name", default="v0_5_2_correctness")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    stats = summarise([(int(g["cluster"]), g["cand_score"]) for g in games])
    lines = [f"== GATE 2: {len(games)} fixed-depth paired games, {arguments.cand_name} (candidate) vs {arguments.base_name} ==", "",
             f"+{stats.wins} ={stats.draws} -{stats.losses}  score {stats.score:.1%}  Elo {stats.elo:+.0f}",
             f"naive 95% CI {stats.naive_low:+.0f} .. {stats.naive_high:+.0f}   paired cluster bootstrap {stats.boot_low:+.0f} .. {stats.boot_high:+.0f}  ({stats.clusters} clusters)",
             f"terminations: {dict(Counter(g['termination'] for g in games))}",
             f"failures (no_move / ply_cap): {sum(1 for g in games if g['termination'] in ('no_move', 'ply_cap'))}",
             f"as white: cand {sum(g['cand_score'] for g in games if g['cand_white']) / max(1, sum(1 for g in games if g['cand_white'])):.1%}, "
             f"as black: cand {sum(g['cand_score'] for g in games if not g['cand_white']) / max(1, sum(1 for g in games if not g['cand_white'])):.1%}", ""]

    lines.append("== TARGETED METRIC: Stockfish loss of each side's moves, by the mover's most advanced passer ==")
    lines.append("(annotated moves only; loss winsorised at 500; serious = loss >= 100; endgame = phase24 <= 8 by the engine's own phase)")
    rows: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for g in games:
        for m in g["moves"]:
            if m.get("cp_loss") is None:
                continue
            board = chess.Board(m["fen"])
            white = board.turn == chess.WHITE
            b = bucket(best_rank(board, white))
            phase = ((board.knights | board.bishops).bit_count() + 2 * board.rooks.bit_count() + 4 * board.queens.bit_count())
            stage = "endgame" if phase <= 8 else "middlegame"
            rows[(m["mover"], stage, b)].append(min(m["cp_loss"], 500))
            rows[(m["mover"], "all", b)].append(min(m["cp_loss"], 500))
    lines.append(f"  {'stage':<11} {'bucket':<17} {'cand n':>7} {'cand loss':>10} {'cand ser':>9} | {'base n':>7} {'base loss':>10} {'base ser':>9}")
    for stage in ("all", "endgame", "middlegame"):
        for b in ("no own passer", "passer rank 2-4", "passer rank 5-6", "passer rank 7"):
            c = rows.get(("cand", stage, b), [])
            d = rows.get(("base", stage, b), [])
            if not c and not d:
                continue
            lines.append(f"  {stage:<11} {b:<17} {len(c):>7} {statistics.mean(c) if c else 0:>10.1f} {sum(x >= 100 for x in c) / max(1, len(c)):>9.1%} | "
                         f"{len(d):>7} {statistics.mean(d) if d else 0:>10.1f} {sum(x >= 100 for x in d) / max(1, len(d)):>9.1%}")
    lines.append("")
    lines.append("== GAMES DECIDED WITH A PASSER ON THE BOARD: who had the more advanced passer at ply 60 and who won ==")
    tally: Counter = Counter()
    for g in games:
        if len(g["moves"]) <= 60:
            continue
        board = chess.Board(g["moves"][60]["fen"])
        cw = best_rank(board, g["cand_white"])
        bw = best_rank(board, not g["cand_white"])
        if cw == bw:
            continue
        holder = "cand" if cw > bw else "base"
        holder_score = g["cand_score"] if holder == "cand" else 1.0 - g["cand_score"]
        result = "won" if holder_score == 1.0 else ("drew" if holder_score == 0.5 else "lost")
        tally[(holder, result)] += 1
    for holder in ("cand", "base"):
        n = sum(v for (h, _), v in tally.items() if h == holder)
        lines.append(f"  {holder} held the better passer in {n} games: won {tally[(holder, 'won')]}, drew {tally[(holder, 'drew')]}, lost {tally[(holder, 'lost')]}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
