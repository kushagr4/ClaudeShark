# Verified competition specification

Every line here was read from the live documentation on the date shown. Quotes
are verbatim. This file exists because two spec claims have already had to be
corrected in this repository, and a wrong number here is the kind of mistake
that gets a submission rejected rather than merely scoring badly.

**Last verified: 2026-09-02**, from two sources that agree with each other:

* `https://aichessathon.com/docs`
* `https://aichessathon.com/docs/rules.md` (the canonical file the vendored
  `harness/rules.py` names as its source)

`https://aichessathon.com/terms` defers all technical detail to `/docs`.

## Verified facts

| | verbatim |
|---|---|
| Time control | "120s per side, plus 0.5s per move" |
| Init budget | "60s init budget runs before the clock starts" |
| CPU | "1 dedicated core" |
| RAM | "2 GB" |
| Network | "none, in either direction" |
| Filesystem | "read-only, plus 256 MB scratch at `/tmp`" |
| Submission size | **"<= 50 MB unzipped"** |
| Uploads | "6 uploads per team per day, the latest valid version plays" |
| Entry point | `def get_move(fen: str, time_left_ms: int) -> str`, returning UCI |
| Output cap | "4096 bytes per move; past it the game is lost" |
| Runtime | "Python 3.12 with torch, numpy, python-chess, onnxruntime and numba preinstalled at fixed versions" |
| Extra packages | "Nothing else installs and a `requirements.txt` in the zip is ignored" |
| Requesting a package | "Ask at hello@aichessathon.com for an addition and any grant is announced to every team" |
| Native binaries | "Native binaries inside the zip are rejected. What you ship has to be source a judge can read." |
| What may run | "Everything that runs is python from your zip plus the preinstalled stack." |
| Third-party engines | "Third party engines are prohibited: Stockfish, Lc0, Maia and any wrapper around one." |
| Process model | "One process serves one game, started fresh for every game"; "the process stays alive between moves, so state you keep in memory carries across your own moves" |
| Adjudication | "300 plies without a result is adjudicated on material, else drawn" |

## Dependencies: the precise position

There are two separate things and they are easy to conflate.

1. **Native binaries bundled in the zip are rejected.** Shipping a compiled
   `.so`, a static binary, or a Cython-built extension inside the submission is
   an automatic rejection: "What you ship has to be source a judge can read."
2. **Extra PyPI packages are not installed at all.** This is not a
   permitted/prohibited question — nothing installs, and a `requirements.txt`
   in the zip is ignored. Importing anything outside the five preinstalled
   packages crashes the agent, which loses the game. There is an email route to
   *request* an addition, and any grant is announced to every team, so a
   dependency only becomes usable after such an announcement.

Consequence for us: **Cython and hand-written C extensions are out.** Numba
stays available because it is preinstalled and ships as Python source that is
compiled at runtime — nothing compiled goes into the zip.

## Two claims that could not be confirmed

These were reported to this project as current, and both fetches above
contradict them. **The conservative reading is retained everywhere in this
repository until an organiser or a fresh reading of the live docs settles it.**

| claim reported | what the live docs say | stance taken |
|---|---|---|
| Submission limit is **200 MB expanded** | "<= 50 MB unzipped" | Kept 50 MB. Our submission is ~58 KB, so nothing depends on this; but a release gate that passes an oversized zip is worse than one that is too strict. |
| **Compiled PyPI dependencies with Linux wheels are permitted** | "Nothing else installs and a `requirements.txt` in the zip is ignored" | Kept "five preinstalled packages only". Acting on the looser reading risks an `ImportError` at validation, which loses every game. |

If the 200 MB figure is correct, the only change needed is the constant in
`tools/release_check.py` and the row above; nothing in the engine depends on it.

## Pondering: awaiting organiser clarification

The documentation read on 2026-09-02 does say, twice, that pondering is allowed
— `/docs`: "The process keeps its dedicated core after `get_move` returns, and
pondering is allowed", and `/docs/rules.md`: "Pondering allowed. Your process
keeps its core while the opponent thinks."

**We are nevertheless treating this as unresolved and are not implementing it.**
The decision is deliberate and conservative: background computation between
calls is the kind of behaviour where a misreading looks like abuse of the
harness rather than an honest mistake, and local referee behaviour is not proof
of competition policy. Clarification has been sought from the organisers.

Until an explicit answer arrives:

* the production agent does no work between `get_move` calls;
* no background threads or processes are started;
* `docs/PONDERING.md` holds design analysis only, and is not wired into
  anything.
