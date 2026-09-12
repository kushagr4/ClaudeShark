# ClaudeShark: Windows → macOS migration

Everything needed to reconstruct the project on a Mac at exactly the state the Windows machine
is in. Nothing here starts research: C28 stays at pre-adjudication repair, no Stockfish runs, no
games, no training, no push.

## 0. What must survive, in one line each

| | |
|---|---|
| **5 local commits that are not on GitHub** | `.git` must be copied as files; a `git clone` loses them |
| **13 untracked C28 files** | not committed, not on GitHub, and not in a `git bundle` |
| **RC-J release archive** | `corpus/release/claudeshark_rc_j.zip`, SHA-256 `c8226c03…22fb5`, never regenerated |
| **RC-J runtime identity** | the 16 engine modules stay byte-identical to `2bf6885` — no line-ending conversion |
| **Frozen N1 evidence** | weights, freeze manifest, gates, reports: historical, never rewritten |
| **External research data** | `ClaudeShark-data/` (111 MB) and the TWIC PGN issues (69 MB) |

## 1. Sizes and what is not transferred

| component | size | transfer |
|---|---|---|
| repository excluding `.venv` and caches (includes `.git` 34 MB) | **205 MB** | yes |
| `ClaudeShark-data/` (N1 pools, labels, pairs, holdout, scratch engines) | **111 MB** | yes |
| TWIC PGN issues, `C:\Users\epick\engines\twic` | **69 MB** | yes |
| **transfer total** | **≈ 385 MB** | |
| `.venv/` | 809 MB | **no** — rebuilt by `uv sync` |
| Windows Stockfish binary + its download zip | 114 MB + 77 MB | **no** — install a macOS build |
| `__pycache__`, `*.pyc`, Numba `*.nbi`/`*.nbc`, lint and test caches | — | **no** — rebuilt |
| `ClaudeShark-cleanup-20260911/` + `ClaudeShark-pre-cleanup-20260911.bundle` | 35 MB + 29 MB | optional recovery archives |

385 MB is small enough that any transport works; nothing needs a staged or resumable copy.

## 2. Build the transport package (on Windows)

```powershell
powershell -File migration\package_for_mac.ps1 -Mode Report    # sizes, copies nothing
powershell -File migration\package_for_mac.ps1 -Mode Full      # ~385 MB into ClaudeShark-Mac-Migration\
```

`-Mode Full` mirrors the repository (keeping `.git`, untracked files and ignored research files,
excluding `.venv` and caches), copies the external data and TWIC, drops in the manifests, the
bootstrap scripts and a `git bundle` of every ref, and writes `SHA256SUMS.txt`.

## 3. Transfer

**A. External SSD or USB.** Format the volume **exFAT or APFS**, not FAT32 (4 GB file limit) —
then copy `ClaudeShark-Mac-Migration\` to it and on the Mac:

```bash
cd /Volumes/<disk>/ClaudeShark-Mac-Migration
shasum -a 256 -c SHA256SUMS.txt | grep -v ': OK$' || echo "all files verified"
mkdir -p ~/Documents
rsync -a repo/ ~/Documents/ClaudeShark/
rsync -a external-data/ClaudeShark-data/ ~/Documents/ClaudeShark-data/
rsync -a external-data/twic/ ~/Documents/ClaudeShark-twic/
cd ~/Documents/ClaudeShark && git config --local core.autocrlf false && git checkout-index -a -f
```

That last line is not optional — see §3a.

**B. Network, straight from the originals** (no duplicate on Windows). Enable OpenSSH Server on
Windows, or run this from the Mac with the Windows shares mounted. Resumable and checksummed:

```bash
rsync -avz --partial --progress \
      --exclude '.venv/' --exclude '__pycache__/' --exclude '*.pyc' \
      --exclude '.pytest_cache/' --exclude '.ruff_cache/' --exclude '.mypy_cache/' \
      --exclude '*.nbi' --exclude '*.nbc' \
      epick@<windows-host>:/c/Users/epick/Documents/ClaudeShark/ ~/Documents/ClaudeShark/
rsync -avz --partial --progress \
      epick@<windows-host>:/c/Users/epick/Documents/ClaudeShark-data/ ~/Documents/ClaudeShark-data/
rsync -avz --partial --progress \
      epick@<windows-host>:/c/Users/epick/engines/twic/ ~/Documents/ClaudeShark-twic/
