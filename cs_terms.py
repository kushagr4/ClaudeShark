"""Registry of optional positional terms: one place to switch a term on, measure it, or ship it.

The evaluator proper (``cs_eval``) is material plus piece-square tables, the
bishop pair and tempo. Everything positional beyond that is a *term*: a
function of the board that returns White's-point-of-view centipawns, with a
transparently written reference twin the fast version is tested against.
Terms are independent of one another by construction -- each reads the
board, none reads another term -- so one can be enabled, measured and
benchmarked without touching the rest.

A term enters the evaluation at one of two stages:

* ``packed``: a middlegame/endgame pair in the evaluator's packed format
  ``(mg << 16) + eg``, added before the taper so it is phased exactly like
  the piece-square tables. This is where almost every term belongs. A
  middlegame-only term packs ``(mg << 16)``; that is numerically identical
  to adding to the middlegame total after the split.
* ``post``: whole centipawns added after the taper. Only for terms whose
  positions are endgames by definition and whose gradient must not be
  diluted (the bare-king mop-up). Not equivalent to ``packed`` with
  ``mg == eg`` in every case, because the final division truncates the sum,
  so the stage is part of a term's definition and is recorded here.

Which terms are active is decided once at import from the environment --
each term's own variable (``CS_EVAL_PASSED=1``) or the list
``CS_EVAL_TERMS=passed,mopup`` -- and can be changed at runtime with
``cs_eval.set_terms`` for tests and tools. Shipped defaults are the
``DEFAULTS`` table below and nothing else; the competition process sets no
variables, so what ships is what that table says.

Adding a term: write the module with a fast function and a reference
function, add one ``Term`` line here and one ``DEFAULTS`` entry, and
``tests/test_terms.py`` will check its colour antisymmetry, its
fast/reference agreement on random positions and that the evaluator with
the term off is untouched. ``tools/v2/termbench.py`` measures its cost,
activation frequency and effect on the calibration set.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

import chess

from cs_king import king_safety_mg, king_safety_mg_reference
from cs_mopup import mop_up, mop_up_reference
from cs_passed import passed_pawns_packed, passed_pawns_reference

# Shipped defaults. Edit this table to ship a term; nothing else decides it.
DEFAULTS: dict[str, bool] = {
    "king_safety": False,
    "mopup": False,
    "passed": False,
}


@dataclass(frozen=True)
class Term:
    name: str
    flag: str  # environment variable that switches this term alone
    stage: str  # "packed" or "post"
    fast: Callable[[chess.Board], int]  # packed: (mg << 16) + eg; post: centipawns. White's view.
    reference: Callable[[chess.Board], tuple[int, int] | int]  # packed: (mg, eg); post: centipawns


def _king_safety_packed(board: chess.Board) -> int:
    return king_safety_mg(board) << 16


def _king_safety_reference(board: chess.Board) -> tuple[int, int]:
    return king_safety_mg_reference(board), 0


TERMS: tuple[Term, ...] = (
    Term("king_safety", "CS_EVAL_KING_SAFETY", "packed",
         _king_safety_packed, _king_safety_reference),
    Term("mopup", "CS_EVAL_MOPUP", "post", mop_up, mop_up_reference),
    Term("passed", "CS_EVAL_PASSED", "packed", passed_pawns_packed, passed_pawns_reference),
)
BY_NAME: dict[str, Term] = {term.name: term for term in TERMS}
assert set(DEFAULTS) == set(BY_NAME), "every term needs a shipped default and vice versa"


def _truthy(raw: str) -> bool:
    return raw.strip().lower() not in {"", "0", "false", "no", "off"}


def enabled_from_environment() -> frozenset[str]:
    """The set of term names the environment (or the shipped defaults) switches on."""
    names: set[str] = set()
    for term in TERMS:
        raw = os.environ.get(term.flag)
        if DEFAULTS[term.name] if raw is None else _truthy(raw):
            names.add(term.name)
    listed = os.environ.get("CS_EVAL_TERMS", "")
    for name in listed.split(","):
        name = name.strip()
        if not name:
            continue
        if name not in BY_NAME:
            raise ValueError(
                f"CS_EVAL_TERMS names an unknown term {name!r}; known: {sorted(BY_NAME)}")
        names.add(name)
    return frozenset(names)


def unpack(packed: int) -> tuple[int, int]:
    """Split a packed (mg << 16) + eg value the way the evaluator does."""
    eg = packed & 0xFFFF
    if eg >= 0x8000:
        eg -= 0x10000
    return (packed - eg) >> 16, eg
