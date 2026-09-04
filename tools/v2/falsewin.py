"""Build the V2.2 false-win corpus: positions V2.1 calls won that Stockfish calls level.

Sources: the V2 calibration set (its false-win class, which is rated V1's
false wins, plus any row where V2.1's depth-6 root is >= +150 with
Stockfish within +-60) and V2.1's own moves in the two retained Gate 2
matches (root >= +150, Stockfish within +-60 before and within +-80 after
the move actually played). Exact FENs are deduplicated; a trajectory is one
game; at most two rows per trajectory, six plies apart, highest V2.1 root
first. Every kept row is relabelled by the oracle at one budget and scored
by rated V1 and by V2.1 (static, root quiescence, depth-6 root, move), and
V2.1's static is decomposed into material, tables, pair and the king-pawn
term.

    uv run python -m tools.v2.falsewin --out corpus/v2/fw/falsewin_corpus_v1.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import chess

from cs_kingpawn import king_pawn_packed
from tools.corpus.oracle import Oracle
from tools.corpus.structure import analyse_structure
from tools.postmortem.play import Engine
from tools.v2.calibration import signature
from tools.v2.decompose import decompose

CALIBRATION_RUNS = ("corpus/v2/kp/04_validation_candidate.jsonl", "corpus/v2/kp/sweep_MEDIUM_calibration.jsonl")
GAMES = {"gate2_v1": "corpus/v2/kp/games/gate2_annotated.jsonl", "gate2_passed": "corpus/v2/kp/games/secondary_vs_passed_annotated.jsonl"}


def stm(v: int | None, white: bool) -> int | None:
    return None if v is None else (v if white else -v)


def read_jsonl(path: str) -> list[dict]:
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def harvest(root_min: int, sf_band: int) -> list[dict]:
    rows: list[dict] = []
    for path in CALIBRATION_RUNS:
        for r in read_jsonl(path):
            v1_false = r["class"] == "false_win"
            v21_false = r["root"] >= root_min and abs(r["sf_cp"]) <= sf_band
            if not (v1_false or v21_false):
                continue
            rows.append({"fen": r["fen"], "source": "calibration:" + r["source"], "trajectory": r["trajectory"], "ply": r["ply"],
                         "origin_class": r["class"], "v1_false_win": v1_false, "v21_false_win": v21_false,
                         "game_result_for_mover": r.get("game_result_for_mover"), "select_root": r["root"]})
    for source, path in GAMES.items():
        for g in read_jsonl(path):
            traj = f"{source}:{g['cluster']}:{'cW' if g['cand_white'] else 'cB'}"
            for m in g["moves"]:
                if m["mover"] != "cand" or m.get("sf_cp_white_before") is None:
                    continue
                white = m["turn"] == "w"
                sf = stm(m["sf_cp_white_before"], white)
                sf_after = stm(m.get("sf_cp_white_after"), white)
                if m["score_stm"] >= root_min and abs(sf) <= sf_band and (sf_after is None or abs(sf_after) <= 80):
                    rows.append({"fen": m["fen"], "source": source, "trajectory": traj, "ply": m["ply"], "origin_class": "v2.1 play",
                                 "v1_false_win": False, "v21_false_win": True, "game_result_for_mover": g["cand_score"],
                                 "select_root": m["score_stm"]})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-min", type=int, default=150)
    parser.add_argument("--sf-band", type=int, default=60)
    parser.add_argument("--per-trajectory", type=int, default=2)
    parser.add_argument("--min-gap", type=int, default=6)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    raw = harvest(arguments.root_min, arguments.sf_band)
    seen: dict[str, dict] = {}
    for r in sorted(raw, key=lambda r: -r["select_root"]):
        if r["fen"] in seen:
            seen[r["fen"]]["v1_false_win"] |= r["v1_false_win"]
            seen[r["fen"]]["v21_false_win"] |= r["v21_false_win"]
        else:
            seen[r["fen"]] = dict(r)
    by_traj: dict[str, list[dict]] = defaultdict(list)
    for r in seen.values():
        by_traj[r["trajectory"]].append(r)
    rows = []
    for cands in by_traj.values():
        kept: list[dict] = []
        for c in sorted(cands, key=lambda c: -c["select_root"]):
            if all(abs(c["ply"] - k["ply"]) >= arguments.min_gap for k in kept):
                kept.append(c)
            if len(kept) >= arguments.per_trajectory:
                break
        rows.extend(kept)
    print(f"harvested {len(raw)} rows, {len(seen)} unique FENs, {len(rows)} kept over {len(by_traj)} trajectories", flush=True)

    v1 = Engine(Path("champions/rated_v1"), arguments.depth)
    v21 = Engine(Path("champions/v2_1_kingpawn"), arguments.depth)
    try:
        with Oracle() as oracle:
            for i, r in enumerate(rows, start=1):
                board = chess.Board(r["fen"])
                white = board.turn == chess.WHITE
                label = oracle.analyse(r["fen"], arguments.nodes)
                r.update({"sf_cp": label.cp_stm, "sf_mate": label.mate, "sf_wdl": label.wdl_stm, "sf_best": label.best,
                          "sf_pv": list(label.pv)[:12], "nodes": arguments.nodes})
                for name, e in (("v1", v1), ("v21", v21)):
                    e.ask("new")
                    q = e.ask(f"qs {r['fen']}")
                    e.ask("new")
                    g = e.ask(f"go {r['fen']}")
                    r.update({f"{name}_static": stm(g["static"], white), f"{name}_qs": stm(q["qs"], white), f"{name}_root": g["score"],
                              f"{name}_move": g["move"], f"{name}_pv": g["pv"][:8]})
                st = analyse_structure(board)
                d = decompose(board)
                r.update({"side": "white" if white else "black", "signature": signature(board), "phase": st.phase, "phase24": st.phase24,
                          "tags": list(st.tags), "pawns_remain": bool(board.pawns), "king_pawn_active": king_pawn_packed(board) != 0,
                          "material_stm": (st.material_white - st.material_black) * (1 if white else -1),
                          "decomposition_stm": {k: (v if white else -v) for k, v in d.items() if k in ("material", "pst", "pair", "king_pawn", "white_view_before_tempo")},
                          "v21_static_check": d["stm_score"]})
                if i % 20 == 0:
                    print(f"  scored {i}/{len(rows)}", flush=True)
    finally:
        v1.close()
        v21.close()
    rows.sort(key=lambda r: (r["trajectory"], r["ply"]))
    for i, r in enumerate(rows):
        r["id"] = f"fw-{i:03d}"
    body = "\n".join(json.dumps(r) for r in rows)
    header = {"record": "header", "suite": "falsewin_corpus", "version": "v1", "size": len(rows), "trajectories": len(by_traj),
              "selection": f"V2.1 root >= {arguments.root_min} with |SF| <= {arguments.sf_band}, plus rated V1 false wins; <= {arguments.per_trajectory} per trajectory",
              "sources": dict(Counter(r["source"] for r in rows)), "hash": hashlib.sha256(body.encode()).hexdigest()[:16]}
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(header) + "\n" + body + "\n", encoding="utf-8")
    print(json.dumps(header, indent=1))


if __name__ == "__main__":
    main()
