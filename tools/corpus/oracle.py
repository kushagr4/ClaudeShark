"""Offline reference oracle: a strong external engine, driven at fixed nodes.

**Tooling only.** The engine binary lives outside the repository, is never
copied into it and never ships. The competition permits labelling positions
with an existing engine offline; it prohibits shipping one. This module is the
former.

Why fixed nodes rather than time: a node limit makes a label reproducible on
any machine running the same binary, while a time limit measures the laptop.
The engine runs single-threaded with the hash cleared before every position
(``ucinewgame``), so two runs of the same position at the same node count give
the same score, best move and principal variation.

Every label records enough provenance to be reproduced: engine name as it
reports itself, the binary path and its SHA-256, the UCI options in force and
the node limit.

    ORACLE_ENGINE_PATH=C:\\path\\to\\stockfish.exe   (default: see ORACLE_DEFAULT)
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import chess
import chess.engine

ORACLE_DEFAULT = r"C:\Users\epick\engines\stockfish\stockfish-windows-x86-64-avx2.exe"
ORACLE_ENV = "ORACLE_ENGINE_PATH"

# Single-threaded and hash-cleared per position, so a node limit is a
# reproducible label rather than a wall-clock measurement.
ORACLE_OPTIONS: dict[str, Any] = {"Threads": 1, "Hash": 256, "UCI_ShowWDL": True}

# A mate is recorded as a centipawn score clamped here, with the mate distance
# kept alongside, so a table can be sorted without special-casing.
MATE_CP = 10_000


def oracle_path() -> Path:
    return Path(os.environ.get(ORACLE_ENV, ORACLE_DEFAULT))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class Line:
    """One multipv line, scored from the side to move's point of view."""

    move: str
    cp: int  # side-to-move centipawns, mates clamped to +-MATE_CP
    mate: int | None  # moves to mate, python-chess sign convention
    wdl: tuple[int, int, int] | None  # side to move: wins, draws, losses per mille
    pv: list[str]


@dataclass(frozen=True)
class Label:
    fen: str
    nodes: int
    depth: int
    seldepth: int | None
    cp_stm: int
    cp_white: int
    mate: int | None
    wdl_stm: tuple[int, int, int] | None
    wdl_white: tuple[int, int, int] | None
    best: str
    pv: list[str]
    lines: list[Line] = field(default_factory=list)  # multipv, best first

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["lines"] = [asdict(line) for line in self.lines]
        return data

    @staticmethod
    def from_json(data: dict[str, Any]) -> Label:
        def triple(value: Any) -> tuple[int, int, int] | None:
            return (int(value[0]), int(value[1]), int(value[2])) if value else None

        lines = [
            Line(
                move=line["move"], cp=line["cp"], mate=line.get("mate"),
                wdl=triple(line.get("wdl")), pv=list(line["pv"]),
            )
            for line in data.get("lines", [])
        ]
        return Label(
            fen=data["fen"], nodes=data["nodes"], depth=data["depth"],
            seldepth=data.get("seldepth"), cp_stm=data["cp_stm"], cp_white=data["cp_white"],
            mate=data.get("mate"), wdl_stm=triple(data.get("wdl_stm")),
            wdl_white=triple(data.get("wdl_white")),
            best=data["best"], pv=list(data["pv"]), lines=lines,
        )


def expected_score(wdl: tuple[int, int, int] | None) -> float | None:
    """Win probability plus half the draw probability, from a per-mille WDL."""
    if wdl is None:
        return None
    wins, draws, _ = wdl
    return (wins + 0.5 * draws) / 1000.0


def _clamp(score: chess.engine.Score) -> tuple[int, int | None]:
    mate = score.mate()
    if mate is not None:
        return (MATE_CP if mate > 0 else -MATE_CP), mate
    cp = score.score()
    assert cp is not None
    return max(-MATE_CP, min(MATE_CP, cp)), None


