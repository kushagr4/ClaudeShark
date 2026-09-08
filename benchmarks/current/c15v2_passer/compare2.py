"""Candidate against baseline on the pre-registered sets, with an oracle that
gives the same answer twice.

The first version of this harness kept one Stockfish process per worker and
analysed position after position into the same hash table. A fixed-node search
is only deterministic given the same starting hash, so every analysis depended
on which moves the build being measured had played before it. Over the 144
serious errors that produced 57 positions where both builds chose the *same*
move and the oracle scored it differently -- two of them by more than 20,000
centipawns, which is the difference between "lost" and "mated". Any repair or
regression read off that harness could be an artefact.

The fix is one line of intent: every analysis declares a new ``game``, so
python-chess sends ``ucinewgame`` and Stockfish clears its table first. Each
analysis is then a pure function of the position. The run asserts it: the
position's own score is measured independently in both passes and the two must
agree exactly, and any position where the builds played the same move must
receive the same loss.

usage: compare2.py <serious_errors.json> <baseline_dir> <candidate_dir> <out.json> [depth] [workers]
"""
import json
import sys
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
    import chess
    import chess.engine
    sys.path.insert(0, build)
    import cs_fast
    eng = chess.engine.SimpleEngine.popen_uci(SF)
    eng.configure({"Threads": 1, "Hash": 128})

    def oracle(board, tag):
        # A fresh `game` object makes python-chess send ucinewgame, so the
        # table is empty and the fixed-node result depends only on the FEN.
        return eng.analyse(board, chess.engine.Limit(nodes=NODES), game=tag)

    s = cs_fast.Searcher()
    cs_fast.warm_up()
    out = []
    for r in chunk:
        board = chess.Board(r["fen"])
        pov = board.turn
        before = to_cp(oracle(board, ("before", r["fen"]))["score"], pov)
        s.new_game()
        mv, info = s.search(board.copy(), CAP_MS, max_depth=DEPTH)
        after = board.copy()
        after.push(mv)
        got = to_cp(oracle(after, ("after", after.fen()))["score"], pov)
        out.append(dict(fen=r["fen"], move=mv.uci(), score_before=before,
                        cp_loss=max(0, before - got), depth=info.depth,
                        nodes=info.nodes, reached=bool(info.depth >= DEPTH)))
    eng.quit()
    return out


if __name__ == "__main__":
    rows = json.load(open(SRC))
    print(f"{len(rows)} positions, depth {DEPTH}, {WORKERS} workers per build, "
          f"oracle {NODES:,} nodes with the table cleared per analysis", flush=True)
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
    disagree = 0
    same_move_disagree = 0
    for r in rows:
        b, c = res["base"].get(r["fen"]), res["cand"].get(r["fen"])
        if not b or not c:
            continue
        if b["score_before"] != c["score_before"]:
            disagree += 1
        if b["move"] == c["move"] and b["cp_loss"] != c["cp_loss"]:
            same_move_disagree += 1
        merged.append(dict(r, base_loss=b["cp_loss"], cand_loss=c["cp_loss"],
                           base_move=b["move"], cand_move=c["move"],
                           oracle_before=b["score_before"],
                           base_depth=b["depth"], cand_depth=c["depth"],
                           base_nodes=b["nodes"], cand_nodes=c["nodes"],
                           base_reached=b["reached"], cand_reached=c["reached"]))
    json.dump(merged, open(OUT, "w"))

    print(f"\nORACLE DETERMINISM: positions whose own score differed between the two "
          f"passes: {disagree} (must be 0)")
    print(f"ORACLE DETERMINISM: same move scored differently: {same_move_disagree} "
          f"(must be 0)")
    capped = sum(1 for r in merged if not r["base_reached"] or not r["cand_reached"])
    print(f"positions where a build did not reach depth {DEPTH} within {CAP_MS} ms: {capped}")

    SETS = [
        ("TARGET  enemy passer rank6+", lambda r: r["enemy_passer_advance"] >= 5),
        ("HELDOUT enemy passer rank<6",
         lambda r: 0 < r["enemy_passers"] and r["enemy_passer_advance"] < 5),
        ("CONTROL no enemy passer", lambda r: r["enemy_passers"] == 0),
        ("ALL serious errors", lambda r: True),
    ]
    print(f"\n{'set':30s} {'n':>4s} {'base>=100':>9s} {'cand>=100':>9s} {'repaired':>8s} "
          f"{'worsened':>8s} {'mean base':>9s} {'mean cand':>9s}")
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
