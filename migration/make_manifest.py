"""Build MIGRATION_MAC_MANIFEST.json: every component that must reach the Mac, with its class.

Classification (the brief's categories):

  A_GIT            the .git directory: local commits that are not on GitHub live only here
  B_TRACKED        tracked working-tree files
  C_UNTRACKED_REQ  untracked or ignored files that are research state and must migrate
  D_EXTERNAL_DATA  research data outside the repository
  E_RELEASE        canonical release artefacts and the production runtime identity
  F_REGENERABLE    machine-specific, rebuilt on the Mac, never transported
  G_SECRET         credentials: never packaged; variable names only

Individual SHA-256 hashes are recorded for the artefacts whose identity is the point (the release
archive, the production runtime sources, the frozen N1 artefacts, the C28 pre-adjudication
sources, the external-data manifests). Bulk data directories are covered by a directory digest
(the sorted list of relative path, size and SHA-256 of every file, hashed) rather than by listing
every file inline.

    python migration/make_manifest.py [--out migration/MIGRATION_MAC_MANIFEST.json]
                                      [--data-root C:/Users/epick/Documents/ClaudeShark-data]
                                      [--quick]   (skip the bulk directory digests)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DATA_ROOT = os.environ.get("CLAUDESHARK_DATA_ROOT",
                                   os.path.join(os.path.dirname(ROOT), "ClaudeShark-data"))
DEFAULT_TWIC = os.environ.get("CLAUDESHARK_TWIC", "C:/Users/epick/engines/twic")
DEFAULT_SF_DIR = "C:/Users/epick/engines/stockfish"

RELEASE_ZIP = "corpus/release/claudeshark_rc_j.zip"
RELEASE_ZIP_SHA256 = "c8226c03164e70454d4a1c03c72f3a253912616386dc415e2b6f140b05122fb5"
RCJ_SOURCE_COMMIT = "2bf6885"
SF_WINDOWS_SHA256 = "c86215fa1977d53b82ed854540a4c7b025be4cd042276c85ba3de53fb9118911"
SF_VERSION = "Stockfish 18"

# The engine modules that make up the shipped runtime, exactly the set inside the release archive.
RUNTIME_FILES = ("agent.py", "cs_constants.py", "cs_core.py", "cs_drawish.py", "cs_eval.py",
                 "cs_fast.py", "cs_king.py", "cs_kingpawn.py", "cs_mopup.py", "cs_ordering.py",
                 "cs_passed.py", "cs_search.py", "cs_see.py", "cs_terms.py", "cs_time.py",
                 "cs_tt.py")

N1_ARTEFACTS = (
    "benchmarks/current/learned_eval/results/n1/n1_weights.npz",
    "benchmarks/current/learned_eval/results/n1/n1_weights.json",
    "benchmarks/current/learned_eval/results/n1/freeze.json",
    "benchmarks/current/learned_eval/results/n1/calibration.json",
    "benchmarks/current/learned_eval/results/n1/selection.json",
    "benchmarks/current/learned_eval/results/n1/acceptance.json",
    "benchmarks/current/learned_eval/results/n1/magnitude_audit.json",
    "benchmarks/current/learned_eval/results/n1/test_gates.json",
    "benchmarks/current/learned_eval/results/n1/speed_n1.json",
    "benchmarks/current/learned_eval/results/n1/holdout.json",
    "benchmarks/current/learned_eval/results/n1/engine_checks_frozen.json",
    "benchmarks/current/learned_eval/DESIGN_N1.md",
    "benchmarks/current/learned_eval/REPORT_N1.md",
    "benchmarks/current/learned_eval/results/e1_weights.json",
)

REGENERABLE = (
    (".venv/", "Windows virtual environment: uv sync rebuilds it from uv.lock"),
    ("**/__pycache__/", "CPython bytecode"),
    ("**/*.pyc", "CPython bytecode"),
    (".pytest_cache/", "pytest cache"),
    (".ruff_cache/ .mypy_cache/", "linter and type-checker caches"),
    ("**/.numba_cache/ **/*.nbi **/*.nbc", "Numba JIT caches: x86-64 machine code, invalid on arm64"),
    ("ClaudeShark-data/learned_eval/**/engines/**/__pycache__/",
     "bytecode of the N1 scratch engines; the .py sources beside them are kept"),
    (DEFAULT_SF_DIR + "/stockfish-windows-x86-64-avx2.exe",
     "Windows Stockfish binary: a macOS build of the same release is installed instead"),
    ("C:/Users/epick/engines/sf18-avx2.zip", "Windows Stockfish download archive"),
)

SECRET_VARIABLES = (
    dict(name="(none required)",
         note="No credential, token or key is read by any engine, tool or research script. "
              "GitHub access uses the user's own git credential helper on each machine."),
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def entry(logical: str, source: str, cls: str, portable: bool, regenerate: bool,
          historical: bool, note: str = "", want_hash: bool = True) -> dict:
    row = dict(logical_path=logical, source_windows_path=source.replace("\\", "/"),
               classification=cls, portable_directly=portable, regenerate_on_mac=regenerate,
               historical_artifact=historical)
    if note:
        row["note"] = note
    if os.path.isfile(source):
        row["exists"] = True
        row["size"] = os.path.getsize(source)
        if want_hash:
            row["sha256"] = sha256_file(source)
    elif os.path.isdir(source):
        row["exists"] = True
        row["is_directory"] = True
    else:
        row["exists"] = False
    return row


def dir_digest(path: str, skip_names: tuple[str, ...] = ("__pycache__",)) -> dict:
    """Size, file count and a digest over (relative path, size, sha256) of every file."""
    if not os.path.isdir(path):
        return dict(exists=False)
    files, total = [], 0
    for base, dirs, names in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip_names]
        for n in sorted(names):
            full = os.path.join(base, n)
            rel = os.path.relpath(full, path).replace("\\", "/")
            size = os.path.getsize(full)
            total += size
            files.append((rel, size, sha256_file(full)))
    files.sort()
    digest = hashlib.sha256(
        "\n".join(f"{r}\t{s}\t{h}" for r, s, h in files).encode()).hexdigest()
    return dict(exists=True, files=len(files), bytes=total,
                megabytes=round(total / (1 << 20), 2), tree_sha256=digest)


def git(*args: str) -> str:
    return subprocess.run(("git", *args), cwd=ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, "migration", "MIGRATION_MAC_MANIFEST.json"))
    ap.add_argument("--data-root", default=DEFAULT_DATA_ROOT)
    ap.add_argument("--twic", default=DEFAULT_TWIC)
    ap.add_argument("--quick", action="store_true", help="skip the bulk directory digests")
    args = ap.parse_args()
    t0 = time.perf_counter()

    untracked = [ln[3:].strip('"') for ln in
                 git("status", "--porcelain", "--untracked-files=all").splitlines()
                 if ln.startswith("??")]
    ignored_all = [ln[3:].strip('"') for ln in
                   git("status", "--porcelain", "--ignored=matching",
                       "--untracked-files=all").splitlines() if ln.startswith("!!")]
    cache_marks = (".venv/", "__pycache__/", ".pytest_cache/", ".ruff_cache/", ".mypy_cache/",
                   ".numba_cache/")
    ignored_required = [p for p in ignored_all if not any(m in p for m in cache_marks)]

    components: list[dict] = []

    components.append(dict(
        logical_path=".git/", source_windows_path=os.path.join(ROOT, ".git").replace("\\", "/"),
        classification="A_GIT", portable_directly=True, regenerate_on_mac=False,
        historical_artifact=False,
        note="Carries the local commits that are not on GitHub. Transfer as files; a clone of "
             "origin/main would lose them.",
        head=git("rev-parse", "HEAD"), branch=git("rev-parse", "--abbrev-ref", "HEAD"),
        unpushed_commits=git("log", "origin/main..HEAD", "--oneline").splitlines(),
        tags=git("tag").splitlines(), stashes=git("stash", "list").splitlines(),
        worktrees=[ln for ln in git("worktree", "list").splitlines()],
        **({} if args.quick else {"size": dir_digest(os.path.join(ROOT, ".git"))["bytes"]})))

    components.append(entry("corpus/release/claudeshark_rc_j.zip",
                            os.path.join(ROOT, RELEASE_ZIP), "E_RELEASE", True, False, True,
                            "Canonical submitted archive. Must keep SHA-256 "
                            f"{RELEASE_ZIP_SHA256}. Never regenerate, never repack."))

    for name in RUNTIME_FILES:
        components.append(entry(name, os.path.join(ROOT, name), "E_RELEASE", True, False, False,
                                f"Production runtime; byte-identical to {RCJ_SOURCE_COMMIT}. "
                                "No line-ending conversion."))

    for rel in N1_ARTEFACTS:
        components.append(entry(rel, os.path.join(ROOT, rel), "B_TRACKED", True, False, True,
                                "Frozen N1 evidence: never rewritten on the Mac."))

    self_rel = os.path.relpath(os.path.abspath(args.out), ROOT).replace("\\", "/")
    for rel in sorted(untracked):
        if rel == self_rel:
            continue  # the manifest cannot hash itself: writing it changes the hash
        if rel.startswith("migration/"):
            note = ("Migration tooling written for this move; untracked until the user approves "
                    "the commit. Transfers with the working tree either way.")
        else:
            note = ("C28 pre-adjudication source: not committed, not on GitHub, and not contained "
                    "in a git bundle. Must be transferred with the working tree.")
        components.append(entry(rel, os.path.join(ROOT, rel), "C_UNTRACKED_REQ", True, False,
                                False, note))

    for rel in sorted(ignored_required):
        src = os.path.join(ROOT, rel)
        components.append(entry(rel, src, "C_UNTRACKED_REQ", True, False, True,
                                "Ignored by .gitignore but part of the research record.",
                                want_hash=os.path.isfile(src) and os.path.getsize(src) < (32 << 20)))

    data_root = args.data_root
    components.append(dict(
        logical_path="${CLAUDESHARK_DATA_ROOT}", source_windows_path=data_root.replace("\\", "/"),
        classification="D_EXTERNAL_DATA", portable_directly=True, regenerate_on_mac=False,
        historical_artifact=True,
        note="External research data: N1 pools, labels, pairs, holdout, scratch engines. "
             "Mac default ~/Documents/ClaudeShark-data, overridable with CLAUDESHARK_DATA_ROOT.",
        digest=dict(exists=os.path.isdir(data_root)) if args.quick else dir_digest(data_root)))

    components.append(dict(
        logical_path="twic/", source_windows_path=args.twic,
        classification="D_EXTERNAL_DATA", portable_directly=True, regenerate_on_mac=False,
        historical_artifact=False,
        note="The Week in Chess PGN issues: the game source for the N1 pool and for C28's fresh "
             "pools. Referenced by build_pool.py and c28paths.py.",
        digest=dict(exists=os.path.isdir(args.twic)) if args.quick else dir_digest(args.twic)))

    for pattern, why in REGENERABLE:
        components.append(dict(logical_path=pattern, source_windows_path=pattern,
                               classification="F_REGENERABLE", portable_directly=False,
                               regenerate_on_mac=True, historical_artifact=False, note=why))

    stockfish = dict(
        classification="F_REGENERABLE", engine=SF_VERSION,
        windows_binary=DEFAULT_SF_DIR + "/stockfish-windows-x86-64-avx2.exe",
        windows_sha256=SF_WINDOWS_SHA256,
        windows_build="official release build stockfish-windows-x86-64-avx2",
        note="Do not copy the Windows executable to the Mac. Install the macOS build of the same "
             "release (arm64 on Apple Silicon). The Mac SHA-256 will differ: that is expected "
             "provenance, not corruption. Historical label manifests keep the Windows hash; new "
             "labels record the Mac hash.",
        required_options=dict(Threads=1, Hash=32, UCI_ShowWDL=True,
                              state="ucinewgame before every search", limit="fixed nodes"))
    if os.path.isfile(stockfish["windows_binary"]):
        stockfish["windows_size"] = os.path.getsize(stockfish["windows_binary"])

    res = dict(
        schema="claudeshark-mac-migration/1",
        created=time.strftime("%Y-%m-%d %H:%M:%S"),
        source_machine=dict(system=platform.system(), release=platform.release(),
                            machine=platform.machine(), python=sys.version.split()[0],
                            repo=ROOT.replace("\\", "/"), data_root=data_root.replace("\\", "/")),
        policy=dict(branches_expected=["main"], tags_expected=0, stashes_expected=0,
                    worktrees_expected=1, push="never without explicit authorisation",
                    git_user_name="kushagr4", git_user_email="ratrakushagra@gmail.com",
                    ai_attribution="never"),
        release=dict(zip=RELEASE_ZIP, sha256=RELEASE_ZIP_SHA256,
                     runtime_source_commit=RCJ_SOURCE_COMMIT, runtime_files=list(RUNTIME_FILES)),
        stockfish=stockfish,
        secrets=list(SECRET_VARIABLES),
        counts=dict(untracked=len(untracked), ignored_non_cache=len(ignored_required),
                    components=len(components)),
        components=components,
    )
    res["manifest_body_sha256"] = hashlib.sha256(
        json.dumps(res["components"], sort_keys=True).encode()).hexdigest()
    res["seconds"] = round(time.perf_counter() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(dict(out=args.out, components=len(components),
                          untracked=len(untracked), ignored_non_cache=len(ignored_required),
                          manifest_body_sha256=res["manifest_body_sha256"],
                          seconds=res["seconds"]), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
