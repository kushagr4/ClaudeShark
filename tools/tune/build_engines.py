"""Materialise the three deterministic candidates as engine directories.

Baseline, the one-parameter material scale and the ten-parameter fit, each
as a complete agent directory under `corpus/tune/engines/`, so the standard
benchmark and arena tooling can address them like any frozen champion. They are
derived artefacts, rebuilt by this script, and are not tracked.

    uv run python -m tools.tune.build_engines
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.tune.simulate import patched_engine

PRODUCTION_MG = [82, 337, 365, 477, 1025]
PRODUCTION_EG = [94, 281, 297, 512, 936]
OUT = Path("corpus/tune/engines")


def main() -> None:
    candidates = json.loads(
        Path("corpus/tune/material_candidates.json").read_text(encoding="utf-8")
    )
    scale_key = next(k for k in candidates if k.startswith("scale "))
    built = {
        "baseline": (PRODUCTION_MG, PRODUCTION_EG),
        "scale": (candidates[scale_key]["mg"], candidates[scale_key]["eg"]),
        "tenparam": (candidates["quiet (tol 30)"]["mg"], candidates["quiet (tol 30)"]["eg"]),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (mg, eg) in built.items():
        patched_engine(mg, eg, OUT / name)
        print(f"{name:<10} MG {mg}  EG {eg}")


if __name__ == "__main__":
    main()
