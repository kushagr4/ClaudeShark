"""Move quality: how much does selective search cost us in centipawns?

Node counts say how *fast* a variant searches. This says whether the moves it
picks are any good, which is the question pruning experiments actually raise.

Method, per position:

1. A **reference** searches to ``--ref-depth``. The reference runs PVS only.
   PVS is score-exact -- it changes the cost of a search, never its result --
   whereas null-move and LMR are approximations, so an unpruned-but-PVS engine
   is the strongest oracle available that is still affordable.
2. The **candidate** searches the same position to ``--depth``.
3. If they agree, the loss is zero. If they disagree, the reference evaluates
   the candidate's move by searching the position after it, and the loss is
   how much worse that is than the reference's own move.

The output is average and worst-case centipawn loss, plus how many positions
lost more than a pawn. A variant that saves nodes while raising this number is
buying speed with blunders.

    uv run python -m tools.movequality --depth 6 --ref-depth 6
"""

from __future__ import annotations

import argparse

import chess

import cs_search
from cs_search import Searcher
from tools.positions import BALANCED_OPENINGS, SHARP_POSITIONS

# (name, PVS, null move, LMR, safe LMR, SEE in quiescence, SEE in ordering)
VARIANTS: tuple[tuple[str, bool, bool, bool, bool, bool, bool], ...] = (
    ("v0.3 shipping", True, True, True, True, False, False),
    ("+ SEE quiescence", True, True, True, True, True, False),
    ("+ SEE ordering", True, True, True, True, False, True),
    ("+ SEE both", True, True, True, True, True, True),
    ("no LMR", True, True, False, False, False, False),
)


def configure(
    pvs: bool, nmp: bool, lmr: bool, safe: bool, see_qs: bool = False, see_order: bool = False
) -> None:
    """Set the search feature flags for this process.

    The flags are module globals read at node time, so mutating them here
    reconfigures the search without a subprocess or a second copy of the code.
    """
    cs_search.USE_PVS = pvs
    cs_search.USE_NULL_MOVE = nmp
    cs_search.USE_LMR = lmr
    cs_search.LMR_SAFE = safe
    cs_search.USE_SEE_QS = see_qs
    cs_search.USE_SEE_ORDER = see_order


def search_at(fen: str, depth: int) -> tuple[chess.Move, int]:
    """Fresh searcher per call, so a table filled by one variant never leaks."""
    move, info = Searcher().search(chess.Board(fen), 0, max_depth=depth)
    assert move is not None
    return move, info.score


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure centipawn loss against a reference.")
    parser.add_argument("--depth", type=int, default=6, help="candidate search depth")
    parser.add_argument("--ref-depth", type=int, default=6, help="reference search depth")
    parser.add_argument("--positions", type=int, default=0)
    parser.add_argument(
        "--suite",
        choices=("balanced", "sharp", "both"),
        default="sharp",
        help="sharp positions are where reduction blindness actually shows",
    )
    arguments = parser.parse_args()

    if arguments.suite == "balanced":
        fens = BALANCED_OPENINGS
    elif arguments.suite == "sharp":
        fens = SHARP_POSITIONS
    else:
        fens = BALANCED_OPENINGS + SHARP_POSITIONS
    if arguments.positions:
        fens = fens[: arguments.positions]

    # Reference pass: PVS only, no approximating pruning.
    print(f"reference: PVS only at depth {arguments.ref_depth} over {len(fens)} positions...")
    configure(True, False, False, False)
    reference: dict[str, tuple[chess.Move, int]] = {}
    for fen in fens:
        reference[fen] = search_at(fen, arguments.ref_depth)

    print(f"\n{'variant':<22} {'agree':>6} {'avg loss':>9} {'worst':>7} {'>100cp':>7}")
    for name, pvs, nmp, lmr, safe, see_qs, see_order in VARIANTS:
        losses: list[int] = []
        agreements = 0
        detail: list[str] = []

        for fen in fens:
            reference_move, reference_score = reference[fen]

            configure(pvs, nmp, lmr, safe, see_qs, see_order)
            candidate_move, _ = search_at(fen, arguments.depth)

            if candidate_move == reference_move:
                agreements += 1
                losses.append(0)
                continue

            # Score the candidate's move with the reference, one ply shallower
            # since we are already a move deep.
            configure(True, False, False, False)
            board = chess.Board(fen)
            board.push(candidate_move)
            _, reply_score = search_at(board.fen(), max(1, arguments.ref_depth - 1))
            candidate_score = -reply_score

            loss = max(0, reference_score - candidate_score)
            losses.append(loss)
            if loss > 0:
                detail.append(
                    f"      {candidate_move.uci()} vs {reference_move.uci()} "
                    f"loses {loss}cp  [{fen}]"
                )

        average = sum(losses) / len(losses)
        worst = max(losses)
        blunders = sum(1 for loss in losses if loss > 100)
        print(
            f"{name:<22} {agreements:>4}/{len(fens)} {average:>8.1f} "
            f"{worst:>7} {blunders:>7}"
        )
        for line in detail[:6]:
            print(line)


if __name__ == "__main__":
    main()
