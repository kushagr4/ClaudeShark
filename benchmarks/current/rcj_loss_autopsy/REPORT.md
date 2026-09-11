# RC-J real-loss autopsy (R76–R105)

RC-J = `2bf6885`. Read-only diagnosis. Nothing was implemented, no arena was run, nothing was pushed. Heavy work ran one job at a time.

**Method**
- **Reference.** Isolated Stockfish (sha256 `c86215fa…`, the same binary as C26) on every RC-J move: 925 moves, fresh hash per analysis. The played move and the best move were scored from the same root via root-restricted search. The last *exact* info line was used, and scores were taken from RC-J's point of view.
- **Result categories.** From Stockfish's WDL expectation E: win at E ≥ 0.75, loss at E ≤ 0.25, draw otherwise.
- **Selection.** The first decisive error was chosen by a frozen rule, then re-verified at 10M nodes.
- **Depth test.** RC-J (shipped core) was run from a cold table at its recorded clock and at fixed depths d, d+1 and d+2. It was classified by frozen code: GOOD ≤ 30 cp, BAD ≥ 40 cp.
- **Causal categories.** Seven read-only agents assigned them from measured evidence. Three adversarial reviewers then corrected them.

## 1. RC-J real-loss verdict

| | games | W | D | L | score |
|---|---|---|---|---|---|
| R76–R93 | 18 | 7 | 5 | 6 | 9.5 = 52.8% |
| R94–R105 | 12 | 3 | 1 | 8 | 3.5 = 29.2% |
| **R76–R105** | **30** | **10** | **6** | **14** | **13.0 = 43.3%** |

- The inventory is complete: rounds are contiguous and every termination is consistent with the final position.
- R94–R105 were not on disk. They were fetched from the public team page (a signed-out read) and include **8 of the 14 losses**.
- Losses: R79, R81, R83, R88, R91, R92, R94, R95, R98, R99, R101, R102, R103 and R105.
- RC-I games (R69–R75) are excluded.

## 2. C26 prior evidence

- **Exists:** yes. Branch `kushagra/c26-failure-diagnosis`, commit `f575372`.
- **Positions:** 12, one per game. Codex's corpus took the first RC-J move after which the site's eval (Stockfish 16, depth 16) crossed −200 cp.
- **Games represented:** RC-I R70, R73, R74 and R75; RC-J R79, R80, R81, R83, R88, R91, R92 and R93. That is 6 RC-J losses and 2 draws. R94–R105 did not exist yet.
- **Methodology trustworthy: PARTIAL.**
  - The Stockfish check was sound: 3M nodes, fresh hash, per-line bounds.
  - But the positions were threshold crossings, not first decisive errors. Four of its six RC-J-loss positions are later symptoms or non-errors:
    - R92-18b was the reference move itself.
    - R83-21w comes one move after the decisive m20.
    - R88-31b comes 14 moves after the decisive m17.
    - R91-17w comes after the decisive m13.
  - The depth ladder was cold-only and meaningful for just two RC-J losses.
- **Original claim:** "+1 repaired 0, +2 repaired 0; RC-J searches the better move, values it, and rejects it." My own later paraphrase added "evaluation errors of 75–415 cp". That range really came from C27's table and included an RC-I draw.
- **Audited claim:**
  - **Practical core survives, and is stronger.** On the correctly selected 14-loss set, +1 ply repairs **0 of 14** decisive errors.
  - **The literal "+2 repaired none" does not survive.** Three of 19 confirmed errors are repaired within +2 ply.
  - **The "75–415 cp evaluation errors" does not survive.** Decisive errors are 57–158 cp at 10M, and non-repair by depth is not proof of an evaluation error.

## 3. Loss table

The cp loss is measured at 10M nodes. d is RC-J's reconstructed cold depth; live depth may be up to ±1 ply different.

