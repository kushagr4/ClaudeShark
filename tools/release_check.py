"""Release gate: would I upload this exact tree to the live Chessathon now?

Builds the real submission with the official packager, extracts it to a
temporary directory, and then treats that directory as the only thing that
exists -- every runtime check runs in a subprocess against the extracted copy,
never against the working tree. A module that works in the repository but was
never packaged has to fail here, because that is exactly the failure the gate
exists to catch.

    uv run python -m tools.release_check
    uv run python -m tools.release_check --fast     # skip the pytest run

Exit status is 0 only if every check passes.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from harness.package import DEFAULT_INCLUDES, build

ROOT = Path(__file__).resolve().parent.parent

# docs/SPEC.md: "<= 50 MB unzipped". A reported 200 MB figure could not be
# confirmed; the stricter limit is deliberate. If the looser one is confirmed,
# this constant is the only thing that needs changing.
MAX_UNZIPPED_BYTES = 50_000_000
# Nothing we ship should come close. A file this large is an accident.
LARGE_FILE_BYTES = 5_000_000

# docs/SPEC.md: nothing installs at validation and a requirements.txt is
# ignored, so an import outside this set plus the standard library crashes the
# agent and loses the game.
PREINSTALLED = frozenset({"chess", "numpy", "torch", "onnxruntime", "numba"})

# Modules that only exist in development. Shipping an import of one of these is
# an instant crash on the platform.
DEV_ONLY = frozenset({"pytest", "ruff", "mypy", "tools", "harness", "tests", "_pytest"})

NETWORK_MODULES = frozenset(
    {
        "socket", "ssl", "urllib", "urllib2", "http", "httplib", "requests",
        "httpx", "ftplib", "smtplib", "telnetlib", "xmlrpc", "asyncio",
        "socketserver", "webbrowser",
    }
)

# Any of these appearing in shipped source means the agent might try to write
# somewhere. The filesystem is read-only apart from /tmp, and our agent writes
# nothing at all, so the strict rule is simply "no write APIs".
WRITE_APIS = ("open(", "write_text", "write_bytes", "mkdir", "makedirs", "NamedTemporaryFile")

# Executable file signatures: ELF, Mach-O (both endians, both widths), PE/COFF.
BINARY_MAGIC = (
    b"\x7fELF",
    b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf",
    b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe",
    b"MZ",
)
BINARY_SUFFIXES = frozenset({".so", ".pyd", ".dll", ".dylib", ".exe", ".a", ".o", ".bin"})

PROBE_FENS = (
    ("start (white)", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("middlegame (black)", "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 b - - 0 9"),
    ("endgame (white)", "8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 40"),
    ("endgame (black)", "8/5pk1/6p1/8/8/1R6/5PPP/6K1 b - - 0 40"),
    ("in check (white)", "4k3/8/8/8/7q/8/8/4K3 w - - 0 1"),
    ("promotion (white)", "8/4P1k1/8/8/8/8/6K1/8 w - - 0 1"),
    ("en passant (white)", "k7/8/8/3pP3/8/8/8/7K w - d6 0 2"),
    ("one legal move (black)", "7k/8/8/8/8/8/5Q2/6RK b - - 0 1"),
    # Terminal positions: no legal move exists, so "0000" is the correct answer
    # and anything else would be a malformed-output loss.
    ("checkmate (black)", "R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1"),
    ("stalemate (black)", "7k/5Q2/8/8/8/8/8/6K1 b - - 0 1"),
)
PROBE_CLOCKS = (1, 10, 50, 200, 1_000, 120_000)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def shipped_sources(extracted: Path) -> list[Path]:
    return sorted(extracted.rglob("*.py"))


def top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def check_contents(extracted: Path, names: list[str]) -> list[Check]:
    checks = []

    checks.append(
        Check("agent.py at zip root", "agent.py" in names,
              "the platform imports agent by name from the root")
    )

    expected = {path.name for path in ROOT.glob("cs_*.py")}
    missing = sorted(expected - set(names))
    checks.append(
        Check("engine modules packaged", not missing,
              f"missing from zip: {missing}" if missing else f"{len(expected)} cs_* modules")
    )

    unzipped = sum(path.stat().st_size for path in extracted.rglob("*") if path.is_file())
    checks.append(
        Check("expanded size within limit", unzipped <= MAX_UNZIPPED_BYTES,
              f"{unzipped:,} bytes of {MAX_UNZIPPED_BYTES:,}")
    )

    large = [
        f"{p.relative_to(extracted)} ({p.stat().st_size:,})"
        for p in extracted.rglob("*")
        if p.is_file() and p.stat().st_size > LARGE_FILE_BYTES
    ]
    checks.append(Check("no unexpectedly large files", not large, ", ".join(large) or "none"))

    binaries = []
    for path in extracted.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            binaries.append(f"{path.relative_to(extracted)} (suffix)")
            continue
        head = path.read_bytes()[:4]
        if any(head.startswith(magic) for magic in BINARY_MAGIC):
            binaries.append(f"{path.relative_to(extracted)} (magic)")
    checks.append(
        Check("no native binaries in zip", not binaries, ", ".join(binaries) or "source only")
    )

    return checks


def check_imports(extracted: Path) -> list[Check]:
    allowed = PREINSTALLED | set(sys.stdlib_module_names)
    shipped_names = {path.stem for path in shipped_sources(extracted)}

    unknown: set[str] = set()
    dev: set[str] = set()
    network: set[str] = set()
    for path in shipped_sources(extracted):
        for name in top_level_imports(path):
            if name in shipped_names:
                continue
            if name in DEV_ONLY:
                dev.add(f"{path.name}:{name}")
            if name in NETWORK_MODULES:
                network.add(f"{path.name}:{name}")
            if name not in allowed:
                unknown.add(f"{path.name}:{name}")

    return [
        Check("only preinstalled + stdlib imports", not unknown,
              ", ".join(sorted(unknown)) or "clean"),
        Check("no development-only imports", not dev, ", ".join(sorted(dev)) or "clean"),
        Check("no network imports", not network, ", ".join(sorted(network)) or "clean"),
    ]


def check_source_hygiene(extracted: Path) -> list[Check]:
    absolute: list[str] = []
    writes: list[str] = []
    for path in shipped_sources(extracted):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "C:\\" in line or "/home/" in line or "/Users/" in line:
                absolute.append(f"{path.name}:{line_number}")
            for api in WRITE_APIS:
                if api in line:
                    writes.append(f"{path.name}:{line_number} {api}")
    return [
        Check("no machine-specific absolute paths", not absolute,
              ", ".join(absolute) or "clean"),
        Check("no filesystem writes", not writes, ", ".join(writes) or "clean"),
    ]


PROBE = r"""
import json, sys, time
sys.path.insert(0, sys.argv[1])
import chess
import agent

