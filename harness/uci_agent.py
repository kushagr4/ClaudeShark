"""A UCI engine wrapped as a referee ``Agent``.

The referee speaks one protocol: ``start``, ``move(fen, time_left_ms)``,
``stop``. This wrapper lets a UCI engine (Stockfish at a limited strength) sit
on the other side of the board so ClaudeShark can be benchmarked against an
external, reproducible opponent with the same clock the competition uses.

The referee only tells the mover its own clock; the opponent's clock is
reported to the engine as the same value, which is what the competition's
per-side clock looks like from one seat and is never consulted by the engine
for its own allocation.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import chess
import chess.engine

from harness.sandbox import AgentFailure


def uci_identity(binary: Path, options: dict[str, object]) -> str:
    """A short identity for a UCI opponent: binary hash plus the strength options."""
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()[:16]
    knobs = ",".join(f"{k}={v}" for k, v in sorted(options.items()))
    return f"{digest}[{knobs}]"


class UciAgent:
    def __init__(self, binary: Path, options: dict[str, object], increment_ms: int) -> None:
        self.binary = binary
        self.options = dict(options)
        self.increment_ms = increment_ms
        self.stderr_tail = ""
        self._engine: chess.engine.SimpleEngine | None = None

    def start(self, init_budget_s: float) -> None:
        try:
            engine = chess.engine.SimpleEngine.popen_uci(str(self.binary), timeout=init_budget_s)
            engine.configure(self.options)
        except (chess.engine.EngineError, OSError) as failure:
            self.stderr_tail = str(failure)
            raise AgentFailure("init") from failure
        self._engine = engine

    def move(self, fen: str, time_left_ms: int) -> str:
        if self._engine is None:
            raise RuntimeError("agent moved before start")
        board = chess.Board(fen)
        seconds = max(time_left_ms, 1) / 1000.0
        limit = chess.engine.Limit(
            white_clock=seconds, black_clock=seconds,
            white_inc=self.increment_ms / 1000.0, black_inc=self.increment_ms / 1000.0,
        )
        try:
            result = self._engine.play(board, limit)
        except chess.engine.EngineTerminatedError as failure:
            self.stderr_tail = str(failure)
            raise AgentFailure("crash") from failure
        except chess.engine.EngineError as failure:
            self.stderr_tail = str(failure)
            raise AgentFailure("illegal") from failure
        if result.move is None:
            raise AgentFailure("illegal")
        return result.move.uci()

    def stop(self) -> None:
        if self._engine is None:
            return
        try:
            self._engine.quit()
        except chess.engine.EngineError:
            self._engine.close()
        self._engine = None
