"""Focused C9 correctness reproduction: quiescence on a stalemate whose only
capture is illegal (found at the RC-E review, fixed in RC-F, commit b7f42cf).

Prints the compiled and interpreted quiescence scores and exits 1 when they
disagree, so it demonstrates the defect on commit 99afd81 and the fix on
b7f42cf. The permanent regression tests are in tests/test_core.py.

Run: uv run python -m tools.review_c9_repro
"""
import os
from time import perf_counter

os.environ["CS_CORE"] = "python"

import chess
import cs_core as core
import cs_fast
from cs_search import PySearcher


def args(s):
    return (s.B, s.O, s.M, s.S, s.U, s.MLS, s.MSS, s.PATH, s.GK,
            s.TK, s.TV, s.KILL, s.HIST, s.CTL, s.TCTL, s.GAINS)


def prepare(s, board):
    s.new_game()
    s.CTL[:] = 0
    s.PATH[:] = 0
    s.TCTL[0] = perf_counter() + 3600
    core.load_board(board, s.B, s.O, s.M, s.S)


def main():
    s = cs_fast.Searcher()
    ref = PySearcher(tt_bits=14)
    fen = "6Bk/5K2/8/8/8/8/8/R7 b - - 0 1"
    board = chess.Board(fen)
    assert board.is_valid() and board.is_stalemate()
    prepare(s, board)
    n = core.gen_moves(s.B, s.O, s.M, s.S, s.MLS[0], True)
    print("stalemate FEN:", fen, flush=True)
    print("pseudo tactical:", [core.move_to_uci(int(m)) for m in s.MLS[0, :n]], flush=True)
    actual = core.quiescence(*args(s), -32000, 32000, 0, 0)
    expected = ref._quiescence(board, -32000, 32000, 0, 0)
    print("qsearch C9 / C5:", actual, expected, flush=True)
    verdict = "AGREE" if actual == expected == 0 else "DIVERGENCE"
    print("verdict:", verdict, flush=True)
    prepare(s, board)
    actual_rfp = core.negamax(*args(s), 1, -1001, -1000, 1, False)
    expected_rfp = ref._negamax(board, 1, -1001, -1000, 1, False)
    print("RFP stalemate C9 / C5 (must both be 0):", actual_rfp, expected_rfp, flush=True)
    parent = chess.Board(fen.replace(" b ", " w "))
    assert parent.is_valid()
    s.new_game()
    move, info = s.search(parent, 0, max_depth=1)
    parent.push(move)
    print("C9 depth-1 root:", move.uci(), "score:", info.score,
          "result:", parent.outcome(claim_draw=True), flush=True)
    raise SystemExit(0 if verdict == "AGREE" else 1)


if __name__ == "__main__":
    main()
