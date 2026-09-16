#!/usr/bin/env bash
# Prepare a migrated ClaudeShark checkout on macOS. Conservative and idempotent: it installs the
# environment and verifies state, and it starts no research.
#
# It never: adjudicates C28, runs Stockfish labels, plays arena games, trains a model, modifies
# RC-J, pushes to Git, or opens the sealed C28 confirmation pool.
#
#   bash migration/bootstrap_mac.sh                 # full bootstrap
#   bash migration/bootstrap_mac.sh --check-only    # report, install nothing
#
# Environment variables it honours:
#   CLAUDESHARK_DATA_ROOT   external research data (default ~/Documents/ClaudeShark-data)
#   CLAUDESHARK_TWIC        TWIC PGN issues        (default ~/Documents/ClaudeShark-twic)
#   CLAUDESHARK_STOCKFISH   macOS Stockfish binary (default: whatever is on PATH)
#
# None of the three hardcodes a username: each falls back to a $HOME-relative path.

set -uo pipefail

CHECK_ONLY=0
[ "${1:-}" = "--check-only" ] && CHECK_ONLY=1

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

FAILED=0
step()  { printf '\n=== %s\n' "$1"; }
ok()    { printf '  OK    %s\n' "$1"; }
warn()  { printf '  WARN  %s\n' "$1"; }
fail()  { printf '  FAIL  %s\n' "$1"; FAILED=$((FAILED + 1)); }

# 1 -------------------------------------------------------------------- platform
step "1. platform"
if [ "$(uname -s)" != "Darwin" ]; then
  fail "this script is for macOS; uname -s is $(uname -s)"
  exit 1
fi
ARCH="$(uname -m)"
ok "macOS $(sw_vers -productVersion 2>/dev/null || echo '?'), architecture ${ARCH}"
case "$ARCH" in
  arm64)  ok "Apple Silicon: the locked wheels for torch, numba, llvmlite and onnxruntime are arm64" ;;
  x86_64) warn "Intel Mac: uv.lock carries macOS wheels only for arm64. 'uv sync' will have to
        re-resolve, and torch 2.13.0 may have no macOS x86_64 build. Report this before changing
        uv.lock; the engine itself does not need torch (it is only used for N1 training)." ;;
  *)      warn "unrecognised architecture ${ARCH}" ;;
esac

# 2 -------------------------------------------------------------------- project root
step "2. project root"
if [ -f "$REPO/cs_core.py" ] && [ -f "$REPO/pyproject.toml" ]; then
  ok "repository: $REPO"
else
  fail "not a ClaudeShark checkout: $REPO"
  exit 1
fi

# 3 -------------------------------------------------------------------- data root
step "3. external data root"
DATA_ROOT="${CLAUDESHARK_DATA_ROOT:-$HOME/Documents/ClaudeShark-data}"
if [ -d "$DATA_ROOT" ]; then
  ok "data root: $DATA_ROOT ($(du -sh "$DATA_ROOT" 2>/dev/null | cut -f1))"
  [ -f "$DATA_ROOT/learned_eval/n1/pool.jsonl" ] \
    && ok "N1 pool present" \
    || warn "N1 pool missing at $DATA_ROOT/learned_eval/n1/pool.jsonl"
else
  fail "data root not found: $DATA_ROOT (set CLAUDESHARK_DATA_ROOT)"
fi
TWIC_ROOT="${CLAUDESHARK_TWIC:-$HOME/Documents/ClaudeShark-twic}"
if [ -d "$TWIC_ROOT" ]; then
  N_PGN=$(find "$TWIC_ROOT" -maxdepth 1 -name '*.pgn' 2>/dev/null | wc -l | tr -d ' ')
  ok "TWIC corpus: $TWIC_ROOT (${N_PGN} PGN issue(s))"
  [ "$N_PGN" = "0" ] && warn "no *.pgn in $TWIC_ROOT"
else
  warn "TWIC corpus not found at $TWIC_ROOT (set CLAUDESHARK_TWIC)"
fi
if ! grep -q 'CLAUDESHARK_DATA_ROOT' "$HOME/.zshrc" 2>/dev/null; then
  printf '  note  add to ~/.zshrc:\n'
  printf '          export CLAUDESHARK_DATA_ROOT="%s"\n' "$DATA_ROOT"
  printf '          export CLAUDESHARK_TWIC="%s"\n' "$TWIC_ROOT"
