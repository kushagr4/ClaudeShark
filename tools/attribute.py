"""Attribute the search features: which of PVS, null-move and LMR actually pay?

Runs every variant as a subprocess with the ``CS_*`` feature flags set, so all
variants are the same code and cannot drift apart the way hand-edited copies
would.

The primary measurement is deliberately **fixed depth, not fixed time**. At a
fixed depth every variant does the same nominal work, so the node count is a
clean, deterministic, machine-independent measure of how much the pruning
actually saves. A time-limited run would measure the laptop as much as the
engine, and would reward a feature for reaching a bigger depth number without
asking whether the moves got better.

Tactical solve count is reported alongside, because saving nodes by skipping the
move that wins is not a saving.

    uv run python -m tools.attribute --depth 6
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass

# name -> (PVS, null move, LMR)
VARIANTS: tuple[tuple[str, tuple[bool, bool, bool]], ...] = (
    ("baseline (v0.1 search)", (False, False, False)),
    ("PVS only", (True, False, False)),
    ("null-move only", (False, True, False)),
    ("LMR only", (False, False, True)),
    ("PVS + null-move", (True, True, False)),
    ("PVS + LMR", (True, False, True)),
    ("null-move + LMR", (False, True, True)),
    ("all three (v0.2)", (True, True, True)),
)


@dataclass
class Result:
    name: str
    nodes: int
    seconds: float
    solved: int
    extra: str = ""


def _env(pvs: bool, nmp: bool, lmr: bool, **overrides: str) -> dict[str, str]:
    environment = dict(os.environ)
    environment["CS_PVS"] = "1" if pvs else "0"
    environment["CS_NMP"] = "1" if nmp else "0"
    environment["CS_LMR"] = "1" if lmr else "0"
    environment.update(overrides)
    return environment


def _run(arguments: list[str], environment: dict[str, str]) -> str:
    completed = subprocess.run(
        [sys.executable, "-m", *arguments],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"{' '.join(arguments)} failed:\n{completed.stdout}\n{completed.stderr}")
    return completed.stdout


def _measure(name: str, environment: dict[str, str], depth: int, tactics_ms: int) -> Result:
    bench = _run(["tools.bench", "--depth", str(depth)], environment)
    nodes = int(re.search(r"total nodes\s+([\d,]+)", bench).group(1).replace(",", ""))
    seconds = float(re.search(r"time in search\s+([\d.]+)s", bench).group(1))

    tactics = _run(["tools.tactics", "--ms", str(tactics_ms), "--quiet"], environment)
    solved = int(re.search(r"solved (\d+)/", tactics).group(1))

    return Result(name=name, nodes=nodes, seconds=seconds, solved=solved)


def main() -> None:
    parser = argparse.ArgumentParser(description="Attribute the v0.2 search features.")
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--tactics-ms", type=int, default=1_000)
    parser.add_argument(
        "--lmr-safe",
        action="store_true",
        help="also measure the check-aware LMR variant against plain LMR",
    )
    arguments = parser.parse_args()

    variants = list(VARIANTS)
    results: list[Result] = []

    for name, flags in variants:
        result = _measure(name, _env(*flags), arguments.depth, arguments.tactics_ms)
        results.append(result)
        print(
            f"{result.name:<24} nodes {result.nodes:>10,}  "
            f"{result.seconds:>6.1f}s  tactics {result.solved}/13",
            flush=True,
        )

    if arguments.lmr_safe:
        for label, safe in (("v0.2 + safe LMR", "1"),):
            result = _measure(
                label, _env(True, True, True, CS_LMR_SAFE=safe), arguments.depth,
                arguments.tactics_ms,
            )
            results.append(result)
            print(
                f"{result.name:<24} nodes {result.nodes:>10,}  "
                f"{result.seconds:>6.1f}s  tactics {result.solved}/13",
                flush=True,
            )

    baseline = results[0]
    print(f"\nfixed depth {arguments.depth}, 24 positions. Fewer nodes is better at equal depth.")
    print(f"{'variant':<24} {'nodes':>11} {'vs baseline':>12} {'time':>8} {'tactics':>8}")
    for result in results:
        change = 100.0 * (result.nodes - baseline.nodes) / baseline.nodes
        print(
            f"{result.name:<24} {result.nodes:>11,} {change:>11.1f}% "
            f"{result.seconds:>7.1f}s {result.solved:>6}/13"
        )


if __name__ == "__main__":
    main()
