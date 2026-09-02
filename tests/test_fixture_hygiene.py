"""Every hard-coded FEN in the test suite must be a legal position.

This exists because fixture quality has been a recurring failure in this
project, not a hypothetical one. Found so far, each by a different route:

* an `OPPOSITE_CHECK` position in the benchmark corpus, used as a game start by
  every arena for several sessions;
* a "stalemate" fixture that was actually checkmate;
* two bishops labelled same-coloured that were on opposite colours;
* an en-passant puzzle whose stated best move was not uniquely best;
* a clock-99 fixture with adjacent kings that also had non-zeroing moves, so it
  never tested the case its name claimed.

The pattern is the same every time: the assertion passes, because the code
under test does not consult legality, and the test quietly proves nothing.
Scanning for it is cheaper than catching it one report at a time.

Positions that are *deliberately* illegal -- the ones used to prove validation
rejects them -- are listed in DELIBERATELY_INVALID and must stay illegal.
"""

from __future__ import annotations

import re
from pathlib import Path

import chess
import pytest

ROOT = Path(__file__).resolve().parent.parent

# Matches a FEN in a double-quoted string: placement, side, castling, en passant,
# and optionally the two counters.
FEN_PATTERN = re.compile(
    r'"([1-8pnbrqkPNBRQK/]+\s+[wb]\s+(?:[KQkq]{1,4}|-)\s+(?:[a-h][1-8]|-)(?:\s+\d+\s+\d+)?)"'
)

# Fixtures whose whole purpose is to be rejected.
DELIBERATELY_INVALID = frozenset(
    {
        "8/2n2pk1/6p1/8/8/2B3P1/5P1P/6K1 w - - 0 40",  # OPPOSITE_CHECK, corpus v1
        "8/8/8/8/8/8/8/8 w - - 0 1",  # empty board
    }
)


def _sources() -> list[Path]:
    return sorted((ROOT / "tests").glob("*.py")) + sorted((ROOT / "tools").glob("*.py"))


def _fens() -> list[tuple[Path, int, str]]:
    found: list[tuple[Path, int, str]] = []
    for path in _sources():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in FEN_PATTERN.finditer(line):
                found.append((path, number, match.group(1)))
    return found


ALL_FENS = _fens()


def test_the_scanner_actually_finds_fens() -> None:
    """A scanner that matches nothing would pass this file silently."""
    assert len(ALL_FENS) > 100, f"only found {len(ALL_FENS)} FENs; the pattern is probably broken"


@pytest.mark.parametrize(
    ("path", "line", "fen"),
    ALL_FENS,
    ids=[f"{p.name}:{n}" for p, n, _ in ALL_FENS],
)
def test_every_fixture_is_a_legal_position(path: Path, line: int, fen: str) -> None:
    if fen in DELIBERATELY_INVALID:
        assert not chess.Board(fen).is_valid(), (
            f"{fen} is listed as deliberately invalid but is legal; "
            "remove it from DELIBERATELY_INVALID"
        )
        return
    board = chess.Board(fen)
    assert board.is_valid(), f"{path.name}:{line} {fen}: {board.status()!r}"


def test_no_fixture_has_adjacent_kings() -> None:
    """Named separately because it is the failure that keeps recurring."""
    offenders = []
    for path, line, fen in ALL_FENS:
        if fen in DELIBERATELY_INVALID:
            continue
        board = chess.Board(fen)
        white = board.king(chess.WHITE)
        black = board.king(chess.BLACK)
        if white is None or black is None:
            continue
        if chess.square_distance(white, black) <= 1:
            offenders.append(f"{path.name}:{line} {fen}")
    assert not offenders, "kings on adjacent squares:\n" + "\n".join(offenders)


def test_deliberately_invalid_list_is_not_stale() -> None:
    """Every entry must still appear somewhere, or the list is misleading."""
    seen = {fen for _, _, fen in ALL_FENS}
    unused = DELIBERATELY_INVALID - seen
    assert not unused, f"listed as deliberately invalid but no longer used: {sorted(unused)}"
