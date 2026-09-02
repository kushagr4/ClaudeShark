"""Benchmark-integrity tests for the arena.

Two classes of silent corruption are guarded here:

* an experiment flag left exported in the parent shell reaching **both**
  engines, changing the result while appearing nowhere in the record;
* a match running at all on a corpus containing an illegal position.

Both had happened, in some form, before these existed.
"""

from __future__ import annotations

import os

import pytest

from tools.arena import (
    COMPETITION_PLY_CAP,
    KNOWN_CS_VARS,
    build_schedule,
    sanitise_environment,
    snapshot_identity,
)
from tools.positions import BALANCED_OPENINGS, invalid_positions


@pytest.fixture(autouse=True)
def _restore_environment():
    saved = {k: v for k, v in os.environ.items() if k.startswith("CS_") or k == "CLAUDESHARK_DEBUG"}
    yield
    for name in list(os.environ):
        if name.startswith("CS_") or name == "CLAUDESHARK_DEBUG":
            del os.environ[name]
    os.environ.update(saved)


def test_stray_parent_variable_is_stripped() -> None:
    """A forgotten export must not reach the engines."""
    os.environ["CS_LMR"] = "0"
    os.environ["CS_SEE_QS"] = "0"
    report = sanitise_environment({})
    assert "CS_LMR" not in os.environ
    assert "CS_SEE_QS" not in os.environ
    assert set(report["stripped"]) >= {"CS_LMR", "CS_SEE_QS"}
    assert report["effective"] == {}


def test_requested_variables_are_set_and_recorded() -> None:
    os.environ["CS_LMR"] = "0"  # stray, must go
    report = sanitise_environment({"CS_INCREMENT_MS": "200"})
    assert os.environ["CS_INCREMENT_MS"] == "200"
    assert "CS_LMR" not in os.environ
    assert report["effective"] == {"CS_INCREMENT_MS": "200"}
    assert "CS_LMR" in report["stripped"]


def test_every_known_variable_is_reported_when_set() -> None:
    """The record must be able to state every flag actually in force."""
    allow = {name: "1" for name in KNOWN_CS_VARS}
    report = sanitise_environment(allow)
    assert set(report["effective"]) == set(KNOWN_CS_VARS)


def test_debug_flag_is_also_controlled() -> None:
    """CLAUDESHARK_DEBUG prints from inside the search and would skew timing."""
    os.environ["CLAUDESHARK_DEBUG"] = "1"
    report = sanitise_environment({})
    assert "CLAUDESHARK_DEBUG" not in os.environ
    assert "CLAUDESHARK_DEBUG" in report["stripped"]


def test_arena_would_refuse_an_invalid_corpus() -> None:
    """The precondition the arena checks before playing anything."""
    assert invalid_positions() == []


def test_default_ply_cap_matches_the_competition() -> None:
    assert COMPETITION_PLY_CAP == 300


def test_schedule_pairs_colours_on_the_same_position() -> None:
    """Every cluster must be played once with each colour."""
    schedule = build_schedule(len(BALANCED_OPENINGS) * 2, BALANCED_OPENINGS)
    by_cluster: dict[int, list[bool]] = {}
    for spec in schedule:
        by_cluster.setdefault(spec.cluster, []).append(spec.agent_is_white)
    assert len(by_cluster) == len(BALANCED_OPENINGS)
    for cluster, colours in by_cluster.items():
        assert sorted(colours) == [False, True], f"cluster {cluster} is not colour-paired"


def test_schedule_uses_the_position_its_cluster_names() -> None:
    for spec in build_schedule(96, BALANCED_OPENINGS):
        assert spec.fen == BALANCED_OPENINGS[spec.cluster]


def test_snapshot_identity_is_stable_and_distinguishing(tmp_path) -> None:
    """A record names exact code by content, not by directory name."""
    from pathlib import Path

    one = Path("champions/v0_3")
    two = Path("champions/v0_3_sf60")
    assert snapshot_identity(one) == snapshot_identity(one)
    assert snapshot_identity(one) != snapshot_identity(two), (
        "variants differing by one constant must hash differently"
    )
