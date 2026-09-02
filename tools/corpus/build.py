"""Build the two suites from a labelled candidate pool.

**COMPETITION_LIKE** is for strength measurement: legal, non-terminal, unique,
near-level by the oracle, not tactically forced, structurally diverse, one
position per source game. **STRESS_TEST** is for finding failures: large
imbalances, sacrifices with compensation, promotion races, locked centres,
odd kings. Its results never feed a headline Elo figure.

The near-level band is a parameter, and ``--sensitivity`` prints what each
plausible band would admit before anything is chosen, so the choice is made
on evidence rather than on a number that sounds reasonable.

    uv run python -m tools.corpus.build --labelled corpus\\candidates_labelled.jsonl ^
        --sensitivity
    uv run python -m tools.corpus.build --labelled corpus\\candidates_labelled.jsonl ^
        --band 50 --max-gap 100 --size 240 --out-dir corpus
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

import chess

from tools.corpus.extract import MAINSTREAM
from tools.corpus.oracle import read_jsonl
from tools.corpus.structure import analyse_structure

# Tags that carry almost no information for grouping (nearly every position
# has an open or semi-open file) and are excluded from the diversity score.
UNINFORMATIVE = frozenset({"open_file", "semi_open_file"})

# Piece-placement distance at or below which two positions are treated as the
# same position for de-duplication: a single piece having moved.
NEAR_DUPLICATE_SQUARES = 2

BANDS = (25, 50, 75, 100)
GAPS = (50, 100, 150)


def board_key(fen: str) -> str:
    """Placement, side to move, castling and en passant -- no counters."""
    return " ".join(fen.split()[:4])


def placement_vector(fen: str) -> str:
    board = chess.Board(fen)
    return "".join(
        (board.piece_at(square).symbol() if board.piece_at(square) else ".")
        for square in chess.SQUARES
    )


def placement_distance(a: str, b: str) -> int:
    return sum(1 for x, y in zip(a, b, strict=True) if x != y)


def is_near_level(row: dict[str, Any], band: int, max_gap: int, max_dev: float) -> bool:
    if row.get("reference", {}).get("mate") is not None:
        return False
    if abs(row["cp_white"]) > band:
        return False
    gap = row.get("second_gap_cp")
    if gap is not None and gap > max_gap:
        return False
    expected = row.get("expected_score_white")
    return expected is None or abs(expected - 0.5) <= max_dev


def sensitivity(rows: list[dict[str, Any]]) -> str:
    lines = ["## Band sensitivity over the labelled pool", "",
             f"Pool: {len(rows)} labelled candidates from {len({r['game_id'] for r in rows})} "
             "games.", "",
             "| band | max gap | admitted | opening | middlegame | endgame | families >= 4 | "
             "families >= 8 | tags >= 10 |",
             "|---|---|---|---|---|---|---|---|---|"]
    for band in BANDS:
        for gap in GAPS:
            admitted = [r for r in rows if is_near_level(r, band, gap, 1.0)]
            phases = Counter(r["structure"]["phase"] for r in admitted)
            families = Counter(r["family"] for r in admitted)
            tags = Counter(t for r in admitted for t in r["structure"]["tags"]
                           if t not in UNINFORMATIVE)
            lines.append(
                f"| +/-{band} | {gap} | {len(admitted)} | {phases.get('opening', 0)} | "
                f"{phases.get('middlegame', 0)} | {phases.get('endgame', 0)} | "
                f"{sum(1 for v in families.values() if v >= 4)} | "
                f"{sum(1 for v in families.values() if v >= 8)} | "
                f"{sum(1 for v in tags.values() if v >= 10)} |"
            )
    lines += ["", "### WDL view: expected score deviation from 0.5", "",
              "| max |E-0.5| | admitted | mean |cp| among admitted | max |cp| |",
              "|---|---|---|---|"]
    for dev in (0.05, 0.10, 0.15, 0.20):
        admitted = [r for r in rows if r.get("expected_score_white") is not None
                    and abs(r["expected_score_white"] - 0.5) <= dev]
        if admitted:
            mean_cp = sum(abs(r["cp_white"]) for r in admitted) / len(admitted)
            max_cp = max(abs(r["cp_white"]) for r in admitted)
        else:
            mean_cp = max_cp = 0
        lines.append(f"| {dev:.2f} | {len(admitted)} | {mean_cp:.0f} | {max_cp} |")
    lines += ["", "### Score distribution of the whole pool (white POV, cp)", "",
              "| bucket | count |", "|---|---|"]
    buckets = Counter()
    for r in rows:
        cp = r["cp_white"]
        edge = min(400, (abs(cp) // 50) * 50)
        buckets[edge] += 1
    for edge in sorted(buckets):
        label = f"{edge}..{edge + 49}" if edge < 400 else "400+"
        lines.append(f"| {label} | {buckets[edge]} |")
    return "\n".join(lines)


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop exact and near-duplicate positions, keeping the first seen."""
    seen_keys: set[str] = set()
    kept: list[dict[str, Any]] = []
    vectors: list[tuple[str, bool]] = []
    for row in rows:
        key = board_key(row["fen"])
        if key in seen_keys:
            continue
        vector = placement_vector(row["fen"])
        turn = chess.Board(row["fen"]).turn
        if any(t == turn and placement_distance(vector, v) <= NEAR_DUPLICATE_SQUARES
               for v, t in vectors):
            continue
        seen_keys.add(key)
        vectors.append((vector, turn))
        kept.append(row)
    return kept


