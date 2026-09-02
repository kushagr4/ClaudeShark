"""What the static evaluator is missing, measured against the oracle.

For every labelled position this computes ClaudeShark's own evaluation (the
static evaluator, and the same after a depth-1 search so pending captures are
resolved) and the difference from the oracle's score. That residual is then
regressed on cheap relational features -- passed, isolated, doubled and
backward pawns, rook files, king shelter, mobility, space, outposts -- each
tapered by game phase so a middlegame and an endgame weight are fitted
separately. A feature with a large, well-determined coefficient is something
the evaluator would pay to know about; one near zero is not, at least not
linearly and not on this corpus.

This is the evidence behind ranking evaluation terms, and it is also the
first step of the offline weight-fitting route: the coefficients *are* the
weights such a term would ship with.

    uv run python -m tools.corpus.eval_residuals --labelled corpus\\candidates_labelled.jsonl ^
        --out corpus\\eval_residuals.md
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import chess
import numpy as np

from tools.corpus.oracle import read_jsonl
from tools.corpus.structure import _outposts, _pawn_features

CLIP_CP = 600

FEATURES = (
    "pawn", "knight", "bishop", "rook", "queen",
    "bishop_pair", "passed", "passed_advance", "protected_passed", "connected_passed",
    "isolated", "doubled", "backward", "pawn_chain_links",
    "rook_open_file", "rook_semi_open", "rook_seventh",
    "king_shelter", "king_zone_attackers", "king_open_files",
    "mobility_knight", "mobility_bishop", "mobility_rook", "mobility_queen",
    "space", "outpost", "hanging_pieces", "tempo",
)


def _side_features(board: chess.Board, colour: bool) -> dict[str, float]:
    own = board.occupied_co[colour]
    them = board.occupied_co[not colour]
    own_pawns = board.pawns & own
    enemy_pawns = board.pawns & them
    pawn = _pawn_features(board, colour)
    out: dict[str, float] = {
        "pawn": chess.popcount(own_pawns),
        "knight": chess.popcount(board.knights & own),
        "bishop": chess.popcount(board.bishops & own),
        "rook": chess.popcount(board.rooks & own),
        "queen": chess.popcount(board.queens & own),
        "bishop_pair": 1.0 if chess.popcount(board.bishops & own) >= 2 else 0.0,
        "passed": pawn["passed"],
        "protected_passed": pawn["protected_passed"],
        "connected_passed": pawn["connected_passed"],
        "isolated": pawn["isolated"],
        "doubled": pawn["doubled"],
        "backward": pawn["backward"],
        "outpost": _outposts(board, colour),
    }
    # Passed-pawn advancement: ranks travelled beyond the second, summed, so a
    # pawn on the sixth counts four and one on the third counts one.
    advance = 0
    for square in chess.scan_forward(own_pawns):
        rank = chess.square_rank(square)
        relative = rank if colour == chess.WHITE else 7 - rank
        from tools.corpus.structure import _passed

        if _passed(board, square, colour):
            advance += max(0, relative - 1)
    out["passed_advance"] = advance
    links = 0
    for square in chess.scan_forward(own_pawns):
        if board.attackers(colour, square) & own_pawns:
            links += 1
    out["pawn_chain_links"] = links

    files_own = {chess.square_file(s) for s in chess.scan_forward(own_pawns)}
    files_enemy = {chess.square_file(s) for s in chess.scan_forward(enemy_pawns)}
    open_files = semi = seventh = 0
    seventh_rank = 6 if colour == chess.WHITE else 1
    for square in chess.scan_forward(board.rooks & own):
        f = chess.square_file(square)
        if f not in files_own and f not in files_enemy:
            open_files += 1
        elif f not in files_own:
            semi += 1
        if chess.square_rank(square) == seventh_rank:
            seventh += 1
    out["rook_open_file"] = open_files
    out["rook_semi_open"] = semi
    out["rook_seventh"] = seventh

    king = board.king(colour)
    shelter = 0
    king_open = 0
    attackers = 0
    if king is not None:
        kf, kr = chess.square_file(king), chess.square_rank(king)
        for df in (-1, 0, 1):
            f = kf + df
            if not 0 <= f < 8:
                continue
            if f not in files_own:
                king_open += 1
            for dr in (1, 2):
                r = kr + dr if colour == chess.WHITE else kr - dr
                if 0 <= r < 8 and own_pawns & chess.BB_SQUARES[chess.square(f, r)]:
                    shelter += 1
                    break
        zone = chess.BB_KING_ATTACKS[king]
        for piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
            for square in chess.scan_forward(board.pieces_mask(piece_type, not colour)):
                if board.attacks_mask(square) & zone:
                    attackers += 1
    out["king_shelter"] = shelter
    out["king_open_files"] = king_open
    out["king_zone_attackers"] = attackers

    enemy_pawn_attacks = 0
    for square in chess.scan_forward(enemy_pawns):
        enemy_pawn_attacks |= chess.BB_PAWN_ATTACKS[not colour][square]
    safe = chess.BB_ALL & ~own & ~enemy_pawn_attacks
    for name, piece_type in (("knight", chess.KNIGHT), ("bishop", chess.BISHOP),
                             ("rook", chess.ROOK), ("queen", chess.QUEEN)):
        count = 0
        for square in chess.scan_forward(board.pieces_mask(piece_type, colour)):
            count += chess.popcount(board.attacks_mask(square) & safe)
        out[f"mobility_{name}"] = count
    advanced = chess.BB_RANK_5 | chess.BB_RANK_6 if colour == chess.WHITE else \
        chess.BB_RANK_4 | chess.BB_RANK_3
    out["space"] = chess.popcount(own_pawns & advanced)
    hanging = 0
    for piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
        for square in chess.scan_forward(board.pieces_mask(piece_type, colour)):
            if board.attackers(not colour, square) and not board.attackers(colour, square):
                hanging += 1
    out["hanging_pieces"] = hanging
    out["tempo"] = 1.0 if board.turn == colour else 0.0
    return out


def feature_vector(board: chess.Board) -> tuple[np.ndarray, float]:
    white = _side_features(board, chess.WHITE)
    black = _side_features(board, chess.BLACK)
    phase = min(24, chess.popcount(board.knights | board.bishops) + 2 * chess.popcount(board.rooks)
                + 4 * chess.popcount(board.queens))
    mg = phase / 24.0
    diff = np.array([white[name] - black[name] for name in FEATURES], dtype=float)
    return np.concatenate([diff * mg, diff * (1 - mg)]), mg


def engine_scores(fen: str) -> tuple[int, int]:
    """Static evaluation and depth-1 (quiescence-resolved) score, white POV."""
    from cs_eval import evaluate
    from cs_search import Searcher

    board = chess.Board(fen)
    static = evaluate(board)
    _, info = Searcher().search(board, 0, max_depth=1)
    sign = 1 if board.turn == chess.WHITE else -1
    return sign * static, sign * info.score


def fit(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Least squares with an intercept; returns coefficients, standard errors, R^2."""
    design = np.hstack([x, np.ones((len(x), 1))])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    predicted = design @ coef
    residual = y - predicted
    ss_res = float(residual @ residual)
    ss_tot = float(((y - y.mean()) ** 2).sum()) or 1.0
    dof = max(1, len(y) - design.shape[1])
    sigma2 = ss_res / dof
    try:
        cov = sigma2 * np.linalg.inv(design.T @ design)
        se = np.sqrt(np.clip(np.diag(cov), 0, None))
    except np.linalg.LinAlgError:
        se = np.full(design.shape[1], np.nan)
    return coef, se, 1.0 - ss_res / ss_tot