results = []
for label, fen in json.loads(sys.argv[2]):
    for clock in json.loads(sys.argv[3]):
        started = time.perf_counter()
        uci = agent.get_move(fen, clock)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        board = chess.Board(fen)
        options = {m.uci() for m in board.legal_moves}
        # A terminal position has no legal move; the null move is the only
        # correct response and the referee ends the game on its own check.
        legal = (uci == "0000") if not options else (uci in options)
        results.append({
            "label": label, "clock": clock, "uci": uci,
            "legal": legal, "elapsed_ms": elapsed_ms,
        })
print(json.dumps(results))
"""


def check_runtime(extracted: Path) -> list[Check]:
    completed = subprocess.run(
        [
            sys.executable, "-c", PROBE, str(extracted),
            json.dumps([[label, fen] for label, fen in PROBE_FENS]),
            json.dumps(list(PROBE_CLOCKS)),
        ],
        capture_output=True, text=True, check=False, cwd=tempfile.gettempdir(),
    )
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout).strip()[-500:]
        return [Check("extracted zip imports and runs", False, tail)]

    results = json.loads(completed.stdout)
    illegal = [r for r in results if not r["legal"]]
    overruns = [
        f"{r['label']}@{r['clock']}ms took {r['elapsed_ms']:.0f}ms"
        for r in results
        if r["elapsed_ms"] > max(300.0, r["clock"] * 0.6)
    ]
    return [
        Check("extracted zip imports and runs", True, f"{len(results)} probes"),
        Check("legal move on every probe", not illegal,
              ", ".join(f"{r['label']}@{r['clock']}: {r['uci']}" for r in illegal) or "all legal"),
        Check("stays inside every clock", not overruns, ", ".join(overruns) or "all within budget"),
    ]


def check_smoke_game(extracted: Path) -> list[Check]:
    from harness.referee import play_match
    from harness.sandbox import local

    outcome = play_match(
        local(extracted), local(ROOT / "baselines" / "greedy"),
        base_ms=5_000, increment_ms=100, ply_cap=60,
    )
    bad = {"crash", "illegal", "flag", "init", "both_failed"}
    return [
        Check("smoke game from extracted zip", outcome.termination not in bad,
              f"{outcome.result} by {outcome.termination}")
    ]


def check_tests() -> list[Check]:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    summary = (completed.stdout.strip().splitlines() or ["no output"])[-1]
    return [Check("test suite", completed.returncode == 0, summary)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-upload release gate.")
    parser.add_argument("--fast", action="store_true", help="skip the pytest run")
    arguments = parser.parse_args()

    with tempfile.TemporaryDirectory() as workspace:
        archive = Path(workspace) / "submission.zip"
        names = build(ROOT, archive, DEFAULT_INCLUDES)
        extracted = Path(workspace) / "extracted"
        with zipfile.ZipFile(archive) as opened:
            opened.extractall(extracted)

        checks: list[Check] = []
        checks += check_contents(extracted, names)
        checks += check_imports(extracted)
        checks += check_source_hygiene(extracted)
        checks += check_runtime(extracted)
        checks += check_smoke_game(extracted)
        if not arguments.fast:
            checks += check_tests()

        zipped = archive.stat().st_size

    width = max(len(check.name) for check in checks)
    for check in checks:
        print(f"{'PASS' if check.ok else 'FAIL':<5} {check.name:<{width}}  {check.detail}")

    failed = [check for check in checks if not check.ok]
    print(f"\nsubmission.zip would be {zipped:,} bytes compressed")
    if failed:
        print(f"NOT READY TO UPLOAD: {len(failed)} check(s) failed")
        raise SystemExit(1)
    print("READY TO UPLOAD")


if __name__ == "__main__":
    main()
