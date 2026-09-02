"""Static exchange evaluation tests.

SEE is used to prune and to order, so a wrong answer here does not crash
anything -- it quietly makes the engine play worse. Every case below states the
exchange in words and the arithmetic that follows from it.

The last test is the important one: SEE is checked against an independent
brute-force swap-off over randomly generated positions, so agreement is not
just asserted on cases chosen by the same person who wrote the algorithm.
"""

from __future__ import annotations

import random

import chess
import pytest

from cs_constants import PIECE_VALUE
from cs_see import see

P = PIECE_VALUE[chess.PAWN]
N = PIECE_VALUE[chess.KNIGHT]
B = PIECE_VALUE[chess.BISHOP]
R = PIECE_VALUE[chess.ROOK]
Q = PIECE_VALUE[chess.QUEEN]


CASES = [
    # (name, fen, uci, expected)
    ("free pawn", "4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5", P),
    ("defended pawn, equal trade", "4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5", 0),
    ("queen takes defended pawn", "4k3/8/2p5/3p4/8/8/8/3QK3 w - - 0 1", "d1d5", P - Q),
    ("pawn takes free queen", "4k3/8/8/3q4/4P3/8/8/4K3 w - - 0 1", "e4d5", Q),
    ("rook trade defended by king", "3rk3/8/8/8/8/8/8/3RK3 w - - 0 1", "d1d8", 0),
    ("knight takes free rook", "4k3/8/8/3r4/8/4N3/8/4K3 w - - 0 1", "e3d5", R),
    ("quiet move scores zero", "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1", "e2e4", 0),
]


@pytest.mark.parametrize(("name", "fen", "uci", "expected"), CASES, ids=[c[0] for c in CASES])
def test_known_exchanges(name: str, fen: str, uci: str, expected: int) -> None:
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci)
    assert move in board.legal_moves, f"{name}: {uci} is not legal"
    assert see(board, move) == expected, name


def test_xray_rook_joins_the_exchange() -> None:
    """A rook behind a rook must count once the front one has moved.

    White doubles on the d-file against a rook defended only by the king.
    Rxd8 Kxd8 leaves white a rook up only if the back rook is counted, so a SEE
    that took its attacker set once at the start would score this wrong.
    """
    board = chess.Board("3rk3/8/8/8/8/8/3R4/3RK3 w - - 0 1")
    move = chess.Move.from_uci("d2d8")
    assert move in board.legal_moves
    # Rxd8 wins a rook; Kxd8 is refused because the d1 rook still covers d8.
    assert see(board, move) == R


def test_losing_capture_is_negative() -> None:
    board = chess.Board("4k3/8/2p5/3p4/8/8/8/3QK3 w - - 0 1")
    assert see(board, chess.Move.from_uci("d1d5")) < 0


def _brute_force_swap(board: chess.Board, move: chess.Move) -> int:
    """Independent reference: play out the capture sequence with real moves.

    At each step the side to move either stops, or recaptures on the square with
    its cheapest legal capturer. This uses python-chess's own legality rules
    rather than the bitboard reasoning under test.
    """
    square = move.to_square

    def best(node: chess.Board) -> int:
        captures = [
            candidate
            for candidate in node.legal_moves
            if candidate.to_square == square and node.is_capture(candidate)
        ]
        if not captures:
            return 0
        captures.sort(key=lambda c: PIECE_VALUE[node.piece_type_at(c.from_square) or 1])
        cheapest = captures[0]
        victim = node.piece_type_at(square)
        gain = PIECE_VALUE[victim] if victim else PIECE_VALUE[chess.PAWN]
        node.push(cheapest)
        value = gain - best(node)
        node.pop()
        # The side to move may decline the exchange.
        return max(0, value)

    victim = board.piece_type_at(square)
    gain = PIECE_VALUE[victim] if victim else PIECE_VALUE[chess.PAWN]
    board.push(move)
    result = gain - best(board)
    board.pop()
    return result


def _random_capture_positions(count: int, seed: int = 902) -> list[tuple[chess.Board, chess.Move]]:
    rng = random.Random(seed)
    found: list[tuple[chess.Board, chess.Move]] = []
    while len(found) < count:
        board = chess.Board()
        for _ in range(rng.randint(4, 60)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        captures = [
            m
            for m in board.legal_moves
            if board.is_capture(m) and not m.promotion and m.to_square != board.ep_square
        ]
        if captures:
            found.append((board.copy(stack=False), rng.choice(captures)))
    return found


def test_matches_brute_force_on_random_positions() -> None:
    """Agreement with an independent swap-off over positions nobody chose.

    SEE reasons about attackers, not about legality, so it does not know that a
    recapture can be pinned. That is the standard limitation of the algorithm
    and it is accepted here rather than engineered away: making it pin-aware
    would cost far more than the rare inaccuracy does, and the failure mode is
    mis-ranking one capture, not producing an illegal move.

    What is asserted is that such cases stay rare. A sudden rise in this rate
    would mean a real bug rather than the known approximation.
    """
    samples = _random_capture_positions(250)
    mismatches = []
    for board, move in samples:
        expected = _brute_force_swap(board, move)
        actual = see(board, move)
        if expected != actual:
            mismatches.append((board.fen(), move.uci(), actual, expected))

    rate = len(mismatches) / len(samples)
    detail = "; ".join(f"{f} {u}: see={a} brute={b}" for f, u, a, b in mismatches[:3])
    assert rate <= 0.02, f"{len(mismatches)}/{len(samples)} disagree ({rate:.1%}): {detail}"


def test_pinned_recapture_is_the_known_limitation() -> None:
    """Pin the recapturing pawn and SEE reports a loss where none exists.

    Black's Nxf3+ wins a pawn because White's e2 pawn is pinned against the king
    by the queen on e7 and cannot take back. SEE counts the pawn as an attacker
    and reports losing a knight for a pawn.
    """
    board = chess.Board("r1b3r1/ppp1qk1p/3p3n/4npp1/6PP/B1N2P1B/PPP1P3/RQ2KN1R b - - 1 17")
    move = chess.Move.from_uci("e5f3")
    assert move in board.legal_moves

    board.push(move)
    recapture = chess.Move.from_uci("e2f3")
    assert recapture not in board.legal_moves, "the e-pawn should be pinned"
    board.pop()

    assert see(board, move) == P - N  # pessimistic: pretends the pin does not exist
    assert _brute_force_swap(board, move) == P  # the truth
