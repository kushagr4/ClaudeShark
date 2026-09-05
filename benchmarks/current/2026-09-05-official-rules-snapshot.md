# Official rules snapshot, 2026-09-05 01:11 local

Fetched with plain unauthenticated HTTP from the two public pages, saved raw as
`analysis/rules/terms_2026-09-05.html` and `analysis/rules/docs_2026-09-05.html`
with tag-stripped text beside them. The rules page carries the version stamp
**`Competition · 2026-08-31.v3`**. The docs page carries no version stamp. The
rules page says "the latest dated competition rules take precedence for
competition matters" and delegates every operational number to the docs.

## What the docs say, quoted

| topic | current official text |
|---|---|
| API | `def get_move(fen: str, time_left_ms: int) -> str`; one JSON object per line on stdin/stdout, handled by the provided runner |
| process | "One process serves one game, started fresh for every game." "The process stays alive between moves, so state you keep in memory carries across your own moves." |
| **opponent's clock** | **"Your process is suspended while your opponent moves, so work you leave running between your own moves does not run."** |
| threads | "During your own move one thread is fastest, since threads past the first share the single core and cost you time." "Processes 128. On one core, threads past the first cost you time" |
| init | "The 90s init budget covers importing your agent and runs before the clock starts" (failure reference: "no ready line within the 90s init budget" = loss) |
| CPU | "one core of an AMD EPYC 9V74 at 2.60 GHz, yours alone while you think" |
| memory | 2 GB; filesystem read-only plus 256 MB scratch at `/tmp`, empty per game |
| network / GPU | none |
| clock | "120s per side, plus 0.5s per move"; "The increment lands after you move" |
| game end | "FIDE rules. 300 plies without a result is adjudicated on material, else drawn"; the referee claims threefold and fifty-move draws automatically |
| ladder | "rated rounds every hour, 08:00 to 22:00", Glicko-2 shown as an Elo-style number; "The ladder only seeds the final Swiss" |
| openings | "every game starts from a curated position that is close to level. Knockout ties play each position once with each colour" |
| qualification | "a 13-round Swiss over the locked builds decides the order the 50 London seats fill, by points"; odd field gives one 1-point bye; "Seats go one per UK member and at most two per team" |
| tie-breaks | "points, Buchholz, head-to-head, earlier final submission" |
| eligibility | "the ladder is open worldwide. A team enters the final Swiss if at least one member is a UK university student, and only its UK members can take a London seat, verified before invites" |
| Python | 3.12; torch 2.13.0+cpu, numpy 2.5.2, python-chess 1.11.2, onnxruntime 1.29.0, numba 0.67.0; requirements.txt ignored; imports outside the set crash |
| binaries | "Native binaries inside the zip are rejected"; Cython impossible; numba JIT allowed |
| size | "50 MB unzipped at most"; files at the zip root |
| uploads | "10 uploads per team per day"; "Uploads close 11 September 11:00"; "your latest submission that passed validation" plays |
| validation | "build, then two smoke games at the match clock, one as each colour" |
| engines | Stockfish, Lc0, Maia, "any wrapper around one and any port or translation of one" prohibited; "Your moves come from code you wrote." |
| training data | "training it on positions an existing engine labelled is allowed"; starting from a published network is not |
| **lookup data** | **"a database of engine moves or evaluations shipped for lookup at runtime is an engine, not training data."** |
| books / tablebases | "Opening books and endgame tablebases are permitted as shipped data, and chess.polyglot and chess.syzygy are in the base image." |
| readability | "What you ship has to be source a judge can read"; weights (.onnx/.safetensors/.pt) are fine; obfuscated agents are disqualified; disqualification can be retroactive |
| output | stdout is redirected to stderr before import, so `print` is safe; 8 KB of output kept |
| Daily Five | 6 to 10 September, one attempt a day, five positions, 20 minutes; "no engines, no other people, no other accounts, no looking positions up" |

## Differences from the take-over brief

| brief said | official page says | consequence |
|---|---|---|
| pondering is explicitly allowed; the core remains available after `get_move` returns | **the process is suspended while the opponent moves; work left running between moves does not run** | **the pondering lane is closed by the rules, not by engineering.** No thread, no background search, nothing can use the opponent's clock. Extra threads on our own move are explicitly slower. |
| docs state a 60 s init budget; logs show 90 s | docs state **90 s**, the failure reference states 90 s, and every direct log states `Budget 90.0 s` | no discrepancy remains; the engine's ~2 s startup is irrelevant either way |
| six uploads per team per day | **10** | more room for a validated final, not a licence to iterate |
| a public-start book of offline oracle moves is a legal candidate | opening books are permitted **as shipped data**, but "a database of engine moves or evaluations shipped for lookup at runtime is an engine" | **a Stockfish-annotated book is prohibited.** A book is legal only if its moves come from our own code (ClaudeShark's own deeper offline search) or from a conventional non-engine source such as human master games. |
| Swiss over locked builds, tie-breaks, 50 seats, 11 Sept 11:00 close, 2 GB, no GPU, no network, 120+0.5, 50 MB, Python 3.12, package list, no native binaries, books and tablebases allowed, readable source | identical | none |

## What this does to the overnight plan

* **Pondering:** audit answer is "not implemented" (`agent.py` is single-threaded,
  no `threading` anywhere in the engine), and the rules make it worthless. No
  prototype is built. Any candidate that spawned a thread would also violate
  "one thread is fastest".
* **Public-start book:** recurrence is still measured, because it is cheap and it
  decides whether *any* book is worth the risk; but the only legal source of
  book moves is ClaudeShark's own offline search or non-engine data.
* **Adjudication at 300 plies on material** is a rule the engine does not know
  about; long games in the public corpus (300 and 213 plies) are relevant to it.
* **Eligibility:** the page ties Swiss entry to a UK university student on the
  team. Not interpreted here. Action item for the user: **get written organiser
  clarification.**

## Rules of record for the development day (re-fetched 07:00 local)

Both pages re-fetched at 07:00 (`analysis/rules/*_2026-09-05T0700.html/.txt`)
are **line-for-line identical** to the 01:11 snapshot. No organiser
`rules.md` or e-mail text exists on this machine; the user's summary of the
organiser e-mail (90 s init, 10 uploads/day, process suspended while the
opponent thinks) agrees with the live docs page on every point, and the
"60 s / 6 uploads / pondering allowed" wording exists only in stale search
caches. The live docs page is therefore taken as the frozen rules of record:

| clause | value of record |
|---|---|
| init budget | 90 s |
| uploads | 10 per team per day; close 11 Sept 11:00; latest passing plays |
| process | suspended while the opponent moves; **no pondering possible** |
| threads | one is fastest; extra threads cost time |
| books | permitted as shipped data (chess.polyglot available) |
| tablebases | permitted as shipped data (chess.syzygy available) |
| engine-annotated training data | permitted for training a model we ship |
| **lookup data** | "a database of engine moves or evaluations shipped for lookup at runtime is an engine" — **prohibited**; a book may not contain Stockfish choices |
| submission | 50 MB unzipped, files at the zip root, readable source, no native binaries |
| environment | Python 3.12; torch 2.13.0+cpu, numpy 2.5.2, python-chess 1.11.2, onnxruntime 1.29.0, numba 0.67.0; nothing else |

Not revisited again today unless the organisers issue an update.
