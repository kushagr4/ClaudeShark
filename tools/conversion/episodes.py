"""Advantage episodes: what happens after an engine reaches a winning score.

Built from retained fixed-depth self-play games with full move histories and
per-move Stockfish annotation. An *episode* is one (game, side, threshold):
the first ply at which that side's Stockfish standing reaches the threshold,
followed to the end of the game. Counting the first crossing only is what
keeps hundreds of adjacent positions from being mistaken for hundreds of
independent observations; game-level statistics are reported alongside.

For every episode the record carries the position, its Stockfish score and
WDL, material balance, phase, pieces remaining, structural tags, the eventual
result, the peak advantage, the standing 5/10/20 plies later, the first serious
error that side made after crossing, whether the advantage was recovered
afterwards, and -- for failed conversions -- the exact move producing the
largest early deterioration with the score trajectory around it.

Thresholds are applied to the engine's own standing, so the same machinery
yields defensive episodes at the negative thresholds.

    uv run python -m tools.conversion.episodes --games <annotated.jsonl> --out <dir>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import chess

from tools.corpus.structure import analyse_structure

THRESHOLDS = (100, 200, 300, 500)
SERIOUS = 100
VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def standing(move: dict, side_is_white: bool) -> int:
    cp = move["sf_cp_white_before"]
    return cp if side_is_white else -cp


def material(board: chess.Board, white: bool) -> int:
    us = sum(v * len(board.pieces(p, white)) for p, v in VALUES.items())
    them = sum(v * len(board.pieces(p, not white)) for p, v in VALUES.items())
    return us - them


def imbalance_kind(board: chess.Board, white: bool) -> str:
    """Coarse description of the material situation from `white`'s side."""
    def count(p, colour):
        return len(board.pieces(p, colour))
    us, them = white, not white
    dq = count(chess.QUEEN, us) - count(chess.QUEEN, them)
    dr = count(chess.ROOK, us) - count(chess.ROOK, them)
    dm = (count(chess.KNIGHT, us) + count(chess.BISHOP, us)) - (
        count(chess.KNIGHT, them) + count(chess.BISHOP, them))
    dp = count(chess.PAWN, us) - count(chess.PAWN, them)
    total = material(board, white)
    if dq != 0:
        return "queen imbalance"
    if dr > 0 and dm < 0:
        return "exchange up"
    if dr < 0 and dm > 0:
        return "exchange down"
    if dr > 0 and dm == 0:
        return "rook up"
    if dm > 0 and dr == 0:
        return "piece up"
    if dr == 0 and dm == 0:
        if dp >= 2:
            return "+2 pawns or more"
        if dp == 1:
            return "+1 pawn"
        if dp == 0:
            return "level material"
        return "pawns down"
    return f"mixed ({total:+d})"


