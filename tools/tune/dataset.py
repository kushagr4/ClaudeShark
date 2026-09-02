"""Verify the labelled pool and freeze a by-game train/validation/test split.

Verification is done from the raw labels, independently of the feature cache,
so that a label problem is found before anything is fitted on it. The checks
that matter most are the sign conventions: a perspective error is the single
most likely way to manufacture an absurd fitted material coefficient.

The split is by **source game**, never by position -- two positions from one
game share almost everything, and a random split would leak. It is stratified
by phase bucket and material balance so the three parts are comparable, and
frozen to `corpus/tune/split.json` under a fixed seed.

    uv run python -m tools.tune.dataset --labelled corpus/candidates_labelled.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import chess

SPLIT_PATH = Path("corpus/tune/split.json")
SEED = 20260902


def load_rows(labelled: Path) -> tuple[dict, list[dict]]:
    header: dict = {}
    rows: list[dict] = []
    with labelled.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record") == "header":
                header = record
            else:
                rows.append(record)
    return header, rows


def verify(labelled: Path) -> list[str]:
    header, rows = load_rows(labelled)
    out: list[str] = []
    problems = 0

    out.append(f"file            {labelled}")
    out.append(f"positions       {len(rows)}   (header says {header.get('positions')})")
    oracle = header.get("oracle", {})
    out.append(f"oracle          {oracle.get('engine')}  nodes={header.get('nodes')}  "
               f"multipv={header.get('multipv')}  options={oracle.get('options')}")
    outside = not Path(str(oracle.get("binary"))).resolve().is_relative_to(Path(".").resolve())
    sha = str(oracle.get("binary_sha256"))[:16]
    out.append(f"binary sha256   {sha}  (outside repo: {outside})")

    # --- sign conventions -------------------------------------------------
    stm_agree = wdl_agree = 0
    mates = 0
    missing_wdl = 0
    for r in rows:
        ref = r["reference"]
        board = chess.Board(r["fen"])
        sign = 1 if board.turn == chess.WHITE else -1
        if ref.get("mate") is not None:
            mates += 1
        if ref.get("cp_white") is None or ref.get("cp_stm") is None:
            continue
        if ref["cp_white"] == sign * ref["cp_stm"]:
            stm_agree += 1
        if ref.get("wdl_white") and ref.get("wdl_stm"):
            w, d, l_ = ref["wdl_stm"]
            expect = [w, d, l_] if sign == 1 else [l_, d, w]
            if list(ref["wdl_white"]) == expect:
                wdl_agree += 1
        else:
            missing_wdl += 1
    out.append(f"cp_white == sign*cp_stm      {stm_agree}/{len(rows)}")
    out.append(f"wdl_white consistent w/ stm  {wdl_agree}/{len(rows)}   "
               f"(missing wdl: {missing_wdl})")
    out.append(f"mate-labelled positions      {mates}")
    if stm_agree != len(rows):
        problems += 1
        out.append("  !! perspective inconsistency between cp_white and cp_stm")

    # cp vs expected-score direction: they must agree in sign.
    agree_dir = 0
    counted = 0
    for r in rows:
        ref = r["reference"]
        if ref.get("cp_white") is None or not ref.get("wdl_white"):
            continue
        w, d, l_ = ref["wdl_white"]
        es = (w + d / 2) / 1000
        if abs(ref["cp_white"]) < 15:
            continue
        counted += 1
        if (ref["cp_white"] > 0) == (es > 0.5):
            agree_dir += 1
    out.append(f"cp sign agrees with WDL side  {agree_dir}/{counted} (|cp| >= 15)")

    # static evaluator direction sanity: correlation sign with oracle
    from cs_eval import evaluate

    xs, ys = [], []
    for r in rows[::7]:
        board = chess.Board(r["fen"])
        sign = 1 if board.turn == chess.WHITE else -1
        xs.append(sign * evaluate(board))
        ys.append(r["reference"]["cp_white"])
    import numpy as np

    corr = float(np.corrcoef(xs, ys)[0, 1])
    out.append(f"static (white POV) vs oracle cp_white correlation: {corr:+.3f}  "
               "(must be positive)")
    if corr <= 0:
        problems += 1
        out.append("  !! static evaluator and oracle disagree in sign -- perspective bug")

    # --- duplicates, games, distributions ---------------------------------
    fens = [r["fen"] for r in rows]
    placements = [f.split(" ")[0] for f in fens]
    out.append(f"unique FENs                  {len(set(fens))}/{len(fens)}")
    out.append(f"unique placements (ignore stm/ep/counters) {len(set(placements))}")
    games = Counter(r["game_id"] for r in rows)
    out.append(f"source games                 {len(games)}   positions/game: "
               f"min {min(games.values())} median {sorted(games.values())[len(games) // 2]} "
               f"max {max(games.values())}")
    invalid = [f for f in fens if not chess.Board(f).is_valid()]
    out.append(f"invalid FENs                 {len(invalid)}")
    if invalid:
        problems += 1

    phases = Counter(r["structure"]["phase"] for r in rows)
    out.append(f"phase                        {dict(phases)}")
    ph24 = Counter(r["structure"]["phase24"] for r in rows)
    out.append(f"phase24 buckets              0-6:{sum(v for k, v in ph24.items() if k <= 6)}  "
               f"7-12:{sum(v for k, v in ph24.items() if 7 <= k <= 12)}  "
               f"13-18:{sum(v for k, v in ph24.items() if 13 <= k <= 18)}  "
               f"19-24:{sum(v for k, v in ph24.items() if k >= 19)}")
    md = Counter(max(-4, min(4, r["structure"]["material_diff"])) for r in rows)
    out.append(f"material_diff (clamped +/-4) {dict(sorted(md.items()))}")
    cps = sorted(r["reference"]["cp_white"] for r in rows
                 if r["reference"].get("cp_white") is not None)
    q = lambda p: cps[int(p * (len(cps) - 1))]  # noqa: E731
    out.append(f"oracle cp_white quantiles    p1 {q(0.01)} p5 {q(0.05)} p25 {q(0.25)} "
               f"p50 {q(0.5)} p75 {q(0.75)} p95 {q(0.95)} p99 {q(0.99)}")
    out.append(f"|cp_white| > 600             {sum(1 for c in cps if abs(c) > 600)}"
               f"   > 1000: {sum(1 for c in cps if abs(c) > 1000)}")
    out.append(f"PROBLEMS: {problems}")
    return out


def make_split(labelled: Path, seed: int = SEED) -> dict:
    """Split by game, stratified on (phase bucket, |material_diff| bucket)."""
    _, rows = load_rows(labelled)
    by_game: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_game[r["game_id"]].append(r)

    def stratum(game_rows: list[dict]) -> str:
        r = game_rows[len(game_rows) // 2]
        ph = r["structure"]["phase24"]
        bucket = "eg" if ph <= 8 else ("mid" if ph <= 16 else "op")
        bal = "bal" if abs(r["structure"]["material_diff"]) <= 1 else "imb"
        return f"{bucket}:{bal}"

    strata: dict[str, list[str]] = defaultdict(list)
    for gid, grows in by_game.items():
        strata[stratum(grows)].append(gid)

    rng = random.Random(seed)
    assign: dict[str, str] = {}
    for _name, gids in sorted(strata.items()):
        gids = sorted(gids)
        rng.shuffle(gids)
        n = len(gids)
        n_val = round(0.15 * n)
        n_test = round(0.15 * n)
        for i, gid in enumerate(gids):
            assign[gid] = "test" if i < n_test else ("val" if i < n_test + n_val else "train")

    counts = Counter(assign[r["game_id"]] for r in rows)
    digest = hashlib.sha256(json.dumps(assign, sort_keys=True).encode()).hexdigest()[:16]
    split = {
        "seed": seed,
        "labelled": str(labelled),
        "games": len(by_game),
        "positions": dict(counts),
        "strata": {k: len(v) for k, v in sorted(strata.items())},
        "hash": digest,
        "assign": assign,
    }
    SPLIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPLIT_PATH.write_text(json.dumps(split, indent=1, sort_keys=True), encoding="utf-8")
    return split


def load_split() -> dict[str, str]:
    return json.loads(SPLIT_PATH.read_text(encoding="utf-8"))["assign"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the labelled pool and freeze a split.")
    parser.add_argument("--labelled", type=Path, default=Path("corpus/candidates_labelled.jsonl"))
    parser.add_argument("--split", action="store_true", help="also write the split")
    arguments = parser.parse_args()
    for line in verify(arguments.labelled):
        print(line)
    if arguments.split:
        split = make_split(arguments.labelled)
        print(f"\nsplit written to {SPLIT_PATH}: {split['positions']} hash {split['hash']}")
        print(f"strata (games): {split['strata']}")


if __name__ == "__main__":
    main()
