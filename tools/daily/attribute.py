"""Which structural features explain the engine's disagreement with the oracle?

The calibration report says *how much* the engine's score disagrees with the
oracle and in which phase. It does not say *why*. This module attaches
structural features to every position in the annotated corpora and reports the
signed residual -- the engine's root score minus the oracle's, from the mover's
point of view -- inside each feature bucket.

The signed residual is the number that chooses the next feature. A large
positive residual in a bucket means the engine is too optimistic exactly there,
a large negative one means it is too pessimistic, and a bucket where the
residual is near zero is not worth a term however large its error magnitude,
because a symmetric error is noise rather than missing knowledge.

Every feature is a candidate hypothesis from the V2 shortlist made measurable:
passer count and advancement, whether the defending king is inside the square
of the best passer, rook behind a passer, opposite-coloured bishops, pawns
confined to one wing, king centralisation, and total pawn count.

    uv run python -m tools.daily.attribute --out corpus/daily/attribution.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

import chess

from cs_constants import TOTAL_PHASE

CORPORA = (
    "corpus/postmortem/games/annotated.jsonl",
    "corpus/v2/kp/games/gate2_annotated.jsonl",
    "corpus/passed/games/gate2_annotated.jsonl",
    "corpus/mopup/games/gate2_annotated.jsonl",
)

PHASE_WEIGHT = {chess.KNIGHT: 1, chess.BISHOP: 1, chess.ROOK: 2, chess.QUEEN: 4}


def phase_of(board: chess.Board) -> int:
    total = 0
    for piece_type, weight in PHASE_WEIGHT.items():
        total += weight * (len(board.pieces(piece_type, chess.WHITE)) + len(board.pieces(piece_type, chess.BLACK)))
    return min(TOTAL_PHASE, total)


def passers(board: chess.Board, colour: chess.Color) -> list[int]:
    """Squares of ``colour``'s passed pawns: no enemy pawn ahead on its file or either neighbour."""
    out = []
    enemy = board.pieces(chess.PAWN, not colour)
    for square in board.pieces(chess.PAWN, colour):
        file_index, rank = chess.square_file(square), chess.square_rank(square)
        blocked = False
        for f in (file_index - 1, file_index, file_index + 1):
            if not 0 <= f <= 7:
                continue
            for e in enemy:
                if chess.square_file(e) != f:
                    continue
                ahead = chess.square_rank(e) > rank if colour == chess.WHITE else chess.square_rank(e) < rank
                if ahead:
                    blocked = True
                    break
            if blocked:
                break
        if not blocked:
            out.append(square)
    return out


def relative_rank(square: int, colour: chess.Color) -> int:
    rank = chess.square_rank(square)
    return rank if colour == chess.WHITE else 7 - rank


def promotion_square(square: int, colour: chess.Color) -> int:
    return chess.square(chess.square_file(square), 7 if colour == chess.WHITE else 0)


def in_the_square(board: chess.Board, pawn: int, colour: chess.Color) -> bool:
    """Is the defending king inside the square of this pawn (the classical rule)?"""
    king = board.king(not colour)
    if king is None:
        return True
    target = promotion_square(pawn, colour)
    steps = 7 - relative_rank(pawn, colour)
    if relative_rank(pawn, colour) == 1:
        steps -= 1  # the double step
    distance = chess.square_distance(king, target)
    return distance <= steps + (0 if board.turn != colour else 1)


