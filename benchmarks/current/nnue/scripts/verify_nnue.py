"""Evidence for the default-off NNUE integration (benchmarks/current/nnue/README.md).

Every engine run is its own subprocess, one at a time. RC-J is reconstructed byte for byte from
commit 2bf6885 with ``git archive`` into a scratch directory (no worktree, no branch).

  identity   RC-J (2bf6885) and this tree with CS_NNUE unset, depth 10 on the 24 balanced openings:
             node totals, per-opening moves and completed depths must be identical, and the total
             must be RC-J's recorded 16,818,635.
  verify     this tree with CS_NNUE=1 CS_NNUE_VERIFY=1: the incremental accumulator is compared with
             a from-scratch rebuild at every evaluation inside real search (depth 10 on the
             openings, and 60 plies of self-play at depth 5 with no new_game between moves): zero
             mismatches, and rebuilds equal to root seeds (the search never rebuilds otherwise).
  walk       the random make/unmake walk (accumulator_walk.py) with CS_NNUE=1.
  speed      (--speed) CS_NNUE unset against RC-J at depth 10, identical trees, ABBA rounds, with a
             null control of RC-J against a second RC-J copy. The block is valid only if the null
             control's median per-round ratio is within +-2%; otherwise it is reported as INVALID /
             NON-DECISIVE and the numbers are descriptive only.

    python verify_nnue.py [--speed] [--rounds 3] [--walks 400] [--out ../results/verify_nnue.json]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RCJ_COMMIT = "2bf6885"
RCJ_DEPTH10_NODES = 16_818_635
NNUE_WEIGHTS = os.path.join(
    ROOT, "benchmarks", "current", "learned_eval", "results", "n1", "n1_weights.npz"
)
NNUE_WEIGHTS_SHA256 = "b1b809b79d84238ef292096334d598d2a6327e96df690ade182dcf4e871da201"
# The walk must actually exercise every transition kind, not merely report zero failures.
WALK_MINIMUMS = dict(
    transitions=15000,
    evaluations=7000,
    capture=1,
    en_passant=1,
    king_move=1,
    null_move=1,
    unmake=1,
    multi_ply_catch_up=1,
    promotion_queen=1,
    promotion_rook=1,
    promotion_bishop=1,
    promotion_knight=1,
    castle_kingside_white=1,
    castle_queenside_white=1,
    castle_kingside_black=1,
    castle_queenside_black=1,
)
PY = sys.executable


def log(msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)


def sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha256_text(path: str) -> str:
    """LF-normalised, so a Windows working copy and a macOS checkout of one commit agree."""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def inputs_now() -> dict:
    """SHA-256 of every file that decides the result (text sources LF-normalised)."""
    text = {
        "cs_core.py": os.path.join(ROOT, "cs_core.py"),
        "cs_fast.py": os.path.join(ROOT, "cs_fast.py"),
        "probe.py": os.path.join(HERE, "probe.py"),
        "accumulator_walk.py": os.path.join(HERE, "accumulator_walk.py"),
        "verify_nnue.py": os.path.abspath(__file__),
    }
    out = {name: sha256_text(path) for name, path in text.items()}
    out["n1_weights.npz"] = sha256(NNUE_WEIGHTS)
    return out


def git(*args: str) -> str:
    return subprocess.run(
        ("git", *args), cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def extract_rcj(dest: str) -> dict:
    names = [
        n
        for n in git("ls-tree", "--name-only", RCJ_COMMIT).splitlines()
        if n == "agent.py" or (n.startswith("cs_") and n.endswith(".py"))
    ]
    blob = subprocess.run(
        ("git", "archive", "--format=tar", RCJ_COMMIT, *names),
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    os.makedirs(dest, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        tar.extractall(dest, filter="data")
    return {n: sha256(os.path.join(dest, n)) for n in names}


def env_for(nnue: bool, verify: bool = False) -> dict:
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("CS_NNUE", "CS_NNUE_VERIFY", "CS_NNUE_WEIGHTS")
    }
    if nnue:
        env["CS_NNUE"] = "1"
    if verify:
        env["CS_NNUE_VERIFY"] = "1"
    return env


def probe(engine: str, mode: str, arg: int, env: dict) -> dict:
    t = time.perf_counter()
    p = subprocess.run(
        (PY, os.path.join(HERE, "probe.py"), engine, mode, str(arg)),
        env=env,
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"probe failed ({engine} {mode} {arg}): {p.stderr[-2000:]}")
    res = json.loads(p.stdout.strip().splitlines()[-1])
    log(
        f"  probe {os.path.basename(engine) or engine} {mode} {arg} nnue={res['nnue']} "
        f"nodes={res['nodes']:,} nps={res['nps']:,} ({time.perf_counter() - t:.0f}s)"
    )
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--speed", action="store_true")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--walks", type=int, default=400)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "results", "verify_nnue.json"))
    a = ap.parse_args()
    scratch = tempfile.mkdtemp(prefix="claudeshark_nnue_verify_")
    rcj, rcj2 = os.path.join(scratch, "rcj_2bf6885"), os.path.join(scratch, "rcj_2bf6885_copy")
    res: dict = dict(
        started=time.strftime("%Y-%m-%d %H:%M:%S"),
        head=git("rev-parse", "HEAD"),
        tree_dirty=bool(git("status", "--porcelain", "--untracked-files=no")),
        inputs=inputs_now(),
        hash_basis="text sources LF-normalised (git canonical form); .npz raw bytes",
        env_stripped_for_every_run=["CS_NNUE", "CS_NNUE_VERIFY", "CS_NNUE_WEIGHTS"],
    )
    if res["inputs"]["n1_weights.npz"] != NNUE_WEIGHTS_SHA256:
        raise SystemExit(f"{NNUE_WEIGHTS} is not the frozen N1-U network")
    res["rcj_extracted"] = extract_rcj(rcj)
    extract_rcj(rcj2)
    log(f"RC-J {RCJ_COMMIT} extracted to {scratch}")

    log("identity: RC-J and this tree with the flag unset, depth 10")
    a_rcj = probe(rcj, "depth", 10, env_for(False))
    a_off = probe(ROOT, "depth", 10, env_for(False))
    res["identity"] = dict(
        rcj_nodes=a_rcj["nodes"],
        off_nodes=a_off["nodes"],
        recorded=RCJ_DEPTH10_NODES,
        nodes_identical=a_rcj["nodes"] == a_off["nodes"] == RCJ_DEPTH10_NODES,
        moves_identical=a_rcj["moves"] == a_off["moves"],
        depths_identical=a_rcj["completed"] == a_off["completed"],
        off_flag_reported=a_off["nnue"],
        off_counters=a_off["counters"],
        compile_s=dict(rcj=a_rcj["compile_s"], off=a_off["compile_s"]),
    )
    res["identity"]["passed"] = bool(
        res["identity"]["nodes_identical"]
        and res["identity"]["moves_identical"]
        and res["identity"]["depths_identical"]
        and not a_off["nnue"]
        and not any(a_off["counters"].values())
    )

    log("verify: CS_NNUE=1 CS_NNUE_VERIFY=1, depth 10 and 60 plies of self-play")
    v10 = probe(ROOT, "depth", 10, env_for(True, True))
    vsp = probe(ROOT, "selfplay", 5, env_for(True, True))
    mism = v10["counters"]["verify_mismatches"] + vsp["counters"]["verify_mismatches"]
    res["verify"] = dict(
        depth10=v10,
        selfplay=vsp,
        mismatches_total=mism,
        rebuilds_equal_root_seeds=all(
            p["counters"]["rebuilds"] == p["counters"]["root_seeds"] for p in (v10, vsp)
        ),
        evaluations=v10["counters"]["evaluate_calls"] + vsp["counters"]["evaluate_calls"],
        moves_differ_from_rcj=sum(
            x != y for x, y in zip(v10["moves"], a_rcj["moves"], strict=True)
        ),
    )
    res["verify"]["passed"] = bool(
        v10["nnue"]
        and v10["nnue_verify"]
        and mism == 0
        and res["verify"]["rebuilds_equal_root_seeds"]
        and res["verify"]["evaluations"] > 0
    )

    log(f"walk: {a.walks} walks")
    wout = os.path.join(scratch, "walk.json")
    p = subprocess.run(
        (PY, os.path.join(HERE, "accumulator_walk.py"), "--walks", str(a.walks), "--out", wout),
        env=env_for(True),
        capture_output=True,
        text=True,
    )
    if os.path.exists(wout):
        with open(wout, encoding="utf-8") as fh:
            res["walk"] = json.load(fh)
    else:
        res["walk"] = dict(passed=False, error=p.stderr[-2000:])
    counts = res["walk"].get("counts", {})
    short = {k: [counts.get(k, 0), v] for k, v in WALK_MINIMUMS.items() if counts.get(k, 0) < v}
    res["walk"]["coverage_minimums"] = WALK_MINIMUMS
    res["walk"]["coverage_shortfalls"] = short
    res["walk"]["gate_passed"] = bool(res["walk"].get("passed") and not short)
    log(
        f"  walk exact={res['walk'].get('passed')} gate={res['walk']['gate_passed']} "
        f"transitions={counts.get('transitions')} exact_checks={counts.get('evaluations')}"
    )

    if a.speed:
        log(f"speed: {a.rounds} ABBA rounds, flag unset against RC-J, plus the null control")
        rounds, nulls = [], []
        for r in range(a.rounds):
            a1 = probe(rcj, "depth", 10, env_for(False))
            b1 = probe(ROOT, "depth", 10, env_for(False))
            b2 = probe(ROOT, "depth", 10, env_for(False))
            a2 = probe(rcj, "depth", 10, env_for(False))
            rounds.append(
                dict(
                    round=r,
                    rcj_nps=[a1["nps"], a2["nps"]],
                    off_nps=[b1["nps"], b2["nps"]],
                    ratio=(b1["nps"] + b2["nps"]) / (a1["nps"] + a2["nps"]),
                )
            )
            n1 = probe(rcj, "depth", 10, env_for(False))
            n2 = probe(rcj2, "depth", 10, env_for(False))
            n3 = probe(rcj2, "depth", 10, env_for(False))
            n4 = probe(rcj, "depth", 10, env_for(False))
            nulls.append(dict(round=r, ratio=(n2["nps"] + n3["nps"]) / (n1["nps"] + n4["nps"])))
        null_median = statistics.median(n["ratio"] for n in nulls)
        ratios = [x["ratio"] for x in rounds]
        valid = abs(null_median - 1.0) <= 0.02
        res["speed"] = dict(
            rounds=rounds,
            null_control=nulls,
            null_median=round(null_median, 4),
            valid=valid,
            formal="VALID" if valid else "INVALID / NON-DECISIVE",
            ratio_median=round(statistics.median(ratios), 4),
            ratio_min=round(min(ratios), 4),
            cost_pessimistic=round(1 - min(ratios), 4),
            cost_median=round(1 - statistics.median(ratios), 4),
            slowdown_time_pessimistic=round(1 / min(ratios) - 1, 4),
            slowdown_time_median=round(1 / statistics.median(ratios) - 1, 4),
            basis="ratio = flag-off NPS / RC-J NPS over depth-10 runs of the 24 openings "
            "(identical trees, so the time slowdown is 1/ratio - 1); NPS is whole-search wall "
            "time, including the Python root work both engines share",
        )
        log(
            f"  speed ratio median {res['speed']['ratio_median']} min {res['speed']['ratio_min']}; "
            f"null median {null_median:.4f} -> {res['speed']['formal']}"
        )

    res["inputs_unchanged_during_run"] = inputs_now() == res["inputs"]
    res["passed"] = bool(
        res["identity"]["passed"]
        and res["verify"]["passed"]
        and res["walk"].get("gate_passed")
        and res["inputs_unchanged_during_run"]
    )
    res["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    log(f"DONE passed={res['passed']} -> {os.path.abspath(a.out)}")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
