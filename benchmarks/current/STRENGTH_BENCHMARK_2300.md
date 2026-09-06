# ~2300 BENCHMARK-A — definition (frozen 2026-09-05 23:34 UK, before any result was seen)

This is a **proxy**, labelled "~2300 BENCHMARK", not "exactly 2300 Chess.com".
No local opponent is calibrated to Chess.com's rating pool, and automating
play against Chess.com bots is not clearly permitted, so no public service
is used.

| field | value |
|---|---|
| OPPONENT IMPLEMENTATION | Stockfish, `C:\Users\epick\engines\stockfish\stockfish-windows-x86-64-avx2.exe` (114,007,552 bytes; sha256 prefix `c86215fa1977d53b` as recorded by the arena) |
| VERSION | `id name Stockfish 18` (reported by the binary on `uci`) |
| SETTINGS | `UCI_LimitStrength true`, `UCI_Elo 2300`, `Threads 1`, `Hash 16`; no opening book, no tablebases, no pondering; a fresh engine process per game |
| TIME CONTROL | 120 s + 0.5 s per side, 300-ply cap, adjudication as the internal arena (`harness/referee.py`); **draw claim `strict`** (a threefold ends the game only when a position has actually occurred three times) — see the amendment below |
| STRENGTH LIMIT | `UCI_Elo 2300` (range 1320–3190 in this build) |
| RATING CALIBRATION SOURCE | Stockfish's own documentation (wiki page "UCI Protocol and Stockfish Commands", fetched 2026-09-05 23:45 UK): "If `UCI_LimitStrength` is enabled, it aims for an engine strength of the given Elo. This Elo rating has been calibrated at a time control of 120s+1s and anchored to CCRL 40/4." |
| HARNESS | `tools.arena --opponent-uci <binary> --uci-elo 2300 --uci-hash 16` via `harness/uci_agent.py` (python-chess `SimpleEngine`, `Limit(white_clock, black_clock, increments)` fed from the referee's clock) |
| START SETS | `corpus/strength/dev.jsonl` (50 organiser starts, paired colours → 100 games) for the baseline and every screen; `holdout_a.jsonl` (50) for qualification; `holdout_b.jsonl` (50) for confirmation; hashes in `corpus/strength/FROZEN.md` |
| MACHINE | AMD Ryzen 5 5600X, 6 physical cores, Windows 11; 6 games in parallel, each game one Stockfish process and one ClaudeShark runner alternating, so one core per game |

## Limitations (read before quoting any number)

1. **CCRL 40/4 Elo is not Chess.com Elo.** The two pools are unrelated; the
   correspondence is unknown and is not claimed. "~2300" means "Stockfish's
   UCI_Elo 2300 setting", nothing more.
2. **Different time control from the calibration.** Stockfish calibrated the
   scale at 120 s + 1 s; the benchmark uses the competition's 120 s + 0.5 s.
   Limited-strength play is skill-level based (it picks among candidate moves
   with a rating-dependent randomness), so its strength drifts with the time
   control in ways the calibration does not cover.
3. **Style.** A handicapped strong engine does not play like a 2300 human or
   like a 2300 competition bot: it mixes near-perfect moves with deliberately
   chosen weaker ones. Results measure our robustness against that mixture.
4. **One machine, one binary.** The Stockfish build is the AVX2 Windows binary;
   the same settings on another machine give a similar but not identical opponent.
5. **Calibration sanity check owed.** If ClaudeShark scores far from 50% at
   this setting, the setting's relation to our own strength must be mapped
   (short screens at other `UCI_Elo` values) before any "2300 cleared"
   claim is made; the 2300/2400 labels are then reported alongside the
   `UCI_Elo` value at which ClaudeShark scores 50%.

## Amendment 2026-09-06 01:10 UK — draw claim must be `strict`

The first 100-game run (`rcc_vs_sf2300_dev_100`, `--draw-claim auto`) ended
29 games as threefold draws. Replaying every one of them: **0 were actual
threefolds; all 29 were "claimable via a move"** (python-chess's
`can_claim_threefold_repetition`), and in **18 of them Stockfish was the side
to move while winning** — the referee claimed the draw on behalf of a player
who would never have claimed it. RC-C's final oracle score in those games was
below −300 in 26 of the 29. The `auto` mode is the documented historical
artefact in `harness/referee.py`; it never mattered for engine-vs-engine
comparisons where both sides share it, but against an external opponent it
gifts the losing side (mostly us) a half point. From this amendment on the
benchmark is defined with `--draw-claim strict`; the `auto` run stays on
record as evidence and is not the baseline.

## Benchmark B (confirmation)

Same binary and settings on `holdout_b.jsonl` with a different position
set; if a second, independently calibrated ~2300 configuration becomes
available locally it replaces this. The limitation that A and B share one
strength-limiting mechanism is on record.

## ~2400 BENCHMARK-A (defined now, used only after 2300 is cleared)

Identical except `UCI_Elo 2400`, with new dev/val/holdout sets built from
positions not used for the 2300 stage.
