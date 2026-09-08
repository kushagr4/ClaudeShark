#!/bin/bash
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c15v2"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
O="benchmarks/current/c15v2_passer"
R="C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/research/benchmarks/current/research_top3"
RCI="C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/rcg"
echo "=== COMPARE (deterministic oracle) RC-I vs C15-v2  $(date '+%H:%M:%S') ==="
$PY $O/compare2.py "$R/serious_errors.json" "$RCI" "$(pwd)" $O/compare.json 12 6 2>&1 | grep -v -i warning
echo "=== DONE $(date '+%H:%M:%S') ==="
