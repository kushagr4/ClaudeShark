"""Freeze the current engine as a champion, to be used as an arena opponent.

A champion directory is a complete, standalone agent: ``agent.py`` plus the
``cs_*`` modules, exactly as they would be zipped. The harness puts the
directory first on ``sys.path`` and imports ``agent`` from it, so a frozen
champion keeps running its own code even after the working tree moves on.

    uv run python -m tools.freeze v0_1
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAMPIONS = ROOT / "champions"


def submission_files(root: Path) -> list[Path]:
    """The files the official packager would ship: every ``*.py`` at the root."""
    return sorted(root.glob("*.py"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Snapshot the engine as a champion.")
    parser.add_argument("name", help="champion directory name, e.g. v0_1")
    parser.add_argument("--force", action="store_true", help="overwrite an existing champion")
    arguments = parser.parse_args()

    destination = CHAMPIONS / arguments.name
    if destination.exists():
        if not arguments.force:
            raise SystemExit(
                f"{destination} already exists. A frozen champion is a reference point; "
                f"pass --force only if you really mean to move it."
            )
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    files = submission_files(ROOT)
    if not any(path.name == "agent.py" for path in files):
        raise SystemExit("no agent.py at the repository root")
    for path in files:
        shutil.copy2(path, destination / path.name)

    print(f"froze {len(files)} files into {destination.relative_to(ROOT)}")
    for path in files:
        print(f"  {path.name}")


if __name__ == "__main__":
    main()
