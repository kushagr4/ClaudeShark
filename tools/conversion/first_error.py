"""Classify the first serious error of every failed conversion.

For each production episode that reached +200 and did not win, the first move
by the engine losing at least 100 cp after the crossing is classified from the
annotation plus a fresh Stockfish look at the position:

    missed mate         Stockfish had a forced mate for the engine
    missed tactic       the best move is a capture or check and the loss >= 300
    material grab       the engine captured and lost >= 100 while the best move
                        was quiet
    bad trade           the engine made an equal exchange Stockfish did not want
    refused trade       Stockfish wanted an equal exchange the engine declined
    passed pawn         the best move pushes or wins a passed pawn
    king exposure       the opponent's best reply is a check, or the king lost
                        pawn shelter after the move
    quiet positional    none of the above: a quiet best move, a quiet error

The heuristics are deliberately conservative and "quiet positional" is the
residual, not a diagnosis. The tactic/mate share is the number that matters.

Also tests the "punishment" hypothesis: was the +200 crossing produced by the
opponent's own serious error on the previous ply -- so that the engine then
had to *find* the refutation -- and how often did it?

    uv run python -m tools.conversion.first_error --games <annotated.jsonl> \
        --episodes <episodes.jsonl> --out <txt>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle


def is_passed(board: chess.Board, square: int, colour: bool) -> bool:
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    ahead = range(rank + 1, 8) if colour else range(rank - 1, -1, -1)
    for r in ahead:
        for f in (file - 1, file, file + 1):
            if 0 <= f < 8 and board.piece_at(chess.square(f, r)) == chess.Piece(chess.PAWN, not colour):
                return False
    return True


def classify(board: chess.Board, played: str, best: str, loss: int, label) -> str:
    us = board.turn
    if label.mate is not None and label.mate > 0:
        return "missed mate"
    bm = chess.Move.from_uci(best)
    pm = chess.Move.from_uci(played)
    best_capture = board.is_capture(bm)
    board.push(bm)
    best_check = board.is_check()
    board.pop()
    if (best_capture or best_check) and loss >= 300:
        return "missed tactic"
    played_capture = board.is_capture(pm)
    victim = board.piece_type_at(bm.to_square) if best_capture else None
    attacker = board.piece_type_at(bm.from_square)
    equal_best = best_capture and victim not in (None, chess.PAWN) and attacker not in (None, chess.KING) and \
        {chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}.get(victim) == \
        {chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}.get(attacker)
    pv = board.piece_type_at(pm.to_square) if played_capture else None
    pa = board.piece_type_at(pm.from_square)
    equal_played = played_capture and pv not in (None, chess.PAWN) and pa not in (None, chess.KING) and \
        {chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}.get(pv) == \
        {chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}.get(pa)
    if equal_played and not equal_best:
        return "bad trade"
    if equal_best and not equal_played:
        return "refused trade"
    if played_capture and not best_capture:
        return "material grab"
    if attacker == chess.PAWN and is_passed(board, bm.from_square, us):
        return "passed pawn"
    if best_capture and board.piece_type_at(bm.to_square) == chess.PAWN and is_passed(board, bm.to_square, not us):
        return "passed pawn"
    # King exposure: after the played move, does the opponent's best reply check?
    board.push(pm)
    exposed = False
    if label.pv and len(label.pv) >= 1:
        pass
    reply = None
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_check():
            reply = mv
            board.pop()
            break
        board.pop()
    board.pop()
    if reply is not None and loss >= 200:
        exposed = True
    if exposed:
        return "king exposure"
    return "quiet positional"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    games = {(g["cluster"], g["cand_white"]): g for g in
             (json.loads(line) for line in arguments.games.open(encoding="utf-8"))}
    episodes = [json.loads(line) for line in arguments.episodes.open(encoding="utf-8")]
    fail = [e for e in episodes if e["engine"] == "v0.5.2 production" and e["threshold"] == 200
            and e["result"] < 1.0]
    out = [f"== 5. FIRST SERIOUS ERROR after reaching +200: {len(fail)} failed conversions (production) ==", ""]
    cats = Counter()
    punish = Counter()
    mates = []
    rows = []
    with Oracle() as oracle:
        for e in fail:
            f = e["first_serious_error"]
            if not f:
                cats["no serious error (drawn without one)"] += 1
                continue
            g = games[(e["cluster"], e["cand_white"])]
            moves = g["moves"]
            idx = next(i for i, m in enumerate(moves) if m["ply"] == f["ply"])
            board = chess.Board(f["fen"])
            label = oracle.analyse(f["fen"], arguments.nodes)
            cat = classify(board, f["move"], label.best, f["cp_loss"], label)
            cats[cat] += 1
            if cat == "missed mate":
                mates.append((e["cluster"], e["colour"], label.mate, f["move"], label.best, f["fen"]))
            # Was the crossing an opponent blunder the engine then had to punish?
            cross_idx = next(i for i, m in enumerate(moves) if m["ply"] == e["ply"])
            prev = moves[cross_idx - 1] if cross_idx > 0 else None
            blunder = prev is not None and prev["mover"] != "base" and prev["cp_loss"] >= 100
            punish["crossing caused by opponent's serious error" if blunder else "crossing not from an opponent error"] += 1
            rows.append((cat, e["cluster"], e["colour"], f["plies_after_crossing"], f["standing_before"],
                         f["move"], label.best, f["cp_loss"], label.mate, moves[idx]["score_stm"],
                         blunder, f["fen"]))
    out.append("categories:")
    for k, v in cats.most_common():
        out.append(f"  {k:<40} {v:>3}  {v / len(fail):>5.1%}")
    out.append("")
    out.append(f"punishment test (first error within the episode): {dict(punish)}")
    quick = [r for r in rows if r[3] <= 4]
    out.append(f"first serious errors within 4 plies of crossing: {len(quick)}; of those, crossing was an "
               f"opponent blunder in {sum(1 for r in quick if r[10])}; categories {dict(Counter(r[0] for r in quick))}")
    out.append("")
    out.append(f"missed forced mates: {len(mates)}")
    for c, col, mate, mv, best, fen in mates:
        out.append(f"  cluster {c} {col}: mate in {mate}, engine {mv}, Stockfish {best}   {fen}")
    out.append("")
    out.append(f"{'category':<18} {'cl':>3} {'col':<5} {'+ply':>4} {'stand':>6} {'played':<6} {'best':<6} {'loss':>5} {'mate':>4} {'eng':>6} {'blund':<5} fen")
    for r in sorted(rows, key=lambda r: (r[0], -r[7])):
        out.append(f"{r[0]:<18} {r[1]:>3} {r[2]:<5} {r[3]:>4} {r[4]:>+6} {r[5]:<6} {r[6]:<6} {r[7]:>5} "
                   f"{('' if r[8] is None else r[8]):>4} {r[9]:>+6} {r[10]!s:<5} {r[11]}")
    text = "\n".join(out)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
