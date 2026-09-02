"""A deliberately broad set of starting positions for benchmarking.

**Corpus version 2.** Every position is validated by `tests/test_positions.py`,
which fails the suite if any FEN is not `board.is_valid()`. That test exists
because version 1 shipped an illegal position -- `BALANCED_OPENINGS[19]` had a
bishop on c3 giving check to the black king on g7 with White to move
(`Status.OPPOSITE_CHECK`) -- and every arena the project had run to that point
used it as a starting position.

Corpus identity, so results can be tied to the corpus that produced them:

| version | balanced | sharp | combined sha256[:16] | note |
|---|---|---|---|---|
| v1 | 24 | 18 | `0c1fd866a32163e5` | contained one illegal position |
| v2 | 24 | 18 | see `corpus_hash()` | index 19 replaced |

Results produced under v1 are **not** directly comparable with results produced
under v2. See `benchmarks/README.md`.


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
    # Corpus v2: the bishop was on c3, where it attacked the black king on g7
    # while it was White to move -- an OPPOSITE_CHECK position that python-chess
    # rejects as invalid. Moved to e3, which keeps the intended material and
    # structure (bishop against knight, three pawns each) and is legal.
    "8/2n2pk1/6p1/8/8/4B1P1/5P1P/6K1 w - - 0 40",
    # Pawn endings
    "8/5pk1/6p1/8/6P1/5PK1/8/8 w - - 0 40",
    "8/p4pk1/1p4p1/8/1P4P1/P4PK1/8/8 w - - 0 36",
    # Material imbalance, roughly level
    "r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/2KR1B1R w kq - 0 15",
    "r1b1k2r/pppp1ppp/8/8/8/8/PPPP1PPP/R1B1K2R w KQkq - 0 12",
)

# Sharp positions: loose pieces, open lines to the king, pins and available
# checks. The quiet suite above is the right place to measure ordinary play, but
# it is the wrong place to catch a reduction scheme skipping a forcing move --
# on a quiet board there is nothing forcing to skip. These exist so
# tools/movequality.py has somewhere for tactical blindness to show up.
SHARP_POSITIONS: tuple[str, ...] = (
    # Exposed kings, opposite castling, pawn storms
    "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 9",
    "r2qk2r/ppp1bppp/2n1bn2/3p4/3P1B2/2N1PN2/PPQ2PPP/R3KB1R w KQkq - 0 9",
    "r1bqk2r/pp1nbppp/2p1pn2/3p2B1/2PP4/2N1PN2/PPQ2PPP/R3KB1R w KQkq - 0 8",
    # Loose and hanging pieces
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "r1bqkb1r/pppp1ppp/2n5/4p3/2B1n3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2BPP3/5N2/PPP2PPP/RNBQK2R b KQkq - 0 5",
    # Pins and discovered attacks
    "r2qkb1r/pp2pppp/2n2n2/3p1b2/3P4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 7",
    "rnbqk2r/ppp2ppp/4pn2/3p4/1bPP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 6",
    # Central tension, many captures available
    "r1bqkb1r/pp3ppp/2n1pn2/2pp4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 7",
    "rnbqkb1r/pp2pppp/3p1n2/2pP4/4P3/2N5/PPP2PPP/R1BQKBNR b KQkq - 0 5",
    "r1bqkbnr/pp1p1ppp/2n5/2p1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4",
    # Queenside majority races and sacrificial motifs
    "r2q1rk1/1b1nbppp/p2ppn2/1p6/3NPP2/1BN1B3/PPPQ2PP/2KR3R w - - 0 13",
    "r1b2rk1/pp1nqppp/2pbpn2/3p4/2PP4/2NBPN2/PPQ2PPP/R1B2RK1 w - - 0 10",
    # King in the centre
    "r1bqk2r/ppppbppp/2n2n2/4N3/2B1P3/8/PPPP1PPP/RNBQK2R b KQkq - 0 5",
    "rnbqkb1r/ppp2ppp/4pn2/3P4/3P4/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 4",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR b KQkq - 0 3",
    # En passant available, and the choice actually matters.
    "k7/8/8/3pP3/8/8/8/7K w - d6 0 2",
    "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 4",
)

CORPUS_VERSION = 2
# The combined hash of corpus v1, kept so a result recorded under it can still
# be identified. v1 contained one illegal position; see the module docstring.
CORPUS_V1_HASH = "0c1fd866a32163e5"


def corpus_hash(positions: tuple[str, ...] | None = None) -> str:
    """Stable identifier for a set of positions, for benchmark records."""
    import hashlib

    chosen = positions if positions is not None else BALANCED_OPENINGS + SHARP_POSITIONS
    return hashlib.sha256("\n".join(chosen).encode()).hexdigest()[:16]


def unsuitable(fens: tuple[str, ...], label: str = "selected") -> list[tuple[str, int, str, str]]:
    """Validate whatever set of positions is actually about to be benchmarked.

    Applies to the built-in corpus, a custom ``--start-fen`` and any future
    externally supplied set alike. Validating only the built-in corpus was not
    enough: a custom FEN went straight through, so the arena could knowingly
    benchmark an illegal position.

    A position is unsuitable if python-chess rejects it, if the game is already
    over before a move is played, or if the side not to move is in check --
    the specific defect that got a bishop-gives-check position into corpus v1.
    """
    import chess

    bad: list[tuple[str, int, str, str]] = []
    for index, fen in enumerate(fens):
        try:
            board = chess.Board(fen)
        except ValueError as error:
            bad.append((label, index, fen, f"unparseable: {error}"))
            continue
        if not board.is_valid():
            bad.append((label, index, fen, repr(board.status())))
            continue
        if board.is_game_over(claim_draw=False):
            bad.append((label, index, fen, "already over before a move is played"))
            continue
        mirror = board.copy(stack=False)
        mirror.turn = not board.turn
        if mirror.is_check():
            bad.append((label, index, fen, "side not to move is in check"))
    return bad


def invalid_positions() -> list[tuple[str, int, str, str]]:
    """Every position that python-chess rejects, as (suite, index, fen, status).

    Used by the test that guards the corpus and by the arena, which refuses to
    start a match on an invalid position rather than producing games from one.
    """
    import chess

    bad: list[tuple[str, int, str, str]] = []
    suites = (("BALANCED_OPENINGS", BALANCED_OPENINGS), ("SHARP_POSITIONS", SHARP_POSITIONS))
    for name, suite in suites:
        for index, fen in enumerate(suite):
            board = chess.Board(fen)
            if not board.is_valid():
                bad.append((name, index, fen, repr(board.status())))
    return bad
