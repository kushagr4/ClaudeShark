"""KRB v KR and KRN v KR: is the false win a nominal minor counted at full value, and can one condition separate draws from wins?

Builds, per family, every retained game position of that material (grouped
by game), the false-win corpus rows in it, and a fixed-seed random sample
labelled by the oracle. Every position gets Stockfish's score, mate
distance, best move and line; V2.1's static, root quiescence and root at
depths 4, 6, 8 (10 on a subset); the static decomposed into material,
tables and tempo; and tactical flags read from the position and from the
first plies of Stockfish's line. Then three predefined scalings of the
minor's nominal value are applied offline to the static and, as an
approximation that holds while the material stays on the board, to the
root, and read on draws, on strategic wins and on tactical wins separately.

    uv run python -m tools.v2.krminor --out corpus/v2/fw/krminor/01_report.txt
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle
from tools.postmortem.play import Engine
from tools.v2.decompose import decompose

GAME_FILES = ("corpus/postmortem/games/annotated.jsonl", "corpus/mopup/games/gate2_annotated.jsonl",
              "corpus/passed/games/gate2_annotated.jsonl", "corpus/v2/kp/games/gate2_annotated.jsonl",
              "corpus/v2/kp/games/secondary_vs_passed_annotated.jsonl")
VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def family_of(board: chess.Board) -> tuple[str, bool] | None:
    """('KRB-KR' | 'KRN-KR', colour of the side with the minor) or None."""
    if board.pawns or board.queens:
        return None
    if len(board.pieces(chess.ROOK, True)) != 1 or len(board.pieces(chess.ROOK, False)) != 1:
        return None
    minors = {c: board.pieces_mask(chess.BISHOP, c) | board.pieces_mask(chess.KNIGHT, c) for c in (True, False)}
    if (minors[True] != 0) == (minors[False] != 0):
        return None
    strong = minors[True] != 0
    if minors[strong].bit_count() != 1:
        return None
    return ("KRB-KR" if board.bishops else "KRN-KR"), strong


def tactical_flags(board: chess.Board, strong: bool, label) -> dict:
    weak = not strong
    flags = {"in_check": board.is_check(), "hanging_rook_weak": False, "hanging_rook_strong": False, "hanging_minor": False,
             "material_change_in_pv6": False, "capture_in_pv6_by": None, "forced_mate": label.mate is not None and label.mate > 0,
             "mate_distance": label.mate, "trapped_king_weak": False, "sf_best_is_check": False, "sf_best_is_capture": False}

    def hanging(square: int, owner: bool) -> bool:
        attackers = board.attackers(not owner, square)
        if not attackers:
            return False
        defenders = board.attackers(owner, square)
        if not defenders:
            return True
        value = VALUE[board.piece_type_at(square)]
        return any(VALUE.get(board.piece_type_at(a), 0) < value for a in attackers)

    for sq in board.pieces(chess.ROOK, weak):
        flags["hanging_rook_weak"] = hanging(sq, weak)
    for sq in board.pieces(chess.ROOK, strong):
        flags["hanging_rook_strong"] = hanging(sq, strong)
    for sq in list(board.pieces(chess.BISHOP, strong)) + list(board.pieces(chess.KNIGHT, strong)):
        flags["hanging_minor"] = hanging(sq, strong)
    wk = board.king(weak)
    if wk is not None:
        on_rim = chess.square_file(wk) in (0, 7) or chess.square_rank(wk) in (0, 7)
        probe = board.copy(stack=False)
        probe.turn = weak
        if not probe.is_valid():
            king_moves = 8
        else:
            king_moves = sum(1 for m in probe.legal_moves if m.from_square == wk)
        flags["trapped_king_weak"] = on_rim and king_moves <= 1
    b = board.copy(stack=False)
    for i, uci in enumerate(list(label.pv)[:6]):
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            break
        if move not in b.legal_moves:
            break
        if i == 0:
            flags["sf_best_is_check"] = b.gives_check(move)
            flags["sf_best_is_capture"] = b.is_capture(move)
        if b.is_capture(move):
            flags["material_change_in_pv6"] = True
            flags["capture_in_pv6_by"] = "strong" if b.turn == strong else "weak"
            break
        b.push(move)
    return flags


def synthetic(family: str, n: int, rng: random.Random) -> list[chess.Board]:
    minor = chess.BISHOP if family == "KRB-KR" else chess.KNIGHT
    out = []
    while len(out) < n:
        board = chess.Board(None)
        squares = rng.sample(range(64), 5)
        strong = rng.choice((True, False))
        board.set_piece_at(squares[0], chess.Piece(chess.KING, True))
        board.set_piece_at(squares[1], chess.Piece(chess.KING, False))
        board.set_piece_at(squares[2], chess.Piece(chess.ROOK, strong))
        board.set_piece_at(squares[3], chess.Piece(chess.ROOK, not strong))
        board.set_piece_at(squares[4], chess.Piece(minor, strong))
        board.turn = rng.choice((True, False))
        if board.is_valid() and not board.is_game_over():
            out.append(board)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", type=int, default=150)
    parser.add_argument("--depth10", type=int, default=40, help="synthetic positions per family also searched to depth 10")
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20260904)

    rows: list[dict] = []
    # Retained game positions of the family, up to three per game, four plies apart.
    for path in GAME_FILES:
        with Path(path).open(encoding="utf-8") as fh:
            games = [json.loads(line) for line in fh]
        for g in games:
            traj = f"{path.split('/')[1]}:{g['cluster']}:{'cW' if g['cand_white'] else 'cB'}"
            kept: list[dict] = []
            for m in g["moves"]:
                board = chess.Board(m["fen"])
                fam = family_of(board)
                if fam is None:
                    continue
                if any(abs(m["ply"] - k["ply"]) < 4 for k in kept) or len(kept) >= 3:
                    continue
                mover_is_strong = board.turn == fam[1]
                mover_score = g["cand_score"] if m["mover"] == "cand" else 1.0 - g["cand_score"]
                kept.append({"fen": m["fen"], "family": fam[0], "strong_white": fam[1], "source": "game", "trajectory": traj, "ply": m["ply"],
                             "game_result_for_strong": mover_score if mover_is_strong else 1.0 - mover_score})
            rows.extend(kept)
    fw_ids = set()
    with Path("corpus/v2/fw/falsewin_corpus_v1.jsonl").open(encoding="utf-8") as fh:
        for line in list(fh)[1:]:
            r = json.loads(line)
            if family_of(chess.Board(r["fen"])) is not None:
                fw_ids.add(r["fen"])
    for fam in ("KRB-KR", "KRN-KR"):
        for i, board in enumerate(synthetic(fam, arguments.synthetic, rng)):
            rows.append({"fen": board.fen(), "family": fam, "strong_white": family_of(board)[1], "source": "synthetic",
                         "trajectory": f"synthetic:{fam}:{i}", "ply": 0, "game_result_for_strong": None})
    seen: set[str] = set()
    rows = [r for r in rows if not (r["fen"] in seen or seen.add(r["fen"]))]
    for r in rows:
        r["in_false_win_corpus"] = r["fen"] in fw_ids
    print(f"{len(rows)} positions: {dict(Counter((r['family'], r['source']) for r in rows))}", flush=True)

    engines = {d: Engine(Path("champions/v2_1_kingpawn"), d) for d in (4, 6, 8, 10)}
    d10_budget = Counter()
    try:
        with Oracle() as oracle:
            for i, r in enumerate(rows, start=1):
                board = chess.Board(r["fen"])
                strong = r["strong_white"]
                sign = 1 if board.turn == strong else -1  # convert side-to-move scores to the strong side's view
                label = oracle.analyse(r["fen"], arguments.nodes)
                r["sf_strong"] = sign * label.cp_stm
                r["sf_mate_strong"] = None if label.mate is None else sign * label.mate
                r["sf_best"] = label.best
                r["sf_pv"] = list(label.pv)[:8]
                r["flags"] = tactical_flags(board, strong, label)
                if r["sf_mate_strong"] is not None and r["sf_mate_strong"] < 0:
                    r["flags"]["forced_mate"] = False
                for d in (4, 6, 8):
                    engines[d].ask("new")
                    r[f"v21_d{d}"] = sign * engines[d].ask(f"go {r['fen']}")["score"]
                engines[6].ask("new")
                q = engines[6].ask(f"qs {r['fen']}")["qs"]
                r["v21_qs"] = q if strong else -q  # qs is White's view
                st = engines[6].ask(f"static {r['fen']}")["static"]
                r["v21_static"] = st if strong else -st
                want10 = r["source"] == "game" or r["in_false_win_corpus"] or d10_budget[r["family"]] < arguments.depth10
                if want10:
                    d10_budget[r["family"]] += 1 if r["source"] != "game" else 0
                    engines[10].ask("new")
                    r["v21_d10"] = sign * engines[10].ask(f"go {r['fen']}")["score"]
                d = decompose(board)
                view = 1 if strong else -1
                r["decomposition_strong"] = {k: view * d[k] for k in ("material", "pst", "pair", "king_pawn")}
                r["tempo_strong"] = 8 if board.turn == strong else -8
                r["minor_value_tapered"] = abs(d["material"])  # the only material difference is the minor
                sf = r["sf_strong"]
                if (r["sf_mate_strong"] is not None and r["sf_mate_strong"] > 0) or sf >= 300:
                    r["label"] = "win"
                elif abs(sf) <= 60 and r["sf_mate_strong"] is None:
                    r["label"] = "draw"
                else:
                    r["label"] = "other"
                f = r["flags"]
                r["tactical"] = bool(f["forced_mate"] and (r["sf_mate_strong"] or 99) <= 15) or f["material_change_in_pv6"] or f["hanging_rook_weak"] or f["trapped_king_weak"]
                r["false_win"] = r["label"] == "draw" and r["v21_d6"] >= 150
                if i % 25 == 0:
                    print(f"  {i}/{len(rows)}", flush=True)
    finally:
        for e in engines.values():
            e.close()

    lines = [f"== KRB v KR and KRN v KR: {len(rows)} positions ({dict(Counter(r['source'] for r in rows))}), oracle {arguments.nodes} nodes, V2.1 ==",
             "all scores from the side with the minor ('strong'); win = SF >= +300 or mate for strong; draw = |SF| <= 60 and no mate; false win = draw with V2.1 depth-6 root >= +150", ""]
    for fam in ("KRB-KR", "KRN-KR"):
        rs = [r for r in rows if r["family"] == fam]
        lines.append(f"-- {fam}: {len(rs)} positions, {len({r['trajectory'] for r in rs})} trajectories; game positions {sum(r['source'] == 'game' for r in rs)} in {len({r['trajectory'] for r in rs if r['source'] == 'game'})} games")
        for lab in ("win", "draw", "other"):
            xs = [r for r in rs if r["label"] == lab]
            lines.append(f"   {lab:<5} {len(xs):>4} positions ({len({r['trajectory'] for r in xs})} traj); tactical {sum(r['tactical'] for r in xs)}, strategic {sum(not r['tactical'] for r in xs)}; false wins {sum(r['false_win'] for r in xs)}")
        draws = [r for r in rs if r["label"] == "draw"]
        wins = [r for r in rs if r["label"] == "win"]
        lines.append(f"   false wins: {sum(r['false_win'] for r in draws)} of {len(draws)} draws ({sum(r['false_win'] for r in draws) / max(1, len(draws)):.0%}); from the false-win corpus {sum(r['in_false_win_corpus'] for r in rs)} rows")
        lines.append("")
        lines.append("   tactical contamination of the wins (a win may carry several flags):")
        for key in ("forced_mate", "material_change_in_pv6", "hanging_rook_weak", "hanging_minor", "hanging_rook_strong", "in_check", "trapped_king_weak", "sf_best_is_check", "sf_best_is_capture"):
            lines.append(f"      {key:<26} wins {sum(r['flags'][key] for r in wins):>3}/{len(wins):<3}  draws {sum(r['flags'][key] for r in draws):>3}/{len(draws)}")
        strategic_wins = [r for r in wins if not r["tactical"]]
        lines.append(f"   wins remaining after excluding forced mate (<= 15), material change within 6 plies of the line, a hanging defending rook or a trapped defending king: {len(strategic_wins)} of {len(wins)}")
        lines.append("")
        lines.append("   static decomposition (strong side's view) and depth behaviour, means:")
        lines.append(f"      {'class':<16} {'n':>3} {'material':>8} {'tables':>7} {'tempo':>6} {'static':>7} {'qs':>6} {'d4':>6} {'d6':>6} {'d8':>6} {'d10':>6} {'n10':>4}")
        for lab, xs in (("draw", draws), ("false win", [r for r in draws if r["false_win"]]), ("win", wins), ("strategic win", strategic_wins), ("tactical win", [r for r in wins if r["tactical"]])):
            if not xs:
                continue
            d10 = [r["v21_d10"] for r in xs if "v21_d10" in r]
            lines.append(f"      {lab:<16} {len(xs):>3} {statistics.mean(r['decomposition_strong']['material'] for r in xs):>+8.0f} {statistics.mean(r['decomposition_strong']['pst'] for r in xs):>+7.0f} {statistics.mean(r['tempo_strong'] for r in xs):>+6.0f} "
                         f"{statistics.mean(r['v21_static'] for r in xs):>+7.0f} {statistics.mean(r['v21_qs'] for r in xs):>+6.0f} {statistics.mean(r['v21_d4'] for r in xs):>+6.0f} {statistics.mean(r['v21_d6'] for r in xs):>+6.0f} {statistics.mean(r['v21_d8'] for r in xs):>+6.0f} "
                         f"{(statistics.mean(d10) if d10 else 0):>+6.0f} {len(d10):>4}")
        lines.append("")
        lines.append("   distributions of the depth-6 root (strong side's view):")
        buckets = ((-10**6, 100), (100, 200), (200, 300), (300, 10**6))
        for lab, xs in (("draws", draws), ("wins", wins), ("strategic wins", strategic_wins)):
            cells = " ".join(f"{lo if lo > -10**6 else '<'}..{hi if hi < 10**6 else ''}: {sum(lo <= r['v21_d6'] < hi for r in xs):>3}" for lo, hi in buckets)
            lines.append(f"      {lab:<16} {cells}")
        lines.append("")
        lines.append("   scaler screen: nominal minor value scaled by f; adjusted = score - (1 - f) * minor (root adjustment is the same shift, valid while the minor stays on the board)")
        lines.append(f"      {'f':<8} {'draw static':>11} {'draw d6':>8} {'draws d6 < +100':>15} {'false wins d6 < +150':>20} {'win static':>10} {'win d6':>7} {'wins d6 < +100':>14} {'strategic wins d6 < +100':>24} {'tactical wins d6 < +100':>23}")
        for name, f in (("off", 1.0), ("mild", 0.5), ("medium", 0.25), ("strong", 0.125)):
            def adj(r, key, f=f):
                return r[key] - (1 - f) * r["minor_value_tapered"]
            fw = [r for r in draws if r["false_win"]]
            tact = [r for r in wins if r["tactical"]]
            lines.append(f"      {name:<8} {statistics.mean(adj(r, 'v21_static') for r in draws) if draws else 0:>+11.0f} {statistics.mean(adj(r, 'v21_d6') for r in draws) if draws else 0:>+8.0f} {sum(adj(r, 'v21_d6') < 100 for r in draws):>7}/{len(draws):<7} {sum(adj(r, 'v21_d6') < 150 for r in fw):>10}/{len(fw):<9} "
                         f"{statistics.mean(adj(r, 'v21_static') for r in wins) if wins else 0:>+10.0f} {statistics.mean(adj(r, 'v21_d6') for r in wins) if wins else 0:>+7.0f} {sum(adj(r, 'v21_d6') < 100 for r in wins):>6}/{len(wins):<7} {sum(adj(r, 'v21_d6') < 100 for r in strategic_wins):>12}/{len(strategic_wins):<11} {sum(adj(r, 'v21_d6') < 100 for r in tact):>11}/{len(tact)}")
        lines.append("")
        lines.append("   condition screen: within the family, does one condition separate draws from wins? (share of positions meeting the condition that are wins)")
        conds = {
            "all family positions": lambda r: True,
            "not in check": lambda r: not r["flags"]["in_check"],
            "no hanging piece (either side)": lambda r: not (r["flags"]["hanging_rook_weak"] or r["flags"]["hanging_rook_strong"] or r["flags"]["hanging_minor"]),
            "no capture within 6 plies of SF's line": lambda r: not r["flags"]["material_change_in_pv6"],
            "no forced mate": lambda r: not r["flags"]["forced_mate"],
            "defending king not trapped on the rim": lambda r: not r["flags"]["trapped_king_weak"],
            "quiet: none of the above": lambda r: not (r["flags"]["in_check"] or r["flags"]["hanging_rook_weak"] or r["flags"]["hanging_rook_strong"] or r["flags"]["hanging_minor"] or r["flags"]["material_change_in_pv6"] or r["flags"]["forced_mate"] or r["flags"]["trapped_king_weak"]),
        }
        for name, cond in conds.items():
            xs = [r for r in rs if cond(r) and r["label"] in ("win", "draw")]
            w = sum(r["label"] == "win" for r in xs)
            lines.append(f"      {name:<42} n {len(xs):>3}  wins {w:>3} ({w / max(1, len(xs)):.0%})  draws {len(xs) - w:>3}  | V2.1 d6 on the draws {statistics.mean(r['v21_d6'] for r in xs if r['label'] == 'draw') if len(xs) - w else 0:+.0f}")
        lines.append("")
        lines.append("   game positions (retained self-play), strong side's view:")
        for r in [r for r in rs if r["source"] == "game"]:
            lines.append(f"      {r['trajectory']:<26} ply {r['ply']:>3} {r['label']:<5} SF {r['sf_strong']:>+5} mate {r['sf_mate_strong']}  static {r['v21_static']:>+4} d6 {r['v21_d6']:>+4} d10 {r.get('v21_d10', '-')}  tactical {r['tactical']}  result for strong {r['game_result_for_strong']}  fw-corpus {r['in_false_win_corpus']}  {r['fen']}")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
