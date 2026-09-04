"""Single-writer ownership for experiment output files.

Twice in one session two independent match processes were started against the
same output path. The first time it corrupted a JSONL -- one process opened the
file for writing, truncating what the other had produced, and both then appended
through their own handles, leaving one torn line and a silently mixed record
set. The artifact was retained as evidence and discarded as data. The second
time it was caught before any game was written.

Relying on the operator to notice is not a control. This module makes the
runner enforce it: a match acquires ownership of its output path **before any
game starts**, and a second root process asking for the same path fails closed
with an explanatory error rather than quietly interleaving.

The mechanism is an ``O_CREAT | O_EXCL`` sidecar next to the output file, which
is atomic on every filesystem this project runs on -- unlike "check whether the
file exists, then create it", which has a window between the two. The sidecar
records who owns the path, so a refusal can say which process to look at.

A stale sidecar left by a killed process is **never removed automatically**.
Deleting an owner record on the assumption that its process is gone is exactly
how the first incident would have been re-enabled. Recovery is explicit:
``--force-unlock`` refuses unless the recorded process is genuinely dead, and it
touches only the sidecar, never the data file.

    with own(output_path, argv):
        ...write games...
"""

from __future__ import annotations

import contextlib
import ctypes
import json
import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path

SUFFIX = ".owner"

_SYNCHRONIZE = 0x00100000
_WAIT_TIMEOUT = 0x00000102


class OutputBusyError(RuntimeError):
    """Raised when another live process already owns the output path."""


def sidecar_for(output: Path) -> Path:
    return output.with_name(output.name + SUFFIX)


def process_is_alive(pid: int) -> bool:
    """Best-effort liveness. Errs toward 'alive', because refusing is the safe failure."""
    if pid <= 0:
        return False
    if os.name == "nt":
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.OpenProcess(_SYNCHRONIZE, False, pid)
        if not handle:
            # No handle: either the process is gone or we may not query it.
            # ERROR_ACCESS_DENIED (5) means it exists and is not ours.
            return ctypes.get_last_error() == 5 or kernel32.GetLastError() == 5
        try:
            return kernel32.WaitForSingleObject(handle, 0) == _WAIT_TIMEOUT
        finally:
            kernel32.CloseHandle(handle)
    try:
        # Signal 0 performs the permission and existence check without delivering
        # anything. This branch is never taken on Windows, where os.kill would
        # terminate the process instead.
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_owner(output: Path) -> dict | None:
    path = sidecar_for(output)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # An unreadable owner record is still an owner record. Fail closed.
        return {"pid": -1, "command": "<unreadable owner record>", "started": None}


def acquire(output: Path, command: list[str] | None = None) -> Path:
    """Take ownership of ``output``. Raises OutputBusyError if someone else has it."""
    output.parent.mkdir(parents=True, exist_ok=True)
    path = sidecar_for(output)
    record = {
        "pid": os.getpid(),
        "command": " ".join(command if command is not None else sys.argv),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "output": str(output),
    }
    payload = json.dumps(record, indent=1).encode("utf-8")
    try:
        handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        existing = read_owner(output) or {}
        pid = int(existing.get("pid", -1) or -1)
        alive = process_is_alive(pid)
        state = "still running" if alive else "no longer running"
        raise OutputBusyError(
            f"{output} is already owned by pid {pid} ({state}).\n"
            f"  owner command: {existing.get('command')}\n"
            f"  owner started: {existing.get('started')}\n"
            f"  owner record:  {path}\n"
            + ("Stop that process, or write to a different --out path."
               if alive else
               "The owning process is gone. Re-run with --force-unlock to take over; "
               "the data file itself is never touched by that flag.")
        ) from None
    with os.fdopen(handle, "wb") as fh:
        fh.write(payload)
    return path


def release(output: Path) -> None:
    """Drop ownership if this process holds it. Never removes someone else's record."""
    record = read_owner(output)
    if record and record.get("pid") == os.getpid():
        with contextlib.suppress(OSError):
            sidecar_for(output).unlink()


def force_unlock(output: Path) -> str:
    """Explicit recovery. Refuses while the recorded process is alive."""
    record = read_owner(output)
    if record is None:
        return f"no owner record for {output}"
    pid = int(record.get("pid", -1) or -1)
    if process_is_alive(pid):
        raise OutputBusyError(
            f"refusing to unlock {output}: the owning process (pid {pid}) is still running.\n"
            f"  owner command: {record.get('command')}"
        )
    sidecar_for(output).unlink()
    return (f"removed the stale owner record of pid {pid} for {output}"
            " (the data file was not touched)")


@contextlib.contextmanager
def own(output: Path, command: list[str] | None = None, force: bool = False) -> Iterator[Path]:
    """Own ``output`` for the duration of the block."""
    if force:
        with contextlib.suppress(OutputBusyError):
            print(force_unlock(output), file=sys.stderr)
    path = acquire(output, command)
    try:
        yield path
    finally:
        release(output)
