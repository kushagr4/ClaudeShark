"""Tactical test suite: does the engine find the move, at a fixed budget?

Nominal depth is not strength. A selective search that reduces the wrong moves
reaches a bigger number and plays worse. This suite is the counterweight: every
position has one objectively correct move, and the score is how many the engine
finds. It is deterministic, it runs in seconds, and it is the first thing to
check after any change to pruning or reduction.

Positions are split into two kinds:

* ``mate`` -- a forced mate exists. These are verified programmatically by
  ``--verify``, which proves the mate distance with an independent
  minimax-to-fixed-depth that uses no pruning heuristics at all.
* ``win`` -- a tactic that wins material or saves a lost position. These are
  positions where the refutation is short and unambiguous.

    uv run python -m tools.tactics --ms 1000
    uv run python -m tools.tactics --ms 1000 --engine champions/v0_1
    uv run python -m tools.tactics --verify
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import chess


@dataclass(frozen=True)
class Puzzle:
    name: str
    fen: str
    best: tuple[str, ...]  # accepted moves in UCI
    kind: str  # "mate" or "win"
    note: str = ""


SUITE: tuple[Puzzle, ...] = (
    # ---------------------------------------------------------------- mates
    Puzzle("back_rank_m1", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", ("a1a8",), "mate"),
    Puzzle("queen_m1", "7k/6pp/8/8/8/8/5PPP/4Q1K1 w - - 0 1", ("e1e8",), "mate"),
    # Qxd8 is mate at once, not the mate in two it looks like: the queen
    # captures the defending rook and the back rank is already sealed.
    Puzzle(
        "queen_takes_defender_m1",
        "3r2k1/5ppp/8/8/8/8/5PPP/3QR1K1 w - - 0 1",
        ("d1d8",),
        "mate",
    ),
    Puzzle(
        "knight_m1",
        "6rk/6pp/8/6N1/8/8/8/6K1 w - - 0 1",
        ("g5f7",),
        "mate",
        "Nf7# -- g8 and h7 are blocked by black's own pieces",
    ),
    # The rook ladder: the first move is quiet, which is what makes it a test.
    Puzzle(
        "rook_ladder_g8_m2",
        "6k1/8/8/8/8/8/R7/1R4K1 w - - 0 1",
        ("a2a7", "b1b7"),
        "mate",
    ),
    Puzzle(
        "rook_ladder_h8_m2",
        "7k/8/8/8/8/8/R7/1R5K w - - 0 1",
        ("a2a7", "b1b7", "b1g1"),
        "mate",
    ),
    # Requires a quiet king approach before the queen can mate.
    Puzzle(
        "queen_king_m2",
        "7k/8/4K3/8/8/8/8/6Q1 w - - 0 1",
        ("e6f6", "e6f7"),
        "mate",
    ),
    # ----------------------------------------------------------- win material
    Puzzle(
        "hanging_queen",
        "4k3/8/8/3q4/4P3/8/8/4K3 w - - 0 1",
        ("e4d5",),
        "win",
        "free queen",
    ),
    Puzzle(
        "must_take_the_queen",
        "4k3/8/8/8/4N3/8/8/3qK3 w - - 0 1",
        ("e1d1",),
        "win",
        "white is in check from d1; Kxd1 is the only move that wins the queen",
    ),
    Puzzle(
        "recapture_on_d5",
        "rnb1kbnr/ppp1pppp/8/3q4/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 4",
        ("c3d5",),
        "win",
        "queen is free",
    ),
    Puzzle(
        "save_the_knight",
        "4k3/8/3p4/4N3/8/8/8/4K3 w - - 0 1",
        (),
        "win",
        "any move that saves the knight; scored by the checker",
    ),
    Puzzle(
        "promote_to_win",
        "8/4P1k1/8/8/8/8/6K1/8 w - - 0 1",
        ("e7e8q",),
        "win",
        "queen promotion",
    ),
    Puzzle(
        "win_the_pinned_piece",
        "4k3/8/8/8/8/3n4/8/3RK3 w - - 0 1",
        ("d1d3",),
        "win",
        "knight is pinned and lost",
    ),
)


_MATE = 1000


def _solve(node: chess.Board, remaining: int) -> int:
    """Exhaustive minimax with terminal detection only.

    Returns, from the side to move's point of view, ``_MATE - n`` when it can
    force mate in ``n`` plies, ``-(_MATE - n)`` when it is mated in ``n``, and 0
    when no forced result exists inside the horizon. Deliberately has no
    transposition table, no pruning and no evaluation, so it is an independent
    check on the engine rather than a restatement of it.
    """
    if node.is_checkmate():
        return -_MATE
    if remaining == 0 or node.is_stalemate() or node.is_insufficient_material():
        return 0
    best = -_MATE - 1
    for move in node.legal_moves:
        node.push(move)
        score = -_solve(node, remaining - 1)
        node.pop()
        # Step the mate distance by one ply so a faster mate scores higher and
        # plain max() picks the quickest one.
        if score > 500:
            score -= 1
        elif score < -500:
            score += 1
        if score > best:
            best = score
    return best


def mate_plies(board: chess.Board, max_plies: int = 5) -> int | None:
    """Shortest forced mate for the side to move, in plies, or None."""
    for horizon in range(1, max_plies + 1, 2):
        score = _solve(board, horizon)
        if score > 500:
            return _MATE - score
    return None


def fastest_mating_moves(board: chess.Board, distance: int) -> list[str]:
    """Every move that forces mate in exactly ``distance`` plies."""
    moves = []
    for move in board.legal_moves:
        board.push(move)
        reply = _solve(board, distance - 1)
        board.pop()
        # After our move the opponent is to move and is being mated in
        # distance - 1 plies, which is a large negative score for them.
        if reply < -500 and _MATE + reply == distance - 1:
            moves.append(move.uci())
    return sorted(moves)


def verify() -> int:
    """Prove every ``mate`` puzzle, and report the true distance and best moves.

    The verifier is the authority: if a label disagrees with it, the label is
    wrong. Puzzles whose ``best`` set does not intersect the proven fastest
    mating moves are reported as MISMATCH.
    """
    failures = 0
    for puzzle in SUITE:
        board = chess.Board(puzzle.fen)
        if not board.is_valid():
            print(f"INVALID  {puzzle.name}: {board.status()!r}")
            failures += 1
            continue

        # Every listed move must actually be legal. A typo here would silently
        # make a puzzle unsolvable and look like an engine regression.
        legal = {move.uci() for move in board.legal_moves}
        illegal = [uci for uci in puzzle.best if uci not in legal]
        if illegal:
            print(f"ILLEGAL  {puzzle.name}: {illegal} not legal in this position")
            failures += 1
            continue

        if puzzle.kind != "mate":
            print(f"skip     {puzzle.name} (kind={puzzle.kind})")
            continue

        distance = mate_plies(board)
        if distance is None:
            print(f"NO MATE  {puzzle.name}: no forced mate within 5 plies")
            failures += 1
            continue

        best_moves = fastest_mating_moves(board, distance)
        ok = bool(set(puzzle.best) & set(best_moves))
        if not ok:
            failures += 1
        print(
            f"{'ok' if ok else 'MISMATCH':<8} {puzzle.name}: mate in "
            f"{(distance + 1) // 2} ({distance} plies), fastest = {best_moves}"
        )
    return failures


def _saves_the_knight(board: chess.Board, move: chess.Move) -> bool:
    """Checker for the one puzzle whose success is a property, not a move."""
    board.push(move)
    knight = board.piece_at(chess.E5)
    survived = not (knight and knight.piece_type == chess.KNIGHT and knight.color)
    board.pop()
    return survived


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the tactical suite.")
    parser.add_argument("--ms", type=int, default=1_000, help="fixed budget per puzzle")
    parser.add_argument("--engine", type=Path, default=None, help="frozen champion directory")
    parser.add_argument("--verify", action="store_true", help="prove the mate puzzles instead")
    parser.add_argument("--quiet", action="store_true")
    arguments = parser.parse_args()

    if arguments.verify:
        raise SystemExit(1 if verify() else 0)

    if arguments.engine:
        sys.path.insert(0, str(arguments.engine.resolve()))
    from cs_search import Searcher

    solved = 0
    total_nodes = 0
    total_depth = 0
    failed: list[str] = []

    for puzzle in SUITE:
        board = chess.Board(puzzle.fen)
        move, info = Searcher().search(board, 0, fixed_budget_ms=arguments.ms)
        assert move is not None

        if puzzle.name == "save_the_knight":
            ok = _saves_the_knight(board, move)
        else:
            ok = move.uci() in puzzle.best

        solved += ok
        total_nodes += info.nodes
        total_depth += info.depth
        if not ok:
            failed.append(f"{puzzle.name} (played {move.uci()}, want {'/'.join(puzzle.best)})")
        if not arguments.quiet:
            print(
                f"{'PASS' if ok else 'FAIL':<5} {puzzle.name:<24} "
                f"played {move.uci():<6} depth {info.depth:>2} nodes {info.nodes:>8}"
            )

    count = len(SUITE)
    print(f"\nengine: {arguments.engine or 'working tree'}   budget: {arguments.ms} ms")
    print(f"solved {solved}/{count}   avg depth {total_depth / count:.2f}   nodes {total_nodes:,}")
    for name in failed:
        print(f"  missed: {name}")


if __name__ == "__main__":
    main()
