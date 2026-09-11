"""Bare-king mating check for the magnitude audit (DESIGN_N1.md section 10): one engine plays both
sides at 200 ms per move from each position until mate or 100 plies.

    python mate_probe.py ENGINE_DIR POSITIONS.json OUT.json
"""
import json
import os
import sys

eng, pos_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
sys.path.insert(0, os.path.abspath(eng))

import chess  # noqa: E402
import cs_fast  # noqa: E402

assert os.path.dirname(os.path.abspath(cs_fast.__file__)) == os.path.abspath(eng)
cs_fast.warm_up()
s = cs_fast.Searcher()
res = []
for fen in json.load(open(pos_path, encoding="utf-8")):
    b = chess.Board(fen)
    s.new_game()
    plies = 0
    while plies < 100 and not b.is_game_over(claim_draw=True):
        mv, _ = s.search(b, 0, fixed_budget_ms=200.0)
        b.push(mv)
        plies += 1
    res.append(dict(fen=fen, mated=b.is_checkmate(), plies=plies, result=b.result(claim_draw=True)))
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1)
print(json.dumps(dict(mated=sum(r["mated"] for r in res), n=len(res))))