def episode(game: dict, side: str, thr: int, cache: dict) -> dict | None:
    side_is_white = game["cand_white"] == (side == "cand")
    moves = game["moves"]
    cross = next((i for i, m in enumerate(moves)
                  if abs(m["sf_cp_white_before"]) < 9000
                  and (standing(m, side_is_white) >= thr if thr > 0
                       else standing(m, side_is_white) <= thr)), None)
    if cross is None:
        return None
    m0 = moves[cross]
    board = chess.Board(m0["fen"])
    st = cache.setdefault(m0["fen"], analyse_structure(board))
    result = game["cand_score"] if side == "cand" else 1.0 - game["cand_score"]
    later = [standing(m, side_is_white) for m in moves[cross:]]

    def at(k: int) -> int | None:
        return later[k] if k < len(later) else None

    own_after = [(i, m) for i, m in enumerate(moves) if i >= cross and m["mover"] == side]
    first_err = next(((i, m) for i, m in own_after if m["cp_loss"] >= SERIOUS), None)
    recovered = False
    if first_err is not None:
        after_err = [standing(m, side_is_white) for m in moves[first_err[0] + 1:]]
        recovered = any((v >= thr) if thr > 0 else (v <= thr) for v in after_err)

    # Largest early deterioration by this side after crossing, with trajectory.
    collapse = None
    if own_after:
        worst = max(own_after, key=lambda im: im[1]["cp_loss"])
        i, m = worst
        traj = [standing(x, side_is_white) for x in moves[max(cross, i - 4):i + 1]]
        after = standing(moves[i + 1], side_is_white) if i + 1 < len(moves) else None
        collapse = {
            "ply": m["ply"], "fen": m["fen"], "move": m["move"], "cp_loss": m["cp_loss"],
            "sf_best": m["sf_best"], "standing_before": standing(m, side_is_white),
            "standing_after": after, "trajectory_before": traj,
            "engine_score_stm": m["score_stm"], "static_own": (
                m["cand_static"] if side == "cand" else m["base_static"]),
            "plies_after_crossing": i - cross,
        }
    peak = max(later) if thr > 0 else min(later)
    return {
        "cluster": game["cluster"], "cand_white": game["cand_white"], "side": side,
        "engine": "v0.6 scale" if side == "cand" else "v0.5.2 production",
        "colour": "white" if side_is_white else "black", "threshold": thr,
        "ply": m0["ply"], "fen": m0["fen"], "sf_cp": standing(m0, side_is_white),
        "sf_wdl_white": m0.get("sf_wdl_white_before"),
        "material": material(board, side_is_white),
        "imbalance": imbalance_kind(board, side_is_white),
        "phase": st.phase, "phase24": st.phase24, "pieces": len(board.piece_map()),
        "tags": list(st.tags), "result": result, "peak": peak,
        "after_5": at(5), "after_10": at(10), "after_20": at(20),
        "plies_remaining": len(later), "termination": game["termination"],
        "first_serious_error": None if first_err is None else {
            "ply": first_err[1]["ply"], "plies_after_crossing": first_err[0] - cross,
            "move": first_err[1]["move"], "cp_loss": first_err[1]["cp_loss"],
            "sf_best": first_err[1]["sf_best"], "fen": first_err[1]["fen"],
            "standing_before": standing(first_err[1], side_is_white),
            "phase": cache.setdefault(first_err[1]["fen"],
                                      analyse_structure(chess.Board(first_err[1]["fen"]))).phase,
        },
        "recovered_after_error": recovered,
        "collapse": collapse,
    }


def pct(a: float, b: float) -> str:
    return f"{a / b:.1%}" if b else "  n/a"