| round | opp | col | first decisive position | RC-J | ref | cp | E | clock | d | deeper RC-J | category | conf |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 79 | bentheboss1236 | W | `rnbq1rk1/1p1nbpp1/7p/p1ppP3/3P4/5NP1/PPQN1PBP/R1B2RK1 w - - 0 12` | Nb3 | Rd1 | 81 | 0.49→0.25 | 109 s | 13 | DOES NOT REPAIR | UNKNOWN (eval-suspect) | low |
| 81 | Logang | B | `r2qk2r/pp2bppp/2np1n2/4p1Bb/4P3/N1N2P2/PPPQ2PP/R3KB1R b KQkq - 4 10` | h6 | d5 | 93 | 0.47→0.12 | 115 s | 10 | DOES NOT REPAIR | UNKNOWN | low |
| 83 | Oxchess | W | `r1b1r3/p1p5/1p1n2k1/2p2ppp/P7/2PPBPN1/2P3PP/4RRK1 w - - 0 20` | Bf2 | Bd2 | 158 | 0.48→0.00 | 78 s | 14 | DOES NOT REPAIR (switches to f4, 118) | UNKNOWN (search-side suspect) | low |
| 88 | rogo | B | `r3r1k1/1ppq1ppp/1b1p1nb1/pP2p3/P1BPPn2/1QP2NNP/R4PP1/2B1R1K1 b - - 8 17` | Rac8 | N4h5 | 111 | 0.45→0.06 | 95 s | 11 | UNSTABLE (cold moves also bad) | other static eval (PeSTO knight square) | low |
| 91 | TriggerFish | W | `r4rk1/pp2ppb1/1q1p2pp/2pPn2P/6b1/P2P2P1/1PP1NPB1/R1BQ1RK1 w - - 1 13` | f4 | f3 | 103 | 0.50→0.24 | 102 s | 14 | DOES NOT REPAIR | UNKNOWN | low |
| 92 | Rush hour | B | `r1bq1rk1/1p1pppbp/p1n2np1/2P5/3N4/2N3P1/PP2PPBP/R1BQ1RK1 b - - 0 9` | e5 | h6 | 63 | 0.36→0.09 | 111 s | 13 | UNSTABLE (cold plays Re8, GOOD) | state-dependence | low |
| 94 | POFPOF | W | `8/1r2pk2/p2p4/P2P1p2/P1p3p1/2P3P1/rb1B1PK1/1R1R4 w - - 4 44` | Bc1 | Rh1 | 138 | 0.50→0.04 | 52 s | 16 | DOES NOT REPAIR | UNKNOWN | low |
| 95 | The W in Woxbridge | B | `1r2r1k1/pp3pp1/3b1qp1/2p5/1nP1B3/4N1PP/P2PPP2/RQ3RK1 b - - 0 20` | Qe6 | Qd4 | 87 | 0.47→0.07 | 85 s | 12 | DOES NOT REPAIR | UNKNOWN (search-side suspect) | low |
| 98 | zz | W | `r7/2pqrp1k/p1np1npp/1p1b4/1P1P4/P1QBB2P/3N1PPK/2R1R3 w - - 5 25` | Bc2 | Nf1 | 95 | 0.47→0.07 | 77 s | 11 | UNSTABLE (cold Kg1 keeps the draw) | state-dependence | medium |
| 99 | Yumo | B | `2b3k1/1N3pb1/p1p2npp/P3p3/2P3P1/1Q3P2/1P2PB1P/2q2BK1 b - - 0 25` | Be6 | e4 | 57 | 0.22→0.01 | 75 s | 13 | REPAIRS at +2 only | search horizon (already lost at 10M) | medium |
| 101 | rogo | B | `r4rk1/2q2pb1/3p2p1/8/1Q1PPp2/pRP2P2/P5B1/1R4K1 b - - 6 29` | Rfd8 | Bf6 | 63 | 0.86→0.53 | 75 s | 12 | UNSTABLE (cold Rfc8, 88) | UNKNOWN | low |
| 102 | YG | W | `r1bq1rk1/pp3ppp/3b1n2/1Bppn3/5B2/2P1P2N/PP1N1PPP/R2Q1RK1 w - - 0 10` | Nf3 | Be2 | 148 | 0.35→0.00 | 114 s | 13 | DOES NOT REPAIR | UNKNOWN | low |
| 103 | Quant Larper | W | `r5k1/4pp1p/3p2pQ/3P4/1q6/r2bPBPP/5PK1/2R1R3 w - - 5 25` | Red1 | Qf4 | 87 | 0.49→0.08 | 84 s | 12 | REPAIRS at +2 only | search horizon | medium |
| 105 | Boardzempic | B | `r1bq1r1k/1p1p2bp/p5p1/3Bpp2/N1P5/4Q1P1/PP2PP1P/R4RK1 b - - 3 16` | Rb8 | d6 | 133 | 0.37→0.00 | 86 s | 13 | DOES NOT REPAIR | piece activity (bishop locked by own pawns) | low |