def features(board: chess.Board) -> dict[str, object]:
    us, them = board.turn, not board.turn
    ours, theirs = passers(board, us), passers(board, them)
    our_best = max((relative_rank(s, us) for s in ours), default=-1)
    their_best = max((relative_rank(s, them) for s in theirs), default=-1)
    pawns = board.pawns
    files = {chess.square_file(s) for s in chess.SquareSet(pawns)}
    minors_us = len(board.pieces(chess.BISHOP, us)) + len(board.pieces(chess.KNIGHT, us))
    minors_them = len(board.pieces(chess.BISHOP, them)) + len(board.pieces(chess.KNIGHT, them))
    bishops_us = board.pieces(chess.BISHOP, us)
    bishops_them = board.pieces(chess.BISHOP, them)
    opposite_bishops = (
        len(bishops_us) == 1 and len(bishops_them) == 1 and minors_us == 1 and minors_them == 1
        and (next(iter(bishops_us)) in chess.SquareSet(chess.BB_LIGHT_SQUARES))
        != (next(iter(bishops_them)) in chess.SquareSet(chess.BB_LIGHT_SQUARES))
    )
    our_rooks = board.pieces(chess.ROOK, us)
    rook_behind = any(
        chess.square_file(r) == chess.square_file(p)
        and (chess.square_rank(r) < chess.square_rank(p) if us == chess.WHITE else chess.square_rank(r) > chess.square_rank(p))
        for r in our_rooks for p in ours
    )
    their_king_caught = all(in_the_square(board, p, us) for p in ours) if ours else None
    our_king_caught = all(in_the_square(board, p, them) for p in theirs) if theirs else None
    king_us, king_them = board.king(us), board.king(them)
    centre = {chess.D4, chess.D5, chess.E4, chess.E5}
    return {
        "phase": phase_of(board),
        "our passers": min(3, len(ours)),
        "their passers": min(3, len(theirs)),
        "our best passer rank": our_best,
        "their best passer rank": their_best,
        "their king inside our passer's square": their_king_caught,
        "our king inside their passer's square": our_king_caught,
        "rook behind our own passer": rook_behind,
        "opposite-coloured bishops": opposite_bishops,
        "pawns on one wing only": bool(files) and (max(files) - min(files) <= 3),
        "total pawns": min(8, chess.popcount(pawns)),
        "our king centralisation": min(chess.square_distance(king_us, c) for c in centre) if king_us is not None else -1,
        "king centralisation edge": (
            min(chess.square_distance(king_them, c) for c in centre)
            - min(chess.square_distance(king_us, c) for c in centre)
            if king_us is not None and king_them is not None else 0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--clamp", type=int, default=2000)
    parser.add_argument("--max-phase", type=int, default=9, help="restrict to phase <= this; -1 for all")
    arguments = parser.parse_args()
    rows = []
    for path in CORPORA:
        p = Path(path)
        if not p.exists():
            continue
        for line in p.open(encoding="utf-8"):
            g = json.loads(line)
            for m in g["moves"]:
                sf_white = m.get("sf_cp_white_before")
                if sf_white is None or abs(sf_white) > arguments.clamp:
                    continue
                board = chess.Board(m["fen"])
                white = board.turn == chess.WHITE
                sf = sf_white if white else -sf_white
                f = features(board)
                if arguments.max_phase >= 0 and f["phase"] > arguments.max_phase:
                    continue
                field = "cand_static" if m["mover"] == "cand" else "base_static"
                static_white = m.get(field)
                if static_white is None:
                    continue
                rows.append({"sf": sf, "root": m["score_stm"],
                             "static": static_white if white else -static_white,
                             "residual": m["score_stm"] - sf, **f})
    print(f"{len(rows)} positions", flush=True)
    # The engine compresses decisive scores toward zero, so a bucket that is on
    # average losing will show a positive raw residual for that reason alone.
    # Calibrating an expected root score per oracle band and measuring the
    # departure from *that* is what separates missing knowledge from
    # compression. Bands are 50 cp wide, and a band with too few positions
    # falls back to the identity.
    def band_key(cp: int) -> int:
        return int(cp // 50)

    band_rows = defaultdict(list)
    for r in rows:
        band_rows[band_key(r["sf"])].append(r)
    expected = {k: statistics.mean(x["root"] for x in v) for k, v in band_rows.items() if len(v) >= 40}
    expected_static = {k: statistics.mean(x["static"] for x in v) for k, v in band_rows.items() if len(v) >= 40}
    for r in rows:
        r["residual"] = r["root"] - expected.get(band_key(r["sf"]), r["sf"])
        r["static_residual"] = r["static"] - expected_static.get(band_key(r["sf"]), r["sf"])
    overall = statistics.mean(r["residual"] for r in rows)
    overall_static = statistics.mean(r["static_residual"] for r in rows)
    lines = [f"== FEATURE ATTRIBUTION OF THE ENGINE-ORACLE RESIDUAL: {len(rows)} positions, phase <= {arguments.max_phase} ==",
             "residual = engine depth-6 root minus the mean root of every position in the same 50 cp oracle band,",
             "which removes the engine's uniform compression of decisive scores and leaves only what a feature explains.",
             f"overall mean root residual {overall:+.0f} cp, static residual {overall_static:+.0f} cp; a bucket is interesting when it departs from those.",
             "A bucket whose ROOT departs but whose STATIC does not is a search-horizon effect, not missing evaluation knowledge.", ""]
    for key in features(chess.Board()):
        if key == "phase":
            continue
        groups = defaultdict(list)
        for r in rows:
            groups[r[key]].append(r)
        lines.append(f"-- {key} --")
        lines.append(f"   {'value':<10} {'n':>6} {'mean SF':>8} {'mean root':>10} {'root departure':>15} {'static departure':>17} {'mean |resid|':>13}")
        for value in sorted(groups, key=lambda v: (v is None, v)):
            rs = groups[value]
            if len(rs) < 40:
                continue
            resid = statistics.mean(r["residual"] for r in rs)
            sresid = statistics.mean(r["static_residual"] for r in rs)
            lines.append(f"   {value!s:<10} {len(rs):>6} {statistics.mean(r['sf'] for r in rs):>+8.0f} "
                         f"{statistics.mean(r['root'] for r in rs):>+10.0f} {resid - overall:>+15.0f} {sresid - overall_static:>+17.0f} "
                         f"{statistics.mean(abs(r['residual']) for r in rs):>13.0f}")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
