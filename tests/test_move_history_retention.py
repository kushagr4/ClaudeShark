"""Strength matches must keep their moves.

The v0.6 arena was run without `--pgn`. Two hundred games produced a score and
nothing else, so the post-mortem that followed could not reconstruct a single
trajectory and had to build an entirely separate fixed-depth game set to ask
what had happened. Retention is therefore the default, discarding is explicit
and warned, and every PGN carries the identifiers that tie it back to its JSONL
row.
"""

from __future__ import annotations

import io
from pathlib import Path

import chess
import chess.pgn
import pytest

from tools.arena import resolve_pgn_path, tag_pgn


def test_pgn_defaults_to_the_jsonl_path(capsys: pytest.CaptureFixture[str]) -> None:
    path = resolve_pgn_path(None, Path("benchmarks/current/run.jsonl"), no_pgn=False)
    assert path == Path("benchmarks/current/run.pgn")
    assert "move history ->" in capsys.readouterr().out


def test_an_explicit_pgn_path_wins() -> None:
    chosen = Path("somewhere/else.pgn")
    assert resolve_pgn_path(chosen, Path("run.jsonl"), no_pgn=False) == chosen


def test_discarding_history_requires_saying_so_and_warns(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert resolve_pgn_path(None, Path("run.jsonl"), no_pgn=True) is None
    assert "WARNING" in capsys.readouterr().out


def test_no_pgn_conflicts_with_an_explicit_path() -> None:
    with pytest.raises(SystemExit):
        resolve_pgn_path(Path("a.pgn"), Path("run.jsonl"), no_pgn=True)


def test_a_match_with_no_record_at_all_is_warned_about(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert resolve_pgn_path(None, None, no_pgn=False) is None
    assert "WARNING" in capsys.readouterr().out


def sample_pgn() -> str:
    board = chess.Board("6k1/8/8/8/8/8/8/R5K1 w - - 0 1")
    board.push_uci("a1a8")
    return str(chess.pgn.Game.from_board(board))


def test_tagging_ties_a_game_to_its_jsonl_row() -> None:
    tagged = tag_pgn(sample_pgn(), {
        "Event": "m-1", "Round": 7, "White": "champions/a", "Black": "champions/b",
        "MatchId": "m-1", "GameIndex": 7, "PgnIndex": 3, "Cluster": 2,
    })
    game = chess.pgn.read_game(io.StringIO(tagged))
    assert game is not None
    assert game.headers["MatchId"] == "m-1"
    assert game.headers["GameIndex"] == "7"
    assert game.headers["PgnIndex"] == "3"
    assert game.headers["Cluster"] == "2"
    assert game.headers["White"] == "champions/a"
    assert game.headers["Black"] == "champions/b"


def test_tagging_preserves_the_moves_and_the_starting_position() -> None:
    original = sample_pgn()
    tagged = tag_pgn(original, {"MatchId": "m-1"})
    before = chess.pgn.read_game(io.StringIO(original))
    after = chess.pgn.read_game(io.StringIO(tagged))
    assert before is not None and after is not None
    assert [m.uci() for m in after.mainline_moves()] == [m.uci() for m in before.mainline_moves()]
    assert after.headers["FEN"] == before.headers["FEN"]
    assert after.headers["Result"] == before.headers["Result"]


def test_tagging_survives_an_unparseable_pgn() -> None:
    assert tag_pgn("", {"MatchId": "m-1"}) == ""


def test_a_tagged_pgn_replays_to_the_recorded_final_position() -> None:
    """The property the post-mortem needed and did not have."""
    tagged = tag_pgn(sample_pgn(), {"MatchId": "m-1"})
    game = chess.pgn.read_game(io.StringIO(tagged))
    assert game is not None
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
    assert board.fen().startswith("R5k1/8/8/8/8/8/8/6K1")
