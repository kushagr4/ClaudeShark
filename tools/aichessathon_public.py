# ruff: noqa: E501
"""Collect and analyse public AI Chessathon leaderboard games.

This tool deliberately uses only pages available to a signed-out visitor.  It
does not accept cookies, tokens, Supabase keys, or arbitrary table names.

Examples:
    python -m tools.aichessathon_public leaderboard --top 50
    python -m tools.aichessathon_public games --top 50
    python -m tools.aichessathon_public analyse
    python -m tools.aichessathon_public all --top 50
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import chess
import chess.pgn

BASE_URL = "https://aichessathon.com"
DEFAULT_OUTPUT = Path("analysis")
USER_AGENT = "ClaudeShark-public-research/1.0 (+public unauthenticated pages only)"
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<(?:script|style)\b.*?</(?:script|style)>", re.I | re.S)
SR_ONLY_RE = re.compile(r'<span\b[^>]*class="[^"]*sr-only[^"]*"[^>]*>.*?</span>', re.I | re.S)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def clean_text(fragment: str, *, keep_sr_only: bool = False) -> str:
    fragment = SCRIPT_RE.sub("", fragment)
    if not keep_sr_only:
        fragment = SR_ONLY_RE.sub("", fragment)
    fragment = TAG_RE.sub(" ", fragment)
    return " ".join(html.unescape(fragment).split())


def fetch(url: str, *, retries: int = 6, timeout: float = 45.0) -> str:
    """Fetch a public page without credentials, retrying transient failures."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt + 1 == retries:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 == retries:
                raise
            delay = 2**attempt
        time.sleep(delay)
    raise AssertionError("unreachable")


def extract_cells(row_html: str) -> list[str]:
    return re.findall(r"<td\b[^>]*>(.*?)</td>", row_html, re.I | re.S)


