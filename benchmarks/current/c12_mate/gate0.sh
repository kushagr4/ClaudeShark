#!/bin/bash
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c12"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
O="benchmarks/current/c12_mate"
LANE="$(pwd)"
echo "=== FULL SUITE $(date '+%H:%M:%S') ==="
$PY -m pytest -q -p no:cacheprovider 2>&1 | tail -3
echo "=== ROUND 54 + C11-RESIDUAL PLAYOUTS (fixed depth) $(date '+%H:%M:%S') ==="
for pos in "R54-m91:7R/1K6/5k2/8/8/8/8/8 w - - 0 91" "R54-m93:8/1K6/5k2/3R4/8/8/8/8 w - - 4 93" "KQK-2:8/8/2k5/8/8/8/8/3QK3 w - - 0 1" "KQK-3:8/5k2/8/8/8/8/1Q6/6K1 w - - 0 1"; do
  lab="${pos%%:*}"; fen="${pos#*:}"
  for b in "champions/rc_f:RC-F" "$LANE:C12"; do
    dir="${b%%:*}"; bn="${b##*:}"
    for d in 8 10 12 14; do
      $PY $O/playout.py "$dir" "$fen" "$lab" $d 120 2>/dev/null | sed "s/^RESULT/$bn RESULT/"
    done
  done
done
echo "=== OUTSIDE DOMAIN 240 @ depth 8 $(date '+%H:%M:%S') ==="
$PY $O/outside_domain.py 8 2>&1 | grep -v -i warning
echo "=== TACTICS $(date '+%H:%M:%S') ==="
$PY -m tools.tactics --ms 1000 2>&1 | tail -3
echo "=== CLOCK LADDER $(date '+%H:%M:%S') ==="
$PY -m tools.clockladder 2>&1 | tail -8
echo "=== NPS + TT HIT RATE, alternating $(date '+%H:%M:%S') ==="
for i in 1 2; do
  echo "--- run $i RC-F ---"; $PY -m tools.bench --ms 2000 --engine champions/rc_f 2>&1 | grep -E "nodes/second|tt hit rate"
  echo "--- run $i C12  ---"; $PY -m tools.bench --ms 2000 2>&1 | grep -E "nodes/second|tt hit rate"
done
echo "=== FIXED-DEPTH FINGERPRINT $(date '+%H:%M:%S') ==="
echo -n "RC-F d8: "; $PY -m tools.bench --depth 8 --engine champions/rc_f 2>&1 | grep "total nodes"
echo -n "C12  d8: "; $PY -m tools.bench --depth 8 2>&1 | grep "total nodes"
echo "=== DONE $(date '+%H:%M:%S') ==="
