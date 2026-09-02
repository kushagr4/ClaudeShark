"""Extract candidate positions from master games, by opening family.

Source games are The Week in Chess (TWIC) PGN issues, kept outside the
repository (they are large and not ours to redistribute). Each candidate keeps
enough provenance to find the game again: issue file, event, players, ratings,
date, round, ECO and the ply at which it was sampled.

Opening names are only a way to reach diverse structures. The family is
recognised from the first moves, with the ECO tag as a fallback, and every
family is capped so mainstream openings do not drown the niche ones. What
comes out is a *candidate pool*: nothing here decides whether a position is
near-level -- that is the oracle's job in ``build.py``.

    uv run python -m tools.corpus.extract --pgn-dir C:\\Users\\epick\\engines\\twic ^
        --out corpus\\candidates.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chess
import chess.pgn

from tools.corpus.structure import analyse_structure

MAINSTREAM = (
    "ruy_lopez", "italian", "scotch", "queens_gambit_declined", "queens_gambit_accepted",
    "slav", "semi_slav", "sicilian", "french", "caro_kann", "kings_indian", "grunfeld",
    "nimzo_indian", "queens_indian", "english", "reti", "catalan",
)
NICHE = (
    "benoni", "benko", "dutch", "pirc", "modern", "alekhine", "scandinavian", "kings_gambit",
    "evans_gambit", "danish_gambit", "smith_morra", "budapest", "trompowsky", "bird",
    "owens", "polish", "london", "colle", "nimzo_larsen", "vienna", "petrov", "philidor",
    "four_knights", "bogo_indian", "old_indian", "chigorin", "albin", "sicilian_alapin",
    "sicilian_closed", "torre", "ponziani", "bishops_opening", "centre_game", "other",
)


def _san_list(game: chess.pgn.Game, plies: int) -> list[str]:
    board = game.board()
    sans: list[str] = []
    for move in game.mainline_moves():
        sans.append(board.san(move))
        board.push(move)
        if len(sans) >= plies:
            break
    return sans


def _played(sans: list[str], colour: str, move: str, within: int) -> bool:
    """Did ``colour`` play ``move`` (SAN, check marks ignored) within N moves?"""
    start = 0 if colour == "w" else 1
    for index in range(start, min(len(sans), 2 * within), 2):
        if sans[index].rstrip("+#") == move:
            return True
    return False


def opening_family(sans: list[str], eco: str) -> str:
    """Name the opening family from the first moves, falling back to ECO."""
    w = [s.rstrip("+#") for s in sans[0::2]]
    b = [s.rstrip("+#") for s in sans[1::2]]

    def wm(i: int) -> str:
        return w[i] if i < len(w) else ""

    def bm(i: int) -> str:
        return b[i] if i < len(b) else ""

    first, reply = wm(0), bm(0)

    if first == "b4":
        return "polish"
    if first == "b3":
        return "nimzo_larsen"
    if first == "f4":
        return "bird"

    if first == "e4":
        if reply == "c5":
            if wm(1) == "c3":
                return "sicilian_alapin"
            if wm(1) == "d4" and bm(1) == "cxd4" and wm(2) == "c3":
                return "smith_morra"
            if wm(1) in ("Nc3", "f4", "g3") and not _played(sans, "w", "d4", 6):
                return "sicilian_closed"
            return "sicilian"
        if reply == "e6":
            return "french"
        if reply == "c6":
            return "caro_kann"
        if reply == "d5":
            return "scandinavian"
        if reply == "Nf6":
            return "alekhine"
        if reply == "d6":
            if _played(sans, "b", "e5", 4):
                return "philidor"
            return "pirc"
        if reply == "g6":
            return "modern"
        if reply == "b6":
            return "owens"
        if reply == "e5":
            if wm(1) == "f4":
                return "kings_gambit"
            if wm(1) == "Nc3":
                if bm(1) == "Nf6" and wm(2) == "Nf3" and bm(2) == "Nc6":
                    return "four_knights"
                return "vienna"
            if wm(1) == "Bc4":
                return "bishops_opening"
            if wm(1) == "d4":
                if bm(1) == "exd4" and wm(2) == "c3":
                    return "danish_gambit"
                return "centre_game"
            if wm(1) == "Nf3":
                if bm(1) == "Nf6":
                    return "petrov"
                if bm(1) == "d6":
                    return "philidor"
                if bm(1) == "Nc6":
                    if wm(2) == "Bb5":
                        return "ruy_lopez"
                    if wm(2) == "Bc4":
                        if bm(2) == "Bc5" and wm(3) == "b4":
                            return "evans_gambit"
                        return "italian"
                    if wm(2) == "d4":
                        return "scotch"
                    if wm(2) == "c3":
                        return "ponziani"
                    if wm(2) == "Nc3":
                        if bm(2) == "Nf6":
                            return "four_knights"
                        return "vienna"
            return "other"
        return "other"

    if first == "d4":
        if reply == "f5" or (reply == "e6" and bm(1) == "f5"):
            return "dutch"
        if reply == "Nf6":
            if wm(1) == "Bg5":
                return "trompowsky"
            if wm(1) == "Bf4" or (wm(1) == "Nf3" and wm(2) == "Bf4"):
                return "london"
            if wm(1) == "Nf3" and wm(2) == "Bg5":
                return "torre"
            if wm(1) == "Nf3" and wm(2) == "e3" and _played(sans, "w", "Bd3", 6) \
                    and not _played(sans, "w", "c4", 6):
                return "colle"
            if bm(1) == "e5" and wm(1) == "c4":
                return "budapest"
            if bm(1) == "c5" and _played(sans, "w", "d5", 4):
                if _played(sans, "b", "b5", 5):
                    return "benko"
                return "benoni"
            if bm(1) == "g6":
                if _played(sans, "b", "d5", 5) and _played(sans, "w", "c4", 5):
                    return "grunfeld"
                if _played(sans, "w", "c4", 5):
                    return "kings_indian"
                if wm(1) == "Bf4" or wm(2) == "Bf4":
                    return "london"
                return "kings_indian"
            if bm(1) == "d6" and not _played(sans, "b", "g6", 5):
                return "old_indian"
            if bm(1) == "e6":
                if _played(sans, "w", "g3", 4) and _played(sans, "w", "c4", 4):
                    return "catalan"
                if wm(2) == "Nc3" and bm(2) == "Bb4":
                    return "nimzo_indian"
                if wm(2) == "Nf3" and bm(2) == "b6":
                    return "queens_indian"
                if wm(2) == "Nf3" and bm(2) == "Bb4":
                    return "bogo_indian"
                if _played(sans, "b", "d5", 4) and _played(sans, "w", "c4", 4):
                    if _played(sans, "b", "c6", 6):
                        return "semi_slav"
                    return "queens_gambit_declined"
                if _played(sans, "w", "Bf4", 4):
                    return "london"
                if _played(sans, "w", "Bg5", 4):
                    return "torre"
                if _played(sans, "w", "e3", 4) and _played(sans, "w", "Bd3", 6):
                    return "colle"
                return "other"
            if bm(1) == "d5":
                if _played(sans, "w", "g3", 4) and _played(sans, "w", "c4", 4):
                    return "catalan"
                if _played(sans, "w", "Bf4", 4):
                    return "london"
                if _played(sans, "w", "c4", 4):
                    if _played(sans, "b", "c6", 5) and _played(sans, "b", "e6", 5):
                        return "semi_slav"
                    if _played(sans, "b", "c6", 5):
                        return "slav"
                    if _played(sans, "b", "dxc4", 5):
                        return "queens_gambit_accepted"
                    return "queens_gambit_declined"
                if _played(sans, "w", "e3", 4) and _played(sans, "w", "Bd3", 6):
                    return "colle"
                return "other"
            return "other"
        if reply == "d5":
            if wm(1) == "Bf4" or (wm(1) == "Nf3" and wm(2) == "Bf4"):
                return "london"
            if wm(1) == "c4" or wm(2) == "c4":
                if bm(1) == "c6" or bm(2) == "c6":
                    if _played(sans, "b", "e6", 6) and _played(sans, "b", "Nf6", 6):
                        return "semi_slav"
                    return "slav"
                if bm(1) == "dxc4" or bm(2) == "dxc4":
                    return "queens_gambit_accepted"
                if bm(1) == "Nc6":
                    return "chigorin"
                if bm(1) == "e5":
                    return "albin"
                if _played(sans, "w", "g3", 4):
                    return "catalan"
                return "queens_gambit_declined"
            if wm(1) == "e3" or (wm(1) == "Nf3" and wm(2) == "e3"):
                return "colle"
            return "other"
        if reply == "c5":
            return "benoni"
        if reply == "g6":
            if _played(sans, "w", "c4", 4):
                return "kings_indian"
            return "modern"
        if reply == "e6" and bm(1) == "c5":
            return "benoni"
        if reply == "b6":
            return "owens"
        return "other"

    if first == "c4":
        return "english"
    if first == "Nf3":
        if reply == "d5" and wm(1) == "c4":
            return "reti"
        if reply == "Nf6" and wm(1) == "c4":
            return "english"
        if _played(sans, "w", "d4", 3) and _played(sans, "w", "Bf4", 4):
            return "london"
        if _played(sans, "w", "d4", 3):
            return eco_family(eco)
        if _played(sans, "w", "c4", 3):
            return "english"
        return "reti"
    if first == "g3":
        return "reti"
    return eco_family(eco)


def eco_family(eco: str) -> str:
    """ECO ranges, for games the move rules do not recognise."""
    if not eco or len(eco) < 3:
        return "other"
    letter, number = eco[0], int(eco[1:3]) if eco[1:3].isdigit() else -1
    if letter == "A":
        if number == 0:
            return "polish"
        if number == 1:
            return "nimzo_larsen"
        if number in (2, 3):
            return "bird"
        if 4 <= number <= 9:
            return "reti"
        if 10 <= number <= 39:
            return "english"
        if number in (51, 52):
            return "budapest"
        if 53 <= number <= 55:
            return "old_indian"
        if 57 <= number <= 59:
            return "benko"
        if 56 <= number <= 79:
            return "benoni"
        if 80 <= number <= 99:
            return "dutch"
        return "other"
    if letter == "B":
        if number == 0:
            return "owens"
        if number == 1:
            return "scandinavian"
        if 2 <= number <= 5:
            return "alekhine"
        if number == 6:
            return "modern"
        if 7 <= number <= 9:
            return "pirc"
        if 10 <= number <= 19:
            return "caro_kann"
        return "sicilian"
    if letter == "C":
        if number <= 19:
            return "french"
        if number == 21:
            return "danish_gambit"
        if number == 22:
            return "centre_game"
        if number in (23, 24):
            return "bishops_opening"
        if 25 <= number <= 29:
            return "vienna"
        if 30 <= number <= 39:
            return "kings_gambit"
        if number == 41:
            return "philidor"
        if number in (42, 43):
            return "petrov"
        if number == 44:
            return "ponziani"
        if number == 45:
            return "scotch"
        if 46 <= number <= 49:
            return "four_knights"
        if number in (51, 52):
            return "evans_gambit"
        if 50 <= number <= 59:
            return "italian"
        if number >= 60:
            return "ruy_lopez"
        return "other"
    if letter == "D":
        if number == 2:
            return "london"
        if number in (4, 5):
            return "colle"
        if number == 7:
            return "chigorin"
        if number in (8, 9):
            return "albin"
        if 10 <= number <= 19:
            return "slav"
        if 20 <= number <= 29:
            return "queens_gambit_accepted"
        if 43 <= number <= 49:
            return "semi_slav"
        if 30 <= number <= 69:
            return "queens_gambit_declined"
        if number >= 70:
            return "grunfeld"
        return "other"
    if letter == "E":
        if number <= 9:
            return "catalan"
        if number == 11:
            return "bogo_indian"
        if 12 <= number <= 19:
            return "queens_indian"
        if 20 <= number <= 59:
            return "nimzo_indian"
        return "kings_indian"
    return "other"


@dataclass(frozen=True)
class Candidate:
    fen: str
    family: str
    eco: str
    ply: int
    game_id: str
    source: str
    event: str
    white: str
    black: str
    white_elo: int
    black_elo: int
    date: str
    result: str
    opening_header: str
    line: str  # first twelve plies in SAN, for a human reader

    def as_json(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        data["structure"] = analyse_structure(chess.Board(self.fen)).as_json()
        return data


def _game_id(headers: chess.pgn.Headers, source: str) -> str:
    key = "|".join(
        headers.get(k, "?") for k in ("Event", "Site", "Date", "Round", "White", "Black", "ECO")
    )
    return hashlib.sha1(f"{source}|{key}".encode()).hexdigest()[:12]


def _elo(headers: chess.pgn.Headers, key: str) -> int:
    try:
        return int(headers.get(key, "0"))
    except ValueError:
        return 0


def iter_games(pgn_dir: Path) -> Iterator[tuple[str, chess.pgn.Game]]:
    for path in sorted(pgn_dir.glob("*.pgn")):
        with path.open(encoding="latin-1") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                yield path.name, game


def acceptable_start(board: chess.Board) -> bool:
    """A position a game can start from: legal, live, and not already forced."""
    if not board.is_valid() or board.is_game_over(claim_draw=False):
        return False
    if board.is_check():
        return False
    if board.halfmove_clock > 20:
        return False
    legal = board.legal_moves.count()
    return legal >= 4


def sample_plies(rng: random.Random, total_plies: int) -> list[int]:
    """One transitional position, and one later position if the game allows.

    The first window (plies 16..40, moves 8..20) is where an opening has
    become a structure. The second (from ply 44) catches the queenless and
    endgame positions master games reach. Two samples from one game are kept
    at least twelve plies apart so they cannot be near-duplicates.
    """
    plies: list[int] = []
    if total_plies >= 24:
        plies.append(rng.randint(16, min(40, total_plies - 4)))
    if total_plies >= 60:
        later = rng.randint(44, min(100, total_plies - 8))
        if not plies or later - plies[0] >= 12:
            plies.append(later)
    return plies


def extract(
    pgn_dir: Path, min_elo: int, per_family_main: int, per_family_niche: int, seed: int,
    limit_games: int = 0, niche_min_elo: int | None = None,
) -> list[Candidate]:
    if niche_min_elo is None:
        niche_min_elo = min_elo
    rng = random.Random(seed)
    # Reservoir sampling per family so the choice is uniform over the games
    # seen and reproducible from the seed, regardless of file order effects.
    reservoirs: dict[str, list[Candidate]] = {}
    seen: dict[str, int] = {}
    games = 0
    for source, game in iter_games(pgn_dir):
        headers = game.headers
        if headers.get("Variant") or headers.get("FEN") or headers.get("SetUp") == "1":
            continue
        if headers.get("Result") not in ("1-0", "0-1", "1/2-1/2"):
            continue
        sans = _san_list(game, 12)
        eco = headers.get("ECO", "")
        family = opening_family(sans, eco)
        mainstream = family in MAINSTREAM
        # Niche openings are rare at the top; a lower rating floor for them
        # trades a little game quality for structural coverage. The oracle
        # decides whether the position itself is sound, not the players.
        floor = min_elo if mainstream else niche_min_elo
        if _elo(headers, "WhiteElo") < floor or _elo(headers, "BlackElo") < floor:
            continue
        moves = list(game.mainline_moves())
        if len(moves) < 24:
            continue
        games += 1
        if limit_games and games > limit_games:
            break
        cap = per_family_main if mainstream else per_family_niche

        board = game.board()
        wanted = sample_plies(rng, len(moves))
        for index, move in enumerate(moves, 1):
            board.push(move)
            if index not in wanted:
                continue
            if not acceptable_start(board):
                continue
            candidate = Candidate(
                fen=board.fen(), family=family, eco=eco, ply=index,
                game_id=_game_id(headers, source), source=source,
                event=headers.get("Event", "?"), white=headers.get("White", "?"),
                black=headers.get("Black", "?"), white_elo=_elo(headers, "WhiteElo"),
                black_elo=_elo(headers, "BlackElo"), date=headers.get("Date", "?"),
                result=headers.get("Result", "*"), opening_header=headers.get("Opening", ""),
                line=" ".join(sans),
            )
            seen[family] = seen.get(family, 0) + 1
            pool = reservoirs.setdefault(family, [])
            if len(pool) < cap:
                pool.append(candidate)
            else:
                slot = rng.randrange(seen[family])
                if slot < cap:
                    pool[slot] = candidate
    out: list[Candidate] = []
    for family in sorted(reservoirs):
        out.extend(reservoirs[family])
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract candidate positions from PGN.")
    parser.add_argument("--pgn-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--min-elo", type=int, default=2300)
    parser.add_argument("--niche-min-elo", type=int, default=2100,
                        help="rating floor for niche families, which are rare at the top")
    parser.add_argument("--per-family-main", type=int, default=160)
    parser.add_argument("--per-family-niche", type=int, default=120)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--limit-games", type=int, default=0)
    arguments = parser.parse_args()

    candidates = extract(
        arguments.pgn_dir, arguments.min_elo, arguments.per_family_main,
        arguments.per_family_niche, arguments.seed, arguments.limit_games,
        arguments.niche_min_elo,
    )
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    with arguments.out.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate.as_json(), separators=(",", ":")) + "\n")
    families: dict[str, int] = {}
    for candidate in candidates:
        families[candidate.family] = families.get(candidate.family, 0) + 1
    print(f"{len(candidates)} candidates from {arguments.pgn_dir} -> {arguments.out}")
    for family, count in sorted(families.items(), key=lambda kv: -kv[1]):
        kind = "main" if family in MAINSTREAM else "niche"
        print(f"  {family:<26} {kind:<6} {count}")


if __name__ == "__main__":
    main()