```

Re-running `rsync` after an interruption resumes, and `-a` preserves bytes exactly — which is
precisely why §3a is needed: the bytes on the Windows disk are not the canonical ones.

## 3a. Line endings: do this, or the byte-identity claim breaks

Measured on the Windows machine:

* the 16 production modules **as committed at `2bf6885`** and **as stored in
  `claudeshark_rc_j.zip`** are byte-identical to each other, with **LF** endings;
* the same 16 files **in the Windows working tree** carry **CRLF in 12 of them** (`agent.py`,
  `cs_core.py`, `cs_drawish.py`, `cs_eval.py`, `cs_fast.py`, `cs_king.py`, `cs_kingpawn.py`,
  `cs_ordering.py`, `cs_passed.py`, `cs_search.py`, `cs_terms.py`, `cs_time.py` — 4,690 CR bytes
  in `cs_core.py` alone). Git reports the tree as clean because Windows has
  `core.autocrlf=true` at **system** scope and converts on the way in and out.

So a faithful byte-for-byte copy of the Windows working tree gives the Mac **CRLF files that do
not match the shipped release**, and with `core.autocrlf=false` on the Mac git would then show 12
modified files — inviting exactly the line-ending-only commit that is forbidden.

The fix, after any copy method, is one command that rewrites the working tree from the committed
blobs (tracked files are unmodified, so nothing is lost):

```bash
cd ~/Documents/ClaudeShark
git config --local core.autocrlf false
git checkout-index -a -f
```

Verify:

```bash
for f in agent.py cs_core.py cs_search.py cs_eval.py cs_tt.py; do
  git show 2bf6885:$f | cmp -s - $f && echo "OK   $f" || echo "DIFF $f"
