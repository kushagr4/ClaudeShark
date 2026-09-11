"""Open the sealed N1 test split once and judge the static gates (DESIGN_N1.md section 9).

Requires the freeze manifest. N1q (the quantised runtime network) against E0, test split, 1M
labels. Bootstrap: 1,000 paired resamples of test groups (same draws for both models), seed
20260911, percentile 2.5/97.5; relative BCE = ratio of resampled means.

    gates_n1.py DATA_DIR RESULTS_N1_DIR PILOT_DATA_DIR
"""
import collections
import hashlib
import json
import os
import sys
import time

import chess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import features as F  # noqa: E402
import freeze_n1 as FZ  # noqa: E402
import nn1  # noqa: E402
import nn1kit  # noqa: E402
import pairs_n1  # noqa: E402
import train_n1 as T  # noqa: E402

BAL = 0.10
NB = 1000


class Boot:
    """Paired group bootstrap: one set of group draws reused for every statistic."""

    def __init__(self, groups, seed=20260911):
        self.groups = np.asarray(groups)
        keys = sorted(set(self.groups.tolist()))
        index = {k: i for i, k in enumerate(keys)}
        gi = np.array([index[g] for g in self.groups])
        rng = np.random.default_rng(seed)
        draws = rng.integers(0, len(keys), (NB, len(keys)))
        self.weights = np.zeros((NB, len(self.groups)))
        for b in range(NB):
            counts = np.bincount(draws[b], minlength=len(keys))
            self.weights[b] = counts[gi]
        self.n_groups = len(keys)

    def mean(self, v, mask=None):
        v = np.asarray(v, dtype=np.float64)
        w = self.weights if mask is None else self.weights * mask
        return (w * v).sum(1) / np.maximum(w.sum(1), 1e-12)

    def ci(self, stats, point):
        return dict(point=float(point), lo=float(np.percentile(stats, 2.5)), hi=float(np.percentile(stats, 97.5)),
                    groups=self.n_groups)


