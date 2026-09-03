"""One-parameter material scale: is material underweighted against the tables?

The ten-parameter fit preserved the current relative piece ratios almost
exactly while pushing four parameters onto their bounds. That is the signature
of a model with one real degree of freedom wearing ten, so this fits the one:

    material_contribution_new = s * material_contribution_current

with every piece-square table, the bishop pair and tempo untouched. The scaled
values are rounded to integers once, at candidate construction, so the shipped
form is a constant change and costs nothing at runtime.

s is chosen on the **validation** split alone; the test split is read once,
afterwards, for the chosen s only.

**The sigmoid scale K is refitted on the training split at every s**, and that
is not a detail. Holding K fixed conflates two different things: scaling
material makes the evaluator's *units* bigger, which improves an
expected-score fit for free, and it also changes the *balance* between material
and the piece-square tables, which is the only part that can change a move.
With K fixed the curve runs monotonically off the edge of any grid and reports
-11.4%; with K free it has an interior optimum worth about -2.6%. The gap
between those numbers is calibration, not chess.

The whole-evaluator scale is the control that proves it. It is statically
decision-invariant, and with K free its curve is flat to four decimal places --
s and K are the same knob. Any move-quality difference a uniform scale produces
in the real engine is therefore search-margin calibration (aspiration widths
and delta margins stay in centipawns) and must never be counted as an
evaluation improvement.

    uv run python -m tools.tune.scale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from tools.tune.audit import material_design, quiet_mask, robust_metrics
from tools.tune.dataset import load_split
from tools.tune.features import EG_VALUE, MG_VALUE, PIECE_NAMES, load

CANDIDATES = Path("corpus/tune/material_candidates.json")


def scaled_constants(s: float) -> tuple[list[int], list[int]]:
    """Integer MG/EG constants for a given scale, rounded once."""
    return ([round(v * s) for v in MG_VALUE], [round(v * s) for v in EG_VALUE])


def _mse(pred: np.ndarray, es: np.ndarray, k: float) -> float:
    return float(((1.0 / (1.0 + np.exp(-pred / k)) - es) ** 2).mean())


def _best_k(pred: np.ndarray, es: np.ndarray) -> float:
    ks = np.arange(60.0, 1200.0, 2.0)
    return float(ks[int(np.argmin([_mse(pred, es, k) for k in ks]))])


def curves(
    d: dict[str, np.ndarray], train: np.ndarray, val: np.ndarray, material: np.ndarray,
    grid: np.ndarray, whole: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Train loss, validation loss and the K fitted on train, at each s."""
    tr_loss = np.empty(len(grid))
    va_loss = np.empty(len(grid))
    ks = np.empty(len(grid))
    static = d["static"]
    es = d["oracle_es"]
    for i, s in enumerate(grid):
        if whole:
            pred_tr = s * static[train]
            pred_va = s * static[val]
        else:
            pred_tr = static[train] + (s - 1.0) * material[train]
            pred_va = static[val] + (s - 1.0) * material[val]
        k = _best_k(pred_tr, es[train])
        ks[i] = k
        tr_loss[i] = _mse(pred_tr, es[train], k)
        va_loss[i] = _mse(pred_va, es[val], k)
    return tr_loss, va_loss, ks


