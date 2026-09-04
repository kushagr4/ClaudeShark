"""Which of several engine variants picks better moves, judged by the oracle?

Node counts and calibration statistics both mislead here. A change that makes
the engine's numbers agree better with Stockfish has not been shown to play
better, and the user's standing rule is that a calibration change must never be
scored as a quality improvement. So the only thing measured is the move: each
variant searches each position at a fixed depth, and the oracle scores the
position that results. Higher is better, and the oracle's own first choice is
reported as the ceiling.

**The mean loss is reported alongside robust statistics, and the robust ones
are the ones to read.** A single position where one variant walks into a mate
contributes ten thousand centipawns to that variant's total and about three
hundred to a thirty-position bucket mean, which is larger than any real
difference between two builds of the same engine. The first run of this tool on
the tempo family produced exactly that: a validation endgame bucket reading 326
for two variants and 24 for the other two, entirely from one position. The
count of losses at or above 100 and 300 centipawns, the median, and a mean with
each loss clamped at 1,000 are printed for that reason, and the per-position
losses are written to the JSONL so the outliers can be found.

Positions are split by source cluster, never by row, so a variant chosen on the
diagnostic half has not seen the validation half. The validation column is
printed with both halves so the split is visible, but the intended use is to
select on the diagnostic column and read validation exactly once.

    uv run python -m tools.daily.variants --engines champions/v2_1_kingpawn champions/v2_1_kingpawn_tempo24 --out corpus/daily/tempo_variants.txt
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

import chess

from tools.corpus.oracle import MATE_CP, label_many
from tools.postmortem.play import Engine

CORPORA = (
    "corpus/postmortem/games/annotated.jsonl",
    "corpus/v2/kp/games/gate2_annotated.jsonl",
    "corpus/passed/games/gate2_annotated.jsonl",
    "corpus/mopup/games/gate2_annotated.jsonl",
)

PHASE_WEIGHT = {chess.KNIGHT: 1, chess.BISHOP: 1, chess.ROOK: 2, chess.QUEEN: 4}


def phase_of(board: chess.Board) -> int:
    return min(24, sum(w * (len(board.pieces(pt, chess.WHITE)) + len(board.pieces(pt, chess.BLACK)))
                       for pt, w in PHASE_WEIGHT.items()))


def bucket(phase: int) -> str:
    return ("opening" if phase >= 18 else "middlegame" if phase >= 10
            else "late" if phase >= 4 else "endgame")


def sample(per_bucket: int, seed: int, clamp: int) -> list[dict]:
    """An unselected, phase-stratified sample. Not conditioned on the engine having erred."""
    pools: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for path in CORPORA:
        p = Path(path)
        if not p.exists():
            continue
        for line in p.open(encoding="utf-8"):
            g = json.loads(line)
            half = "diagnostic" if int(g["cluster"]) % 2 == 0 else "validation"
            for m in g["moves"]:
                sf_white = m.get("sf_cp_white_before")
                if sf_white is None or abs(sf_white) > clamp:
                    continue
                board = chess.Board(m["fen"])
                pools[(half, bucket(phase_of(board)))].append({
                    "fen": m["fen"], "half": half, "phase": bucket(phase_of(board)),
                    "cluster": int(g["cluster"]), "sf_best": m["sf_best"],
                    "sf_before": sf_white if board.turn == chess.WHITE else -sf_white,
                })
    rng = random.Random(seed)
    out: list[dict] = []
    for key in sorted(pools):
        rows = pools[key]
        rng.shuffle(rows)
        seen: set[str] = set()
        kept = []
        for r in rows:
            if r["fen"] in seen:
                continue
            seen.add(r["fen"])
            kept.append(r)
            if len(kept) >= per_bucket:
                break
        out += kept
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engines", type=Path, nargs="+", required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--per-bucket", type=int, default=40)
    parser.add_argument("--clamp", type=int, default=900)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--seed", type=int, default=53)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    positions = sample(arguments.per_bucket, arguments.seed, arguments.clamp)
    print(f"{len(positions)} positions "
          f"({sum(r['half'] == 'diagnostic' for r in positions)} diagnostic, "
          f"{sum(r['half'] == 'validation' for r in positions)} validation)", flush=True)

    names = [str(e) for e in arguments.engines]
    for engine_dir in arguments.engines:
        name = str(engine_dir)
        engine = Engine(engine_dir, arguments.depth)
        try:
            for i, r in enumerate(positions, start=1):
                engine.ask("new")
                reply = engine.ask(f"go {r['fen']}")
                r[name] = {"move": reply["move"], "score": reply["score"], "nodes": reply.get("nodes")}
                if i % 60 == 0:
                    print(f"   {name}: {i}/{len(positions)}", flush=True)
        finally:
            engine.close()
        print(f"  {name} done", flush=True)

    keys: dict[tuple[str, str], None] = {}
    for r in positions:
        for name in names:
            if r[name]["move"]:
                keys[(r["fen"], r[name]["move"])] = None
        if r["sf_best"]:
            keys[(r["fen"], r["sf_best"])] = None
    pairs = list(keys)
    after = []
    for fen, move in pairs:
        board = chess.Board(fen)
        board.push_uci(move)
        after.append(board.fen())
    print(f"scoring {len(after)} resulting positions at {arguments.nodes} nodes", flush=True)
    labels = label_many(after, arguments.nodes, workers=arguments.workers, progress=True)
    value: dict[tuple[str, str], int] = {}
    for (fen, move), label in zip(pairs, labels, strict=True):
        white = chess.Board(fen).turn == chess.WHITE
        value[(fen, move)] = max(-MATE_CP, min(MATE_CP, label.cp_white if white else -label.cp_white))

    def loss(r: dict, name: str) -> int:
        move = r[name]["move"]
        if not move or not r["sf_best"]:
            return 0
        return max(0, value[(r["fen"], r["sf_best"])] - value[(r["fen"], move)])

    lines = [f"== VARIANT MOVE QUALITY: {len(positions)} positions at depth {arguments.depth}, oracle at {arguments.nodes} nodes ==",
             "Loss is the oracle score of its first choice minus the oracle score after the variant's move, floored at zero.",
             "Split by source cluster: even clusters diagnostic, odd validation. Select on diagnostic, read validation once.", ""]
    for half in ("diagnostic", "validation"):
        rows = [r for r in positions if r["half"] == half]
        lines.append(f"-- {half} ({len(rows)} positions) --")
        lines.append(f"   {'engine':<44} {'mean':>8} {'clamped':>8} {'median':>7} {'>=100':>6} {'>=300':>6} {'= oracle':>9} {'nodes':>10}")
        for name in names:
            losses = [loss(r, name) for r in rows]
            agree = sum(1 for r in rows if r[name]["move"] == r["sf_best"])
            lines.append(f"   {name:<44} {statistics.mean(losses):>8.1f} "
                         f"{statistics.mean(min(x, 1000) for x in losses):>8.1f} {statistics.median(losses):>7.0f} "
                         f"{sum(1 for x in losses if x >= 100):>6} {sum(1 for x in losses if x >= 300):>6} "
                         f"{agree:>5}/{len(rows):<3} "
                         f"{statistics.mean(r[name]['nodes'] or 0 for r in rows):>10,.0f}")
        lines.append("")
        for phase in ("opening", "middlegame", "late", "endgame"):
            sub = [r for r in rows if r["phase"] == phase]
            if not sub:
                continue
            cells = "  ".join(f"{name.split('/')[-1]} {statistics.mean(loss(r, name) for r in sub):.0f}" for name in names)
            lines.append(f"   {phase:<12} n={len(sub):<4} {cells}")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in positions) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