def spearman_w(x, y, w):
    """Spearman correlation with integer bootstrap weights (repeat each observation w times)."""
    idx = np.repeat(np.arange(len(x)), w.astype(np.int64))
    if len(idx) < 3:
        return np.nan
    return T.spearman(x[idx], y[idx])


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    data, res, pilot = sys.argv[1], sys.argv[2], sys.argv[3]
    freeze_path = os.path.join(res, "freeze.json")
    assert os.path.exists(freeze_path), "no freeze manifest: the test split stays sealed"
    fz = json.load(open(freeze_path, encoding="utf-8"))
    assert sha256(os.path.join(res, "n1_weights.npz")) == fz["files"]["n1_weights.npz"], "weights changed after freeze"
    sealed = os.path.join(data, "test_sealed")
    fl, Q = nn1.load(os.path.join(res, "n1_weights.npz"))
    calib = json.load(open(os.path.join(res, "calibration.json"), encoding="utf-8"))
    K, s_star = (calib["K_mg"], calib["K_eg"]), calib["shrink_s_star"]
    out = dict(opened=time.strftime("%Y-%m-%d %H:%M:%S"), freeze_sha256=sha256(freeze_path))

    te_all = T.load_split(data, "test", os.path.join(sealed, "labels_test_1m.jsonl"))
    BB, SS, STM = F.arrays_from_boards(te_all["boards"])
    _, QP = nn1kit.params(fl, Q)
    fq_all = np.array([nn1kit.nnq_cp(BB[i], STM[i], *QP) for i in range(len(STM))], dtype=np.float64)
    q = te_all["quiet"]
    te = T.sub(te_all, q)
    fq = fq_all[q]
    e0, y, ph, cp = te["e0"], te["y"], te["ph"], te["cp"]
    ev1 = e0 + fq
    groups = [r["group"] for r in te["rows"]]
    bt = Boot(groups)
    band = np.abs(y - 0.5) < BAL
    mid = (np.abs(y - 0.5) >= BAL) & (np.abs(y - 0.5) < 0.30)
    cell = FZ.cells(ph, te["boards"])
    p0a, p1a = T.probs(e0, ph, K), T.probs(ev1, ph, K)
    p0b, p1b = FZ.probs_rich(e0, cell, fz["rich_links"]["E0"]), FZ.probs_rich(ev1, cell, fz["rich_links"]["N1q"])
    out["n"] = dict(quiet=int(len(y)), all=int(len(te_all["y"])), band=int(band.sum()), mid=int(mid.sum()),
                    groups=bt.n_groups)

    def rel_bce(p0, p1, mask=None):
        b0, b1 = T.bce(p0, y), T.bce(p1, y)
        m = np.ones(len(y)) if mask is None else mask.astype(np.float64)
        stats = bt.mean(b1, m) / bt.mean(b0, m)
        sel = slice(None) if mask is None else mask
        return bt.ci(stats - 1, b1[sel].mean() / b0[sel].mean() - 1)

    g1a, g1b = rel_bce(p0a, p1a), rel_bce(p0b, p1b)
    out["G1"] = dict(link_a=g1a, link_b=g1b, passed=g1a["hi"] < 0 and g1b["hi"] < 0)

    def band_mse_diff(p0, p1):
        d = (p1 - y) ** 2 - (p0 - y) ** 2
        return bt.ci(bt.mean(d, band.astype(float)), d[band].mean())

    g2i_a, g2i_b = band_mse_diff(p0a, p1a), band_mse_diff(p0b, p1b)
    pshr = T.probs(s_star * e0, ph, K)
    g2ii = band_mse_diff(pshr, p1a)
    ok = band & ~np.isnan(cp)
    cpc = np.clip(np.nan_to_num(cp), -300, 300)
    sp_stats = np.array([spearman_w(ev1[ok], cpc[ok], bt.weights[b][ok]) - spearman_w(e0[ok], cpc[ok], bt.weights[b][ok])
                         for b in range(NB)])
    g2iii = bt.ci(sp_stats, T.spearman(ev1[ok], cpc[ok]) - T.spearman(e0[ok], cpc[ok]))
    ratio = float(np.median(np.abs(ev1[band])) / max(1e-9, np.median(np.abs(e0[band]))))
    bb0, bb1 = T.bce(p0a, y), T.bce(p1a, y)
    band_bce = float(bb1[band].mean() / bb0[band].mean() - 1)
    mid_bce = float(bb1[mid].mean() / bb0[mid].mean() - 1)
    out["G2"] = dict(i_link_a=g2i_a, i_link_b=g2i_b, ii_shrink=dict(s_star=s_star, **g2ii), iii_spearman=g2iii,
                     iv_magnitude_ratio=ratio, v_band_bce_rel=band_bce, v_mid_bce_rel=mid_bce,
                     band_mse=dict(E0=float(((p0a - y)[band] ** 2).mean()), N1q=float(((p1a - y)[band] ** 2).mean()),
                                   shrink=float(((pshr - y)[band] ** 2).mean())))
    out["G2"]["passed"] = (g2i_a["hi"] < 0 and g2i_b["hi"] < 0 and g2ii["hi"] < 0 and g2iii["lo"] > 0
                           and 0.8 <= ratio <= 1.25 and band_bce <= 0 and mid_bce <= 0.01)

    roots, plab = pairs_n1.load(os.path.join(sealed, "pairs"), "test")
    sc = nn1kit.NNScorer(fl=fl, Q=Q)
    items = pairs_n1.score(roots, plab, sc, [0, 2])
    pb = Boot([it["group"] for it in items])
    dq = np.array([int(it["qs2"]) - int(it["qs0"]) for it in items], dtype=np.float64)
    g3i = pb.ci(pb.mean(dq), dq.mean())
    balm = np.array([abs(it["root_E"] - 0.5) < BAL for it in items], dtype=np.float64)
    g3ii = pb.ci(pb.mean(dq, balm), dq[balm.astype(bool)].mean() if balm.any() else np.nan)
    q0 = np.array([sc.root(te["boards"][i], 0)[1] for i in np.where(band)[0]], dtype=np.float64)
    q1 = np.array([sc.root(te["boards"][i], 2)[1] for i in np.where(band)[0]], dtype=np.float64)
    dqs = np.zeros(len(y))
    dqs[band] = (T.probs(q1, ph[band], K) - y[band]) ** 2 - (T.probs(q0, ph[band], K) - y[band]) ** 2
    g3iii = bt.ci(bt.mean(dqs, band.astype(float)), dqs[band].mean())
    underpowered = g3i["lo"] <= 0 <= g3i["hi"] and g3i["hi"] >= 0.02
    out["G3"] = dict(pairs=len(items), balanced_root_pairs=int(balm.sum()),
                     qs_acc=dict(E0=float(np.mean([it["qs0"] for it in items])), N1q=float(np.mean([it["qs2"] for it in items]))),
                     static_acc=dict(E0=float(np.mean([it["static0"] for it in items])),
                                     N1q=float(np.mean([it["static2"] for it in items]))),
                     i_all_pairs=g3i, ii_balanced_roots=g3ii, iii_qs_root_band_mse=g3iii, underpowered=underpowered)
    out["G3"]["passed"] = g3i["lo"] > 0 and g3ii["lo"] >= -0.01 and g3iii["hi"] < 0

    nq = ~q
    b0n = T.bce(T.probs(te_all["e0"][nq], te_all["ph"][nq], K), te_all["y"][nq])
    b1n = T.bce(T.probs(te_all["e0"][nq] + fq_all[nq], te_all["ph"][nq], K), te_all["y"][nq])
    out["G4"] = dict(n=int(nq.sum()), nonquiet_bce_rel=float(b1n.mean() / b0n.mean() - 1))
    out["G4"]["passed"] = out["G4"]["nonquiet_bce_rel"] <= 0.01

    out["static_pass"] = all(out[g]["passed"] for g in ("G1", "G2", "G3", "G4"))
    others_pass = all(out[g]["passed"] for g in ("G1", "G2", "G4")) and out["G3"]["ii_balanced_roots"]["lo"] >= -0.01 \
        and out["G3"]["iii_qs_root_band_mse"]["hi"] < 0
    out["static_label"] = "PASS" if out["static_pass"] else ("UNKNOWN/UNDERPOWERED" if underpowered and others_pass else "FAIL")

    # Sensitivity flags (not gates).
    fam = np.array([r["family"] for r in te["rows"]])
    tw = fam == "TWIC"
    sens = {}
    if tw.sum() > 50:
        btw = Boot(np.array(groups)[tw])
        b0, b1 = T.bce(p0a, y)[tw], T.bce(p1a, y)[tw]
        d = ((p1a - y) ** 2 - (p0a - y) ** 2)[tw]
        bm = band[tw].astype(float)
        sens["twic_only"] = dict(G1=btw.ci(btw.mean(b1) / btw.mean(b0) - 1, b1.mean() / b0.mean() - 1),
                                 G2i=btw.ci(btw.mean(d, bm), d[band[tw]].mean()))
        sens["twic_only"]["cluster_driven_flag"] = not (sens["twic_only"]["G1"]["hi"] < 0 and sens["twic_only"]["G2i"]["hi"] < 0)
    prow = [json.loads(l) for l in open(os.path.join(pilot, "pool.jsonl"), encoding="utf-8")]
    seen = {r["group"] for r in prow if r["split"] in ("val", "test")}
    unseen = np.array([g not in seen for g in groups])
    if unseen.sum() > 50:
        bu = Boot(np.array(groups)[unseen])
        b0, b1 = T.bce(p0a, y)[unseen], T.bce(p1a, y)[unseen]
        d = ((p1a - y) ** 2 - (p0a - y) ** 2)[unseen]
        sens["pilot_unseen"] = dict(n=int(unseen.sum()), G1=bu.ci(bu.mean(b1) / bu.mean(b0) - 1, b1.mean() / b0.mean() - 1),
                                    G2i=bu.ci(bu.mean(d, band[unseen].astype(float)), d[band[unseen]].mean()))
    sens["groups_per_family"] = {f: len({g for g, ff in zip(groups, fam) if ff == f}) for f in sorted(set(fam))}
    out["sensitivity"] = sens

    strata = {}
    for name, m in (("phase>=16", ph >= 16), ("phase8-15", (ph >= 8) & (ph < 16)), ("phase<8", ph < 8),
                    ("balance<0.1", band), ("balance0.1-0.3", mid), ("balance>=0.3", np.abs(y - 0.5) >= 0.30),
                    *[(f"family_{f}", fam == f) for f in ("TWIC", "PUBLIC", "VS_SF", "SELFPLAY")]):
        if m.sum() >= 20:
            strata[name] = dict(n=int(m.sum()), bce_E0=float(T.bce(p0a, y)[m].mean()), bce_N1q=float(T.bce(p1a, y)[m].mean()),
                                mse_E0=float(((p0a - y)[m] ** 2).mean()), mse_N1q=float(((p1a - y)[m] ** 2).mean()))
    kinds = collections.defaultdict(list)
    for it in items:
        kinds[it["kind"]].append(it)
        if it["quiet"]:
            kinds["quiet_pairs"].append(it)
    ff = np.array([nn1.float_forward_cp(*nn1.board_features(b), fl) for b in te["boards"]])
    out["reported"] = dict(
        strata=strata, float_bce_rel_link_a=float(T.bce(T.probs(e0 + ff, ph, K), y).mean() / T.bce(p0a, y).mean() - 1),
        spearman_cp_all=dict(E0=T.spearman(e0[~np.isnan(cp)], cp[~np.isnan(cp)]),
                             N1q=T.spearman(ev1[~np.isnan(cp)], cp[~np.isnan(cp)])),
        pair_kinds={k: dict(n=len(v), qs_E0=float(np.mean([x["qs0"] for x in v])), qs_N1q=float(np.mean([x["qs2"] for x in v])),
                            static_E0=float(np.mean([x["static0"] for x in v])),
                            static_N1q=float(np.mean([x["static2"] for x in v]))) for k, v in kinds.items()})
    with open(os.path.join(res, "test_gates.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: out[k] for k in ("opened", "n", "G1", "G2", "G3", "G4", "static_pass", "static_label")}, indent=1))


if __name__ == "__main__":
    main()
