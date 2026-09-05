# Mac → PC handoff — 2026-09-05 14:55 UK (Mac)

REPOSITORY: https://github.com/kushagr4/ClaudeShark

BRANCH TO RESUME: `mac-full-development`

FINAL MAC HEAD: the commit that introduces this file. Its parent is
`3ec58017ca229c035a6a6a716b988a1e4e647c7a` (the state commit). Confirm with `git rev-parse HEAD` after pulling;
the full SHA is also in the chat reply that accompanied the push.

CURRENT SUBMITTED: **RC-B** (uploaded by the user 2026-09-05 12:01 UK), archive
`corpus/release/claudeshark_rc_b.zip`, frozen engine commit
`3d918a5db6233e9f0c7a4dcbee6713b83f758c11`. RC-A (`3a89bf3e…ff9b`, commit
`98c48c8`) is the historical fallback. No later upload was made.

CURRENT SUBMITTED SHA-256:
`f7b94b6507c39f32c6ba40f453e302812ba0bfbce1c8be16d2129ecb458c9c1a`

CURRENT CHAMPION: **RC-B** (`champions/rc_b`): +59 Elo over RC-A, 226 games,
80 informative families, bootstrap +25..+95, sleep-excluded +57.

CURRENT RC-C CANDIDATE: **candidate 3, identity-preserving speed** =
`champions/rcc_speed` = engine files at commit `f2543bd` (unchanged since):
incremental piece-square sum + inline out-of-check capture generation.

CANDIDATE STATUS: **Gate 0 PASSED** (fingerprints 1,708,269 / 1,852,716
identical to RC-B; 1,227 tests + 1 skip; +18.7% knps on the Mac).
**Gate 2 NOT DONE**: the 100-game timed screen vs RC-B was stopped at 59
games for this handoff (+18 =25 −16, non-decisive). Not champion.

LAST COMPLETED EXPERIMENT: check extension (candidates 1 and 2) —
**rejected**: −24 Elo over 100 games vs RC-B at the competition clock and
−0.55 ply on the 240 ordinary positions, despite repairing R20 12…Nxd5, R20
11…d5 and R17 47.Re1 at fixed depth (`2026-09-05-rcc-check-extension-prereg.md`).

ACTIVE BACKGROUND TASKS: NONE

WORKING TREE: CLEAN

IMPORTANT PARTIAL ARTIFACTS:
`corpus/daily/rcc/speed_vs_rcb_120s_100.PARTIAL-NON-DECISIVE-STOPPED-FOR-PC-HANDOFF.jsonl`
(+ `.txt`; no PGN, the arena writes it at the end). Not strength evidence.

DO-NOT-USE ARTIFACTS: the partial file above; the older ones listed in
`V2_ACTIVE_STATE.md` section 9. `corpus/daily/rcc/checkext_vs_rcb_120s_100.jsonl`
is valid but records a rejected candidate.

ROUND 20: **RC-B, high confidence by timing** (game started ~12:07 UK, six
minutes after the 12:01 upload; the platform log has no build identity; a
cold replay of all 43 Black moves is neutral). Lost to five consecutive
100–143 cp errors on moves 8–12; the decisive one, 12…Nxd5 (root +9, truth
−481), walks into 13.Qxd5! … 16.Nc7+, a fork by check one ply past the
capture-only quiescence. Files `corpus/daily/rcb/`, record in
`V2_ACTIVE_STATE.md` section 2 and `2026-09-05-rcc-check-extension-prereg.md`.
RC-A live games: R16 W, R17 D, R18 L, R19 W (`corpus/daily/rca/`,
`2026-09-05-rca-live-games-r16-r19.md`).

NEXT 3 ACTIONS:
1. Confirm the environment: `uv sync`, `uv run python -m pytest -q` (1,227
   passed, 1 skipped), `uv run python -m tools.bench --depth 6` (1,708,269 nodes).
2. Rerun candidate 3's Gate 2 in full: `uv run python -m tools.arena --agent
   champions/rcc_speed --opponent champions/rc_b --games 100 --base-ms 120000
   --increment-ms 500 --ply-cap 300 --workers 8 --corpus
   corpus/daily/pool/competition_actual_suite.jsonl --jsonl <new path>`; if not
   negative, 226 games; report families, bootstrap, leave-one-out, clock floor;
   then release check + `RC_C_UPLOAD_CARD.md` following `RC_B_UPLOAD_CARD.md`.
3. Ingest new rated games from the public team page (all RC-B since 12:01 UK
   unless a later user-confirmed upload is recorded), then continue the
   fingerprint-gated speed lane per `V2_ACTIVE_STATE.md` section 6.

## Windows resume commands (repo already cloned)

```
cd C:\Users\epick\Documents\ClaudeShark
git fetch origin
git checkout mac-full-development
git pull --ff-only origin mac-full-development
git rev-parse HEAD
git status
git config user.name "kushagr4"
git config user.email "ratrakushagra@gmail.com"
```

`git rev-parse HEAD` must return the commit that introduces this file (its
parent is `3ec58017ca229c035a6a6a716b988a1e4e647c7a`); see the chat reply for the full SHA. Do not create the PC
development branch on the Mac; decide that after pulling this exact state.
Nothing was uploaded to Chessathon during the handoff and no history was
rewritten.
