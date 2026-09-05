# Mac handoff — 2026-09-05 07:25 (from Windows)

REPO: https://github.com/kushagr4/ClaudeShark

BRANCH TO FETCH ON MAC: `v2.2-development`

FINAL WINDOWS HEAD: the commit that introduces this file ("Windows handoff
before Mac development"); its parent is `a391310`. Confirm with
`git log -1 --format=%H` after pulling; the full SHA is also in the chat reply
that accompanied the push.

CURRENT SUBMITTED BUILD: RC-A / exact rated-v1
(`corpus/release/claudeshark_rated_v1_rc_a.zip`, commit `98c48c89b3a8142e6567e5f46b2d2036df7297d1`)

CURRENT SUBMITTED ZIP SHA-256:
`3a89bf3e2fbfab0b7e07baf2fff7e0edf2288fc2a4d372e8eda823db1767ff9b`

CURRENT BEST PROVEN BUILD: RC-A / exact rated-v1 (nothing has beaten it on
the organiser-start distribution; every candidate of the last day was
rejected — see `V2_ACTIVE_STATE.md` sections 3 and 4).

CURRENT EXPERIMENTAL CANDIDATE: C1-search-staged, **design only**.
`staged_moves` in `cs_ordering.py` is written and identity-tested
(`tests/test_staged_moves.py`) but not wired into `cs_search.py`; the engine's
behaviour is unchanged. Gate 0 and a short timed screen remain.

BACKGROUND TASKS: NONE (verified by process sweep before the commit).

WORKING TREE: CLEAN (untracked, deliberately not committed: rejected
`champions/v2_1_kingpawn_sf*`/`_tempo*` variants, `corpus/daily/report_chunks/`
shards, `analysis/refresh_2026-09-05/collect.log`).

NEXT STEPS ON MAC:
1. Confirm the environment: `uv run python -m pytest -q` (1,205 pass) and
   `uv run python -m tools.bench --depth 6` (1,712,405 nodes).
2. Finish C1: wire `staged_moves` into `_negamax` behind `CS_STAGED_MOVES`
   with the seventh-rank guard; Gate 0 = identical per-position node counts
   with the flag on and off, NPS before/after; short timed screen on
   `corpus/daily/pool/competition_actual_suite.jsonl`; freeze RC-B only if the
   tree is identical and the screen is not negative.
3. Lane B (attack blindness): pre-registered positive/negative set from
   `corpus/daily/rated15_key_positions.json` and the round 10/11 sequences;
   smallest separating signal; never broad king safety.

Mac commands:

```
git clone https://github.com/kushagr4/ClaudeShark.git
```

or, if already cloned:

```
git fetch origin
```

then:

```
git checkout v2.2-development
git pull --ff-only origin v2.2-development
git config user.name "kushagr4"
git config user.email "ratrakushagra@gmail.com"
```

Do not create the Mac development branch from here; create it on the Mac
after pulling this exact state. Nothing was uploaded to Chessathon and no
history was rewritten on Windows.
