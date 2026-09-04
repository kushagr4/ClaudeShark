"""How well does the engine's own score agree with the oracle, across every phase?

The V2 calibration set answered this for endgames and found two failure
directions -- blind wins, where Stockfish is winning and the engine is level,
and false wins, where the engine is winning and Stockfish is level. The rated
games showed a third that the endgame set could not see, because it only
sampled endgames and only sampled the two extreme classes: in a middlegame the
engine can be several hundred centipawns worse and read its own position as
roughly equal.

This module measures agreement without selecting positions at all. Every ply of
every retained annotated game is used, scored from the **mover's** point of
view, so the sample is not conditioned on the engine having erred, on the phase,
or on the class. Both the static evaluation and the depth-6 root score are
compared with the oracle, because they fail differently: the static score is the
evaluator alone, and the root score also contains whatever the search found and
the upward bias of maximising over noisy leaves.

Four classes are counted, all from the mover's point of view:

    blind win     oracle >= +300 and the engine's root < +100
    false win     |oracle| <= 60 and the engine's root >= +150
    blind loss    oracle <= -300 and the engine's root > -100
    false loss    |oracle| <= 60 and the engine's root <= -150

    uv run python -m tools.daily.calibrate --out corpus/daily/calibration_all_phases.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

import chess

from cs_constants import TOTAL_PHASE

CORPORA = {
    "postmortem (rated-v1 vs v0.8, 200 games)": ("corpus/postmortem/games/annotated.jsonl", "cand_static", "base_static"),
    "king-pawn Gate 2 (V2.1 vs rated-v1, 200 games)": ("corpus/v2/kp/games/gate2_annotated.jsonl", "cand_static", "base_static"),
    "passed-pawn Gate 2 (200 games)": ("corpus/passed/games/gate2_annotated.jsonl", "cand_static", "base_static"),
    "mop-up Gate 2 (200 games)": ("corpus/mopup/games/gate2_annotated.jsonl", "cand_static", "base_static"),
}

PHASE_WEIGHT = {chess.KNIGHT: 1, chess.BISHOP: 1, chess.ROOK: 2, chess.QUEEN: 4}


def phase_of(board: chess.Board) -> int:
    total = 0
    for piece_type, weight in PHASE_WEIGHT.items():
        total += weight * len(board.pieces(piece_type, chess.WHITE))
        total += weight * len(board.pieces(piece_type, chess.BLACK))
    return min(TOTAL_PHASE, total)


def bucket(phase: int) -> str:
    if phase >= 18:
        return "opening   (phase 18-24)"
    if phase >= 10:
        return "middlegame (phase 10-17)"
    if phase >= 4:
        return "late      (phase 4-9)"
    return "endgame   (phase 0-3)"


def band(cp: int) -> str:
    a = abs(cp)
    if a <= 60:
        return "|SF| <= 60      "
    if a <= 150:
        return "|SF| 61-150     "
    if a <= 300:
        return "|SF| 151-300    "
    if a <= 600:
        return "|SF| 301-600    "
    return "|SF| > 600      "


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--clamp", type=int, default=2000, help="drop rows whose oracle score exceeds this (mates)")
    arguments = parser.parse_args()
    rows = []
    for label, (path, cand_field, base_field) in CORPORA.items():
        p = Path(path)
        if not p.exists():
            print(f"missing {path}")
            continue
        for line in p.open(encoding="utf-8"):
            g = json.loads(line)
            for m in g["moves"]:
                sf_white = m.get("sf_cp_white_before")
                if sf_white is None or abs(sf_white) > arguments.clamp:
                    continue
                board = chess.Board(m["fen"])
                white = board.turn == chess.WHITE
                field = cand_field if m["mover"] == "cand" else base_field
                static_white = m.get(field)
                if static_white is None:
                    continue
                rows.append({
                    "corpus": label, "phase": phase_of(board),
                    "sf": sf_white if white else -sf_white,
                    "static": static_white if white else -static_white,
                    "root": m["score_stm"],
                })
    print(f"{len(rows)} positions", flush=True)

    lines = [f"== ENGINE-VERSUS-ORACLE CALIBRATION, ALL PHASES: {len(rows)} positions from {len(CORPORA)} annotated corpora ==",
             "Every ply of every game, scored from the mover's point of view. No position is selected on having been an error.", ""]

    def block(title: str, groups: dict[str, list[dict]]) -> None:
        lines.append(title)
        lines.append(f"   {'group':<24} {'n':>6} {'mean SF':>8} {'mean static':>12} {'bias':>7} {'mean root':>10} {'bias':>7} {'root-SF |err|':>13}")
        for key in sorted(groups):
            rs = groups[key]
            if not rs:
                continue
            sf = statistics.mean(r["sf"] for r in rs)
            st = statistics.mean(r["static"] for r in rs)
            rt = statistics.mean(r["root"] for r in rs)
            err = statistics.mean(abs(r["root"] - r["sf"]) for r in rs)
            lines.append(f"   {key:<24} {len(rs):>6} {sf:>+8.0f} {st:>+12.0f} {st - sf:>+7.0f} {rt:>+10.0f} {rt - sf:>+7.0f} {err:>13.0f}")
        lines.append("")

    by_phase = defaultdict(list)
    for r in rows:
        by_phase[bucket(r["phase"])].append(r)
    block("== BY PHASE ==", by_phase)

    by_band = defaultdict(list)
    for r in rows:
        by_band[band(r["sf"])].append(r)
    block("== BY ORACLE BAND (mover's view; the sign of the bias is what matters) ==", by_band)

    by_signed = defaultdict(list)
    for r in rows:
        s = r["sf"]
        key = ("mover winning  " if s >= 300 else "mover better   " if s >= 100 else
               "level          " if s > -100 else "mover worse    " if s > -300 else "mover losing   ")
        by_signed[key].append(r)
    block("== BY SIGNED ORACLE CLASS ==", by_signed)

    lines.append("== THE FOUR MISREADINGS, from the mover's point of view ==")
    classes = {
        "blind win   (SF >= +300, root <  +100)": [r for r in rows if r["sf"] >= 300 and r["root"] < 100],
        "false win   (|SF| <=  60, root >= +150)": [r for r in rows if abs(r["sf"]) <= 60 and r["root"] >= 150],
        "blind loss  (SF <= -300, root >  -100)": [r for r in rows if r["sf"] <= -300 and r["root"] > -100],
        "false loss  (|SF| <=  60, root <= -150)": [r for r in rows if abs(r["sf"]) <= 60 and r["root"] <= -150],
    }
    denom = {
        "blind win   (SF >= +300, root <  +100)": [r for r in rows if r["sf"] >= 300],
        "false win   (|SF| <=  60, root >= +150)": [r for r in rows if abs(r["sf"]) <= 60],
        "blind loss  (SF <= -300, root >  -100)": [r for r in rows if r["sf"] <= -300],
        "false loss  (|SF| <=  60, root <= -150)": [r for r in rows if abs(r["sf"]) <= 60],
    }
    for key, rs in classes.items():
        d = denom[key]
        lines.append(f"   {key:<40} {len(rs):>6} of {len(d):>6} eligible ({len(rs) / max(1, len(d)):6.1%})")
        if rs:
            by = defaultdict(int)
            for r in rs:
                by[bucket(r["phase"])] += 1
            lines.append(f"      by phase: {dict(sorted(by.items()))}")
    lines.append("")
    lines.append("== SYMMETRY OF THE TWO DIRECTIONS ==")
    win_side = [r for r in rows if r["sf"] >= 300]
    lose_side = [r for r in rows if r["sf"] <= -300]
    lines.append(f"   when the mover is winning (SF >= +300, n={len(win_side)}): mean root {statistics.mean(r['root'] for r in win_side):+.0f} against mean SF {statistics.mean(r['sf'] for r in win_side):+.0f}")
    lines.append(f"   when the mover is losing  (SF <= -300, n={len(lose_side)}): mean root {statistics.mean(r['root'] for r in lose_side):+.0f} against mean SF {statistics.mean(r['sf'] for r in lose_side):+.0f}")
    lines.append("   If the engine simply compressed every score toward zero these two rows would be mirror images.")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
