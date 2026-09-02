"""Time management.

A flag is a whole point, so this module is deliberately pessimistic. Two
deadlines govern a move:

* the **soft** deadline decides whether to start another iterative-deepening
  iteration, and is checked only between root moves and between iterations;
* the **hard** deadline aborts the search wherever it is, and is checked from
  inside the tree every ``CHECK_INTERVAL`` nodes.

The referee measures wall time around the whole request/response round trip, so
our own budget has to sit strictly inside the clock we were handed, with room
for JSON encoding, pipe traffic and process scheduling.

The agent API never tells us the increment, so we infer it: after a move we know
how long we took and what the clock said, and on the next call the difference
between the new clock and that prediction is the increment. The estimate is
biased low on purpose (our measured elapsed time is slightly less than the
referee's, which includes IPC), so we never over-spend on an increment that is
not really there.
"""

from __future__ import annotations

from time import perf_counter

# Wall time the referee attributes to us that we cannot measure from inside:
# writing the response, the pipe, and the parent waking up.
OVERHEAD_MS = 40.0
# Never plan to leave the clock below this.
RESERVE_MS = 200.0
# Nodes between hard-deadline checks. perf_counter() costs ~50 ns, so this is
# well under 1% of a node while bounding overshoot to a fraction of a millisecond.
CHECK_INTERVAL = 1024

# How many more moves we assume this side has to make. Lower spends faster.
DEFAULT_MOVES_TO_GO = 26
# Endgames are cheaper per move and benefit from depth, so budget slightly harder.
ENDGAME_MOVES_TO_GO = 20

MAX_INCREMENT_MS = 5_000.0


class TimeManager:
    __slots__ = (
        "_hard",
        "_last_clock_ms",
        "_last_spend_ms",
        "_seen_move",
        "_soft",
        "_started",
        "increment_ms",
    )

    def __init__(self) -> None:
        self._started = 0.0
        self._soft = 0.0
        self._hard = 0.0
        self.increment_ms = 0.0
        self._last_clock_ms = 0.0
        self._last_spend_ms = 0.0
        self._seen_move = False

    def observe(self, time_left_ms: int) -> None:
        """Update the inferred increment from the clock we were just handed."""
        if self._seen_move:
            predicted = self._last_clock_ms - self._last_spend_ms
            estimate = time_left_ms - predicted
            if 0.0 <= estimate <= MAX_INCREMENT_MS:
                # Keep the smallest plausible estimate; over-estimating the
                # increment is the failure mode that flags.
                self.increment_ms = (
                    estimate if self.increment_ms == 0.0 else min(self.increment_ms, estimate)
                )
        self._last_clock_ms = float(time_left_ms)

    def begin(self, time_left_ms: int, phase: int) -> None:
        """Open a budget for one move. ``phase`` is 0 (bare kings) to 24 (full board)."""
        self._started = perf_counter()

        usable = time_left_ms - OVERHEAD_MS - RESERVE_MS
        if usable <= 0.0:
            # Almost out of time: spend a token amount and rely on the depth-1
            # result, or on the fallback move if even that does not finish.
            self._soft = self._hard = max(1.0, time_left_ms * 0.1)
            self._finish()
            return

        moves_to_go = DEFAULT_MOVES_TO_GO if phase > 8 else ENDGAME_MOVES_TO_GO
        soft = usable / moves_to_go + self.increment_ms * 0.75
        # Never commit more than a third of what is left to a single move, no
        # matter what the per-move arithmetic says.
        hard = min(usable * 0.33, soft * 3.0)
        if soft > hard:
            soft = hard

        self._soft = soft
        self._hard = hard
        self._finish()

    def begin_fixed(self, budget_ms: float) -> None:
        """Open a fixed budget, ignoring the clock. For benchmarking only."""
        self._started = perf_counter()
        self._soft = budget_ms
        self._hard = budget_ms * 1.25
        self._finish()

    def _finish(self) -> None:
        self._seen_move = True

    def record_spend(self) -> None:
        """Remember what this move actually cost, for the increment estimate."""
        self._last_spend_ms = (perf_counter() - self._started) * 1000.0

    def elapsed_ms(self) -> float:
        return (perf_counter() - self._started) * 1000.0

    def soft_expired(self) -> bool:
        return (perf_counter() - self._started) * 1000.0 >= self._soft

    def hard_expired(self) -> bool:
        return (perf_counter() - self._started) * 1000.0 >= self._hard

    def soft_fraction_used(self) -> float:
        if self._soft <= 0.0:
            return 1.0
        return (perf_counter() - self._started) * 1000.0 / self._soft

    @property
    def soft_ms(self) -> float:
        return self._soft

    @property
    def hard_ms(self) -> float:
        return self._hard
