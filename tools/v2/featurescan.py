"""Score candidate single features against the V1 residual on the calibration set, diagnostic half only.

Each candidate is one cheap function of the board, from the side to move,
weighted by the endgame share of the phase. Its scale is the least-squares
slope of the residual (clamped Stockfish minus V1 static) on the feature
over the *diagnostic* endgame rows -- one number per feature, nothing else
fitted -- and the reading is what that one number does to each class on the
*validation* rows: blind wins should rise, false wins should fall, the
recognised classes and controls should not move, and the count of
trajectories the feature touches says how much of the corpus it can reach.

    uv run python -m tools.v2.featurescan --suite corpus/v2/endgame_calibration_v1.jsonl --out corpus/v2/03_featurescan.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import chess

from cs_passed import passed_pawn_mask

CLASSES = ("blind_win", "false_win", "recognised_win", "recognised_draw", "losing", "control_middle", "control_tactic")


def cheb(a: int, b: int) -> int:
    return max(abs(chess.square_file(a) - chess.square_file(b)), abs(chess.square_rank(a) - chess.square_rank(b)))


def king_to(board: chess.Board, king: int | None, mask: int) -> int:
    if king is None or not mask:
        return 8
    return min(cheb(king, s) for s in chess.scan_forward(mask))


def rel_rank(sq: int, white: bool) -> int:
    return chess.square_rank(sq) if white else 7 - chess.square_rank(sq)


def unstoppable(board: chess.Board, white: bool) -> int:
    """1 if the side has a passer the enemy king cannot catch and the enemy has no pieces (square rule, side to move adjusted)."""
    them = not white
    if (board.occupied_co[them] & ~board.pawns & ~board.kings):
        return 0
    their_king = board.king(them)
    if their_king is None:
        return 0
    for sq in chess.scan_forward(passed_pawn_mask(board, white)):
        promo = chess.square(chess.square_file(sq), 7 if white else 0)
        steps = 7 - rel_rank(sq, white)
        if rel_rank(sq, white) == 1:
            steps -= 1
        tempo = 0 if board.turn == white else 1
        if cheb(their_king, promo) > steps + tempo:
            return 1
    return 0


def rook_activity(board: chess.Board, white: bool) -> int:
    us = white
    score = 0
    seventh = 6 if us else 1
    for sq in chess.scan_forward(board.pieces_mask(chess.ROOK, us)):
        file_bb = chess.BB_FILES[chess.square_file(sq)]
        if chess.square_rank(sq) == seventh:
            score += 1
        if not (file_bb & board.pawns & board.occupied_co[us]):
            score += 1
        # Behind a passer of either colour on the same file.
        for colour in (us, not us):
            for p in chess.scan_forward(passed_pawn_mask(board, colour) & file_bb):
                behind = (chess.square_rank(sq) < chess.square_rank(p)) if colour else (chess.square_rank(sq) > chess.square_rank(p))
                if behind:
                    score += 1
    return score


def features(board: chess.Board) -> dict[str, float]:
    us = board.turn
    them = not us
    ok, tk = board.king(us), board.king(them)
    pawns = board.pawns
    ours = pawns & board.occupied_co[us]
    theirs = pawns & board.occupied_co[them]
    our_passers = passed_pawn_mask(board, us)
    their_passers = passed_pawn_mask(board, them)
    our_pieces = (board.occupied_co[us] & ~pawns & ~board.kings).bit_count()
    their_pieces = (board.occupied_co[them] & ~pawns & ~board.kings).bit_count()

    def centre(k):
        return 0 if k is None else (3.5 - abs(chess.square_file(k) - 3.5)) + (3.5 - abs(chess.square_rank(k) - 3.5))

    f: dict[str, float] = {}
    # 1. king proximity to any pawn: positive when our king is nearer the pawns than theirs.
    f["king_pawn_proximity"] = king_to(board, tk, pawns) - king_to(board, ok, pawns)
    # 2. king proximity to the enemy's pawns (attacking king) minus the same for them.
    f["king_to_enemy_pawns"] = king_to(board, tk, ours) - king_to(board, ok, theirs)
    # 3. king proximity to the opponent's most advanced passer's promotion square: defending.
    def promo_dist(king, passers, colour):
        best = None
        for sq in chess.scan_forward(passers):
            promo = chess.square(chess.square_file(sq), 7 if colour else 0)
            d = cheb(king, promo) if king is not None else 8
            best = d if best is None or d < best else best
        return best
    ours_d = promo_dist(tk, our_passers, us)  # their king to our passer's queening square
    theirs_d = promo_dist(ok, their_passers, them)
    f["king_vs_passer_geometry"] = (ours_d if ours_d is not None else 0) - (theirs_d if theirs_d is not None else 0)
    # 4. unstoppable passer by the square rule.
    f["unstoppable_passer"] = unstoppable(board, us) - unstoppable(board, them)
    # 5. rook activity.
    f["rook_activity"] = rook_activity(board, us) - rook_activity(board, them)
    # 6. opposite bishops: negative of our material edge when it is a pure OCB ending.
    bishops_only = (board.queens | board.rooks | board.knights) == 0 and board.pieces(chess.BISHOP, us) and board.pieces(chess.BISHOP, them)
    if bishops_only and (bool(board.pieces(chess.BISHOP, us) & chess.BB_LIGHT_SQUARES) != bool(board.pieces(chess.BISHOP, them) & chess.BB_LIGHT_SQUARES)):
        f["opposite_bishops"] = -(ours.bit_count() - theirs.bit_count())
    else:
        f["opposite_bishops"] = 0
    # 7. king centralisation (what the PST already rewards): control.
    f["king_centralisation"] = centre(ok) - centre(tk)
    # 8. passer count difference (already tested as rank bonus): control.
    f["passer_count"] = our_passers.bit_count() - their_passers.bit_count()
    # 9. pawn-ending king race: our king to their pawns minus theirs to ours, only in pawn endings.
    f["pawn_ending_king_race"] = f["king_to_enemy_pawns"] if (our_pieces == 0 and their_pieces == 0) else 0
    return f


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--clamp", type=int, default=1000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    rows = [json.loads(line) for line in arguments.suite.open(encoding="utf-8")][1:]
    for r in rows:
        board = chess.Board(r["fen"])
        r["features"] = features(board)
        r["eg_weight"] = (24 - r["phase24"]) / 24
        r["residual"] = min(max(r["sf_cp"], -arguments.clamp), arguments.clamp) - r["v1_static"]
    names = list(rows[0]["features"])
    diag = [r for r in rows if r["role"] == "diagnostic" and r["class"] not in ("control_tactic",)]
    valid = [r for r in rows if r["role"] == "validation"]
    lines = [f"== SINGLE-FEATURE SCAN on the V2 calibration set (clamp +-{arguments.clamp}; scale fitted on {len(diag)} diagnostic rows, read on {len(valid)} validation rows) ==",
             "slope = least-squares scale (cp per unit of endgame-weighted feature) of the V1 residual on the feature; R2 on diagnostic",
             "then, on validation with that one scale applied to V1 static: blind wins 'below' SF (want smaller), false wins 'above' SF (want smaller), MAE per class (want no rise)", ""]
    baseline = {}
    for cls in CLASSES:
        rs = [r for r in valid if r["class"] == cls]
        if rs:
            baseline[cls] = statistics.mean(abs(r["residual"]) for r in rs)
    lines.append(f"{'feature':<26} {'slope':>7} {'R2':>6} {'traj touched':>12} | {'blind below':>11} {'false above':>11} | " + " ".join(f"{c[:10]:>10}" for c in CLASSES) + "  (validation MAE, baseline in the first row)")
    lines.append(f"{'V1 as is':<26} {'':>7} {'':>6} {'':>12} | {statistics.mean(r['residual'] for r in valid if r['class'] == 'blind_win'):>+11.0f} {statistics.mean(-r['residual'] for r in valid if r['class'] == 'false_win'):>+11.0f} | " + " ".join(f"{baseline.get(c, 0):>10.0f}" for c in CLASSES))
    results = []
    for name in names:
        xs = [r["features"][name] * r["eg_weight"] for r in diag]
        ys = [r["residual"] for r in diag]
        sxx = sum(x * x for x in xs)
        slope = sum(x * y for x, y in zip(xs, ys, strict=True)) / sxx if sxx else 0.0
        ss_tot = sum((y - statistics.mean(ys)) ** 2 for y in ys)
        ss_res = sum((y - slope * x) ** 2 for x, y in zip(xs, ys, strict=True))
        r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
        touched = len({r["trajectory"] for r in rows if r["features"][name] != 0 and r["class"] in ("blind_win", "false_win")})
        by_class = {}
        for cls in CLASSES:
            rs = [r for r in valid if r["class"] == cls]
            if rs:
                by_class[cls] = statistics.mean(abs(r["residual"] - slope * r["features"][name] * r["eg_weight"]) for r in rs)
        blind = [r for r in valid if r["class"] == "blind_win"]
        false = [r for r in valid if r["class"] == "false_win"]
        below = statistics.mean(r["residual"] - slope * r["features"][name] * r["eg_weight"] for r in blind)
        above = statistics.mean(-(r["residual"] - slope * r["features"][name] * r["eg_weight"]) for r in false)
        results.append((name, slope, r2, touched, below, above, by_class))
        lines.append(f"{name:<26} {slope:>+7.1f} {r2:>6.3f} {touched:>12} | {below:>+11.0f} {above:>+11.0f} | " + " ".join(f"{by_class.get(c, 0):>10.0f}" for c in CLASSES))
    lines.append("")
    lines.append("feature distribution by class (mean raw value, share of rows non-zero):")
    lines.append(f"{'feature':<26} " + " ".join(f"{c[:14]:>16}" for c in CLASSES))
    for name in names:
        cells = []
        for cls in CLASSES:
            rs = [r for r in rows if r["class"] == cls]
            cells.append(f"{statistics.mean(r['features'][name] for r in rs):>+7.2f} {sum(r['features'][name] != 0 for r in rs) / len(rs):>7.0%}")
        lines.append(f"{name:<26} " + " ".join(f"{c:>16}" for c in cells))
    lines.append("")
    lines.append("sign agreement on the failure classes (all rows): blind wins with feature > 0 / < 0, false wins with feature < 0 / > 0")
    for name in names:
        b = [r["features"][name] for r in rows if r["class"] == "blind_win"]
        f_ = [r["features"][name] for r in rows if r["class"] == "false_win"]
        lines.append(f"  {name:<26} blind +{sum(x > 0 for x in b):>3} -{sum(x < 0 for x in b):>3} 0:{sum(x == 0 for x in b):>3}   false -{sum(x < 0 for x in f_):>3} +{sum(x > 0 for x in f_):>3} 0:{sum(x == 0 for x in f_):>3}")
    text = "\n".join(lines)
    print(text)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps([{"feature": n, "slope": s, "r2": r2, "trajectories_touched": t, "blind_below": b, "false_above": a, "validation_mae": bc} for n, s, r2, t, b, a, bc in results], indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
