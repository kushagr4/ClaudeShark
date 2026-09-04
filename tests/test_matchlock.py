"""Single-writer ownership of experiment output files.

These cover the failure that actually happened: two match roots pointed at one
JSONL, the second truncating and then interleaving with the first. The guard has
to refuse the second **before** any game is written, and it must never delete
the data file or another live process's ownership record to get out of the way.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.matchlock import (
    OutputBusyError,
    acquire,
    force_unlock,
    own,
    process_is_alive,
    read_owner,
    release,
    sidecar_for,
)


def test_first_writer_acquires_and_records_who_it_is(tmp_path: Path) -> None:
    out = tmp_path / "games.jsonl"
    path = acquire(out, ["python", "-m", "tools.postmortem.play", "--out", str(out)])
    try:
        assert path == sidecar_for(out)
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["pid"] == os.getpid()
        assert "tools.postmortem.play" in record["command"]
        assert record["started"]
        assert record["output"] == str(out)
    finally:
        release(out)


def test_second_writer_is_refused_while_the_first_is_alive(tmp_path: Path) -> None:
    out = tmp_path / "games.jsonl"
    acquire(out)
    try:
        with pytest.raises(OutputBusyError) as caught:
            acquire(out)
        message = str(caught.value)
        assert "already owned by pid" in message
        assert "still running" in message
    finally:
        release(out)


def test_different_output_paths_do_not_contend(tmp_path: Path) -> None:
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    acquire(a)
    acquire(b)
    try:
        assert sidecar_for(a).exists()
        assert sidecar_for(b).exists()
    finally:
        release(a)
        release(b)


def test_refusal_does_not_touch_the_data_file(tmp_path: Path) -> None:
    """The first incident destroyed data. A refusal must never write to the output."""
    out = tmp_path / "games.jsonl"
    out.write_text('{"game": 1}\n', encoding="utf-8")
    acquire(out)
    try:
        with pytest.raises(OutputBusyError):
            acquire(out)
        assert out.read_text(encoding="utf-8") == '{"game": 1}\n'
    finally:
        release(out)
    assert out.read_text(encoding="utf-8") == '{"game": 1}\n'


def test_a_stale_record_is_not_silently_reused(tmp_path: Path) -> None:
    """A dead owner still blocks; taking over has to be asked for explicitly."""
    out = tmp_path / "games.jsonl"
    sidecar_for(out).parent.mkdir(parents=True, exist_ok=True)
    dead = _a_pid_that_is_not_running()
    stale = json.dumps({"pid": dead, "command": "old run", "started": "then"})
    sidecar_for(out).write_text(stale, encoding="utf-8")
    with pytest.raises(OutputBusyError) as caught:
        acquire(out)
    assert "no longer running" in str(caught.value)
    assert "--force-unlock" in str(caught.value)
    assert sidecar_for(out).exists(), "the stale record must survive a refusal"


def test_force_unlock_recovers_a_stale_record_and_leaves_the_data(tmp_path: Path) -> None:
    out = tmp_path / "games.jsonl"
    out.write_text('{"game": 1}\n', encoding="utf-8")
    dead = _a_pid_that_is_not_running()
    stale = json.dumps({"pid": dead, "command": "old run", "started": "then"})
    sidecar_for(out).write_text(stale, encoding="utf-8")
    message = force_unlock(out)
    assert "stale owner record" in message
    assert not sidecar_for(out).exists()
    assert out.read_text(encoding="utf-8") == '{"game": 1}\n'
    acquire(out)
    release(out)


def test_force_unlock_refuses_while_the_owner_is_alive(tmp_path: Path) -> None:
    out = tmp_path / "games.jsonl"
    acquire(out)
    try:
        with pytest.raises(OutputBusyError) as caught:
            force_unlock(out)
        assert "still running" in str(caught.value)
        assert sidecar_for(out).exists()
    finally:
        release(out)


def test_own_releases_on_exit_and_on_failure(tmp_path: Path) -> None:
    out = tmp_path / "games.jsonl"
    with own(out):
        assert sidecar_for(out).exists()
    assert not sidecar_for(out).exists()
    with pytest.raises(ValueError), own(out):
        raise ValueError("the match failed")
    assert not sidecar_for(out).exists(), "a crash must not leave the path owned by this process"


def test_release_never_removes_another_process_record(tmp_path: Path) -> None:
    out = tmp_path / "games.jsonl"
    sidecar_for(out).parent.mkdir(parents=True, exist_ok=True)
    other = json.dumps({"pid": os.getpid() + 1, "command": "someone else"})
    sidecar_for(out).write_text(other, encoding="utf-8")
    release(out)
    assert sidecar_for(out).exists()


def test_an_unreadable_owner_record_still_blocks(tmp_path: Path) -> None:
    out = tmp_path / "games.jsonl"
    sidecar_for(out).parent.mkdir(parents=True, exist_ok=True)
    sidecar_for(out).write_text("not json at all", encoding="utf-8")
    assert read_owner(out) is not None
    with pytest.raises(OutputBusyError):
        acquire(out)


def test_liveness_recognises_this_process_and_a_finished_one() -> None:
    assert process_is_alive(os.getpid())
    finished = subprocess.run([sys.executable, "-c", "pass"], check=True)
    assert finished.returncode == 0
    assert not process_is_alive(_a_pid_that_is_not_running())


def _a_pid_that_is_not_running() -> int:
    """Start a process, wait for it, and reuse its identifier."""
    finished = subprocess.Popen([sys.executable, "-c", "pass"])
    finished.wait()
    return finished.pid
