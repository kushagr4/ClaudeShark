#!/bin/bash
# Alternating measurement of the four LMR variants: v0 v1 v2 v3, three rounds,
# so thermal drift and background noise fall on every build equally.
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/nps"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
: > results.jsonl
for round in 1 2 3; do
  for v in v0 v1 v2 v3; do
    echo "round $round $v $(date '+%H:%M:%S')"
    "$PY" probe.py "$(pwd)/$v" 2>/dev/null | grep '^JSON' | sed "s/^JSON/{\"round\": $round, /; s/{\"round\": $round, {/{\"round\": $round, /" >> results.jsonl
  done
done
echo "DONE $(date '+%H:%M:%S')"
