"""POST-HOC diagnostic: test-split loss by balance band for E0, E1 and the phase-K variants.

The preregistered E1 improved unbalanced positions and was worse on near-balanced ones. This
checks whether the calibration-corrected variants (E1b, E1c from diag_phasek.py) behave the same
way on the near-balanced band, where RC-J's real-loss errors begin.

    diag_strata.py DATA_DIR LABELS.jsonl RESULTS_DIR
"""
import json
import os
import sys

import chess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diag_phasek as D  # noqa: E402
import features as F  # noqa: E402
import train_eval as T  # noqa: E402


def main():
    data, labels_path, res_dir = sys.argv[1:4]
    pool = {r["pid"]: r for r in map(json.loads, open(os.path.join(data, "pool.jsonl"), encoding="utf-8"))}
    labels = {r["pid"]: r for r in map(json.loads, open(labels_path, encoding="utf-8"))}
    rows = [dict(pool[p], lab=labels[p]) for p in pool if p in labels and labels[p]["E"] is not None]
    boards = [chess.Board(r["fen"]) for r in rows]
    quiet = np.array([r["lab"]["bestmove"] is not None and not b.is_capture(chess.Move.from_uci(r["lab"]["bestmove"]))
                      and chess.Move.from_uci(r["lab"]["bestmove"]).promotion is None for r, b in zip(rows, boards)])
    X, PH, E0 = F.extract(boards)
    E0, PH = E0.astype(float), PH.astype(float)
    y = np.array([r["lab"]["E"] for r in rows])
    split = np.array([r["split"] for r in rows])
    Z = T.design(X.astype(float), PH)
    tr = np.where((split == "train") & quiet)[0]
    te = np.where((split == "test") & quiet)[0]

    def load_w(path):
        return np.array(json.load(open(path, encoding="utf-8"))["W"])

    evs = {"E0": E0, "E1": E0 + Z @ load_w(os.path.join(res_dir, "e1_weights.json")),
           "E1b": E0 + Z @ load_w(os.path.join(res_dir, "diag_phasek", "E1b_phaseK_weights.json")),
           "E1c": E0 + Z @ load_w(os.path.join(res_dir, "diag_phasek", "E1c_phaseK_no_material_weights.json"))}
    probs = {}
    for name, ev in evs.items():
        k = T.fit_k(ev[tr], y[tr])
        probs[name + "_singleK"] = T.sig(ev / k)
        kk = D.fit_phase_k(ev[tr], PH[tr], y[tr])
        probs[name + "_phaseK"] = T.sig(ev * D.inv_k(PH, *kk))
    bal = np.abs(y - 0.5)
    bands = {"balance<0.1": bal < 0.1, "balance0.1-0.3": (bal >= 0.1) & (bal < 0.3), "balance>=0.3": bal >= 0.3,
             "all": np.ones(len(y), dtype=bool)}
    out = {}
    for band, m in bands.items():
        sel = te[m[te]]
        out[band] = dict(n=int(len(sel)), **{name: dict(bce=round(float(T.bce(p[sel], y[sel]).mean()), 4),
                                                         mse=round(float(((p[sel] - y[sel]) ** 2).mean()), 4))
                                             for name, p in probs.items()})
    with open(os.path.join(res_dir, "diag_phasek", "diag_strata.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    for band, v in out.items():
        print(band, "n", v["n"], {k: (x["bce"], x["mse"]) for k, x in v.items() if k != "n"})


if __name__ == "__main__":
    main()
