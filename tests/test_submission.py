"""Packaging tests.

The engine is split across several modules, so the thing that would quietly
break a submission is a module that does not make it into the zip. These tests
build the real archive with the official packager and then play a game out of
the extracted copy, through the official harness.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import chess

from harness.package import DEFAULT_INCLUDES, build
from harness.referee import play_match
from harness.rules import MAX_UNZIPPED_BYTES
from harness.sandbox import local

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {
    "agent.py",
    "cs_constants.py",
    "cs_eval.py",
    "cs_ordering.py",
    "cs_search.py",
    "cs_time.py",
    "cs_tt.py",
}


def _build(tmp_path: Path) -> Path:
    archive = tmp_path / "submission.zip"
    build(ROOT, archive, DEFAULT_INCLUDES)
    return archive


def test_every_engine_module_is_packaged(tmp_path: Path) -> None:
    with zipfile.ZipFile(_build(tmp_path)) as archive:
        names = set(archive.namelist())
    missing = EXPECTED - names
    assert not missing, f"the submission would ship without {sorted(missing)}"
    assert "agent.py" in names, "the platform imports agent.py by name from the zip root"


def test_submission_is_well_under_the_size_cap(tmp_path: Path) -> None:
    unzipped = sum(path.stat().st_size for path in ROOT.glob("*.py"))
    assert unzipped < MAX_UNZIPPED_BYTES


def test_no_forbidden_dependency_is_imported(tmp_path: Path) -> None:
    """The agent must not pull in a third-party engine, or the network."""
    forbidden = ("stockfish", "lc0", "leela", "maia", "socket", "urllib", "requests", "httpx")
    for path in ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for name in forbidden:
            assert f"import {name}" not in source, f"{path.name} imports {name}"


def test_the_extracted_zip_plays_a_real_game(tmp_path: Path) -> None:
    """The submission has to work from the extracted archive, not the repo."""
    extracted = tmp_path / "submission"
    with zipfile.ZipFile(_build(tmp_path)) as archive:
        archive.extractall(extracted)

    outcome = play_match(
        local(extracted),
        local(ROOT / "baselines" / "random"),
        base_ms=3_000,
        increment_ms=50,
        ply_cap=40,
        start_fen=chess.STARTING_FEN,
    )
    assert outcome.termination not in {"crash", "illegal", "flag", "init", "both_failed"}, (
        f"the packaged submission failed: {outcome.termination}"
    )
