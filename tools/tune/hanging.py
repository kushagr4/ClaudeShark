"""Is `hanging_pieces` an evaluation feature or a search signal?

The residual regression gave `hanging_pieces` the largest explanatory power of
any positional term. That could mean the static evaluator is missing a real
concept -- or that the term is simply reading off tactics the search already
resolves, in which case adding it to evaluation would count them twice.

The test: regress the residual of the oracle against the engine's score at
increasing depth on the full feature set, and watch the `hanging_pieces`
coefficient and its drop-one ΔR². A genuine static concept keeps its weight as
depth increases; a tactical artefact collapses once quiescence and a few plies
of search have had their say.

    uv run python -m tools.tune.hanging
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from tools.tune.audit import CLIP, ols, quiet_mask
from tools.tune.features import load


def r2(x: np.ndarray, y: np.ndarray) -> float:
    design = np.hstack([x, np.ones((len(x), 1))])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ coef
    return 1.0 - float(resid @ resid) / (float(((y - y.mean()) ** 2).sum()) or 1.0)


def main() -> None:
    # Windows consoles default to cp1252, which cannot print the Greek and
    # box characters in these tables; the files are always UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Hanging-piece residual by search depth.")
    parser.add_argument("--labelled", type=Path, default=Path("corpus/candidates_labelled.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("corpus/tune/hanging.md"))
    arguments = parser.parse_args()

    d = load(arguments.labelled)
    names = list(d["residual_names"])
    feats = d["residual_feats"]
    hi = names.index("hanging_pieces")
    col_mg, col_eg = hi, len(names) + hi
    oracle = np.clip(d["oracle_cp"], -CLIP, CLIP)

    scores = {"static (depth 0)": d["static"]}
    for j, depth in enumerate(d["depths"]):
        scores[f"depth {int(depth)}"] = d["depth_scores"][:, j]

    out = ["# hanging_pieces: evaluation feature or search signal?", "",
           "Residual = clip(oracle) - clip(engine score at depth). Full 56-column feature "
           "regression; the hanging_pieces row only.", ""]
    for subset_name, mask in (("all positions", np.ones(len(oracle), bool)),
                              ("quiet subset (tol 30)", quiet_mask(d, 30))):
        out += [f"## {subset_name} (n = {int(mask.sum())})", "",
                "| engine score | residual R² (all feats) | hanging MG cp | ±se "
                "| hanging EG cp | ±se | drop-one ΔR² | mean |residual| |",
                "|---|---|---|---|---|---|---|---|"]
        for label, s in scores.items():
            y = oracle[mask] - np.clip(s[mask], -CLIP, CLIP)
            x = feats[mask]
            coef, se = ols(x, y)
            full = r2(x, y)
            keep = [i for i in range(x.shape[1]) if i not in (col_mg, col_eg)]
            without = r2(x[:, keep], y)
            out.append(f"| {label} | {full:.3f} | {coef[col_mg]:+.1f} | {se[col_mg]:.1f} | "
                       f"{coef[col_eg]:+.1f} | {se[col_eg]:.1f} | {full - without:.4f} | "
                       f"{np.abs(y).mean():.0f} |")
        out.append("")

    # Direct: how often does the static "hanging" signal survive one ply of quiescence?
    h = d["hanging"]
    has = h != 0
    q1 = d["depth_scores"][:, 0]
    swing = q1 - d["static"]
    out += ["## What quiescence does to positions with a hanging piece", "",
            "| group | n | mean (depth1 - static) | mean |oracle - static| "
            "| mean |oracle - depth1| | mean |oracle - depth3| |",
            "|---|---|---|---|---|---|"]
    d3 = d["depth_scores"][:, 1] if d["depth_scores"].shape[1] > 1 else q1
    for name, m in (("hanging ≠ 0", has), ("hanging = 0", ~has)):
        out.append(f"| {name} | {int(m.sum())} | {swing[m].mean():+.0f} | "
                   f"{np.abs(oracle[m] - np.clip(d['static'][m], -CLIP, CLIP)).mean():.0f} | "
                   f"{np.abs(oracle[m] - np.clip(q1[m], -CLIP, CLIP)).mean():.0f} | "
                   f"{np.abs(oracle[m] - np.clip(d3[m], -CLIP, CLIP)).mean():.0f} |")

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
