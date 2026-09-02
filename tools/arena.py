"""Arena: many games between two agent directories, with recoverable results.

Differences from `harness/arena.py`, which it otherwise reuses wholesale:

* games start from a curated FEN corpus rather than always the initial position,
  matching how rated games are played, and the corpus is **validated** before a
  single game is played;
* every position is played twice, once with each engine as white;
* games run concurrently;
* **every game is written to JSONL** with enough context to reconstruct the
  match, optionally with PGN, because a console aggregate is not a record;
* the `CS_*` experiment environment is **sanitised and recorded**, so a flag
  left in a parent shell cannot silently alter both contestants;
* uncertainty is reported both game-level and by **paired bootstrap over
  starting positions**, because repeated positions are clusters, not
  independent samples.

The default ply cap is 300, matching the competition. Historical runs in this
repository used 200; pass `--ply-cap 200` to reproduce them.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from cs_search import DECLARED_FLAGS
from cs_time import DECLARED_VARS
from harness.referee import FAILED_TERMINATIONS, Outcome, play_match
from harness.sandbox import local
from tools.positions import (
    BALANCED_OPENINGS,
    CORPUS_VERSION,
    corpus_hash,
    unsuitable,
)
from tools.stats import DRAW, LOSS, WIN, summarise

# The competition adjudicates at 300 plies. Historical arenas here used 200.
COMPETITION_PLY_CAP = 300

# Experiment variables the arena may pass through, taken from the engine itself
# rather than copied here. A hand-maintained list had already fallen a flag
# behind -- CS_SEE_KEEP_CHECKS took effect while matches recorded
# "effective: {}" -- so the list is now derived from what the engine declares it
# reads. tests/test_arena_integrity.py fails if the two ever diverge.
KNOWN_CS_VARS: tuple[str, ...] = tuple(
    sorted(set(DECLARED_FLAGS) | set(DECLARED_VARS))
)


@dataclass(frozen=True)
class GameSpec:
    index: int
    cluster: int  # index into the corpus; games sharing it are one cluster
    fen: str
    agent_is_white: bool


def sanitise_environment(allow: dict[str, str]) -> dict[str, str]:
    """Strip every CS_* variable, then re-add only what was asked for.

    Returns the values actually in force, for the record. Mutates os.environ,
    which is safe because it happens once before any engine is spawned and both
    contestants are spawned from the same parent.
    """
    removed = {}
    for name in list(os.environ):
        if name.startswith("CS_") or name == "CLAUDESHARK_DEBUG":
            removed[name] = os.environ.pop(name)
    for name, value in allow.items():
        os.environ[name] = value
    effective = {n: os.environ[n] for n in KNOWN_CS_VARS if n in os.environ}
    return {"stripped": removed, "effective": effective}  # type: ignore[return-value]


def snapshot_identity(directory: Path) -> str:
    """A content hash of an agent directory, so a record names exact code."""
    import hashlib

    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*.py")):
        digest.update(path.relative_to(directory).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=False,
        )
        return result.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def build_schedule(games: int, fens: tuple[str, ...]) -> list[GameSpec]:
    """Pair every game with its colour-reversed twin on the same position."""
    schedule = []
    for index in range(games):
        cluster = (index // 2) % len(fens)
        schedule.append(
            GameSpec(index=index, cluster=cluster, fen=fens[cluster],
                     agent_is_white=index % 2 == 0)
        )
    return schedule


def _play(spec: GameSpec, agent: Path, opponent: Path, base_ms: int, increment_ms: int,
          ply_cap: int) -> tuple[GameSpec, Outcome, float]:
    white, black = (agent, opponent) if spec.agent_is_white else (opponent, agent)
    started = time.time()
    outcome = play_match(
        local(white), local(black), base_ms, increment_ms, ply_cap=ply_cap,
        start_fen=spec.fen,
    )
    return spec, outcome, time.time() - started


def _final_position(pgn: str, start_fen: str) -> tuple[str, int]:
    """Replay the PGN to recover the final FEN and ply count."""
    import io

    import chess.pgn

    game = chess.pgn.read_game(io.StringIO(pgn))
    board = chess.Board(start_fen)
    plies = 0
    if game is not None:
        for move in game.mainline_moves():
            if move not in board.legal_moves:
                break
            board.push(move)
            plies += 1
    return board.fen(), plies


def main() -> None:
    parser = argparse.ArgumentParser(description="Score an agent over many games.")
    parser.add_argument("--agent", type=Path, default=Path("."))
    parser.add_argument("--opponent", type=Path, default=Path("champions/v0_3"))
    parser.add_argument("--games", type=int, default=96)
    parser.add_argument("--base-ms", type=int, default=20_000)
    parser.add_argument("--increment-ms", type=int, default=200)
    parser.add_argument("--ply-cap", type=int, default=COMPETITION_PLY_CAP,
                        help="300 matches the competition; historical runs used 200")
    parser.add_argument("--workers", type=int, default=max(1, ((os.cpu_count() or 4) - 2) // 2))
    parser.add_argument("--start-fen", default=None, help="Use one position instead of the corpus.")
    parser.add_argument("--jsonl", type=Path, default=None, help="per-game record (recommended)")
    parser.add_argument("--pgn", type=Path, default=None)
    parser.add_argument("--set-env", action="append", default=[],
                        help="CS_VAR=value to pass to BOTH engines; everything else is stripped")
    parser.add_argument("--bootstrap", type=int, default=5000)
    arguments = parser.parse_args()

    # 1. Refuse to run on an invalid position set. An illegal starting position
    #    silently corrupted every arena this project ran before it was caught,
    #    and validating only the built-in corpus let a custom --start-fen
    #    through unchecked.
    selected = (
        (arguments.start_fen,) if arguments.start_fen else BALANCED_OPENINGS
    )
    label = "--start-fen" if arguments.start_fen else "BALANCED_OPENINGS"
    bad = unsuitable(selected, label)
    if bad:
        for suite, index, fen, status in bad:
            print(f"UNSUITABLE {suite}[{index}] {fen}: {status}", file=sys.stderr)
        raise SystemExit("refusing to benchmark an unsuitable starting position")

    # 2. Colour pairing is the basis of every strength claim here: each position
    #    is played once with each engine as white. An odd count leaves a final
    #    unpaired game whose colour bias goes straight into the score, so it is
    #    refused rather than run under paired statistics.
    if arguments.games % 2 != 0:
        raise SystemExit(
            f"--games must be even for paired arena matches, got {arguments.games}. "
            f"Every position is played once with each colour; an odd count leaves "
            f"one game unpaired and biases the score."
        )
    if arguments.games <= 0:
        raise SystemExit(f"--games must be positive, got {arguments.games}")

    # 3. Control the environment before anything is spawned. An unrecognised
    #    name is refused rather than accepted: a typo like CS_LRM=0 would
    #    otherwise be set, recorded, and change nothing, quietly producing a
    #    benchmark of something other than what was intended.
    allow: dict[str, str] = {}
    for item in arguments.set_env:
        name, separator, value = item.partition("=")
        if not separator:
            raise SystemExit(f"--set-env expects NAME=value, got {item!r}")
        if name not in KNOWN_CS_VARS:
            raise SystemExit(
                f"--set-env: unrecognised variable {name!r}.\n"
                f"The engine reads: {', '.join(KNOWN_CS_VARS)}"
            )
        allow[name] = value
    environment = sanitise_environment(allow)

    agent = arguments.agent.resolve()
    opponent = arguments.opponent.resolve()
    fens = selected
    schedule = build_schedule(arguments.games, fens)

    match_id = f"{int(time.time())}-{agent.name}-vs-{opponent.name}"
    header = {
        "record": "match_header",
        "match_id": match_id,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit(),
        "agent": str(arguments.agent),
        "agent_snapshot": snapshot_identity(agent),
        "opponent": str(arguments.opponent),
        "opponent_snapshot": snapshot_identity(opponent),
        "corpus_version": CORPUS_VERSION,
        "corpus_hash": corpus_hash(fens),
        "corpus_size": len(fens),
        "games": arguments.games,
        "base_ms": arguments.base_ms,
        "increment_ms": arguments.increment_ms,
        "ply_cap": arguments.ply_cap,
        "workers": arguments.workers,
        "env_effective": environment["effective"],
        "env_stripped": sorted(environment["stripped"]),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }

    handle = arguments.jsonl.open("w", encoding="utf-8") if arguments.jsonl else None
    if handle:
        handle.write(json.dumps(header) + "\n")
        handle.flush()

    print(
        f"{arguments.agent} vs {arguments.opponent}: {arguments.games} games at "
        f"{arguments.base_ms / 1000:g}s+{arguments.increment_ms / 1000:g}s, "
        f"ply cap {arguments.ply_cap}, {arguments.workers} concurrent, "
        f"corpus v{CORPUS_VERSION} ({corpus_hash(fens)}, {len(fens)} positions)",
        flush=True,
    )
    if environment["effective"]:
        print(f"  CS_* in force: {environment['effective']}", flush=True)
    if environment["stripped"]:
        print(f"  CS_* stripped from parent: {sorted(environment['stripped'])}", flush=True)

    outcomes: list[tuple[int, float]] = []
    terminations: dict[str, int] = {}
    our_failures: dict[str, int] = {}
    pgns: list[str] = []
    wins = draws = losses = 0

    with ThreadPoolExecutor(max_workers=arguments.workers) as pool:
        futures = [
            pool.submit(_play, spec, agent, opponent, arguments.base_ms,
                        arguments.increment_ms, arguments.ply_cap)
            for spec in schedule
        ]
        for done, future in enumerate(futures, start=1):
            spec, outcome, seconds = future.result()
            terminations[outcome.termination] = terminations.get(outcome.termination, 0) + 1
            pgns.append(outcome.pgn)

            if outcome.result in ("draw", "void"):
                draws += 1
                score, symbol = DRAW, "="
            elif (outcome.result == "white") == spec.agent_is_white:
                wins += 1
                score, symbol = WIN, "+"
            else:
                losses += 1
                score, symbol = LOSS, "-"
                if outcome.termination in FAILED_TERMINATIONS:
                    our_failures[outcome.termination] = (
                        our_failures.get(outcome.termination, 0) + 1
                    )
            outcomes.append((spec.cluster, score))

            if handle:
                final_fen, plies = _final_position(outcome.pgn, spec.fen)
                handle.write(json.dumps({
                    "record": "game",
                    "match_id": match_id,
                    "game_index": spec.index,
                    "cluster": spec.cluster,
                    "start_fen": spec.fen,
                    "white": str(arguments.agent if spec.agent_is_white else arguments.opponent),
                    "black": str(arguments.opponent if spec.agent_is_white else arguments.agent),
                    "agent_is_white": spec.agent_is_white,
                    "result": outcome.result,
                    "termination": outcome.termination,
                    "agent_score": score,
                    "plies": plies,
                    "final_fen": final_fen,
                    "seconds": round(seconds, 2),
                    "failed": outcome.termination in FAILED_TERMINATIONS,
                }) + "\n")
                handle.flush()

            print(
                f"[{done:>4}/{arguments.games}] {symbol} {outcome.termination:<20} "
                f"+{wins} ={draws} -{losses}",
                flush=True,
            )

    stats = summarise(outcomes, iterations=arguments.bootstrap)

    print(f"\n{arguments.agent} vs {arguments.opponent} over {stats.games} games")
    print(stats.describe())
    print("terminations: " + ", ".join(f"{k} {v}" for k, v in sorted(terminations.items())))

    if handle:
        handle.write(json.dumps({
            "record": "match_summary",
            "match_id": match_id,
            "games": stats.games,
            "wins": stats.wins,
            "draws": stats.draws,
            "losses": stats.losses,
            "score": stats.score,
            "elo": stats.elo,
            "naive_ci": [stats.naive_low, stats.naive_high],
            "bootstrap_ci": [stats.boot_low, stats.boot_high],
            "clusters": stats.clusters,
            "terminations": terminations,
            "our_failures": our_failures,
        }) + "\n")
        handle.close()
        print(f"per-game records written to {arguments.jsonl}")

    if arguments.pgn:
        arguments.pgn.write_text("\n\n".join(pgns) + "\n", encoding="utf-8")
        print(f"pgn written to {arguments.pgn}")

    if our_failures:
        print("\nOUR FAILURES: " + ", ".join(f"{k} {v}" for k, v in our_failures.items()),
              file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
