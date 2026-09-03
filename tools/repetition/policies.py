"""Audit-only repetition policies, and what each one plays.

Production scores a draw the first time the search re-enters a position the
engine has already been handed this game:

    if key in self._game_counts:
        return DRAW_SCORE

`_game_counts` is a counter, but only its keys are consulted, so one earlier
occurrence is enough. FIDE needs three. The variants isolate that one line;
the path scan that prevents the search looping inside a single line is left
alone in every variant, so none of them can search forever.

    D  current               `key in self._game_counts`      (control)
    A  threefold-aware       `self._game_counts.get(key, 0) >= 2`
    C  game-level disabled   the check removed entirely

Each variant is a scratch copy. Nothing here is a production change, and the
patcher asserts on its match so a silent no-op is impossible.

    uv run python -m tools.repetition.policies --out <scratch> --probe <cases.json>
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import chess

from tools.postmortem.play import Engine

CURRENT = "        if key in self._game_counts:\n            return DRAW_SCORE\n"

VARIANTS = {
    "D_current": None,
    "A_threefold": (
        "        # AUDIT VARIANT A: a draw only once this occurrence would be the\n"
        "        # third, which is what FIDE actually requires.\n"
        "        if self._game_counts.get(key, 0) >= 2:\n"
        "            return DRAW_SCORE\n"
    ),
    "C_disabled": (
        "        # AUDIT VARIANT C: no game-level repetition scoring at all. The\n"
        "        # path scan above still stops the search looping.\n"
    ),
}


def build(source: Path, out: Path) -> dict[str, Path]:
    built: dict[str, Path] = {}
    for name, replacement in VARIANTS.items():
        dest = out / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns("__pycache__"))
        if replacement is not None:
            path = dest / "cs_search.py"
            src = path.read_text(encoding="utf-8")
            if src.count(CURRENT) != 1:
                raise SystemExit(f"repetition site not found exactly once in {path}")
            path.write_text(src.replace(CURRENT, replacement), encoding="utf-8")
        built[name] = dest
    return built


def probe(engines: dict[str, Engine], fen: str, history: list[str],
          start_fen: str, moves: list[str]) -> dict[str, dict]:
    """Ask each variant what it plays, with the game's own repetition record.

    The board is rebuilt by replaying the game, not from the FEN: a board built
    from a FEN alone has no move stack, and `can_claim_threefold_repetition()`
    on such a board is unconditionally False.
    """
    board = chess.Board(start_fen)
    for uci in moves:
        board.push_uci(uci)
    assert board.fen() == fen, "replay did not reach the probed position"
    repeats = []
    for move in board.legal_moves:
        board.push(move)
        if board.can_claim_threefold_repetition():
            repeats.append(move.uci())
        board.pop()
    out = {}
    for name, engine in engines.items():
        engine.ask("new")
        for seen in history:
            engine.ask(f"seen {seen}")
        reply = engine.ask(f"go {fen}")
        out[name] = {
            "move": reply["move"], "score": reply["score"],
            "nodes": reply["nodes"], "depth": reply["depth"],
            "repeats": reply["move"] in repeats,
        }
    out["_repeating_moves"] = repeats
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit-only repetition policies.")
    parser.add_argument("--source", type=Path, default=Path("champions/v0_5_2_correctness"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--report", type=Path, default=Path("corpus/repetition/03_policies.txt"))
    arguments = parser.parse_args()

    built = build(arguments.source, arguments.out)
    print(f"built variants: {list(built)}")
    engines = {name: Engine(path, arguments.depth) for name, path in built.items()}
    cases = json.loads(arguments.cases.read_text(encoding="utf-8"))

    lines = [f"== AUDIT-ONLY REPETITION POLICIES (source {arguments.source}, depth {arguments.depth}) ==", ""]
    try:
        for case in cases:
            result = probe(engines, case["fen"], case.get("history", []),
                           case["start_fen"], case["moves"])
            lines.append(f"-- {case['label']}")
            lines.append(f"   FEN {case['fen']}")
            lines.append(f"   Stockfish: {case['sf_cp']:+} cp, WDL {case['sf_wdl']}, best {case['sf_best']}")
            lines.append(f"   moves that hand over a claimable threefold: {result['_repeating_moves']}")
            lines.append(f"   {'policy':<14} {'move':<7} {'score':>7} {'nodes':>9}  repeats?")
            for name in VARIANTS:
                r = result[name]
                lines.append(f"   {name:<14} {r['move']:<7} {r['score']:>7} {r['nodes']:>9}  "
                             f"{'YES -- draw' if r['repeats'] else 'no'}")
            lines.append("")
    finally:
        for e in engines.values():
            e.close()

    text = "\n".join(lines)
    arguments.report.parent.mkdir(parents=True, exist_ok=True)
    arguments.report.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
