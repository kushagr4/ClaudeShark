"""Simplification, material/compensation calibration and phase timing.

Three questions the conversion audit asks of the retained games, answered
from the per-move annotation alone (no new searches):

* does the engine mishandle simplification while ahead -- declining equal
  trades Stockfish prefers, or trading into bad endgames?
* how does the production static evaluation, and its search score, compare
  with Stockfish across material imbalances, and in positions where one side
  has compensation?
* does a failed conversion's first serious error begin in the endgame, or does
  the advantage merely *arise* there because the corpus starts are late?

    uv run python -m tools.conversion.calibration --games <annotated.jsonl> \
        --episodes <episodes.jsonl> --out <txt>
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import chess

VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def own(m: dict) -> int:
    return m["sf_cp_white_before"] if m["turn"] == "w" else -m["sf_cp_white_before"]


def own_static(m: dict) -> int:
    return m["base_static"] if m["turn"] == "w" else -m["base_static"]


def trade_kind(board: chess.Board, uci: str | None) -> str | None:
    """An equal exchange of non-pawn pieces, or None."""
    if not uci:
        return None
    mv = chess.Move.from_uci(uci)
    if not board.is_capture(mv) or board.is_en_passant(mv):
        return None
    victim = board.piece_type_at(mv.to_square)
    attacker = board.piece_type_at(mv.from_square)
    if victim is None or victim == chess.PAWN or attacker in (None, chess.KING):
        return None
    if VALUES[victim] != VALUES[attacker]:
        return None
    return {chess.QUEEN: "queen trade", chess.ROOK: "rook trade"}.get(victim, "minor trade")


def imbalance(board: chess.Board, white: bool) -> str:
    def c(p, col):
        return len(board.pieces(p, col))
    us, them = white, not white
    dq = c(chess.QUEEN, us) - c(chess.QUEEN, them)
    dr = c(chess.ROOK, us) - c(chess.ROOK, them)
    dm = (c(chess.KNIGHT, us) + c(chess.BISHOP, us)) - (c(chess.KNIGHT, them) + c(chess.BISHOP, them))
    dp = c(chess.PAWN, us) - c(chess.PAWN, them)
    if dq:
        return "queen imbalance"
    if dr > 0 and dm < 0:
        return "exchange up"
    if dr < 0 and dm > 0:
        return "exchange down"
    if dr > 0 and dm == 0:
        return "rook up"
    if dr < 0 and dm == 0:
        return "rook down"
    if dm > 0 and dr == 0:
        return "piece up"
    if dm < 0 and dr == 0:
        return "piece down"
    if dr == 0 and dm == 0:
        return ("+2 pawns" if dp >= 2 else "+1 pawn" if dp == 1 else "level" if dp == 0
                else "-1 pawn" if dp == -1 else "-2 pawns")
    return "mixed"


def material(board: chess.Board, white: bool) -> int:
    return sum(v * (len(board.pieces(p, white)) - len(board.pieces(p, not white)))
               for p, v in VALUES.items())


def simplification(games: list[dict], out: list[str]) -> None:
    out.append("== 8. SIMPLIFICATION AUDIT (production; equal non-pawn exchanges) ==")
    ahead = [m for g in games for m in g["moves"] if m["mover"] == "base" and 200 <= own(m) < 9000]
    level = [m for g in games for m in g["moves"] if m["mover"] == "base" and abs(own(m)) < 100]
    for label, ms in (("AHEAD >= +200", ahead), ("LEVEL |eval| < 100 (control)", level)):
        sf_trade = took = eng_trade = eng_not_best = 0
        declined: list[int] = []
        traded: list[int] = []
        kinds = Counter()
        for m in ms:
            b = chess.Board(m["fen"])
            bt = trade_kind(b, m.get("sf_best"))
            et = trade_kind(b, m["move"])
            if bt:
                sf_trade += 1
                kinds[bt] += 1
                if m["move"] == m["sf_best"]:
                    took += 1
                else:
                    declined.append(m["cp_loss"])
            if et:
                eng_trade += 1
                traded.append(m["cp_loss"])
                if not bt:
                    eng_not_best += 1
        n = len(ms)
        out.append(f"-- {label}: n={n}")
        out.append(f"   Stockfish's best is an equal trade in {sf_trade} ({sf_trade / n:.1%}) {dict(kinds)}; "
                   f"engine played it {took}/{sf_trade} ({took / max(1, sf_trade):.0%}); when it declined, "
                   f"mean loss {statistics.mean(declined) if declined else 0:.0f} cp, serious {sum(v >= 100 for v in declined)}")
        out.append(f"   engine traded in {eng_trade} ({eng_trade / n:.1%}); mean loss of those trades "
                   f"{statistics.mean(traded) if traded else 0:.0f} cp, serious {sum(v >= 100 for v in traded)}; "
                   f"trades Stockfish did not prefer {eng_not_best}")
    into_pawn = []
    for m in ahead:
        b = chess.Board(m["fen"])
        if trade_kind(b, m["move"]) and sum(
                1 for pc in b.piece_map().values() if pc.piece_type not in (chess.PAWN, chess.KING)) <= 2:
            into_pawn.append(m["cp_loss"])
    out.append(f"-- trades into a pawn ending while ahead: {len(into_pawn)}, mean loss "
               f"{statistics.mean(into_pawn) if into_pawn else 0:.0f} cp")
    out.append("")


def calibration(games: list[dict], out: list[str]) -> None:
    out.append("== 9/10. MATERIAL / COMPENSATION CALIBRATION (production is the mover) ==")
    acc: dict[str, list] = defaultdict(list)
    per_unit: dict[int, list] = defaultdict(list)
    up_comp, down_comp = [], []
    for g in games:
        for m in g["moves"]:
            if m["mover"] != "base" or abs(m["sf_cp_white_before"]) >= 9000:
                continue
            b = chess.Board(m["fen"])
            white = b.turn
            row = (own(m), own_static(m), m["score_stm"], m["cp_loss"])
            acc[imbalance(b, white)].append(row)
            mat = material(b, white)
            if 1 <= mat <= 6:
                per_unit[mat].append(row)
            if mat >= 2 and row[0] <= 0:
                up_comp.append(row)
            if mat <= -2 and row[0] >= 0:
                down_comp.append(row)
    out.append(f"{'imbalance (mover)':<18} {'n':>5} {'SF':>6} {'static':>7} {'search':>7} "
               f"{'static-SF':>10} {'search-SF':>10} {'|static-SF|':>12} {'serious%':>9}")
    for k in ("-2 pawns", "-1 pawn", "level", "+1 pawn", "+2 pawns", "exchange down", "exchange up",
              "piece down", "piece up", "rook down", "rook up", "queen imbalance", "mixed"):
        r = acc.get(k, [])
        if len(r) < 15:
            continue
        sf = statistics.mean(x[0] for x in r)
        st = statistics.mean(x[1] for x in r)
        sr = statistics.mean(x[2] for x in r)
        out.append(f"{k:<18} {len(r):>5} {sf:>+6.0f} {st:>+7.0f} {sr:>+7.0f} {st - sf:>+10.0f} {sr - sf:>+10.0f} "
                   f"{statistics.mean(abs(x[1] - x[0]) for x in r):>12.0f} "
                   f"{sum(x[3] >= 100 for x in r) / len(r):>9.1%}")
    out.append("")
    out.append("compensation positions:")
    for label, r in (("up >= 2 units, Stockfish says not better", up_comp),
                     ("down >= 2 units, Stockfish says not worse", down_comp)):
        if r:
            out.append(f"  {label}: n={len(r)}  SF {statistics.mean(x[0] for x in r):+.0f}  "
                       f"static {statistics.mean(x[1] for x in r):+.0f}  search {statistics.mean(x[2] for x in r):+.0f}  "
                       f"serious-error rate {sum(x[3] >= 100 for x in r) / len(r):.1%}")
    out.append("")
    out.append("per unit of material advantage (mover ahead by k pawn-units):")
    out.append(f"{'k':>4} {'n':>5} {'SF/unit':>8} {'static/unit':>12} {'search/unit':>12}   {'SF':>6} {'static':>7} {'search':>7}")
    for k in sorted(per_unit):
        r = per_unit[k]
        if len(r) < 20:
            continue
        out.append(f"{k:>+4} {len(r):>5} {statistics.mean(x[0] / k for x in r):>+8.0f} "
                   f"{statistics.mean(x[1] / k for x in r):>+12.0f} {statistics.mean(x[2] / k for x in r):>+12.0f}   "
                   f"{statistics.mean(x[0] for x in r):>+6.0f} {statistics.mean(x[1] for x in r):>+7.0f} "
                   f"{statistics.mean(x[2] for x in r):>+7.0f}")
    out.append("")


def phase_timing(episodes: list[dict], out: list[str]) -> None:
    out.append("== 11. ENDGAME: CAUSE OR VENUE? (production, +200 episodes) ==")
    prod = [e for e in episodes if e["engine"] == "v0.5.2 production" and e["threshold"] == 200]
    fail = [e for e in prod if e["result"] < 1.0]
    ok = [e for e in prod if e["result"] == 1.0]
    tr = Counter()
    for e in fail:
        f = e["first_serious_error"]
        tr["no serious error" if not f else f"{e['phase']} -> {f['phase']}"] += 1
    out.append(f"phase at crossing -> phase of first serious error (failed): {dict(tr)}")
    out.append(f"crossing phase: failed {dict(Counter(e['phase'] for e in fail))}, converted {dict(Counter(e['phase'] for e in ok))}")
    out.append(f"pieces at crossing: failed mean {statistics.mean(e['pieces'] for e in fail):.1f}, "
               f"converted mean {statistics.mean(e['pieces'] for e in ok):.1f}")
    for lo, hi, lab in ((0, 8, "<= 8"), (9, 14, "9-14"), (15, 32, ">= 15")):
        w = sum(1 for e in ok if lo <= e["pieces"] <= hi)
        n = sum(1 for e in prod if lo <= e["pieces"] <= hi)
        out.append(f"   conversion with {lab} pieces on the board at crossing: {w}/{n}")
    out.append(f"failed conversions already in the endgame at the crossing: "
               f"{sum(1 for e in fail if e['phase'] == 'endgame')}/{len(fail)}")
    out.append("")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    episodes = [json.loads(line) for line in arguments.episodes.open(encoding="utf-8")]
    out: list[str] = []
    simplification(games, out)
    calibration(games, out)
    phase_timing(episodes, out)
    text = "\n".join(out)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
