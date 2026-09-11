"""Magnitude audit of N1q before the test opens (DESIGN_N1.md sections 8 step 3 and 10).

RC-J consumers of evaluation magnitude (cs_core.py / cs_fast.py, RC-J 2bf6885):
  reverse futility       static - 120 * depth >= beta, depth <= 3, non-PV        cs_core.py:1330-1334
  quiescence stand-pat   stand_pat >= beta cut; alpha raise                       cs_core.py:1203-1210
  delta pruning          stand_pat + victim value + 200 < alpha                    cs_core.py:1228-1235
  aspiration windows     previous +/- 30, doubling to 800                          cs_fast.py:28-30, 273-295
  TT score field         16 bits with +32768 offset; |score| must stay < 32768     cs_core.py:1077, 1086-1087
  mate guards            |score| > MATE_BOUND 29000 treated as mate                cs_core.py:1100-1115, 1331
  draw score / root rule 0; a drawing root move is played only if best < 0         cs_fast.py:243-245
  mop-up                 bare-king gradient up to 180, inside E0                   cs_core.py:814-837
  instability counter    |score change| >= 50 between iterations (reporting only)  cs_fast.py:217-220
Null move, LMR and the time manager do not read the evaluation (the time manager uses phase).

Criteria (all required; any failure = MAGNITUDE-INCOMPATIBLE):
  A  p99 |f| <= 250 cp in every phase band at sampled evaluate call sites (audit build, depth-10
     searches of the 24 openings, depth-8 searches of 300 validation roots)
  B  |mean f| <= 10 cp on the validation balanced band (quiet, |E - 0.5| < 0.10)
  C  slope of N1q on E0 over validation positions in [0.8, 1.25] per phase band
  D  N1q's own phase link refitted on train ∩ quiet: K_mg and K_eg within +/-10% of the frozen link
  E  analytic max |f| over all inputs <= 3,000 cp; no W1 parameter clipped in quantisation
  F  20 seeded bare-king positions (10 KQK, 10 KRK), each engine against itself at 200 ms/move:
     N1 mates every position RC-J mates, in at most RC-J's plies + 10

    audit_n1.py DATA_DIR RESULTS_N1_DIR
"""
import json
import os
import random
import subprocess
import sys

import chess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diag_phasek as D  # noqa: E402
import engine_n1  # noqa: E402
import features as F  # noqa: E402
import nn1  # noqa: E402
import nn1kit  # noqa: E402
import train_n1 as TN  # noqa: E402

PY = sys.executable
BANDS = (("phase>=16", 16, 99), ("phase8-15", 8, 16), ("phase<8", 0, 8))


def bare_king_positions():
    rng = random.Random("N1-20260911|mate")
    out = []
    for piece, n in ((chess.QUEEN, 10), (chess.ROOK, 10)):
        while n:
            sq = rng.sample(range(64), 3)
            b = chess.Board(None)
            b.set_piece_at(sq[0], chess.Piece(chess.KING, chess.WHITE))
            b.set_piece_at(sq[1], chess.Piece(piece, chess.WHITE))
            b.set_piece_at(sq[2], chess.Piece(chess.KING, chess.BLACK))
            b.turn = chess.WHITE
            if b.is_valid() and not b.is_game_over() and not b.is_check() and len(list(b.legal_moves)) > 3:
                out.append(b.fen())
                n -= 1
    return out


