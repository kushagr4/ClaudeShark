#!/bin/bash
# Paired strength screen: C15-v2 against the frozen RC-I snapshot, competition
# time control, strict claims, the organiser start set.
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c15v2"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
GAMES=${1:-30}
TAG=${2:-30}
echo "launch $(date '+%Y-%m-%d %H:%M:%S') C15-v2 vs RC-I dev $GAMES strict 120s+0.5s 6 workers" \
  > corpus/strength/c15v2/c15v2_vs_rci_dev_${TAG}_strict.launch.txt
$PY -m tools.arena --agent . --opponent champions/rc_i --games $GAMES \
  --base-ms 120000 --increment-ms 500 --ply-cap 300 --workers 6 \
  --draw-claim strict --corpus corpus/strength/dev.jsonl \
  --jsonl corpus/strength/c15v2/c15v2_vs_rci_dev_${TAG}_strict.jsonl 2>&1 | tail -30
echo "=== SCREEN DONE $(date '+%H:%M:%S') ==="
