"""Lane B: does any narrow static king-attack signal separate real attacks?

Label, white view: ``SF - material``, on middlegame positions with both queens
on the board. POS = |label| >= 200 (a dynamic factor worth two pawns that the
material count cannot see); NEG = |label| <= 100 (the material count is
right), with the hard negatives |material| >= 200 reported separately. Each
signal is a white-view difference D = f(white attacks black king) - f(black
attacks white king). A term built on it needs |D| large and sign-aligned on
POS and |D| small on NEG.

Sources: every ply of the 15 rated games (both sides) and the 6,203-position
labelled TWIC pool. The frozen competition holdout is in neither file.

    uv run python -m tools.daily.laneb_signals

The second table prints the five attack sequences the rated-games postmortem
named (rounds 1, 5, 10, 11 and round 3 moves 18-20), position by position.
"""

from __future__ import annotations

import bisect
import json
import statistics
from pathlib import Path

import chess

V = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900}
SIGNALS = ("safe_checks", "escapes", "ring_attackers", "ring_net", "pinned")
SEQUENCES = {
    "round1-the-castle-gambit": range(19, 43),
    "round5-stonkfish": range(31, 41),
    "round10-elbow-grease": range(14, 30),
    "round11-mangodogo": range(19, 53),
    "round3-baryon": range(35, 41),
}


def material_white(board: chess.Board) -> int:
    return sum(
        value
        * (
            chess.popcount(board.pieces_mask(piece, True))
            - chess.popcount(board.pieces_mask(piece, False))
        )
        for piece, value in V.items()
    )


def _ring(board: chess.Board, colour: chess.Color) -> tuple[int, int]:
    king = board.king(colour)
    assert king is not None
    return king, chess.BB_KING_ATTACKS[king] | chess.BB_SQUARES[king]


def safe_checks(board: chess.Board, attacker: chess.Color) -> int:
    """Checks the attacker could give now onto squares the defender does not
    control (a king-only defence of a square the attacker also covers counts)."""
    defender = not attacker
    probe = board.copy(stack=False)
    if probe.turn != attacker:
        probe.turn = attacker
    if probe.is_check():
        return 0
    count = 0
    for move in probe.generate_pseudo_legal_moves():
        if not probe.gives_check(move):
            continue
        from_mask = chess.BB_SQUARES[move.from_square]
        defenders = probe.attackers(defender, move.to_square) & ~from_mask
        king_only = defenders == (defenders & probe.kings)
        if not defenders or (
            king_only and probe.attackers(attacker, move.to_square) & ~from_mask
        ):
            count += 1
    return count


def escapes(board: chess.Board, defender: chess.Color) -> int:
    attacker = not defender
    king, _ = _ring(board, defender)
    free = chess.BB_KING_ATTACKS[king] & ~board.occupied_co[defender]
    return sum(1 for square in chess.scan_forward(free) if not board.attackers(attacker, square))


def pressure(board: chess.Board, attacker: chess.Color) -> tuple[int, int]:
    """(attacker pieces bearing on the defender's king ring, defender pieces defending it)."""
    defender = not attacker
    _, ring = _ring(board, defender)
    attacking = sum(
        1
        for square in chess.scan_forward(board.occupied_co[attacker] & ~board.kings)
        if board.attacks(square) & ring
    )
    defending = sum(
        1
        for square in chess.scan_forward(board.occupied_co[defender] & ~board.kings)
        if board.attacks(square) & ring
    )
    return attacking, defending


def pinned(board: chess.Board, defender: chess.Color) -> int:
    return sum(
        1
        for square in chess.scan_forward(board.occupied_co[defender] & ~board.kings)
        if board.is_pinned(defender, square)
    )


def signals(board: chess.Board) -> dict[str, int]:
    """White-view differences: positive means White is the one attacking."""
    attack_w, defend_b = pressure(board, True)
    attack_b, defend_w = pressure(board, False)
    return {
        "safe_checks": safe_checks(board, True) - safe_checks(board, False),
        "escapes": escapes(board, False) - escapes(board, True),
        "ring_attackers": attack_w - attack_b,
        "ring_net": (attack_w - defend_b) - (attack_b - defend_w),
        "pinned": pinned(board, False) - pinned(board, True),
    }


def middlegame(board: chess.Board) -> bool:
    return bool(
        board.queens & board.occupied_co[True]
        and board.queens & board.occupied_co[False]
        and chess.popcount(board.occupied) >= 16
    )


def auc(positives: list[int], negatives: list[int]) -> float:
    """P(|D| on a positive > |D| on a negative), ties counted half."""
    ordered = sorted(negatives)
    total = 0.0
    for value in positives:
        low = bisect.bisect_left(ordered, value)
        high = bisect.bisect_right(ordered, value)
        total += low + 0.5 * (high - low)
    return total / (len(positives) * len(negatives))