fi
# Reported, not silently patched: the research scripts still carry the Windows TWIC path as their
# default (learned_eval/scripts/build_pool.py and hard_position_mining/scripts/c28paths.py). They
# are read by C28, which is frozen for repair, so they are left exactly as they are. The variables
# above are the documented mechanism those defaults must be changed to during that repair.
for f in benchmarks/current/learned_eval/scripts/build_pool.py \
         benchmarks/current/hard_position_mining/scripts/c28paths.py; do
  [ -f "$f" ] && grep -q 'C:/Users/epick/engines/twic' "$f" 2>/dev/null \
    && warn "$f still defaults TWIC_DIR to the Windows path (fix during the C28 repair, not here)"
done

# 4 -------------------------------------------------------------------- commands
step "4. command dependencies"
for c in git curl; do
  command -v "$c" >/dev/null 2>&1 && ok "$c $(command -v $c)" || fail "$c not found"
done
command -v brew >/dev/null 2>&1 && ok "brew $(command -v brew)" || warn "Homebrew not installed (only needed for Stockfish)"

# 5 -------------------------------------------------------------------- uv
step "5. uv"
if command -v uv >/dev/null 2>&1; then
  ok "uv $(uv --version)"
elif [ "$CHECK_ONLY" = 1 ]; then
  warn "uv not installed; install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
else
  printf '  ..    installing uv\n'
  curl -LsSf https://astral.sh/uv/install.sh | sh || fail "uv install failed"
  export PATH="$HOME/.local/bin:$PATH"
  command -v uv >/dev/null 2>&1 && ok "uv $(uv --version)" || fail "uv still not on PATH"
fi

# 6 -------------------------------------------------------------------- environment
step "6. python environment"
REQ_PY="$(sed -n 's/^requires-python = "\(.*\)"/\1/p' pyproject.toml)"
ok "pyproject requires-python ${REQ_PY:-unknown}"
if [ "$CHECK_ONLY" = 1 ]; then
  warn "--check-only: skipping 'uv sync'"
else
  printf '  ..    uv sync (rebuilds .venv from uv.lock; the Windows .venv is never reused)\n'
  if uv sync; then ok "uv sync"; else fail "uv sync failed (see the architecture note in step 1)"; fi
fi

# 7 -------------------------------------------------------------------- imports
step "7. imports"
if [ -x .venv/bin/python ]; then
  .venv/bin/python - <<'PY' && ok "imports" || fail "imports"
import chess, numpy, numba
import sys, os
sys.path.insert(0, os.path.abspath("."))
import cs_core, cs_fast
print(f"  python-chess {chess.__version__}, numpy {numpy.__version__}, numba {numba.__version__}")
print(f"  cs_core MATE_SCORE {cs_core.MATE_SCORE}, QS_MAX_PLY {cs_core.QS_MAX_PLY}")
PY
else
  fail ".venv/bin/python not present"
fi

# 8 -------------------------------------------------------------------- caches
step "8. platform-specific caches"
N_PYC=$(find . -name '__pycache__' -type d -not -path './.venv/*' 2>/dev/null | wc -l | tr -d ' ')
N_NB=$(find . \( -name '*.nbi' -o -name '*.nbc' -o -name '.numba_cache' \) -not -path './.venv/*' 2>/dev/null | wc -l | tr -d ' ')
if [ "$N_PYC" != "0" ] || [ "$N_NB" != "0" ]; then
  warn "$N_PYC __pycache__ dirs and $N_NB Numba cache entries carried over from Windows"
  if [ "$CHECK_ONLY" = 0 ]; then
    find . -name '__pycache__' -type d -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null
    find . \( -name '*.nbi' -o -name '*.nbc' \) -not -path './.venv/*' -delete 2>/dev/null
    ok "removed (they hold x86-64 machine code and CPython bytecode; both rebuild on first run)"
  fi
else
  ok "none present"
fi

# 9 -------------------------------------------------------------------- stockfish
step "9. Stockfish (macOS build of the same release)"
SF="${CLAUDESHARK_STOCKFISH:-$(command -v stockfish 2>/dev/null || true)}"
if [ -n "$SF" ] && [ -f "$SF" ]; then
  ok "binary: $SF"
  ok "sha256: $(shasum -a 256 "$SF" | cut -d' ' -f1)"
  printf '  note  the historical Windows binary was Stockfish 18,\n'
  printf '        sha256 c86215fa1977d53b82ed854540a4c7b025be4cd042276c85ba3de53fb9118911.\n'
  printf '        A different hash here is expected provenance, not corruption. Old label\n'
  printf '        manifests keep the Windows hash; new labels must record this one.\n'
