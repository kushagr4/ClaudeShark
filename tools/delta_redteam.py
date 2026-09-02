"""Red-team delta pruning: does it ever cost a real move?

Delta pruning decides before the capture is pushed, so it cannot know whether
the move gives check, and is therefore not covered by the SEE check exemption.
That is a real hole in the code. The question this answers is whether it is
reachable.

Method. Search every position twice at a fixed depth -- once shipping, once with
delta pruning effectively disabled -- and collect the positions where the chosen
move differs. Then re-run only those at deeper fixed depths and classify:

    A converges     the difference disappears with depth: a shallow artefact
    B equivalent    stable difference, but the scores agree within a margin
    C failure       stable difference and delta-on is materially worse

Only C is a bug. A and B are the search picking between moves it cannot
distinguish, which is expected and harmless.

The position set is deliberately wider than the benchmark corpus: it adds
generated positions that actually contain the motif at issue -- negative-SEE
captures that give check -- because the corpus was never selected for that.

    uv run python -m tools.delta_redteam --depth 6 --deep 8
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

import chess

import cs_search
from cs_search import Searcher
from cs_see import see
from tools.positions import BALANCED_OPENINGS, SHARP_POSITIONS
from tools.tactics import SUITE

DELTA_OFF = 10_000_000


@dataclass
class Divergence:
    fen: str
    depth: int
    on_move: str
    off_move: str
    on_score: int
    off_score: int
    on_nodes: int
    off_nodes: int

    @property
    def gap(self) -> int:
        """How much worse the shipping engine's own search rates its choice."""
        return self.off_score - self.on_score


def search(fen: str, depth: int, margin: int) -> tuple[str, int, int]:
    cs_search.DELTA_MARGIN = margin
    try:
        move, info = Searcher(tt_bits=17).search(chess.Board(fen), 0, max_depth=depth)
    finally:
        cs_search.DELTA_MARGIN = BASELINE_MARGIN
    return (move.uci() if move else "none"), info.score, info.nodes


BASELINE_MARGIN = cs_search.DELTA_MARGIN


def has_negative_see_check(board: chess.Board) -> bool:
    """Does this position contain the motif delta pruning could mishandle?"""
    for move in board.legal_moves:
        if not board.is_capture(move):
            continue
        if see(board, move) >= 0:
            continue
        board.push(move)
        giving_check = board.is_check()
        board.pop()
        if giving_check:
            return True
    return False


def generated_positions(target: int, seed: int) -> list[str]:
    """Random positions that actually contain a negative-SEE checking capture.

    The benchmark corpus was chosen for balance, not for this motif, so leaving
    the search to it would be testing the wrong board.
    """
    rng = random.Random(seed)
    found: list[str] = []
    attempts = 0
    while len(found) < target and attempts < 40_000:
        attempts += 1
        board = chess.Board()
        for _ in range(rng.randint(8, 70)):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
        if board.is_game_over() or not board.is_valid():
            continue
        if has_negative_see_check(board):
            found.append(board.fen())
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description="Red-team delta pruning.")
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--deep", type=int, nargs="+", default=[7, 8])
    parser.add_argument("--generated", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260902)
    parser.add_argument("--equal-margin", type=int, default=25,
                        help="score gap below which two moves count as equivalent")
    arguments = parser.parse_args()

    corpus = list(BALANCED_OPENINGS) + list(SHARP_POSITIONS)
    tactics = [p.fen for p in SUITE]
    generated = generated_positions(arguments.generated, arguments.seed)
    positions = corpus + tactics + generated
    motif = sum(1 for f in positions if has_negative_see_check(chess.Board(f)))

    print(f"positions: {len(corpus)} corpus + {len(tactics)} tactics + "
          f"{len(generated)} generated = {len(positions)}")
    print(f"  containing a negative-SEE checking capture: {motif}")
    print(f"comparing delta ON (margin {BASELINE_MARGIN}) vs OFF at depth {arguments.depth}\n")

    divergences: list[Divergence] = []
    for index, fen in enumerate(positions):
        on_move, on_score, on_nodes = search(fen, arguments.depth, BASELINE_MARGIN)
        off_move, off_score, off_nodes = search(fen, arguments.depth, DELTA_OFF)
        if on_move != off_move:
            divergences.append(
                Divergence(fen, arguments.depth, on_move, off_move,
                           on_score, off_score, on_nodes, off_nodes)
            )
        if (index + 1) % 40 == 0:
            print(f"  ...{index + 1}/{len(positions)}, {len(divergences)} divergences",
                  flush=True)

    print(f"\ndivergent positions at depth {arguments.depth}: "
          f"{len(divergences)}/{len(positions)}")
    for d in divergences:
        print(f"\n  FEN   {d.fen}")
        print(f"  depth {d.depth}  ON {d.on_move} ({d.on_score}) {d.on_nodes:,} nodes"
              f"   OFF {d.off_move} ({d.off_score}) {d.off_nodes:,} nodes"
              f"   gap {d.gap:+d}cp")

    if not divergences:
        print("\nno divergences: delta pruning changed no chosen move.")
        return

    print(f"\n{'=' * 70}\ndeeper follow-up on the divergent positions only\n{'=' * 70}")
    verdicts: dict[str, str] = {}
    for d in divergences:
        print(f"\n  {d.fen}")
        classification = "A converges"
        for depth in arguments.deep:
            on_move, on_score, _ = search(d.fen, depth, BASELINE_MARGIN)
            off_move, off_score, _ = search(d.fen, depth, DELTA_OFF)
            gap = off_score - on_score
            same = on_move == off_move
            print(f"    depth {depth}: ON {on_move} ({on_score})  "
                  f"OFF {off_move} ({off_score})  gap {gap:+d}cp"
                  f"{'  [same move]' if same else ''}")
            if not same:
                classification = (
                    "B equivalent" if abs(gap) <= arguments.equal_margin
                    else "C FAILURE"
                )
        verdicts[d.fen] = classification
        print(f"    -> {classification}")

    print(f"\n{'=' * 70}\nclassification\n{'=' * 70}")
    for label in ("A converges", "B equivalent", "C FAILURE"):
        matching = [f for f, v in verdicts.items() if v == label]
        print(f"  {label:<14} {len(matching)}")
        for fen in matching:
            print(f"      {fen}")
    if any(v == "C FAILURE" for v in verdicts.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
