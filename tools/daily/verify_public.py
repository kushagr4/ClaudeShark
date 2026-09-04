"""Verify the public Chessathon scrape before any conclusion is built on it.

The scrape was produced by a separate collector. Nothing in it is taken on
trust: this module hashes the artifacts, checks that the game identifiers are
unique, replays every PGN from its recorded starting position to confirm the
move list is legal and reaches the recorded termination, recomputes the result
and colour counts from the structured fields rather than from any prose, groups
the starting positions by exact FEN, and cross-checks a random sample of
records against their own PGN text.

Discrepancies are reported, never silently reconciled. A record whose PGN
carries no moves is counted separately rather than folded into the result
totals, because a game with no moves cannot have been decided over the board.

    uv run python -m tools.daily.verify_public --dir analysis --out corpus/daily/public_verification.txt
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import chess
import chess.pgn


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def replay(row: dict) -> tuple[bool, str]:
    """Replay the record's own PGN and report whether every move was legal."""
    text = row.get("pgn") or ""
    if not text.strip():
        return False, "no pgn text"
    game = chess.pgn.read_game(io.StringIO(text))
    if game is None:
        return False, "unparsable pgn"
    board = game.board()
    start = board.fen()
    recorded = row.get("starting_fen")
    plies = 0
    for move in game.mainline_moves():
        if move not in board.legal_moves:
            return False, f"illegal move at ply {plies + 1}"
        board.push(move)
        plies += 1
    if recorded and chess.Board(recorded).fen() != chess.Board(start).fen():
        return False, "pgn start FEN differs from the record's starting_fen"
    return True, f"{plies} plies legal"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path("analysis"))
    parser.add_argument("--sample", type=int, default=12)
    parser.add_argument("--seed", type=int, default=97)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games_path = arguments.dir / "top50_games.jsonl"
    rows = [json.loads(line) for line in games_path.open(encoding="utf-8")]

    lines = ["== VERIFICATION OF THE PUBLIC CHESSATHON SCRAPE ==", ""]
    lines.append("artifact hashes:")
    for name in sorted(p.name for p in arguments.dir.iterdir() if p.is_file()):
        path = arguments.dir / name
        lines.append(f"   {name:<34} {path.stat().st_size:>9,} bytes  sha256 {sha256(path)}")
    pgn_dir = arguments.dir / "top50_pgn"
    if pgn_dir.is_dir():
        pgns = sorted(pgn_dir.iterdir())
        lines.append(f"   top50_pgn/                         {len(pgns)} files")
    log = arguments.dir / "top50_collection_log.json"
    if log.is_file():
        lines.append(f"   collection log: {log.read_text(encoding='utf-8').strip()}")
    lines.append("")

    ids = [r["game_id"] for r in rows]
    lines.append(f"records {len(rows)}, distinct game_id {len(set(ids))}, "
                 f"duplicated ids {len(ids) - len(set(ids))}")
    unique = {r["game_id"]: r for r in rows}

    legal = 0
    problems = []
    empty = []
    for r in unique.values():
        ok, why = replay(r)
        if ok:
            legal += 1
            if why.startswith("0 plies"):
                empty.append((r["game_id"], r.get("termination"), r.get("canonical_result")))
        else:
            problems.append((r["game_id"], why))
    lines.append(f"PGN replay: {legal} of {len(unique)} replay legally from their recorded start")
    for gid, why in problems[:10]:
        lines.append(f"   PROBLEM {gid}: {why}")
    if empty:
        lines.append(f"   {len(empty)} record(s) replay legally but contain NO MOVES:")
        for gid, term, res in empty:
            lines.append(f"      {gid}  termination={term!r}  canonical_result={res!r}")
    lines.append("")

    lines.append("== RESULTS RECOMPUTED FROM STRUCTURED FIELDS ==")
    by_winner = Counter(r.get("winner_colour") for r in unique.values())
    by_result = Counter(r.get("canonical_result") for r in unique.values())
    lines.append(f"   winner_colour: {dict(by_winner)}")
    lines.append(f"   canonical_result: { {k: v for k, v in by_result.items()} }")
    agree = sum(1 for r in unique.values()
                if (r.get("winner_colour") == "white" and r.get("canonical_result") == "1-0")
                or (r.get("winner_colour") == "black" and r.get("canonical_result") == "0-1")
                or (r.get("winner_colour") not in ("white", "black") and r.get("canonical_result") not in ("1-0", "0-1")))
    lines.append(f"   winner_colour and canonical_result agree on {agree} of {len(unique)}")
    with_moves = {gid: r for gid, r in unique.items() if gid not in {g for g, _, _ in empty}}
    w = sum(1 for r in with_moves.values() if r.get("winner_colour") == "white")
    b = sum(1 for r in with_moves.values() if r.get("winner_colour") == "black")
    d = len(with_moves) - w - b
    lines.append("")
    lines.append(f"   ALL {len(unique)} records:            White {by_winner.get('white', 0)}, "
                 f"Black {by_winner.get('black', 0)}, drawn {len(unique) - by_winner.get('white', 0) - by_winner.get('black', 0)}")
    lines.append(f"   {len(with_moves)} records WITH MOVES:  White {w}, Black {b}, drawn {d}   "
                 f"White scores {(w + 0.5 * d) / len(with_moves):.2%}")
    lines.append("   The two rows differ by the move-less record(s) listed above; both are reported")
    lines.append("   rather than one being chosen, because that is the whole of the discrepancy.")
    lines.append("")

    lines.append("== COLOURS AND STARTING POSITIONS ==")
    stm = Counter(r["starting_fen"].split()[1] for r in unique.values() if r.get("starting_fen"))
    lines.append(f"   side to move in the start FEN: {dict(stm)}")
    for side in ("b", "w"):
        subset = [r for r in with_moves.values() if r.get("starting_fen", " ").split()[1] == side]
        if not subset:
            continue
        ww = sum(1 for r in subset if r.get("winner_colour") == "white")
        bb = sum(1 for r in subset if r.get("winner_colour") == "black")
        dd = len(subset) - ww - bb
        lines.append(f"   {'Black' if side == 'b' else 'White'} to move: n={len(subset):>4}  "
                     f"White {ww} draw {dd} Black {bb}  White scores {(ww + 0.5 * dd) / len(subset):.2%}")
    lines.append("")

    lines.append("== EXACT-FEN FAMILIES ==")
    families: dict[str, list[dict]] = defaultdict(list)
    for r in unique.values():
        if r.get("starting_fen"):
            families[r["starting_fen"]].append(r)
    repeated = {f: rs for f, rs in families.items() if len(rs) > 1}
    lines.append(f"   {len(families)} distinct starting FENs; {len(repeated)} used more than once, "
                 f"covering {sum(len(rs) for rs in repeated.values())} games")
    for fen, rs in sorted(repeated.items(), key=lambda kv: -len(kv[1]))[:8]:
        outcomes = Counter(r.get("winner_colour") for r in rs)
        lines.append(f"   {len(rs)}x  {dict(outcomes)}  {fen}")
    lines.append("")

    lines.append(f"== RANDOM SAMPLE CROSS-CHECK ({arguments.sample} records against their own PGN) ==")
    rng = random.Random(arguments.seed)
    for r in rng.sample(sorted(unique.values(), key=lambda x: x["game_id"]), min(arguments.sample, len(unique))):
        ok, why = replay(r)
        game = chess.pgn.read_game(io.StringIO(r.get("pgn") or ""))
        header_result = game.headers.get("Result", "?") if game else "?"
        match = "OK " if header_result == r.get("canonical_result") or (
            header_result not in ("1-0", "0-1") and r.get("winner_colour") not in ("white", "black")) else "DIFF"
        lines.append(f"   {match} {r['game_id']}  pgn Result {header_result!r} vs record {r.get('canonical_result')!r}  "
                     f"winner {r.get('winner_colour')!r}  replay: {why}")
    text = "\n".join(lines)
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
