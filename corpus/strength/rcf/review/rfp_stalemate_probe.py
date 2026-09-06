"""RFP-on-stalemate activation and decision relevance, instrumented RC-F copy.

CTL[12] = RFP hits, CTL[11] = RFP hits on a node with no legal move,
CTL[13] = 1 makes such a node return DRAW_SCORE (the candidate guard).
"""
import sys, json, io, re
sys.path.insert(0, r"C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/rcf_instr")
import chess, chess.pgn
import cs_fast

REPO = r"C:/Users/epick/Documents/ClaudeShark/"
DEPTH_SUITE = int(sys.argv[1]) if len(sys.argv) > 1 else 7
DEPTH_END = int(sys.argv[2]) if len(sys.argv) > 2 else 9

suite = [r["fen"] for r in (json.loads(l) for l in open(REPO + "corpus/competition_like_v1.jsonl", encoding="utf-8")) if "fen" in r]

endings = []
for p in ("corpus/strength/rcf/rcf_vs_sf2800_dev2400_60_strict.pgn",
          "corpus/strength/c9/c9_vs_c5_dev_60_strict.pgn"):
    f = open(REPO + p, encoding="utf-8", errors="replace")
    while True:
        g = chess.pgn.read_game(f)
        if g is None:
            break
        b = g.board()
        seen = set()
        for mv in g.mainline_moves():
            b.push(mv)
            n = len(b.piece_map())
            if n <= 7 and not b.is_game_over(claim_draw=True):
                k = b._transposition_key()
                if k not in seen:
                    seen.add(k)
                    endings.append(b.fen())
endings = endings[::max(1, len(endings) // 300)][:300]
print(f"endgame positions: {len(endings)}", flush=True)

s = cs_fast.Searcher()
cs_fast.warm_up()


def run(fens, depth, label):
    hits = stale = 0
    changed = []
    for i, fen in enumerate(fens):
        b = chess.Board(fen)
        s.CTL[13] = 0
        s.new_game(); s.CTL[11] = 0; s.CTL[12] = 0
        m0, i0 = s.search(b, 0, max_depth=depth)
        hits += int(s.CTL[12]); stale += int(s.CTL[11])
        st = int(s.CTL[11])
        s.CTL[13] = 1
        s.new_game(); s.CTL[11] = 0; s.CTL[12] = 0
        m1, i1 = s.search(b, 0, max_depth=depth)
        if m0 != m1 or i0.score != i1.score or i0.nodes != i1.nodes:
            changed.append((fen, m0.uci(), i0.score, i0.nodes, m1.uci(), i1.score, i1.nodes, st))
    print(f"{label}: {len(fens)} positions depth {depth}: RFP hits {hits:,}, RFP hits on stalemate {stale}, "
          f"positions whose root move/score/nodes change with the guard: {len(changed)}", flush=True)
    for c in changed:
        print("  CHANGED", c, flush=True)
    return hits, stale, changed


run(suite, DEPTH_SUITE, "competition_like_v1")
run(endings, DEPTH_END, "endgames<=7 pieces")
s.CTL[13] = 0
