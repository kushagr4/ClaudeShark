"""Isolated Stockfish scan of every RC-J move in the R76+ Chessathon games.

For each RC-J move the position BEFORE the move is analysed twice from the SAME
root, so the two scores are directly comparable:
  best   = unrestricted search
  played = search restricted to the played move (root_moves=[move])
If the played move IS the engine's best move the loss is 0 by definition; two
separate noisy searches of one move are never subtracted (no phantom losses).

Defects avoided, each learned in an earlier lane:
  * persistent-hash contamination -> a fresh `game` tag per analysis (ucinewgame)
  * root/successor subtraction    -> both scores are root scores, same side to move
  * bounds read as exact          -> the per-line info stream is read; the last
                                     EXACT line is used, and a bound-only result
                                     is flagged, never silently trusted
  * delivered-mate sign mistakes  -> scores are taken as .pov(side to move) at the
                                     root; a mating move scores +mate for RC-J
Scores are from RC-J's point of view. cp is capped at +-1500 for the loss
arithmetic; mate is reported separately.
"""
import argparse, hashlib, json, os, re, sys, time
import chess, chess.pgn, chess.engine

PUBLIC = "C:/Users/epick/Documents/ClaudeShark/scratch/gameplay_research_20260910/public"
SF = "C:/Users/epick/engines/stockfish/stockfish-windows-x86-64-avx2.exe"
CLK = re.compile(r"\[%clk\s+(\d+):(\d+):([\d.]+)\]")
CAP = 1500

def outcome(res, side):
    if res == "1/2-1/2": return "D"
    if res not in ("1-0", "0-1"): return "?"
    return "W" if (res == "1-0") == (side == chess.WHITE) else "L"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", default=PUBLIC)
    ap.add_argument("--min-round", type=int, default=76)
    ap.add_argument("--results", default="L")
    ap.add_argument("--nodes", type=int, default=2_000_000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sha = hashlib.sha256(open(SF, "rb").read()).hexdigest()
    eng = chess.engine.SimpleEngine.popen_uci(SF)
    eng.configure({"Threads": 1, "Hash": 64, "UCI_ShowWDL": True})
    counter = [0]

    def run(board, root_moves=None):
        counter[0] += 1
        last = exact = None
        with eng.analysis(board, chess.engine.Limit(nodes=a.nodes), root_moves=root_moves,
                          game=("autopsy", counter[0])) as an:
            for info in an:
                if "score" not in info or "pv" not in info or info.get("multipv", 1) != 1:
                    continue
                b = "lower" if info.get("lowerbound") else "upper" if info.get("upperbound") else "exact"
                rec = dict(score=info["score"], bound=b, wdl=info.get("wdl"),
                           move=info["pv"][0], depth=info.get("depth"), pv=[m.uci() for m in info["pv"][:8]])
                last = rec
                if b == "exact": exact = rec
        r = exact or last
        s = r["score"].pov(board.turn)
        e = r["wdl"].pov(board.turn).expectation() if r["wdl"] else None
        return dict(cp=max(-CAP, min(CAP, s.score(mate_score=100000))), mate=s.mate(),
                    E=e, bound=r["bound"], depth=r["depth"], move=r["move"].uci(), pv=r["pv"])

    cat = lambda E: None if E is None else ("win" if E >= 0.75 else "loss" if E <= 0.25 else "draw")
    rank = {"loss": 0, "draw": 1, "win": 2}
    out = open(a.out, "w", encoding="utf-8")
    t0 = time.perf_counter()
    for f in sorted(os.listdir(a.public)):
        if not f.endswith(".pgn"): continue
        g = chess.pgn.read_game(open(os.path.join(a.public, f), encoding="utf-8", errors="replace"))
        h = g.headers; rnd = int(h["Round"])
        side = (chess.WHITE if h["White"].lower() == "claudeshark"
                else chess.BLACK if h["Black"].lower() == "claudeshark" else None)
        if rnd < a.min_round or side is None: continue
        res = outcome(h["Result"], side)
        if res not in a.results: continue
        board = g.board(); prev_clk = None; n = 0; gt = time.perf_counter()
        for node in g.mainline():
            mv = node.move
            m = CLK.search(node.comment or "")
            clk_after = (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))) if m else None
            if board.turn == side:
                fen = board.fen(); best = run(board)
                if best["move"] == mv.uci():
                    pl = dict(best); same = True
                else:
                    pl = run(board, root_moves=[mv]); same = False
                loss = best["cp"] - pl["cp"]
                rec = dict(round=rnd, game=f[:-4], side="white" if side else "black", result=res,
                           move_number=board.fullmove_number, fen=fen, played=mv.uci(),
                           san=board.san(mv), best=best["move"], same_move=same,
                           best_cp=best["cp"], best_mate=best["mate"], best_E=best["E"], best_bound=best["bound"],
                           played_cp=pl["cp"], played_mate=pl["mate"], played_E=pl["E"], played_bound=pl["bound"],
                           loss_cp=max(0, loss), raw_loss_cp=loss, noise_negative=loss < 0,
                           dE=(best["E"] - pl["E"]) if best["E"] is not None and pl["E"] is not None else None,
                           cat_best=cat(best["E"]), cat_played=cat(pl["E"]),
                           flip=(cat(best["E"]) is not None and cat(pl["E"]) is not None
                                 and rank[cat(pl["E"])] < rank[cat(best["E"])]),
                           clock_in_s=prev_clk, clock_after_s=clk_after,
                           best_pv=best["pv"], played_pv=pl["pv"], sf_depth=best["depth"])
                out.write(json.dumps(rec) + "\n"); out.flush(); n += 1
                if clk_after is not None: prev_clk = clk_after
            board.push(mv)
        print(f"R{rnd} {res} {h['White']} - {h['Black']}: {n} RC-J moves in {time.perf_counter()-gt:.0f}s "
              f"(total {time.perf_counter()-t0:.0f}s)", flush=True)
    eng.quit(); out.close()
    print(f"done. stockfish sha256 {sha[:16]} nodes {a.nodes} analyses {counter[0]}", flush=True)

main()
