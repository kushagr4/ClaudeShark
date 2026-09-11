"""Train N1 under natural (U) and balanced-aware (B) weighting, select on validation, quantise, accept.

Implements DESIGN_N1.md sections 4 (link a), 6, 7 and 8 (steps 1-2). Reads only the train (50k)
and validation (1M) labels and the validation pairs; the test split and the RC-J holdout are never
opened here. Writes n1_weights.npz / n1_weights.json, calibration.json, selection.json and
acceptance.json. The magnitude audit, rich-link fits and freeze manifest are separate steps.

    train_n1.py DATA_DIR OUT_DIR
"""
import collections
import hashlib
import json
import os
import sys
import time

import chess
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diag_phasek as D  # noqa: E402  (fit_phase_k, inv_k)
import features as F  # noqa: E402
import nn1  # noqa: E402
import nn1kit  # noqa: E402
import pairs_n1  # noqa: E402

SEED = 20260911
BAL = 0.10
SHRINK_GRID = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class N1(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.emb = torch.nn.EmbeddingBag(nn1.N_IN + 1, nn1.N_ACC, mode="sum", padding_idx=nn1.PAD)
        self.b1 = torch.nn.Parameter(torch.full((nn1.N_ACC,), 0.5))
        self.l2 = torch.nn.Linear(2 * nn1.N_ACC, nn1.N_H2)
        self.l3 = torch.nn.Linear(nn1.N_H2, 1)
        with torch.no_grad():
            self.emb.weight.normal_(0.0, 0.05)
            self.emb.weight[nn1.PAD].zero_()
            self.l3.weight.zero_()
            self.l3.bias.zero_()

    def forward(self, xs, xo):
        a_s = torch.clamp(self.emb(xs) + self.b1, 0.0, 1.0)
        a_o = torch.clamp(self.emb(xo) + self.b1, 0.0, 1.0)
        h2 = torch.clamp(self.l2(torch.cat([a_s, a_o], 1)), 0.0, 1.0)
        return 100.0 * self.l3(h2).squeeze(1)

    def export(self):
        return dict(W1=self.emb.weight[:nn1.N_IN].detach().numpy().astype(np.float64),
                    b1=self.b1.detach().numpy().astype(np.float64),
                    W2=self.l2.weight.detach().numpy().astype(np.float64),
                    b2=self.l2.bias.detach().numpy().astype(np.float64),
                    w3=self.l3.weight.detach().numpy()[0].astype(np.float64),
                    b3=np.float64(self.l3.bias.detach().numpy()[0]))


def load_split(data, split, labels_path):
    labels = {r["pid"]: r for r in map(json.loads, open(labels_path, encoding="utf-8"))}
    rows = [json.loads(l) for l in open(os.path.join(data, "pool.jsonl"), encoding="utf-8")]
    rows = [dict(r, lab=labels[r["pid"]]) for r in rows
            if r["split"] == split and r["pid"] in labels and labels[r["pid"]]["E"] is not None]
    boards = [chess.Board(r["fen"]) for r in rows]
    quiet = np.array([r["lab"]["bestmove"] is not None and not b.is_capture(chess.Move.from_uci(r["lab"]["bestmove"]))
                      and chess.Move.from_uci(r["lab"]["bestmove"]).promotion is None for r, b in zip(rows, boards)])
    _, PH, E0 = F.extract(boards)
    xs, xo = nn1.batch_features(boards)
    y = np.array([r["lab"]["E"] for r in rows], dtype=np.float64)
    cp = np.array([np.nan if r["lab"]["cp"] is None else r["lab"]["cp"] for r in rows], dtype=np.float64)
    return dict(rows=rows, boards=boards, quiet=quiet, ph=PH.astype(np.float64), e0=E0.astype(np.float64),
                xs=xs, xo=xo, y=y, cp=cp)


def sub(d, mask):
    return {k: (v[mask] if isinstance(v, np.ndarray) else [x for x, m in zip(v, mask) if m]) for k, v in d.items()}


def bce(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def probs(ev, ph, K):
    return 1.0 / (1.0 + np.exp(-ev * D.inv_k(ph, *K)))


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def predict(model, d):
    with torch.no_grad():
        return model(torch.tensor(d["xs"]), torch.tensor(d["xo"])).numpy().astype(np.float64)


def shrink_s(e0, ph, y, K):
    band = np.abs(y - 0.5) < BAL
    return min(SHRINK_GRID, key=lambda s: float(((probs(s * e0[band], ph[band], K) - y[band]) ** 2).mean()))


def band_metrics(ev, d, K, s_star):
    """Validation versions of the G2 quantities (points) for evaluation ev on quiet subset d."""
    y, ph, e0 = d["y"], d["ph"], d["e0"]
    p, p0 = probs(ev, ph, K), probs(e0, ph, K)
    band = np.abs(y - 0.5) < BAL
    mid = (np.abs(y - 0.5) >= BAL) & (np.abs(y - 0.5) < 0.30)
    ok = band & ~np.isnan(d["cp"])
    pc = probs(s_star * e0, ph, K)
    return dict(bce=float(bce(p, y).mean()), mse=float(((p - y) ** 2).mean()),
                band_mse=float(((p[band] - y[band]) ** 2).mean()),
                band_mse_E0=float(((p0[band] - y[band]) ** 2).mean()),
                band_mse_shrink=float(((pc[band] - y[band]) ** 2).mean()),
                band_bce_rel=float(bce(p[band], y[band]).mean() / bce(p0[band], y[band]).mean() - 1),
                mid_bce_rel=float(bce(p[mid], y[mid]).mean() / bce(p0[mid], y[mid]).mean() - 1),
                band_spearman=spearman(ev[ok], np.clip(d["cp"][ok], -300, 300)),
                band_spearman_E0=spearman(e0[ok], np.clip(d["cp"][ok], -300, 300)),
                band_magnitude_ratio=float(np.median(np.abs(ev[band])) / max(1e-9, np.median(np.abs(e0[band])))),
                n=int(len(y)), n_band=int(band.sum()))


def eligible(m, pair_acc, pair_acc_e0):
    return (m["band_mse"] < m["band_mse_E0"] and m["band_mse"] < m["band_mse_shrink"]
            and m["band_spearman"] > m["band_spearman_E0"] and 0.8 <= m["band_magnitude_ratio"] <= 1.25
            and m["band_bce_rel"] <= 0 and m["mid_bce_rel"] <= 0.01 and pair_acc > pair_acc_e0)


def train_run(tr, va, K, weighting, log):
    torch.manual_seed(SEED)
    model = N1()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    xs, xo = torch.tensor(tr["xs"]), torch.tensor(tr["xo"])
    e0 = torch.tensor(tr["e0"], dtype=torch.float32)
    ik = torch.tensor(D.inv_k(tr["ph"], *K), dtype=torch.float32)
    y = torch.tensor(tr["y"], dtype=torch.float32)
    w = np.ones(len(tr["y"]))
    if weighting == "B":
        w[np.abs(tr["y"] - 0.5) < BAL] = 2.0
    w = torch.tensor(w / w.mean(), dtype=torch.float32)
    gen = torch.Generator().manual_seed(SEED)
    best, best_state, since, history = np.inf, None, 0, []
    lim = 127.0 / 64.0
    for epoch in range(60):
        model.train()
        perm = torch.randperm(len(y), generator=gen)
        tot = 0.0
        for i in range(0, len(y), 1024):
            idx = perm[i:i + 1024]
            f = model(xs[idx], xo[idx])
            loss = (w[idx] * torch.nn.functional.binary_cross_entropy_with_logits(
                (e0[idx] + f) * ik[idx], y[idx], reduction="none")).sum() / w[idx].sum()
            opt.zero_grad()
            loss.backward()
            opt.step()
            with torch.no_grad():
                model.l2.weight.clamp_(-lim, lim)
            tot += float(loss) * len(idx)
        model.eval()
        v = float(bce(probs(va["e0"] + predict(model, va), va["ph"], K), va["y"]).mean())
        history.append(dict(epoch=epoch, train_loss=tot / len(y), val_bce=v))
        log(f"  {weighting} epoch {epoch:2d} train {tot / len(y):.5f} val {v:.5f}")
        if v < best - 1e-7:
            best, since = v, 0
            best_state = {k: t.clone() for k, t in model.state_dict().items()}
        else:
            since += 1
            if since >= 6:
                break
    model.load_state_dict(best_state)
    model.eval()
    return model, history, min(range(len(history)), key=lambda i: history[i]["val_bce"])


def main():
    data, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    t0 = time.time()
    lines = []

    def log(s):
        print(s, flush=True)
        lines.append(s)

    ltr = os.path.join(data, "labels_train_50k.jsonl")
    lva = os.path.join(data, "labels_val_1m.jsonl")
    pool_split = {json.loads(l)["pid"]: json.loads(l)["split"] for l in open(os.path.join(data, "pool.jsonl"), encoding="utf-8")}
    tr_pids = {json.loads(l)["pid"] for l in open(ltr, encoding="utf-8")}
    assert all(pool_split.get(p) == "train" for p in tr_pids), "train label file contains a non-train pid"
    assert not os.path.exists(os.path.join(data, "labels_test_1m.jsonl")), "test labels outside the sealed directory"
    tr_all = load_split(data, "train", ltr)
    va_all = load_split(data, "val", lva)
    tr, va = sub(tr_all, tr_all["quiet"]), sub(va_all, va_all["quiet"])
    log(f"train quiet {len(tr['y'])} of {len(tr_all['y'])}; val quiet {len(va['y'])} of {len(va_all['y'])}")

    K = D.fit_phase_k(tr["e0"], tr["ph"], tr["y"])
    Kc = D.fit_phase_k(1.5 * tr["e0"], tr["ph"], tr["y"])
    s_star = shrink_s(tr["e0"], tr["ph"], tr["y"], K)
    calib = dict(K_mg=K[0], K_eg=K[1], fitted_on="train quiet, E0, 50k labels", shrink_s_star=s_star,
                 control_E0x1p5_val_bce=float(bce(probs(1.5 * va["e0"], va["ph"], Kc), va["y"]).mean()),
                 E0_val_bce=float(bce(probs(va["e0"], va["ph"], K), va["y"]).mean()))
    with open(os.path.join(out, "calibration.json"), "w", encoding="utf-8") as fh:
        json.dump(calib, fh, indent=1)
    log(f"frozen link K_mg {K[0]:.1f} K_eg {K[1]:.1f}; shrink s* {s_star}; control {calib['control_E0x1p5_val_bce']:.6f}"
        f" vs E0 {calib['E0_val_bce']:.6f}")

    pdir = os.path.join(data, "pairs")
    roots, plab = pairs_n1.load(pdir, "val")
    e0_items = pairs_n1.score(roots, plab, nn1kit.NNScorer(), [0])
    e0_pair = float(np.mean([it["qs0"] for it in e0_items]))
    runs = dict(E0=dict(band_metrics(va["e0"], va, K, s_star), pair_qs_acc=e0_pair, pairs=len(e0_items)))
    models = {}
    for wmode in ("U", "B"):
        model, hist, best_epoch = train_run(tr, va, K, wmode, log)
        fl = model.export()
        ev = va["e0"] + predict(model, va)
        m = band_metrics(ev, va, K, s_star)
        items = pairs_n1.score(roots, plab, nn1kit.NNScorer(fl=fl), [1])
        m.update(pair_qs_acc=float(np.mean([it["qs1"] for it in items])), best_epoch=best_epoch, epochs_run=len(hist))
        m["eligible"] = eligible(m, m["pair_qs_acc"], e0_pair)
        runs[wmode] = m
        models[wmode] = (model, fl, hist, ev)
        log(f"{wmode}: {json.dumps(m)}")

    # Section 7 choice.
    y = va["y"]
    band = np.abs(y - 0.5) < BAL
    groups = np.array([r["group"] for r in va["rows"]])
    d_band = ((probs(models["B"][3], va["ph"], K) - y) ** 2 - (probs(models["U"][3], va["ph"], K) - y) ** 2)[band]
    gb = groups[band]
    by = collections.defaultdict(list)
    for v, g in zip(d_band, gb):
        by[g].append(v)
    keys = sorted(by)
    rng = np.random.default_rng(SEED)
    bs = [np.mean(np.concatenate([by[keys[k]] for k in rng.integers(0, len(keys), len(keys))])) for _ in range(1000)]
    se = float(np.std(bs))
    eu, eb = runs["U"]["eligible"], runs["B"]["eligible"]
    if eu and eb:
        chosen = "B" if float(d_band.mean()) < -se else "U"
    elif eu or eb:
        chosen = "U" if eu else "B"
    else:
        chosen = "U"
    validation_fail = not (eu or eb)
    sel = dict(runs=runs, band_mse_B_minus_U=float(d_band.mean()), paired_bootstrap_se=se, chosen=chosen,
               validation_fail=validation_fail, shrink_s_star=s_star)
    with open(os.path.join(out, "selection.json"), "w", encoding="utf-8") as fh:
        json.dump(sel, fh, indent=1)
    log(f"selection: chosen {chosen}; eligible U {eu} B {eb}; B-U band mse {d_band.mean():.6f} se {se:.6f}")

    model, fl, hist, _ = models[chosen]
    Q = nn1.quantise(fl)
    clips = dict(W1=int((np.abs(fl["W1"] * nn1.QA) > 32767).sum()), W2=int((np.abs(fl["W2"] * nn1.QB) > 127.5).sum()))
    BB, SS, STM = F.arrays_from_boards(va_all["boards"])
    _, QP = nn1kit.params(fl, Q)
    qcp_all = np.array([nn1kit.nnq_cp(BB[i], STM[i], *QP) for i in range(len(STM))], dtype=np.float64)
    fcp_all = predict(model, va_all)
    qcp = qcp_all[va_all["quiet"]]
    mq = band_metrics(va["e0"] + qcp, va, K, s_star)
    mf = band_metrics(va["e0"] + predict(model, va), va, K, s_star)
    qitems = pairs_n1.score(roots, plab, nn1kit.NNScorer(fl=fl, Q=Q), [1, 2])
    agree = float(np.mean([it["qs1"] == it["qs2"] for it in qitems]))
    acc = dict(float_band_mse=mf["band_mse"], quant_band_mse=mq["band_mse"],
               band_mse_rel_diff=abs(mq["band_mse"] - mf["band_mse"]) / mf["band_mse"],
               max_abs_cp_diff=float(np.abs(qcp_all - fcp_all).max()), mean_abs_cp_diff=float(np.abs(qcp_all - fcp_all).mean()),
               pair_agreement=agree, quant_pair_qs_acc=float(np.mean([it["qs2"] for it in qitems])),
               clip_counts=clips, quant_metrics=mq)
    acc["passed"] = acc["band_mse_rel_diff"] <= 0.02 and acc["max_abs_cp_diff"] <= 10 and agree >= 0.99
    with open(os.path.join(out, "acceptance.json"), "w", encoding="utf-8") as fh:
        json.dump(acc, fh, indent=1)
    log(f"N1q acceptance: {json.dumps({k: v for k, v in acc.items() if k != 'quant_metrics'})}")

    meta = dict(architecture="N1 residual: 768 -> 2x128 CReLU -> 32 CReLU -> 1 (cp), added to E0",
                parameters=int(sum(p.numel() for p in model.parameters()) - nn1.N_ACC), chosen=chosen,
                validation_fail=validation_fail, calibration=calib, seed=SEED, history=hist,
                labels={"train_50k": sha256(ltr), "val_1m": sha256(lva), "val_pairs": sha256(os.path.join(pdir, "val_pair_labels.jsonl"))},
                pool_sha256=sha256(os.path.join(data, "pool.jsonl")), torch=torch.__version__,
                seconds=round(time.time() - t0, 1), test_opened=False, holdout_opened=False)
    nn1.save(os.path.join(out, "n1_weights.npz"), fl, Q, meta)
    for w in ("U", "B"):
        with open(os.path.join(out, f"history_{w}.json"), "w", encoding="utf-8") as fh:
            json.dump(models[w][2], fh, indent=1)
    with open(os.path.join(out, "train_log.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    log(f"weights sha256 {sha256(os.path.join(out, 'n1_weights.npz'))}; acceptance {'PASS' if acc['passed'] else 'FAIL'}")


if __name__ == "__main__":
    main()
