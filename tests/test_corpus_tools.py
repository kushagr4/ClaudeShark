"""Tests for the corpus tooling in ``tools/corpus``.

Two kinds of guarantee. The pure functions -- structural tags, opening
recognition, de-duplication, the near-level filter, coverage selection -- are
checked on positions with known properties. The shipped suites, when present,
are checked the way the legacy corpus is: every FEN legal, non-terminal,
unique, and every competition-like position inside the band its header
declares. None of this needs the reference engine binary.
"""

from __future__ import annotations

import json
from pathlib import Path

import chess
import pytest

from tools.corpus.build import (
    HANDPICKED_STRESS,
    dedupe,
    is_near_level,
    select_diverse,
)
from tools.corpus.extract import MAINSTREAM, NICHE, eco_family, opening_family
from tools.corpus.oracle import Label, Line, expected_score
from tools.corpus.structure import structure_of
from tools.positions import unsuitable

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"


# ------------------------------------------------------------- structure


@pytest.mark.parametrize(
    ("fen", "expected"),
    [
        # Isolated d-pawn in a Tarrasch-like structure.
        ("r1bq1rk1/pp3ppp/2n2n2/2bp4/8/2N1PN2/PP2BPPP/R1BQ1RK1 w - - 0 10", "isolated_queen_pawn"),
        # Exchange QGD skeleton.
        ("r1bq1rk1/pp1n1ppp/2pb1n2/3p4/3P4/2NBPN2/PPQ2PPP/R1B2RK1 w - - 0 10", "carlsbad"),
        # Pawns on c4 and e4 against a Sicilian with the c-pawn gone.
        ("r1bqkb1r/pp1ppp1p/2n2np1/8/2PNP3/2N5/PP2BPPP/R1BQK2R b KQkq - 0 7", "maroczy_bind"),
        ("8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 40", "rook_ending"),
        ("8/p4pk1/1p4p1/8/1P4P1/P4PK1/8/8 w - - 0 36", "pawn_ending"),
        ("r1b1k2r/pppp1ppp/8/8/8/8/PPPP1PPP/R1B1K2R w KQkq - 0 12", "opposite_coloured_bishops"),
        ("r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/2KR1B1R w kq - 0 15", "material_imbalance"),
        ("r3k2r/pp3ppp/2n1bn2/2bp4/8/2N1BN2/PPP2PPP/R3KB1R w KQkq - 0 11", "queenless_middlegame"),
        ("8/8/8/3pP3/8/8/8/k6K w - d6 0 2", "passed_pawn"),
    ],
)
def test_structure_tags(fen: str, expected: str) -> None:
    structure = structure_of(fen)
    assert expected in structure.tags, (fen, structure.tags)


def test_structure_phase_and_material() -> None:
    start = structure_of(chess.STARTING_FEN)
    assert start.phase == "opening"
    assert start.phase24 == 24
    assert start.material_diff == 0
    assert start.imbalance == "even"
    ending = structure_of("8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 40")
    assert ending.phase == "endgame"
    assert ending.material_diff == 6  # a whole rook and a pawn
    # Two rooks and a bishop against two rooks is a piece up, whatever the old
    # corpus comment said; a rook against a bishop is the exchange.
    piece_up = structure_of("r3k2r/ppp2ppp/8/8/8/8/PPP2PPP/2KR1B1R w kq - 0 15")
    assert piece_up.imbalance == "piece"
    exchange = structure_of("r3k3/8/8/8/8/8/8/2B1K3 w - - 0 1")
    assert exchange.imbalance == "exchange"


def test_structure_is_colour_symmetric() -> None:
    """Mirroring the board must not change the tags."""
    fen = "r1bq1rk1/pp1n1ppp/2pb1n2/3p4/3P4/2NBPN2/PPQ2PPP/R1B2RK1 w - - 0 10"
    board = chess.Board(fen)
    mirrored = board.mirror()
    assert structure_of(fen).tags == structure_of(mirrored.fen()).tags


# --------------------------------------------------------------- openings


