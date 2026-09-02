"""King safety v1.

The term exists because king structures carry the worst error rates in the
calibrated corpus: `unusual_king_placement` errs at 2.67x the baseline rate and
`exposed_king` at 2.04x, the two highest of any structural tag.

The property that matters most here is the **endgame taper**. A king-safety term
that survived into the endgame would teach the engine to hide its king exactly
when it should be marching, so several tests below pin that to zero rather than
merely "small".
"""

from __future__ import annotations

import chess
import pytest

import cs_eval
from cs_king import king_safety_mg, king_safety_mg_reference


@pytest.fixture(autouse=True)
def _enable():
    saved = cs_eval.USE_KING_SAFETY
    cs_eval.USE_KING_SAFETY = True
    yield
    cs_eval.USE_KING_SAFETY = saved


MIRROR_CASES = [
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9",
    "r2q1rk1/1b1nbppp/p2ppn2/1p6/3NPP2/1BN1B3/PPPQ2PP/2KR3R w - - 0 13",
    "3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
    "r3k2r/pppq1ppp/2n5/3np3/1b6/2NP1N2/PPPBQPPP/R3K2R w KQkq - 0 10",
]


# ------------------------------------------------------------------ symmetry


@pytest.mark.parametrize("fen", MIRROR_CASES)
def test_mirroring_negates_the_term(fen: str) -> None:
    """White minus black must be exactly antisymmetric under a colour flip."""
    board = chess.Board(fen)
    assert board.is_valid()
    assert king_safety_mg(board) == -king_safety_mg(board.mirror())


@pytest.mark.parametrize("fen", MIRROR_CASES)
def test_full_evaluation_stays_symmetric(fen: str) -> None:
    board = chess.Board(fen)
    assert cs_eval.evaluate(board) == cs_eval.evaluate(board.mirror())


def test_a_symmetric_position_scores_zero() -> None:
    """Identical structures for both sides must cancel exactly."""
    board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert king_safety_mg(board) == 0


def test_fast_and_reference_evaluators_still_agree() -> None:
    for fen in MIRROR_CASES:
        board = chess.Board(fen)
        assert cs_eval.evaluate(board) == cs_eval.evaluate_reference(board)


# ------------------------------------------------------------- the concepts