else
  warn "no Stockfish found. Install a macOS build of Stockfish 18, then set CLAUDESHARK_STOCKFISH."
  printf '        Homebrew:  brew install stockfish   (check the version it gives you)\n'
  printf '        Official:  https://stockfishchess.org/download/  (macOS ARM64 for Apple Silicon)\n'
fi

# 10 ------------------------------------------------------------------- git config
step "10. git configuration"
NAME="$(git config --get user.name || true)"
MAIL="$(git config --get user.email || true)"
if [ "$NAME" = "kushagr4" ] && [ "$MAIL" = "ratrakushagra@gmail.com" ]; then
  ok "identity kushagr4 <ratrakushagra@gmail.com> (repository-local)"
elif [ "$CHECK_ONLY" = 1 ]; then
  warn "identity is '$NAME <$MAIL>'; run: git config --local user.name kushagr4; git config --local user.email ratrakushagra@gmail.com"
else
  git config --local user.name kushagr4
  git config --local user.email ratrakushagra@gmail.com
  ok "identity set repository-locally (global config untouched)"
fi
if [ "$CHECK_ONLY" = 0 ] && [ "$(git config --local --get core.autocrlf || true)" != "false" ]; then
  git config --local core.autocrlf false
  ok "core.autocrlf=false set repository-locally (protects byte-identical production sources)"
else
  ok "core.autocrlf $(git config --get core.autocrlf || echo '(unset)')"
fi
[ "$CHECK_ONLY" = 0 ] && [ "$(git config --local --get core.filemode || true)" != "false" ] \
  && git config --local core.filemode false \
  && ok "core.filemode=false set (a tree copied from Windows otherwise shows mode churn)"

# The Windows working tree carries CRLF in most production modules (its system-wide
# core.autocrlf=true), while the committed blobs are LF. Re-materialise the tracked files from
# the blobs so the bytes on disk are the canonical ones. Tracked files are unmodified, so
# nothing is lost.
step "10b. line endings of the production sources"
RUNTIME_CRLF=0
for f in agent.py cs_constants.py cs_core.py cs_drawish.py cs_eval.py cs_fast.py cs_king.py \
         cs_kingpawn.py cs_mopup.py cs_ordering.py cs_passed.py cs_search.py cs_see.py \
         cs_terms.py cs_time.py cs_tt.py; do
  [ -f "$f" ] && LC_ALL=C grep -q $'\r' "$f" 2>/dev/null && RUNTIME_CRLF=$((RUNTIME_CRLF + 1))
done
CHANGED_TRACKED="$(git diff --name-only | wc -l | tr -d ' ')"
if [ "$RUNTIME_CRLF" != "0" ] || [ "$CHANGED_TRACKED" != "0" ]; then
  warn "$RUNTIME_CRLF production module(s) carry CRLF; git reports $CHANGED_TRACKED changed tracked file(s)"
  if [ "$CHECK_ONLY" = 0 ]; then
    # With core.autocrlf=false git reports every CRLF copy as modified, so "nothing modified" is
    # the wrong guard. Re-materialise only if each reported change is line endings alone.
    REAL=0
    while IFS= read -r -d '' f; do
      if ! LC_ALL=C tr -d '\r' < "$f" | cmp -s - <(git show ":$f"); then
        REAL=$((REAL + 1))
        warn "$f has uncommitted changes beyond line endings"
      fi
    done < <(git diff --name-only -z)
    if [ "$REAL" = 0 ]; then
      git checkout-index -a -f && ok "re-materialised every tracked file from its committed blob"
    else
      fail "$REAL tracked file(s) have real uncommitted changes; resolve before re-materialising"
    fi
  fi
else
  ok "all 16 production modules already have canonical (LF) bytes"
fi
RUNTIME="agent.py cs_constants.py cs_core.py cs_drawish.py cs_eval.py cs_fast.py cs_king.py
         cs_kingpawn.py cs_mopup.py cs_ordering.py cs_passed.py cs_search.py cs_see.py
         cs_terms.py cs_time.py cs_tt.py"
