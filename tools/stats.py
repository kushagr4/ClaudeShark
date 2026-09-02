"""Match statistics, including a cluster-aware interval.

Arena games are not independent samples. Every starting position is played
twice, once with each engine as white, and the suite is cycled repeatedly, so a
400-game match is really ~24 positions resampled. Treating each game as an
independent draw understates the uncertainty, sometimes badly, because two
engines that differ only slightly will play near-identical games from the same
position again and again.

Two intervals are produced and they are labelled differently on purpose:

* **naive** -- the game-level normal approximation. Comparable with the
  project's historical numbers, and what every earlier record used.
* **paired bootstrap** -- resamples *starting positions* with replacement,
  keeping each position's games together, which respects the clustering.

The bootstrap is the honest one. The naive figure is kept so old records remain
readable, not because it is right.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass

# Score of one game from the candidate's point of view.
WIN, DRAW, LOSS = 1.0, 0.5, 0.0


def elo_from_score(score: float) -> float:
    """Elo difference implied by a score fraction. Saturates at +/-800."""
    if score <= 0.0:
        return -800.0
    if score >= 1.0:
        return 800.0
    return -400.0 * math.log10(1.0 / score - 1.0)


@dataclass(frozen=True)
class MatchStats:
    games: int
    wins: int
    draws: int
    losses: int
    score: float
    elo: float
    naive_low: float
    naive_high: float
    boot_low: float
    boot_high: float
    clusters: int

    def describe(self) -> str:
        return (
            f"+{self.wins} ={self.draws} -{self.losses}, score {self.score:.1%}\n"
            f"elo {self.elo:+.0f}\n"
            f"  naive game-level 95% CI    {self.naive_low:+.0f} .. {self.naive_high:+.0f}\n"
            f"  paired bootstrap 95% CI    {self.boot_low:+.0f} .. {self.boot_high:+.0f}"
            f"   ({self.clusters} position clusters)"
        )


def naive_interval(wins: int, draws: int, losses: int) -> tuple[float, float, float]:
    """Elo and a game-level normal-approximation interval."""
    games = wins + draws + losses
    if games == 0:
        return 0.0, 0.0, 0.0
    score = (wins + draws * 0.5) / games
    variance = (
        wins * (1.0 - score) ** 2 + draws * (0.5 - score) ** 2 + losses * score**2
    ) / games
    stderr = math.sqrt(variance / games)
    return (
        elo_from_score(score),
        elo_from_score(max(0.0, score - 1.96 * stderr)),
        elo_from_score(min(1.0, score + 1.96 * stderr)),
    )


def paired_bootstrap(
    outcomes: list[tuple[int, float]], iterations: int = 5000, seed: int = 20260902
) -> tuple[float, float]:
    """95% interval by resampling starting-position clusters with replacement.

    ``outcomes`` is a list of ``(cluster_id, score)`` where score is 1/0.5/0 from
    the candidate's point of view and ``cluster_id`` identifies the starting
    position. All games from a resampled cluster are taken together, which is
    what makes this respect the pairing rather than pretending 400 games are 400
    independent observations.
    """
    if not outcomes:
        return 0.0, 0.0

    grouped: dict[int, list[float]] = defaultdict(list)
    for cluster, score in outcomes:
        grouped[cluster].append(score)
    clusters = list(grouped.values())

    rng = random.Random(seed)
    count = len(clusters)
    samples: list[float] = []
    for _ in range(iterations):
        total = 0.0
        played = 0
        for _ in range(count):
            chosen = clusters[rng.randrange(count)]
            total += sum(chosen)
            played += len(chosen)
        samples.append(total / played if played else 0.0)

    samples.sort()
    low = samples[int(0.025 * len(samples))]
    high = samples[min(len(samples) - 1, int(0.975 * len(samples)))]
    return elo_from_score(low), elo_from_score(high)


def summarise(
    outcomes: list[tuple[int, float]], iterations: int = 5000, seed: int = 20260902
) -> MatchStats:
    wins = sum(1 for _, s in outcomes if s == WIN)
    draws = sum(1 for _, s in outcomes if s == DRAW)
    losses = sum(1 for _, s in outcomes if s == LOSS)
    games = len(outcomes)
    score = (wins + draws * 0.5) / games if games else 0.0
    elo, naive_low, naive_high = naive_interval(wins, draws, losses)
    boot_low, boot_high = paired_bootstrap(outcomes, iterations, seed)
    return MatchStats(
        games=games,
        wins=wins,
        draws=draws,
        losses=losses,
        score=score,
        elo=elo,
        naive_low=naive_low,
        naive_high=naive_high,
        boot_low=boot_low,
        boot_high=boot_high,
        clusters=len({c for c, _ in outcomes}),
    )