def parse_leaderboard(
    page: str, *, top: int | None = None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    pattern = re.compile(
        rf'<tr\b(?P<attrs>[^>]*data-href="/team/(?P<id>{UUID})\?from=lb"[^>]*)>'
        r"(?P<body>.*?)</tr>",
        re.I | re.S,
    )
    for match in pattern.finditer(page):
        cells = extract_cells(match.group("body"))
        if len(cells) < 5:
            continue
        rank_match = re.search(r'class="ladder-rank"[^>]*>\s*(\d+)', cells[0], re.I)
        name_match = re.search(
            r'<span\b[^>]*class="ladder-bot-name"[^>]*>(.*?)</span>', cells[1], re.I | re.S
        )
        if rank_match is None or name_match is None:
            continue
        name_html = name_match.group(1)
        small_match = re.search(r"<small\b[^>]*>(.*?)</small>", name_html, re.I | re.S)
        subtitle = clean_text(small_match.group(1)) if small_match else None
        bot_name = clean_text(
            re.sub(r"<small\b[^>]*>.*?</small>", "", name_html, flags=re.I | re.S)
        )
        rating = int(re.search(r"\d+", clean_text(cells[3])).group())
        games = int(re.search(r"\d+", clean_text(cells[4])).group())
        record_text = clean_text(cells[5]) if len(cells) > 5 else ""
        wdl = [int(value) for value in re.findall(r"\d+", record_text)[:3]]
        while len(wdl) < 3:
            wdl.append(0)
        rank = int(rank_match.group(1))
        team_id = match.group("id")
        records.append(
            {
                "rank": rank,
                "team_name": bot_name,
                "team_subtitle": subtitle,
                "team_id": team_id,
                "university": clean_text(cells[2]),
                "rating": rating,
                "games_played": games,
                "wins": wdl[0],
                "draws": wdl[1],
                "losses": wdl[2],
                "provisional": "data-provisional" in match.group("attrs"),
                "public_team_url": f"{BASE_URL}/team/{team_id}",
            }
        )
    records.sort(key=lambda row: row["rank"])
    if top is not None:
        records = records[:top]

    ratings_after = re.search(r"Ratings after.*?<dd[^>]*>(.*?)</dd>", page, re.I | re.S)
    current_round = re.search(r"Current round.*?<dd[^>]*>(.*?)</dd>", page, re.I | re.S)
    teams = re.search(r"Teams.*?<dd[^>]*>(.*?)</dd>", page, re.I | re.S)
    metadata = {
        "ratings_after": clean_text(ratings_after.group(1)) if ratings_after else None,
        "current_round": clean_text(current_round.group(1)) if current_round else None,
        "teams": int(clean_text(teams.group(1)))
        if teams and clean_text(teams.group(1)).isdigit()
        else None,
    }
    if not records:
        raise ValueError("No leaderboard rows found; the public HTML schema may have changed")
    return records, metadata


def parse_team_games(page: str, team: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pattern = re.compile(
        rf'<tr\b[^>]*data-href="/game/(?P<game>{UUID})\?from=t\.(?P<team>{UUID})"[^>]*>'
        r"(?P<body>.*?)</tr>",
        re.I | re.S,
    )
    for match in pattern.finditer(page):
        cells = extract_cells(match.group("body"))
        if len(cells) < 5:
            continue
        opponent = re.search(
            rf'href="/team/(?P<id>{UUID})\?[^" ]*"[^>]*>(?P<name>.*?)</a>', cells[2], re.I | re.S
        )
        rows.append(
            {
                "game_id": match.group("game"),
                "team_id": team["team_id"],
                "team_name": team["team_name"],
                "team_rank": team["rank"],
                "team_rating": team["rating"],
                "our_colour": clean_text(cells[1]).lower(),
                "result": clean_text(cells[3]).lower(),
                "round": clean_text(cells[0]),
                "opening": clean_text(cells[4]),
                "opponent_id": opponent.group("id") if opponent else None,
                "opponent_name": clean_text(opponent.group("name")) if opponent else None,
                "source_url": f"{BASE_URL}/game/{match.group('game')}",
            }
        )
    return rows


def parse_review(page: str) -> dict[str, Any] | None:
    source = re.search(
        r'<span\b[^>]*class="game-review-source"[^>]*>(.*?)</span>', page, re.I | re.S
    )
    sides = re.findall(
        r'<div\b[^>]*class="review-side"[^>]*>(.*?)</dl>\s*</div>', page, re.I | re.S
    )
    if not sides:
        return None
    players: list[dict[str, Any]] = []
    for side in sides:
        name = re.search(r'<p\b[^>]*class="review-name"[^>]*>(.*?)</p>', side, re.I | re.S)
        stats = {
            clean_text(label).lower().replace(" ", "_"): clean_text(value)
            for label, value in re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", side, re.I | re.S)
        }
        parsed: dict[str, Any] = {"name": clean_text(name.group(1)) if name else None}
        for key, value in stats.items():
            number = re.search(r"-?\d+(?:\.\d+)?", value)
            parsed[key] = (
                float(number.group())
                if number and "." in number.group()
                else (int(number.group()) if number else value)
            )
        players.append(parsed)
    return {"source": clean_text(source.group(1)) if source else None, "players": players}


def parse_pgn_details(pgn_text: str) -> dict[str, Any]:
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        raise ValueError("Embedded PGN could not be parsed")
    board = game.board()
    moves_uci: list[str] = []
    moves_san: list[str] = []
    clocks: list[dict[str, Any]] = []
    captures = checks = promotions = 0
    material_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
    }
    material_trace: list[int] = []
    endgame_start_ply: int | None = None
    for ply, node in enumerate(game.mainline(), start=1):
        move = node.move
        san = board.san(move)
        if board.is_capture(move):
            captures += 1
        if move.promotion:
            promotions += 1
        board.push(move)
        if board.is_check():
            checks += 1
        moves_uci.append(move.uci())
        moves_san.append(san)
        clock = node.clock()
        clocks.append(
            {
                "ply": ply,
                "colour": "white" if ply % 2 else "black",
                "san": san,
                "uci": move.uci(),
                "clock_seconds": clock,
            }
        )
        material = sum(
            value * (len(board.pieces(piece, chess.WHITE)) - len(board.pieces(piece, chess.BLACK)))
            for piece, value in material_values.items()
        )
        material_trace.append(material)
        non_pawn_non_king = sum(
            len(board.pieces(piece, colour))
            for piece in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
            for colour in (chess.WHITE, chess.BLACK)
        )
        if endgame_start_ply is None and non_pawn_non_king <= 2:
            endgame_start_ply = ply
    headers = dict(game.headers)
    return {
        "starting_fen": headers.get("FEN", chess.STARTING_FEN),
        "pgn_headers": headers,
        "moves": moves_uci,
        "moves_san": moves_san,
        "clock_data": clocks,
        "features": {
            "plies": len(moves_uci),
            "captures": captures,
            "checks": checks,
            "promotions": promotions,
            "endgame_start_ply": endgame_start_ply,
            "max_white_material_edge_cp": max(material_trace, default=0),
            "max_black_material_edge_cp": -min(material_trace, default=0),
        },
    }


def parse_game(
    page: str,
    game_id: str,
    perspectives: list[dict[str, Any]],
    ladder_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    heading = re.search(r'<h1\b[^>]*class="game-title"[^>]*>(.*?)</h1>', page, re.I | re.S)
    if heading is None:
        raise ValueError(f"No game heading found for {game_id}")
    sides = re.findall(
        rf'href="/team/(?P<id>{UUID})\?[^" ]*"[^>]*>(?P<name>.*?)</a>',
        heading.group(1),
        re.I | re.S,
    )
    score_match = re.search(
        r'<span\b[^>]*class="game-score"[^>]*>(.*?)</span>', heading.group(1), re.I | re.S
    )
    if len(sides) != 2 or score_match is None:
        raise ValueError(f"Incomplete game heading for {game_id}")
    white_id, white_name_html = sides[0]
    black_id, black_name_html = sides[1]
    white_name, black_name = clean_text(white_name_html), clean_text(black_name_html)
    score = clean_text(score_match.group(1))

    facts = {
        clean_text(label).lower(): clean_text(value)
        for label, value in re.findall(
            r"<div><dt>(.*?)</dt><dd>(.*?)</dd></div>", page, re.I | re.S
        )
    }
    pgn_uri = re.search(r'href="(data:application/x-chess-pgn[^\"]+)"', page, re.I | re.S)
    if pgn_uri is None:
        raise ValueError(f"No public PGN data URI found for {game_id}")
    uri = html.unescape(pgn_uri.group(1))
    pgn_text = urllib.parse.unquote(uri.split(",", 1)[1])
    parsed = parse_pgn_details(pgn_text)

    if score == "1-0":
        result, winner_id = "white", white_id
    elif score == "0-1":
        result, winner_id = "black", black_id
    else:
        result, winner_id = "draw", None

    public_players = {
        "white": _player_snapshot(white_id, white_name, ladder_by_id),
        "black": _player_snapshot(black_id, black_name, ladder_by_id),
    }
    top50_participants: list[dict[str, Any]] = []
    for item in sorted(perspectives, key=lambda row: row["team_rank"]):
        top50_participants.append(
            {
                "team_id": item["team_id"],
                "team_name": item["team_name"],
                "rank": item["team_rank"],
                "rating": item["team_rating"],
                "our_colour": item["our_colour"],
                "result": item["result"],
            }
        )
    primary = top50_participants[0]
    opponent_colour = "black" if primary["our_colour"] == "white" else "white"
    opponent = public_players[opponent_colour]
    return {
        "game_id": game_id,
        "team_id": primary["team_id"],
        "team_name": primary["team_name"],
        "opponent_id": opponent["team_id"],
        "opponent_name": opponent["team_name"],
        "our_colour": primary["our_colour"],
        "result": primary["result"],
        "canonical_result": score,
        "winner_colour": result,
        "winner_id": winner_id,
        "white": public_players["white"],
        "black": public_players["black"],
        "top50_participants": top50_participants,
        "round": facts.get("round") or perspectives[0].get("round"),
        "starting_fen": parsed["starting_fen"],
        "pgn": pgn_text,
        "moves": parsed["moves"],
        "moves_san": parsed["moves_san"],
        "termination": facts.get("termination") or parsed["pgn_headers"].get("Termination"),
        "timestamp": None,
        "rating_context": {
            "kind": "leaderboard snapshot, not rating at game time",
            "white": {
                "rank": public_players["white"]["rank"],
                "rating": public_players["white"]["rating"],
            },
            "black": {
                "rank": public_players["black"]["rank"],
                "rating": public_players["black"]["rating"],
            },
        },
        "clock_data": parsed["clock_data"],
        "opening": facts.get("opening") or perspectives[0].get("opening"),
        "review": parse_review(page),
        "features": parsed["features"],
        "source_url": f"{BASE_URL}/game/{game_id}",
    }


def _player_snapshot(team_id: str, name: str, ladder: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = ladder.get(team_id)
    return {
        "team_id": team_id,
        "team_name": name,
        "rank": row["rank"] if row else None,
        "rating": row["rating"] if row else None,
    }


def write_leaderboard(
    output_dir: Path,
    records: list[dict[str, Any]],
    metadata: dict[str, Any],
    scraped_at: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "scraped_at_utc": scraped_at,
        "source_url": f"{BASE_URL}/leaderboard",
        "round_state": metadata,
        "count": len(records),
        "entries": records,
    }
    (output_dir / "top50_leaderboard.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    fieldnames = [
        "rank",
        "team_name",
        "team_subtitle",
        "team_id",
        "university",
        "rating",
        "games_played",
        "wins",
        "draws",
        "losses",
        "provisional",
        "public_team_url",
    ]
    with (output_dir / "top50_leaderboard.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def collect_leaderboard(
    top: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], str]:
    scraped_at = utc_now()
    all_rows, metadata = parse_leaderboard(fetch(f"{BASE_URL}/leaderboard"))
    return all_rows[:top], all_rows, metadata, scraped_at


def collect_games(
    top_rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    *,
    workers: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    team_pages: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch, row["public_team_url"]): row["team_id"] for row in top_rows}
        for future in as_completed(futures):
            team_pages[futures[future]] = future.result()

    perspectives: dict[str, list[dict[str, Any]]] = defaultdict(list)
    top_by_id = {row["team_id"]: row for row in top_rows}
    for team_id, page in team_pages.items():
        for game in parse_team_games(page, top_by_id[team_id]):
            perspectives[game["game_id"]].append(game)

    ladder_by_id = {row["team_id"]: row for row in all_rows}
    games: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(fetch, f"{BASE_URL}/game/{game_id}"): game_id for game_id in perspectives
        }
        for future in as_completed(futures):
            game_id = futures[future]
            page = future.result()
            try:
                games.append(parse_game(page, game_id, perspectives[game_id], ladder_by_id))
            except ValueError as exc:
                if "No public PGN data URI" not in str(exc) or "data-live" not in page:
                    raise
                skipped.append(
                    {
                        "game_id": game_id,
                        "status": "live",
                        "reason": "No final downloadable PGN was exposed when fetched",
                        "source_url": f"{BASE_URL}/game/{game_id}",
                        "top50_participants": perspectives[game_id],
                    }
                )
    games.sort(key=lambda game: (_round_number(game.get("round")), game["game_id"]))
    skipped.sort(key=lambda game: game["game_id"])
    return games, skipped