BAD=0
for f in $RUNTIME; do
  git show "HEAD:$f" 2>/dev/null | cmp -s - "$f" || BAD=$((BAD + 1))
done
[ "$BAD" = 0 ] && ok "all 16 production modules byte-identical to their committed blobs" \
               || fail "$BAD production module(s) differ from the committed blob byte for byte"
# RC-J is commit 2bf6885. Since 2026-09-16 cs_core.py and cs_fast.py also carry the optional
# NNUE (CS_NNUE, off by default); every other production module must still be RC-J's.
UNEXPECTED=0
# shellcheck disable=SC2086
for f in $(git diff --name-only 2bf6885 HEAD -- $RUNTIME); do
  case "$f" in
    cs_core.py|cs_fast.py) ;;
    *) UNEXPECTED=$((UNEXPECTED + 1)); warn "$f differs from RC-J (2bf6885)" ;;
  esac
done
[ "$UNEXPECTED" = 0 ] && ok "the other 14 production modules are RC-J's (2bf6885), byte for byte" \
                      || fail "$UNEXPECTED production module(s) changed outside the NNUE flag"
if [ -x .venv/bin/python ]; then
  env -u CS_NNUE -u CS_NNUE_VERIFY .venv/bin/python -c \
    "import cs_core, sys; sys.exit(1 if getattr(cs_core, 'NNUE_ENABLED', False) else 0)" \
    && ok "NNUE flag off by default (the engine is RC-J unless CS_NNUE=1)" \
    || fail "cs_core reports the NNUE enabled with CS_NNUE unset"
fi

# 11 ------------------------------------------------------------------- verification
step "11. state verification"
if [ -x .venv/bin/python ]; then
  .venv/bin/python migration/verify_mac_port.py ${SF:+--stockfish "$SF"} || FAILED=$((FAILED + 1))
else
  warn "skipped: no .venv yet"
fi

# 12 ------------------------------------------------------------------- light tests
step "12. lightweight tests"
if [ "$CHECK_ONLY" = 1 ]; then
  warn "--check-only: skipping tests"
elif [ -x .venv/bin/python ]; then
  printf '  ..    engine unit tests (no arena, no Stockfish, no training)\n'
  printf '        Windows baseline 2026-09-12: 1486 passed in 192 s\n'
  if .venv/bin/python -m pytest -q tests; then ok "tests/"; else fail "tests/"; fi
  printf '  ..    learned-evaluation unit tests\n'
  .venv/bin/python -m pytest -q \
      benchmarks/current/learned_eval/scripts/test_features.py \
      benchmarks/current/learned_eval/scripts/test_evalkit.py 2>/dev/null \
    && ok "learned_eval tests" \
    || warn "learned_eval tests need CLAUDESHARK_DATA_ROOT pools; see README_MAC_MIGRATION.md"
  printf '  ..    cross-platform evaluator comparison\n'
  REF="migration/reference_windows.json"
  if [ -f "$REF" ]; then
    .venv/bin/python migration/make_reference.py --out /tmp/reference_mac.json >/dev/null \
      && .venv/bin/python migration/make_reference.py --compare "$REF" /tmp/reference_mac.json \
      && ok "E0 / E1 / N1 float / N1 quantised identical to the Windows reference" \
      || fail "evaluator outputs differ from the Windows reference: investigate, do not rewrite the fixture"
  else
    warn "no Windows reference fixture at $REF"
  fi
fi

# ---------------------------------------------------------------------- summary
printf '\n%s\n' "========================================================================"
if [ "$FAILED" = 0 ]; then
  printf 'BOOTSTRAP COMPLETE - environment ready.\n'
else
  printf 'BOOTSTRAP FINISHED WITH %s FAILURE(S) - read the FAIL lines above.\n' "$FAILED"
fi
cat <<'EON'

The optional deterministic node fingerprint is NOT run here (it is a benchmark).
To check it later, on an idle machine:

    .venv/bin/python -m tools.bench --depth 10

RC-J's recorded depth-10 fingerprint over the 24 balanced openings is 16,818,635 nodes.
Node identity should be invariant across platforms if the semantics are identical; timing
is not. If the node count differs, investigate it. Do not rewrite the expected value.

C28 remains at pre-adjudication repair. Do not start oracle adjudication, Stockfish
labelling, training or games until the repairs and the second review are complete and the
work is explicitly authorised.
EON
exit $((FAILED > 0))
