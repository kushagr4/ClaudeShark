"""RC-F runtime-share profile: call counters from a real 2 s search over the
bench suite, times per-call microbenchmarks of each component, on a scratch
copy of champions/rc_f (the champion is not modified).
"""
import os, re, shutil, sys, time, json, random
import numpy as np

SCR = r"C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad"
REPO = r"C:/Users/epick/Documents/ClaudeShark"
P = os.path.join(SCR, "rcf_prof")
if os.path.isdir(P):
    shutil.rmtree(P)
shutil.copytree(os.path.join(REPO, "champions", "rc_f"), P, ignore=shutil.ignore_patterns("__pycache__"))

core_path = os.path.join(P, "cs_core.py")
s = open(core_path, encoding="utf-8").read()
a = s.index("def quiescence(")
b = s.index("def search_root(")
body = s[a:b]
body = body.replace("        make_move(B, O, M, S, U, move)\n", "        CTL[11] += 1\n        make_move(B, O, M, S, U, move)\n")
body = re.sub(r"(\n\s+)(n = gen_moves\(B, O, M, S, ML, (?:True|False)\))", r"\1CTL[12] += 1\1\2", body)
body = re.sub(r"(\n\s+)(stand_pat = evaluate\(B, S\)|static = evaluate\(B, S\))", r"\1CTL[13] += 1\1\2", body)
body = re.sub(r"(\n\s+)(return evaluate\(B, S\))", r"\1CTL[13] += 1\1\2", body)
body = body.replace("            losing = see(B, O, M, S, move, GAINS) < 0\n", "            CTL[14] += 1\n            losing = see(B, O, M, S, move, GAINS) < 0\n")
body = body.replace("score_moves(B, O, M, S, ML, MS, n, ttm, killer_1, killer_2, HIST, GAINS)", "score_moves(B, O, M, S, ML, MS, n, ttm, killer_1, killer_2, HIST, GAINS, CTL)")
body = body.replace("        score_captures(M, ML, MS, n)\n", "        CTL[15] += 1\n        score_captures(M, ML, MS, n)\n")
s = s[:a] + body + s[b:]
s = s.replace("def score_moves(B, O, M, S, ML, MS, n, tt_move, killer_1, killer_2, HIST, gains):",
              "def score_moves(B, O, M, S, ML, MS, n, tt_move, killer_1, killer_2, HIST, gains, CTL):\n    CTL[15] += 1")
s = s.replace("            elif PIECE_VALUE[victim_t] < PIECE_VALUE[attacker_t] and see(B, O, M, S, move, gains) < 0:",
              "            elif PIECE_VALUE[victim_t] < PIECE_VALUE[attacker_t] and _see_count(CTL, B, O, M, S, move, gains) < 0:")
s = s.replace("@njit(cache=False)\ndef score_moves(", "@njit(cache=False)\ndef _see_count(CTL, B, O, M, S, move, gains):\n    CTL[14] += 1\n    return see(B, O, M, S, move, gains)\n\n\n@njit(cache=False)\ndef score_moves(")
open(core_path, "w", encoding="utf-8", newline="\n").write(s)
fast_path = os.path.join(P, "cs_fast.py")
f = open(fast_path, encoding="utf-8").read()
f = f.replace("self.HIST, self.GAINS)\n        order = sorted", "self.HIST, self.GAINS, self.CTL)\n        order = sorted")
# time inside the compiled root
f = f.replace("        score, move = core.search_root(", "        _t0 = _pc()\n        score, move = core.search_root(")
f = f.replace("        if self.CTL[0]:\n            return int(score), int(move), root_moves\n        order = sorted(range(n)",
              "        self.inside += _pc() - _t0\n        if self.CTL[0]:\n            return int(score), int(move), root_moves\n        order = sorted(range(n)")
f = f.replace("import chess\nimport numpy as np\n", "import chess\nimport numpy as np\nfrom time import perf_counter as _pc\n")
f = f.replace("        self._game_keys: list[int] = []\n", "        self._game_keys: list[int] = []\n        self.inside = 0.0\n")
open(fast_path, "w", encoding="utf-8", newline="\n").write(f)
assert "CTL[14]" in s and "CTL[11]" in s and "self.inside" in f

sys.path.insert(0, P)
import chess
import cs_core as core
import cs_fast
from numba import njit

fens = [json.loads(l)["fen"] for l in open(os.path.join(REPO, "corpus", "competition_like_v1.jsonl"), encoding="utf-8") if '"fen"' in l]
bench = [l.strip() for l in open(os.path.join(REPO, "benchmarks", "fens.txt"), encoding="utf-8") if l.strip() and not l.startswith("#")] if os.path.exists(os.path.join(REPO, "benchmarks", "fens.txt")) else fens[:24]

