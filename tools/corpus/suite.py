"""Load a built suite (``corpus/*.jsonl``) as starting positions.

Kept free of engine imports so the arena can use it without pulling in the
oracle. A suite file is a header record followed by one record per position;
``load_suite`` returns the header and the FENs in file order, which is the
order the arena's cluster numbering follows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_suite(path: Path) -> tuple[dict[str, Any], tuple[str, ...]]:
    header: dict[str, Any] = {}
    fens: list[str] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("record") == "header":
                header = record
                continue
            fens.append(record["fen"])
    if not fens:
        raise ValueError(f"{path} contains no positions")
    return header, tuple(fens)
