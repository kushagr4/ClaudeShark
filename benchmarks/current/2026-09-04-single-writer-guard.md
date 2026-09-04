# Single-writer ownership for experiment outputs, and the erratum that forced it

**Date:** 2026-09-04. **Branch:** `v2.2-development`. **Research-integrity
change only.** No engine file is touched; the depth-6 fingerprint is unchanged
at 1,712,405 nodes.

## 1. Three incidents, two of them corrupting

**Incident 1.** Two independent `tools.postmortem.play` roots were started
against `corpus/daily/pool/games/v21_vs_ratedv1.jsonl`. Each opened the path
with mode `w`, so the second truncated what the first had written, and both then
appended through their own handles. The result parsed as 29 games plus one torn
line. Retained as
`corpus/daily/pool/games/v21_vs_ratedv1.CORRUPT-DISCARDED.jsonl` and never used
as evidence; the match was re-run from scratch. The proximate cause was that
`pkill -f` silently matches nothing in this shell, so a kill that appeared to
succeed had not.

**Incident 2.** The same thing was set up again on
`v21_vs_ratedv1_actual.jsonl` — an earlier backgrounded launch had in fact
started, slowly, and a second was added. It was caught by an explicit
root-writer check **before any game was written**, both trees were killed, the
empty file removed, and one clean run started.

**Incident 3, and this one is an erratum.** With the clean 226-game match
running, the newly written guard was smoke-tested — against the live match's own
output path. The guard could not refuse it, because the running match had been
started before the guard existed and therefore held no ownership record. The
smoke test truncated the file and wrote two games; the live match, still holding
its handle at its old offset, continued writing past the gap. The file ended as
**587,848 bytes containing 4 parseable lines**. The match was stopped, the
artifact retained as
`corpus/daily/pool/games/v21_vs_ratedv1_actual.CORRUPT-DISCARDED-2.jsonl`, and
the run restarted. **No result was ever computed from it**, and none of the
conclusions in this session depend on it.

The lesson is not "be more careful with paths". It is that a smoke test of a
safety mechanism must not use production state, and that a guard which only
protects processes started after it was written protects nothing during the
transition.

## 2. The guard

`tools/matchlock.py`. Ownership of an output path is taken **before the output
file is opened**, because the failure being prevented is one process truncating
a file another is writing.

* The mechanism is an `O_CREAT | O_EXCL` sidecar, `<output>.owner`. That is
  atomic; "check whether the file exists, then create it" is not, and has a
  window exactly wide enough for this bug.
* The record holds the pid, the full command, the start time and the output
  path, so a refusal can name the process to look at rather than saying "busy".
* A second root **fails closed** with that message. The data file is not opened,
  not created and not modified on the refusal path.
* A stale record left by a killed process is **never removed automatically**.
  Silently reclaiming a path because its owner looks dead is how incident 1
  would be re-enabled. Recovery is `--force-unlock`, which refuses while the
  recorded process is alive and removes only the sidecar.
* Liveness on Windows goes through `OpenProcess` + `WaitForSingleObject`, not
  `os.kill(pid, 0)` — on Windows that call terminates the process rather than
  probing it. It errs toward "alive", because refusing to start is the safe
  failure.
* Ownership is released on normal exit and on an exception, and `release` will
  not remove a record belonging to another pid.

Wired into `tools/postmortem/play.py` only. Eleven tests in
`tests/test_matchlock.py` cover: the first writer acquiring and recording
itself; the second being refused while the first lives; different paths not
contending; **a refusal leaving the data file byte-identical**; a stale record
surviving a refusal rather than being reused; `--force-unlock` recovering a
stale record while leaving the data; `--force-unlock` refusing a live owner;
release on normal and exceptional exit; release not removing another process's
record; an unreadable record still blocking; and the liveness probe itself.

## 3. Demonstrated, not asserted

With the re-run match owning the path:

```
$ uv run python -m tools.postmortem.play ... --out corpus/daily/pool/games/v21_vs_ratedv1_actual.jsonl
tools.matchlock.OutputBusyError: ...v21_vs_ratedv1_actual.jsonl is already owned by pid 22392 (still running).
  owner command: ...--cand champions/v2_1_kingpawn --base champions/rated_v1 ...
  owner started: 2026-09-04T11:58:58+0100
  owner record:  ...v21_vs_ratedv1_actual.jsonl.owner
Stop that process, or write to a different --out path.
```