# ---------------------------------------------------------------- real search
cs_fast.warm_up()
S = cs_fast.Searcher()
tot = np.zeros(16, dtype=np.int64)
elapsed = 0.0
inside0 = S.inside
for fen in bench[:24]:
    S.CTL[11:16] = 0
    t = time.perf_counter()
    S.search(chess.Board(fen), 0, fixed_budget_ms=2000)
    elapsed += time.perf_counter() - t
    tot += S.CTL
inside = S.inside - inside0
nodes, qnodes, probes = int(tot[2]), int(tot[3]), int(tot[7])
makes, gens, evals, sees, scores = (int(tot[i]) for i in range(11, 16))
print(f"search: {len(bench[:24])} positions x 2 s; wall {elapsed:.2f}s, inside compiled root {inside:.2f}s ({100*inside/elapsed:.1f}%)")
print(f"nodes {nodes:,} (q {qnodes:,}, {100*qnodes/nodes:.0f}%) nps {nodes/elapsed:,.0f}; make+unmake {makes:,}; gen_moves {gens:,}; evaluate {evals:,}; see {sees:,}; score lists {scores:,}; tt probes {probes:,}")

# ---------------------------------------------------------------- microbenchmarks
B, O, M, St, U = core.new_board_arrays()
ML = np.zeros(256, dtype=np.int64); MS = np.zeros(256, dtype=np.int64)
GAINS = np.zeros(40, dtype=np.int64); HIST = np.zeros(8192, dtype=np.int64)
TK = np.zeros(1 << core.TT_BITS, dtype=np.int64); TV = np.zeros(1 << core.TT_BITS, dtype=np.int64)
CTL = np.zeros(16, dtype=np.int64); TCTL = np.zeros(2, dtype=np.float64); TCTL[0] = 1e18

rng = random.Random(5)
sample = []
for fen in fens[:200]:
    b = chess.Board(fen)
    for _ in range(rng.randint(0, 6)):
        mv = list(b.legal_moves)
        if not mv:
            break
        b.push(rng.choice(mv))
    if not b.is_game_over():
        sample.append(b)
NPOS = len(sample)
BB = np.zeros((NPOS, 13), dtype=np.int64); OO = np.zeros((NPOS, 3), dtype=np.int64)
MM = np.zeros((NPOS, 64), dtype=np.int64); SS = np.zeros((NPOS, 8), dtype=np.int64)
for i, b in enumerate(sample):
    core.load_board(b, B, O, M, St)
    BB[i] = B; OO[i] = O; MM[i] = M; SS[i] = St


@njit(cache=False)
def k_eval(BB, SS, reps):
    acc = 0
    for r in range(reps):
        for i in range(BB.shape[0]):
            acc += core.evaluate(BB[i], SS[i])
    return acc


@njit(cache=False)
def k_gen(BB, OO, MM, SS, ML, reps, caps):
    acc = 0
    for r in range(reps):
        for i in range(BB.shape[0]):
            acc += core.gen_moves(BB[i], OO[i], MM[i], SS[i], ML, caps)
    return acc


@njit(cache=False)
def k_make(BB, OO, MM, SS, U, ML, reps):
    acc = 0
    for r in range(reps):
        for i in range(BB.shape[0]):
            B = BB[i]; O = OO[i]; M = MM[i]; S = SS[i]
            n = core.gen_moves(B, O, M, S, ML, False)
            for j in range(n):
                core.make_move(B, O, M, S, U, ML[j])
                acc += core.is_legal_after_make(B, O, S)
                core.unmake_move(B, O, M, S, U)
    return acc


@njit(cache=False)
def k_gen_count(BB, OO, MM, SS, ML):
    acc = 0
    for i in range(BB.shape[0]):
        acc += core.gen_moves(BB[i], OO[i], MM[i], SS[i], ML, False)
    return acc


@njit(cache=False)
def k_see(BB, OO, MM, SS, ML, GAINS, reps):
    acc = 0; calls = 0
    for r in range(reps):
        for i in range(BB.shape[0]):
            B = BB[i]; O = OO[i]; M = MM[i]; S = SS[i]
            n = core.gen_moves(B, O, M, S, ML, True)
            for j in range(n):
                acc += core.see(B, O, M, S, ML[j], GAINS)
                calls += 1
    return acc, calls