def test_an_open_king_file_is_penalised() -> None:
    """Same material and king square; only the shelter pawn differs."""
    sheltered = chess.Board("r5k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
    exposed = chess.Board("r5k1/5ppp/8/8/8/8/5PP1/R5K1 w - - 0 1")
    assert king_safety_mg(exposed) < king_safety_mg(sheltered)


def test_an_open_file_needs_an_enemy_heavy_piece_to_matter() -> None:
    """A hole is only a road if the enemy has something to drive down it."""
    with_rook = chess.Board("r5k1/5pp1/8/8/8/8/5PP1/6K1 w - - 0 1")
    without = chess.Board("6k1/5pp1/8/8/8/8/5PP1/6K1 w - - 0 1")
    assert king_safety_mg(with_rook) < king_safety_mg(without)


def test_enemy_attackers_near_the_king_are_penalised() -> None:
    near = chess.Board("6k1/5ppp/8/8/8/5q2/5PPP/6K1 w - - 0 1")
    far = chess.Board("6k1/5ppp/8/8/8/q7/5PPP/6K1 w - - 0 1")
    assert king_safety_mg(near) < king_safety_mg(far)


def test_a_blocked_slider_is_not_counted_as_an_attacker() -> None:
    """Sliding attacks go through real occupancy, not through pieces."""
    blocked = chess.Board("6k1/5ppp/8/8/8/8/5PPP/1b4K1 w - - 0 1")
    clear = chess.Board("6k1/5ppp/8/8/8/8/5PP1/1b4K1 w - - 0 1")
    assert king_safety_mg(clear) < king_safety_mg(blocked)


@pytest.mark.parametrize(
    "attacker_fen",
    [
        "6k1/5ppp/8/8/8/5q2/5PPP/6K1 w - - 0 1",
        "6k1/5ppp/8/8/8/5r2/5PPP/6K1 w - - 0 1",
        "6k1/5ppp/8/8/8/4b3/5PPP/6K1 w - - 0 1",
        "6k1/5ppp/8/8/8/4n3/5PPP/6K1 w - - 0 1",
    ],
    ids=["queen", "rook", "bishop", "knight"],
)
def test_every_piece_type_can_be_an_attacker(attacker_fen: str) -> None:
    quiet = chess.Board("6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 0 1")
    assert king_safety_mg(chess.Board(attacker_fen)) < king_safety_mg(quiet)


def test_shelter_pawns_help() -> None:
    """Same three pawns, in front of the king or away on the other wing."""
    sheltering = chess.Board("6k1/8/8/8/8/8/5PPP/6K1 w - - 0 1")
    elsewhere = chess.Board("6k1/8/8/8/8/8/PPP5/6K1 w - - 0 1")
    assert king_safety_mg(sheltering) > king_safety_mg(elsewhere)


def test_an_enemy_pawn_storm_is_penalised() -> None:
    """Pawns are attackers. Omitting them made the term cancel on cl-170."""
    quiet = chess.Board("6k1/8/8/8/8/8/5PPP/6K1 w - - 0 1")
    stormed = chess.Board("6k1/8/8/8/8/6p1/5PPP/6K1 w - - 0 1")
    assert king_safety_mg(stormed) < king_safety_mg(quiet)


def test_the_flagship_failure_position_now_favours_black() -> None:
    """cl-170: the white king is the one under attack, and the term must say so.

    This is a diagnostic example, not a tuning target: the gate is the
    240-position suite. It is pinned because a piece-only attacker count scored
    both kings at 16 here and cancelled to exactly zero.
    """
    board = chess.Board("3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 0 1")
    assert king_safety_mg(board) < 0


def test_the_attacker_count_saturates() -> None:
    """Many attackers must not produce an unbounded penalty."""
    swarm = chess.Board("6k1/5ppp/8/8/1q1r1b2/2n2n2/5PPP/6K1 w - - 0 1")
    assert king_safety_mg(swarm) > -400, "penalty ran away"


# ------------------------------------------------------------ king placement


@pytest.mark.parametrize(
    "fen",
    [
        "8/8/8/8/8/8/8/K6k w - - 0 1",
        "K7/8/8/8/8/8/8/7k w - - 0 1",
        "8/8/8/3K4/8/8/8/7k w - - 0 1",
        "7K/8/8/8/8/8/8/k7 w - - 0 1",
    ],
    ids=["corner", "corner2", "centre", "edge"],
)
def test_kings_anywhere_do_not_crash(fen: str) -> None:
    board = chess.Board(fen)
    king_safety_mg(board)
    cs_eval.evaluate(board)


def test_a_king_in_the_centre_is_worse_than_a_castled_one() -> None:
    castled = chess.Board("r3k2r/pppppppp/8/8/8/8/PPPPP1PP/R4RK1 w kq - 0 1")
    central = chess.Board("r3k2r/pppppppp/8/8/8/8/PPPPP1PP/R3K2R w KQkq - 0 1")
    assert king_safety_mg(castled) > king_safety_mg(central)


def test_queenside_and_kingside_shelter_are_both_recognised() -> None:
    """The term must not be hard-coded to the kingside."""
    kingside = chess.Board("6k1/8/8/8/8/8/5PPP/6K1 w - - 0 1")
    queenside = chess.Board("1k6/8/8/8/8/8/PPP5/1K6 w - - 0 1")
    assert king_safety_mg(kingside) == -king_safety_mg(queenside.mirror())


# ------------------------------------------------------------------- taper


def test_the_term_is_middlegame_only_by_construction() -> None:
    """A phase-zero endgame must be untouched by king safety."""
    board = chess.Board("8/8/8/8/8/8/8/K6k w - - 0 1")
    phase = (
        (board.knights | board.bishops).bit_count()
        + 2 * board.rooks.bit_count()
        + 4 * board.queens.bit_count()
    )
    assert phase == 0

    cs_eval.USE_KING_SAFETY = False
    off = cs_eval.evaluate(board)
    cs_eval.USE_KING_SAFETY = True
    assert cs_eval.evaluate(board) == off, "king safety leaked into a phase-0 endgame"


def test_an_active_endgame_king_is_not_punished() -> None:
    """The failure mode that would cost endgames: hiding an active king."""
    active = chess.Board("8/8/8/3K4/8/5k2/8/8 w - - 0 1")
    passive = chess.Board("8/8/8/8/8/5k2/8/K7 w - - 0 1")
    cs_eval.USE_KING_SAFETY = False
    off = cs_eval.evaluate(active) - cs_eval.evaluate(passive)
    cs_eval.USE_KING_SAFETY = True
    on = cs_eval.evaluate(active) - cs_eval.evaluate(passive)
    assert on == off


def test_the_flag_actually_gates_the_term() -> None:
    board = chess.Board("3r4/1kp5/5b2/1pq1p3/4Pp1p/3P1PpQ/rBPR2K1/2RN4 w - - 0 1")
    cs_eval.USE_KING_SAFETY = False
    off = cs_eval.evaluate(board)
    cs_eval.USE_KING_SAFETY = True
    assert cs_eval.evaluate(board) != off


def test_no_dependence_on_castling_rights_or_move_counters() -> None:
    """The term reads the board, not its history."""
    a = chess.Board("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
    b = chess.Board("r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w - - 40 90")
    assert king_safety_mg(a) == king_safety_mg(b)


# ------------------------------------------------- fast path vs reference


def test_fast_path_agrees_with_the_reference_on_random_play() -> None:
    """The zone pre-filter is only safe if it never changes the answer.

    It did, once: a queen reaching the ring both diagonally and orthogonally was
    counted twice by the fast path and once by the reference, disagreeing on 92
    of 1200 positions until attackers were accumulated as a bitboard.
    """
    import random

    rng = random.Random(20260902)
    mismatches = []
    for _ in range(600):
        board = chess.Board()
        for _ in range(rng.randint(0, 90)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        if king_safety_mg(board) != king_safety_mg_reference(board):
            mismatches.append(board.fen())
    assert not mismatches, f"{len(mismatches)} mismatches, first {mismatches[:2]}"


@pytest.mark.parametrize("fen", MIRROR_CASES)
def test_fast_path_agrees_with_the_reference_on_the_suite(fen: str) -> None:
    board = chess.Board(fen)
    assert king_safety_mg(board) == king_safety_mg_reference(board)


def test_a_queen_on_a_diagonal_and_a_file_counts_once() -> None:
    """The specific double-count, pinned."""
    board = chess.Board("6k1/5ppp/8/8/8/6q1/5PPP/6K1 w - - 0 1")
    assert king_safety_mg(board) == king_safety_mg_reference(board)
