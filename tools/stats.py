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
    """Elo difference implied by a score fraction.

    Clamped at +/-ELO_SATURATION. A score of exactly 0 or 1 has no finite Elo,
    so the clamp is a floor on the difference rather than an estimate of it;
    MatchStats flags that case explicitly rather than printing a number that
    looks like a measurement.
    """
    if score <= 0.0:
        return -ELO_SATURATION
    if score >= 1.0:
        return ELO_SATURATION
    return max(-ELO_SATURATION, min(ELO_SATURATION, -400.0 * math.log10(1.0 / score - 1.0)))


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
    saturated: bool = False
    boot_degenerate: bool = False

    def describe(self) -> str:
        lines = [
            f"+{self.wins} ={self.draws} -{self.losses}, score {self.score:.1%}",
            f"elo {self.elo:+.0f}" + (" (saturated, see below)" if self.saturated else ""),
            f"  Wilson score 95% CI        {self.naive_low:+.0f} .. {self.naive_high:+.0f}",
            f"  paired bootstrap 95% CI    {self.boot_low:+.0f} .. {self.boot_high:+.0f}"
            f"   ({self.clusters} position clusters)",
        ]
        if self.saturated:
            lines.append(
                "  NOTE: every game had the same result, so the point estimate is at the"
                f" +/-{ELO_SATURATION:.0f} clamp and is a floor on the true difference, not"
                " a measurement of it."
            )
        if self.boot_degenerate:
            lines.append(
                "  NOTE: the bootstrap interval is zero-width because every position"
                " cluster produced the same score. That is an absence of observed"
                " variation, not precision; read the Wilson interval instead."
            )
        return "\n".join(lines)


ELO_SATURATION = 800.0


def wilson_interval(successes: float, games: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval for a score fraction, valid at the boundaries.

    The previous normal approximation used the observed between-game variance,
    which is exactly zero when every game ends the same way. That produced a
    zero-width interval -- 96 straight wins reported +800 .. +800, implying
    certainty a sample of any size cannot supply. Wilson's interval is derived
    from the binomial rather than from the observed spread, so an all-wins
    sample still yields a finite lower bound that widens as the sample shrinks.

    Draws count as half a success, which is the usual chess adaptation. It
    slightly overstates uncertainty for a match of nothing but draws, and that
    is the right direction to err.
    """
    if games <= 0:
        return 0.0, 1.0
    proportion = successes / games
    denominator = 1.0 + z * z / games
    centre = (proportion + z * z / (2 * games)) / denominator
    spread = z * math.sqrt(
        proportion * (1.0 - proportion) / games + z * z / (4 * games * games)
    ) / denominator
    return max(0.0, centre - spread), min(1.0, centre + spread)


def naive_interval(wins: int, draws: int, losses: int) -> tuple[float, float, float]:
    """Elo point estimate and a Wilson score interval, in Elo."""
    games = wins + draws + losses
    if games == 0:
        return 0.0, -ELO_SATURATION, ELO_SATURATION
    score = (wins + draws * 0.5) / games
    low, high = wilson_interval(wins + draws * 0.5, games)
    return elo_from_score(score), elo_from_score(low), elo_from_score(high)


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
        # Every game identical: the Elo transform is at its clamp and the number
        # is a floor, not a measurement.
        saturated=bool(games) and score in (0.0, 1.0),
        # No between-cluster variation, so the bootstrap cannot estimate spread.
        boot_degenerate=bool(games) and boot_low == boot_high,
    )