@njit(cache=False)
def k_score(BB, OO, MM, SS, ML, MS, HIST, GAINS, CTL, reps):
    acc = 0
    for r in range(reps):
        for i in range(BB.shape[0]):
            B = BB[i]; O = OO[i]; M = MM[i]; S = SS[i]
            n = core.gen_moves(B, O, M, S, ML, False)
            core.score_moves(B, O, M, S, ML, MS, n, 0, 0, 0, HIST, GAINS, CTL)
            for j in range(n):
                acc += core.pick_next(ML, MS, n, j)
    return acc


@njit(cache=False)
def k_tt(TK, TV, SS, reps):
    acc = 0
    for r in range(reps):
        for i in range(SS.shape[0]):
            key = SS[i, 4] + r
            core.tt_store(TK, TV, key, 5, 10, 1, 77)
            acc += core.tt_probe(TK, TV, key)
    return acc


@njit(cache=False)
def k_incheck(BB, OO, SS, reps):
    acc = 0
    for r in range(reps):
        for i in range(BB.shape[0]):
            acc += core.in_check(BB[i], OO[i], SS[i])
    return acc


@njit(cache=False)
def k_time(CTL, TCTL, reps):
    for r in range(reps):
        core._check_time(CTL, TCTL)
    return CTL[2]


def timeit(fn, *args):
    fn(*args)  # compile
    t = time.perf_counter(); out = fn(*args); return time.perf_counter() - t, out


REPS = 200
t_eval, _ = timeit(k_eval, BB, SS, REPS)
t_gen, ngen = timeit(k_gen, BB, OO, MM, SS, ML, REPS, False)
t_genc, ngenc = timeit(k_gen, BB, OO, MM, SS, ML, REPS, True)
t_make, _ = timeit(k_make, BB, OO, MM, SS, U, ML, REPS)
moves_per_pos = k_gen_count(BB, OO, MM, SS, ML)
t_see, (_, see_calls) = timeit(k_see, BB, OO, MM, SS, ML, GAINS, REPS)
t_score, _ = timeit(k_score, BB, OO, MM, SS, ML, MS, HIST, GAINS, CTL, REPS)
t_tt, _ = timeit(k_tt, TK, TV, SS, REPS)
t_chk, _ = timeit(k_incheck, BB, OO, SS, REPS)
CTL[2] = 0
t_time, _ = timeit(k_time, CTL, TCTL, 1024 * 2000)

calls = REPS * NPOS
u_eval = t_eval / calls
u_gen = t_gen / calls
u_genc = t_genc / calls
u_make = (t_make - t_gen) / (REPS * moves_per_pos)          # make + legality + unmake, per move
u_see = t_see / max(1, see_calls) - u_genc * 0                # see per call (gen cost included, small)
u_see = (t_see - t_genc) / max(1, see_calls)
u_score = (t_score - t_gen) / calls                            # score + pick a whole list
u_score_per_move = (t_score - t_gen) / (REPS * moves_per_pos)
u_tt = t_tt / calls                                            # store + probe
u_chk = t_chk / calls
u_time_per_node = t_time / (1024 * 2000)

print(f"\nmicrobench ({NPOS} positions, avg {moves_per_pos/NPOS:.1f} legal-ish moves): per call us: evaluate {u_eval*1e6:.2f}, gen all {u_gen*1e6:.2f}, gen captures {u_genc*1e6:.2f}, make+legal+unmake per move {u_make*1e6:.3f}, see {u_see*1e6:.2f}, score list {u_score*1e6:.2f} ({u_score_per_move*1e6:.3f}/move), tt store+probe {u_tt*1e6:.3f}, in_check {u_chk*1e6:.3f}, time check per node {u_time_per_node*1e6:.4f}")

est = {
    "make/unmake+legality": makes * u_make,
    "move generation": gens * (u_gen * 0.6 + u_genc * 0.4),
    "evaluation": evals * u_eval,
    "SEE": sees * u_see,
    "move ordering (score+pick)": scores * u_score,
    "TT probe+store": probes * u_tt * 0.75,
    "in_check (node + LMR)": (nodes + makes // 2) * u_chk,
    "time checks (objmode)": nodes * u_time_per_node,
    "Python<->Numba root/ID overhead": elapsed - inside,
}
total_est = sum(est.values())
print(f"\nestimated shares of {elapsed:.2f}s wall (components sum to {total_est:.2f}s = {100*total_est/elapsed:.0f}%; remainder is search control flow, pruning tests, history/killers, recursion):")
for k, v in sorted(est.items(), key=lambda kv: -kv[1]):
    print(f"  {k:34s} {v:6.2f}s  {100*v/elapsed:5.1f}%")
print(f"  {'remainder (control flow etc.)':34s} {elapsed-total_est:6.2f}s  {100*(elapsed-total_est)/elapsed:5.1f}%")
