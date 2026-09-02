# Pondering — design analysis only

**Status: awaiting organiser clarification. Not implemented. Not scheduled.**

The documentation read on 2026-09-02 does state that pondering is allowed
(`/docs`: "The process keeps its dedicated core after `get_move` returns, and
pondering is allowed"; `/docs/rules.md`: "Pondering allowed. Your process keeps
its core while the opponent thinks"). This project is nevertheless treating the
question as open and the production agent does no work between `get_move` calls.

The reasoning: background computation between calls is the one category of
behaviour where a misreading looks like exploiting the harness rather than an
honest mistake. Local referee behaviour is not evidence of competition policy —
our harness simply blocks on a pipe read and would never notice a background
thread, which proves nothing about what the platform permits or measures. The
cost of waiting for an explicit answer is some Elo; the cost of being wrong is
the entry. That trade is not close.

This note exists so the work is ready if and when it is approved. Nothing below
is wired into anything.

## What it would be worth

On 120 s + 0.5 s, both sides think for comparable stretches. Search time that
overlaps the opponent's turn is free on our clock, so a pondering engine that
guesses the opponent's reply correctly roughly doubles the thinking behind the
move it eventually plays. Realistically the hit rate on the predicted reply is
somewhere around 40–70% for an engine of this strength, and a miss still leaves
a warmed transposition table, so the expected gain is well short of a doubling
but clearly positive — plausibly comparable to a full extra ply.

## How it would work

**Starting.** At the end of `get_move`, the principal variation gives our move
and the expected reply. Push both, then start a background search of the
resulting position with no deadline. The thread must be a daemon so it can never
keep the process alive.

**Predicting the reply.** The second move of our own PV is the natural guess and
costs nothing to obtain. There is no need for a separate opponent model.

**Invalidating stale analysis.** The next `get_move` arrives with a FEN. Compare
it against the position we pondered:

* *Hit* — the opponent played the predicted move. The transposition table is
  already warm for exactly this position, and the search simply continues with a
  real deadline. The root move ordering from the ponder search is reusable.
* *Miss* — the opponent played something else. The ponder results are not
  *wrong*, only irrelevant: transposition entries are keyed by position, so
  entries for positions that did not occur are dead weight but never incorrect.
  Nothing needs to be discarded for correctness; the table simply carries some
  useless entries.

This is the property that makes pondering safe here. Because the transposition
table is keyed on an exact position descriptor and never on "the current
search", a wrong guess cannot corrupt anything.

**Contention on one core.** This is the hard part, and the reason a naive
implementation would lose Elo rather than gain it. With a single dedicated core,
a ponder thread still running when `get_move` is called competes directly with
the real search, and the GIL makes that worse: the pondering thread holds the
interpreter for its share of switch intervals regardless of priority.

The ponder thread must therefore be **stopped and joined before any real search
begins**, not merely signalled. Concretely: a `threading.Event` the ponder loop
checks on the same node counter that already checks the clock, set at the very
top of `get_move`, followed by a bounded `join()`. If the join times out, the
safe response is to proceed anyway and accept one move of contention, because
blocking is worse than sharing.

**Shutdown.** Daemon thread, an explicit stop event, and a join with a timeout.
No process spawning: the process budget is generous but a second process on one
core buys nothing and complicates teardown.

**State that is safe to reuse.** The transposition table (position-keyed, so
always valid), and the history heuristic (a soft ordering hint whose staleness
costs at most a little ordering quality). Killer moves are indexed by ply and
would need clearing, since ply means something different in a search rooted two
moves later. The repetition history must not be updated by a ponder search,
because the positions it visits were never actually played.

## Remaining risks even if approved

1. **The single core.** Any overlap between pondering and a real search is a
   direct loss. The stop-and-join discipline has to be exactly right, and it has
   to be tested under load, not just in isolation.
2. **Init and teardown interactions.** A thread still running when the game ends
   could delay process exit or produce output after the final move. Daemon
   threads plus an explicit stop event address this, but it needs testing.
3. **Memory.** A ponder search fills the same fixed-size table. It is bounded by
   construction, so this is a non-issue for us, but it would not be for a
   growing table.
4. **Measurement difficulty.** The gain only appears in real games on a real
   clock. None of the deterministic instruments in this repository — fixed-depth
   benchmarks, tactics, move quality — can see it at all. Validating it means
   arena games, and the session record already shows how easily a change that
   only manifests under a clock can be validated by the wrong instrument.

## If approval arrives

Implement behind a flag defaulting to **off**, measure with an arena of at least
400 games at a competition-scale per-move budget, and only then flip the
default. Do not ship it on the strength of a plausible argument; that is exactly
the mistake the aspiration-window regression already taught this project once.
