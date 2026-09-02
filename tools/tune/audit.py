"""Explain the suspicious material coefficients, then build the quiet subset.

The retained residual regression reported a middlegame queen coefficient of
about -1088 cp. Taken at face value that says Stockfish values a queen at
roughly zero, which is absurd, so before anything is tuned the question is
*which modelling choice manufactured that number*. This refits the same
regression under controlled variations and reports how the coefficient moves:

    A. as retained:   residual = clip(oracle, +/-600) - static   (static unclipped)
    B. no clipping
    C. both clipped
    D. direct fit of the oracle (not the residual) on material + intercept
    E. quiet subset only
    F. depth-1 residual (oracle - quiescence-resolved score) instead of static

Then the quiet subset is defined and its effect on every coefficient measured,
and baseline error metrics are reported per split, phase and balance.

    uv run python -m tools.tune.audit
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from tools.tune.dataset import load_split
from tools.tune.features import EG_VALUE, MG_VALUE, PIECE_NAMES, load

CLIP = 600.0


def ols(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Least squares with intercept; returns (coef, se) with intercept last."""
    design = np.hstack([x, np.ones((len(x), 1))])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ coef
    dof = max(1, len(y) - design.shape[1])
    sigma2 = float(resid @ resid) / dof
    try:
        cov = sigma2 * np.linalg.inv(design.T @ design)
        se = np.sqrt(np.clip(np.diag(cov), 0, None))
    except np.linalg.LinAlgError:
        se = np.full(design.shape[1], np.nan)
    return coef, se


def material_design(d: dict[str, np.ndarray]) -> np.ndarray:
    """Tapered material columns exactly as the evaluator applies them."""
    mgw = (d["phase"] / 24.0)[:, None]
    return np.hstack([d["counts"] * mgw, d["counts"] * (1 - mgw)])


def quiet_mask(d: dict[str, np.ndarray], tol: int) -> np.ndarray:
    """Positions where a static score is a meaningful thing to have.

    Excluded: any mate score, side to move in check, oracle best move a capture
    or promotion, and any position where the engine's own one-ply quiescence
    changes its static score by more than ``tol`` cp -- the direct signature of
    a pending tactic.
    """
    q1 = d["depth_scores"][:, 0]
    return (
        ~d["mate"]
        & ~d["in_check"]
        & ~d["best_capture"]
        & (np.abs(q1 - d["static"]) <= tol)
    )


def coefficient_table(d: dict[str, np.ndarray], mask: np.ndarray | None = None) -> list[str]:
    if mask is None:
        mask = np.ones(len(d["static"]), dtype=bool)
    x = material_design(d)[mask]
    oracle = d["oracle_cp"][mask]
    static = d["static"][mask]
    q1 = d["depth_scores"][mask, 0]

    variants = {
        "A retained (clip oracle, raw static)": np.clip(oracle, -CLIP, CLIP) - static,
        "B no clipping": oracle - static,
        "C both clipped": np.clip(oracle, -CLIP, CLIP) - np.clip(static, -CLIP, CLIP),
        "F depth-1 residual, both clipped": np.clip(oracle, -CLIP, CLIP) - np.clip(q1, -CLIP, CLIP),
    }
    lines = [f"n = {int(mask.sum())}", "",
             "| variant | " + " | ".join(f"{p} MG" for p in PIECE_NAMES)
             + " | " + " | ".join(f"{p} EG" for p in PIECE_NAMES) + " |",
             "|---|" + "---|" * 10]
    for name, y in variants.items():
        coef, se = ols(x, y)
        cells = [f"{c:+.0f}±{s:.0f}" for c, s in zip(coef[:10], se[:10], strict=True)]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")

    # D: direct fit -- what does the oracle itself say a piece is worth?
    coef, se = ols(x, np.clip(oracle, -CLIP, CLIP))
    cells = [f"{c:+.0f}±{s:.0f}" for c, s in zip(coef[:10], se[:10], strict=True)]
    lines.append("| D direct: clip(oracle) ~ material | " + " | ".join(cells) + " |")
    coef, se = ols(x, oracle)
    cells = [f"{c:+.0f}±{s:.0f}" for c, s in zip(coef[:10], se[:10], strict=True)]
    lines.append("| D' direct: raw oracle ~ material | " + " | ".join(cells) + " |")
    lines.append("")
    mg_text = ", ".join(f"{p} {v:.0f}" for p, v in zip(PIECE_NAMES, MG_VALUE, strict=True))
    eg_text = ", ".join(f"{p} {v:.0f}" for p, v in zip(PIECE_NAMES, EG_VALUE, strict=True))
    lines.append(f"Production values: MG {mg_text} / EG {eg_text}")
    return lines


def clipping_demo(d: dict[str, np.ndarray]) -> list[str]:
    """Show directly how the clip manufactures a negative queen residual."""
    q = d["counts"][:, 4]
    up = q > 0
    down = q < 0
    even = q == 0
    lines = ["| queen balance | n | mean static | mean oracle | mean clip(oracle) "
             "| mean residual (A) |",
             "|---|---|---|---|---|---|"]
    for name, m in (("white +Q", up), ("even", even), ("black +Q", down)):
        if not m.any():
            continue
        s = d["static"][m]
        o = d["oracle_cp"][m]
        c = np.clip(o, -CLIP, CLIP)
        lines.append(f"| {name} | {int(m.sum())} | {s.mean():+.0f} | {o.mean():+.0f} | "
                     f"{c.mean():+.0f} | {(c - s).mean():+.0f} |")
    return lines


