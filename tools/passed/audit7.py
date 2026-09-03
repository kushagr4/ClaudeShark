"""Why the rank-only passer term reached seventh-rank passers more often and did worse there.

Every Gate 2 game is scanned for episodes in which the side to move owns a
passed pawn on its seventh rank (relative rank index 6). An episode is one
pawn in one game for one side, from the first ply it stands on the seventh
until it promotes, is captured, or the game ends; episodes are deduplicated
by the position at entry, so the two games of a pair that reach the same
structure count once. At entry, the position is read for the things a rank
bonus cannot see -- what stands on the promotion square, who controls it,
whether the pawn can simply be taken, where the kings are, whether the
opponent has a passer of its own -- and Stockfish's score says whether the
passer was actually worth anything. The move that put the pawn there is
scored too, because a pawn pushed to the seventh at a Stockfish loss is a
pawn pushed for the bonus.

    uv run python -m tools.passed.audit7 --games corpus/passed/games/gate2_annotated.jsonl --out corpus/passed/14_seventh_rank_audit.txt
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

import chess

from cs_passed import passed_pawn_mask

MECHANISMS = ("pawn immediately capturable", "blocked by enemy king", "piece blockade",
              "promotion square controlled", "enemy rook/queen behind or beside", "losing mutual pawn race",
              "wrong rook pawn / corner draw", "defending king close enough", "supporting king too far away",
              "advancement abandons another obligation", "search/horizon", "other")


def cheb(a: int, b: int) -> int:
    return max(abs(chess.square_file(a) - chess.square_file(b)), abs(chess.square_rank(a) - chess.square_rank(b)))


def mover_cp(m: dict, key: str = "sf_cp_white_before") -> int | None:
    v = m.get(key)
    if v is None:
        return None
    return v if m["turn"] == "w" else -v


def geometry(board: chess.Board, pawn: int, us: bool) -> dict:
    them = not us
    promo = chess.square(chess.square_file(pawn), 7 if us else 0)
    our_king = board.king(us)
    their_king = board.king(them)
    assert our_king is not None and their_king is not None
    on_promo = board.piece_at(promo)
    enemy_attackers = board.attackers(them, pawn)
    our_defenders = board.attackers(us, pawn)
    heavy = board.pieces(chess.ROOK, them) | board.pieces(chess.QUEEN, them)
    file_bb = chess.BB_FILES[chess.square_file(pawn)]
    rank_bb = chess.BB_RANKS[chess.square_rank(pawn)]
    their_passers = passed_pawn_mask(board, them)
    their_best = max((chess.square_rank(s) if them else 7 - chess.square_rank(s)) for s in chess.scan_forward(their_passers)) if their_passers else -1
    our_pieces = (board.occupied_co[us] & ~board.pawns & ~board.kings).bit_count()
    their_pieces = (board.occupied_co[them] & ~board.pawns & ~board.kings).bit_count()
    rook_pawn = chess.square_file(pawn) in (0, 7)
    our_bishops = board.pieces(chess.BISHOP, us)
    wrong_bishop = bool(our_bishops) and not (our_bishops & (chess.BB_LIGHT_SQUARES if promo in chess.SquareSet(chess.BB_LIGHT_SQUARES) else chess.BB_DARK_SQUARES))
    return {
        "promo": chess.square_name(promo),
        "blocked_by_king": on_promo is not None and on_promo.piece_type == chess.KING and on_promo.color == them,
        "piece_blockade": on_promo is not None and on_promo.color == them and on_promo.piece_type != chess.KING,
        "own_piece_on_promo": on_promo is not None and on_promo.color == us,
        "promo_attackers_them": len(board.attackers(them, promo)),
        "promo_attackers_us": len(board.attackers(us, promo)),
        "capturable": len(enemy_attackers) > 0 and len(our_defenders) == 0,
        "attacked": len(enemy_attackers) > 0,
        "defended": len(our_defenders) > 0,
        "heavy_behind_or_beside": bool(heavy & (file_bb | rank_bb)),
        "their_best_passer_rank": their_best,
        "our_king_to_pawn": cheb(our_king, pawn),
        "their_king_to_promo": cheb(their_king, promo),
        "their_king_to_pawn": cheb(their_king, pawn),
        "our_pieces": our_pieces,
        "their_pieces": their_pieces,
        "rook_pawn": rook_pawn,
        "corner_draw_shape": rook_pawn and (cheb(their_king, promo) <= 1) and (our_pieces == 0 or (our_pieces == 1 and wrong_bishop)),
        "pawn_ending": our_pieces == 0 and their_pieces == 0,
    }


def classify(ep: dict) -> str:
    g = ep["geometry"]
    if g["capturable"]:
        return "pawn immediately capturable"
    if g["blocked_by_king"]:
        return "blocked by enemy king"
    if g["piece_blockade"]:
        return "piece blockade"
    if g["promo_attackers_them"] > g["promo_attackers_us"]:
        return "promotion square controlled"
    if g["heavy_behind_or_beside"]:
        return "enemy rook/queen behind or beside"
    if g["corner_draw_shape"]:
        return "wrong rook pawn / corner draw"
    if g["their_best_passer_rank"] >= 5 and ep["sf_entry"] is not None and ep["sf_entry"] < 100:
        return "losing mutual pawn race"
    if g["their_king_to_promo"] <= 1:
        return "defending king close enough"
    if g["our_king_to_pawn"] >= 3 and g["our_pieces"] == 0:
        return "supporting king too far away"
    if ep["creating_loss"] is not None and ep["creating_loss"] >= 100:
        return "advancement abandons another obligation"
    if ep["first_move_loss"] is not None and ep["first_move_loss"] >= 100:
        return "search/horizon"
    return "other"


def episodes_of(game: dict) -> list[dict]:
    moves = game["moves"]
    out = []
    active: dict[tuple[str, int], dict] = {}
    for i, m in enumerate(moves):
        board = chess.Board(m["fen"])
        us = board.turn
        side = m["mover"]
        mask = passed_pawn_mask(board, us)
        seventh = [s for s in chess.scan_forward(mask) if (chess.square_rank(s) if us else 7 - chess.square_rank(s)) == 6]
        seen_now = set()
        for s in seventh:
            key = (side, s)
            seen_now.add(key)
            if key in active:
                active[key]["plies"] += 1
                continue
            prev = moves[i - 2] if i >= 2 and moves[i - 2]["mover"] == side else None
            creating = prev if prev and chess.Move.from_uci(prev["move"]).to_square == s else None
            ep = {
                "cluster": game["cluster"], "cand_white": game["cand_white"], "side": side, "pawn": chess.square_name(s),
                "entry_ply": m["ply"], "entry_fen": m["fen"], "sf_entry": mover_cp(m), "wdl_entry": m.get("sf_wdl_white_before"),
                "first_move": m["move"], "first_move_loss": m.get("cp_loss"), "sf_best_at_entry": m.get("sf_best"),
                "creating_move": creating["move"] if creating else None,
                "creating_loss": creating.get("cp_loss") if creating else None,
                "creating_sf_best": creating.get("sf_best") if creating else None,
                "creating_sf_before": mover_cp(creating) if creating else None,
                "creating_fen": creating["fen"] if creating else None,
                "geometry": geometry(board, s, us), "plies": 1, "fate": "stuck at the end",
                "result_for_mover": (game["cand_score"] if side == "cand" else 1.0 - game["cand_score"]),
                "termination": game["termination"], "game_plies": game["plies"],
            }
            active[key] = ep
            out.append(ep)
        # Fate of active pawns that are no longer on the seventh for this side.
        if side is not None:
            for key in [k for k in active if k[0] == side and k not in seen_now]:
                ep = active.pop(key)
                sq = chess.parse_square(ep["pawn"])
                piece = board.piece_at(sq)
                if piece is None or piece.color != us or piece.piece_type != chess.PAWN:
                    # Look back one ply of ours: did we promote from that square?
                    prev_own = moves[i - 2] if i >= 2 else None
                    if prev_own and prev_own["mover"] == side and prev_own["move"].startswith(ep["pawn"]) and len(prev_own["move"]) == 5:
                        ep["fate"] = "promoted"
                    else:
                        ep["fate"] = "captured"
                else:
                    ep["fate"] = "no longer passed"
                ep["exit_ply"] = m["ply"]
    return out


def table(title: str, eps: list[dict], lines: list[str]) -> None:
    lines.append(title)
    lines.append(f"  {'':<40} {'cand':>6} {'base':>6}")
    for mech in MECHANISMS:
        c = sum(1 for e in eps if e["side"] == "cand" and e["mechanism"] == mech)
        b = sum(1 for e in eps if e["side"] == "base" and e["mechanism"] == mech)
        if c or b:
            lines.append(f"  {mech:<40} {c:>6} {b:>6}")
    lines.append(f"  {'TOTAL':<40} {sum(1 for e in eps if e['side'] == 'cand'):>6} {sum(1 for e in eps if e['side'] == 'base'):>6}")
    lines.append("")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    raw = [e for g in games for e in episodes_of(g)]
    seen = set()
    eps = []
    for e in raw:
        key = (e["entry_fen"], e["pawn"])
        if key in seen:
            continue
        seen.add(key)
        e["mechanism"] = classify(e)
        eps.append(e)

    lines = [f"== SEVENTH-RANK PASSER AUDIT: {len(raw)} episodes in {len(games)} Gate 2 games, {len(eps)} after deduplication by entry position ==",
             "an episode = one pawn of the side to move standing on its seventh rank, from entry until it promotes, is captured or the game ends",
             "sf = Stockfish at entry from the mover's side (annotation budget); 'not winning' = sf < +100; 'won' = sf >= +300", ""]
    for side in ("cand", "base"):
        es = [e for e in eps if e["side"] == side]
        sf = [e["sf_entry"] for e in es if e["sf_entry"] is not None]
        lines.append(f"-- {side}: {len(es)} episodes, mean plies on the seventh {statistics.mean(e['plies'] for e in es):.1f}; "
                     f"sf at entry mean {statistics.mean(sf):+.0f}, not winning {sum(v < 100 for v in sf)}/{len(sf)}, won {sum(v >= 300 for v in sf)}/{len(sf)}; "
                     f"fate {dict(Counter(e['fate'] for e in es))}; game result for the mover {statistics.mean(e['result_for_mover'] for e in es):.1%}")
        cr = [e for e in es if e["creating_move"] is not None]
        cl = [e["creating_loss"] for e in cr if e["creating_loss"] is not None]
        non_pawn = sum(1 for e in cr if e["creating_sf_best"]
                       and chess.Board(e["creating_fen"]).piece_type_at(chess.Move.from_uci(e["creating_sf_best"]).from_square) != chess.PAWN)
        lines.append(f"   created by the mover's own push in {len(cr)}: creating-move loss mean {statistics.mean(cl) if cl else 0:.0f}, "
                     f">= 100 in {sum(v >= 100 for v in cl)}/{len(cl)}; Stockfish preferred a non-pawn move to the push in {non_pawn}/{len(cr)}")
    lines.append("")
    not_winning = [e for e in eps if e["sf_entry"] is not None and e["sf_entry"] < 100]
    winning = [e for e in eps if e["sf_entry"] is not None and e["sf_entry"] >= 300]
    table("== MECHANISM at entry, episodes where the passer was NOT winning (sf < +100) ==", not_winning, lines)
    table("== MECHANISM at entry, episodes where the passer WAS winning (sf >= +300), for contrast ==", winning, lines)
    table("== MECHANISM at entry, all episodes ==", eps, lines)

    lines.append("== FEATURE RATES at entry, cand vs base, not-winning episodes vs winning episodes ==")
    feats = ("capturable", "attacked", "defended", "blocked_by_king", "piece_blockade", "heavy_behind_or_beside",
             "corner_draw_shape", "pawn_ending", "rook_pawn")
    lines.append(f"  {'feature':<26} {'cand !win':>10} {'base !win':>10} {'cand win':>10} {'base win':>10}")

    def rate(es, f):
        return f"{sum(e['geometry'][f] for e in es) / len(es):.0%}" if es else "-"

    groups = {"cand !win": [e for e in not_winning if e["side"] == "cand"], "base !win": [e for e in not_winning if e["side"] == "base"],
              "cand win": [e for e in winning if e["side"] == "cand"], "base win": [e for e in winning if e["side"] == "base"]}
    for f in feats:
        lines.append(f"  {f:<26} " + " ".join(f"{rate(groups[k], f):>10}" for k in groups))
    for f, label in (("promo_attackers_them", "enemy attackers on promo sq (mean)"), ("their_king_to_promo", "their king to promo sq (mean)"),
                     ("our_king_to_pawn", "our king to pawn (mean)"), ("their_best_passer_rank", "their best passer rank (mean)"),
                     ("our_pieces", "our pieces (mean)"), ("their_pieces", "their pieces (mean)")):
        lines.append(f"  {label:<34} " + " ".join(f"{(statistics.mean(e['geometry'][f] for e in groups[k]) if groups[k] else 0):>10.2f}" for k in groups))
    lines.append(f"  {'n':<26} " + " ".join(f"{len(groups[k]):>10}" for k in groups))
    lines.append("")
    lines.append("== CONTROL of the promotion square, not-winning episodes: enemy attackers minus ours ==")
    for side in ("cand", "base"):
        es = [e for e in not_winning if e["side"] == side]
        lines.append(f"  {side}: {dict(sorted(Counter(e['geometry']['promo_attackers_them'] - e['geometry']['promo_attackers_us'] for e in es).items()))}")
    lines.append("")
    lines.append("== EPISODES, not winning at entry (hand-readable) ==")
    for e in sorted(not_winning, key=lambda e: (e["side"], e["sf_entry"])):
        g = e["geometry"]
        lines.append(f"  {e['side']} cl {e['cluster']:>3} ply {e['entry_ply']:>3} pawn {e['pawn']} sf {e['sf_entry']:>+5}  {e['mechanism']:<40} fate {e['fate']:<18} result {e['result_for_mover']:.1f}  "
                     f"created by {e['creating_move'] or '-':<6} loss {e['creating_loss'] if e['creating_loss'] is not None else '-':>4} (SF best {e['creating_sf_best'] or '-'})  "
                     f"promo {g['promo']} atk {g['promo_attackers_them']}/{g['promo_attackers_us']} Kthem->promo {g['their_king_to_promo']} Kus->pawn {g['our_king_to_pawn']} pieces {g['our_pieces']}/{g['their_pieces']}")
        lines.append(f"        {e['entry_fen']}")
    text = "\n".join(lines)
    arguments.out.write_text(text + "\n", encoding="utf-8")
    arguments.out.with_suffix(".jsonl").write_text("\n".join(json.dumps(e) for e in eps) + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
