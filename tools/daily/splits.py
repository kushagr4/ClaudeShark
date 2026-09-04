"""Deterministic exact-FEN family splits of the observed competition positions.

The public scrape gives the organisers' own starting positions, which makes it
the right population for judging whether a candidate transfers to the
competition. It is also finite and easy to burn: once a pool has been used to
choose a coefficient it is no longer a holdout, and once it has been *inspected*
it is no longer pristine.

So the population is split once, deterministically, by **exact starting FEN
family**. Every game that begins from the same FEN goes to the same side of the
split, because two games from one position are not independent evidence about a
candidate. Splitting on games rather than families would leak.

Three parts:

    competition_diagnostic   where hypotheses may be formed and coefficients chosen
    competition_validation   read once, after a choice is frozen
    competition_holdout      not inspected during feature design

ClaudeShark's own rated starting positions are excluded entirely, in either
direction: they stay external deployment evidence and never enter selection.

The 113-position match already run against `competition_actual_pairs.json`
covers essentially this whole population, so that population is now
**exploratory distribution evidence**, not a pristine holdout. The splits here
exist for candidates chosen *after* it, and the holdout part of them is the
thing to keep clean from here on.

    uv run python -m tools.daily.splits --games analysis/top50_games.jsonl --out-dir corpus/daily/splits
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import chess

from tools.daily.realpool import OURS

SPLITS = (("competition_diagnostic", 0.50), ("competition_validation", 0.25), ("competition_holdout", 0.25))


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260904)
    arguments = parser.parse_args()
    rows = {r["game_id"]: r for r in (json.loads(line) for line in arguments.games.open(encoding="utf-8"))}

    families: dict[str, list[str]] = {}
    for r in rows.values():
        fen = r.get("starting_fen")
        if not fen or fen in OURS:
            continue
        families.setdefault(fen, []).append(r["game_id"])
    ordered = sorted(families)  # deterministic before shuffling
    rng = random.Random(arguments.seed)
    rng.shuffle(ordered)

    assigned: dict[str, list[str]] = {name: [] for name, _ in SPLITS}
    # Largest families first within the shuffled order would bias sizes, so the
    # shuffled order is walked and each family goes to whichever split is
    # furthest below its target share of *games*, which keeps game counts close
    # without ever separating a family.
    targets = {name: share for name, share in SPLITS}
    counts = dict.fromkeys(targets, 0)
    for fen in ordered:
        size = len(families[fen])
        total = sum(counts.values()) + size
        deficits = {name: targets[name] * total - counts[name] for name in targets}
        pick = max(deficits, key=lambda name: deficits[name])
        assigned[pick].append(fen)
        counts[pick] += size

    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "source": str(arguments.games),
        "source_sha256": hashlib.sha256(arguments.games.read_bytes()).hexdigest(),
        "seed": arguments.seed,
        "algorithm": "shuffle families with the seed, then assign each to the split furthest below its target share of games; families are never split",
        "excluded_our_own_rated_starts": sorted(OURS),
        "families_total": len(families),
        "games_total": sum(len(v) for v in families.values()),
        "splits": {},
    }
    lines = ["== EXACT-FEN FAMILY SPLITS OF THE OBSERVED COMPETITION POSITIONS ==",
             f"source {arguments.games} (sha256 {summary['source_sha256'][:16]}...), seed {arguments.seed}",
             f"{len(families)} families covering {sum(len(v) for v in families.values())} games; "
             f"ClaudeShark's own {len(OURS)} rated starts excluded entirely", ""]
    for name, share in SPLITS:
        fens = sorted(assigned[name])
        games = sum(len(families[f]) for f in fens)
        pairs = [{"id": f"{name[:4]}-{i:03d}", "cluster": 9000 + abs(hash(f)) % 100000, "fen": f,
                  "uses_in_scrape": len(families[f]),
                  "side_to_move": "w" if chess.Board(f).turn == chess.WHITE else "b",
                  "fullmove": chess.Board(f).fullmove_number, "phase": "opening"}
                 for i, f in enumerate(fens)]
        # Clusters must be unique inside a split; fall back to the index if a hash collides.
        seen: set[int] = set()
        for i, entry in enumerate(pairs):
            if entry["cluster"] in seen:
                entry["cluster"] = 900000 + i
            seen.add(entry["cluster"])
        path = arguments.out_dir / f"{name}.json"
        path.write_text(json.dumps(pairs, indent=1) + "\n", encoding="utf-8")
        members = arguments.out_dir / f"{name}_fens.txt"
        members.write_text("\n".join(fens) + "\n", encoding="utf-8")
        summary["splits"][name] = {
            "target_share_of_games": share, "families": len(fens), "games": games,
            "pairs_file": str(path), "fens_file": str(members),
            "fens_sha256": digest("\n".join(fens)),
            "side_to_move": dict(Counter(e["side_to_move"] for e in pairs)),
            "repeated_families": sum(1 for f in fens if len(families[f]) > 1),
        }
        lines.append(f"{name:<24} families {len(fens):>4}  games {games:>4} "
                     f"({games / summary['games_total']:5.1%})  repeated families {summary['splits'][name]['repeated_families']:>3}  "
                     f"side to move {summary['splits'][name]['side_to_move']}")
        lines.append(f"   fens sha256 {summary['splits'][name]['fens_sha256']}")
        lines.append(f"   {path}")
    overlap = set()
    for name, _ in SPLITS:
        for other, _ in SPLITS:
            if name < other:
                overlap |= set(assigned[name]) & set(assigned[other])
    lines.append("")
    lines.append(f"families appearing in more than one split: {len(overlap)} (must be 0)")
    assert not overlap, "a family was split across parts"
    lines.append("")
    lines.append("The 113-position match already run covers essentially this whole population, so it is")
    lines.append("exploratory distribution evidence. The holdout part is for candidates chosen after it")
    lines.append("and must not be inspected during feature design.")
    (arguments.out_dir / "splits_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    text = "\n".join(lines)
    (arguments.out_dir / "splits.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