def main():
    data, res = sys.argv[1], sys.argv[2]
    fl, Q = nn1.load(os.path.join(res, "n1_weights.npz"))
    calib = json.load(open(os.path.join(res, "calibration.json"), encoding="utf-8"))
    acc = json.load(open(os.path.join(res, "acceptance.json"), encoding="utf-8"))
    K = (calib["K_mg"], calib["K_eg"])
    eng_dir = os.path.join(data, "engines")
    audit_eng = os.path.join(eng_dir, "n1_audit_frozen")
    real_eng = os.path.join(eng_dir, "n1_real_frozen")
    engine_n1.build(audit_eng, Q, "audit")
    if not os.path.exists(real_eng):
        engine_n1.build(real_eng, Q, "real")
    out = dict()

    va_all = TN.load_split(data, "val", os.path.join(data, "labels_val_1m.jsonl"))
    va = TN.sub(va_all, va_all["quiet"])
    roots = [r["fen"] for r in va["rows"]]
    random.Random("N1-20260911|audit").shuffle(roots)
    rp = os.path.join(data, "audit_roots.json")
    json.dump(roots[:300], open(rp, "w", encoding="utf-8"))
    ap = os.path.join(data, "audit_callsites.json")
    subprocess.run([PY, os.path.join(HERE, "audit_probe.py"), audit_eng, rp, ap], check=True)
    cs = json.load(open(ap, encoding="utf-8"))
    f = np.array([r["f"] for r in cs["rows"]], dtype=np.float64)
    ph = np.array([r["phase"] for r in cs["rows"]])
    A = {}
    for name, lo, hi in BANDS:
        m = (ph >= lo) & (ph < hi)
        v = f[m]
        if len(v) == 0:
            A[name] = dict(n=0, p99_abs=None, note="no sampled call site in this band: criterion not verifiable")
            continue
        A[name] = dict(n=int(m.sum()), mean=float(v.mean()), sd=float(v.std()), p1=float(np.percentile(v, 1)),
                       p99=float(np.percentile(v, 99)), p99_abs=float(np.percentile(np.abs(v), 99)),
                       max_abs=float(np.abs(v).max()))
    out["A_callsites"] = dict(evaluate_calls=cs["evaluate_calls"], sampled=cs["sampled"], bands=A,
                              share_abs_f_ge_30=float(np.mean(np.abs(f) >= 30)),
                              share_abs_f_ge_120=float(np.mean(np.abs(f) >= 120)),
                              share_abs_f_ge_200=float(np.mean(np.abs(f) >= 200)),
                              passed=all(b["p99_abs"] is not None and b["p99_abs"] <= 250 for b in A.values()))

    BB, SS, STM = F.arrays_from_boards(va_all["boards"])
    _, QP = nn1kit.params(fl, Q)
    fv = np.array([nn1kit.nnq_cp(BB[i], STM[i], *QP) for i in range(len(STM))], dtype=np.float64)
    band = va_all["quiet"] & (np.abs(va_all["y"] - 0.5) < 0.10)
    out["B_balanced_mean_f"] = dict(mean=float(fv[band].mean()), n=int(band.sum()),
                                    passed=abs(float(fv[band].mean())) <= 10)

    C = {}
    for name, lo, hi in BANDS:
        m = (va_all["ph"] >= lo) & (va_all["ph"] < hi)
        C[name] = float(np.polyfit(va_all["e0"][m], va_all["e0"][m] + fv[m], 1)[0])
    out["C_slopes"] = dict(bands=C, passed=all(0.8 <= s <= 1.25 for s in C.values()))

    tr_all = TN.load_split(data, "train", os.path.join(data, "labels_train_50k.jsonl"))
    tr = TN.sub(tr_all, tr_all["quiet"])
    BBt, SSt, STMt = F.arrays_from_boards(tr["boards"])
    ft = np.array([nn1kit.nnq_cp(BBt[i], STMt[i], *QP) for i in range(len(STMt))], dtype=np.float64)
    Kn = D.fit_phase_k(tr["e0"] + ft, tr["ph"], tr["y"])
    out["D_own_link"] = dict(K_frozen=K, K_N1q=Kn, rel=[Kn[0] / K[0] - 1, Kn[1] / K[1] - 1],
                             passed=abs(Kn[0] / K[0] - 1) <= 0.10 and abs(Kn[1] / K[1] - 1) <= 0.10)

    w3, b3 = Q["w3q"].astype(np.int64), int(Q["b3q"][0])
    lo = nn1.trunc_div(100 * (b3 + 255 * int(np.minimum(w3, 0).sum())), nn1.OUT_DEN)
    hi = nn1.trunc_div(100 * (b3 + 255 * int(np.maximum(w3, 0).sum())), nn1.OUT_DEN)
    out["E_analytic"] = dict(f_min=lo, f_max=hi, W1_clipped=acc["clip_counts"]["W1"],
                             passed=max(abs(lo), abs(hi)) <= 3000 and acc["clip_counts"]["W1"] == 0)

    mp = os.path.join(data, "mate_positions.json")
    json.dump(bare_king_positions(), open(mp, "w", encoding="utf-8"))
    mres = {}
    for name, eng in (("rcj", engine_n1.ROOT), ("n1", real_eng)):
        o = os.path.join(data, f"mate_{name}.json")
        subprocess.run([PY, os.path.join(HERE, "mate_probe.py"), eng, mp, o], check=True)
        mres[name] = json.load(open(o, encoding="utf-8"))
    ok = True
    for a, b in zip(mres["rcj"], mres["n1"]):
        if a["mated"] and (not b["mated"] or b["plies"] > a["plies"] + 10):
            ok = False
    out["F_bare_king"] = dict(rcj_mated=sum(r["mated"] for r in mres["rcj"]), n1_mated=sum(r["mated"] for r in mres["n1"]),
                              rcj_plies=[r["plies"] for r in mres["rcj"]], n1_plies=[r["plies"] for r in mres["n1"]],
                              passed=ok)
    out["passed"] = all(v["passed"] for k, v in out.items() if isinstance(v, dict) and "passed" in v)
    with open(os.path.join(res, "magnitude_audit.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