**Other confirmed ≥100 cp result flips made while RC-J was not yet lost:**

| position | move | cp | depth result |
|---|---|---|---|
| R81 m8 | Bh5 | 125 | **repaired at +1** |
| R94 m33 | Ra1 | 199 | UNSTABLE; cold plays Stockfish's Rbe1 |
| R94 m35 | Rb1 | 159 | not repaired |
| R101 m57 | Ba7+ | **546** | not repaired to depth 23 |
| R101 m61 | Bd6 | **545** | UNSTABLE; cold Be5 is worse |

R101 m52 was not confirmed (0 cp at 10M).

## 4. Depth-repair summary

| | count | repaired by deeper RC-J | not repaired | unstable | unknown |
|---|---|---|---|---|---|
| serious errors (confirmed, ≥40 cp, not yet lost) | 19 | 3 (R81 m8 at +1; R99 and R103 at +2) | 10 | 6 | 0 |
| first-decisive errors | 14 | 2 (both +2 only) | 8 | 4 | 0 |
| result flips (10M) | 18 | 2 (R81 m8 at +1, R103 at +2) | — | — | — |
| ≥300 cp | 2 | **0** | — | — | — |
| ≥100 cp | 11 | 1 (R81 m8) | — | — | — |

**+1 ply repairs of a live first-decisive error: 0 of 14.**

## 5. Timing verdict

**Would about +0.26 mean ply plausibly have solved the observed losses? NO.**

- Replaying C22's actual trigger, the extra iteration fires at only 4 of 19 errors, and **all four still play a bad move**.
- The two +2 ply repairs (R99, R103) are out of reach of *any* START_FRACTION: the d+1 iteration alone overruns the whole soft budget.
- No loss was time-pressed: decisive errors came with 52–115 s on the clock.

**C22 0.50 next-arena value: LOW.** C22 should not receive the next arena.

## 6. Failure clusters (after adversarial correction)

1. **UNKNOWN, evaluation-suspect (no feature isolated).**
   - Losses: R79, R81, R91, R94, R102 (R101 partly).
   - First-decisive in all of them; 81–148 cp; 0 repaired by depth; the cold search reproduces the live move.
   - Confidence it is not depth: high. Cause: unknown.
   - Fixability: none identified. Risk if a term is built: high.
2. **UNKNOWN, search-side suspect.**
   - Losses: R83, R95 (158 and 87 cp); neither repaired by depth.
   - RC-J's own static evaluation prefers Stockfish's line at the end of the PV, yet its search chose otherwise.
   - Fixability: unknown; it would need a search trace.
3. **State-dependence where a cold search is good.**
   - Losses: R92, R98, plus R94 m33 (63, 95 and 199 cp).
   - From a clean table RC-J avoids the result flip.
   - Fixability: low (no defect found). Risk: high for any change to how the transposition table is kept.
4. **State only chose between bad moves.**
   - Losses: R88, R101 m29, R101 m61. Here state is not the cause.
5. **Horizon.**
   - Losses: R99, R103; repaired at +2 ply only, beyond any time policy. Fixability: very low.
6. **Piece activity (weak).**
   - Losses: R105 (bishop locked in by its own pawns) and R88 (PeSTO square value of the f4 knight).
   - Confidence: low. Fixability: low. Risk: high (the king-safety v1 pattern).
7. **Endgame knowledge (low confidence).**
   - Position: R101 m57, 546 cp.
   - RC-J's own search at depth 21–23 rates the losing move and the drawing move as a near-tie (−81 vs −78). It was not the first decisive error.

Ranked by frequency × severity × fixability ÷ risk, every cluster scores **0–0.18**. A buildable candidate needs roughly 1.0.

## 7. Dominant failure

Quiet, early-to-middle middlegame misjudgements of 57–158 cp:
- They start from roughly equal positions (E 0.35–0.50), at moves 9–44, with ample clock.
- RC-J's own search scores the played move as equal to or better than Stockfish's move.
- +1 or +2 ply does not change them.
- **After adversarial review their specific cause is UNKNOWN in 8 of 14 losses.**

