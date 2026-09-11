"""Write the N1 freeze manifest (DESIGN_N1.md section 8, steps 4-5). No test data is read.

Requires acceptance.json (passed) and magnitude_audit.json. Fits the rich link family (section 4b:
one scale per phase band x pawn-count bucket) on validation ∩ quiet, separately for E0 and N1q,
and records hashes of every frozen input and script. Every later test step checks this file.

    freeze_n1.py DATA_DIR RESULTS_N1_DIR
"""
import hashlib
import json
import os
import sys
import time

import chess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PHASE_BANDS = ((16, 99), (8, 16), (0, 8))
PAWN_BUCKETS = ((0, 9), (9, 13), (13, 99))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cells(ph, boards):
    pawns = np.array([chess.popcount(b.pawns) for b in boards])
    c = np.zeros(len(ph), dtype=np.int64)
    for i, (lo, hi) in enumerate(PHASE_BANDS):
        for j, (plo, phi) in enumerate(PAWN_BUCKETS):
            c[(ph >= lo) & (ph < hi) & (pawns >= plo) & (pawns < phi)] = 3 * i + j
    return c


def fit_rich(ev, cell, y):
    import train_eval as T
    ks = []
    for k in range(9):
        m = cell == k
        ks.append(T.fit_k(ev[m], y[m]) if m.sum() >= 30 else T.fit_k(ev, y))
    return ks


def probs_rich(ev, cell, ks):
    k = np.array(ks)[cell]
    return 1.0 / (1.0 + np.exp(-ev / k))


def main():
    data, res = sys.argv[1], sys.argv[2]
    import features as F
    import nn1
    import nn1kit
    import train_n1 as TN
    acc = json.load(open(os.path.join(res, "acceptance.json"), encoding="utf-8"))
    if not acc["passed"]:
        print("N1q acceptance FAILED: no freeze manifest; the test is never opened (DESIGN_N1.md section 8)")
        sys.exit(1)
    audit_path = os.path.join(res, "magnitude_audit.json")
    assert os.path.exists(audit_path), "run audit_n1.py first"
    audit = json.load(open(audit_path, encoding="utf-8"))
    fl, Q = nn1.load(os.path.join(res, "n1_weights.npz"))
    va_all = TN.load_split(data, "val", os.path.join(data, "labels_val_1m.jsonl"))
    va = TN.sub(va_all, va_all["quiet"])
    BB, SS, STM = F.arrays_from_boards(va["boards"])
    _, QP = nn1kit.params(fl, Q)
    qcp = np.array([nn1kit.nnq_cp(BB[i], STM[i], *QP) for i in range(len(STM))], dtype=np.float64)
    cell = cells(va["ph"], va["boards"])
    rich = dict(E0=fit_rich(va["e0"], cell, va["y"]), N1q=fit_rich(va["e0"] + qcp, cell, va["y"]),
                phase_bands=PHASE_BANDS, pawn_buckets=PAWN_BUCKETS, fitted_on="validation quiet, 1M labels")
    files = {n: sha256(os.path.join(res, n)) for n in ("n1_weights.npz", "calibration.json", "selection.json",
                                                         "acceptance.json", "magnitude_audit.json")}
    scripts = {n: sha256(os.path.join(HERE, n)) for n in ("engine_n1.py", "nn1.py", "nn1kit.py", "features.py", "train_n1.py",
                                                            "gates_n1.py", "pairs_n1.py", "speed_n1.py", "regress_n1.py",
                                                            "holdout_n1.py", "freeze_n1.py", "audit_n1.py")}
    sel = json.load(open(os.path.join(res, "selection.json"), encoding="utf-8"))
    manifest = dict(frozen_at=time.strftime("%Y-%m-%d %H:%M:%S"), chosen=sel["chosen"], validation_fail=sel["validation_fail"],
                    acceptance_passed=acc["passed"], magnitude_audit_passed=audit["passed"], rich_links=rich,
                    files=files, scripts=scripts, rule="after any test label is read: no retraining, reselection, "
                    "re-quantisation, link refit, weight edit or threshold change")
    with open(os.path.join(res, "freeze.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("scripts",)}, indent=1))


if __name__ == "__main__":
    main()
