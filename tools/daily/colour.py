"""Colour audit over every retained paired fixed-depth corpus.

Two different questions are answered from the same files and must not be
confused.

ENGINE COLOUR SPLIT asks how the candidate scored when it happened to be
White and when it happened to be Black. Because every start position is
played twice with the colours swapped, a difference here is a property of the
candidate relative to its baseline, not of the position pool.

SIDE-TO-MOVE RESULT asks, ignoring which engine was which, how often White
won. Both players are near-identical engines on the same start positions, so
this measures the pool: whether the retained start positions favour White or
Black at all, and by how much.

    uv run python -m tools.daily.colour --out corpus/daily/colour_split.txt
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

CORPORA = {
    "postmortem (rated-v1 self, 100 pairs)": "corpus/postmortem/games/fixed_depth.jsonl",
    "mopup gate2": "corpus/mopup/games/gate2_fixed_depth.jsonl",
    "passed gate2": "corpus/passed/games/gate2_fixed_depth.jsonl",
    "kingpawn gate2 (V2.1 v rated-v1)": "corpus/v2/kp/games/gate2_fixed_depth.jsonl",
    "kingpawn secondary (V2.1 v v0_8_passed)": "corpus/v2/kp/games/secondary_vs_passed.jsonl",
    "lowmat gate2 (V2.2a v V2.1)": "corpus/v2/fw/lowmat/games/gate2_fixed_depth.jsonl",
    "lowmat targeted (V2.2a v V2.1)": "corpus/v2/fw/lowmat/games/targeted_fixed_depth.jsonl",
}


def elo(score: float) -> float:
    score = min(max(score, 1e-6), 1 - 1e-6)
    return -400.0 * math.log10(1.0 / score - 1.0)


def boot(pairs: list[tuple[int, float]], n: int = 20000, seed: int = 7) -> tuple[float, float]:
    """Cluster bootstrap on the score, resampling whole start clusters."""
    by = defaultdict(list)
    for cluster, s in pairs:
        by[cluster].append(s)
    keys = list(by)
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        vals = []
        for _ in keys:
            vals += by[rng.choice(keys)]
        out.append(sum(vals) / len(vals))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n)]


def wdl(scores: list[float]) -> tuple[int, int, int]:
    c = Counter(scores)
    return c[1.0], c[0.5], c[0.0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    lines = ["== COLOUR AUDIT OVER RETAINED PAIRED FIXED-DEPTH CORPORA ==", ""]
    all_side = []
    for label, path in CORPORA.items():
        p = Path(path)
        if not p.exists():
            lines.append(f"{label}: MISSING ({path})")
            continue
        games = [json.loads(line) for line in p.open(encoding="utf-8")]
        lines.append(f"{label}   n={len(games)}   {path}")
        # Engine colour split: candidate's score when it was White / Black.
        for cw, name in ((True, "candidate as White"), (False, "candidate as Black")):
            rs = [g for g in games if g["cand_white"] == cw]
            s = [g["cand_score"] for g in rs]
            w, d, ls = wdl(s)
            if rs:
                lo, hi = boot([(int(g["cluster"]), g["cand_score"]) for g in rs])
                lines.append(f"   {name:<22} +{w:<3} ={d:<3} -{ls:<3}  score {sum(s) / len(s):6.1%}  Elo {elo(sum(s) / len(s)):+6.0f}  cluster boot {lo:.1%}..{hi:.1%}")
        # Side-to-move result: who won, ignoring which engine.
        side = []
        for g in games:
            white_score = g["cand_score"] if g["cand_white"] else 1.0 - g["cand_score"]
            side.append((int(g["cluster"]), white_score))
            all_side.append((f"{label}:{g['cluster']}", white_score))
        s = [x for _, x in side]
        w, d, ls = wdl(s)
        lo, hi = boot(side)
        lines.append(f"   {'WHITE (either engine)':<22} +{w:<3} ={d:<3} -{ls:<3}  score {sum(s) / len(s):6.1%}  Elo {elo(sum(s) / len(s)):+6.0f}  cluster boot {lo:.1%}..{hi:.1%}")
        # A paired match confounds two effects. Each start position is played twice
        # with the colours swapped, so the candidate's average over the two is its
        # own edge over the baseline, and half the difference between them is the
        # advantage of the move itself in this pool. Reading "candidate as White
        # scored more than candidate as Black" as a colour weakness of the
        # candidate is the mistake this decomposition prevents.
        cw = [g["cand_score"] for g in games if g["cand_white"]]
        cb = [g["cand_score"] for g in games if not g["cand_white"]]
        if cw and cb:
            a, b = sum(cw) / len(cw), sum(cb) / len(cb)
            lines.append(f"   {'decomposition':<22} candidate edge over baseline {(a + b) / 2 - 0.5:+.1%}   advantage of having White {(a - b) / 2:+.1%}")
        lines.append("")
    lines.append("== POOLED SIDE-TO-MOVE RESULT ACROSS ALL CORPORA (clusters namespaced per corpus) ==")
    s = [x for _, x in all_side]
    w, d, ls = wdl(s)
    by = defaultdict(list)
    for k, v in all_side:
        by[k].append(v)
    keys = list(by)
    rng = random.Random(11)
    outs = []
    for _ in range(20000):
        vals = []
        for _ in keys:
            vals += by[rng.choice(keys)]
        outs.append(sum(vals) / len(vals))
    outs.sort()
    lines.append(f"   White +{w} ={d} -{ls}   n={len(s)}   score {sum(s) / len(s):.1%}   Elo {elo(sum(s) / len(s)):+.0f}   cluster boot {outs[500]:.1%}..{outs[19500]:.1%}   ({len(keys)} clusters)")
    lines.append("   Note: both sides of every pair are the same two engines on the same start position,")
    lines.append("   so this is a property of the retained start-position pool and the move, not of either engine.")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
