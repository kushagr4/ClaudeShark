"""Verify a migrated ClaudeShark checkout. Read-only: it starts nothing and changes nothing.

Runs on either machine. On the Mac it answers one question: is this checkout the same scientific
state as the source machine, with only the differences a platform change legitimately produces?

    python migration/verify_mac_port.py [--manifest migration/MIGRATION_MAC_MANIFEST.json]
                                        [--reference migration/reference_windows.json]
                                        [--json OUT.json] [--stockfish PATH]

It never runs Stockfish, never adjudicates, never opens the sealed C28 confirmation pool, never
pushes and never modifies the working tree. A Mac Stockfish hash that differs from the recorded
Windows hash is reported as expected provenance, not as a failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SF_WINDOWS_SHA256 = "c86215fa1977d53b82ed854540a4c7b025be4cd042276c85ba3de53fb9118911"
RELEASE_ZIP = "corpus/release/claudeshark_rc_j.zip"
RELEASE_ZIP_SHA256 = "c8226c03164e70454d4a1c03c72f3a253912616386dc415e2b6f140b05122fb5"
RCJ_SOURCE_COMMIT = "2bf6885"
C28_DIR = "benchmarks/current/hard_position_mining"
C28_ORACLE_MARKS = ("oracle_1m.jsonl", "oracle_4m.jsonl", "classified_1m.jsonl",
                    "classified_4m.jsonl", "tasks_4m.jsonl")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(("git", *args), cwd=ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.checks: dict[str, dict] = {}
        self.failed = 0

    def info(self, label: str, value: object) -> None:
        self.lines.append(f"{label + ':':<34}{value}")
        self.checks[label] = dict(status="INFO", value=value)

    def check(self, label: str, ok: bool, value: object = "", note: str = "") -> None:
        status = "PASS" if ok else "FAIL"
        if not ok:
            self.failed += 1
        text = f"{label + ':':<34}{status}"
        if value != "":
            text += f"  {value}"
        if note:
            text += f"  ({note})"
        self.lines.append(text)
        self.checks[label] = dict(status=status, value=value, note=note)

    def expected(self, label: str, value: object, note: str) -> None:
        self.lines.append(f"{label + ':':<34}EXPECTED DIFFERENT  {value}  ({note})")
        self.checks[label] = dict(status="EXPECTED_DIFFERENT", value=value, note=note)


def data_root() -> str:
    env = os.environ.get("CLAUDESHARK_DATA_ROOT")
    if env:
        return os.path.expanduser(env)
    return os.path.join(os.path.dirname(ROOT), "ClaudeShark-data")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--manifest", default=os.path.join(ROOT, "migration",
                                                       "MIGRATION_MAC_MANIFEST.json"))
    ap.add_argument("--reference", default=os.path.join(ROOT, "migration",
                                                        "reference_windows.json"))
    ap.add_argument("--stockfish", default=os.environ.get("CLAUDESHARK_STOCKFISH", ""))
    ap.add_argument("--json", default="")
    args = ap.parse_args()
    r = Report()

    r.info("OS", f"{platform.system()} {platform.release()}")
    r.info("architecture", platform.machine())
    r.info("Python", sys.version.split()[0])
    uv = shutil.which("uv")
    r.info("uv", subprocess.run([uv, "--version"], capture_output=True, text=True,
                                check=False).stdout.strip() if uv else "NOT FOUND")
    r.info("repository", ROOT)
    r.info("data root", data_root())

    # ---------------------------------------------------------------- repository state
    r.info("Git HEAD", git("rev-parse", "HEAD"))
    r.info("Git HEAD subject", git("log", "-1", "--format=%s"))
    branches = [b for b in git("branch", "--format=%(refname:short)").splitlines() if b]
    tags = [t for t in git("tag").splitlines() if t]
    stashes = [s for s in git("stash", "list").splitlines() if s]
    worktrees = [w for w in git("worktree", "list").splitlines() if w]
    r.check("branch count", len(branches) == 1 and branches[:1] == ["main"], branches)
    r.check("tags", len(tags) == 0, len(tags))
    r.check("stashes", len(stashes) == 0, len(stashes))
    r.check("worktrees", len(worktrees) == 1, len(worktrees))
    author = f"{git('config', '--get', 'user.name')} <{git('config', '--get', 'user.email')}>"
    r.check("git identity", author == "kushagr4 <ratrakushagra@gmail.com>", author)
    modified = [ln for ln in git("status", "--porcelain").splitlines() if not ln.startswith("??")]
    r.check("tracked files unmodified", not modified, f"{len(modified)} modified",
            "line-ending or content drift" if modified else "")
    r.info("untracked entries", len([ln for ln in git("status", "--porcelain",
                                                      "--untracked-files=all").splitlines()
                                     if ln.startswith("??")]))

    # ---------------------------------------------------------------- release identity
    zip_path = os.path.join(ROOT, RELEASE_ZIP)
    if os.path.isfile(zip_path):
        got = sha256_file(zip_path)
        r.check("RC-J ZIP hash", got == RELEASE_ZIP_SHA256, got,
                "STOP and report; do not regenerate" if got != RELEASE_ZIP_SHA256 else "")
    else:
        r.check("RC-J ZIP hash", False, "MISSING")

    runtime = ("agent.py", "cs_constants.py", "cs_core.py", "cs_drawish.py", "cs_eval.py",
               "cs_fast.py", "cs_king.py", "cs_kingpawn.py", "cs_mopup.py", "cs_ordering.py",
               "cs_passed.py", "cs_search.py", "cs_see.py", "cs_terms.py", "cs_time.py", "cs_tt.py")
    diff = git("diff", "--stat", RCJ_SOURCE_COMMIT, "HEAD", "--", *runtime)
    r.check("RC-J production-source identity", diff == "",
            f"committed blobs identical to {RCJ_SOURCE_COMMIT}"
            if diff == "" else diff.splitlines()[-1])

    # The stronger claim: the bytes on disk, not just the committed blobs. A tree copied from
    # Windows with core.autocrlf=true carries CRLF and fails this until it is re-materialised.
    crlf, differ = [], []
    for name in runtime:
        path = os.path.join(ROOT, name)
        if not os.path.isfile(path):
            differ.append(name)
            continue
        with open(path, "rb") as fh:
            disk = fh.read()
        blob = subprocess.run(("git", "show", f"{RCJ_SOURCE_COMMIT}:{name}"), cwd=ROOT,
                              capture_output=True, check=False).stdout
        if disk != blob:
            (crlf if disk.replace(b"\r\n", b"\n") == blob else differ).append(name)
    r.check("RC-J runtime bytes on disk", not crlf and not differ,
            f"{len(runtime) - len(crlf) - len(differ)}/{len(runtime)} byte-identical",
            (f"CRLF line endings in {len(crlf)} file(s): run "
             "`git config --local core.autocrlf false && git checkout-index -a -f`"
             if crlf else "") + (f" content differs: {differ}" if differ else ""))

    # ---------------------------------------------------------------- manifest hashes
    if os.path.isfile(args.manifest):
        with open(args.manifest, encoding="utf-8") as fh:
            man = json.load(fh)
        bad, checked, missing = [], 0, 0
        for c in man.get("components", []):
            if "sha256" not in c or c.get("classification") == "F_REGENERABLE":
                continue
            p = os.path.join(ROOT, c["logical_path"])
            if not os.path.isfile(p):
                missing += 1
                continue
            checked += 1
            if sha256_file(p) != c["sha256"]:
                bad.append(c["logical_path"])
        r.check("manifest hashes", not bad, f"{checked} verified, {len(bad)} differ, "
                                            f"{missing} not in this tree",
                ", ".join(bad[:5]))
        n1 = [c for c in man.get("components", [])
              if c.get("historical_artifact") and "results/n1/" in c.get("logical_path", "")]
        n1_bad = [c["logical_path"] for c in n1
                  if "sha256" in c and os.path.isfile(os.path.join(ROOT, c["logical_path"]))
                  and sha256_file(os.path.join(ROOT, c["logical_path"])) != c["sha256"]]
        r.check("N1 frozen artifacts", not n1_bad, f"{len(n1)} listed", ", ".join(n1_bad[:5]))
    else:
        r.check("manifest hashes", False, "manifest not found", args.manifest)

    # ---------------------------------------------------------------- external data
    droot = data_root()
    if os.path.isdir(droot):
        n1_pool = os.path.join(droot, "learned_eval", "n1", "pool.jsonl")
        r.check("external-data manifests", os.path.isfile(n1_pool),
                "learned_eval/n1/pool.jsonl present" if os.path.isfile(n1_pool) else "MISSING")
    else:
        r.check("external-data manifests", False, f"data root missing: {droot}")

    # ---------------------------------------------------------------- C28 state
    c28 = os.path.join(ROOT, C28_DIR)
    design = os.path.join(c28, "DESIGN_C28.md")
    scripts = os.path.join(c28, "scripts")
    n_scripts = len([f for f in os.listdir(scripts) if f.endswith(".py")]) if os.path.isdir(scripts) else 0
    r.check("C28 pre-adjudication state", os.path.isfile(design) and n_scripts >= 12,
            f"DESIGN_C28.md {'present' if os.path.isfile(design) else 'MISSING'}, "
            f"{n_scripts} scripts")
    found = []
    for base in (os.path.join(droot, "hard_position_mining"), c28):
        for walk_base, _dirs, names in os.walk(base) if os.path.isdir(base) else []:
            for n in names:
                if n in C28_ORACLE_MARKS:
                    found.append(os.path.join(walk_base, n))
    r.check("C28 oracle outputs present", not found,
            "EXPECTED NONE" if not found else f"UNEXPECTED: {found[:3]}")
    sealed = os.path.join(droot, "hard_position_mining", "c28", "sealed")
    sealed_n = len(os.listdir(sealed)) if os.path.isdir(sealed) else 0
    r.info("C28 sealed confirmation pool", f"{sealed_n} entries (not inspected)")

    # ---------------------------------------------------------------- Stockfish provenance
    sf = args.stockfish or shutil.which("stockfish") or ""
    if sf and os.path.isfile(sf):
        r.info("Stockfish path", sf)
        r.info("Stockfish Mac SHA", sha256_file(sf))
        r.info("historical Windows Stockfish SHA", SF_WINDOWS_SHA256)
        r.expected("Stockfish binary hash", "differs from Windows",
                   "same release, different platform build; historical labels keep the Windows hash")
    else:
        r.info("Stockfish path", "not configured (set CLAUDESHARK_STOCKFISH or --stockfish)")

    # ---------------------------------------------------------------- numerical equivalence
    if os.path.isfile(args.reference):
        with open(args.reference, encoding="utf-8") as fh:
            ref = json.load(fh)
        r.info("reference fixture", f"{len(ref.get('positions', []))} positions from "
                                    f"{ref.get('platform', {}).get('system')} "
                                    f"{ref.get('platform', {}).get('machine')}")
        r.info("reference comparison", "run: python migration/make_reference.py --out /tmp/ref_mac.json "
                                       "&& python migration/make_reference.py --compare "
                                       f"{os.path.relpath(args.reference, ROOT)} /tmp/ref_mac.json")
    else:
        r.info("reference fixture", "not present")

    # ---------------------------------------------------------------- heavy jobs
    busy = []
    try:
        out = subprocess.run(["ps", "-Ao", "comm="], capture_output=True, text=True, check=False).stdout
        busy = [ln.strip() for ln in out.splitlines()
                if "stockfish" in ln.lower() and "grep" not in ln.lower()]
    except Exception:
        pass
    r.check("heavy jobs", not busy, f"{len(busy)} Stockfish process(es)", ", ".join(busy[:3]))

    print("CLAUDESHARK MAC PORT VERIFICATION")
    print("=" * 72)
    for ln in r.lines:
        print(ln)
    print("=" * 72)
    print(f"RESULT: {'ALL CHECKS PASS' if r.failed == 0 else str(r.failed) + ' CHECK(S) FAILED'}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(dict(failed=r.failed, checks=r.checks), fh, indent=1)
    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main())
