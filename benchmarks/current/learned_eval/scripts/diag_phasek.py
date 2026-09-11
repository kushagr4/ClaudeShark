"""POST-HOC diagnostic, not part of the preregistered verdict: how much of E1's gain is calibration?

Stockfish's WDL model is material-dependent, so one sigmoid scale K cannot map the same
centipawn edge to the same expected score in a middlegame and an endgame. With E0's coefficient
fixed at 1, the preregistered E1 can absorb that through its material counts (it came out with
material scaled roughly 0.6x in the middlegame and 1.3x in the endgame), which is a units change,
not chess knowledge. This script gives E0 a phase-dependent scale first,

    p = sigmoid(eval * (ph/24 / K_mg + (24 - ph)/24 / K_eg)),

then refits the correction on top of that (E1b), and once more without the material family (E1c).
The E1b - E0(phase-K) difference is the part of the gain a per-phase rescaling cannot explain.

    diag_phasek.py DATA_DIR LABELS.jsonl OUT_DIR
"""
import argparse
import collections
import json
import os
import sys

import chess
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import features as F  # noqa: E402
import train_eval as T  # noqa: E402


def inv_k(ph, kmg, keg):
    m = ph / 24.0
    return m / kmg + (1 - m) / keg


def fit_phase_k(ev, ph, y):
    ev_t, ph_t, y_t = (torch.tensor(v, dtype=torch.float64) for v in (ev, ph, y))
    lk = torch.tensor([np.log(160.0), np.log(160.0)], dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([lk], lr=1.0, max_iter=200, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        m = ph_t / 24.0
        z = ev_t * (m / torch.exp(lk[0]) + (1 - m) / torch.exp(lk[1]))
        loss = torch.nn.functional.binary_cross_entropy_with_logits(z, y_t)
        loss.backward()
        return loss

    opt.step(closure)
    return float(np.exp(lk[0].item())), float(np.exp(lk[1].item()))


def train_w_phase(Z, e0, ph, y, kmg, keg, lam, mask=None):
    Zt, e0t, yt = (torch.tensor(v, dtype=torch.float64) for v in (Z, e0, y))
    ik = torch.tensor(inv_k(ph, kmg, keg), dtype=torch.float64)
    keep = torch.ones(Z.shape[1], dtype=torch.float64)
    if mask:
        keep[list(mask)] = 0.0
    w = torch.zeros(Z.shape[1], dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([w], lr=1.0, max_iter=500, tolerance_grad=1e-10, tolerance_change=1e-12,
                            history_size=50, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        z = (e0t + Zt @ (w * keep)) * ik
        loss = torch.nn.functional.binary_cross_entropy_with_logits(z, yt) + lam * ((w * keep / 100.0) ** 2).sum()
        loss.backward()
        return loss

    opt.step(closure)
    return (w * keep).detach().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("labels")
    ap.add_argument("out")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    pool = {r["pid"]: r for r in map(json.loads, open(os.path.join(a.data, "pool.jsonl"), encoding="utf-8"))}
    labels = {r["pid"]: r for r in map(json.loads, open(a.labels, encoding="utf-8"))}
    rows = [dict(pool[p], lab=labels[p]) for p in pool if p in labels and labels[p]["E"] is not None]
    boards = [chess.Board(r["fen"]) for r in rows]
    quiet = np.array([r["lab"]["bestmove"] is not None and not b.is_capture(chess.Move.from_uci(r["lab"]["bestmove"]))
                      and chess.Move.from_uci(r["lab"]["bestmove"]).promotion is None for r, b in zip(rows, boards)])
    X, PH, E0 = F.extract(boards)
    E0, PH = E0.astype(float), PH.astype(float)
    y = np.array([r["lab"]["E"] for r in rows])
    split = np.array([r["split"] for r in rows])
    groups = np.array([r["group"] for r in rows])
    Z = T.design(X.astype(float), PH)
    idx = {s: np.where((split == s) & quiet)[0] for s in ("train", "val", "test")}
    tr, va, te = idx["train"], idx["val"], idx["test"]

    def loss_at(ev, kk, ii):
        return T.bce(T.sig(ev[ii] * inv_k(PH[ii], *kk)), y[ii])

    k0 = fit_phase_k(E0[tr], PH[tr], y[tr])
    material = set(range(0, 5)) | {F.NF + j for j in range(0, 5)}
    out = dict(E0_phaseK=dict(K_mg=k0[0], K_eg=k0[1]), models={})
    per_pos = {"E0_phaseK": loss_at(E0, k0, np.arange(len(y)))}
    for name, mask in (("E1b_phaseK", None), ("E1c_phaseK_no_material", material)):
        best = None
        for lam in T.LAMBDAS:
            w = train_w_phase(Z[tr], E0[tr], PH[tr], y[tr], *k0, lam, mask)
            ev = E0 + Z @ w
            v = float(loss_at(ev, k0, va).mean())
            if best is None or v < best[0]:
                best = (v, lam, w)
        _, lam, w = best
        ev = E0 + Z @ w
        kk = fit_phase_k(ev[tr], PH[tr], y[tr])
        per_pos[name] = loss_at(ev, kk, np.arange(len(y)))
        out["models"][name] = dict(lam=lam, K_mg=kk[0], K_eg=kk[1],
                                   w_mg=dict(zip(F.NAMES, np.round(w[:F.NF], 1).tolist())),
                                   w_eg=dict(zip(F.NAMES, np.round(w[F.NF:2 * F.NF], 1).tolist())),
                                   intercepts=[round(float(w[-2]), 1), round(float(w[-1]), 1)], W=w.tolist())
        with open(os.path.join(a.out, f"{name}_weights.json"), "w", encoding="utf-8") as fh:
            json.dump(dict(W=w.tolist(), names=list(F.NAMES), lam=lam, K_mg=kk[0], K_eg=kk[1],
                           note="POST-HOC diagnostic model; not the preregistered E1"), fh, indent=1)

    base_single = T.bce(T.sig(E0 / T.fit_k(E0[tr], y[tr])), y)
    out["test_bce"] = dict(E0_singleK=float(base_single[te].mean()),
                           **{k: float(v[te].mean()) for k, v in per_pos.items()})
    out["val_bce"] = dict(E0_singleK=float(base_single[va].mean()), **{k: float(v[va].mean()) for k, v in per_pos.items()})
    by = collections.defaultdict(list)
    for i in te:
        by[groups[i]].append(i)
    keys = sorted(by)
    rng = np.random.default_rng(20260911)
    for name in ("E1b_phaseK", "E1c_phaseK_no_material"):
        d = per_pos[name] - per_pos["E0_phaseK"]
        bs = []
        for _ in range(1000):
            ii = np.concatenate([by[keys[k]] for k in rng.integers(0, len(keys), len(keys))])
            bs.append(d[ii].mean() / per_pos["E0_phaseK"][ii].mean())
        out[f"{name}_vs_E0_phaseK_rel_bce"] = dict(point=float(d[te].mean() / per_pos["E0_phaseK"][te].mean()),
                                                    lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)))
    with open(os.path.join(a.out, "diag_phasek.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "models"}, indent=1))
    for name, m in out["models"].items():
        print(name, "lam", m["lam"], "material mg", {k: m["w_mg"][k] for k in F.NAMES[:5]},
              "eg", {k: m["w_eg"][k] for k in F.NAMES[:5]})


if __name__ == "__main__":
    main()
