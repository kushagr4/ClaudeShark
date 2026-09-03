"""Build the V2 endgame calibration set from retained evidence, both directions of failure.

Every position comes from a retained, annotated fixed-depth self-play game
in which the production engine (rated V1) was to move, or from the blind-win
episode file built from those games, or -- for the controls -- from the
labelled competition-like suite and the tactics fixtures. Classes:

    blind_win        Stockfish >= +300, V1 root < +100           (underestimates a real win)
    false_win        V1 root >= +200, Stockfish within +-50       (overestimates a drawn position)
    recognised_win   both >= +300
    recognised_draw  both within +-50, endgame
    losing           Stockfish <= -300 (V1 root recorded either way)
    control_middle   level middlegame positions from the competition-like suite
    control_tactic   the tactics fixtures, mates and material wins

Scores are from the side to move. Exact FENs are deduplicated. A trajectory
is one game (source file, cluster, colour assignment); at most ``--per-game``
positions per class per trajectory are kept, at least six plies apart, the
ones with the largest disagreement first, so no game dominates. The split
is by cluster parity within a source, which keeps both games of a pair --
same starting position -- on the same side.

Every kept position is relabelled by the oracle at a fixed node budget (the
game annotations mix budgets) and re-scored by rated V1: static, root
quiescence and the depth-6 root, from a fresh searcher each time.

    uv run python -m tools.v2.calibration --out corpus/v2/endgame_calibration_v1.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import chess

from cs_passed import passed_pawn_mask
from tools.corpus.oracle import Oracle
from tools.corpus.structure import analyse_structure
from tools.postmortem.play import Engine
from tools.tactics import SUITE as TACTICS

GAME_FILES = {
    "postmortem": Path("corpus/postmortem/games/annotated.jsonl"),
    "mopup": Path("corpus/mopup/games/gate2_annotated.jsonl"),
    "passed": Path("corpus/passed/games/gate2_annotated.jsonl"),
}
BLIND_EPISODES = Path("corpus/blindwin/03_gap.jsonl")
COMPETITION = Path("corpus/passed/analysis_cl_v1_d6_baseline.jsonl")

CLASSES = ("blind_win", "false_win", "recognised_win", "recognised_draw", "losing", "control_middle", "control_tactic")


def stm(value: int | None, white_to_move: bool) -> int | None:
    if value is None:
        return None
    return value if white_to_move else -value


def classify(root: int, sf: int, phase24: int) -> str | None:
    if sf >= 300 and root < 100:
        return "blind_win"
    if root >= 200 and abs(sf) <= 50:
        return "false_win"
    if sf >= 300 and root >= 300:
        return "recognised_win"
    if abs(sf) <= 50 and abs(root) < 50 and phase24 <= 8:
        return "recognised_draw"
    if sf <= -300:
        return "losing"
    return None


def signature(board: chess.Board) -> str:
    order = "KQRBNP"
    out = []
    for colour in (chess.WHITE, chess.BLACK):
        s = ""
        for letter, pt in zip(order, (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN), strict=True):
            s += letter * len(board.pieces(pt, colour))
        out.append(s)
    return "-".join(out)


def cheb(a: int, b: int) -> int:
    return max(abs(chess.square_file(a) - chess.square_file(b)), abs(chess.square_rank(a) - chess.square_rank(b)))


def features(board: chess.Board) -> dict:
    us = board.turn
    them = not us
    st = analyse_structure(board)
    ours = passed_pawn_mask(board, us)
    theirs = passed_pawn_mask(board, them)
    our_king = board.king(us)
    their_king = board.king(them)
    pawns = list(chess.scan_forward(board.pawns))
    non_pawn = {c: (board.occupied_co[c] & ~board.pawns & ~board.kings).bit_count() for c in (us, them)}
    rooks_only = (board.queens | board.bishops | board.knights) == 0 and board.rooks != 0

    def rel(sq: int, colour: bool) -> int:
        return chess.square_rank(sq) if colour else 7 - chess.square_rank(sq)

    return {
        "phase": st.phase, "phase24": st.phase24, "tags": list(st.tags), "signature": signature(board),
        "material_stm": (st.material_white - st.material_black) * (1 if us else -1),
        "our_passers": ours.bit_count(), "their_passers": theirs.bit_count(),
        "our_best_passer_rank": max((rel(s, us) for s in chess.scan_forward(ours)), default=-1),
        "their_best_passer_rank": max((rel(s, them) for s in chess.scan_forward(theirs)), default=-1),
        "pawn_ending": non_pawn[us] == 0 and non_pawn[them] == 0 and board.pawns != 0,
        "rook_ending": rooks_only,
        "our_pieces": non_pawn[us], "their_pieces": non_pawn[them],
        "our_king_to_nearest_pawn": min((cheb(our_king, p) for p in pawns), default=-1) if our_king is not None else -1,
        "their_king_to_nearest_pawn": min((cheb(their_king, p) for p in pawns), default=-1) if their_king is not None else -1,
        "our_king_centre": (3.5 - abs(chess.square_file(our_king) - 3.5)) + (3.5 - abs(chess.square_rank(our_king) - 3.5)) if our_king is not None else 0,
        "their_king_centre": (3.5 - abs(chess.square_file(their_king) - 3.5)) + (3.5 - abs(chess.square_rank(their_king) - 3.5)) if their_king is not None else 0,
        "kings_distance": cheb(our_king, their_king) if our_king is not None and their_king is not None else -1,
    }


def harvest_games(per_game: int, min_gap: int) -> list[dict]:
    rows = []
    for source, path in GAME_FILES.items():
        for g in (json.loads(line) for line in path.open(encoding="utf-8")):
            traj = f"{source}:{g['cluster']}:{'cW' if g['cand_white'] else 'cB'}"
            picks: dict[str, list[dict]] = defaultdict(list)
            for m in g["moves"]:
                if m["mover"] != "base" or m.get("sf_cp_white_before") is None:
                    continue
                white = m["turn"] == "w"
                sf = stm(m["sf_cp_white_before"], white)
                root = m["score_stm"]
                board = chess.Board(m["fen"])
                st = analyse_structure(board)
                cls = classify(root, sf, st.phase24)
                if cls is None:
                    continue
                if cls in ("blind_win", "false_win", "recognised_win", "recognised_draw", "losing") and st.phase24 > 12:
                    continue  # the V2 target is the endgame and its approaches
                sf_after = stm(m.get("sf_cp_white_after"), white)
                if cls == "false_win" and sf_after is not None and abs(sf_after) > 80:
                    continue  # a false win must still be level after the move actually played
                picks[cls].append({
                    "fen": m["fen"], "source": source, "cluster": g["cluster"], "trajectory": traj, "ply": m["ply"],
                    "class": cls, "root_at_source": root, "static_at_source": stm(m["base_static"], white),
                    "sf_at_source": sf, "sf_after_played": sf_after, "played_at_source": m["move"],
                    "sf_best_at_source": m.get("sf_best"), "loss_at_source": m.get("cp_loss"),
                    "game_result_for_mover": g["cand_score"] if m["mover"] == "cand" else 1.0 - g["cand_score"],
                    "disagreement": abs(sf - root),
                })
            for cands in picks.values():
                kept: list[dict] = []
                for c in sorted(cands, key=lambda c: -c["disagreement"]):
                    if all(abs(c["ply"] - k["ply"]) >= min_gap for k in kept):
                        kept.append(c)
                    if len(kept) >= per_game:
                        break
                rows.extend(kept)
    return rows


def harvest_blind_episodes(per_game: int) -> list[dict]:
    rows = []
    by: dict[str, list[dict]] = defaultdict(list)
    for e in (json.loads(line) for line in BLIND_EPISODES.open(encoding="utf-8")):
        traj = f"blindwin:{e['cluster']}:{'cW' if e['cand_white'] else 'cB'}"
        by[traj].append({
            "fen": e["fen"], "source": "blindwin", "cluster": e["cluster"], "trajectory": traj, "ply": e["ply"],
            "class": "blind_win", "root_at_source": e["root"], "static_at_source": e["static"], "sf_at_source": e["sf_cp_1m"],
            "sf_after_played": None, "played_at_source": e["move"], "sf_best_at_source": e["sf_best"], "loss_at_source": e["cp_loss"],
            "game_result_for_mover": None, "disagreement": abs(min(e["sf_cp_1m"], 2000) - e["root"]),
            "pv_at_source": e["pv"], "mechanism_at_source": e["mechanism"],
        })
    for cands in by.values():
        rows.extend(sorted(cands, key=lambda c: -c["disagreement"])[:per_game])
    return rows


def harvest_controls(n_middle: int) -> list[dict]:
    rows = []
    comp = [json.loads(line) for line in COMPETITION.open(encoding="utf-8")][1:]
    level = [r for r in comp if r["structure"]["phase"] == "middlegame" and abs(r["reference_cp_stm"]) <= 60 and not r.get("mate_involved")]
    for r in sorted(level, key=lambda r: r["id"])[:n_middle]:
        rows.append({"fen": r["fen"], "source": "competition_like", "cluster": r["id"], "trajectory": f"competition:{r['id']}", "ply": 0,
                     "class": "control_middle", "root_at_source": r["engine"]["score"], "static_at_source": r["engine"]["static_eval"],
                     "sf_at_source": r["reference_cp_stm"], "sf_after_played": None, "played_at_source": r["engine"]["move"],
                     "sf_best_at_source": r["reference_best"], "loss_at_source": r["cp_loss"], "game_result_for_mover": None,
                     "disagreement": abs(r["reference_cp_stm"] - r["engine"]["score"])})
    for p in TACTICS:
        rows.append({"fen": p.fen, "source": "tactics", "cluster": p.name, "trajectory": f"tactics:{p.name}", "ply": 0,
                     "class": "control_tactic", "root_at_source": None, "static_at_source": None, "sf_at_source": None,
                     "sf_after_played": None, "played_at_source": None, "sf_best_at_source": (p.best[0] if p.best else None), "loss_at_source": None,
                     "game_result_for_mover": None, "disagreement": 0, "tactic_kind": p.kind})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-game", type=int, default=2)
    parser.add_argument("--min-gap", type=int, default=6)
    parser.add_argument("--middle-controls", type=int, default=24)
    parser.add_argument("--cap", type=int, default=100)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--engine", type=Path, default=Path("champions/v0_5_2_correctness"))
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    raw = harvest_games(arguments.per_game, arguments.min_gap) + harvest_blind_episodes(arguments.per_game) + harvest_controls(arguments.middle_controls)
    seen: dict[str, dict] = {}
    for r in sorted(raw, key=lambda r: -r["disagreement"]):
        seen.setdefault(r["fen"], r)
    rows = list(seen.values())
    print(f"harvested {len(raw)} rows, {len(rows)} unique FENs", flush=True)
    # The failure classes are kept whole; the recognised and losing classes are
    # capped at one position per trajectory and then a deterministic sample,
    # so the set punishes both directions without the easy cases outnumbering
    # the hard ones four to one.
    capped = []
    for cls in CLASSES:
        rs = [r for r in rows if r["class"] == cls]
        if cls in ("recognised_win", "recognised_draw", "losing"):
            first: dict[str, dict] = {}
            for r in sorted(rs, key=lambda r: -r["disagreement"]):
                first.setdefault(r["trajectory"], r)
            rs = sorted(first.values(), key=lambda r: hashlib.sha256(r["fen"].encode()).hexdigest())[: arguments.cap]
        capped.extend(rs)
    rows = capped
    print(f"after class caps: {len(rows)} positions, {len({r['trajectory'] for r in rows})} trajectories", flush=True)

    engine = Engine(arguments.engine, arguments.depth)
    try:
        with Oracle() as oracle:
            for i, r in enumerate(rows, start=1):
                board = chess.Board(r["fen"])
                white = board.turn == chess.WHITE
                if board.is_game_over():
                    continue
                label = oracle.analyse(r["fen"], arguments.nodes)
                r.update({"sf_cp": label.cp_stm, "sf_mate": label.mate, "sf_wdl": label.wdl_stm, "sf_best": label.best,
                          "sf_pv": list(label.pv)[:12], "nodes": arguments.nodes})
                engine.ask("new")
                q = engine.ask(f"qs {r['fen']}")
                engine.ask("new")
                g = engine.ask(f"go {r['fen']}")
                r.update({"v1_static": stm(g["static"], white), "v1_qs": stm(q["qs"], white), "v1_root": g["score"],
                          "v1_move": g["move"], "v1_pv": g["pv"][:8], "v1_nodes": g["nodes"]})
                r.update(features(board))
                if i % 25 == 0:
                    print(f"  labelled {i}/{len(rows)}", flush=True)
    finally:
        engine.close()
    rows = [r for r in rows if "sf_cp" in r]
    # Re-check the class with the fresh labels; keep the source class as provenance.
    for r in rows:
        r["class_at_source"] = r["class"]
        if r["class"] not in ("control_middle", "control_tactic"):
            fresh = classify(r["v1_root"], r["sf_cp"], r["phase24"])
            r["class_fresh"] = fresh
        else:
            r["class_fresh"] = r["class"]
        key = f"{r['source']}:{r['cluster']}"
        r["role"] = "diagnostic" if int(hashlib.sha256(key.encode()).hexdigest(), 16) % 2 == 0 else "validation"
    rows.sort(key=lambda r: (CLASSES.index(r["class"]), r["source"], str(r["cluster"]), r["ply"]))
    for i, r in enumerate(rows):
        r["id"] = f"ec-{i:03d}"
    body = "\n".join(json.dumps(r) for r in rows)
    header = {"record": "header", "suite": "endgame_calibration", "version": "v1", "size": len(rows), "nodes": arguments.nodes,
              "engine": str(arguments.engine), "depth": arguments.depth,
              "classes": dict(Counter(r["class"] for r in rows)), "roles": dict(Counter(r["role"] for r in rows)),
              "trajectories": len({r["trajectory"] for r in rows}), "hash": hashlib.sha256(body.encode()).hexdigest()[:16]}
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    with arguments.out.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(header) + "\n" + body + "\n")
    print(json.dumps(header, indent=1))

    # Statistics.
    lines = [f"== V2 ENDGAME CALIBRATION SET v1: {len(rows)} unique FENs, {header['trajectories']} trajectories, hash {header['hash']} ==",
             f"oracle {arguments.nodes} nodes; V1 = {arguments.engine} (static, root quiescence, depth-{arguments.depth} root), all from the side to move", ""]
    lines.append(f"{'class':<16} {'rows':>4} {'traj':>4} {'diag':>4} {'valid':>5} {'SF':>6} {'V1 static':>9} {'V1 qs':>6} {'V1 root':>7} {'fresh class kept':>16} {'endgame':>7} {'pawn end':>8} {'rook end':>8} {'own passer':>10} {'their passer':>12}")
    for cls in CLASSES:
        rs = [r for r in rows if r["class"] == cls]
        if not rs:
            continue
        lines.append(f"{cls:<16} {len(rs):>4} {len({r['trajectory'] for r in rs}):>4} {sum(r['role'] == 'diagnostic' for r in rs):>4} {sum(r['role'] == 'validation' for r in rs):>5} "
                     f"{statistics.mean(min(max(r['sf_cp'], -2000), 2000) for r in rs):>+6.0f} {statistics.mean(r['v1_static'] for r in rs):>+9.0f} {statistics.mean(r['v1_qs'] for r in rs):>+6.0f} {statistics.mean(r['v1_root'] for r in rs):>+7.0f} "
                     f"{sum(r['class_fresh'] == cls for r in rs) / len(rs):>16.0%} {sum(r['phase'] == 'endgame' for r in rs) / len(rs):>7.0%} {sum(r['pawn_ending'] for r in rs) / len(rs):>8.0%} {sum(r['rook_ending'] for r in rs) / len(rs):>8.0%} "
                     f"{sum(r['our_passers'] > 0 for r in rs) / len(rs):>10.0%} {sum(r['their_passers'] > 0 for r in rs) / len(rs):>12.0%}")
    lines.append("")
    lines.append("material signature, top 8 per failure class:")
    for cls in ("blind_win", "false_win"):
        rs = [r for r in rows if r["class"] == cls]
        lines.append(f"  {cls}: {Counter(r['signature'] for r in rs).most_common(8)}")
    lines.append("")
    lines.append("king activity (Chebyshev distance of each king to its nearest pawn; centralisation 0..7), by class:")
    for cls in CLASSES:
        rs = [r for r in rows if r["class"] == cls and r["our_king_to_nearest_pawn"] >= 0]
        if rs:
            lines.append(f"  {cls:<16} our king->pawn {statistics.mean(r['our_king_to_nearest_pawn'] for r in rs):.2f}  their king->pawn {statistics.mean(r['their_king_to_nearest_pawn'] for r in rs):.2f}  "
                         f"our centre {statistics.mean(r['our_king_centre'] for r in rs):.2f}  their centre {statistics.mean(r['their_king_centre'] for r in rs):.2f}  material(stm) {statistics.mean(r['material_stm'] for r in rs):+.2f}")
    lines.append("")
    lines.append("structure tags, failure classes (share of rows):")
    for cls in ("blind_win", "false_win"):
        rs = [r for r in rows if r["class"] == cls]
        tc = Counter(t for r in rs for t in r["tags"])
        lines.append(f"  {cls}: " + ", ".join(f"{t} {c / len(rs):.0%}" for t, c in tc.most_common(12)))
    text = "\n".join(lines)
    arguments.out.with_suffix(".txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
