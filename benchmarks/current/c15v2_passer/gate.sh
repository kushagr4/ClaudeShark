#!/bin/bash
# Tests, tactics and the clock ladder for C15-v2. The two corpus comparisons
# are run separately by equivalence.sh.
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c15v2"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
echo "=== FULL TEST SUITE $(date '+%H:%M:%S') ==="
$PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -4
echo "=== TACTICS $(date '+%H:%M:%S') ==="
$PY -m tools.tactics --ms 1000 2>&1 | tail -3
echo "=== CLOCK LADDER $(date '+%H:%M:%S') ==="
$PY -m tools.clockladder 2>&1 | tail -8
echo "=== GATE DONE $(date '+%H:%M:%S') ==="