@pytest.mark.parametrize(
    ("moves", "family"),
    [
        ("e4 e5 Nf3 Nc6 Bb5 a6", "ruy_lopez"),
        ("e4 e5 Nf3 Nc6 Bc4 Bc5", "italian"),
        ("e4 e5 Nf3 Nc6 Bc4 Bc5 b4", "evans_gambit"),
        ("e4 e5 Nf3 Nc6 d4 exd4", "scotch"),
        ("e4 e5 f4 exf4", "kings_gambit"),
        ("e4 e5 d4 exd4 c3 dxc3", "danish_gambit"),
        ("e4 c5 d4 cxd4 c3 dxc3", "smith_morra"),
        ("e4 c5 Nf3 d6 d4 cxd4", "sicilian"),
        ("e4 c5 c3 Nf6", "sicilian_alapin"),
        ("e4 e6 d4 d5", "french"),
        ("e4 c6 d4 d5", "caro_kann"),
        ("e4 d5 exd5 Qxd5", "scandinavian"),
        ("e4 Nf6 e5 Nd5", "alekhine"),
        ("e4 d6 d4 Nf6 Nc3 g6", "pirc"),
        ("e4 g6 d4 Bg7", "modern"),
        ("e4 b6 d4 Bb7", "owens"),
        ("d4 d5 c4 e6 Nc3 Nf6", "queens_gambit_declined"),
        ("d4 d5 c4 c6 Nf3 Nf6 Nc3 e6", "semi_slav"),
        ("d4 d5 c4 c6 Nf3 Nf6 Nc3 dxc4", "slav"),
        ("d4 d5 c4 dxc4", "queens_gambit_accepted"),
        ("d4 Nf6 c4 g6 Nc3 Bg7 e4 d6", "kings_indian"),
        ("d4 Nf6 c4 g6 Nc3 d5", "grunfeld"),
        ("d4 Nf6 c4 e6 Nc3 Bb4", "nimzo_indian"),
        ("d4 Nf6 c4 e6 Nf3 b6", "queens_indian"),
        ("d4 Nf6 c4 e6 g3 d5 Bg2", "catalan"),
        ("d4 Nf6 c4 c5 d5 b5", "benko"),
        ("d4 Nf6 c4 c5 d5 e6", "benoni"),
        ("d4 Nf6 c4 e5", "budapest"),
        ("d4 Nf6 Bg5", "trompowsky"),
        ("d4 d5 Bf4", "london"),
        ("d4 Nf6 Nf3 e6 Bf4", "london"),
        ("d4 d5 Nf3 Nf6 e3 e6 Bd3", "colle"),
        ("d4 f5", "dutch"),
        ("c4 e5", "english"),
        ("Nf3 d5 c4", "reti"),
        ("b4 e5", "polish"),
        ("b3 e5", "nimzo_larsen"),
        ("f4 d5", "bird"),
    ],
)
def test_opening_family_from_moves(moves: str, family: str) -> None:
    assert opening_family(moves.split(), "") == family


def test_eco_fallback_and_family_lists() -> None:
    assert eco_family("C65") == "ruy_lopez"
    assert eco_family("E97") == "kings_indian"
    assert eco_family("A57") == "benko"
    assert eco_family("") == "other"
    assert not set(MAINSTREAM) & set(NICHE)


# ---------------------------------------------------------------- build


def _row(fen: str, cp: int = 0, gap: int = 10, game: str = "g", family: str = "x") -> dict:
    return {
        "fen": fen, "cp_white": cp, "second_gap_cp": gap, "game_id": game, "family": family,
        "expected_score_white": 0.5, "reference": {"mate": None},
        "structure": structure_of(fen).as_json(),
    }


def test_dedupe_drops_exact_and_near_duplicates() -> None:
    a = "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9"
    same_clock_differs = "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 3 12"
    one_piece_moved = "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQR1K1 w - - 0 9"
    different = "8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 40"
    kept = dedupe([_row(a), _row(same_clock_differs), _row(one_piece_moved), _row(different)])
    assert [r["fen"] for r in kept] == [a, different]


def test_near_level_filter() -> None:
    fen = chess.STARTING_FEN
    assert is_near_level(_row(fen, cp=40, gap=50), 50, 100, 0.15)
    assert not is_near_level(_row(fen, cp=60, gap=50), 50, 100, 0.15)
    assert not is_near_level(_row(fen, cp=0, gap=250), 50, 100, 0.15)
    mate = _row(fen)
    mate["reference"] = {"mate": 3}
    assert not is_near_level(mate, 50, 100, 0.15)
    skewed = _row(fen)
    skewed["expected_score_white"] = 0.8
    assert not is_near_level(skewed, 50, 100, 0.15)


