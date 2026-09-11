"""Deeper-RC-J repair test on first-decisive-error positions.

Exact RC-J (shipped cs_core via the verified trace driver) from a COLD searcher:
  1. the production time path at the game's recorded input clock, which gives the
     reconstructed completed depth d and whether the cold search even reproduces
     the live move (C27 showed live moves can depend on accumulated TT state);
  2. fixed completed depths d, d+1, ..., d+extra, each from new_game(), so no
     depth inherits a table from another.
The ladder stops early once a single depth takes longer than --max-seconds.
Moves are judged afterwards against the isolated Stockfish reference; this script
only records what RC-J does. Labelled COLD_FROM_FEN.
"""
import argparse, json, os, sys, time
C27 = "C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/6aa4cc83-13ea-4a98-8c08-bba93a80f5d1/scratchpad/c27"
sys.path.insert(0, C27)
import chess
import cs_fast_trace as engine

ap = argparse.ArgumentParser()
ap.add_argument("--positions", required=True)
ap.add_argument("--extra", type=int, default=3)
ap.add_argument("--max-seconds", type=float, default=75.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()
P = json.load(open(a.positions, encoding="utf-8"))
engine.warm_up(); s = engine.Searcher(); out = []; t0 = time.perf_counter()
for p in P:
    clk = p.get("clock_in_ms") or 120_000
    s.new_game(); t = time.perf_counter()
    _, i = s.search(chess.Board(p["fen"]), int(clk))
    timed = dict(move=i.completed_move, depth=i.completed_depth, score=i.score, nodes=i.nodes,
                 stop=i.stop_reason, seconds=round(time.perf_counter() - t, 2), clock_in_ms=clk,
                 clock_assumed=p.get("clock_in_ms") is None)
    rec = dict(id=p["id"], fen=p["fen"], played=p["played"], reference=p.get("reference"),
               timed=timed, reproduces_live=timed["move"] == p["played"], ladder=[])
    print(f"{p['id']:10s} timed@{clk/1000:6.1f}s d={timed['depth']:2d} {timed['move']} "
          f"{'== live' if rec['reproduces_live'] else '!= live ' + p['played']}  ({timed['seconds']}s)", flush=True)
    for d in range(timed["depth"], timed["depth"] + a.extra + 1):
        s.new_game(); t = time.perf_counter()
        _, j = s.search(chess.Board(p["fen"]), 0, max_depth=d)
        sec = time.perf_counter() - t
        rec["ladder"].append(dict(depth=d, move=j.completed_move, score=j.score, nodes=j.nodes, seconds=round(sec, 2)))
        print(f"    d{d:2d} {j.completed_move:6s} {j.score:+6d} {j.nodes:>11,} {sec:6.1f}s", flush=True)
        if sec > a.max_seconds: break
    # RC-J's OWN value of the played move and the reference move, each by pushing it and
    # searching the child from new_game() at the reconstructed depth (C26 phase 2 method).
    def value(uci, depth):
        b = chess.Board(p["fen"]); mv = chess.Move.from_uci(uci)
        if mv not in b.legal_moves: return None
        b.push(mv)
        if b.is_game_over(claim_draw=True):
            r = b.result(claim_draw=True); return 0 if r == "1/2-1/2" else 30000
        s.new_game(); _, k = s.search(b, 0, max_depth=max(1, depth - 1)); return -k.score
    if p.get("reference") and p["reference"] != p["played"]:
        dd = timed["depth"]
        rec["rcj_values"] = dict(depth=dd, played=value(p["played"], dd), reference=value(p["reference"], dd))
        print(f"    RC-J own values @d{dd}: played {rec['rcj_values']['played']} reference {rec['rcj_values']['reference']}", flush=True)
    out.append(rec)
    json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1)
print(f"done {len(out)} positions in {time.perf_counter() - t0:.0f}s", flush=True)
