from urllib.parse import quote

from tools.aichessathon_public import (
    outcome_counts,
    parse_game,
    parse_leaderboard,
    parse_team_games,
)

TEAM_A = "00000000-0000-4000-8000-000000000001"
TEAM_B = "00000000-0000-4000-8000-000000000002"
GAME = "00000000-0000-4000-8000-000000000003"


def test_parse_public_pages() -> None:
    leaderboard_html = f"""
    <dl><div>Ratings after</div><dd>Round 4</dd></dl>
    <tr data-href="/team/{TEAM_A}?from=lb" data-provisional="">
      <td><span class="ladder-rank">1<span>up 2</span></span></td>
      <td><span class="ladder-bot-name">Bot A<small>Team A</small></span></td>
      <td>Oxford</td><td>1700</td><td>3</td><td>2-1-0</td>
    </tr>
    """
    rows, _metadata = parse_leaderboard(leaderboard_html)
    assert rows[0]["team_id"] == TEAM_A
    assert rows[0]["team_name"] == "Bot A"
    assert rows[0]["team_subtitle"] == "Team A"
    assert (rows[0]["wins"], rows[0]["draws"], rows[0]["losses"]) == (2, 1, 0)

    team_html = f"""
    <tr data-href="/game/{GAME}?from=t.{TEAM_A}">
      <td><a>Rated 4<span class="sr-only"> view the game</span></a></td>
      <td><span class="match-colour">White</span></td>
      <td><a href="/team/{TEAM_B}?from=t.{TEAM_A}">Bot B</a></td>
      <td>Win</td><td>Test Opening</td>
    </tr>
    """
    perspectives = parse_team_games(team_html, rows[0])
    assert perspectives[0]["game_id"] == GAME
    assert perspectives[0]["opponent_id"] == TEAM_B

    pgn = """[Result "1-0"]
[FEN "7k/8/5KQ1/8/8/8/8/8 w - - 0 1"]
[SetUp "1"]
[Termination "checkmate"]

1. Qg7# { [%clk 0:00:10] } 1-0"""
    game_html = f"""
    <h1 class="game-title">
      <a href="/team/{TEAM_A}?from=g.{GAME}">Bot A</a>
      <span class="game-score">1-0</span>
      <a href="/team/{TEAM_B}?from=g.{GAME}">Bot B</a>
    </h1>
    <div><dt>Round</dt><dd>Rated 4</dd></div>
    <div><dt>Termination</dt><dd>checkmate</dd></div>
    <div><dt>Opening</dt><dd>Test Opening</dd></div>
    <a href="data:application/x-chess-pgn;charset=utf-8,{quote(pgn)}">Download</a>
    """
    ladder = {TEAM_A: rows[0], TEAM_B: {"rank": 2, "rating": 1650}}
    game = parse_game(game_html, GAME, perspectives, ladder)
    assert game["canonical_result"] == "1-0"
    assert game["moves"] == ["g6g7"]
    assert game["clock_data"][0]["clock_seconds"] == 10.0


def test_colour_statistics() -> None:
    games = [
        {"winner_colour": "white"},
        {"winner_colour": "black"},
        {"winner_colour": "draw"},
    ]
    result = outcome_counts(games)
    assert result["white_score_pct"] == 50.0
    assert result["black_score_pct"] == 50.0
    assert result["two_sided_exact_binomial_p"] == 1.0
