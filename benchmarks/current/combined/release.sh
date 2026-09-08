#!/bin/bash
set -e
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/rcg"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
S="C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad"
echo "=== FREEZE SNAPSHOT $(date '+%H:%M:%S') ==="
$PY -m tools.freeze rc_i 2>&1 | tail -2
echo "=== LF EXPORT ==="
rm -rf $S/rci_export && mkdir -p $S/rci_export
for f in champions/rc_i/*.py; do tr -d '\r' < "$f" > "$S/rci_export/$(basename $f)"; done
ls $S/rci_export | wc -l
echo "=== RELEASE CHECK $(date '+%H:%M:%S') ==="
$PY -m tools.release_check --source $S/rci_export --keep corpus/release/claudeshark_rc_i.zip 2>&1 | tail -22
echo "=== HASH ==="
sha256sum corpus/release/claudeshark_rc_i.zip
$PY -c "import zipfile;z=zipfile.ZipFile('corpus/release/claudeshark_rc_i.zip');print(len(z.namelist()),'files',sum(i.file_size for i in z.infolist()),'bytes unpacked')"
echo "=== PY3.12 SMOKE $(date '+%H:%M:%S') ==="
sed 's|claudeshark_rc_e.zip|claudeshark_rc_i.zip|' $S/rce_smoke.py > $S/rci_smoke.py
uv run --python 3.12 --no-project --with chess==1.11.2 --with numpy==2.5.2 --with numba==0.67.0 python $S/rci_smoke.py $S/rci_extract312 corpus/release/rc_i_smoke_py312.json 2>&1 | grep -v -i warning | tail -14
echo "=== DONE $(date '+%H:%M:%S') ==="