def test_select_diverse_respects_caps() -> None:
    fens = [
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9",
        "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6",
        "r1bq1rk1/pp3ppp/2n1pn2/2pp4/1b1P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9",
        "rn1qkb1r/pp2pppp/2p2n2/3p1b2/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5",
        "8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 40",
        "8/p4pk1/1p4p1/8/1P4P1/P4PK1/8/8 w - - 0 36",
    ]
    rows = [_row(f, game=f"g{i}", family="a" if i < 4 else "b") for i, f in enumerate(fens)]
    rows[1]["game_id"] = rows[0]["game_id"]  # same game: only one may be chosen
    chosen = select_diverse(rows, size=10, seed=1, per_family=2)
    assert len({r["game_id"] for r in chosen}) == len(chosen)
    families = [r["family"] for r in chosen]
    assert families.count("a") <= 2 and families.count("b") <= 2


@pytest.mark.parametrize(
    ("fen", "reason"), HANDPICKED_STRESS, ids=[r for _, r in HANDPICKED_STRESS]
)
def test_handpicked_stress_positions_are_playable(fen: str, reason: str) -> None:
    assert not unsuitable((fen,), reason)


# ---------------------------------------------------------------- oracle


def test_label_round_trip_and_expected_score() -> None:
    label = Label(
        fen=chess.STARTING_FEN, nodes=1000, depth=10, seldepth=12, cp_stm=20, cp_white=20,
        mate=None, wdl_stm=(100, 800, 100), wdl_white=(100, 800, 100), best="e2e4",
        pv=["e2e4", "e7e5"], lines=[Line("e2e4", 20, None, (100, 800, 100), ["e2e4", "e7e5"])],
    )
    assert Label.from_json(json.loads(json.dumps(label.to_json()))) == label
    assert expected_score((100, 800, 100)) == pytest.approx(0.5)
    assert expected_score((1000, 0, 0)) == 1.0
    assert expected_score(None) is None


# --------------------------------------------------------- shipped suites


def _suite_rows(name: str) -> tuple[dict, list[dict]]:
    path = CORPUS / name
    if not path.exists():
        pytest.skip(f"{name} not built")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    header = rows[0]
    assert header.get("record") == "header"
    return header, rows[1:]


@pytest.mark.parametrize("name", ["competition_like_v1.jsonl", "stress_test_v1.jsonl"])
def test_shipped_suite_positions_are_playable_and_unique(name: str) -> None:
    _, rows = _suite_rows(name)
    fens = tuple(r["fen"] for r in rows)
    assert len(fens) == len(set(fens)), "duplicate FEN in suite"
    keys = {" ".join(f.split()[:4]) for f in fens}
    assert len(keys) == len(fens), "same position with different counters"
    assert not unsuitable(fens, name)


def test_competition_like_suite_is_inside_its_declared_band() -> None:
    header, rows = _suite_rows("competition_like_v1.jsonl")
    band = header["band_cp"]
    gap = header["max_gap_cp"]
    for row in rows:
        reference = row["reference"]
        assert abs(reference["cp_white"]) <= band, row["id"]
        assert reference["second_gap_cp"] is None or reference["second_gap_cp"] <= gap, row["id"]
        assert reference["best"] in {m.uci() for m in chess.Board(row["fen"]).legal_moves}
    games = [r["source"]["game_id"] for r in rows]
    assert len(games) == len(set(games)), "more than one position from one source game"
    colours = [r["fen"].split()[1] for r in rows]
    assert 0.35 <= colours.count("w") / len(colours) <= 0.65, "side to move is lopsided"


def test_legacy_calibration_covers_the_whole_corpus() -> None:
    path = CORPUS / "legacy_v2_calibration.jsonl"
    if not path.exists():
        pytest.skip("legacy calibration not built")
    from tools.positions import BALANCED_OPENINGS, SHARP_POSITIONS, corpus_hash

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    header, body = rows[0], rows[1:]
    assert header["corpus_hash"] == corpus_hash(), "calibration is for a different corpus"
    assert [r["fen"] for r in body] == list(BALANCED_OPENINGS + SHARP_POSITIONS)


def test_load_suite_reads_header_and_fens(tmp_path: Path) -> None:
    from tools.corpus.suite import load_suite

    path = tmp_path / "suite.jsonl"
    path.write_text(
        json.dumps({"record": "header", "suite": "x", "version": "v9", "hash": "abc"}) + "\n"
        + json.dumps({"id": "x-000", "fen": chess.STARTING_FEN}) + "\n",
        encoding="utf-8",
    )
    header, fens = load_suite(path)
    assert header["hash"] == "abc"
    assert fens == (chess.STARTING_FEN,)
    empty = tmp_path / "empty.jsonl"
    empty.write_text(json.dumps({"record": "header"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_suite(empty)
