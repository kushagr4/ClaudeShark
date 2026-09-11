"""Re-verify each decisive position at a much larger Stockfish budget.

Same isolation rules as sf_scan.py (fresh game tag per analysis, root-restricted
played-move search from the same root, last EXACT info line, RC-J's point of view).
Also scores any extra moves requested per position (RC-J's deeper-search choices),
so a 'repair' is judged by the same reference that labelled the error.
Input: a JSON list of {id, fen, played, best, extra:[uci,...]}.
"""
import argparse, json, sys, time
import chess, chess.engine
SF = "C:/Users/epick/engines/stockfish/stockfish-windows-x86-64-avx2.exe"
CAP = 1500
ap = argparse.ArgumentParser(); ap.add_argument("--positions", required=True)
ap.add_argument("--nodes", type=int, default=20_000_000); ap.add_argument("--out", required=True)
a = ap.parse_args()
eng = chess.engine.SimpleEngine.popen_uci(SF); eng.configure({"Threads": 1, "Hash": 256, "UCI_ShowWDL": True})
n = [0]
def run(board, root_moves=None):
    n[0] += 1; last = exact = None
    with eng.analysis(board, chess.engine.Limit(nodes=a.nodes), root_moves=root_moves, game=("verify", n[0])) as an:
        for info in an:
            if "score" not in info or "pv" not in info or info.get("multipv", 1) != 1: continue
            b = "lower" if info.get("lowerbound") else "upper" if info.get("upperbound") else "exact"
            rec = dict(score=info["score"], bound=b, wdl=info.get("wdl"), move=info["pv"][0].uci(), depth=info.get("depth"))
            last = rec
            if b == "exact": exact = rec
    r = exact or last; s = r["score"].pov(board.turn)
    return dict(cp=max(-CAP, min(CAP, s.score(mate_score=100000))), mate=s.mate(),
                E=r["wdl"].pov(board.turn).expectation() if r["wdl"] else None, bound=r["bound"], depth=r["depth"], move=r["move"])
out = []; t0 = time.perf_counter()
for p in json.load(open(a.positions, encoding="utf-8")):
    b = chess.Board(p["fen"]); best = run(b); rec = dict(id=p["id"], fen=p["fen"], best=best, moves={})
    for u in dict.fromkeys([p["played"], p["best"]] + p.get("extra", [])):
        mv = chess.Move.from_uci(u)
        if mv not in b.legal_moves: rec["moves"][u] = None; continue
        rec["moves"][u] = dict(best) if u == best["move"] else run(b, root_moves=[mv])
        rec["moves"][u]["loss_cp"] = max(0, best["cp"] - rec["moves"][u]["cp"])
    out.append(rec); json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1)
    pl = rec["moves"].get(p["played"]) or {}
    print(f"{p['id']:9s} SF@{a.nodes/1e6:.0f}M best {best['move']} {best['cp']:+d} E{best['E']:.2f} d{best['depth']} | played {p['played']} "
          f"{pl.get('cp', 0):+d} E{(pl.get('E') or 0):.2f} loss {pl.get('loss_cp')} {pl.get('bound')}  "
          f"extra {{{', '.join(f'{u}:{v and v['loss_cp']}' for u, v in rec['moves'].items() if u not in (p['played'],))}}}  {time.perf_counter()-t0:.0f}s", flush=True)
eng.quit()
