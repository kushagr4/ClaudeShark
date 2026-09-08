#!/bin/bash
# Two behavioural comparisons over the 240-position competition-like corpus.
#   1. C15 semantics on RC-I (the nps lane's v1) against C15-v2: must be
#      identical in move, score and node count, or the reimplementation is not
#      the same rule.
#   2. RC-I against C15-v2: the set of positions the rule actually changes.
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c15v2"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
O="benchmarks/current/c15v2_passer"
S="C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad"
echo "=== EQUIVALENCE  C15-semantics(v1) vs C15-v2  $(date '+%H:%M:%S') ==="
$PY $O/outside_domain.py "$S/nps/v1" "$(pwd)" 8 $O/equivalence_v1_vs_c15v2.json 2>&1 | grep -v -i warning
echo "=== BEHAVIOUR  RC-I vs C15-v2  $(date '+%H:%M:%S') ==="
$PY $O/outside_domain.py "$S/rcg" "$(pwd)" 8 $O/outside_domain_rci_vs_c15v2.json 2>&1 | grep -v -i warning
echo "=== DONE $(date '+%H:%M:%S') ==="