def main() -> None:
    parser = argparse.ArgumentParser(description="Regress the evaluator's residual on features.")
    parser.add_argument("--labelled", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    arguments = parser.parse_args()

    rows = [r for r in read_jsonl(arguments.labelled)
            if r.get("record") != "header" and r.get("cp_white") is not None]
    if arguments.limit:
        rows = rows[: arguments.limit]
    print(f"{len(rows)} labelled positions", flush=True)

    xs, mgs, oracle, static, quiet = [], [], [], [], []
    tags_of: list[list[str]] = []
    for index, row in enumerate(rows, 1):
        board = chess.Board(row["fen"])
        vector, mg = feature_vector(board)
        s, q = engine_scores(row["fen"])
        xs.append(vector)
        mgs.append(mg)
        oracle.append(max(-CLIP_CP, min(CLIP_CP, row["cp_white"])))
        static.append(s)
        quiet.append(q)
        tags_of.append(row["structure"]["tags"])
        if index % 500 == 0:
            print(f"  {index}/{len(rows)}", flush=True)
    x = np.array(xs)
    y_oracle = np.array(oracle, dtype=float)
    y_static = np.array(static, dtype=float)
    y_quiet = np.array(quiet, dtype=float)

    def r2(pred: np.ndarray, target: np.ndarray) -> float:
        ss_res = float(((target - pred) ** 2).sum())
        ss_tot = float(((target - target.mean()) ** 2).sum()) or 1.0
        return 1.0 - ss_res / ss_tot

    lines = ["# Evaluator residuals against the oracle", "",
             f"{len(rows)} labelled positions; oracle scores clipped to +/-{CLIP_CP} cp; all "
             "scores from White's point of view.", "",
             "## How well does the engine's own evaluation track the oracle?", "",
             "| engine score | corr | R^2 vs oracle | mean |error| | median |error| |",
             "|---|---|---|---|---|"]
    for name, ys in (("static evaluate()", y_static), ("depth-1 + quiescence", y_quiet)):
        err = np.abs(ys - y_oracle)
        lines.append(f"| {name} | {np.corrcoef(ys, y_oracle)[0, 1]:.3f} | {r2(ys, y_oracle):.3f} | "
                     f"{err.mean():.0f} | {np.median(err):.0f} |")

    for name, ys in (("static", y_static), ("quiet", y_quiet)):
        residual = y_oracle - ys
        coef, se, r2_fit = fit(x, residual)
        lines += ["", f"## Residual regression: oracle - {name} score", "",
                  f"R^2 of the residual explained by the features: **{r2_fit:.3f}** "
                  f"(baseline {name} R^2 {r2(ys, y_oracle):.3f}; with the fitted terms added "
                  f"{r2(ys + np.hstack([x, np.ones((len(x), 1))]) @ coef, y_oracle):.3f}).", "",
                  "Coefficients are centipawns per unit of (white minus black), middlegame and "
                  "endgame fitted separately by phase taper. |t| >= 3 is well determined.", "",
                  "| feature | MG cp | MG t | EG cp | EG t | drop-one dR^2 |",
                  "|---|---|---|---|---|---|"]
        n = len(FEATURES)
        scored = []
        for i, feature in enumerate(FEATURES):
            keep = [j for j in range(2 * n) if j not in (i, i + n)]
            _, _, r2_without = fit(x[:, keep], residual)
            t_mg = coef[i] / se[i] if se[i] else float("nan")
            t_eg = coef[i + n] / se[i + n] if se[i + n] else float("nan")
            scored.append((r2_fit - r2_without, feature, coef[i], t_mg, coef[i + n], t_eg))
        scored.sort(key=lambda s: -s[0])
        for gain, feature, c_mg, t_mg, c_eg, t_eg in scored:
            lines.append(f"| {feature} | {c_mg:+.1f} | {t_mg:+.1f} | {c_eg:+.1f} | {t_eg:+.1f} | "
                         f"{gain:.4f} |")

    # Where does the engine disagree most with the oracle, by structural tag?
    lines += ["", "## Mean absolute error of the quiet score by structural tag (n >= 30)", "",
              "| tag | n | mean |error| | mean signed (oracle - engine) |", "|---|---|---|---|"]
    by_tag: dict[str, list[int]] = defaultdict(list)
    for index, tags in enumerate(tags_of):
        for tag in tags:
            by_tag[tag].append(index)
    table = []
    for tag, indices in by_tag.items():
        if len(indices) < 30 or tag in ("open_file", "semi_open_file"):
            continue
        idx = np.array(indices)
        err = y_oracle[idx] - y_quiet[idx]
        table.append((float(np.abs(err).mean()), tag, len(indices), float(err.mean())))
    table.sort(reverse=True)
    lines += [f"| {tag} | {n} | {mae:.0f} | {signed:+.0f} |" for mae, tag, n, signed in table]

    text = "\n".join(lines) + "\n"
    arguments.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
