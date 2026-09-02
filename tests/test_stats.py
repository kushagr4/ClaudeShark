"""Match-statistics tests, on synthetic outcomes with known properties.

The point of the cluster-aware interval is that repeated starting positions are
not independent samples. These tests construct cases where that difference is
provable rather than merely plausible.
"""

from __future__ import annotations

import math

import pytest

from tools.stats import DRAW, LOSS, WIN, elo_from_score, naive_interval, paired_bootstrap, summarise


def test_elo_of_an_even_score_is_zero() -> None:
    assert elo_from_score(0.5) == pytest.approx(0.0)


def test_elo_is_monotonic_and_signed() -> None:
    assert elo_from_score(0.6) > 0
    assert elo_from_score(0.4) < 0
    assert elo_from_score(0.75) > elo_from_score(0.6)
    # The standard reference point: 76% is about 200 Elo.
    assert elo_from_score(0.76) == pytest.approx(200, abs=5)


def test_elo_saturates_rather_than_diverging() -> None:
    assert elo_from_score(1.0) == 800.0
    assert elo_from_score(0.0) == -800.0


def test_naive_interval_brackets_the_point_estimate() -> None:
    elo, low, high = naive_interval(wins=60, draws=80, losses=60)
    assert low < elo < high
    assert elo == pytest.approx(0.0, abs=1e-9)


def test_naive_interval_narrows_with_more_games() -> None:
    _, low_small, high_small = naive_interval(15, 20, 15)
    _, low_big, high_big = naive_interval(150, 200, 150)
    assert (high_big - low_big) < (high_small - low_small)


def test_bootstrap_matches_naive_when_every_cluster_is_one_game() -> None:
    """With no clustering the two methods should broadly agree."""
    outcomes = [(i, WIN if i % 2 == 0 else LOSS) for i in range(200)]
    _, naive_low, naive_high = naive_interval(100, 0, 100)
    boot_low, boot_high = paired_bootstrap(outcomes, iterations=2000)
    assert boot_low == pytest.approx(naive_low, abs=25)
    assert boot_high == pytest.approx(naive_high, abs=25)


def test_bootstrap_is_wider_when_outcomes_cluster_by_position() -> None:
    """The property that justifies the whole module.

    Two matches with identical W/D/L. In the first, results are spread across
    many positions. In the second, each position is decisive and repeated ten
    times, so the effective sample is ten times smaller. The naive interval
    cannot tell them apart; the bootstrap must.
    """
    spread = [(i, WIN if i % 2 == 0 else LOSS) for i in range(200)]
    clustered: list[tuple[int, float]] = []
    for cluster in range(20):
        outcome = WIN if cluster % 2 == 0 else LOSS
        clustered.extend((cluster, outcome) for _ in range(10))

    assert sum(s for _, s in spread) == sum(s for _, s in clustered)

    spread_low, spread_high = paired_bootstrap(spread, iterations=3000)
    clustered_low, clustered_high = paired_bootstrap(clustered, iterations=3000)
    assert (clustered_high - clustered_low) > (spread_high - spread_low) * 1.5


def test_all_draws_gives_a_tight_interval_at_zero() -> None:
    outcomes = [(i % 24, DRAW) for i in range(240)]
    stats = summarise(outcomes, iterations=1000)
    assert stats.score == 0.5
    assert stats.elo == pytest.approx(0.0)
    assert stats.boot_low == pytest.approx(0.0)
    assert stats.boot_high == pytest.approx(0.0)


def test_summarise_counts_and_clusters() -> None:
    outcomes = [(0, WIN), (0, LOSS), (1, DRAW), (1, WIN), (2, LOSS), (2, DRAW)]
    stats = summarise(outcomes, iterations=500)
    assert stats.games == 6
    assert (stats.wins, stats.draws, stats.losses) == (2, 2, 2)
    assert stats.clusters == 3
    assert stats.score == pytest.approx(0.5)


def test_bootstrap_is_deterministic_for_a_given_seed() -> None:
    outcomes = [(i % 12, WIN if i % 3 else LOSS) for i in range(120)]
    first = paired_bootstrap(outcomes, iterations=1000, seed=7)
    second = paired_bootstrap(outcomes, iterations=1000, seed=7)
    assert first == second


def test_a_one_sided_match_reports_a_positive_interval() -> None:
    """A genuinely strong result must produce an interval excluding zero."""
    outcomes = [(i % 24, WIN if i % 4 != 3 else DRAW) for i in range(240)]
    stats = summarise(outcomes, iterations=2000)
    assert stats.score > 0.8
    assert stats.boot_low > 0
    assert stats.naive_low > 0


def test_empty_match_does_not_explode() -> None:
    stats = summarise([], iterations=100)
    assert stats.games == 0
    assert not math.isnan(stats.elo)
