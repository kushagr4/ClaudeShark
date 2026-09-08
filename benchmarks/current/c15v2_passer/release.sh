#!/bin/bash
# Build, verify and publish RC-J. RC-G and RC-H belong to the terminal-shortcut
# lane and RC-I is the submitted build, so J is the next free name.
#
# The archive is built in the worktree, then copied to the canonical
# corpus/release directory in the user-facing repository, and the SHA-256 that
# the report quotes is taken from that canonical copy.
set -e
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c15v2"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
S="C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad"
CANON="C:/Users/epick/Documents/ClaudeShark/corpus/release"

echo "=== FREEZE SNAPSHOT $(date '+%H:%M:%S') ==="
$PY -m tools.freeze rc_j 2>&1 | tail -2

echo "=== LF EXPORT ==="
rm -rf $S/rcj_export && mkdir -p $S/rcj_export
for f in champions/rc_j/*.py; do tr -d '\r' < "$f" > "$S/rcj_export/$(basename $f)"; done
ls $S/rcj_export | wc -l

echo "=== RELEASE CHECK $(date '+%H:%M:%S') ==="
$PY -m tools.release_check --source $S/rcj_export --keep corpus/release/claudeshark_rc_j.zip 2>&1 | tail -22

echo "=== WORKTREE HASH ==="
sha256sum corpus/release/claudeshark_rc_j.zip
$PY -c "import zipfile;z=zipfile.ZipFile('corpus/release/claudeshark_rc_j.zip');print(len(z.namelist()),'files',sum(i.file_size for i in z.infolist()),'bytes unpacked')"

echo "=== COPY TO CANONICAL $(date '+%H:%M:%S') ==="
test ! -e "$CANON/claudeshark_rc_j.zip" || { echo "REFUSING: $CANON/claudeshark_rc_j.zip already exists"; exit 1; }
cp corpus/release/claudeshark_rc_j.zip "$CANON/claudeshark_rc_j.zip"
echo "canonical: $CANON/claudeshark_rc_j.zip"
sha256sum "$CANON/claudeshark_rc_j.zip"
cmp corpus/release/claudeshark_rc_j.zip "$CANON/claudeshark_rc_j.zip" && echo "canonical copy is byte-identical to the worktree build"

echo "=== PY3.12 SMOKE AGAINST THE CANONICAL ARTIFACT $(date '+%H:%M:%S') ==="
sed "s|claudeshark_rc_e.zip|claudeshark_rc_j.zip|" $S/rce_smoke.py > $S/rcj_smoke.py
(cd "C:/Users/epick/Documents/ClaudeShark" && uv run --python 3.12 --no-project \
  --with chess==1.11.2 --with numpy==2.5.2 --with numba==0.67.0 \
  python $S/rcj_smoke.py $S/rcj_extract312 "$CANON/rc_j_smoke_py312.json" 2>&1) \
  | grep -v -i warning | tail -14

echo "=== ALSO PUBLISH THE SUBMITTED RC-I ARCHIVE, WHICH IS MISSING FROM CANONICAL ==="
if [ ! -e "$CANON/claudeshark_rc_i.zip" ]; then
  cp "$S/rcg/corpus/release/claudeshark_rc_i.zip" "$CANON/claudeshark_rc_i.zip"
  cp "$S/rcg/corpus/release/rc_i_smoke_py312.json" "$CANON/rc_i_smoke_py312.json"
  sha256sum "$CANON/claudeshark_rc_i.zip"
else
  echo "already present"
fi

echo "=== DONE $(date '+%H:%M:%S') ==="
