"""Shared fixtures.

The evaluator's active-term set is process state and must not leak between tests.
"""

from __future__ import annotations

import os

# The legacy suite exercises the interpreted search in cs_search directly;
# the compiled core has its own tests (tests/test_core.py).
os.environ.setdefault("CS_CORE", "python")

import pytest  # noqa: E402

import cs_eval
import cs_terms


@pytest.fixture(autouse=True)
def _restore_evaluation_terms():
    before = cs_eval.ACTIVE_TERMS
    yield
    if before != cs_eval.ACTIVE_TERMS:
        cs_eval.set_terms(before)
    # And never let a test leave the shipped defaults switched on.
    assert cs_terms.enabled_from_environment() == cs_eval.ACTIVE_TERMS
