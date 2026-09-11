"""Fit K0 for RC-J's evaluator (E0), fit the linear correction E1, and report static metrics.

Implements DESIGN.md sections 5-6 (static part). Lambda is chosen on validation; the test split
is read once, after lambda is frozen. Writes weights and metrics to the results directory.

    .venv/Scripts/python.exe benchmarks/current/learned_eval/scripts/train_eval.py DATA_DIR LABELS.jsonl OUT_DIR
"""
import argparse
import collections
import json
import math
import os
import sys

import chess
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import features as F  # noqa: E402

LAMBDAS = [0.0, 1e-4, 1e-3, 1e-2, 1e-1]
FAMILIES = {
    "material": range(0, 5), "mobility": range(5, 9), "pawns": range(9, 17), "rooks": range(17, 20),
    "king": range(20, 24), "space": range(24, 25), "minor": range(25, 27), "threats": range(27, 31),
}
EPS = 1e-6


def bce(p, y):
    p = np.clip(p, EPS, 1 - EPS)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def fit_k(ev, y):
    """Golden-section search for K minimising mean BCE of sigmoid(ev / K) against y."""
    lo, hi = math.log(20.0), math.log(5000.0)
    g = (math.sqrt(5) - 1) / 2
    f = lambda lk: float(bce(sig(ev / math.exp(lk)), y).mean())
    a, b = lo, hi
    c, d = b - g * (b - a), a + g * (b - a)
    for _ in range(80):
        if f(c) < f(d):
            b = d
        else:
            a = c
        c, d = b - g * (b - a), a + g * (b - a)
    return math.exp((a + b) / 2)


def design(X, ph):
    m = (ph / 24.0)[:, None]
    return np.hstack([X * m, X * (1 - m), m, 1 - m])


