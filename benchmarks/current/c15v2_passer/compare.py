"""Candidate against baseline on pre-registered position sets.

Every set is drawn from the Top-3 differential before the candidate was
written. Each position is searched by both builds at the same fixed depth and
the resulting move is scored by the same oracle, so the comparison is
deterministic and like for like.

usage: compare.py <serious_errors.json> <baseline_dir> <candidate_dir> <out.json> [depth] [workers]
"""
import sys, os, json
from concurrent.futures import ProcessPoolExecutor

SRC, BASE_DIR, CAND_DIR, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
DEPTH = int(sys.argv[5]) if len(sys.argv) > 5 else 12
WORKERS = int(sys.argv[6]) if len(sys.argv) > 6 else 6
SF = r"C:/Users/epick/engines/stockfish/stockfish-windows-x86-64-avx2.exe"
NODES = 1_000_000
MATE_CP = 30000
CAP_MS = 20_000


def to_cp(score, pov):
    s = score.pov(pov)
    if s.is_mate():
        m = s.mate()
        return (MATE_CP - abs(m) * 2) * (1 if m > 0 else -1)
    return s.score()


def work(args):
    build, chunk = args
    import chess, chess.engine
    sys.path.insert(0, build)
    import cs_fast
    eng = chess.engine.SimpleEngine.popen_uci(SF)
    eng.configure({"Threads": 1, "Hash": 128})
    s = cs_fast.Searcher()
    cs_fast.warm_up()
    out = []
    for r in chunk:
        board = chess.Board(r["fen"])
        pov = board.turn
        s.new_game()
        mv, info = s.search(board.copy(), CAP_MS, max_depth=DEPTH)
        b = board.copy()
        b.push(mv)
        i2 = eng.analyse(b, chess.engine.Limit(nodes=NODES))
        loss = max(0, r["score_before"] - to_cp(i2["score"], pov))
        out.append(dict(fen=r["fen"], move=mv.uci(), cp_loss=loss, depth=info.depth,
                        nodes=info.nodes))
    eng.quit()
    return out


if __name__ == "__main__":
    rows = json.load(open(SRC))
    print(f"{len(rows)} positions, depth {DEPTH}, {WORKERS} workers per build", flush=True)
    res = {}
    for label, build in (("base", BASE_DIR), ("cand", CAND_DIR)):
        chunks = [(build, rows[i::WORKERS]) for i in range(WORKERS)]
        got = []
        with ProcessPoolExecutor(max_workers=WORKERS) as ex:
            for part in ex.map(work, chunks):
                got.extend(part)
        res[label] = {r["fen"]: r for r in got}
        print(f"  {label}: {len(got)} searched", flush=True)

    merged = []
    for r in rows:
        b, c = res["base"].get(r["fen"]), res["cand"].get(r["fen"])
        if not b or not c:
            continue
        merged.append(dict(r, base_loss=b["cp_loss"], cand_loss=c["cp_loss"],
                           base_move=b["move"], cand_move=c["move"]))
    json.dump(merged, open(OUT, "w"))

    SETS = [
        ("TARGET  enemy passer rank6+", lambda r: r["enemy_passer_advance"] >= 5),
        ("HELDOUT enemy passer rank<6", lambda r: 0 < r["enemy_passers"] and r["enemy_passer_advance"] < 5),
        ("CONTROL no enemy passer", lambda r: r["enemy_passers"] == 0),
        ("ALL serious errors", lambda r: True),
    ]
    print(f"\n{'set':30s} {'n':>4s} {'base>=100':>9s} {'cand>=100':>9s} {'repaired':>8s} {'worsened':>8s} {'mean base':>9s} {'mean cand':>9s}")
    for name, f in SETS:
        g = [r for r in merged if f(r)]
        if not g:
            continue
        rep = sum(1 for r in g if r["base_loss"] >= 100 and r["cand_loss"] < 100)
        wor = sum(1 for r in g if r["base_loss"] < 100 and r["cand_loss"] >= 100)
        print(f"{name:30s} {len(g):4d} {sum(1 for r in g if r['base_loss']>=100):9d} "
              f"{sum(1 for r in g if r['cand_loss']>=100):9d} {rep:8d} {wor:8d} "
              f"{sum(min(1000,r['base_loss']) for r in g)/len(g):9.1f} "
              f"{sum(min(1000,r['cand_loss']) for r in g)/len(g):9.1f}")
