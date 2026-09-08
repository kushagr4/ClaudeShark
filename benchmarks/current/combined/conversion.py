"""Gate 0 conversion matrix: candidate against frozen RC-F.

Three blocks:
  ROUND 54   the two live positions from the forensic audit
  ELEMENTARY a fresh suite of four K+R vs K and four K+Q vs K positions
  CONTROL    round 48's K+B+N vs K, which is outside the gate and must not move

Every cell is a deterministic fixed-depth playout against the same fixed
defender, so candidate and baseline are compared like for like.
"""
import subprocess, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
LANE = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PY = r"C:/Users/epick/Documents/ClaudeShark/.venv/Scripts/python.exe"
BUILDS = [("C12", r"C:/Users/epick/AppData/Local/Temp/claude/C--Users-epick-Documents-ClaudeShark/e3813b42-0a37-4aea-86be-348b96190e38/scratchpad/c12"), ("RCG", LANE)]
DEPTHS = [8, 10, 12, 14]

ROUND54 = [
    ("R54-entry-m91", "7R/1K6/5k2/8/8/8/8/8 w - - 0 91", 120),
    ("R54-m93", "8/1K6/5k2/3R4/8/8/8/8 w - - 4 93", 120),
]
ELEMENTARY = [
    ("KRK-1", "8/8/8/4k3/8/8/8/R3K3 w - - 0 1", 120),
    ("KRK-2", "8/8/8/8/3k4/8/8/R5K1 w - - 0 1", 120),
    ("KRK-3", "8/6k1/8/8/8/8/R7/6K1 w - - 0 1", 120),
    ("KRK-4", "3k4/8/8/8/8/8/7R/3K4 w - - 0 1", 120),
    ("KQK-1", "8/8/8/4k3/8/8/8/3QK3 w - - 0 1", 120),
    ("KQK-2", "8/8/2k5/8/8/8/8/3QK3 w - - 0 1", 120),
    ("KQK-3", "8/5k2/8/8/8/8/1Q6/6K1 w - - 0 1", 120),
    ("KQK-4", "2k5/8/8/8/8/8/8/Q3K3 w - - 0 1", 120),
]
CONTROL = [("R48-KBN-m77", "6n1/5k1K/8/8/2b5/8/8/8 b - - 1 77", 140)]


def run(build_dir, fen, label, depth, maxply):
    out = subprocess.run([PY, os.path.join(HERE, "playout.py"), build_dir, fen, label,
                          str(depth), str(maxply)], capture_output=True, text=True).stdout
    m = re.search(r"RESULT \S+ build=\S+ depth=\d+ (MATE|FAIL) plies=(\d+) term=(\S+)", out)
    if not m:
        return ("ERR", "?", "?")
    return (m.group(1), m.group(2), m.group(3))


def block(name, cases):
    print(f"\n===== {name} =====")
    print(f"{'position':16s} {'build':6s} " + " ".join(f"d{d:<8d}" for d in DEPTHS) + " converted")
    tally = collections.defaultdict(lambda: collections.defaultdict(list))
    terms = collections.Counter()
    for label, fen, maxply in cases:
        for bname, bdir in BUILDS:
            cells = []
            for d in DEPTHS:
                res, plies, term = run(bdir, fen, label, d, maxply)
                cells.append((res, plies, term))
                terms[(bname, term)] += 1
                tally[bname][label].append(res == "MATE")
            shown = " ".join(f"{r}/{p:<5s}" for r, p, _ in cells)
            ok = sum(1 for r, _, _ in cells if r == "MATE")
            print(f"{label:16s} {bname:6s} {shown} {ok}/{len(DEPTHS)}", flush=True)
    print(f"-- {name} summary --")
    for bname, _ in BUILDS:
        per = tally[bname]
        cells_ok = sum(sum(v) for v in per.values())
        cells_all = sum(len(v) for v in per.values())
        strict = sum(1 for v in per.values() if all(v))
        loose = sum(1 for v in per.values() if sum(v) >= 3)
        print(f"   {bname:6s} cells {cells_ok}/{cells_all}  "
              f"all-depth {strict}/{len(per)}  >=3-of-4 {loose}/{len(per)}")
    for (bname, term), n in sorted(terms.items()):
        print(f"   {bname:6s} {term:24s} {n}")
    return tally


t1 = block("ROUND 54 LIVE POSITIONS", ROUND54)
t2 = block("ELEMENTARY SUITE (fresh)", ELEMENTARY)
t3 = block("NEGATIVE CONTROL, OUTSIDE THE GATE", CONTROL)

print("\n===== PROMOTION METRIC =====")
for bname, _ in BUILDS:
    per = t2[bname]
    strict = sum(1 for v in per.values() if all(v))
    loose = sum(1 for v in per.values() if sum(v) >= 3)
    cells = sum(sum(v) for v in per.values())
    print(f"  {bname:6s} elementary: all-depth {strict}/8, >=3-of-4 {loose}/8, cells {cells}/32")
for bname, _ in BUILDS:
    per = t3[bname]
    cells = sum(sum(v) for v in per.values())
    print(f"  {bname:6s} KBNK control cells converted {cells}/{len(DEPTHS)} (expected: unchanged)")
