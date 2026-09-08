#!/bin/bash
# The chess gate: RC-I against C15-v2 on the pre-registered position sets.
cd "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c15v2"
PY="C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
O="benchmarks/current/c15v2_passer"
R="C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/research/benchmarks/current/research_top3"
RCI="C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/rcg"

echo "=== COMPARE  RC-I vs C15-v2, 144 serious errors, depth 12  $(date '+%H:%M:%S') ==="
$PY $O/compare.py "$R/serious_errors.json" "$RCI" "$(pwd)" $O/compare.json 12 6 2>&1 | grep -v -i warning

echo "=== RETENTION against the 17 C15 repaired  $(date '+%H:%M:%S') ==="
$PY - <<'EOF'
import json
rows = json.load(open("benchmarks/current/c15v2_passer/compare.json"))
prior = set(json.load(open("C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c15_repaired_fens.json")))
by = {r["fen"]: r for r in rows}
kept = [f for f in prior if f in by and by[f]["base_loss"] >= 100 and by[f]["cand_loss"] < 100]
lost = [f for f in prior if f not in kept]
new = [r["fen"] for r in rows
       if r["base_loss"] >= 100 and r["cand_loss"] < 100 and r["fen"] not in prior]
wor = [r["fen"] for r in rows if r["base_loss"] < 100 and r["cand_loss"] >= 100]
print(f"C15 repaired      : {len(prior)}")
print(f"C15-v2 retained   : {len(kept)}")
print(f"C15-v2 lost       : {len(lost)}")
print(f"C15-v2 new repairs: {len(new)}")
print(f"C15-v2 worsened   : {len(wor)}")
for f in lost:
    r = by.get(f)
    if r:
        print(f"   LOST  {f}  base {r['base_loss']} -> cand {r['cand_loss']}  "
              f"({r['base_move']} -> {r['cand_move']})")
    else:
        print(f"   LOST  {f}  (absent from the candidate run)")
for f in wor:
    r = by[f]
    print(f"   WORSE {f}  base {r['base_loss']} -> cand {r['cand_loss']}")
EOF

echo "=== CAUSAL REPLAY  $(date '+%H:%M:%S') ==="
$PY $O/causal.py $O/compare.json "$R/ladder.json" $O/CAUSAL_REPLAY.md

echo "=== DONE $(date '+%H:%M:%S') ==="
