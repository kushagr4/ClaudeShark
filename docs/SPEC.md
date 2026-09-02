# Verified competition specification

Every line here was read from the live documentation on the date shown. Quotes
are verbatim. This file exists because two spec claims have already had to be
corrected in this repository, and a wrong number here is the kind of mistake
that gets a submission rejected rather than merely scoring badly.

## Provenance, and an unresolved disagreement

There are two sources for the four packaging facts below and **they disagree**.
Both are recorded, with timestamps, rather than one being quietly picked.

**Source A — automated fetch of the live pages.**
Last read **2026-09-02 10:03:44 UTC** (11:03:44 local, UTC+01:00), from
`https://aichessathon.com/docs`, the rendered page (not a cached `rules.md`).
`https://aichessathon.com/terms` defers all technical detail to `/docs`.
**Four separate reads on 2026-09-02** returned identical text on these points,
the later ones uncached.

Verbatim from that retrieval:

> "A submission is a zip, 50 MB unzipped at most."
>
> "Nothing installs at validation and a `requirements.txt` in your zip is ignored."
>
> "The environment is fixed. The container ships Python 3.12, the full standard
> library, and five preinstalled packages" — importing anything outside this set
> "crashes your agent in its smoke games."
>
> "Native binaries inside the zip are rejected. What you ship has to be source a
> judge can read."

**Source B — participant reading of the live `/docs` page**, reported
2026-09-02 and stated to be current. A logged-in or newer deploy that the
automated fetch cannot reach is a plausible explanation for the difference.

| topic | Source A (fetched, verbatim) | Source B (reported) |
|---|---|---|
| Submission size | "A submission is a zip, 50 MB unzipped at most." | 200 MB expanded |
| `requirements.txt` | "Nothing installs at validation and a `requirements.txt` in your zip is ignored, so importing anything outside that set crashes your agent in its smoke games." | supported |
| Compiled PyPI wheels | not permitted; only the five preinstalled packages | permitted |
| Native binaries in the zip | "Native binaries inside the zip are rejected. What you ship has to be source a judge can read." | rejected — **both agree** |

**What the tooling does about it.** `tools/release_check.py` follows **Source A**,
the text actually retrievable from the live page: a 50 MB limit, and imports
restricted to the standard library plus the five preinstalled packages.

This reverses a previous commit that had adopted Source B's 200 MB figure. The
instruction then was to match the live page; a fresh read of the live page still
returns 50 MB, so matching it means 50 MB. Nothing practical turns on it — the
submission is about 66 KB — but the two failure modes are not symmetric:

* a size limit that is **too strict** costs nothing, since we are three orders
  of magnitude below either figure;
* an import allowlist that is **too lenient** costs everything, because Source A
  says an unresolvable import "crashes your agent in its smoke games", and that
  is every game rather than a warning.

`declared_requirements()` in the checker still parses a shipped
`requirements.txt`, gated behind `REQUIREMENTS_HONOURED = False`. Flipping that
one constant is the entire change if the organisers confirm Source B. The
checker also now warns if a `requirements.txt` is shipped at all, since under
Source A it would be silently ignored and give false confidence.

**Before relying on an extra dependency, confirm with the organisers** at
hello@aichessathon.com.

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
