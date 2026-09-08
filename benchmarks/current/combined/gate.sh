#!/bin/bash
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/rcg"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
O="benchmarks/current/combined"
C12="C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c12"
echo "=== FULL SUITE $(date '+%H:%M:%S') ==="
$PY -m pytest -q -p no:cacheprovider 2>&1 | tail -3
echo "=== CONVERSION (C12 vs COMBINED) $(date '+%H:%M:%S') ==="
$PY $O/conversion.py 2>&1 | sed -n '/PROMOTION METRIC/,$p'
echo "=== 240 CORPUS $(date '+%H:%M:%S') ==="
$PY $O/outside_domain.py 8 2>&1 | grep -v -i warning | head -10
echo "=== TACTICS $(date '+%H:%M:%S') ==="
$PY -m tools.tactics --ms 1000 2>&1 | tail -3
echo "=== CLOCK $(date '+%H:%M:%S') ==="
$PY -m tools.clockladder 2>&1 | tail -5
echo "=== NPS vs C12 and vs RC-F $(date '+%H:%M:%S') ==="
for i in 1 2 3; do
 echo -n "  C12  run$i: "; (cd $C12 && $PY -m tools.bench --ms 2000 2>&1 | grep "nodes/second")
 echo -n "  RCG  run$i: "; $PY -m tools.bench --ms 2000 2>&1 | grep "nodes/second"
done
echo -n "  RC-F ref  : "; $PY -m tools.bench --ms 2000 --engine champions/rc_f 2>&1 | grep "nodes/second"
echo "=== DONE $(date '+%H:%M:%S') ==="
