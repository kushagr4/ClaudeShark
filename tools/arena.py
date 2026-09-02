"""Arena: many games between two agent directories, with a score and an Elo estimate.

Differences from ``harness/arena.py``, which it otherwise reuses wholesale:

* games start from a curated FEN suite rather than always the initial position,
  matching how rated games are played;
* every position is played twice, once with each engine as white, so colour and
  opening imbalance cancel;
* games run concurrently, because a 200-game match at a real time control is
  otherwise measured in hours;
* it reports an Elo difference with a confidence interval, so "this helped" is a
  claim with a number behind it rather than an impression.

Concurrency note: the referee measures wall time, so oversubscribing the CPU
slows both engines in a game equally but does make absolute node counts
meaningless. Keep ``--workers`` at or below half the core count.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from harness.referee import FAILED_TERMINATIONS, Outcome, play_match
from harness.rules import PLY_CAP
from harness.sandbox import local
from tools.positions import BALANCED_OPENINGS


@dataclass(frozen=True)
class GameSpec:
    index: int
    fen: str
    agent_is_white: bool


def _play(spec: GameSpec, agent: Path, opponent: Path, base_ms: int, increment_ms: int,
          ply_cap: int) -> tuple[GameSpec, Outcome]:
    white, black = (agent, opponent) if spec.agent_is_white else (opponent, agent)
    outcome = play_match(
        local(white), local(black), base_ms, increment_ms, ply_cap=ply_cap, start_fen=spec.fen
    )
    return spec, outcome


def elo_difference(score: float) -> float:
    """Convert a score fraction to an Elo difference. Saturates at +/-800."""
    if score <= 0.0:
        return -800.0
    if score >= 1.0:
        return 800.0
    return -400.0 * math.log10(1.0 / score - 1.0)


def elo_interval(wins: int, draws: int, losses: int) -> tuple[float, float, float]:
    """Elo difference with a 95% interval, from the per-game score variance."""
    games = wins + draws + losses
    if games == 0:
        return 0.0, 0.0, 0.0
    score = (wins + draws * 0.5) / games
    # Variance of a single game's score around the observed mean.
    variance = (
        wins * (1.0 - score) ** 2 + draws * (0.5 - score) ** 2 + losses * score**2
    ) / games
    stderr = math.sqrt(variance / games)
    low = elo_difference(max(0.0, score - 1.96 * stderr))
    high = elo_difference(min(1.0, score + 1.96 * stderr))
    return elo_difference(score), low, high


def build_schedule(games: int, fens: tuple[str, ...]) -> list[GameSpec]:
    """Pair every game with its colour-reversed twin on the same position."""
    schedule = []
    for index in range(games):
        fen = fens[(index // 2) % len(fens)]
        schedule.append(GameSpec(index=index, fen=fen, agent_is_white=index % 2 == 0))
    return schedule


def main() -> None:
    parser = argparse.ArgumentParser(description="Score an agent over many games from a FEN suite.")
    parser.add_argument("--agent", type=Path, default=Path("."))
    parser.add_argument("--opponent", type=Path, default=Path("baselines/minimax"))
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--base-ms", type=int, default=10_000)
    parser.add_argument("--increment-ms", type=int, default=100)
    parser.add_argument("--ply-cap", type=int, default=PLY_CAP)
    parser.add_argument("--workers", type=int, default=max(1, ((os.cpu_count() or 4) - 2) // 2))
    parser.add_argument("--start-fen", default=None, help="Use one position instead of the suite.")
    parser.add_argument("--pgn", type=Path, default=None)
    arguments = parser.parse_args()

    agent = arguments.agent.resolve()
    opponent = arguments.opponent.resolve()
    fens = (arguments.start_fen,) if arguments.start_fen else BALANCED_OPENINGS
    schedule = build_schedule(arguments.games, fens)

    print(
        f"{arguments.agent} vs {arguments.opponent}: {arguments.games} games at "
        f"{arguments.base_ms / 1000:g}s+{arguments.increment_ms / 1000:g}s, "
        f"{arguments.workers} concurrent, {len(fens)} opening(s)",
        flush=True,
    )

    wins = draws = losses = 0
    terminations: dict[str, int] = {}
    # A crash or a flag is only *our* bug when we are the side that lost by it.
    our_failures: dict[str, int] = {}
    pgns: list[str] = []

    with ThreadPoolExecutor(max_workers=arguments.workers) as pool:
        futures = [
            pool.submit(
                _play, spec, agent, opponent, arguments.base_ms, arguments.increment_ms,
                arguments.ply_cap,
            )
            for spec in schedule
        ]
        for done, future in enumerate(futures, start=1):
            spec, outcome = future.result()
            terminations[outcome.termination] = terminations.get(outcome.termination, 0) + 1
            pgns.append(outcome.pgn)
            if outcome.result in ("draw", "void"):
                draws += 1
                symbol = "="
            elif (outcome.result == "white") == spec.agent_is_white:
                wins += 1
                symbol = "+"
            else:
                losses += 1
                symbol = "-"
                if outcome.termination in FAILED_TERMINATIONS:
                    our_failures[outcome.termination] = (
                        our_failures.get(outcome.termination, 0) + 1
                    )
            print(
                f"[{done:>4}/{arguments.games}] {symbol} {outcome.termination:<20} "
                f"+{wins} ={draws} -{losses}",
                flush=True,
            )

    games = wins + draws + losses
    score = (wins + draws * 0.5) / games if games else 0.0
    elo, low, high = elo_interval(wins, draws, losses)

    print(f"\n{arguments.agent} vs {arguments.opponent} over {games} games")
    print(f"+{wins} ={draws} -{losses}, score {score:.1%}")
    print(f"elo {elo:+.0f}  (95% CI {low:+.0f} .. {high:+.0f})")
    print("terminations: " + ", ".join(f"{k} {v}" for k, v in sorted(terminations.items())))

    if arguments.pgn:
        arguments.pgn.write_text("\n\n".join(pgns) + "\n")
        print(f"pgn written to {arguments.pgn}")

    if our_failures:
        print(
            "\nOUR FAILURES: " + ", ".join(f"{k} {v}" for k, v in our_failures.items()),
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