def main() -> None:
    parser = argparse.ArgumentParser(description="Advantage episodes from annotated games.")
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.out.mkdir(parents=True, exist_ok=True)

    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    cache: dict = {}
    episodes = []
    for g in games:
        for side in ("base", "cand"):
            for thr in THRESHOLDS:
                for sign in (1, -1):
                    e = episode(g, side, sign * thr, cache)
                    if e is not None:
                        episodes.append(e)
    with (arguments.out / "episodes.jsonl").open("w", encoding="utf-8") as fh:
        for e in episodes:
            fh.write(json.dumps(e) + "\n")

    lines = [f"== CONVERSION DATASET: {len(games)} games, {len(episodes)} episodes "
             f"(one per game x side x threshold x sign; first crossing only) ==", ""]
    by = defaultdict(list)
    for e in episodes:
        by[(e["engine"], e["threshold"])].append(e)

    lines += ["== CONVERSION CURVES (W/D/L after first reaching the threshold; episode = game-level here) ==",
              f"{'engine':<18} {'thr':>5} {'n':>4} {'won':>7} {'drew':>7} {'lost':>7} "
              f"{'1st err<=10':>12} {'recov':>6} {'mean +10':>9} {'mean +20':>9}"]
    for eng in ("v0.5.2 production", "v0.6 scale"):
        for thr in THRESHOLDS:
            es = by[(eng, thr)]
            if not es:
                continue
            n = len(es)
            won = sum(1 for e in es if e["result"] == 1.0)
            drew = sum(1 for e in es if e["result"] == 0.5)
            lost = n - won - drew
            err10 = sum(1 for e in es if e["first_serious_error"]
                        and e["first_serious_error"]["plies_after_crossing"] <= 10)
            rec = sum(1 for e in es if e["recovered_after_error"])
            a10 = [e["after_10"] for e in es if e["after_10"] is not None]
            a20 = [e["after_20"] for e in es if e["after_20"] is not None]
            lines.append(f"{eng:<18} {thr:>+5} {n:>4} {pct(won, n):>7} {pct(drew, n):>7} {pct(lost, n):>7} "
                         f"{pct(err10, n):>12} {pct(rec, n):>6} "
                         f"{(sum(a10) / len(a10) if a10 else 0):>+9.0f} {(sum(a20) / len(a20) if a20 else 0):>+9.0f}")
    lines += ["", "== DEFENCE CURVES (after first reaching the negative threshold) ==",
              f"{'engine':<18} {'thr':>5} {'n':>4} {'held':>7} {'won':>7} {'lost':>7}"]
    for eng in ("v0.5.2 production", "v0.6 scale"):
        for thr in THRESHOLDS:
            es = by[(eng, -thr)]
            if not es:
                continue
            n = len(es)
            won = sum(1 for e in es if e["result"] == 1.0)
            lost = sum(1 for e in es if e["result"] == 0.0)
            lines.append(f"{eng:<18} {-thr:>+5} {n:>4} {pct(n - lost, n):>7} {pct(won, n):>7} {pct(lost, n):>7}")

    # Failed conversions: where the advantage was lost.
    lines += ["", "== FIRST COLLAPSE in failed conversions from +200 (production) =="]
    failed = [e for e in by[("v0.5.2 production", 200)] if e["result"] < 1.0 and e["collapse"]]
    lines.append(f"failed conversions: {len(failed)} of {len(by[('v0.5.2 production', 200)])}")
    ph = Counter(e["first_serious_error"]["phase"] for e in failed if e["first_serious_error"])
    lines.append(f"phase of the FIRST serious error after crossing: {dict(ph)} "
                 f"(no serious error at all: {sum(1 for e in failed if not e['first_serious_error'])})")
    lines.append(f"phase of the episode start: {dict(Counter(e['phase'] for e in failed))}")
    dist = Counter()
    for e in failed:
        d = e["first_serious_error"]["plies_after_crossing"] if e["first_serious_error"] else None
        dist["none" if d is None else "<=4" if d <= 4 else "5-10" if d <= 10 else "11-20" if d <= 20 else ">20"] += 1
    lines.append(f"plies from crossing to the first serious error: {dict(dist)}")
    lines.append(f"{'cl':>4} {'col':<5} {'start':>6} {'peak':>6} {'collapse ply':>12} {'traj (5 plies) -> after':<34} {'move':<6} {'loss':>5} {'SF best':<7} {'engine':>7} {'static':>7} {'res':>4}")
    for e in sorted(failed, key=lambda e: -e["collapse"]["cp_loss"])[:40]:
        c = e["collapse"]
        traj = " ".join(f"{v:+d}" for v in c["trajectory_before"]) + f" -> {c['standing_after']:+d}" if c["standing_after"] is not None else ""
        lines.append(f"{e['cluster']:>4} {e['colour']:<5} {e['sf_cp']:>+6} {e['peak']:>+6} {c['ply']:>12} {traj:<34} {c['move']:<6} {c['cp_loss']:>5} {c['sf_best']:<7} {c['engine_score_stm']:>+7} {c['static_own']:>+7} {e['result']:>4}")

    # Structural and imbalance breakdown of production episodes at +200.
    lines += ["", "== STRUCTURE / IMBALANCE at the +200 crossing (production) =="]
    es = by[("v0.5.2 production", 200)]
    for key in ("imbalance", "phase"):
        cnt = defaultdict(lambda: [0, 0])
        for e in es:
            cnt[e[key]][0] += 1
            cnt[e[key]][1] += e["result"] == 1.0
        lines.append(f"-- by {key}:")
        for k, (n, w) in sorted(cnt.items(), key=lambda kv: -kv[1][0]):
            lines.append(f"   {k:<22} n={n:>3} won {pct(w, n)}")
    tagc = defaultdict(lambda: [0, 0])
    for e in es:
        for t in e["tags"]:
            tagc[t][0] += 1
            tagc[t][1] += e["result"] == 1.0
    lines.append("-- by structural tag (n >= 8), ranked by conversion rate:")
    for t, (n, w) in sorted((kv for kv in tagc.items() if kv[1][0] >= 8), key=lambda kv: kv[1][1] / kv[1][0]):
        lines.append(f"   {t:<26} n={n:>3} won {pct(w, n)}")

    text = "\n".join(lines)
    (arguments.out / "01_dataset_and_curves.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
