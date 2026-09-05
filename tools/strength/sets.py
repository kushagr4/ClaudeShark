"""Freeze the start-position sets for the external-strength programme.

The organisers' own starting positions, as observed in public games, are the
right population for an external benchmark. They are split ONCE, by exact
starting FEN, into four sets with distinct jobs:

    dev        the 100-game baseline and every candidate screen
    val        candidate confirmation before a promotion
    holdout_a  the qualification test (never used for design)
    holdout_b  the confirmation test (never used for design)

The two holdouts are drawn only from positions that no ClaudeShark arena has
ever played (they were absent from the 113-position competition suite), so
that qualification starts are pristine. Dev and val come from the positions
the internal arenas already used. ClaudeShark's own rated starts are dropped
everywhere. Every position is checked with the arena's own suitability test
before it is frozen.

    uv run python -m tools.strength.sets --games analysis/refresh_2026-09-05/top50_games.jsonl \
        --previous corpus/daily/pool/competition_actual_suite.jsonl --out-dir corpus/strength
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from tools.corpus.suite import load_suite
from tools.daily.realpool import OURS
from tools.positions import unsuitable

OUR_TEAM = "6532bc56-58ba-48b5-977d-0c039fe3fd7b"
SIZES = {"dev": 50, "val": 40, "holdout_a": 50, "holdout_b": 50}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _write(path: Path, name: str, fens: list[str], uses: Counter[str], note: str) -> str:
    fen_hash = _sha("\n".join(fens))
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "record": "header", "suite": f"strength_{name}", "version": "2026-09-05",
            "source": note, "positions": len(fens), "hash": fen_hash,
        }) + "\n")
        for index, fen in enumerate(fens):
            handle.write(json.dumps({
                "id": f"{name}-{index:03d}", "cluster": int(_sha(fen)[:8], 16) % 100000,
                "fen": fen, "uses_in_scrape": uses[fen],
            }) + "\n")
    return fen_hash


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True,
                        help="the suite internal arenas already played; its positions "
                             "feed dev/val only")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260905)
    arguments = parser.parse_args()

    uses: Counter[str] = Counter()
    own: set[str] = set(OURS)
    for line in arguments.games.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        game = json.loads(line)
        fen = game.get("starting_fen")
        if not fen:
            continue
        uses[fen] += 1
        sides = {game.get("team_id"), game.get("opponent_id")}
        for colour in ("white", "black"):
            side = game.get(colour)
            if isinstance(side, dict):
                sides.add(side.get("team_id"))
        if OUR_TEAM in sides:
            own.add(fen)

    _, previous = load_suite(arguments.previous)
    played = set(previous)
    candidates = [f for f in uses if f not in own]
    bad = {fen for _, _, fen, _ in unsuitable(tuple(candidates), "strength")}
    candidates = [f for f in candidates if f not in bad]
    fresh = sorted(f for f in candidates if f not in played)
    seen = sorted(f for f in candidates if f in played)

    rng = random.Random(arguments.seed)
    rng.shuffle(fresh)
    rng.shuffle(seen)
    need_fresh = SIZES["holdout_a"] + SIZES["holdout_b"]
    need_seen = SIZES["dev"] + SIZES["val"]
    if len(fresh) < need_fresh or len(seen) < need_seen:
        raise SystemExit(f"not enough positions: fresh {len(fresh)} (need {need_fresh}), "
                         f"seen {len(seen)} (need {need_seen})")
    sets = {
        "dev": seen[: SIZES["dev"]],
        "val": seen[SIZES["dev"]: SIZES["dev"] + SIZES["val"]],
        "holdout_a": fresh[: SIZES["holdout_a"]],
        "holdout_b": fresh[SIZES["holdout_a"]: SIZES["holdout_a"] + SIZES["holdout_b"]],
    }
    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256(arguments.games.read_bytes()).hexdigest()
    lines = [
        "# Strength-programme start sets (frozen)",
        f"source {arguments.games} sha256 {source_hash}",
        f"previous suite {arguments.previous} ({len(played)} positions already played "
        f"by internal arenas)",
        f"seed {arguments.seed}; {sum(uses.values())} games, {len(uses)} distinct starts, "
        f"{len(own)} of ours excluded, {len(bad)} unsuitable, {len(fresh)} fresh, {len(seen)} seen",
        "",
    ]
    for name, fens in sets.items():
        history = ("never played by an internal arena" if name.startswith("holdout")
                   else "already played by internal arenas")
        note = f"organiser starts from {arguments.games.name}; {history}; seed {arguments.seed}"
        fen_hash = _write(arguments.out_dir / f"{name}.jsonl", name, fens, uses, note)
        stm = Counter(f.split()[1] for f in fens)
        lines.append(f"{name:10s} positions {len(fens):3d}  side to move {dict(stm)}  "
                     f"sha256 {fen_hash}")
    members = list(sets.values())
    overlap = sum(len(set(a) & set(b)) for i, a in enumerate(members) for b in members[i + 1:])
    lines.append(f"\npositions in more than one set: {overlap} (must be 0)")
    lines.append("dev: baseline + candidate screens. val: pre-promotion confirmation. "
                 "holdout_a: qualification. holdout_b: confirmation. Never reshuffle.")
    (arguments.out_dir / "FROZEN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
