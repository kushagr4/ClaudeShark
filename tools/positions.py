"""A deliberately broad set of starting positions for benchmarking.

Rated games start from curated neutral positions rather than the initial
position, so a test suite built around openings would measure the wrong thing.
These are roughly balanced and cover the structural families an engine has to
handle: open and closed centres, queenless play, king-safety races, and every
common endgame.

Every position is played twice in the arena, once with each engine as white, so
any residual imbalance cancels out.
"""

from __future__ import annotations

BALANCED_OPENINGS: tuple[str, ...] = (
    # Open middlegames
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6",
    "r1bq1rk1/pp3ppp/2n1pn2/2pp4/1b1P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9",
    "rn1qkb1r/pp2pppp/2p2n2/3p1b2/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5",
    # Closed and semi-closed centres
    "r1bq1rk1/1pp1npbp/p1np2p1/4p3/2PPP3/2N1BP2/PP1QN1PP/R3KB1R w KQ - 0 10",
    "r1bqk2r/pp1nbppp/2p1pn2/3p4/2PP4/2N1PN2/PPQ1BPPP/R1B1K2R w KQkq - 0 8",
    "r1bqk2r/ppp1bppp/2np1n2/4p3/2P5/2NPPN2/PP2BPPP/R1BQK2R w KQkq - 0 7",
    # Tactical middlegames
    "r2q1rk1/pp1bbppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP1QPPP/R1B2RK1 w - - 0 10",
    "r1b1k2r/ppppqppp/2n2n2/2b5/3NP3/2N5/PPP1BPPP/R1BQ1RK1 w kq - 0 8",
    "rnbq1rk1/pp2ppbp/6p1/2p5/3PP3/2P2N2/P3BPPP/R1BQK2R w KQ - 0 9",
    # King-safety / opposite castling
    "r1bqk2r/pp2bppp/2n1pn2/2pp4/3P1B2/2P1PN2/PP1N1PPP/R2QKB1R w KQkq - 0 8",
    "r2qk2r/pb1nbppp/1pp1pn2/3p4/2PP4/1PN1PN2/PB3PPP/R2QKB1R w KQkq - 0 9",
    # Queenless middlegames
    "r3k2r/pp3ppp/2n1bn2/2bp4/8/2N1BN2/PPP2PPP/R3KB1R w KQkq - 0 11",
    "r3k2r/ppp2ppp/2n2n2/3pp3/3PP3/2N2N2/PPP2PPP/R3K2R w KQkq - 0 9",
    # Rook endgames
    "8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 40",
    "8/pp3pk1/6p1/8/8/1R4P1/r4P1P/6K1 w - - 0 35",
    "8/5ppk/8/8/8/1R6/r4PPP/6K1 w - - 0 38",
    # Minor-piece endgames
    "8/5pk1/4b1p1/8/8/4N1P1/5P1P/6K1 w - - 0 40",
    "8/4kp2/6p1/2b5/8/4B1P1/5P1P/6K1 w - - 0 40",
    "8/2n2pk1/6p1/8/8/2B3P1/5P1P/6K1 w - - 0 40",
    # Pawn endings
    "8/5pk1/6p1/8/6P1/5PK1/8/8 w - - 0 40",
    "8/p4pk1/1p4p1/8/1P4P1/P4PK1/8/8 w - - 0 36",
    # Material imbalance, roughly level
    "r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/2KR1B1R w kq - 0 15",
    "r1b1k2r/pppp1ppp/8/8/8/8/PPPP1PPP/R1B1K2R w KQkq - 0 12",
)
