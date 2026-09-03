"""Classify every repetition draw in a retained game set.

The post-mortem counted repetition terminations and stopped there. A count is
not a finding: most repetitions are correct chess. This separates them.

**Move history is essential and easy to lose.** `chess.Board(fen)` carries no
history, so `can_claim_threefold_repetition()` on such a board is always False
and every repetition question silently answers "no". Every board here is built
by replaying the game from its starting position.

Two different questions are answered, because two different agents make the
decision.

*The engine's choice.* The last mover played a move that left the opponent a
claimable draw. Stockfish evaluates that position -- from a fresh board, so its
score is the position's objective value, uncontaminated by the repetition about
to be claimed. From that mover's point of view:

    C  losing side forces the draw    eval <= -100      a good result, not a bug
    B  equal position repeats         -100 < eval < 100 fine
    A  ahead but nothing better       eval >= 100 and no non-repeating move
                                      keeps the advantage
    D  ahead and a better move existed                  a thrown win

*The referee's choice.* `harness/referee.py` ends the game on
`board.outcome(claim_draw=True)`, and python-chess reports a claimable
threefold either when the position has occurred three times or when the side to
move merely has a legal move reaching a third occurrence. Under FIDE the claim
is that player's option and a winning player would decline it, so the audit
also records, at the final position: whether three occurrences actually
happened, whether the side to move was winning, and -- replaying that engine's
own game-level repetition record so the question is faithful rather than asked
of a fresh searcher -- whether it would have repeated at all.

    uv run python -m tools.repetition.audit --games <annotated.jsonl> \
        --cand <dir> --base <dir> --out <jsonl>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import chess

from tools.corpus.oracle import Oracle, expected_score
from tools.postmortem.play import Engine

AHEAD = 100


def replay(game: dict) -> chess.Board:
    """The final position, with the full move history attached."""
    board = chess.Board(game["start_fen"])
    for move in game["moves"]:
        board.push_uci(move["move"])
    return board


def repeating_moves(board: chess.Board) -> list[str]:
    """Legal moves that hand the opponent a claimable threefold."""
    out = []
    for move in board.legal_moves:
        board.push(move)
        if board.can_claim_threefold_repetition():
            out.append(move.uci())
        board.pop()
    return out


def key_counts(board: chess.Board) -> Counter:
    """How often each position has occurred, back to the last irreversible move."""
    counts: Counter = Counter()
    counts.update((board._transposition_key(),))
    switchyard = []
    while board.move_stack:
        move = board.pop()
        switchyard.append(move)
        if board.is_irreversible(move):
            break
        counts.update((board._transposition_key(),))
    while switchyard:
        board.push(switchyard.pop())
    return counts


def audit_game(game: dict, oracle: Oracle, engines: dict[str, Engine],
               nodes: int) -> dict | None:
    final = replay(game)
    if not final.can_claim_threefold_repetition():
        return None
    counts = key_counts(final)
    threefold_on_board = final.is_repetition(3)

    # ---- the referee's side: the claim is made for the side to move ----
    side_is_cand = (final.turn == chess.WHITE) == game["cand_white"]
    who = "cand" if side_is_cand else "base"
    final_label = oracle.analyse(final.fen(), nodes)
    final_reps = repeating_moves(final)

    # Reproduce that engine's own game-level repetition record before asking.
    engine = engines[who]
    engine.ask("new")
    for m in game["moves"]:
        if m["mover"] == who:
            engine.ask(f"seen {m['fen']}")
    reply = engine.ask(f"go {final.fen()}")
    would_repeat = reply["move"] in final_reps

    # ---- the engine's side: the last mover handed over the claim ----
    decision = final.copy(stack=True)
    decision.pop()
    decision_fen = decision.fen()
    last = game["moves"][-1]
    label = oracle.analyse(decision_fen, nodes)
    cp = label.cp_stm
    alternatives = [
        mv for mv in decision.legal_moves
        if mv.uci() != last["move"] and not _hands_over_claim(decision, mv)
    ]

    row = {
        "cluster": game["cluster"], "cand_white": game["cand_white"],
        "plies": game["plies"],
        # referee dimension
        "final_fen": final.fen(),
        "threefold_actually_on_board": threefold_on_board,
        "max_occurrences": max(counts.values()),
        "final_stm": "white" if final.turn else "black",
        "final_stm_engine": who,
        "final_eval_cp_stm": final_label.cp_stm,
        "final_wdl_stm": list(final_label.wdl_stm) if final_label.wdl_stm else None,
        "final_expected_score_stm": expected_score(final_label.wdl_stm),
        "final_repeating_moves": final_reps,
        "final_legal_moves": final.legal_moves.count(),
        "engine_move_at_final": reply["move"],
        "engine_would_repeat": would_repeat,
        "winning_side_to_move": final_label.cp_stm >= AHEAD,
        "cut_short": final_label.cp_stm >= AHEAD and not would_repeat,
        # engine dimension
        "decision_fen": decision_fen,
        "decision_move": last["move"],
        "decision_mover": last["mover"],
        "decision_stm": "white" if decision.turn else "black",
        "eval_cp_stm": cp,
        "wdl_stm": list(label.wdl_stm) if label.wdl_stm else None,
        "sf_best": label.best,
        "legal_moves": decision.legal_moves.count(),
        "non_repeating_moves": len(alternatives),
        "nodes": nodes,
    }

    if cp < AHEAD or not alternatives:
        row["category"] = "C" if cp <= -AHEAD else "B" if cp < AHEAD else "A"
        row["category_reason"] = (
            "losing side forced the draw" if cp <= -AHEAD
            else "position was level" if cp < AHEAD
            else "no non-repeating move available"
        )
        row["best_alternative"] = None
        row["best_alternative_cp"] = None
        return row

    best_move, best_cp, scored = None, -20_000, []
    for mv in alternatives:
        child = oracle.score_after(decision_fen, mv.uci(), nodes)
        value = -child.cp_stm
        scored.append((mv.uci(), value))
        if value > best_cp:
            best_move, best_cp = mv.uci(), value
    scored.sort(key=lambda r: -r[1])
    row.update({
        "best_alternative": best_move, "best_alternative_cp": best_cp,
        "alternatives_top5": scored[:5], "eval_after_repeating": 0,
        "avoidable": best_cp >= AHEAD,
        "category": "D" if best_cp >= AHEAD else "A",
        "category_reason": (
            f"ahead {cp} and {best_move} keeps {best_cp}" if best_cp >= AHEAD
            else f"ahead {cp} but the best non-repeating move is only {best_cp}"
        ),
    })
    return row


def _hands_over_claim(board: chess.Board, move: chess.Move) -> bool:
    board.push(move)
    try:
        return board.can_claim_threefold_repetition()
    finally:
        board.pop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify repetition draws.")
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--cand", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--nodes", type=int, default=1_000_000)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()

    games = [json.loads(line) for line in arguments.games.open(encoding="utf-8")]
    repeats = [g for g in games if g["termination"] == "threefold_repetition"]
    print(f"{len(games)} games, {len(repeats)} ending in a claimed threefold")

    engines = {"cand": Engine(arguments.cand, arguments.depth),
               "base": Engine(arguments.base, arguments.depth)}
    rows = []
    try:
        with Oracle() as oracle:
            for i, game in enumerate(repeats, start=1):
                row = audit_game(game, oracle, engines, arguments.nodes)
                if row is None:
                    print(f"  [{i}] cluster {game['cluster']}: claim not reproducible")
                    continue
                rows.append(row)
                print(f"  [{i:>3}/{len(repeats)}] cl {row['cluster']:>3} "
                      f"{row['category']} | mover {row['decision_mover']:<4} "
                      f"eval {row['eval_cp_stm']:>+6} | stm {row['final_stm_engine']:<4} "
                      f"eval {row['final_eval_cp_stm']:>+6} "
                      f"plays {row['engine_move_at_final']:<6}"
                      f"{' REPEATS' if row['engine_would_repeat'] else ''}"
                      f"{'  CUT SHORT' if row['cut_short'] else ''}", flush=True)
    finally:
        for e in engines.values():
            e.close()

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    with arguments.out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    n = len(rows)
    print(f"\ncategories (the last mover's choice): {dict(Counter(r['category'] for r in rows))}")
    print(f"three occurrences actually on the board: "
          f"{sum(1 for r in rows if r['threefold_actually_on_board'])}/{n}")
    print(f"engine to move would itself have repeated: "
          f"{sum(1 for r in rows if r['engine_would_repeat'])}/{n}")
    print(f"side the referee claimed for was winning: "
          f"{sum(1 for r in rows if r['winning_side_to_move'])}/{n}")
    print(f"cut short (winning and would have played on): "
          f"{sum(1 for r in rows if r['cut_short'])}/{n} "
          f"{dict(Counter(r['final_stm_engine'] for r in rows if r['cut_short']))}")
    print(f"written to {arguments.out}")


if __name__ == "__main__":
    main()