**Evidence:**
- **Not tactical.** Material almost never changes hands within 8 plies along either line.
- **Not king safety.** The unshipped king-safety term prefers the *played* move in 10 of 14 positions, and the king zones are quiet.
- **Not mobility.** Stockfish's move is more mobile at 0.64 of decisive positions and 0.57 of harmless alternatives, which is base rate.
- **Not rook placement.** Rook-on-open-file reverses across the other errors.

RC-J's PeSTO-only evaluator is the natural suspect, but no single missing feature is supported by more than one loss.

## 8. One recommended candidate

**D — NO NEW CANDIDATE. KEEP RC-J.**

- **Exact hypothesis:** none survives the evidence.
- **Actual losses addressed:** none.

Why this outranks the alternatives:
- **A (evaluation):** no feature has causal support in two or more losses. The unshipped king-safety term points the wrong way, and mobility sits at base rate. The project already rejected a uniformly applied king-safety term.
- **B (search):** the search-side signals are either horizon (+2 ply, unreachable in time) or state-dependence (no defect found; any fix is broad).
- **C (0.50):** 0 of 14 decisive errors are repaired at +1 ply.

**If implemented: N/A.** No branch, preregistration or code change.

## 9. Arena recommendation

**RUN NEXT: NO.**
- There is no candidate.
- The loss evidence does not support C22.
- Suggested minimum game stage: N/A.

## 10. Time-remaining strategy

**What can realistically improve RC-J now:** keeping RC-J stable. The one identifiable lever is evaluation quality in quiet middlegames. Fixing that needs a properly tuned multi-term evaluation validated on held-out games, not a hand-set term fitted to 14 positions. It is only worth starting if several days remain.

**What should not consume more time:**
- codegen or performance harnesses;
- a C22 0.50 arena;
- single hand-set evaluation terms (king safety, mobility, rook files, passed pawns) built from these losses;
- transposition-table clearing or other state experiments;
- extending this autopsy to draws.

The R94+ drop (29.2%) cannot be attributed. RC-J did not change, and the opponents' strength is unknown.

**Optional informational check, about 5 minutes:** run a cold fixed-depth search at d12 on R92 and d10 on R88. That would separate "accumulated state" from "the live search stopped one ply shallower".

## 11. RECORD THIS

- **"The time tweak buys the extra ply, and the extra ply plays the losing move again."** Run `wf\skeptic_timing\c22_window.py` in this folder with the RC-J venv Python, and film the four `C22_extra_iter=YES` rows.
- **Same engine, same clock, different memory.** Show R94 m33, FEN `8/1r2pk1p/p2p2p1/P2P1p2/P1p5/brP1R1P1/3B1PKP/1R6 w - - 3 33`. Live RC-J played Ra1 (199 cp, draw → loss). A cold RC-J with the same ~2.1 s plays Stockfish's Rbe1 at depths 16, 17 and 18.
- **The 546 cp blunder that looked like a tie.** Show R101 m57, FEN `1b6/1P3p2/8/6p1/4PpBk/p4P2/P4K2/8 b - - 18 57`. Stockfish rates Ba7+ as 546 cp worse than f6. RC-J at depth 21–23 values them −81 and −78.
- **The earlier lane studied the wrong move.** C26 and C27 analysed R83 m21 Ra1 in depth. The first decisive error was the move before it, m20 Bf2 (158 cp).

## 12. Artefacts and reproduction

Everything is in this folder (gitignored, not committed):
- data: `inventory.json`, `scan_all.jsonl`, `decisive.json`, `ladder*.json`, `verify*.json`, `repair.json`, `dossier.json`, `classification.json`, `bundles/`, `wf/`, `public_new/` (the 12 fetched PGNs);
- scripts: `sf_scan.py`, `analyse_scan.py`, `rcj_ladder.py`, `sf_verify.py`, `repair.py`, `dossier.py`, `stage2.py`, `stage3.py`.

Reproduce with `stage2.py` then `stage3.py`, using an RC-J (`2bf6885`) worktree Python with `tools\diag\make_trace_driver.py` already run. The C27 worktree path is hard-coded in `rcj_ladder.py` and `dossier.py`.
