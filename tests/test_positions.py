"""Guard the benchmark corpus.

Corpus v1 shipped a position with a bishop giving check to the side *not* to
move -- `Status.OPPOSITE_CHECK` -- and every arena the project had run used it
as a starting position. python-chess constructs such a board happily and
generates moves from it, so nothing failed loudly; it simply corrupted a fixed
fraction of every result.

These tests exist so that can never recur silently. A single invalid FEN fails
the suite immediately.
"""

from __future__ import annotations

import chess
import pytest

from tools.positions import (
    BALANCED_OPENINGS,
    CORPUS_VERSION,
    SHARP_POSITIONS,
    corpus_hash,
    invalid_positions,
)

ALL = tuple(("balanced", i, f) for i, f in enumerate(BALANCED_OPENINGS)) + tuple(
    ("sharp", i, f) for i, f in enumerate(SHARP_POSITIONS)
)


@pytest.mark.parametrize(("suite", "index", "fen"), ALL, ids=[f"{s}[{i}]" for s, i, _ in ALL])
def test_position_is_valid(suite: str, index: int, fen: str) -> None:
    """Every benchmark position must be one python-chess accepts as legal."""
    board = chess.Board(fen)
    assert board.is_valid(), f"{suite}[{index}] {fen}: {board.status()!r}"


def test_no_invalid_positions_anywhere() -> None:
    """The same guarantee, in the form the arena checks before starting."""
    bad = invalid_positions()
    assert not bad, "\n".join(f"{s}[{i}] {f}: {status}" for s, i, f, status in bad)


@pytest.mark.parametrize(("suite", "index", "fen"), ALL, ids=[f"{s}[{i}]" for s, i, _ in ALL])
def test_position_has_legal_moves(suite: str, index: int, fen: str) -> None:
    """A starting position with no legal move is over before it begins."""
    board = chess.Board(fen)
    assert list(board.legal_moves), f"{suite}[{index}] {fen} is terminal"


@pytest.mark.parametrize(("suite", "index", "fen"), ALL, ids=[f"{s}[{i}]" for s, i, _ in ALL])
def test_side_not_to_move_is_not_in_check(suite: str, index: int, fen: str) -> None:
    """The specific defect that got through: the wrong king in check.

    ``is_valid()`` already covers this, but naming it separately means a future
    failure says what actually went wrong rather than printing a status flag.
    """
    board = chess.Board(fen)
    mirror = board.copy(stack=False)
    mirror.turn = not board.turn
    assert not mirror.is_check(), f"{suite}[{index}] {fen}: side not to move is in check"


def test_corpus_identity_is_recorded() -> None:
    """Benchmark records pin results to a corpus; the hash has to be stable."""
    assert CORPUS_VERSION >= 2
    digest = corpus_hash()
    assert len(digest) == 16
    assert digest == corpus_hash(), "corpus_hash must be deterministic"
    # v1's identity, so an old record remains identifiable.
    assert digest != "0c1fd866a32163e5", "corpus hash still matches the corpus with the illegal FEN"


def test_no_duplicate_positions() -> None:
    combined = BALANCED_OPENINGS + SHARP_POSITIONS
    duplicates = {fen for fen in combined if combined.count(fen) > 1}
    assert not duplicates, f"duplicated positions skew pairing: {duplicates}"