def load_rows() -> list[tuple[str, str, str, int]]:
    rows: list[tuple[str, str, str, int]] = []
    with Path("corpus/daily/games/rated15_annotated.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            game = json.loads(line)
            for move in game["moves"]:
                score = move.get("sf_cp_white_before")
                if score is not None and abs(score) < 5000:
                    rows.append(("rated", game["game"], move["fen"], score))
    with Path("corpus/candidates_labelled.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record") == "header":
                continue
            score = (record.get("reference") or {}).get("cp_white")
            if score is not None and abs(score) < 5000:
                rows.append(("pool", record.get("game_id", ""), record["fen"], score))
    return rows


def separation_table() -> None:
    rows = load_rows()
    positives: list[dict[str, int | str]] = []
    negatives: list[dict[str, int | str]] = []
    for source, game, fen, score in rows:
        board = chess.Board(fen)
        if not middlegame(board):
            continue
        material = material_white(board)
        label = score - material
        record: dict[str, int | str] = {"src": source, "game": game, "mat": material, "label": label}
        record.update(signals(board))
        if abs(label) >= 200:
            positives.append(record)
        elif abs(label) <= 100:
            negatives.append(record)
    rated = [r for r in positives if r["src"] == "rated"]
    hard = [r for r in negatives if abs(int(r["mat"])) >= 200]
    print(
        f"rows {len(rows)}; middlegame with queens: POS {len(positives)} "
        f"(rated {len(rated)}), NEG {len(negatives)}, hard NEG {len(hard)}"
    )
    print(
        f"{'signal':15s} {'AUC':>6s} {'sign agree POS':>15s} {'zero POS':>9s} "
        f"{'mean|D| POS':>12s} {'mean|D| NEG':>12s} {'mean|D| hard':>13s} {'rated AUC':>10s} {'rated agree':>12s}"
    )
    for key in SIGNALS:
        pos_abs = [abs(int(r[key])) for r in positives]
        neg_abs = [abs(int(r[key])) for r in negatives]
        agree = sum(1 for r in positives if int(r[key]) * int(r["label"]) > 0) / len(positives)
        zero = sum(1 for r in positives if int(r[key]) == 0) / len(positives)
        rated_abs = [abs(int(r[key])) for r in rated]
        rated_agree = sum(1 for r in rated if int(r[key]) * int(r["label"]) > 0) / len(rated)
        print(
            f"{key:15s} {auc(pos_abs, neg_abs):6.3f} {agree:15.3f} {zero:9.2f} "
            f"{statistics.mean(pos_abs):12.2f} {statistics.mean(neg_abs):12.2f} "
            f"{statistics.mean(abs(int(r[key])) for r in hard):13.2f} "
            f"{auc(rated_abs, neg_abs):10.3f} {rated_agree:12.3f}"
        )


def sequence_table() -> None:
    with Path("corpus/daily/games/rated15_annotated.jsonl").open(encoding="utf-8") as handle:
        games = {g["game"]: g for g in map(json.loads, handle)}
    with Path("corpus/daily/rated15_report.jsonl").open(encoding="utf-8") as handle:
        report = {(r["game"], r["ply"]): r for r in map(json.loads, handle)}
    print()
    print(
        f"{'game':12s} {'ply':>3s} stm {'sf_w':>5s} {'mat_w':>5s} {'label':>5s} {'root':>5s} "
        f"{'stat':>5s} | {'chk':>3s} {'esc':>3s} {'ratt':>4s} {'rnet':>4s} {'pin':>3s}  san"
    )
    agreement = {key: [0, 0] for key in SIGNALS}
    for game, plies in SEQUENCES.items():
        for move in games[game]["moves"]:
            if move["ply"] not in plies:
                continue
            score = move["sf_cp_white_before"]
            if score is None or abs(score) >= 5000:
                continue
            board = chess.Board(move["fen"])
            material = material_white(board)
            label = score - material
            values = signals(board)
            ours = report.get((game, move["ply"]), {}).get("rated-v1", {})
            root, static = ours.get("score"), ours.get("static")
            if root is not None and move["turn"] == "b":
                root, static = -root, -static
            for key in SIGNALS:
                if values[key]:
                    agreement[key][1] += 1
                    if values[key] * label > 0:
                        agreement[key][0] += 1
            show = lambda v: "-" if v is None else str(v)  # noqa: E731
            print(
                f"{game[:12]:12s} {move['ply']:3d} {move['turn']:3s} {score:5d} {material:5d} "
                f"{label:5d} {show(root):>5s} {show(static):>5s} | {values['safe_checks']:3d} "
                f"{values['escapes']:3d} {values['ring_attackers']:4d} {values['ring_net']:4d} "
                f"{values['pinned']:3d}  {move['san']}"
            )
    print("\nsign agreement with SF - material where the signal is non-zero:")
    for key, (agree, total) in agreement.items():
        print(f"  {key:15s} {agree}/{total}")


if __name__ == "__main__":
    separation_table()
    sequence_table()