def train_w(Z, e0, y, K, lam, mask_cols=None):
    Zt = torch.tensor(Z, dtype=torch.float64)
    e0t = torch.tensor(e0, dtype=torch.float64)
    yt = torch.tensor(y, dtype=torch.float64)
    w = torch.zeros(Z.shape[1], dtype=torch.float64, requires_grad=True)
    keep = torch.ones(Z.shape[1], dtype=torch.float64)
    if mask_cols is not None:
        keep[list(mask_cols)] = 0.0
    opt = torch.optim.LBFGS([w], lr=1.0, max_iter=500, tolerance_grad=1e-10, tolerance_change=1e-12,
                            history_size=50, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        z = (e0t + Zt @ (w * keep)) / K
        loss = torch.nn.functional.binary_cross_entropy_with_logits(z, yt) + lam * ((w * keep / 100.0) ** 2).sum()
        loss.backward()
        return loss

    opt.step(closure)
    return (w * keep).detach().numpy()


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def metrics(ev, K, rows_idx, y, cp, groups=None):
    ev, yy, cpp = ev[rows_idx], y[rows_idx], cp[rows_idx]
    p = sig(ev / K)
    out = dict(n=int(len(rows_idx)), bce=float(bce(p, yy).mean()), mse=float(((p - yy) ** 2).mean()))
    ok = ~np.isnan(cpp)
    out["pearson_cp"] = float(np.corrcoef(ev[ok], np.clip(cpp[ok], -1000, 1000))[0, 1])
    out["spearman_cp"] = spearman(ev[ok], cpp[ok])
    lg = np.log(np.clip(yy, 0.001, 0.999) / (1 - np.clip(yy, 0.001, 0.999)))
    out["pearson_logitE"] = float(np.corrcoef(ev, lg)[0, 1])
    dec = np.abs(yy - 0.5) >= 0.15
    out["sign_acc"] = float(np.mean(np.sign(ev[dec]) == np.sign(yy[dec] - 0.5))) if dec.any() else None
    out["sign_n"] = int(dec.sum())
    return out


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
    quiet = np.zeros(len(rows), dtype=bool)
    for i, (r, b) in enumerate(zip(rows, boards)):
        bm = r["lab"]["bestmove"]
        if bm is None:
            continue
        mv = chess.Move.from_uci(bm)
        quiet[i] = not b.is_capture(mv) and mv.promotion is None and not b.is_check()
    X, PH, E0 = F.extract(boards)
    E0 = E0.astype(np.float64)
    y = np.array([r["lab"]["E"] for r in rows], dtype=np.float64)
    cp = np.array([np.nan if r["lab"]["cp"] is None else r["lab"]["cp"] for r in rows], dtype=np.float64)
    split = np.array([r["split"] for r in rows])
    Z = design(X.astype(np.float64), PH.astype(np.float64))
    idx = {s: np.where((split == s) & quiet)[0] for s in ("train", "val", "test")}
    idx_all = {s: np.where(split == s)[0] for s in ("train", "val", "test")}
    tr = idx["train"]

    K0 = fit_k(E0[tr], y[tr])
    grid = []
    for lam in LAMBDAS:
        w = train_w(Z[tr], E0[tr], y[tr], K0, lam)
        e1 = E0 + Z @ w
        grid.append(dict(lam=lam, train_bce=float(bce(sig(e1[tr] / K0), y[tr]).mean()),
                         val_bce=float(bce(sig(e1[idx["val"]] / K0), y[idx["val"]]).mean()), w=w))
    best = min(grid, key=lambda g: g["val_bce"])
    lam, w = best["lam"], best["w"]
    E1 = E0 + Z @ w
    K1 = fit_k(E1[tr], y[tr])
    Kc = fit_k(1.5 * E0[tr], y[tr])

    # Feature-family ablation on validation only (feature usefulness, not model selection).
    nf = F.NF
    ablation = {}
    for fam, cols in FAMILIES.items():
        mask = set(cols) | {nf + c for c in cols}
        wa = train_w(Z[tr], E0[tr], y[tr], K0, lam, mask_cols=mask)
        ea = E0 + Z @ wa
        ablation[fam] = float(bce(sig(ea[idx["val"]] / K0), y[idx["val"]]).mean()) - best["val_bce"]

    res = dict(n_rows=len(rows), n_quiet=int(quiet.sum()), K0=K0, K1_refit=K1, K_control_1p5=Kc, lam=lam,
               lambda_grid=[{k: v for k, v in g.items() if k != "w"} for g in grid],
               val_ablation_bce_increase=ablation, splits={}, strata={}, bootstrap={})
    for s in ("train", "val", "test"):
        res["splits"][s] = dict(
            E0=metrics(E0, K0, idx[s], y, cp), E1_atK0=metrics(E1, K0, idx[s], y, cp),
            E1=metrics(E1, K1, idx[s], y, cp), control_E0x1p5=metrics(1.5 * E0, Kc, idx[s], y, cp),
            E0_allpositions=metrics(E0, K0, idx_all[s], y, cp), E1_allpositions=metrics(E1, K1, idx_all[s], y, cp))

    te = idx["test"]
    fam = np.array([r["family"] for r in rows])
    bal = np.abs(y - 0.5)
    strata = {
        "balance<0.1": bal < 0.1, "balance0.1-0.3": (bal >= 0.1) & (bal < 0.3), "balance>=0.3": bal >= 0.3,
        "phase>=16": PH >= 16, "phase8-15": (PH >= 8) & (PH < 16), "phase<8": PH < 8,
    }
    for f in ("TWIC", "PUBLIC", "VS_SF", "SELFPLAY"):
        strata["family_" + f] = fam == f
    for name, m in strata.items():
        sel = te[m[te]]
        if len(sel) >= 20:
            res["strata"][name] = dict(E0=metrics(E0, K0, sel, y, cp), E1=metrics(E1, K1, sel, y, cp))

    # Bootstrap by test group for the E1 - E0 differences (calibrated, each with its own K).
    groups = np.array([r["group"] for r in rows])
    d_bce = bce(sig(E1 / K1), y) - bce(sig(E0 / K0), y)
    d_mse = (sig(E1 / K1) - y) ** 2 - (sig(E0 / K0) - y) ** 2
    by_group = collections.defaultdict(list)
    for i in te:
        by_group[groups[i]].append(i)
    keys = sorted(by_group)
    rng = np.random.default_rng(20260911)
    boots = {"bce": [], "mse": [], "rel_bce": []}
    base_bce = bce(sig(E0 / K0), y)
    for _ in range(1000):
        pick = rng.integers(0, len(keys), len(keys))
        ii = np.concatenate([by_group[keys[k]] for k in pick])
        boots["bce"].append(d_bce[ii].mean())
        boots["mse"].append(d_mse[ii].mean())
        boots["rel_bce"].append(d_bce[ii].mean() / base_bce[ii].mean())
    for k, v in boots.items():
        res["bootstrap"][k] = dict(point=float({"bce": d_bce[te].mean(), "mse": d_mse[te].mean(),
                                                 "rel_bce": d_bce[te].mean() / base_bce[te].mean()}[k]),
                                   lo=float(np.percentile(v, 2.5)), hi=float(np.percentile(v, 97.5)))
    res["test_groups"] = len(keys)

    names = list(F.NAMES)
    weights = dict(names=names, w_mg=w[:nf].tolist(), w_eg=w[nf:2 * nf].tolist(),
                   intercept_mg=float(w[2 * nf]), intercept_eg=float(w[2 * nf + 1]), K0=K0, lam=lam,
                   feature_version="features.py v1 (31 stm-relative features)",
                   W=w.tolist())
    with open(os.path.join(a.out, "e1_weights.json"), "w", encoding="utf-8") as fh:
        json.dump(weights, fh, indent=1)
    with open(os.path.join(a.out, "static_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: res[k] for k in ("n_rows", "n_quiet", "K0", "K1_refit", "K_control_1p5", "lam",
                                           "bootstrap", "test_groups")}, indent=1))
    for s in ("train", "val", "test"):
        sp = res["splits"][s]
        print(s, {k: (round(sp[k]["bce"], 5), round(sp[k]["mse"], 5), round(sp[k]["spearman_cp"], 4))
                  for k in ("E0", "E1", "control_E0x1p5")})
    print("weights (mg, eg):")
    for j, n in enumerate(names):
        print(f"  {n:24s} {w[j]:+8.1f} {w[nf + j]:+8.1f}")
    print(f"  {'intercept':24s} {w[2 * nf]:+8.1f} {w[2 * nf + 1]:+8.1f}")
    print("val ablation (BCE increase when family dropped):", {k: round(v, 5) for k, v in ablation.items()})


if __name__ == "__main__":
    main()
