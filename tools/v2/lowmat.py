"""Low-material family expansion: do the siblings of KRB/KRN v KR share the nominal-surplus mechanism?

Families (the "strong" side is the one holding the nominal surplus):
KR v KB, KR v KN (pawnless), KB v K+P, KN v K+P, KB v K+2P, KN v K+2P
(the minor side has no pawns). KRB v KR and KRN v KR are loaded from the
earlier audit as the reference. For each family: retained game positions
(three per game at most), false-win corpus rows, and a fixed-seed random
sample, all labelled by the oracle and scored by V2.1 (static, quiescence,
depths 4/6/8, depth 10 on a subset), the static decomposed, tactical flags
read from the position and Stockfish's line, a per-family scaler screen,
and the real-game reach of every family over the 1,000 retained games.

    uv run python -m tools.v2.lowmat --out corpus/v2/fw/lowmat/01_report.txt
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
from tools.v2.krminor import GAME_FILES, tactical_flags

FAMILIES = ("KR-KB", "KR-KN", "KB-KP", "KN-KP", "KB-KPP", "KN-KPP")
REFERENCE = ("KRB-KR", "KRN-KR")


def family_of(board: chess.Board) -> tuple[str, bool] | None:
    """(family, colour of the strong side) for the six sibling families, or None."""
    if board.queens:
        return None
    counts = {c: {pt: len(board.pieces(pt, c)) for pt in chess.PIECE_TYPES} for c in (True, False)}
    for strong in (True, False):
        a, b = counts[strong], counts[not strong]
        minors_a = a[chess.BISHOP] + a[chess.KNIGHT]
        minors_b = b[chess.BISHOP] + b[chess.KNIGHT]
        if a[chess.PAWN] == 0 and b[chess.PAWN] == 0 and a[chess.ROOK] == 1 and b[chess.ROOK] == 0 and minors_a == 0 and minors_b == 1:
            return ("KR-KB" if b[chess.BISHOP] else "KR-KN"), strong
        if a[chess.PAWN] == 0 and a[chess.ROOK] == 0 and b[chess.ROOK] == 0 and minors_a == 1 and minors_b == 0 and b[chess.PAWN] in (1, 2):
            kind = "KB" if a[chess.BISHOP] else "KN"
            return (f"{kind}-KP" if b[chess.PAWN] == 1 else f"{kind}-KPP"), strong
    return None


def synthetic(family: str, n: int, rng: random.Random) -> list[chess.Board]:
    out = []
    while len(out) < n:
        board = chess.Board(None)
        strong = rng.choice((True, False))
        pieces: list[tuple[int, bool, str]] = []
        if family in ("KR-KB", "KR-KN"):
            pieces = [(chess.ROOK, strong, "any"), (chess.BISHOP if family == "KR-KB" else chess.KNIGHT, not strong, "any")]
        else:
            minor = chess.BISHOP if family.startswith("KB") else chess.KNIGHT
            pieces = [(minor, strong, "any")] + [(chess.PAWN, not strong, "pawn")] * (2 if family.endswith("PP") else 1)
        used: set[int] = set()
        ok = True
        for pt, colour, kind in [(chess.KING, True, "any"), (chess.KING, False, "any"), *pieces]:
            squares = [s for s in range(64) if s not in used and (kind != "pawn" or 1 <= chess.square_rank(s) <= 6)]
            sq = rng.choice(squares)
            board.set_piece_at(sq, chess.Piece(pt, colour))
            used.add(sq)
        board.turn = rng.choice((True, False))
        if ok and board.is_valid() and not board.is_game_over():
            out.append(board)
    return out


def label_of(sf_strong: int, mate_strong: int | None) -> str:
    if (mate_strong is not None and mate_strong > 0) or sf_strong >= 300:
        return "win"
    if (mate_strong is not None and mate_strong < 0) or sf_strong <= -300:
        return "loss"
    if abs(sf_strong) <= 60 and mate_strong is None:
        return "draw"
    return "other"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", type=int, default=100)
    parser.add_argument("--depth10", type=int, default=20)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--reference", type=Path, default=Path("corpus/v2/fw/krminor/01_report.jsonl"))
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20260905)

    rows: list[dict] = []
    reach: dict[str, dict] = {f: {"games": set(), "moves": 0, "false_win_traj": set()} for f in FAMILIES + REFERENCE}
    total_moves = 0
    total_games = 0
    from tools.v2.krminor import family_of as ref_family_of
    for path in GAME_FILES:
        with Path(path).open(encoding="utf-8") as fh:
            games = [json.loads(line) for line in fh]
        for g in games:
            total_games += 1
            traj = f"{path.split('/')[1]}:{g['cluster']}:{'cW' if g['cand_white'] else 'cB'}"
            kept: list[dict] = []
            for m in g["moves"]:
                total_moves += 1
                board = chess.Board(m["fen"])
                fam = family_of(board) or ref_family_of(board)
                if fam is None:
                    continue
                reach[fam[0]]["games"].add(traj)
                reach[fam[0]]["moves"] += 1
                white = m["turn"] == "w"
                sf = m["sf_cp_white_before"] if white else -m["sf_cp_white_before"]
                if sf is not None and m["score_stm"] >= 150 and abs(sf) <= 60 and board.turn == fam[1]:
                    reach[fam[0]]["false_win_traj"].add(traj)
                if fam[0] in REFERENCE:
                    continue
                if any(abs(m["ply"] - k["ply"]) < 4 for k in kept) or len(kept) >= 3:
                    continue
                mover_is_strong = board.turn == fam[1]
                mover_score = g["cand_score"] if m["mover"] == "cand" else 1.0 - g["cand_score"]
                kept.append({"fen": m["fen"], "family": fam[0], "strong_white": fam[1], "source": "game", "trajectory": traj, "ply": m["ply"],
                             "game_result_for_strong": mover_score if mover_is_strong else 1.0 - mover_score})
            rows.extend(kept)
    fw_fens = set()
    with Path("corpus/v2/fw/falsewin_corpus_v1.jsonl").open(encoding="utf-8") as fh:
        for line in list(fh)[1:]:
            r = json.loads(line)
            if family_of(chess.Board(r["fen"])) is not None:
                fw_fens.add(r["fen"])
    for fam in FAMILIES:
        for i, board in enumerate(synthetic(fam, arguments.synthetic, rng)):
            rows.append({"fen": board.fen(), "family": fam, "strong_white": family_of(board)[1], "source": "synthetic",
                         "trajectory": f"synthetic:{fam}:{i}", "ply": 0, "game_result_for_strong": None})
    seen: set[str] = set()
    rows = [r for r in rows if not (r["fen"] in seen or seen.add(r["fen"]))]
    for r in rows:
        r["in_false_win_corpus"] = r["fen"] in fw_fens
    print(f"{len(rows)} positions: {dict(Counter((r['family'], r['source']) for r in rows))}", flush=True)

    engines = {d: Engine(Path("champions/v2_1_kingpawn"), d) for d in (4, 6, 8, 10)}
    d10_budget: Counter = Counter()
    try:
        with Oracle() as oracle:
            for i, r in enumerate(rows, start=1):
                board = chess.Board(r["fen"])
                strong = r["strong_white"]
                sign = 1 if board.turn == strong else -1
                label = oracle.analyse(r["fen"], arguments.nodes)
                r["sf_strong"] = sign * label.cp_stm
                r["sf_mate_strong"] = None if label.mate is None else sign * label.mate
                r["sf_best"] = label.best
                r["sf_pv"] = list(label.pv)[:8]
                flags = tactical_flags(board, strong, label)
                if r["sf_mate_strong"] is not None and r["sf_mate_strong"] < 0:
                    flags["forced_mate"] = False
                # Forced promotion for the pawn side within the line, and a piece win for the strong side.
                b = board.copy(stack=False)
                flags["promotion_in_pv8"] = False
                for uci in list(label.pv)[:8]:
                    mv = chess.Move.from_uci(uci)
                    if mv not in b.legal_moves:
                        break
                    if mv.promotion:
                        flags["promotion_in_pv8"] = True
                        break
                    b.push(mv)
                r["flags"] = flags
                for d in (4, 6, 8):
                    engines[d].ask("new")
                    r[f"v21_d{d}"] = sign * engines[d].ask(f"go {r['fen']}")["score"]
                engines[6].ask("new")
                q = engines[6].ask(f"qs {r['fen']}")["qs"]
                r["v21_qs"] = q if strong else -q
                st = engines[6].ask(f"static {r['fen']}")["static"]
                r["v21_static"] = st if strong else -st
                if r["source"] == "game" or r["in_false_win_corpus"] or d10_budget[r["family"]] < arguments.depth10:
                    if r["source"] != "game":
                        d10_budget[r["family"]] += 1
                    engines[10].ask("new")
                    r["v21_d10"] = sign * engines[10].ask(f"go {r['fen']}")["score"]
                d = decompose(board)
                view = 1 if strong else -1
                r["decomposition_strong"] = {k: view * d[k] for k in ("material", "pst", "pair", "king_pawn")}
                r["tempo_strong"] = 8 if board.turn == strong else -8
                r["surplus_tapered"] = r["decomposition_strong"]["material"]  # the nominal surplus is the whole material term here
                r["label"] = label_of(r["sf_strong"], r["sf_mate_strong"])
                f = r["flags"]
                r["tactical"] = bool(f["forced_mate"] and (r["sf_mate_strong"] or 99) <= 15) or f["material_change_in_pv6"] or f["hanging_rook_weak"] or f["trapped_king_weak"] or f["promotion_in_pv8"]
                r["false_win"] = r["label"] == "draw" and r["v21_d6"] >= 150
                if i % 25 == 0:
                    print(f"  {i}/{len(rows)}", flush=True)
    finally:
        for e in engines.values():
            e.close()

    # Reference rows from the earlier audit, mapped to the same schema.
    reference_rows = []
    if arguments.reference.exists():
        with arguments.reference.open(encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                r["surplus_tapered"] = r["decomposition_strong"]["material"]
                if "loss" not in r["label"] and r["label"] == "other" and r["sf_strong"] <= -300:
                    r["label"] = "loss"
                reference_rows.append(r)

    lines = [f"== LOW-MATERIAL FAMILY EXPANSION: {len(rows)} new positions ({dict(Counter(r['source'] for r in rows))}) + {len(reference_rows)} reference rows; oracle {arguments.nodes} nodes; V2.1 ==",
             "scores from the side with the nominal surplus ('strong'); win/loss = SF >= +300 / <= -300 or mate; draw = |SF| <= 60; false win = draw with V2.1 depth-6 root >= +150", ""]
    lines.append("== REAL-GAME REACH over the 1,000 retained games (5 x 200), all engines' moves ==")
    lines.append(f"   {'family':<8} {'games':>5} {'per 1000':>8} {'moves':>6} {'activation':>10} {'false-win traj (root>=150, |SF|<=60)':>36}")
    for fam in REFERENCE + FAMILIES:
        rc = reach[fam]
        lines.append(f"   {fam:<8} {len(rc['games']):>5} {1000 * len(rc['games']) / total_games:>8.1f} {rc['moves']:>6} {rc['moves'] / total_moves:>10.2%} {len(rc['false_win_traj']):>36}")
    union = set().union(*(reach[f]["games"] for f in REFERENCE + FAMILIES))
    union_moves = sum(reach[f]["moves"] for f in REFERENCE + FAMILIES)
    union_fw = set().union(*(reach[f]["false_win_traj"] for f in REFERENCE + FAMILIES))
    lines.append(f"   {'ALL':<8} {len(union):>5} {1000 * len(union) / total_games:>8.1f} {union_moves:>6} {union_moves / total_moves:>10.2%} {len(union_fw):>36}")
    lines.append(f"   ({total_games} games, {total_moves} moves)")
    lines.append("")
    all_rows = rows + reference_rows
    summary = {}
    for fam in REFERENCE + FAMILIES:
        rs = [r for r in all_rows if r["family"] == fam]
        if not rs:
            continue
        wins = [r for r in rs if r["label"] == "win"]
        draws = [r for r in rs if r["label"] == "draw"]
        losses = [r for r in rs if r["label"] == "loss"]
        others = [r for r in rs if r["label"] == "other"]
        strategic = [r for r in wins if not r["tactical"]]
        fw = [r for r in draws if r["false_win"]]
        lines.append(f"-- {fam}: {len(rs)} positions ({sum(r['source'] == 'game' for r in rs)} from {len({r['trajectory'] for r in rs if r['source'] == 'game'})} games); win {len(wins)}, draw {len(draws)}, loss {len(losses)}, other {len(others)}; false wins {len(fw)} of {len(draws)} draws ({len(fw) / max(1, len(draws)):.0%}); tactical wins {len(wins) - len(strategic)}, strategic wins {len(strategic)}")
        lines.append("   tactical flags on the wins: " + ", ".join(f"{k} {sum(r['flags'].get(k, False) for r in wins)}" for k in ("forced_mate", "material_change_in_pv6", "hanging_rook_weak", "hanging_minor", "promotion_in_pv8", "trapped_king_weak", "in_check")))
        lines.append(f"   {'class':<10} {'n':>3} {'material':>8} {'tables':>7} {'tempo':>6} {'king-pawn':>9} {'static':>7} {'qs':>6} {'d4':>6} {'d6':>6} {'d8':>6} {'d10':>6} {'n10':>4} {'SF':>6}")
        for lab, xs in (("draw", draws), ("false win", fw), ("win", wins), ("strategic", strategic), ("loss", losses)):
            if not xs:
                continue
            d10 = [r["v21_d10"] for r in xs if "v21_d10" in r]
            lines.append(f"   {lab:<10} {len(xs):>3} {statistics.mean(r['decomposition_strong']['material'] for r in xs):>+8.0f} {statistics.mean(r['decomposition_strong']['pst'] for r in xs):>+7.0f} {statistics.mean(r['tempo_strong'] for r in xs):>+6.0f} {statistics.mean(r['decomposition_strong'].get('king_pawn', 0) for r in xs):>+9.0f} "
                         f"{statistics.mean(r['v21_static'] for r in xs):>+7.0f} {statistics.mean(r['v21_qs'] for r in xs):>+6.0f} {statistics.mean(r['v21_d4'] for r in xs):>+6.0f} {statistics.mean(r['v21_d6'] for r in xs):>+6.0f} {statistics.mean(r['v21_d8'] for r in xs):>+6.0f} {(statistics.mean(d10) if d10 else 0):>+6.0f} {len(d10):>4} {statistics.mean(min(max(r['sf_strong'], -2000), 2000) for r in xs):>+6.0f}")
        lines.append(f"   depth-6 root on the draws: <100 {sum(r['v21_d6'] < 100 for r in draws)}, 100-200 {sum(100 <= r['v21_d6'] < 200 for r in draws)}, 200-300 {sum(200 <= r['v21_d6'] < 300 for r in draws)}, >=300 {sum(r['v21_d6'] >= 300 for r in draws)}; on the wins: <100 {sum(r['v21_d6'] < 100 for r in wins)}, >=300 {sum(r['v21_d6'] >= 300 for r in wins)}; on the losses: > -100 {sum(r['v21_d6'] > -100 for r in losses)} of {len(losses)}")
        lines.append("   scaler screen (nominal surplus x f, applied to static and as the same shift to the root):")
        lines.append(f"      {'f':<7} {'draw static':>11} {'draw d6':>8} {'FW removed':>10} {'wins<100':>8} {'wins<200':>8} {'strategic<100':>13} {'tactical<100':>12} {'losses>-100':>11}")
        table = {}
        for name, f in (("off", 1.0), ("1/2", 0.5), ("1/4", 0.25), ("1/8", 0.125)):
            def adj(r, key, f=f):
                return r[key] - (1 - f) * r["surplus_tapered"]
            tact = [r for r in wins if r["tactical"]]
            row = {"draw_static": statistics.mean(adj(r, "v21_static") for r in draws) if draws else 0, "draw_d6": statistics.mean(adj(r, "v21_d6") for r in draws) if draws else 0,
                   "fw_removed": sum(adj(r, "v21_d6") < 150 for r in fw), "wins_lt100": sum(adj(r, "v21_d6") < 100 for r in wins), "wins_lt200": sum(adj(r, "v21_d6") < 200 for r in wins),
                   "strategic_lt100": sum(adj(r, "v21_d6") < 100 for r in strategic), "tactical_lt100": sum(adj(r, "v21_d6") < 100 for r in tact), "losses_gt_m100": sum(adj(r, "v21_d6") > -100 for r in losses)}
            table[name] = row
            lines.append(f"      {name:<7} {row['draw_static']:>+11.0f} {row['draw_d6']:>+8.0f} {row['fw_removed']:>5}/{len(fw):<4} {row['wins_lt100']:>4}/{len(wins):<3} {row['wins_lt200']:>4}/{len(wins):<3} {row['strategic_lt100']:>7}/{len(strategic):<5} {row['tactical_lt100']:>6}/{len(tact):<5} {row['losses_gt_m100']:>5}/{len(losses)}")
        summary[fam] = {"n": len(rs), "wins": len(wins), "draws": len(draws), "losses": len(losses), "false_wins": len(fw), "strategic_wins": len(strategic),
                        "material_on_draws": statistics.mean(r["decomposition_strong"]["material"] for r in draws) if draws else None,
                        "static_on_draws": statistics.mean(r["v21_static"] for r in draws) if draws else None, "table": table,
                        "reach_games": len(reach[fam]["games"]), "reach_moves": reach[fam]["moves"], "reach_false_win_traj": len(reach[fam]["false_win_traj"])}
        gp = [r for r in rs if r["source"] == "game"]
        if gp:
            lines.append("   retained game positions (strong side's view):")
            for r in gp:
                lines.append(f"      {r['trajectory']:<26} ply {r['ply']:>3} {r['label']:<5} SF {r['sf_strong']:>+5} static {r['v21_static']:>+4} d6 {r['v21_d6']:>+4} d10 {r.get('v21_d10', '-')}  tactical {r['tactical']}  result {r['game_result_for_strong']}  fw-corpus {r['in_false_win_corpus']}  {r['fen']}")
        lines.append("")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    arguments.out.with_suffix(".json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
