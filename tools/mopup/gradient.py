"""Evaluation gradient in bare-king endings: baseline against mop-up v1.

For K+Q v K and K+R v K, with the attacker's king and piece fixed, the defending
king is placed on every legal square and the static evaluation recorded; then,
with the defending king cornered, the attacking king is walked in from the far
corner. The spread of each series is the gradient the search has to work with.
The audit measured 61 cp for the baseline against a 936 cp queen.

    uv run python -m tools.mopup.gradient --out corpus/mopup/04_gradient.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path

import chess

import cs_eval
from cs_mopup import EDGE, PROXIMITY, mop_up


def static(board: chess.Board, with_term: bool) -> int:
    """White-point-of-view static score with the term off, or on."""
    saved = cs_eval.USE_MOP_UP
    cs_eval.set_term("mopup", with_term)
    try:
        score = cs_eval.evaluate(board)
    finally:
        cs_eval.set_term("mopup", saved)
    return score - cs_eval.TEMPO if board.turn else -(score - cs_eval.TEMPO)


def series(attacker_pieces: dict[int, chess.Piece], defender_squares: list[int]) -> list[tuple[int, int, int]]:
    out = []
    for sq in defender_squares:
        board = chess.Board(None)
        for s, p in attacker_pieces.items():
            board.set_piece_at(s, p)
        board.set_piece_at(sq, chess.Piece(chess.KING, chess.BLACK))
        board.turn = chess.WHITE
        if not board.is_valid() or board.is_check():
            continue
        out.append((sq, static(board, False), static(board, True)))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    lines = [f"== EVALUATION GRADIENT, baseline vs mop-up v1 (EDGE={EDGE}, PROXIMITY={PROXIMITY}) ==",
             "white-point-of-view static scores, tempo removed; 'spread' = max - min over the series", ""]
    for name, pieces in (("K+Q v K (Ke2, Qd1)", {chess.E2: chess.Piece(chess.KING, chess.WHITE), chess.D1: chess.Piece(chess.QUEEN, chess.WHITE)}),
                         ("K+R v K (Ke2, Rd1)", {chess.E2: chess.Piece(chess.KING, chess.WHITE), chess.D1: chess.Piece(chess.ROOK, chess.WHITE)})):
        rows = series(pieces, list(range(64)))
        b = [r[1] for r in rows]
        c = [r[2] for r in rows]
        lines.append(f"-- {name}: defending king on every legal square (n={len(rows)})")
        lines.append(f"   baseline: min {min(b):+} max {max(b):+} spread {max(b) - min(b)}")
        lines.append(f"   mop-up:   min {min(c):+} max {max(c):+} spread {max(c) - min(c)}")
        for label, sq in (("centre d5", chess.D5), ("edge a5", chess.A5), ("corner a8", chess.A8), ("corner h8", chess.H8)):
            r = next((x for x in rows if x[0] == sq), None)
            if r:
                lines.append(f"   defender on {label:<10} baseline {r[1]:>+5}  mop-up {r[2]:>+5}")
        # Attacking king walking in on a cornered defender.
        walk = []
        for wk in (chess.H1, chess.G2, chess.F3, chess.E4, chess.D5, chess.C6, chess.B6):
            board = chess.Board(None)
            board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
            board.set_piece_at(chess.H1 if wk != chess.H1 else chess.G1, next(p for p in pieces.values() if p.piece_type != chess.KING))
            board.set_piece_at(chess.A8, chess.Piece(chess.KING, chess.BLACK))
            board.turn = chess.WHITE
            if board.is_valid() and not board.is_check():
                walk.append((chess.square_name(wk), static(board, False), static(board, True), mop_up(board)))
        lines.append("   attacking king approaching a cornered defender (defender a8):")
        for name2, b0, c0, t in walk:
            lines.append(f"     K{name2}: baseline {b0:>+5}  mop-up {c0:>+5}  (term {t:+})")
        if walk:
            lines.append(f"   walk spread: baseline {max(w[1] for w in walk) - min(w[1] for w in walk)}, mop-up {max(w[2] for w in walk) - min(w[2] for w in walk)}")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
