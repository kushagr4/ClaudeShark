import time
from dataclasses import dataclass
from typing import Literal

import chess
import chess.pgn

from harness.rules import INIT_BUDGET_S, PLY_CAP
from harness.sandbox import Agent, AgentFailure

PIECE_VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
RESULT_HEADERS = {"white": "1-0", "black": "0-1", "draw": "1/2-1/2", "void": "*"}
FAILED_TERMINATIONS = frozenset({"crash", "illegal", "flag", "init", "both_failed"})

Result = Literal["white", "black", "draw", "void"]
Decision = Literal["white", "black", "draw"]


@dataclass(frozen=True)
class Outcome:
    result: Result
    termination: str
    pgn: str



DRAW_CLAIM_MODES = ("auto", "strict")


def game_outcome(board: chess.Board, draw_claim: str = "auto") -> chess.Outcome | None:
    """The finished outcome of ``board``, or None if play continues.

    ``auto`` is ``board.outcome(claim_draw=True)``: python-chess reports a
    claimable threefold either when the position has occurred three times **or
    when the side to move merely has a legal move reaching a third
    occurrence**, and this claims it for them. Under FIDE the claim is that
    player's option, and a winning player would decline it.

    That is not a hypothetical. Auditing 127 repetition draws in the fixed-depth
    diagnostic set found that not one position had actually occurred three
    times, and that in 44 of them the side the draw was claimed for was winning
    by at least 100 cp and, asked directly, would have played a different move.
    See `benchmarks/current/2026-09-03-repetition-audit.md`.

    ``strict`` therefore ends the game on the automatic outcomes plus a
    repetition claim only once the position has genuinely occurred three times.
    The fifty-move rule is left claimable in both modes, deliberately: the
    engine's own `rules_outcome` mirrors `can_claim_fifty_moves`, and desyncing
    the two is exactly the class of bug that cost this project a benchmark
    before.

    ``auto`` remains the default so that historical results stay comparable.
    """
    if draw_claim == "auto":
        return board.outcome(claim_draw=True)
    if draw_claim != "strict":
        raise ValueError(f"unknown draw_claim {draw_claim!r}")
    finish = board.outcome(claim_draw=False)
    if finish is not None:
        return finish
    if board.is_repetition(3):
        return chess.Outcome(chess.Termination.THREEFOLD_REPETITION, None)
    if board.can_claim_fifty_moves():
        return chess.Outcome(chess.Termination.FIFTY_MOVES, None)
    return None


def play_match(
    white: Agent,
    black: Agent,
    base_ms: int,
    increment_ms: int,
    ply_cap: int = PLY_CAP,
    start_fen: str = chess.STARTING_FEN,
    draw_claim: str = "auto",
) -> Outcome:
    try:
        return _play(white, black, base_ms, increment_ms, ply_cap, start_fen, draw_claim)
    finally:
        white.stop()
        black.stop()


def _play(
    white: Agent, black: Agent, base_ms: int, increment_ms: int, ply_cap: int, start_fen: str,
    draw_claim: str = "auto",
) -> Outcome:
    board = chess.Board(start_fen)
    agents = {chess.WHITE: white, chess.BLACK: black}

    white_failure = _start(white)
    black_failure = _start(black)
    if white_failure is not None and black_failure is not None:
        return _outcome(board, "void", "both_failed")
    if white_failure is not None:
        return _outcome(board, "black", white_failure)
    if black_failure is not None:
        return _outcome(board, "white", black_failure)

    clock = {chess.WHITE: float(base_ms), chess.BLACK: float(base_ms)}

    while True:
        finish = game_outcome(board, draw_claim)
        if finish is not None:
            return _outcome(board, _decide(finish), finish.termination.name.lower())
        if len(board.move_stack) >= ply_cap:
            return _outcome(board, _adjudicate(board), "adjudication")

        mover = board.turn
        started_at = time.monotonic()
        try:
            uci = agents[mover].move(board.fen(), int(clock[mover]))
        except AgentFailure as failure:
            return _outcome(board, _opponent_wins(mover), failure.reason)
        clock[mover] -= (time.monotonic() - started_at) * 1000.0
        if clock[mover] < 0:
            return _outcome(board, _opponent_wins(mover), "flag")

        move = _legal_move(board, uci)
        if move is None:
            return _outcome(board, _opponent_wins(mover), "illegal")
        board.push(move)
        clock[mover] += increment_ms


def _start(agent: Agent) -> str | None:
    try:
        agent.start(INIT_BUDGET_S)
    except AgentFailure as failure:
        return failure.reason
    return None


def _legal_move(board: chess.Board, uci: str) -> chess.Move | None:
    try:
        move = chess.Move.from_uci(uci)
    except chess.InvalidMoveError:
        return None
    return move if move in board.legal_moves else None


def _opponent_wins(mover: chess.Color) -> Decision:
    return "black" if mover == chess.WHITE else "white"


def _decide(finish: chess.Outcome) -> Decision:
    if finish.winner is None:
        return "draw"
    return "white" if finish.winner == chess.WHITE else "black"


def _adjudicate(board: chess.Board) -> Decision:
    balance = sum(
        value * (len(board.pieces(piece, chess.WHITE)) - len(board.pieces(piece, chess.BLACK)))
        for piece, value in PIECE_VALUES.items()
    )
    if balance > 0:
        return "white"
    if balance < 0:
        return "black"
    return "draw"


def _outcome(board: chess.Board, result: Result, termination: str) -> Outcome:
    game = chess.pgn.Game.from_board(board)
    game.headers["Result"] = RESULT_HEADERS[result]
    game.headers["Termination"] = termination
    return Outcome(result=result, termination=termination, pgn=str(game))