done
```

`bootstrap_mac.sh` does this automatically (step 10b) and `verify_mac_port.py` checks all 16
files on disk against the `2bf6885` blobs.

**C. Single archive.** `tar` preserves bytes and is safe for the production sources:

```powershell
tar -cf ClaudeShark-migration.tar -C C:\Users\epick\Documents\ClaudeShark-Mac-Migration .
certutil -hashfile ClaudeShark-migration.tar SHA256
```

Do **not** use GitHub for the external research data, and do not push the unfinished C28 work.

## 4. Bootstrap the Mac

```bash
cd ~/Documents/ClaudeShark
export CLAUDESHARK_DATA_ROOT="$HOME/Documents/ClaudeShark-data"
bash migration/bootstrap_mac.sh --check-only    # report first, install nothing
bash migration/bootstrap_mac.sh                 # install and verify
```

It detects macOS and the architecture, finds the data root, installs `uv` if absent, runs
`uv sync`, checks imports, clears the Windows `__pycache__`/Numba caches, locates Stockfish and
records its hash, sets the repository-local git identity and `core.autocrlf false`, runs
`verify_mac_port.py`, then the unit tests and the cross-platform evaluator comparison. It starts
no research.

**Architecture note.** `uv.lock` carries macOS wheels for `torch`, `numba`, `llvmlite` and
`onnxruntime` **only for arm64**. On Apple Silicon `uv sync` resolves from the lock unchanged. On
an Intel Mac it would have to re-resolve and `torch 2.13.0+cpu` may have no macOS x86_64 build at
all; report that rather than editing `uv.lock`. The engine itself never imports torch — it is used
only by `train_n1.py` — so an Intel Mac could still run everything except N1 training.

## 5. Stockfish

| | |
|---|---|
| version | **Stockfish 18**, official release build |
| Windows binary | `stockfish-windows-x86-64-avx2.exe`, SHA-256 `c86215fa1977d53b82ed854540a4c7b025be4cd042276c85ba3de53fb9118911` |
| research options | `Threads 1`, `Hash 32` (learned-evaluation lane; 256 in the older corpus oracle), `UCI_ShowWDL true`, `ucinewgame` before every search, fixed-node limits |
| Mac requirement | a **macOS build of the same release**; ARM64 on Apple Silicon |

Install from <https://stockfishchess.org/download/> (macOS ARM64) or `brew install stockfish`, then
check the version it actually gives you — Homebrew tracks its own release and will not necessarily
be 18. Set `CLAUDESHARK_STOCKFISH` to the binary.

**The Mac hash will differ from the Windows hash. That is expected provenance, not corruption.**
Record engine version, platform, architecture and binary hash together. Historical label manifests
keep the Windows hash and are never relabelled; new labels record the Mac hash.

## 6. Verify

```bash
cd ~/Documents/ClaudeShark
.venv/bin/python migration/verify_mac_port.py --stockfish "$CLAUDESHARK_STOCKFISH"
.venv/bin/python migration/make_reference.py --out /tmp/reference_mac.json
.venv/bin/python migration/make_reference.py --compare migration/reference_windows.json /tmp/reference_mac.json
.venv/bin/python -m pytest -q tests
```

`verify_mac_port.py` reports OS, architecture, Python, uv, Git HEAD, branch/tag/stash/worktree
counts, working-tree status, the RC-J ZIP hash, RC-J production-source identity, the N1 frozen
artefacts, the external-data manifests, the C28 pre-adjudication state, whether any C28 oracle
output exists (expected: none), Stockfish provenance, and heavy jobs (expected: 0).

`make_reference.py --compare` requires **exact equality** on `e0`, `e1`, `n1q_cp`, `qs_e0`,
`qs_n1q`, the Zobrist key, the packed piece-square value and the legal-move count, and `1e-6`
centipawns on the two float quantities (`e1_correction`, `n1_float_cp`). That tolerance is fixed
in the script now, before any Mac number exists.

**If anything differs, investigate it — never edit the fixture to match.**

### Windows baselines, measured 2026-09-12

| | |
|---|---|
| `pytest -q tests` | **1486 passed** in 192 s |
| reference fixture | **59 positions**, `values_sha256` `49badbe2dbfa4d44b64e4175d9c8a8cef703fc2e4903c70f79e59caf34cf57e0` |
| `verify_mac_port.py` on Windows | every check passes **except** `RC-J runtime bytes on disk` (4/16 — the CRLF issue of §3a) |

On the Mac, after `git checkout-index -a -f`, `RC-J runtime bytes on disk` must read **16/16** and
the whole report must be `ALL CHECKS PASS`. The fixture comparison must print `PASS 59 positions
identical`; the test count should be 1486 (a different count means tests were skipped, not that
the engine changed — check the skip reasons).

## 7. Optional: the deterministic node fingerprint

Not part of the bootstrap because it is a benchmark. On an idle Mac:

```bash
.venv/bin/python -m tools.bench --depth 10
```

RC-J's recorded depth-10 total over the 24 balanced openings is **16,818,635 nodes**. Node identity
should be invariant across platforms when the semantics are identical; wall-clock and NPS will not
be. A different node count is a real finding: investigate before doing anything else, and do not
rewrite the expected value.

## 8. Paths that are not portable

Nothing in the shipped engine hardcodes a path. The absolute Windows paths that exist fall into
four classes, and the migration deliberately changes only the third:

| class | where | action |
|---|---|---|
| **A. historical evidence** | `benchmarks/current/{c12_mate,c15v2_passer,combined}/*`, `rcj_loss_autopsy/wf/*` and `scripts/*`, `corpus/strength/rcf/review/*` — one-off lane scripts that hardcode the session directory they ran in (the autopsy README already says so) | preserve as historical text; they are not re-runnable and were not re-runnable on Windows either |
| **B. runtime configuration** | `tools/corpus/oracle.py` (`ORACLE_DEFAULT`), `learned_eval/scripts/sf_label.py` (`SF_DEFAULT`), `learned_eval/scripts/build_pool.py` (`TWIC_DIR`), `learned_eval/scripts/test_features.py` / `test_evalkit.py` (`POOL`), `hard_position_mining/scripts/c28paths.py` (`DATA`, `DATA_LE`, `TWIC_DIR`, `SF_PATH`) | **must be made configurable** — see below |
| **C. provenance inside results** | `results/**/*.json`, `*.meta.json`, `candidates_labelled.jsonl`, `speed_n1.json`, `classification.json` | preserve exactly; they record where the measurement was made |
| **D. scratch** | `SCRATCH` in the C28 test files; session temp directories | replace with a temp directory at repair time |

The class-B change is small and mechanical: read the location from an environment variable with the
current value as the default. It has **not** been applied yet, because it touches `c28paths.py`,
which is part of the C28 repair Codex is re-auditing, and mixing a portability edit into that
review would confuse the audit. Apply it as its own isolated commit after the migration:

```python
DATA_ROOT = os.environ.get("CLAUDESHARK_DATA_ROOT",
                           os.path.expanduser("~/Documents/ClaudeShark-data"))
