"""Engine-side N1 checks (DESIGN_N1.md section 10). Node counts and exact equalities are deterministic,
so these do not need an idle machine; speed is measured separately (speed_n1.py).

  1. random-walk make/unmake accumulator test (test_n1_engine.py) on a `real` build;
  2. zero-weight plumbing control: RC-J's depth-10 node count and moves on the 24 openings;
  3. shadow-verify build: incremental row compared with a rebuild at every evaluation inside real
     search (depth 10 and 1,000 ms on the openings, plus a 40-move self-play sequence without
     new_game); zero mismatches, RC-J's node count, and rebuilds == root seeds.

    n1_engine_checks.py DATA_DIR OUT_JSON random            (random quantised weights)
    n1_engine_checks.py DATA_DIR OUT_JSON WEIGHTS.npz        (frozen weights)
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine_n1  # noqa: E402

RCJ_DEPTH10_NODES = 16_818_635
PY = sys.executable


def random_weights(seed=20260911):
    r = np.random.default_rng(seed)
    return dict(W1q=r.integers(-200, 201, (768, 128)).astype(np.int16), b1q=r.integers(-100, 356, 128).astype(np.int32),
                W2q=r.integers(-127, 128, (32, 256)).astype(np.int8), b2q=r.integers(-20000, 20001, 32).astype(np.int32),
                w3q=r.integers(-200, 201, 32).astype(np.int32), b3q=np.array([r.integers(-50000, 50001)], np.int64))


def probe(eng, mode, arg):
    out = subprocess.run([PY, os.path.join(HERE, "speed_probe.py"), eng, mode, str(arg)], capture_output=True,
                         text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


SELFPLAY = r'''
import json, os, sys
eng = sys.argv[1]
sys.path.insert(0, os.path.abspath(eng))
import chess, cs_core, cs_fast
cs_fast.warm_up()
s = cs_fast.Searcher()
s.NNA[cs_core.N1_CTRL, :8] = 0
b = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
plies = 0
while plies < 80 and not b.is_game_over(claim_draw=True):
    mv, info = s.search(b, 0, fixed_budget_ms=150.0)
    b.push(mv)
    plies += 1
c = s.NNA[cs_core.N1_CTRL]
print(json.dumps(dict(plies=plies, evaluate_calls=int(c[0]), rebuilds=int(c[1]), catch_up_steps=int(c[2]),
                      verify_mismatches=int(c[4]), root_seeds=int(c[7]))))
'''


def main():
    data, out, wsrc = sys.argv[1], sys.argv[2], sys.argv[3]
    if wsrc == "random":
        Q, tag = random_weights(), "random"
    else:
        z = np.load(wsrc)
        Q, tag = {k: z[k] for k in ("W1q", "b1q", "W2q", "b2q", "w3q", "b3q")}, "frozen"
    eng_dir = os.path.join(data, "engines")
    res = dict(weights=tag)

    real = os.path.join(eng_dir, f"n1_real_{tag}")
    res["build_real"] = engine_n1.build(real, Q, "real")
    acc_out = os.path.join(data, f"accumulator_test_{tag}.json")
    p = subprocess.run([PY, os.path.join(HERE, "test_n1_engine.py"), real, os.path.join(data, "pool.jsonl"),
                        "--walks", "400", "--out", acc_out], capture_output=True, text=True)
    res["accumulator"] = json.load(open(acc_out))
    res["accumulator"]["exit"] = p.returncode

    zero = os.path.join(eng_dir, "n1_zero")
    res["build_zero"] = engine_n1.build(zero, engine_n1.zero_weights(), "real")
    z10, r10 = probe(zero, "depth", 10), probe(engine_n1.ROOT, "depth", 10)
    res["zero_weight_control"] = dict(zero_nodes=z10["nodes"], rcj_nodes=r10["nodes"], recorded=RCJ_DEPTH10_NODES,
                                      nodes_identical=z10["nodes"] == r10["nodes"] == RCJ_DEPTH10_NODES,
                                      moves_identical=z10["moves"] == r10["moves"], counters=z10["n1_counters"])

    ver = os.path.join(eng_dir, f"n1_verify_{tag}")
    res["build_verify"] = engine_n1.build(ver, Q, "shadow_verify")
    v10, v1s = probe(ver, "depth", 10), probe(ver, "budget", 1000)
    sp = subprocess.run([PY, "-c", SELFPLAY, ver], capture_output=True, text=True, check=True)
    sp = json.loads(sp.stdout.strip().splitlines()[-1])
    res["shadow_verify"] = dict(
        depth10=dict(nodes=v10["nodes"], nodes_identical=v10["nodes"] == RCJ_DEPTH10_NODES,
                     moves_identical=v10["moves"] == r10["moves"], counters=v10["n1_counters"]),
        budget1000=dict(nodes=v1s["nodes"], counters=v1s["n1_counters"]), selfplay_40_moves=sp)
    allc = [v10["n1_counters"], v1s["n1_counters"], sp]
    res["shadow_verify"]["mismatches_total"] = sum(c["verify_mismatches"] for c in allc)
    res["shadow_verify"]["rebuilds_equal_root_seeds"] = all(
        c["rebuilds"] == c.get("root_searches", c.get("root_seeds")) for c in allc)
    res["passed"] = bool(res["accumulator"]["passed"] and res["zero_weight_control"]["nodes_identical"]
                         and res["zero_weight_control"]["moves_identical"]
                         and res["shadow_verify"]["mismatches_total"] == 0
                         and res["shadow_verify"]["depth10"]["nodes_identical"]
                         and res["shadow_verify"]["rebuilds_equal_root_seeds"])
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "accumulator"}, indent=1))
    print("accumulator", res["accumulator"]["passed"], res["accumulator"]["failures"], res["accumulator"]["counts"])


if __name__ == "__main__":
    main()
