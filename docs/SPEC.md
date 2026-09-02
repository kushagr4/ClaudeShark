# Verified competition specification

Every line here was read from the live documentation on the date shown. Quotes
are verbatim. This file exists because two spec claims have already had to be
corrected in this repository, and a wrong number here is the kind of mistake
that gets a submission rejected rather than merely scoring badly.

## Provenance, and an unresolved disagreement

There are two sources for the four packaging facts below and **they disagree**.
Both are recorded, with timestamps, rather than one being quietly picked.

**Source A — automated fetch of the live pages.**
Last read **2026-09-02 09:53 UTC** (10:53 local, UTC+01:00), from
`https://aichessathon.com/docs` and `https://aichessathon.com/docs/rules.md`
(the canonical file the vendored `harness/rules.py` names as its source).
`https://aichessathon.com/terms` defers all technical detail to `/docs`.
Three separate reads on 2026-09-02, the last of them uncached, returned
identical text.

**Source B — participant reading of the live `/docs` page**, reported
2026-09-02 and stated to be current. A logged-in or newer deploy that the
automated fetch cannot reach is a plausible explanation for the difference.

| topic | Source A (fetched, verbatim) | Source B (reported) |
|---|---|---|
| Submission size | "A submission is a zip, 50 MB unzipped at most." | 200 MB expanded |
| `requirements.txt` | "Nothing installs at validation and a `requirements.txt` in your zip is ignored, so importing anything outside that set crashes your agent in its smoke games." | supported |
| Compiled PyPI wheels | not permitted; only the five preinstalled packages | permitted |
| Native binaries in the zip | "Native binaries inside the zip are rejected. What you ship has to be source a judge can read." | rejected — **both agree** |

**What the tooling does about it.** `tools/release_check.py` uses Source B's
200 MB limit. That choice is safe in either world: the submission is about
58 KB, so no engine decision depends on the number, and a size check that is too
lenient cannot crash an agent — it can only allow an upload the platform would
reject, which is visible immediately in the validation log.

The dependency question is handled differently, because there the two readings
have opposite failure modes. The checker now validates imports against the
standard library, the five preinstalled packages, **and anything declared in a
`requirements.txt` shipped inside the zip**. Under Source B that is correct
behaviour. Under Source A it is also correct, because we ship no
`requirements.txt` and import nothing outside the preinstalled set, so the check
behaves exactly as it did before. Nothing is silently disabled either way.

**Before relying on an extra dependency, confirm with the organisers.** Source A
states plainly that an undeclared import "crashes your agent in its smoke
games", and that failure costs every game rather than producing a warning. The
asymmetry is large enough to be worth an email to hello@aichessathon.com.

## Everything below is Source A, verbatim

## Verified facts

| | verbatim |
|---|---|
| Time control | "120s per side, plus 0.5s per move" |
| Init budget | "60s init budget runs before the clock starts" |
| CPU | "1 dedicated core" |
| RAM | "2 GB" |
| Network | "none, in either direction" |
| Filesystem | "read-only, plus 256 MB scratch at `/tmp`" |
| Submission size | "A submission is a zip, 50 MB unzipped at most." — **disputed, see above; the tooling uses 200 MB** |
| Uploads | "6 uploads per team per day, the latest valid version plays" |
| Entry point | `def get_move(fen: str, time_left_ms: int) -> str`, returning UCI |
| Output cap | "4096 bytes per move; past it the game is lost" |
| Runtime | "Python 3.12 with torch, numpy, python-chess, onnxruntime and numba preinstalled at fixed versions" |
| Extra packages | "Nothing else installs and a `requirements.txt` in the zip is ignored" — **disputed, see above** |
| Requesting a package | "Ask at hello@aichessathon.com for an addition and any grant is announced to every team" |
| Native binaries | "Native binaries inside the zip are rejected. What you ship has to be source a judge can read." |
| What may run | "Everything that runs is python from your zip plus the preinstalled stack." |
| Third-party engines | "Third party engines are prohibited: Stockfish, Lc0, Maia and any wrapper around one." |
| Process model | "One process serves one game, started fresh for every game"; "the process stays alive between moves, so state you keep in memory carries across your own moves" |
| Adjudication | "300 plies without a result is adjudicated on material, else drawn" |

## Dependencies: the precise position

Two things are easy to conflate, and they are separate under **both** readings.

1. **Native binaries bundled in the zip are rejected.** Both sources agree.
   Shipping a compiled `.so`, a static binary, or a Cython-built extension
   inside the submission is an automatic rejection: "What you ship has to be
   source a judge can read." This is the one packaging rule that is not in
   dispute, and `tools/release_check.py` enforces it by scanning every file in
   the archive for executable magic bytes as well as by extension.

2. **Whether a *dependency* can be declared is disputed.** Source B says a
   `requirements.txt` is supported and compiled PyPI wheels are permitted;
   Source A says nothing installs and such a file is ignored. Note these are
   compatible on the point that matters most: a wheel installed by the platform
   is not a binary *bundled in the zip*, so permitting wheels does not weaken
   rule 1 at all.

Consequence for us today: nothing changes. The engine imports only
`python-chess` and the standard library, ships no `requirements.txt`, and
contains no compiled artefact. **Numba remains the safe route to compiled speed
under either reading** — it is preinstalled, and it ships as Python source
compiled at runtime, so nothing compiled enters the zip.

Consequence for `docs/MOVEGEN.md`: if Source B is correct, a Cython or C
extension distributed as a published PyPI wheel becomes theoretically available
where it previously was not. That does not change the recommendation — the
analysis there rejects a move-generator rewrite on engineering risk, not on
packaging grounds — but the packaging bullet has been corrected.

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