def robust_metrics(
    pred: np.ndarray, oracle_cp: np.ndarray, oracle_es: np.ndarray, k: float
) -> dict[str, float]:
    err = pred - oracle_cp
    abs_err = np.abs(err)
    delta = 100.0
    huber = np.where(abs_err <= delta, 0.5 * err**2, delta * (abs_err - 0.5 * delta))
    es_pred = 1.0 / (1.0 + np.exp(-pred / k))
    return {
        "n": float(len(err)),
        "mae": float(abs_err.mean()),
        "medae": float(np.median(abs_err)),
        "huber": float(huber.mean()),
        "corr": float(np.corrcoef(pred, oracle_cp)[0, 1]) if len(err) > 2 else float("nan"),
        "es_mse": float(((es_pred - oracle_es) ** 2).mean()),
    }


def fit_k(pred: np.ndarray, es: np.ndarray) -> float:
    """Sigmoid scale mapping cp to expected score, fitted on the current evaluator."""
    best_k, best = 400.0, float("inf")
    for k in np.arange(150, 900, 5):
        loss = float(((1 / (1 + np.exp(-pred / k)) - es) ** 2).mean())
        if loss < best:
            best, best_k = loss, float(k)
    return best_k


def baseline_tables(d: dict[str, np.ndarray], assign: dict[str, str], k: float) -> list[str]:
    split = np.array([assign[g] for g in d["game_ids"]])
    lines = ["| subset | n | MAE | median AE | Huber | corr | ES-MSE |",
             "|---|---|---|---|---|---|---|"]
    def row(name: str, m: np.ndarray) -> None:
        if m.sum() < 5:
            return
        r = robust_metrics(d["static"][m], d["oracle_cp"][m], d["oracle_es"][m], k)
        lines.append(f"| {name} | {int(r['n'])} | {r['mae']:.0f} | {r['medae']:.0f} | "
                     f"{r['huber']:.0f} | {r['corr']:.3f} | {r['es_mse']:.4f} |")
    for name in ("train", "val", "test"):
        row(name, split == name)
    mg = d["phase"] >= 13
    row("middlegame (phase>=13)", mg)
    row("endgame (phase<13)", ~mg)
    bal = np.abs(d["counts"] @ np.array([1, 3, 3, 5, 9])) <= 1
    row("materially balanced", bal)
    row("materially imbalanced", ~bal)
    row("quiet subset (tol 30)", quiet_mask(d, 30))
    return lines


def main() -> None:
    # Windows consoles default to cp1252, which cannot print the Greek and
    # box characters in these tables; the files are always UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Audit the tuning dataset and regression.")
    parser.add_argument("--labelled", type=Path, default=Path("corpus/candidates_labelled.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("corpus/tune/audit.md"))
    arguments = parser.parse_args()

    d = load(arguments.labelled)
    assign = load_split()
    k = fit_k(d["static"], d["oracle_es"])

    out: list[str] = ["# Tuning audit", "",
                      f"{len(d['static'])} positions. Sigmoid scale K fitted on the current "
                      f"evaluator: **{k:.0f} cp** per unit logit.", ""]

    out += ["## 1. Why the retained regression wanted a ~-1000 cp queen", "",
            "The same material design matrix, five targets. Coefficients are cp per unit of "
            "(white minus black) count, ± standard error.", ""]
    out += coefficient_table(d)
    out += ["", "### The mechanism, shown directly", "",
            "Split by queen balance. Under variant A the oracle is clipped at ±600 but the "
            "static score is not, so every queen-up position carries a large negative "
            "residual that has nothing to do with what a queen is worth:", ""]
    out += clipping_demo(d)

    out += ["", "## 2. Quiet subset", ""]
    out += ["| tolerance (cp) | kept | dropped | queen MG (A) | queen MG (C) | queen MG (D) |",
            "|---|---|---|---|---|---|"]
    x_all = material_design(d)
    for tol in (0, 15, 30, 60, 100, 100000):
        m = quiet_mask(d, tol)
        x = x_all[m]
        a, _ = ols(x, np.clip(d["oracle_cp"][m], -CLIP, CLIP) - d["static"][m])
        oc = np.clip(d["oracle_cp"][m], -CLIP, CLIP)
        c, _ = ols(x, oc - np.clip(d["static"][m], -CLIP, CLIP))
        dd, _ = ols(x, np.clip(d["oracle_cp"][m], -CLIP, CLIP))
        label = "all (no tactical filter)" if tol >= 100000 else str(tol)
        out.append(f"| {label} | {int(m.sum())} | {int((~m).sum())} | {a[4]:+.0f} | "
                   f"{c[4]:+.0f} | {dd[4]:+.0f} |")
    out += ["", "Full coefficient table on the quiet subset (tolerance 30 cp):", ""]
    out += coefficient_table(d, quiet_mask(d, 30))

    out += ["", "## 3. Baseline error of the current evaluator", "",
            "Static evaluator, white POV, against the oracle. ES-MSE is mean squared error in "
            "expected score after the sigmoid, which is the target the tuner optimises.", ""]
    out += baseline_tables(d, assign, k)

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    json.dump({"k": k}, (arguments.out.parent / "k.json").open("w"))


if __name__ == "__main__":
    main()
