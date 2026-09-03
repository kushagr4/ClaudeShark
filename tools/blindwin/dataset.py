"""Blind-win episodes: positions Stockfish calls won that the root search cannot see.

From retained annotated self-play games, every position on the production
engine's turn where Stockfish's standing is at least ``--sf`` and the engine's
own root score is under ``--root``. Consecutive blind plies in one game are one
*episode*; the record is its first ply. For each episode the oracle is asked
again at a fixed node budget for the principal variation and mate distance, and
the PV is then walked to its end (or ``--walk`` plies) with production's static
evaluation recorded there. That last number is the discriminator:

* static at the PV end already sees the win  -> the search only lacked depth
* static at the PV end is still blind        -> the evaluation cannot recognise
                                                the winning structure at all

The PV also classifies the mechanism: a mate in the line, a promotion, a
material gain, or a quiet line, and the engine's actual move is scored so
"failed to punish" cases (loss >= 100) are separable from "played fine but
did not know it".

    uv run python -m tools.blindwin.dataset --games A.jsonl B.jsonl --out corpus/blindwin
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import chess

import cs_eval
from tools.corpus.oracle import Oracle
from tools.corpus.structure import analyse_structure

VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def own(m: dict) -> int:
    return m["sf_cp_white_before"] if m["turn"] == "w" else -m["sf_cp_white_before"]


def own_static(m: dict) -> int:
    return m["base_static"] if m["turn"] == "w" else -m["base_static"]


def static_stm(board: chess.Board) -> int:
    """Production static from the side to move, tempo removed."""
    return cs_eval.evaluate(board) - cs_eval.TEMPO


def material(board: chess.Board, white: bool) -> int:
    return sum(v * (len(board.pieces(p, white)) - len(board.pieces(p, not white))) for p, v in VALUES.items())


def passers(board: chess.Board, colour: bool) -> list[int]:
    out = []
    for sq in board.pieces(chess.PAWN, colour):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        ahead = range(r + 1, 8) if colour else range(r - 1, -1, -1)
        if not any(board.piece_at(chess.square(ff, rr)) == chess.Piece(chess.PAWN, not colour)
                   for rr in ahead for ff in (f - 1, f, f + 1) if 0 <= ff < 8):
            out.append(sq)
    return out


def mechanism(board: chess.Board, pv: list[str], mate: int | None) -> tuple[str, dict]:
    """What the winning line does, read off the PV."""
    b = board.copy()
    us = b.turn
    start_mat = material(b, us)
    promo = 0
    checks = 0
    king_moves = rook_moves = pawn_moves = 0
    for uci in pv:
        mv = chess.Move.from_uci(uci)
        if mv not in b.legal_moves:
            break
        mover_is_us = b.turn == us
        if mv.promotion:
            promo += 1 if mover_is_us else 0
        piece = b.piece_type_at(mv.from_square)
        if mover_is_us:
            king_moves += piece == chess.KING
            rook_moves += piece == chess.ROOK
            pawn_moves += piece == chess.PAWN
        b.push(mv)
        if mover_is_us and b.is_check():
            checks += 1
    end_mat = material(b, us)
    gain = material(b, us) - start_mat
    info = {"pv_len": len(pv), "promotions": promo, "material_gain": gain, "checks": checks,
            "king_moves": king_moves, "rook_moves": rook_moves, "pawn_moves": pawn_moves,
            "end_fen": b.fen(), "end_material": end_mat}
    if mate is not None and mate > 0:
        return "mating net", info
    if promo:
        return "promotion race", info
    if gain >= 3:
        return "wins a piece", info
    if gain >= 1:
        return "wins pawn(s)", info
    if king_moves >= max(2, len(pv) // 3):
        return "king activity", info
    if rook_moves >= max(2, len(pv) // 3):
        return "rook activity", info
    return "quiet / unresolved", info


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, nargs="+", required=True)
    parser.add_argument("--sf", type=int, default=300)
    parser.add_argument("--root", type=int, default=100)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--walk", type=int, default=10)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.out.mkdir(parents=True, exist_ok=True)
    assert cs_eval.USE_MOP_UP is False, "production static must be measured with the flag off"

    episodes = []
    for path in arguments.games:
        for g in (json.loads(line) for line in path.open(encoding="utf-8")):
            in_run = False
            prev = None
            for m in g["moves"]:
                if m["mover"] != "base":
                    prev = m
                    continue
                blind = arguments.sf <= own(m) < 9000 and m["score_stm"] < arguments.root
                if blind and not in_run:
                    episodes.append({"source": path.name, "cluster": g["cluster"], "cand_white": g["cand_white"],
                                     "ply": m["ply"], "fen": m["fen"], "sf_cp": own(m), "root": m["score_stm"],
                                     "static": own_static(m), "move": m["move"], "cp_loss": m["cp_loss"],
                                     "sf_best_annot": m.get("sf_best"),
                                     "after_opponent_blunder": bool(prev and prev["mover"] != "base" and prev["cp_loss"] >= 100),
                                     "result": 1.0 - g["cand_score"], "termination": g["termination"]})
                in_run = blind
                prev = m
    print(f"{len(episodes)} blind episodes (Stockfish >= +{arguments.sf}, root < +{arguments.root})", flush=True)

    with Oracle() as oracle:
        for i, e in enumerate(episodes, start=1):
            board = chess.Board(e["fen"])
            label = oracle.analyse(e["fen"], arguments.nodes)
            e["sf_cp_1m"] = label.cp_stm
            e["sf_wdl"] = list(label.wdl_stm) if label.wdl_stm else None
            e["sf_mate"] = label.mate
            e["sf_best"] = label.best
            e["pv"] = label.pv[: arguments.walk]
            kind, info = mechanism(board, e["pv"], label.mate)
            e["mechanism"] = kind
            e.update(info)
            # Walk the PV; production static at its end, from the mover's side.
            b = board.copy()
            for uci in e["pv"]:
                mv = chess.Move.from_uci(uci)
                if mv not in b.legal_moves:
                    break
                b.push(mv)
            end_static = static_stm(b)
            e["static_at_pv_end"] = end_static if b.turn == board.turn else -end_static
            e["horizon_or_blind"] = "horizon (static sees it at the PV end)" if e["static_at_pv_end"] >= arguments.sf else \
                "partly (static at PV end 100..299)" if e["static_at_pv_end"] >= 100 else "blind (static still under +100 at the PV end)"
            st = analyse_structure(board)
            e["phase"] = st.phase
            e["tags"] = list(st.tags)
            e["material"] = material(board, board.turn)
            e["pieces"] = len(board.piece_map())
            e["our_passers"] = len(passers(board, board.turn))
            e["their_passers"] = len(passers(board, not board.turn))
            if i % 25 == 0:
                print(f"  {i}/{len(episodes)}", flush=True)

    with (arguments.out / "episodes.jsonl").open("w", encoding="utf-8") as fh:
        for e in episodes:
            fh.write(json.dumps(e) + "\n")

    lines = [f"== BLIND-WIN EPISODES: {len(episodes)} (Stockfish >= +{arguments.sf} for production, root < +{arguments.root}; first ply of each run) ==", ""]
    lines.append(f"after an opponent blunder on the previous ply: {sum(e['after_opponent_blunder'] for e in episodes)}/{len(episodes)}")
    lines.append(f"engine's move at the episode start loses >= 100 cp: {sum(e['cp_loss'] >= 100 for e in episodes)}/{len(episodes)}; >= 300: {sum(e['cp_loss'] >= 300 for e in episodes)}")
    lines.append(f"eventual result from these games: won {sum(e['result'] == 1.0 for e in episodes)}, drawn {sum(e['result'] == 0.5 for e in episodes)}, lost {sum(e['result'] == 0.0 for e in episodes)}")
    lines.append("")
    lines.append("== HORIZON OR BLIND: production static at the end of Stockfish's PV ==")
    for k, v in Counter(e["horizon_or_blind"] for e in episodes).most_common():
        lines.append(f"  {k:<50} {v:>4}  {v / len(episodes):.0%}")
    lines.append(f"  mean static at the episode: {statistics.mean(e['static'] for e in episodes):+.0f}; at the PV end: {statistics.mean(e['static_at_pv_end'] for e in episodes):+.0f}; Stockfish {statistics.mean(min(e['sf_cp_1m'], 2000) for e in episodes):+.0f}")
    lines.append("")
    lines.append("== MECHANISM (from the PV) ==")
    mech = Counter(e["mechanism"] for e in episodes)
    for k, v in mech.most_common():
        sub = [e for e in episodes if e["mechanism"] == k]
        hb = Counter(e["horizon_or_blind"].split(" ")[0] for e in sub)
        lines.append(f"  {k:<22} {v:>4}  {v / len(episodes):.0%}   horizon {hb['horizon']:>3} / partly {hb['partly']:>3} / blind {hb['blind']:>3}   "
                     f"failed-to-punish {sum(e['cp_loss'] >= 100 for e in sub)}   mean SF {statistics.mean(min(e['sf_cp_1m'], 2000) for e in sub):+.0f}")
    lines.append("")
    lines.append("== PHASE / MATERIAL / STRUCTURE ==")
    lines.append(f"  phase: {dict(Counter(e['phase'] for e in episodes))}")
    lines.append(f"  material from production's side: {dict(sorted(Counter(max(-4, min(4, e['material'])) for e in episodes).items()))}")
    lines.append(f"  own passers present: {sum(e['our_passers'] > 0 for e in episodes)}; their passers: {sum(e['their_passers'] > 0 for e in episodes)}")
    tags = Counter(t for e in episodes for t in e["tags"])
    lines.append("  tags (share of episodes): " + ", ".join(f"{t} {c / len(episodes):.0%}" for t, c in tags.most_common(14)))
    byphase = defaultdict(Counter)
    for e in episodes:
        byphase[e["phase"]][e["mechanism"]] += 1
    for ph, c in byphase.items():
        lines.append(f"  {ph}: {dict(c)}")
    text = "\n".join(lines)
    (arguments.out / "01_dataset.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
