"""Material-only tuning: ten tapered piece values, everything else frozen.

Texel-style. The model is the production evaluator with its five middlegame
and five endgame material values replaced by ``production + delta``; every
piece-square table, the bishop pair and tempo are held exactly as they are. The
target is the oracle's expected score from WDL, through a sigmoid whose scale K
was fitted on the current evaluator, so a mate or a +2000 position contributes
a bounded, sensible amount instead of dominating a least-squares fit.

Regularisation is a ridge penalty on the *deltas*, so with strong lambda the
answer is "the values you already have", and the tuner has to earn every
centipawn of movement with validation improvement. Bounds keep each value inside
a chess-plausible band of its production value. Ordering (queen > rook > minor >
pawn) is checked rather than enforced; a fit that violates it is reported as
implausible rather than silently clipped into shape.

Lambda is chosen on the validation split. The test split is touched once, at
the end, for the chosen lambda only.

    uv run python -m tools.tune.material
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from tools.tune.audit import fit_k, material_design, quiet_mask, robust_metrics
from tools.tune.dataset import load_split
from tools.tune.features import EG_VALUE, MG_VALUE, PIECE_NAMES, load

# Plausibility band around production values: a fit outside this is rejected
# as a chess value regardless of what it does to the loss.
LOWER = 0.6
UPPER = 1.5
# Scale for the ridge penalty: a 100 cp move on any value costs the same.
DELTA_SCALE = 100.0


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def fit(
    x: np.ndarray, base: np.ndarray, es: np.ndarray, k: float, lam: float,
    steps: int = 4000, lr: float = 2.0,
) -> np.ndarray:
    """Adam on mean squared expected-score error plus ridge on deltas.

    ``x`` is the tapered material design (n, 10), ``base`` the current
    evaluator's white-POV score, so the model is ``base + x @ delta``.
    """
    prod = np.concatenate([MG_VALUE, EG_VALUE])
    lo = prod * LOWER - prod
    hi = prod * UPPER - prod
    delta = np.zeros(10)
    m = np.zeros(10)
    v = np.zeros(10)
    b1, b2, eps = 0.9, 0.999, 1e-8
    n = len(es)
    for step in range(1, steps + 1):
        pred = base + x @ delta
        s = sigmoid(pred / k)
        err = s - es
        # d loss / d delta  (loss = mean err^2 + lam * sum((delta/scale)^2))
        dl_dpred = 2.0 * err * s * (1.0 - s) / k
        grad = x.T @ dl_dpred / n + 2.0 * lam * delta / (DELTA_SCALE**2)
        m = b1 * m + (1 - b1) * grad
        v = b2 * v + (1 - b2) * grad * grad
        mh = m / (1 - b1**step)
        vh = v / (1 - b2**step)
        delta -= lr * mh / (np.sqrt(vh) + eps)
        delta = np.clip(delta, lo, hi)
    return delta


def plausibility(mg: np.ndarray, eg: np.ndarray) -> list[str]:
    """Named exchanges a tuned set must not make pathological."""
    p, n_, b, r, q = mg
    pe, ne, be, re_, qe = eg
    checks = [
        ("Q vs 2R (MG)", q - 2 * r), ("Q vs 2R (EG)", qe - 2 * re_),
        ("Q vs R+B (MG)", q - (r + b)), ("Q vs R+B (EG)", qe - (re_ + be)),
        ("R vs B+N (MG)", r - (b + n_)), ("R vs B+N (EG)", re_ - (be + ne)),
        ("B vs N (MG)", b - n_), ("B vs N (EG)", be - ne),
        ("3P vs N (MG)", 3 * p - n_), ("3P vs N (EG)", 3 * pe - ne),
        ("R vs N+2P (MG)", r - (n_ + 2 * p)), ("R vs N+2P (EG)", re_ - (ne + 2 * pe)),
        ("exchange R-B (MG)", r - b), ("exchange R-B (EG)", re_ - be),
    ]
    lines = ["| balance | value (cp) |", "|---|---|"]
    lines += [f"| {name} | {val:+.0f} |" for name, val in checks]
    order_ok = q > r > max(b, n_) > p and qe > re_ > max(be, ne) > pe
    lines.append(f"\nordering Q > R > minor > P in both phases: **{'yes' if order_ok else 'NO'}**")
    return lines


def main() -> None:
    # Windows consoles default to cp1252, which cannot print the Greek and
    # box characters in these tables; the files are always UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Fit tapered material values.")
    parser.add_argument("--labelled", type=Path, default=Path("corpus/candidates_labelled.jsonl"))
    parser.add_argument("--quiet-tol", type=int, default=30)
    parser.add_argument("--out", type=Path, default=Path("corpus/tune/material.md"))
    arguments = parser.parse_args()

    d = load(arguments.labelled)
    assign = load_split()
    split = np.array([assign[g] for g in d["game_ids"]])
    k = fit_k(d["static"], d["oracle_es"])
    x = material_design(d)

    out: list[str] = ["# Material-only fit", "",
                      f"K = {k:.0f} cp. Ten parameters, everything else frozen. Ridge on deltas, "
                      f"bounds [{LOWER:.1f}x, {UPPER:.1f}x] of production.", ""]
    results = {}

    subsets = (
        ("all positions", np.ones(len(x), bool)),
        (f"quiet (tol {arguments.quiet_tol})", quiet_mask(d, arguments.quiet_tol)),
    )
    for subset_name, submask in subsets:
        tr = submask & (split == "train")
        va = submask & (split == "val")
        te = submask & (split == "test")
        out += [f"## Subset: {subset_name}  (train {int(tr.sum())}, val {int(va.sum())}, "
                f"test {int(te.sum())})", ""]

        base_val = robust_metrics(d["static"][va], d["oracle_cp"][va], d["oracle_es"][va], k)
        out += ["### Lambda sweep (selected on validation)", "",
                "| lambda | ‖delta‖ max | val ES-MSE | val MAE | val Huber "
                "| Δ ES-MSE vs current |",
                "|---|---|---|---|---|---|"]
        best_lam, best_loss, best_delta = None, float("inf"), None
        for lam in (100.0, 30.0, 10.0, 3.0, 1.0, 0.3, 0.1, 0.03, 0.0):
            delta = fit(x[tr], d["static"][tr], d["oracle_es"][tr], k, lam)
            pred_val = d["static"][va] + x[va] @ delta
            r = robust_metrics(pred_val, d["oracle_cp"][va], d["oracle_es"][va], k)
            out.append(f"| {lam:g} | {np.abs(delta).max():.0f} | {r['es_mse']:.5f} | "
                       f"{r['mae']:.1f} | {r['huber']:.0f} | "
                       f"{r['es_mse'] - base_val['es_mse']:+.5f} |")
            if r["es_mse"] < best_loss:
                best_loss, best_lam, best_delta = r["es_mse"], lam, delta
        assert best_delta is not None
        out.append(f"| current | 0 | {base_val['es_mse']:.5f} | {base_val['mae']:.1f} | "
                   f"{base_val['huber']:.0f} | — |")

        # Prefer the strongest regularisation within 2% of the best validation loss:
        # tiny improvements do not justify large weight movement.
        chosen_lam, chosen_delta = best_lam, best_delta
        for lam in (100.0, 30.0, 10.0, 3.0, 1.0, 0.3, 0.1, 0.03, 0.0):
            delta = fit(x[tr], d["static"][tr], d["oracle_es"][tr], k, lam)
            r = robust_metrics(d["static"][va] + x[va] @ delta, d["oracle_cp"][va],
                               d["oracle_es"][va], k)
            if r["es_mse"] <= best_loss * 1.02:
                chosen_lam, chosen_delta = lam, delta
                break

        mg = MG_VALUE + chosen_delta[:5]
        eg = EG_VALUE + chosen_delta[5:]
        out += ["", f"### Chosen lambda = {chosen_lam:g} "
                "(strongest within 2% of best validation loss)", "",
                "| piece | MG now | MG fit | Δ | EG now | EG fit | Δ |",
                "|---|---|---|---|---|---|---|"]
        for i, p in enumerate(PIECE_NAMES):
            out.append(f"| {p} | {MG_VALUE[i]:.0f} | {mg[i]:.0f} | {chosen_delta[i]:+.0f} | "
                       f"{EG_VALUE[i]:.0f} | {eg[i]:.0f} | {chosen_delta[5 + i]:+.0f} |")

        out += ["", "### Held-out test (touched once)", "",
                "| set | ES-MSE now | ES-MSE fit | MAE now | MAE fit | Huber now | Huber fit |",
                "|---|---|---|---|---|---|---|"]
        for name, m in (("train", tr), ("val", va), ("test", te)):
            a = robust_metrics(d["static"][m], d["oracle_cp"][m], d["oracle_es"][m], k)
            b = robust_metrics(d["static"][m] + x[m] @ chosen_delta, d["oracle_cp"][m],
                               d["oracle_es"][m], k)
            out.append(f"| {name} | {a['es_mse']:.5f} | {b['es_mse']:.5f} | {a['mae']:.1f} | "
                       f"{b['mae']:.1f} | {a['huber']:.0f} | {b['huber']:.0f} |")

        out += ["", "### Chess plausibility", "", *plausibility(mg, eg), ""]
        results[subset_name] = {
            "lambda": chosen_lam, "k": k,
            "mg": [round(v) for v in mg], "eg": [round(v) for v in eg],
            "delta": [float(v) for v in chosen_delta],
        }

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    (arguments.out.parent / "material_candidates.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
