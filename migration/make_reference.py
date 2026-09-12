"""Record this machine's evaluator outputs on a fixed position corpus, for cross-platform comparison.

The corpus is defined in this file (seeded playouts plus hand-written special positions), so the
same input set is reproducible on any machine without external data. Run it once on the source
machine before a migration, once on the target machine afterwards, and compare with --compare.

Quantities recorded per position, all from RC-J's own compiled code:

  e0              cs_core.evaluate                                   integer, must match exactly
  e1_correction   features.e1_correction (the pilot's linear model)  float, tolerance below
  e1              e0 + round(e1_correction)                          integer, must match exactly
  n1_float_cp     nn1.float_forward_cp (N1-U, float32 weights)       float, tolerance below
  n1q_cp          nn1.quant_forward_cp (N1-U quantised, integer)     integer, must match exactly
  qs_e0           RC-J quiescence, E0 leaf (nn1kit.qs_nn mode 0)     integer, must match exactly
  qs_n1q          RC-J quiescence, E0 + N1q leaf (mode 2)            integer, must match exactly
  zobrist         cs_core key                                        integer, must match exactly
  packed_pst      cs_core packed piece-square accumulator            integer, must match exactly
  legal_moves     python-chess legal move count                      integer, must match exactly

FLOAT_TOL is fixed here, before any target-machine number has been seen: 1e-6 centipawns absolute
on e1_correction and n1_float_cp. Both are float64 sums of at most a few hundred products, so any
difference beyond that is a real numerical divergence and not accumulation order.

The controlled capture tree (C28) is recorded only with --with-cct and only as
`provisional_pre_repair`: C28 is in pre-adjudication repair, so those numbers are informational and
are never a pass/fail criterion.

    python migration/make_reference.py --out migration/reference_windows.json [--with-cct]
    python migration/make_reference.py --compare A.json B.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LE_SCRIPTS = os.path.join(ROOT, "benchmarks", "current", "learned_eval", "scripts")
C28_SCRIPTS = os.path.join(ROOT, "benchmarks", "current", "hard_position_mining", "scripts")
for p in (ROOT, LE_SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)

import chess  # noqa: E402

SEED = 20260912
N_PLAYOUT = 40
FLOAT_TOL = 1e-6
EXACT_FIELDS = ("e0", "e1", "n1q_cp", "qs_e0", "qs_n1q", "zobrist", "packed_pst", "legal_moves")
FLOAT_FIELDS = ("e1_correction", "n1_float_cp")

# Hand-written positions: terminal and near-terminal shapes, special moves, and the bare-king
# endings the N1 magnitude audit failed on. Every one is legal and not already game over.
SPECIAL = [
    ("start", chess.STARTING_FEN),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("promotion_white", "8/PPPk4/8/8/8/8/4Kppp/8 w - - 0 1"),
    ("promotion_black", "8/PPPk4/8/8/8/8/4Kppp/8 b - - 0 1"),
    ("en_passant", "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3"),
    ("castle_both", "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"),
    # Terminal by the rules (Fool's mate): kept deliberately, because the evaluators are called on
    # such positions by the search's own terminal handling and the values must still agree.
    ("checkmate_terminal", "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"),
    # In check but not mate: the king may step aside or capture the checker, so the capture tree
    # has to generate evasions rather than captures.
    ("in_check_not_mate", "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1"),
    ("mate_in_one", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
    ("stalemate_in_one", "7k/8/6Q1/8/8/8/8/6K1 w - - 0 1"),
    ("krk", "8/8/8/4k3/8/8/4K3/4R3 w - - 0 1"),
    ("kqk", "8/8/8/4k3/8/8/4K3/4Q3 w - - 0 1"),
    ("kpk", "8/8/8/4k3/8/4P3/4K3/8 w - - 0 1"),
    ("opposite_bishops", "8/2k5/3b4/8/8/3B4/2K5/8 w - - 0 1"),
    ("rook_endgame", "8/5pk1/6p1/8/8/1R6/5PPP/6K1 w - - 0 1"),
    ("queenless_mid", "r4rk1/pp2ppbp/2np1np1/8/3NP3/2N1B3/PPP2PPP/R4RK1 w - - 0 1"),
    ("tactical", "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 5"),
    ("black_to_move_mid", "r2q1rk1/pp2bppp/2n1bn2/3p4/3P4/2N1BN2/PP2BPPP/R2Q1RK1 b - - 0 11"),
    ("bare_kings_plus", "8/8/4k3/8/8/3K4/8/7R b - - 0 1"),
]


def playout_positions(n: int, seed: int) -> list[tuple[str, str]]:
    """Seeded random legal playouts. Python's Mersenne Twister is platform independent, so the
    same seed yields the same positions everywhere; the FENs are also stored in the output."""
    rng = random.Random(seed)
    out: list[tuple[str, str]] = []
    i = 0
    while len(out) < n:
        i += 1
        board = chess.Board()
        plies = rng.randint(10, 70)
        for _ in range(plies):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        if board.is_game_over(claim_draw=False) or not board.is_valid():
            continue
        out.append((f"playout_{len(out):02d}", board.fen()))
    return out


def corpus() -> list[dict]:
    rows = [dict(name=n, fen=f) for n, f in SPECIAL]
    rows += [dict(name=n, fen=f) for n, f in playout_positions(N_PLAYOUT, SEED)]
    return rows


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def measure(rows: list[dict], with_cct: bool) -> dict:
    import numpy as np

    import features as F
    import nn1
    import nn1kit

    weights = os.path.join(ROOT, "benchmarks/current/learned_eval/results/n1/n1_weights.npz")
    e1_path = os.path.join(ROOT, "benchmarks/current/learned_eval/results/e1_weights.json")
    fl, Q = nn1.load(weights)
    with open(e1_path, encoding="utf-8") as fh:
        W_E1 = np.asarray(json.load(fh)["W"], dtype=np.float64)
    scorer = nn1kit.NNScorer(fl, Q)

    boards = [chess.Board(r["fen"]) for r in rows]
    BB, SS, STM = F.arrays_from_boards(boards)
    t0 = time.perf_counter()
    out = []
    for i, (row, board) in enumerate(zip(rows, boards)):
        s_idx, o_idx = nn1.board_features(board)
        e0 = int(F.C.evaluate(BB[i], SS[i]))
        corr = float(F.e1_correction(BB[i], int(STM[i]), W_E1))
        st0, q0 = scorer.root(board, 0)
        st2, q2 = scorer.root(board, 2)
        assert st0 == e0, (row["name"], st0, e0)
        out.append(dict(
            name=row["name"], fen=row["fen"],
            e0=e0,
            e1_correction=corr,
            e1=e0 + int(round(corr)),
            n1_float_cp=float(nn1.float_forward_cp(s_idx, o_idx, fl)),
            n1q_cp=int(nn1.quant_forward_cp(s_idx, o_idx, Q)),
            qs_e0=int(q0),
            qs_n1q=int(q2),
            n1q_static_sum=int(st2),
            zobrist=int(SS[i][4]),
            packed_pst=int(SS[i][5]),
            phase=int(F.e1_phase(BB[i])),
            legal_moves=board.legal_moves.count(),
        ))
    seconds = time.perf_counter() - t0

    res = dict(
        schema="claudeshark-migration-reference/1",
        seed=SEED, n_playout=N_PLAYOUT, float_tol=FLOAT_TOL,
        exact_fields=list(EXACT_FIELDS), float_fields=list(FLOAT_FIELDS),
        platform=dict(system=platform.system(), release=platform.release(),
                      machine=platform.machine(), processor=platform.processor(),
                      python=sys.version.split()[0], python_build=platform.python_build(),
                      numpy=np.__version__, chess=chess.__version__),
        inputs=dict(n1_weights_sha256=sha256_file(weights), e1_weights_sha256=sha256_file(e1_path),
                    cs_core_sha256=sha256_file(os.path.join(ROOT, "cs_core.py")),
                    features_sha256=sha256_file(os.path.join(LE_SCRIPTS, "features.py")),
                    nn1_sha256=sha256_file(os.path.join(LE_SCRIPTS, "nn1.py")),
                    nn1kit_sha256=sha256_file(os.path.join(LE_SCRIPTS, "nn1kit.py"))),
        seconds=round(seconds, 2),
        positions=out,
    )
    try:
        import numba
        res["platform"]["numba"] = numba.__version__
    except Exception:
        res["platform"]["numba"] = None
    if with_cct:
        res["cct_provisional_pre_repair"] = measure_cct(rows)
    res["values_sha256"] = hashlib.sha256(
        json.dumps(out, sort_keys=True).encode()).hexdigest()
    return res


def measure_cct(rows: list[dict]) -> dict:
    """Informational only: C28's controlled capture tree is in pre-adjudication repair, so these
    numbers are not an expectation and never a pass/fail criterion."""
    if C28_SCRIPTS not in sys.path:
        sys.path.insert(0, C28_SCRIPTS)
    try:
        import cct  # noqa: PLC0415
        import critics  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - reported, never fatal
        return dict(status="unavailable", error=f"{type(exc).__name__}: {exc}")
    try:
        cr = critics.load()
        sc = cct.RootScorer(cr, qply_max=4, cap_nodes=2000, cap_root=20000)
        vals = []
        for row in rows[:12]:
            r = sc.score(chess.Board(row["fen"]))
            moves = r.get("moves") or {}
            vals.append(dict(name=row["name"], nodes_total=r["nodes_total"], resolved=r["resolved"],
                             n_legal=r["n_legal"], n_moves_scored=len(moves),
                             root_static_cp=[int(x) for x in r["root"]["static_cp"]],
                             best_cct_cp_e0=(max(int(m["cct_cp"][0]) for m in moves.values())
                                             if moves else None)))
        return dict(status="recorded", caps=dict(qply_max=4, cap_nodes=2000, cap_root=20000),
                    note="provisional: C28 implementation is under repair; informational only",
                    values=vals)
    except Exception as exc:  # pragma: no cover
        return dict(status="error", error=f"{type(exc).__name__}: {exc}")


def compare(a_path: str, b_path: str) -> int:
    with open(a_path, encoding="utf-8") as fh:
        a = json.load(fh)
    with open(b_path, encoding="utf-8") as fh:
        b = json.load(fh)
    pa = {r["name"]: r for r in a["positions"]}
    pb = {r["name"]: r for r in b["positions"]}
    print(f"A: {a['platform']['system']} {a['platform']['machine']} python {a['platform']['python']}")
    print(f"B: {b['platform']['system']} {b['platform']['machine']} python {b['platform']['python']}")
    for key in ("n1_weights_sha256", "e1_weights_sha256", "cs_core_sha256"):
        if a["inputs"].get(key) != b["inputs"].get(key):
            print(f"FAIL input differs: {key}\n  A {a['inputs'].get(key)}\n  B {b['inputs'].get(key)}")
            return 1
    missing = set(pa) ^ set(pb)
    if missing:
        print(f"FAIL position sets differ: {sorted(missing)}")
        return 1
    tol = min(float(a.get("float_tol", FLOAT_TOL)), float(b.get("float_tol", FLOAT_TOL)))
    bad = []
    for name in sorted(pa):
        ra, rb = pa[name], pb[name]
        if ra["fen"] != rb["fen"]:
            bad.append((name, "fen", ra["fen"], rb["fen"]))
            continue
        for f in EXACT_FIELDS:
            if ra[f] != rb[f]:
                bad.append((name, f, ra[f], rb[f]))
        for f in FLOAT_FIELDS:
            if abs(ra[f] - rb[f]) > tol:
                bad.append((name, f, ra[f], rb[f]))
    if bad:
        print(f"FAIL {len(bad)} difference(s), tolerance {tol:g} on {FLOAT_FIELDS}:")
        for name, f, x, y in bad[:40]:
            print(f"  {name:<22} {f:<16} A={x!r}  B={y!r}")
        return 1
    same_hash = a.get("values_sha256") == b.get("values_sha256")
    print(f"PASS {len(pa)} positions identical "
          f"({'values hash equal' if same_hash else 'values hash differs only in float formatting'})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, "migration", "reference_windows.json"))
    ap.add_argument("--with-cct", action="store_true",
                    help="also record the provisional C28 capture-tree numbers (informational)")
    ap.add_argument("--compare", nargs=2, metavar=("A.json", "B.json"))
    args = ap.parse_args()
    if args.compare:
        return compare(*args.compare)
    res = measure(corpus(), args.with_cct)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(dict(out=args.out, positions=len(res["positions"]), seconds=res["seconds"],
                          values_sha256=res["values_sha256"], platform=res["platform"]), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
