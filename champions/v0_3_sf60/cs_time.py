"""Time management.

A flag is a whole point, so this module is deliberately pessimistic.

The competition clock is **120 s per side plus a 500 ms increment**, and that
increment is a published constant, not something to be discovered at runtime.
Earlier versions inferred it from successive clocks; that was unnecessary
machinery for a known number, and it spent the first move of every game
assuming no increment at all. ``INCREMENT_MS`` is now the competition value,
overridable through ``CS_INCREMENT_MS`` purely so local arenas -- which have to
use faster controls to fit games into an afternoon -- can tell the engine what
their increment really is instead of having it guess.

Two deadlines govern a move:

* the **soft** deadline decides whether to *start* another iterative-deepening
  iteration. It is consulted only between iterations, where stopping is free.
* the **hard** deadline aborts the search wherever it is, checked from inside
  the tree every ``CHECK_INTERVAL`` nodes.

The referee measures wall time around the whole request/response round trip, so
our budget sits strictly inside the clock we were handed, with room for JSON
encoding, pipe traffic and process scheduling.
"""

from __future__ import annotations

import os
from time import perf_counter

# Published competition increment. The override exists for test harnesses whose
# time control genuinely differs; it is configuration, not inference.
INCREMENT_MS = float(os.environ.get("CS_INCREMENT_MS", "500"))

# Wall time the referee attributes to us that we cannot measure from inside:
# writing the response, the pipe, and the parent waking up.
OVERHEAD_MS = 40.0
# Never plan to leave the clock below this.
RESERVE_MS = 200.0
# Below this, stop planning and just return something legal quickly.
PANIC_MS = 120.0

# Nodes between hard-deadline checks. perf_counter() costs ~50 ns, so this is
# well under 1% of a node while bounding overshoot to a fraction of a millisecond.
CHECK_INTERVAL = 1024

# How many more moves we assume this side has to make.
DEFAULT_MOVES_TO_GO = 26
# Endgames have fewer plausible moves per position and reward depth, so spend
# slightly harder there.
ENDGAME_MOVES_TO_GO = 20

# Fraction of the increment we plan to consume each move. Below 1.0 so the base
# clock drifts down slowly rather than being spent flat out.
INCREMENT_SHARE = 0.75
# No single move may commit more than this share of the usable clock.
MAX_SHARE_OF_CLOCK = 0.33

# An iteration costs roughly 2-4x the one before, so starting one with more than
# this fraction of the soft budget gone is usually wasted work.
#
# A stability-based version of this was tried and removed: it spent 28% more
# time per move than v0.2 for +0.29 ply, and the arena that followed could not
# distinguish it from noise. Extending on an unstable root is standard practice
# in strong engines and may well be right here, but it went in on intuition and
# nothing measured it, so it does not get to stay. Revisit it as its own
# experiment with an arena big enough to resolve it.
START_FRACTION = 0.60


class TimeManager:
    __slots__ = ("_hard", "_panic", "_soft", "_started")

    def __init__(self) -> None:
        self._started = 0.0
        self._soft = 0.0
        self._hard = 0.0
        self._panic = False

    # ------------------------------------------------------------ allocation

    def begin(self, time_left_ms: int, phase: int) -> None:
        """Open a budget for one move. ``phase`` is 0 (bare kings) to 24 (full board)."""
        self._started = perf_counter()
        self._panic = False

        usable = time_left_ms - OVERHEAD_MS - RESERVE_MS
        if usable <= 0.0 or time_left_ms <= PANIC_MS:
            # Nearly out of time. Spend a sliver and rely on the depth-1 result,
            # or on the legal fallback if even that does not finish.
            self._panic = True
            self._soft = self._hard = max(1.0, time_left_ms * 0.15)
            return

        moves_to_go = DEFAULT_MOVES_TO_GO if phase > 8 else ENDGAME_MOVES_TO_GO

        # The increment is credited every move, so it is genuinely spendable --
        # but only up to what we would still have left, so a short clock never
        # borrows against an increment it cannot afford to burn.
        increment_credit = min(INCREMENT_MS, usable) * INCREMENT_SHARE

        soft = usable / moves_to_go + increment_credit
        hard = min(usable * MAX_SHARE_OF_CLOCK, soft * 3.0)
        if soft > hard:
            soft = hard

        self._soft = soft
        self._hard = hard

    def begin_fixed(self, budget_ms: float) -> None:
        """Open a fixed budget, ignoring the clock. For benchmarking only."""
        self._started = perf_counter()
        self._panic = False
        self._soft = budget_ms
        self._hard = budget_ms * 1.25

    # --------------------------------------------------------------- queries

    def elapsed_ms(self) -> float:
        return (perf_counter() - self._started) * 1000.0

    def hard_expired(self) -> bool:
        return (perf_counter() - self._started) * 1000.0 >= self._hard

    def soft_expired(self) -> bool:
        return (perf_counter() - self._started) * 1000.0 >= self._soft

    def should_start_iteration(self) -> bool:
        """Is there time to begin another iterative-deepening pass?

        Stopping between iterations is free -- the previous depth's move is
        already committed -- so this is the only place the decision is made.
        """
        if self._panic or self._soft <= 0.0:
            return False
        elapsed = (perf_counter() - self._started) * 1000.0
        return elapsed < self._soft * START_FRACTION

    @property
    def soft_ms(self) -> float:
        return self._soft

    @property
    def hard_ms(self) -> float:
        return self._hard

    @property
    def panicking(self) -> bool:
        return self._panic
