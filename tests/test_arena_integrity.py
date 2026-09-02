"""Benchmark-integrity tests for the arena.

Two classes of silent corruption are guarded here:

* an experiment flag left exported in the parent shell reaching **both**
  engines, changing the result while appearing nowhere in the record;
* a match running at all on a corpus containing an illegal position.

Both had happened, in some form, before these existed.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.arena import (
    COMPETITION_PLY_CAP,
    KNOWN_CS_VARS,
    build_schedule,
    sanitise_environment,
    snapshot_identity,
)
from tools.positions import BALANCED_OPENINGS, invalid_positions, unsuitable


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


# ------------------------------------------------- custom starting positions
#
# Validating only the built-in corpus was not enough: a custom --start-fen went
# through unchecked, so the arena could knowingly benchmark an illegal position.

OPPOSITE_CHECK = "8/2n2pk1/6p1/8/8/2B3P1/5P1P/6K1 w - - 0 40"
ALREADY_MATE = "R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1"
STALEMATED = "7k/5Q2/8/8/8/8/8/6K1 b - - 0 1"


@pytest.mark.parametrize(
    ("fen", "reason"),
    [
        (OPPOSITE_CHECK, "side not to move is in check"),
        (ALREADY_MATE, "already over"),
        (STALEMATED, "already over"),
        ("not a fen at all", "unparseable"),
        ("8/8/8/8/8/8/8/8 w - - 0 1", "no kings"),
    ],
)
def test_unsuitable_rejects_bad_starting_positions(fen: str, reason: str) -> None:
    bad = unsuitable((fen,), "--start-fen")
    assert bad, f"accepted an unsuitable position ({reason}): {fen}"


def test_unsuitable_accepts_the_real_corpus() -> None:
    assert unsuitable(BALANCED_OPENINGS, "corpus") == []


def test_arena_cli_rejects_an_invalid_start_fen() -> None:
    """End to end: the process must fail loudly, not skip quietly."""
    result = subprocess.run(
        [
            sys.executable, "-m", "tools.arena",
            "--agent", "champions/v0_3", "--opponent", "champions/v0_3",
            "--games", "2", "--start-fen", OPPOSITE_CHECK,
        ],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0, "the arena ran on an illegal position"
    combined = result.stdout + result.stderr
    assert "UNSUITABLE" in combined
    assert "OPPOSITE_CHECK" in combined


def test_arena_cli_rejects_an_unknown_set_env_name() -> None:
    result = subprocess.run(
        [
            sys.executable, "-m", "tools.arena",
            "--agent", "champions/v0_3", "--opponent", "champions/v0_3",
            "--games", "2", "--set-env", "PATH=/tmp",
        ],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "only accepts CS_*" in result.stdout + result.stderr


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


def test_known_vars_covers_every_flag_the_engine_reads() -> None:
    """The list is derived from the engine, not copied beside it.

    A hand-maintained copy had already fallen a flag behind:
    CS_SEE_KEEP_CHECKS took effect while matches recorded "effective: {}".
    """
    from cs_search import DECLARED_FLAGS
    from cs_time import DECLARED_VARS

    missing = (set(DECLARED_FLAGS) | set(DECLARED_VARS)) - set(KNOWN_CS_VARS)
    assert not missing, f"engine reads {sorted(missing)} but the arena would not record it"


@pytest.mark.parametrize(
    "name",
    [
        "CS_PVS",
        "CS_NMP",
        "CS_LMR",
        "CS_LMR_SAFE",
        "CS_ASPIRATION",
        "CS_TT_PV_CUTOFF",
        "CS_SEE_QS",
        "CS_SEE_ORDER",
        "CS_SEE_KEEP_CHECKS",
        "CS_INCREMENT_MS",
        "CLAUDESHARK_DEBUG",
    ],
)
def test_each_production_toggle_is_sanitised_and_recordable(name: str) -> None:
    """Every live toggle must be strippable when stray and recorded when set."""
    assert name in KNOWN_CS_VARS

    os.environ[name] = "1"
    stripped = sanitise_environment({})
    assert name not in os.environ, f"{name} survived sanitisation"
    assert name in stripped["stripped"]

    recorded = sanitise_environment({name: "1"})
    assert recorded["effective"].get(name) == "1", f"{name} missing from provenance"


def test_unknown_inherited_cs_variables_are_stripped() -> None:
    os.environ["CS_SOMETHING_INVENTED"] = "1"
    report = sanitise_environment({})
    assert "CS_SOMETHING_INVENTED" not in os.environ
    assert "CS_SOMETHING_INVENTED" in report["stripped"]


def test_snapshot_identity_is_stable_and_distinguishing(tmp_path) -> None:
    """A record names exact code by content, not by directory name."""
    from pathlib import Path

    one = Path("champions/v0_3")
    two = Path("champions/v0_3_sf60")
    assert snapshot_identity(one) == snapshot_identity(one)
    assert snapshot_identity(one) != snapshot_identity(two), (
        "variants differing by one constant must hash differently"
    )