def _round_number(value: str | None) -> int:
    match = re.search(r"\d+", value or "")
    return int(match.group()) if match else 0


def write_games(
    output_dir: Path,
    games: list[dict[str, Any]],
    scraped_at: str,
    skipped: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pgn_dir = output_dir / "top50_pgn"
    pgn_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "top50_games.jsonl").open("w", encoding="utf-8") as handle:
        for game in games:
            game["scraped_at_utc"] = scraped_at
            handle.write(json.dumps(game, ensure_ascii=False, separators=(",", ":")) + "\n")
            (pgn_dir / f"{game['game_id']}.pgn").write_text(game["pgn"], encoding="utf-8")
    (output_dir / "top50_collection_log.json").write_text(
        json.dumps(
            {
                "scraped_at_utc": scraped_at,
                "completed_at_utc": utc_now(),
                "completed_games_written": len(games),
                "live_games_without_final_pgn": skipped,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def load_artifacts(output_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    leaderboard = json.loads((output_dir / "top50_leaderboard.json").read_text(encoding="utf-8"))
    games = [
        json.loads(line)
        for line in (output_dir / "top50_games.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return leaderboard, games


def outcome_counts(games: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(game["winner_colour"] for game in games)
    n = len(games)
    decisive = counts["white"] + counts["black"]
    black_share = counts["black"] / decisive if decisive else 0.0
    p_value = exact_binomial_two_sided(counts["black"], decisive) if decisive else 1.0
    low, high = wilson_interval(counts["black"], decisive) if decisive else (0.0, 1.0)
    return {
        "games": n,
        "white_wins": counts["white"],
        "draws": counts["draw"],
        "black_wins": counts["black"],
        "white_score_pct": round(100 * (counts["white"] + 0.5 * counts["draw"]) / n, 2)
        if n
        else 0.0,
        "black_score_pct": round(100 * (counts["black"] + 0.5 * counts["draw"]) / n, 2)
        if n
        else 0.0,
        "black_share_of_decisive_pct": round(100 * black_share, 2),
        "black_decisive_share_95pct_wilson": [round(100 * low, 2), round(100 * high, 2)],
        "two_sided_exact_binomial_p": round(p_value, 6),
        "statistically_credible_at_0_05": p_value < 0.05,
    }


def exact_binomial_two_sided(successes: int, trials: int) -> float:
    if trials == 0:
        return 1.0
    observed = math.comb(trials, successes) / 2**trials
    return min(
        1.0,
        sum(
            math.comb(trials, k) / 2**trials
            for k in range(trials + 1)
            if math.comb(trials, k) / 2**trials <= observed + 1e-15
        ),
    )


def wilson_interval(
    successes: int, trials: int, z: float = 1.959963984540054
) -> tuple[float, float]:
    if trials == 0:
        return 0.0, 1.0
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    spread = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return max(0.0, centre - spread), min(1.0, centre + spread)


def bucket_analysis(games: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {"1-10": (1, 10), "11-25": (11, 25), "26-50": (26, 50)}
    output: dict[str, Any] = {}
    for label, (low, high) in buckets.items():
        selected = [
            game
            for game in games
            if any(low <= participant["rank"] <= high for participant in game["top50_participants"])
        ]
        output[label] = outcome_counts(selected)
    return output


def group_counts(games: list[dict[str, Any]], key: Any) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for game in games:
        groups[str(key(game))].append(game)
    return {name: outcome_counts(items) for name, items in sorted(groups.items())}


def repeated_fen_analysis(games: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for game in games:
        groups[game["starting_fen"]].append(game)
    output: list[dict[str, Any]] = []
    for fen, items in groups.items():
        if len(items) < 2:
            continue
        counts = outcome_counts(items)
        white_players = [game["white"] for game in items if game["white"]["rank"] is not None]
        black_players = [game["black"] for game in items if game["black"]["rank"] is not None]
        winners = []
        upsets = []
        for game in items:
            if game["winner_colour"] == "draw":
                continue
            winner = game[game["winner_colour"]]
            loser = game["black" if game["winner_colour"] == "white" else "white"]
            winners.append((winner.get("rank") or 10_000, game))
            if winner.get("rating") is not None and loser.get("rating") is not None:
                delta = loser["rating"] - winner["rating"]
                if delta > 0:
                    upsets.append((delta, game))
        flags: list[str] = []
        if counts["black_wins"] >= 2 and counts["black_score_pct"] >= 75:
            flags.append("Black dominates this exact FEN in the observed sample")
        if counts["white_wins"] >= 2 and counts["white_score_pct"] >= 75:
            flags.append("White dominates this exact FEN in the observed sample")
        if len({game["winner_colour"] for game in items}) >= 2:
            flags.append("Outcomes vary by engine/pairing")
        output.append(
            {
                "starting_fen": fen,
                **counts,
                "side_to_move": "white" if fen.split()[1] == "w" else "black",
                "highest_ranked_white": min(white_players, key=lambda player: player["rank"])
                if white_players
                else None,
                "highest_ranked_black": min(black_players, key=lambda player: player["rank"])
                if black_players
                else None,
                "strongest_win": _game_summary(min(winners, key=lambda pair: pair[0])[1])
                if winners
                else None,
                "biggest_upset": _game_summary(max(upsets, key=lambda pair: pair[0])[1])
                if upsets
                else None,
                "first_moves": sorted(
                    {game["moves_san"][0] for game in items if game["moves_san"]}
                ),
                "games_detail": [_game_summary(game) for game in items],
                "flags": flags,
            }
        )
    output.sort(key=lambda group: (-group["games"], group["starting_fen"]))
    return output


def _game_summary(game: dict[str, Any]) -> dict[str, Any]:
    return {
        "game_id": game["game_id"],
        "white": game["white"]["team_name"],
        "black": game["black"]["team_name"],
        "result": game["canonical_result"],
        "source_url": game["source_url"],
    }


def research_score(game: dict[str, Any], fen_frequency: Counter[str]) -> float:
    features = game["features"]
    white_rating = game["white"].get("rating")
    black_rating = game["black"].get("rating")
    upset = 0
    if white_rating is not None and black_rating is not None:
        if game["winner_colour"] == "white":
            upset = max(0, black_rating - white_rating)
        elif game["winner_colour"] == "black":
            upset = max(0, white_rating - black_rating)
    winner_edge_against = 0
    if game["winner_colour"] == "white":
        winner_edge_against = features["max_black_material_edge_cp"]
    elif game["winner_colour"] == "black":
        winner_edge_against = features["max_white_material_edge_cp"]
    endgame_plies = 0
    if features["endgame_start_ply"] is not None:
        endgame_plies = features["plies"] - features["endgame_start_ply"]
    review_quality = 0.0
    if game.get("review"):
        review_quality = (
            sum(float(player.get("accuracy", 0)) for player in game["review"]["players"]) / 100
        )
    return (
        5 * (fen_frequency[game["starting_fen"]] - 1)
        + min(upset / 40, 8)
        + min(winner_edge_against / 150, 8)
        + min(endgame_plies / 12, 7)
        + 2.5 * features["promotions"]
        + min(features["plies"] / 50, 5)
        + min(features["checks"] / 8, 3)
        + review_quality
    )


def research_observation(game: dict[str, Any], repeated: int) -> tuple[str, str, str, str]:
    f = game["features"]
    elements: list[str] = []
    hypotheses: list[str] = []
    experiments: list[str] = []
    if repeated > 1:
        elements.append(f"the exact starting FEN appears in {repeated} collected games")
        hypotheses.append(
            "move choice and outcome differences may isolate search/evaluation quality from position selection"
        )
        experiments.append(
            "replay the exact FEN against frozen ClaudeShark variants with both colours and fixed depth"
        )
    if f["endgame_start_ply"] is not None and f["plies"] - f["endgame_start_ply"] >= 20:
        elements.append(f"it contains a {f['plies'] - f['endgame_start_ply']}-ply low-piece ending")
        hypotheses.append("endgame geometry or conversion gradients may separate the engines")
        experiments.append(
            "add the position and pre-ending checkpoints to the conversion/blind-win diagnostics"
        )
    if f["promotions"]:
        elements.append(f"it contains {f['promotions']} promotion(s)")
        hypotheses.append("passed-pawn and pawn-race handling may be decisive")
        experiments.append(
            "test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints"
        )
    comeback = (
        f["max_black_material_edge_cp"]
        if game["winner_colour"] == "white"
        else f["max_white_material_edge_cp"]
    )
    if game["winner_colour"] != "draw" and comeback >= 200:
        elements.append(
            f"the winner was at least {comeback} cp behind by simple material count earlier"
        )
        hypotheses.append("tactical foresight or compensation handling may explain the reversal")
        experiments.append(
            "label the reversal window with an offline oracle and compare depth ladders before changing evaluation"
        )
    if f["plies"] >= 100:
        elements.append(f"the game lasts {f['plies']} plies")
        hypotheses.append(
            "conversion, repetition policy, or clock use may matter more than opening play"
        )
        experiments.append(
            "run ClaudeShark from late-game checkpoints with repetition and clock instrumentation enabled"
        )
    if not elements:
        elements.append(
            f"the public review covers a {f['plies']}-ply {game.get('opening') or 'curated'} position"
        )
        hypotheses.append("quiet move quality or tactical stability may distinguish the result")
        experiments.append(
            "compare ClaudeShark root choices at fixed depth on the first-error candidates"
        )
    observation = "; ".join(elements[:3]).capitalize() + "."
    hypothesis = "; ".join(hypotheses[:2]).capitalize() + "."
    experiment = "; ".join(experiments[:2]).capitalize() + "."
    caution = (
        "Do not infer the opponent's implementation from moves alone, or treat one game/current "
        "snapshot rating as causal Elo evidence."
    )
    return observation, hypothesis, experiment, caution


def build_analysis(
    leaderboard: dict[str, Any], games: list[dict[str, Any]], shortlist: int
) -> dict[str, Any]:
    fen_frequency = Counter(game["starting_fen"] for game in games)
    research_games = sorted(
        games, key=lambda game: (-research_score(game, fen_frequency), game["game_id"])
    )[: min(shortlist, len(games))]
    for index, game in enumerate(research_games, start=1):
        game["research_rank"] = index
        game["research_score"] = round(research_score(game, fen_frequency), 3)
    return {
        "scraped_at_utc": leaderboard["scraped_at_utc"],
        "analysed_at_utc": utc_now(),
        "scope": "Unique public games involving at least one team in the captured top 50",
        "overall": outcome_counts(games),
        "by_rank_bucket": bucket_analysis(games),
        "by_opening_family": group_counts(games, lambda game: game.get("opening") or "Unknown"),
        "by_side_to_move": group_counts(
            games, lambda game: "white" if game["starting_fen"].split()[1] == "w" else "black"
        ),
        "repeated_starting_fens": repeated_fen_analysis(games),
        "research_games": research_games,
    }


def write_top_games(output_dir: Path, analysis: dict[str, Any]) -> None:
    repeated_counts = {
        group["starting_fen"]: group["games"] for group in analysis["repeated_starting_fens"]
    }
    lines = [
        "# Top public games for ClaudeShark research",
        "",
        f"Snapshot: {analysis['scraped_at_utc']}. Ranking is a diagnostic prioritisation, not Elo evidence.",
        "",
    ]
    for game in analysis["research_games"]:
        observation, hypothesis, experiment, caution = research_observation(
            game, repeated_counts.get(game["starting_fen"], 1)
        )
        lines.extend(
            [
                f"## {game['research_rank']}. {game['white']['team_name']} vs {game['black']['team_name']} ({game['canonical_result']})",
                "",
                f"- Game: [{game['game_id']}]({game['source_url']})",
                f"- Round/opening: {game.get('round') or 'not exposed'} · {game.get('opening') or 'not exposed'}",
                f"- Starting FEN: `{game['starting_fen']}`",
                f"- Research-priority score: {game['research_score']} (within this snapshot only)",
                f"- **OBSERVATION:** {observation}",
                f"- **HYPOTHESIS (medium/low confidence):** {hypothesis}",
                f"- **EXPERIMENT:** {experiment}",
                f"- **WHAT NOT TO INFER:** {caution}",
                "",
            ]
        )
    (output_dir / "TOP_GAMES_FOR_CLAUDESHARK.md").write_text("\n".join(lines), encoding="utf-8")


def write_sources(output_dir: Path) -> None:
    lines = [
        "# AI Chessathon public data sources",
        "",
        "Verified from a signed-out browser and unauthenticated HTTP requests on 2026-09-04.",
        "",
        "## Completed-game collection routes",
        "",
        "### `GET https://aichessathon.com/leaderboard`",
        "",
        "- Authentication/headers: no authentication and no required custom header. The collector sends only a descriptive `User-Agent`.",
        "- Query parameters: none required. Team links contain optional `from=lb` navigation context; it does not change the record.",
        "- Response: server-rendered HTML. Each ladder row has `data-href=/team/{team_uuid}?from=lb` and cells for rank, bot/team display, university, rating, games, and W-D-L.",
        "- Pagination: none; the complete current ladder is in one response.",
        "",
        "### `GET https://aichessathon.com/team/{team_uuid}`",
        "",
        "- Authentication/headers: no authentication and no required custom header.",
        "- Query parameters: none required. `from=...` is optional backlink context.",
        "- Response: server-rendered HTML. Game rows expose game UUID, rated round, colour, opponent UUID/name, result, and opening, newest first.",
        "- Pagination: none observed; all public rows are returned in one page.",
        "",
        "### `GET https://aichessathon.com/game/{game_uuid}`",
        "",
        "- Authentication/headers: no authentication and no required custom header.",
        "- Query parameters: none required. `from=...` is optional backlink context.",
        "- Completed response: server-rendered HTML with both team UUIDs/names, result, round, termination, opening, Stockfish review summary, and a `data:application/x-chess-pgn` download URI. The decoded PGN contains starting FEN, SAN movetext, result/termination, and `%clk` comments.",
        "- Live response: public partial movetext/clocks are embedded in the Next.js payload, but there is no final downloadable PGN or result. The completed-game dataset records and excludes such pages until finalisation.",
        "- Timestamps/rating context: completed pages do not expose a game timestamp or historical pre-game ratings. The dataset uses `timestamp: null` and labels current ladder ratings as snapshot context.",
        "- Pagination: not applicable.",
        "",
        "## Live display route",
        "",
        "### `GET https://aichessathon.com/api/platform/broadcast`",
        "",
        "- Authentication/headers/query: no authentication, custom header, or query parameter required.",
        "- Response headers observed: HTTP 200, `Content-Type: application/json`, `Cache-Control: no-store`.",
        "- Top-level schema: `games` array, `total` integer, `serverNow` Unix epoch milliseconds.",
        "- Game schema observed: `matchId`, `roundId`, `finishedAt`, `offsetsMs`, `clocksMs`, `control` (`base_ms`, `inc_ms`), `startFen`, SAN `moves`, `whiteFirst`, `firstMoveNo`, `white` and `black` objects (`teamId`, `name`, `botName`, avatar metadata), and `result`.",
        "- Purpose/retention: transient live rail, polled by the frontend every 60 seconds and after finish notifications; it is not a historical archive and exposes no pagination.",
        "",
        "## Supabase / Next.js findings",
        "",
        "- The public client uses the documented Supabase project host for Realtime channel `live`, broadcast event `game_finished`; the event payload contains `match_id`, after which the client refreshes `/api/platform/broadcast` after about 900 ms.",
        "- The collector does not open that WebSocket and does not use or store the site's public publishable key because neither is needed for completed data.",
        "- No browser-side Supabase REST table, view, or RPC request was observed for the ladder, team history, or completed game. Those arrive server-rendered. No private table names were guessed or probed.",
        "- Next.js navigation may request RSC payloads with framework-generated headers/state. Those are deployment-specific and unnecessary; the stable public HTML pages above are used.",
        "",
        "## Rate limits and retry policy",
        "",
        "No rate-limit documentation or rate-limit headers were observed. This is not proof that no limit exists. The collector uses modest configurable concurrency, a 45-second timeout, and backoff on HTTP 429 and transient 5xx/network failures.",
    ]
    (output_dir / "PUBLIC_DATA_SOURCES.md").write_text("\n".join(lines), encoding="utf-8")


def write_handoff(output_dir: Path, leaderboard: dict[str, Any], analysis: dict[str, Any]) -> None:
    overall = analysis["overall"]
    repeated = analysis["repeated_starting_fens"]
    credible = "yes" if overall["statistically_credible_at_0_05"] else "no"
    collection_log_path = output_dir / "top50_collection_log.json"
    collection_log = (
        json.loads(collection_log_path.read_text(encoding="utf-8"))
        if collection_log_path.exists()
        else {"live_games_without_final_pgn": []}
    )
    live_count = len(collection_log["live_games_without_final_pgn"])
    completed_at = collection_log.get("completed_at_utc", "not recorded")
    repeated_counts = {group["starting_fen"]: group["games"] for group in repeated}
    lines = [
        "# AI Chessathon public top-50 data handoff",
        "",
        f"Scrape timestamp: **{leaderboard['scraped_at_utc']}**",
        "",
        "## 1. Public sources and boundary",
        "",
        "- `GET https://aichessathon.com/leaderboard` — server-rendered complete ladder; no auth; no pagination.",
        "- `GET https://aichessathon.com/team/{team_uuid}` — server-rendered complete public game list; no auth; no pagination.",
        "- `GET https://aichessathon.com/game/{game_uuid}` — public game metadata, Stockfish review, and a data-URI PGN with FEN, moves, termination, and `%clk` comments.",
        "- `GET https://aichessathon.com/api/platform/broadcast` — transient live rail JSON (`games`, `total`, `serverNow`); not a historical archive.",
        "- The public frontend subscribes to Supabase Realtime channel `live`, event `game_finished`, then refreshes the broadcast route. This collector does not connect to Supabase or use a publishable key.",
        "- No direct public Supabase REST table/view/RPC call was observed for leaderboard, team history, or completed-game data. Those views arrive in Next.js server-rendered HTML, so no table names are guessed.",
        "- Required headers: none beyond an ordinary `User-Agent`. No cookies or authorization are sent. No advertised rate limit was found; the collector retries HTTP 429/5xx conservatively.",
        "",
        "## 2. Snapshot summary",
        "",
        f"- Round state: {json.dumps(leaderboard.get('round_state'), ensure_ascii=False)}",
        f"- Collection window: {leaderboard['scraped_at_utc']} to {completed_at}",
        f"- Top-50 teams: {leaderboard['count']}",
        f"- Unique completed public games: {overall['games']}",
        f"- Live game pages without a final downloadable PGN at collection time: {live_count}",
        f"- White/draw/Black: {overall['white_wins']}/{overall['draws']}/{overall['black_wins']}",
        f"- White score: {overall['white_score_pct']}%; Black score: {overall['black_score_pct']}%",
        f"- Black share of decisive games: {overall['black_share_of_decisive_pct']}% (95% Wilson {overall['black_decisive_share_95pct_wilson'][0]}-{overall['black_decisive_share_95pct_wilson'][1]}%)",
        f"- Two-sided exact binomial p-value: {overall['two_sided_exact_binomial_p']}; statistically credible at 0.05: **{credible}**",
        "- This is a top-50-involvement sample, not a field-wide random sample. Selection by current rank can itself bias colour outcomes.",
        "",
        "## 3. Top 50",
        "",
        "| Rank | Bot | Team label | Rating | W-D-L | Team ID |",
        "|---:|---|---|---:|---:|---|",
    ]
    for row in leaderboard["entries"]:
        lines.append(
            f"| {row['rank']} | {row['team_name']} | {row.get('team_subtitle') or ''} | {row['rating']} | {row['wins']}-{row['draws']}-{row['losses']} | `{row['team_id']}` |"
        )
    lines.extend(["", "## 4. Colour by current-rank bucket", ""])
    for label, counts in analysis["by_rank_bucket"].items():
        lines.append(
            f"- {label}: {counts['white_wins']}/{counts['draws']}/{counts['black_wins']} W/D/B across {counts['games']} unique games touching the bucket; Black score {counts['black_score_pct']}%."
        )
    lines.extend(["", "### Starting side and opening-family checks", ""])
    for side, counts in analysis["by_side_to_move"].items():
        lines.append(
            f"- {side.title()} to move in the supplied FEN: {counts['games']} games, W/D/B {counts['white_wins']}/{counts['draws']}/{counts['black_wins']}, Black score {counts['black_score_pct']}%."
        )
    common_openings = sorted(
        analysis["by_opening_family"].items(),
        key=lambda item: (-item[1]["games"], item[0]),
    )[:10]
    for opening, counts in common_openings:
        lines.append(
            f"- {opening}: {counts['games']} games, W/D/B {counts['white_wins']}/{counts['draws']}/{counts['black_wins']}, Black score {counts['black_score_pct']}%."
        )
    lines.extend(["", "## 5. Repeated exact starting FENs", ""])
    if repeated:
        for group in repeated:
            flags = "; ".join(group["flags"]) or "no dominance flag"
            strongest = group["strongest_win"]
            upset = group["biggest_upset"]
            strongest_text = (
                f" strongest observed winner {strongest['white']} vs {strongest['black']} ({strongest['result']})"
                if strongest
                else " no decisive game"
            )
            upset_text = (
                f"; biggest snapshot-rating upset {upset['white']} vs {upset['black']} ({upset['result']})"
                if upset
                else ""
            )
            lines.append(
                f"- `{group['starting_fen']}` — {group['games']} games, W/D/B {group['white_wins']}/{group['draws']}/{group['black_wins']}, first moves {', '.join(group['first_moves'])};{strongest_text}{upset_text}; {flags}."
            )
    else:
        lines.append("- None in this snapshot; exact-FEN causal comparisons are not yet available.")
    lines.extend(["", "## 6. Highest-value research games", ""])
    for game in analysis["research_games"]:
        observation, hypothesis, experiment, caution = research_observation(
            game, repeated_counts.get(game["starting_fen"], 1)
        )
        lines.extend(
            [
                f"### {game['research_rank']}. {game['white']['team_name']}-{game['black']['team_name']} {game['canonical_result']}",
                "",
                f"Game [{game['game_id']}]({game['source_url']}); FEN `{game['starting_fen']}`.",
                "",
                f"**OBSERVATION:** {observation}",
                "",
                f"**HYPOTHESIS (medium/low confidence):** {hypothesis}",
                "",
                f"**EXPERIMENT:** {experiment}",
                "",
                f"**LIMIT:** {caution}",
                "",
            ]
        )
    lines.extend(
        [
            "## 7. Recurring behaviours and ClaudeShark hypotheses",
            "",
            "These are hypotheses generated from public move records, not claims about competitors' implementations:",
            "",
            "- **Endgame conversion (medium):** long low-piece tails and promotion races are candidates for king/pawn geometry tests. Compare V2.1 king-pawn and passed-pawn variants on extracted checkpoints.",
            "- **Compensation/tactical reversals (low):** games where the winner was materially behind deserve oracle-labelled depth ladders before any evaluation change.",
            "- **Repetition/time management (low):** long games under low clock should be replayed with repetition and allocator instrumentation; do not infer causality from final clocks alone.",
            "- **Quiet move quality (low):** use the public Stockfish review only to locate candidate first errors, then reproduce them with the repository's fixed-depth tools.",
            "",
            "What ClaudeShark 'lacks' is not proven by this dataset. The defensible next step is to turn the shortlisted positions into diagnostic fixtures and test one mechanism at a time under the existing gates.",
            "",
            "## 8. Caveats",
            "",
            "- The ladder changed during the live event; all ranks/ratings are snapshot values, not historical pre-game ratings.",
            "- The live site cannot be scraped atomically: the top-50 set is fixed at the first timestamp, while team/game pages are fetched during the recorded collection window.",
            "- Completed-game pages expose no game timestamp. `timestamp` is therefore `null`; the scrape timestamp and rated round are retained.",
            "- Team pages expose completed games only. A game still in progress may appear in the live broadcast route but is intentionally excluded until its public game page has a PGN.",
            f"- This scrape recorded {live_count} such live page(s) in `analysis/top50_collection_log.json`; rerunning later can collect them after finalisation.",
            "- Rank-bucket samples overlap when a game has top-50 participants from different buckets; each game is counted once within each touched bucket.",
            "- The exact binomial test conditions on decisive games and assumes independent fair-colour outcomes. Reused curated FENs and rank-selection can violate that assumption, so the FEN breakdown is essential.",
            "- Public Stockfish labels are observational aids, not a licence to copy an engine or infer another bot's architecture.",
            "",
            "## 9. Reproduction",
            "",
            "```powershell",
            "uv run python -m tools.aichessathon_public all --top 50 --output-dir analysis",
            "uv run python -m tools.aichessathon_public analyse --output-dir analysis --shortlist 20",
            "```",
            "",
            "Raw artifacts: `analysis/top50_leaderboard.json`, `analysis/top50_leaderboard.csv`, `analysis/top50_games.jsonl`, and `analysis/top50_pgn/`.",
        ]
    )
    (output_dir / "TOP50_OPUS_HANDOFF.md").write_text("\n".join(lines), encoding="utf-8")


def write_analysis(
    output_dir: Path, leaderboard: dict[str, Any], games: list[dict[str, Any]], shortlist: int
) -> dict[str, Any]:
    analysis = build_analysis(leaderboard, games, shortlist)
    serializable = {
        **analysis,
        "research_games": [
            _game_summary(game)
            | {
                "research_rank": game["research_rank"],
                "research_score": game["research_score"],
                "starting_fen": game["starting_fen"],
            }
            for game in analysis["research_games"]
        ],
    }
    (output_dir / "top50_analysis.json").write_text(
        json.dumps(serializable, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_top_games(output_dir, analysis)
    write_sources(output_dir)
    write_handoff(output_dir, leaderboard, analysis)
    return analysis


def command_leaderboard(args: argparse.Namespace) -> None:
    top_rows, _all_rows, metadata, scraped_at = collect_leaderboard(args.top)
    write_leaderboard(args.output_dir, top_rows, metadata, scraped_at)
    print(f"Wrote {len(top_rows)} leaderboard rows to {args.output_dir}")


def command_games(args: argparse.Namespace, *, analyse_after: bool = False) -> None:
    top_rows, all_rows, metadata, scraped_at = collect_leaderboard(args.top)
    write_leaderboard(args.output_dir, top_rows, metadata, scraped_at)
    games, skipped = collect_games(top_rows, all_rows, workers=args.workers)
    write_games(args.output_dir, games, scraped_at, skipped)
    print(f"Wrote {len(games)} unique completed public games to {args.output_dir}")
    if skipped:
        print(f"Recorded {len(skipped)} live game pages without a final PGN")
    if analyse_after:
        analysis = write_analysis(
            args.output_dir,
            json.loads((args.output_dir / "top50_leaderboard.json").read_text(encoding="utf-8")),
            games,
            args.shortlist,
        )
        overall = analysis["overall"]
        print(
            "Colour W/D/B: "
            f"{overall['white_wins']}/{overall['draws']}/{overall['black_wins']}; "
            f"exact-binomial p={overall['two_sided_exact_binomial_p']}"
        )


def command_analyse(args: argparse.Namespace) -> None:
    leaderboard, games = load_artifacts(args.output_dir)
    analysis = write_analysis(args.output_dir, leaderboard, games, args.shortlist)
    overall = analysis["overall"]
    print(
        f"Analysed {overall['games']} games: W/D/B "
        f"{overall['white_wins']}/{overall['draws']}/{overall['black_wins']}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("leaderboard", "games", "all"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--top", type=int, default=50)
        sub.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
        if name in {"games", "all"}:
            sub.add_argument("--workers", type=int, default=6)
        if name == "all":
            sub.add_argument("--shortlist", type=int, default=20)
    analyse = subparsers.add_parser("analyse")
    analyse.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    analyse.add_argument("--shortlist", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "top", 1) < 1:
        raise SystemExit("--top must be positive")
    if getattr(args, "workers", 1) < 1:
        raise SystemExit("--workers must be positive")
    try:
        if args.command == "leaderboard":
            command_leaderboard(args)
        elif args.command == "games":
            command_games(args)
        elif args.command == "all":
            command_games(args, analyse_after=True)
        else:
            command_analyse(args)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
