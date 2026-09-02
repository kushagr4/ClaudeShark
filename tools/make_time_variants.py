"""Generate time-policy variants of a frozen champion.

A controlled experiment needs the candidates to differ in exactly one thing.
Hand-copying a directory and editing it does not prove that; this does. Each
variant is produced by copying the base champion and substituting a single
constant, and the tool then **verifies** that the only textual difference
between base and variant is that one line, refusing to write anything otherwise.

    uv run python -m tools.make_time_variants --base champions/v0_3 \
        --constant START_FRACTION --values 0.60 0.75

Produces champions/v0_3_sf60 and champions/v0_3_sf75.
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def patch(source: str, constant: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(constant)}\s*=\s*.+$", re.MULTILINE)
    if not pattern.search(source):
        raise SystemExit(f"{constant} not found as a module-level assignment")
    return pattern.sub(f"{constant} = {value}", source, count=1)


def differing_lines(before: str, after: str) -> list[str]:
    diff = difflib.unified_diff(
        before.splitlines(), after.splitlines(), lineterm="", n=0
    )
    return [
        line
        for line in diff
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Make single-constant time variants.")
    parser.add_argument("--base", type=Path, default=Path("champions/v0_3"))
    parser.add_argument("--module", default="cs_time.py")
    parser.add_argument("--constant", default="START_FRACTION")
    parser.add_argument("--values", nargs="+", required=True)
    parser.add_argument("--suffix", default="sf", help="directory suffix prefix")
    arguments = parser.parse_args()

    base = (ROOT / arguments.base).resolve()
    if not (base / "agent.py").is_file():
        raise SystemExit(f"{base} is not an agent directory")
    original = (base / arguments.module).read_text(encoding="utf-8")

    for value in arguments.values:
        tag = value.replace("0.", "").replace(".", "")
        destination = base.parent / f"{base.name}_{arguments.suffix}{tag}"
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(base, destination)

        patched = patch(original, arguments.constant, value)
        changed = differing_lines(original, patched)
        # Exactly one line removed and one added, and nothing else anywhere.
        if len(changed) != 2:
            shutil.rmtree(destination)
            raise SystemExit(f"refusing to write {destination}: {len(changed)} lines differ")
        (destination / arguments.module).write_text(patched, encoding="utf-8")

        # Re-verify against what actually landed on disk, across every file.
        for path in sorted(base.rglob("*.py")):
            mirror = destination / path.relative_to(base)
            left = path.read_text(encoding="utf-8")
            right = mirror.read_text(encoding="utf-8")
            if left == right:
                continue
            lines = differing_lines(left, right)
            if path.name != arguments.module or len(lines) != 2:
                shutil.rmtree(destination)
                raise SystemExit(f"refusing to write {destination}: {path.name} differs")

        print(f"{destination.relative_to(ROOT)}: {arguments.constant} = {value}")
        for line in changed:
            print(f"    {line}")


if __name__ == "__main__":
    main()
