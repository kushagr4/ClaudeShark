"""Fixed-size transposition table.

Backed by a preallocated list rather than a growing dict so memory is bounded
by construction: the platform gives us 2 GB and a long game would otherwise
accumulate millions of entries. Keys are ``hash(board._transposition_key())``,
a 64-bit digest of an exact position descriptor (piece bitboards, side to move,
castling rights, legal en passant square).

Each slot holds ``(key, depth, score, bound, move)``. Because the full key is
stored alongside, an index collision between two positions is detected instead
of silently returning a wrong score; only a genuine 64-bit hash collision can
slip through, which is the usual engine trade.
"""

from __future__ import annotations

import chess

from cs_constants import MATE_BOUND, MATE_SCORE

Entry = tuple[int, int, int, int, chess.Move | None]

# 2**19 slots is roughly 50-60 MB when saturated, which leaves ample headroom
# inside the 2 GB cap while still being large enough that a 120 s game does not
# thrash it.
DEFAULT_BITS = 19


class TranspositionTable:
    __slots__ = ("_mask", "_slots", "collisions", "hits", "probes", "stores")

    def __init__(self, bits: int = DEFAULT_BITS) -> None:
        self._mask = (1 << bits) - 1
        self._slots: list[Entry | None] = [None] * (1 << bits)
        self.probes = 0
        self.hits = 0
        self.stores = 0
        self.collisions = 0

    def clear(self) -> None:
        self._slots = [None] * (self._mask + 1)
        self.probes = self.hits = self.stores = self.collisions = 0

    def reset_stats(self) -> None:
        self.probes = self.hits = self.stores = self.collisions = 0

    def probe(self, key: int) -> Entry | None:
        entry = self._slots[key & self._mask]
        if entry is not None and entry[0] == key:
            return entry
        return None

    def store(self, key: int, depth: int, score: int, bound: int, move: chess.Move | None) -> None:
        index = key & self._mask
        entry = self._slots[index]
        # Depth-preferred within a position, always-replace across positions:
        # a shallow entry for a position we are no longer searching is dead
        # weight, but a deeper entry for this position is worth keeping.
        if entry is not None and entry[0] == key and entry[1] > depth:
            return
        self._slots[index] = (key, depth, score, bound, move)


def score_to_tt(score: int, ply: int) -> int:
    """Convert a mate score from "distance from root" to "distance from node".

    A mate score is only meaningful relative to where it was found, so it has to
    be stored ply-independently or a transposition at a different depth will
    report the wrong mate distance.
    """
    if score > MATE_BOUND:
        return score + ply
    if score < -MATE_BOUND:
        return score - ply
    return score


def score_from_tt(score: int, ply: int) -> int:
    """Inverse of :func:`score_to_tt`."""
    if score > MATE_BOUND:
        return score - ply
    if score < -MATE_BOUND:
        return score + ply
    return score


def mate_in(score: int) -> int | None:
    """Full moves to mate for a mate score, negative if we are being mated."""
    if score > MATE_BOUND:
        return (MATE_SCORE - score + 1) // 2
    if score < -MATE_BOUND:
        return -((MATE_SCORE + score + 1) // 2)
    return None