def plateau(grid: np.ndarray, values: np.ndarray, tol: float = 0.01) -> tuple[float, float]:
    """Range of s whose loss is within ``tol`` (relative) of the best."""
    best = values.min()
    inside = grid[values <= best * (1.0 + tol)]
    return float(inside.min()), float(inside.max())


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Fit a one-parameter material scale.")
    parser.add_argument("--labelled", type=Path, default=Path("corpus/candidates_labelled.jsonl"))
    parser.add_argument("--quiet-tol", type=int, default=30)
    parser.add_argument("--lo", type=float, default=1.00)
    parser.add_argument("--hi", type=float, default=2.20)
    parser.add_argument("--step", type=float, default=0.01)
    parser.add_argument("--out", type=Path, default=Path("corpus/tune/scale.md"))
    arguments = parser.parse_args()

    d = load(arguments.labelled)
    assign = load_split()
    split = np.array([assign[g] for g in d["game_ids"]])
    x = material_design(d)
    material = x @ np.concatenate([MG_VALUE, EG_VALUE])
    grid = np.round(np.arange(arguments.lo, arguments.hi + 1e-9, arguments.step), 4)
    quiet = quiet_mask(d, arguments.quiet_tol)

    out: list[str] = [
        "# One-parameter material scale", "",
        f"Grid s in [{arguments.lo}, {arguments.hi}] step {arguments.step}. K refitted on "
        "train at every s. Selected on validation; test read once afterwards.", "",
        "The quiet subset is the fitting set: a static evaluator is only meaningfully "
        "compared with an oracle where no tactic is pending. The all-positions curve is "
        "a robustness check, not the selector.", "",
    ]

    selected: dict[str, float] = {}
    selected_k: dict[str, float] = {}
    for name, sub in (("quiet", quiet), ("all", np.ones(len(x), bool))):
        tr = sub & (split == "train")
        va = sub & (split == "val")
        te = sub & (split == "test")
        c_tr, c_va, c_k = curves(d, tr, va, material, grid)
        j = int(np.argmin(c_va))
        s_star = float(grid[j])
        s_train = float(grid[int(np.argmin(c_tr))])
        lo, hi = plateau(grid, c_va)
        selected[name] = s_star
        selected_k[name] = float(c_k[j])

        out += [f"## Fitting set: {name}  (train {int(tr.sum())}, val {int(va.sum())}, "
                f"test {int(te.sum())})", "",
                f"* validation argmin **s = {s_star:.2f}** (K = {c_k[j]:.0f}); "
                f"train argmin {s_train:.2f}",
                f"* validation plateau within 1% of best: **s in [{lo:.2f}, {hi:.2f}]** "
                f"(width {hi - lo:.2f})", "",
                "| s | K(train) | train ES-MSE | val ES-MSE | val vs s=1 |",
                "|---|---|---|---|---|"]
        base_va = float(c_va[0])
        for want in np.arange(1.00, arguments.hi + 1e-9, 0.10):
            j2 = int(np.argmin(np.abs(grid - want)))
            mark = "  <-- selected" if abs(grid[j2] - s_star) < 1e-9 else ""
            out.append(f"| {grid[j2]:.2f} | {c_k[j2]:.0f} | {c_tr[j2]:.5f} | {c_va[j2]:.5f} | "
                       f"{(c_va[j2] / base_va - 1) * 100:+.2f}%{mark} |")
        out.append("")

        k_star = selected_k[name]
        for label, m in (("val", va), ("test", te)):
            a = robust_metrics(d["static"][m], d["oracle_cp"][m], d["oracle_es"][m], k_star)
            pred = d["static"][m] + (s_star - 1.0) * material[m]
            b = robust_metrics(pred, d["oracle_cp"][m], d["oracle_es"][m], k_star)
            out.append(f"* {label} (K={k_star:.0f}): ES-MSE {a['es_mse']:.5f} -> "
                       f"{b['es_mse']:.5f} "
                       f"({(b['es_mse'] / a['es_mse'] - 1) * 100:+.1f}%), "
                       f"MAE {a['mae']:.1f} -> {b['mae']:.1f}")
        out.append("")

    # ---- control: whole-evaluator scale, K free ----
    tr = quiet & (split == "train")
    va = quiet & (split == "val")
    _, c_whole, k_whole = curves(d, tr, va, material, grid, whole=True)
    _, c_mat, _ = curves(d, tr, va, material, grid)
    out += ["## Control: whole-evaluator scale, K free", "",
            "| s | K(train) | val ES-MSE |", "|---|---|---|"]
    for want in (1.0, 1.2, 1.4, 1.6, 1.8, 2.0):
        j2 = int(np.argmin(np.abs(grid - want)))
        out.append(f"| {grid[j2]:.2f} | {k_whole[j2]:.0f} | {c_whole[j2]:.5f} |")
    beyond = (1 - c_mat.min() / c_whole.min()) * 100
    out += ["",
            f"Flat across the whole grid (spread {c_whole.max() - c_whole.min():.5f}), "
            "exactly as theory requires: for a uniform scale, s and K are the same "
            f"parameter. The material scale reaches {c_mat.min():.5f} against this "
            f"control's {c_whole.min():.5f}, so the material/table rebalance is worth "
            f"**{beyond:.1f}% beyond calibration**.", "",
            "Any move-quality change a uniform scale produces in the real engine is "
            "search-margin calibration -- aspiration widths and delta margins are in "
            "centipawns and do not scale with it. Reported, never counted as an "
            "evaluation improvement.", ""]

    # ---- the candidate ----
    s = selected["quiet"]
    mg, eg = scaled_constants(s)
    out += ["## Candidate", "",
            f"s = {s:.2f}, constants rounded once at construction.", "",
            "| piece | MG now | MG scaled | EG now | EG scaled |", "|---|---|---|---|---|"]
    for i, p in enumerate(PIECE_NAMES):
        out.append(f"| {p} | {MG_VALUE[i]:.0f} | {mg[i]} | {EG_VALUE[i]:.0f} | {eg[i]} |")

    existing = json.loads(CANDIDATES.read_text(encoding="utf-8")) if CANDIDATES.exists() else {}
    existing = {k: v for k, v in existing.items() if not k.startswith("scale ")}
    existing[f"scale {s:.2f}"] = {
        "kind": "material_scale", "s": s, "k": selected_k["quiet"],
        "mg": mg, "eg": eg,
        "fitted_on": "quiet (tol 30) train, K refitted per s",
        "selected_on": "validation",
    }
    CANDIDATES.write_text(json.dumps(existing, indent=1), encoding="utf-8")

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    print(f"\ncandidate written to {CANDIDATES} as 'scale {s:.2f}'")


if __name__ == "__main__":
    main()