def select_diverse(
    rows: list[dict[str, Any]], size: int, seed: int, per_family: int, per_game: int = 1,
    phase_share: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Greedy coverage: each pick is the candidate adding the rarest structures.

    The score of a candidate is the sum over its informative tags of
    1/(1 + times already chosen), plus the same for its family and phase, so
    the first pick of a rare tag is worth a lot and the tenth is worth little.
    Family and phase caps keep the mainstream from crowding out the rest.
    """
    rng = random.Random(seed)
    pool = list(rows)
    rng.shuffle(pool)
    share = phase_share or {"opening": 0.15, "middlegame": 0.60, "endgame": 0.25}
    phase_cap = {phase: max(1, round(size * fraction)) for phase, fraction in share.items()}
    tag_count: Counter[str] = Counter()
    family_count: Counter[str] = Counter()
    phase_count: Counter[str] = Counter()
    game_count: Counter[str] = Counter()
    chosen: list[dict[str, Any]] = []
    chosen_vectors: list[tuple[str, bool]] = []

    while pool and len(chosen) < size:
        best_score = -1.0
        best_index = -1
        for index, row in enumerate(pool):
            structure = row["structure"]
            if family_count[row["family"]] >= per_family:
                continue
            if phase_count[structure["phase"]] >= phase_cap.get(structure["phase"], size):
                continue
            if game_count[row["game_id"]] >= per_game:
                continue
            score = 1.0 / (1 + family_count[row["family"]])
            score += 1.0 / (1 + phase_count[structure["phase"]])
            for tag in structure["tags"]:
                if tag not in UNINFORMATIVE:
                    score += 1.0 / (1 + tag_count[tag])
            # Mild preference for the more level positions inside the band.
            score += 0.2 * (1.0 - abs(row["cp_white"]) / 100.0)
            if score > best_score:
                best_score, best_index = score, index
        if best_index < 0:
            break
        row = pool.pop(best_index)
        vector = placement_vector(row["fen"])
        turn = chess.Board(row["fen"]).turn
        if any(t == turn and placement_distance(vector, v) <= NEAR_DUPLICATE_SQUARES
               for v, t in chosen_vectors):
            continue
        chosen.append(row)
        chosen_vectors.append((vector, turn))
        family_count[row["family"]] += 1
        phase_count[row["structure"]["phase"]] += 1
        game_count[row["game_id"]] += 1
        for tag in row["structure"]["tags"]:
            tag_count[tag] += 1
    return chosen


def stress_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Positions built to break an engine, with the reason recorded."""
    out = []
    for row in rows:
        structure = row["structure"]
        tags = set(structure["tags"])
        cp = row["cp_white"]
        material = structure["material_diff"]
        reasons = []
        # Material says one thing, the oracle says another: compensation.
        if abs(material) >= 2 and abs(cp) <= 60:
            reasons.append("compensation_for_material")
        if abs(material) >= 1 and material * cp < 0 and abs(cp) >= 100:
            reasons.append("evaluation_against_material")
        if "exchange_imbalance" in tags:
            reasons.append("exchange_imbalance")
        if structure["imbalance"] in ("queen_vs_pieces", "minor_vs_pawns"):
            reasons.append(structure["imbalance"])
        if "advanced_passer" in tags and "connected_passers" in tags:
            reasons.append("promotion_race")
        if "closed_centre" in tags and "locked_pawn_chain" in tags:
            reasons.append("locked_centre")
        if "unusual_king_placement" in tags:
            reasons.append("unusual_king")
        if "king_attack" in tags and "opposite_side_castling" in tags:
            reasons.append("attack_race")
        if "opposite_coloured_bishops" in tags and structure["phase"] == "endgame" \
                and abs(material) >= 1:
            reasons.append("opposite_bishops_pawn_up")
        if "pawn_ending" in tags:
            reasons.append("pawn_ending")
        if row.get("second_gap_cp") is not None and row["second_gap_cp"] >= 200 \
                and abs(cp) <= 150:
            reasons.append("only_move")
        if reasons:
            copy = dict(row)
            copy["stress_reasons"] = reasons
            out.append(copy)
    return out


# Hand-picked classical positions the master-game pool cannot supply: forced
# zugzwang, textbook rook endings, fortress and breakthrough themes. Each is a
# legal, non-terminal position with the theme named. Verified by
# tests/test_corpus_tools.py.
HANDPICKED_STRESS: tuple[tuple[str, str], ...] = (
    ("8/8/1p6/p1p5/P1P5/1P6/8/k1K5 w - - 0 1", "trebuchet_zugzwang"),
    ("8/8/8/8/8/1k6/8/1K1R4 b - - 0 1", "lone_rook_mate_technique"),
    ("1K1k4/1P6/8/8/8/8/r7/2R5 w - - 0 1", "lucena"),
    ("8/8/8/8/4k3/8/r7/4K2R w K - 0 1", "rook_ending_castling_rights"),
    ("8/8/3b4/8/3k4/1Bp5/8/5K2 w - - 0 1", "opposite_bishops_pawn_down_fortress"),
    ("k7/8/1K6/8/8/8/8/1Q6 w - - 0 1", "queen_mate_stalemate_trap"),
    ("8/5pk1/8/6P1/5P2/8/8/6K1 w - - 0 1", "two_vs_one_kingside"),
    ("8/pp4kp/2p5/8/8/2P5/PP4KP/8 w - - 0 1", "pawn_ending_majority"),
    ("8/1p6/kp6/8/8/1P6/1P6/1K6 w - - 0 1", "doubled_pawns_pawn_ending"),
    ("8/8/8/2k5/2P5/8/2K5/8 w - - 0 1", "opposition"),
    ("2r3k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1", "back_rank_rook_ending"),
    ("r1b2rk1/pp3ppp/2n5/3q4/8/8/PPP2PPP/R2QKB1R w KQ - 0 12", "queen_centralised_open"),
    ("6k1/5pp1/7p/8/8/5N2/5PPP/6K1 w - - 0 1", "knight_vs_pawns_hold"),
    ("1n6/8/4k3/8/8/2N5/6K1/8 w - - 0 1", "knight_vs_knight_not_dead_by_rule"),
    ("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1", "king_pawn_vs_king_win"),
    ("4k3/4p3/8/8/8/8/4P3/4K3 w - - 0 1", "symmetric_pawn_ending"),
    ("r3k2r/ppp2ppp/2n5/3pP3/3P4/2P5/P4PPP/R3K2R w KQkq - 0 12", "locked_centre_manoeuvre"),
    ("rnbqkb1r/pp2pppp/2p2n2/8/2pP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5", "gambit_pawn_down"),
)


def _stress_row(fen: str, reason: str) -> dict[str, Any]:
    return {
        "fen": fen,
        "family": "handpicked",
        "game_id": "handpicked",
        "source": "handpicked",
        "structure": analyse_structure(chess.Board(fen)).as_json(),
        "stress_reasons": [reason],
        "cp_white": None,
        "expected_score_white": None,
        "second_gap_cp": None,
        "reference": None,
    }


def corpus_hash(rows: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join(r["fen"] for r in rows).encode()).hexdigest()[:16]


def summarise(rows: list[dict[str, Any]], title: str, extra: str = "") -> str:
    families = Counter(r["family"] for r in rows)
    phases = Counter(r["structure"]["phase"] for r in rows)
    tags = Counter(t for r in rows for t in r["structure"]["tags"] if t not in UNINFORMATIVE)
    labelled = [r for r in rows if r.get("cp_white") is not None]
    lines = [f"# {title}", "", extra, "",
             f"{len(rows)} positions, {len({r['game_id'] for r in rows})} source games, "
             f"hash `{corpus_hash(rows)}`.", "",
             "## Phase", "", "| phase | count |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in phases.most_common()]
    if labelled:
        cps = sorted(abs(r["cp_white"]) for r in labelled)
        signed = [r["cp_white"] for r in labelled]
        lines += ["", "## Reference evaluation (white POV)", "",
                  f"* mean signed {sum(signed) / len(signed):+.1f} cp, "
                  f"median |cp| {cps[len(cps) // 2]}, max |cp| {cps[-1]}",
                  f"* white-to-move {sum(1 for r in labelled if r['fen'].split()[1] == 'w')}, "
                  f"black-to-move {sum(1 for r in labelled if r['fen'].split()[1] == 'b')}"]
        deviations = [abs(r["expected_score_white"] - 0.5) for r in labelled
                      if r.get("expected_score_white") is not None]
        if deviations:
            lines.append(f"* max |E[score]-0.5| {max(deviations):.3f}")
    lines += ["", "## Opening family", "", "| family | kind | count |", "|---|---|---|"]
    lines += [f"| {k} | {'main' if k in MAINSTREAM else 'niche'} | {v} |"
              for k, v in families.most_common()]
    lines += ["", "## Structural tags", "", "| tag | count |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in tags.most_common()]
    return "\n".join(lines) + "\n"


def slim(row: dict[str, Any], index: int, suite: str) -> dict[str, Any]:
    """The record that ships in the corpus file: everything needed, nothing else."""
    reference = row.get("reference") or {}
    return {
        "id": f"{suite}-{index:03d}",
        "fen": row["fen"],
        "family": row["family"],
        "structure": row["structure"],
        "stress_reasons": row.get("stress_reasons"),
        "reference": {
            "cp_white": row.get("cp_white"),
            "wdl_white": reference.get("wdl_white"),
            "expected_score_white": row.get("expected_score_white"),
            "best": reference.get("best"),
            "pv": reference.get("pv"),
            "second_gap_cp": row.get("second_gap_cp"),
            "nodes": reference.get("nodes"),
            "depth": reference.get("depth"),
            "lines": reference.get("lines"),
        } if reference else None,
        "source": {
            "game_id": row.get("game_id"),
            "file": row.get("source"),
            "event": row.get("event"),
            "white": row.get("white"),
            "black": row.get("black"),
            "white_elo": row.get("white_elo"),
            "black_elo": row.get("black_elo"),
            "date": row.get("date"),
            "result": row.get("result"),
            "eco": row.get("eco"),
            "ply": row.get("ply"),
            "line": row.get("line"),
        },
    }


def write_suite(path: Path, rows: list[dict[str, Any]], header: dict[str, Any], suite: str) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"record": "header", **header}) + "\n")
        for index, row in enumerate(rows):
            handle.write(json.dumps(slim(row, index, suite), separators=(",", ":")) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the competition-like and stress suites.")
    parser.add_argument("--labelled", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("corpus"))
    parser.add_argument("--sensitivity", action="store_true", help="print the band table and stop")
    parser.add_argument("--band", type=int, default=50, help="max |cp| from the oracle")
    parser.add_argument("--max-gap", type=int, default=100, help="max best-minus-second cp")
    parser.add_argument("--max-dev", type=float, default=0.15, help="max |E[score]-0.5|")
    parser.add_argument("--size", type=int, default=240)
    parser.add_argument("--per-family", type=int, default=12)
    parser.add_argument("--stress-size", type=int, default=120)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--version", default="v1")
    arguments = parser.parse_args()

    records = read_jsonl(arguments.labelled)
    header = next((r for r in records if r.get("record") == "header"), {})
    rows = [r for r in records if r.get("record") != "header" and r.get("cp_white") is not None]

    if arguments.sensitivity:
        print(sensitivity(rows))
        return

    level = [
        r for r in rows
        if is_near_level(r, arguments.band, arguments.max_gap, arguments.max_dev)
    ]
    level = dedupe(level)
    chosen = select_diverse(level, arguments.size, arguments.seed, arguments.per_family)
    chosen.sort(key=lambda r: (r["structure"]["phase"], r["family"], r["fen"]))

    stress = stress_candidates(rows)
    stress = [r for r in stress if r["fen"] not in {c["fen"] for c in chosen}]
    stress = dedupe(stress)
    stress_chosen = select_diverse(
        stress, arguments.stress_size, arguments.seed, per_family=8,
        phase_share={"opening": 0.15, "middlegame": 0.55, "endgame": 0.30},
    )
    stress_chosen += [_stress_row(fen, reason) for fen, reason in HANDPICKED_STRESS]

    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    common = {
        "oracle": header.get("oracle"),
        "nodes": header.get("nodes"),
        "multipv": header.get("multipv"),
        "labelled_pool": len(rows),
        "seed": arguments.seed,
    }
    comp_path = arguments.out_dir / f"competition_like_{arguments.version}.jsonl"
    write_suite(comp_path, chosen, {
        **common, "suite": "competition_like", "version": arguments.version,
        "band_cp": arguments.band, "max_gap_cp": arguments.max_gap, "max_dev": arguments.max_dev,
        "per_family": arguments.per_family, "admitted_by_band": len(level),
        "size": len(chosen), "hash": corpus_hash(chosen),
    }, "cl")
    stress_path = arguments.out_dir / f"stress_test_{arguments.version}.jsonl"
    write_suite(stress_path, stress_chosen, {
        **common, "suite": "stress_test", "version": arguments.version,
        "size": len(stress_chosen), "hash": corpus_hash(stress_chosen),
    }, "st")

    comp_md = summarise(
        chosen, f"COMPETITION_LIKE {arguments.version}",
        f"Near-level by **{header.get('oracle', {}).get('engine', 'oracle')}** at "
        f"{header.get('nodes', 0):,} nodes: |cp| <= {arguments.band}, best-minus-second "
        f"<= {arguments.max_gap} cp, |E[score]-0.5| <= {arguments.max_dev}. "
        f"{len(level)} candidates admitted by the band after de-duplication; "
        f"{len(chosen)} selected for coverage with at most {arguments.per_family} per opening "
        f"family and one per source game.",
    )
    (arguments.out_dir / f"competition_like_{arguments.version}.md").write_text(
        comp_md, encoding="utf-8")
    reasons = Counter(reason for r in stress_chosen for reason in r["stress_reasons"])
    stress_md = summarise(
        stress_chosen, f"STRESS_TEST {arguments.version}",
        "Built to find failures, not to measure Elo. Selected for large imbalances, "
        "compensation, promotion races, locked centres, exposed kings and only-moves, "
        "plus hand-picked classical endgame themes.\n\n| reason | count |\n|---|---|\n"
        + "\n".join(f"| {k} | {v} |" for k, v in reasons.most_common()),
    )
    (arguments.out_dir / f"stress_test_{arguments.version}.md").write_text(
        stress_md, encoding="utf-8")
    print(f"competition-like: {len(chosen)} positions (from {len(level)} admitted) -> {comp_path}")
    print(f"stress-test: {len(stress_chosen)} positions -> {stress_path}")
    print(comp_md)


if __name__ == "__main__":
    main()