TWIC_DIR  = os.environ.get("CLAUDESHARK_TWIC", os.path.expanduser("~/Documents/ClaudeShark-twic"))
SF_PATH   = os.environ.get("CLAUDESHARK_STOCKFISH", shutil.which("stockfish") or "")
```

No chess logic changes. `benchmarks/current/rcj_loss_autopsy/scripts/sf_scan.py` also refers to
`ClaudeShark/scratch/gameplay_research_20260910/public`, which **does not exist on this machine**
(`scratch/` is gitignored and was cleared in the 2026-09-11 cleanup); the autopsy's outputs in
`data/` are the record, and that script is class A.

## 8a. External locations on the Mac: the three variables

Nothing that runs may depend on a Windows path or on a username. Every external location is a
variable with a `$HOME`-relative default:

| variable | default | holds |
|---|---|---|
| `CLAUDESHARK_DATA_ROOT` | `~/Documents/ClaudeShark-data` | N1 pools, labels, pairs, holdout, scratch engines |
| `CLAUDESHARK_TWIC` | `~/Documents/ClaudeShark-twic` | the TWIC PGN issues |
| `CLAUDESHARK_STOCKFISH` | first `stockfish` on `PATH` | the macOS Stockfish binary |

```bash
export CLAUDESHARK_DATA_ROOT="$HOME/Documents/ClaudeShark-data"
export CLAUDESHARK_TWIC="$HOME/Documents/ClaudeShark-twic"
export CLAUDESHARK_STOCKFISH="$(command -v stockfish)"
```

`bootstrap_mac.sh` reads and validates all three (step 3 and step 9), `verify_mac_port.py` reads
`CLAUDESHARK_DATA_ROOT` and `CLAUDESHARK_STOCKFISH`, and `make_manifest.py` reads
`CLAUDESHARK_DATA_ROOT` and `CLAUDESHARK_TWIC`. The migration tooling is therefore fully portable.

**Known gap, reported rather than patched.** The *research* scripts still carry the Windows TWIC
path as their default:

* `benchmarks/current/learned_eval/scripts/build_pool.py` → `TWIC_DIR = "C:/Users/epick/engines/twic"`
* `benchmarks/current/hard_position_mining/scripts/c28paths.py` → `TWIC_DIR`, `DATA`, `DATA_LE`, `SF_PATH`

`c28paths.py` belongs to C28, which is frozen for repair and under independent re-audit, so it has
deliberately **not** been touched — changing it now would mix a portability edit into that review.
Both files must be switched to the variables above as part of the C28 repair, in their own isolated
commit. `bootstrap_mac.sh` prints a warning naming each file that still holds the Windows default,
so the gap cannot be forgotten. Until then, C28 tooling would not find the corpus on the Mac — which
is correct, because C28 must not run until it is repaired and re-reviewed anyway.

## 9. Git on the Mac

```bash
git config --local user.name kushagr4
git config --local user.email ratrakushagra@gmail.com
git config --local core.autocrlf false
git config --local core.filemode false      # keeps a Windows-created tree from showing mode churn
```

Repository-local only; do not touch the global config. There is no `.gitattributes`, and Windows
has `core.autocrlf=true` at **system** scope while the repository has it unset — so the Mac must
set it to `false` locally, or a future checkout could rewrite line endings and break the
byte-identity claim on the production sources. Never commit a line-ending-only change.

`main` is the only branch, there are no tags, no stashes and one worktree. Keep it that way: no
migration branch, no tag, no squash, no rebase, no amend. **Do not push** — 5 local commits are
ahead of `origin/main` and the C28 work is unfinished; the user decides when anything reaches
GitHub.

## 10. Where C28 resumes

C28 is in **pre-adjudication repair**: an independent review returned BLOCK on implementation
defects. Nothing has been adjudicated.

* `DESIGN_C28.md` is a **draft**, deliberately not committed and not frozen.
* 12 scripts exist; **`test_normalise.py` is missing** — the agent writing the capture-tree
  module and its normalisation test was interrupted before creating it. That, and the review's
  other findings, are the repair backlog.
* No pool has been built, no position scored, no selection frozen, no Stockfish query made. The
  external C28 directory contains three empty folders and nothing else.
* The sealed confirmation pool does not exist yet and has never been inspected.

After migration the order is unchanged: **repair → second independent review → only after PASS,
freeze the preregistration → pools → selection → oracle.** Do not skip forward, and do not let the
Mac start from the GitHub version, which has none of this work.
