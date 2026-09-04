"""Break a static evaluation into its terms: material, piece-square tables, bishop pair, tempo, registry terms.

Everything is from White's point of view before the tempo, then the tapered
total and the side-to-move score the engine would return. Used by the
false-win audit to say *which* term carries a wrong score.

    uv run python -m tools.v2.decompose "3k4/4R3/8/5K2/4B3/8/4r3/8 w - - 0 1"
"""

from __future__ import annotations

import sys

import chess

import cs_eval
import cs_terms
from cs_constants import (
    _EG_VALUE,
    _MG_VALUE,
    BISHOP_PAIR_EG,
    BISHOP_PAIR_MG,
    EG_BLACK,
    EG_WHITE,
    MG_BLACK,
    MG_WHITE,
    TEMPO,
    TOTAL_PHASE,
)


def taper(mg: int, eg: int, phase: int) -> int:
    total = mg * phase + eg * (TOTAL_PHASE - phase)
    return total // TOTAL_PHASE if total >= 0 else -(-total // TOTAL_PHASE)


def decompose(board: chess.Board, terms: tuple[str, ...] = ("king_pawn",)) -> dict:
    phase = min(TOTAL_PHASE, (board.knights | board.bishops).bit_count() + 2 * board.rooks.bit_count() + 4 * board.queens.bit_count())
    material_mg = material_eg = pst_mg = pst_eg = 0
    for piece_type in chess.PIECE_TYPES:
        for square in board.pieces(piece_type, chess.WHITE):
            material_mg += _MG_VALUE[piece_type]
            material_eg += _EG_VALUE[piece_type]
            pst_mg += MG_WHITE[piece_type][square] - _MG_VALUE[piece_type]
            pst_eg += EG_WHITE[piece_type][square] - _EG_VALUE[piece_type]
        for square in board.pieces(piece_type, chess.BLACK):
            material_mg -= _MG_VALUE[piece_type]
            material_eg -= _EG_VALUE[piece_type]
            pst_mg -= MG_BLACK[piece_type][square] - _MG_VALUE[piece_type]
            pst_eg -= EG_BLACK[piece_type][square] - _EG_VALUE[piece_type]
    pair_mg = pair_eg = 0
    if len(board.pieces(chess.BISHOP, chess.WHITE)) > 1:
        pair_mg += BISHOP_PAIR_MG
        pair_eg += BISHOP_PAIR_EG
    if len(board.pieces(chess.BISHOP, chess.BLACK)) > 1:
        pair_mg -= BISHOP_PAIR_MG
        pair_eg -= BISHOP_PAIR_EG
    out = {"phase": phase, "material": taper(material_mg, material_eg, phase), "material_mg": material_mg, "material_eg": material_eg,
           "pst": taper(pst_mg, pst_eg, phase), "pst_mg": pst_mg, "pst_eg": pst_eg,
           "pair": taper(pair_mg, pair_eg, phase), "tempo_stm": TEMPO}
    total_mg, total_eg = material_mg + pst_mg + pair_mg, material_eg + pst_eg + pair_eg
    post = 0
    for name in terms:
        term = cs_terms.BY_NAME[name]
        if term.stage == "packed":
            mg, eg = cs_terms.unpack(term.fast(board))
            out[name] = taper(mg, eg, phase)
            total_mg += mg
            total_eg += eg
        else:
            value = term.fast(board)
            out[name] = value
            post += value
    white_view = taper(total_mg, total_eg, phase) + post
    out["white_view_before_tempo"] = white_view
    out["stm_score"] = (white_view if board.turn else -white_view) + TEMPO
    return out


def main() -> None:
    board = chess.Board(sys.argv[1])
    terms = tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ("king_pawn",)
    d = decompose(board, terms)
    saved = cs_eval.ACTIVE_TERMS
    cs_eval.set_terms(terms)
    engine = cs_eval.evaluate(board)
    cs_eval.set_terms(saved)
    print(f"phase {d['phase']}/24  (White's view, tapered)")
    for key in ("material", "pst", "pair", *terms):
        print(f"  {key:<12} {d[key]:>+6}")
    print(f"  {'sum':<12} {d['white_view_before_tempo']:>+6}   side to move + tempo {TEMPO}: {d['stm_score']:+}   engine evaluate(): {engine:+}")
    assert engine == d["stm_score"], "decomposition must reproduce the engine's evaluation"


if __name__ == "__main__":
    main()