class Oracle:
    """One engine process. Use as a context manager, or call close()."""

    def __init__(self, path: Path | None = None, options: dict[str, Any] | None = None) -> None:
        self.path = (path or oracle_path()).resolve()
        if not self.path.exists():
            raise FileNotFoundError(
                f"reference engine not found at {self.path}; set {ORACLE_ENV}"
            )
        self.options = dict(ORACLE_OPTIONS if options is None else options)
        self.engine = chess.engine.SimpleEngine.popen_uci(str(self.path))
        self.engine.configure(self.options)
        self.name = self.engine.id.get("name", "unknown")

    def __enter__(self) -> Oracle:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        with contextlib.suppress(chess.engine.EngineError):
            self.engine.quit()

    def provenance(self) -> dict[str, Any]:
        return {
            "engine": self.name,
            "binary": str(self.path),
            "binary_sha256": _sha256(self.path),
            "options": self.options,
            "limit": "nodes (fixed); hash cleared before each position",
        }

    def analyse(self, fen: str, nodes: int, multipv: int = 1) -> Label:
        board = chess.Board(fen)
        # A fresh ``game`` object makes python-chess send ``ucinewgame`` first,
        # which clears the hash. That is what makes a node-limited score
        # reproducible: otherwise the previous position's table shapes this one.
        infos = self.engine.analyse(
            board, chess.engine.Limit(nodes=nodes), multipv=multipv,
            info=chess.engine.INFO_ALL, game=object(),
        )
        if isinstance(infos, dict):
            infos = [infos]
        lines: list[Line] = []
        for info in infos:
            if "score" not in info or not info.get("pv"):
                continue
            pov = info["score"]
            cp, mate = _clamp(pov.pov(board.turn))
            wdl_obj = info.get("wdl")
            wdl = None
            if wdl_obj is not None:
                stm = wdl_obj.pov(board.turn)
                wdl = (stm.wins, stm.draws, stm.losses)
            pv = [m.uci() for m in info["pv"]]
            lines.append(Line(move=pv[0], cp=cp, mate=mate, wdl=wdl, pv=pv))
        if not lines:
            raise RuntimeError(f"oracle returned no line for {fen}")
        top = lines[0]
        first = infos[0]
        wdl_white = None
        if top.wdl is not None:
            wdl_white = (
                top.wdl if board.turn == chess.WHITE else (top.wdl[2], top.wdl[1], top.wdl[0])
            )
        return Label(
            fen=fen, nodes=nodes, depth=int(first.get("depth", 0)),
            seldepth=first.get("seldepth"),
            cp_stm=top.cp, cp_white=top.cp if board.turn == chess.WHITE else -top.cp,
            mate=top.mate, wdl_stm=top.wdl, wdl_white=wdl_white,
            best=top.move, pv=top.pv, lines=lines,
        )

    def score_after(self, fen: str, move: str, nodes: int) -> Label:
        """Label the position after ``move``; useful for scoring a chosen move."""
        board = chess.Board(fen)
        board.push_uci(move)
        return self.analyse(board.fen(), nodes)


# ----------------------------------------------------------------- parallel


def label_many(
    fens: Iterable[str], nodes: int, multipv: int = 1, workers: int = 1,
    path: Path | None = None, progress: bool = False,
) -> list[Label]:
    """Label positions in parallel, one engine per worker thread, order preserved.

    Threads rather than processes: the work happens inside the engine
    processes, so the interpreter lock is irrelevant, and a process pool on
    Windows measured forty times slower for the same job. Each thread owns a
    single-threaded engine with the hash cleared per position, so parallelism
    does not change any label.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor

    tasks = [(fen, nodes, multipv) for fen in fens]
    local = threading.local()
    engines: list[Oracle] = []
    guard = threading.Lock()
    done = 0

    def work(task: tuple[str, int, int]) -> Label:
        nonlocal done
        if not hasattr(local, "oracle"):
            local.oracle = Oracle(path)
            with guard:
                engines.append(local.oracle)
        label = local.oracle.analyse(*task)
        with guard:
            done += 1
            if progress and done % 50 == 0:
                print(f"  labelled {done}/{len(tasks)}", flush=True)
        return label

    try:
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            return list(pool.map(work, tasks))
    finally:
        for oracle in engines:
            oracle.close()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
