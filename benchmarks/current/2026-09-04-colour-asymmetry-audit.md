# Colour asymmetry audit: is ClaudeShark, or the field, worse as White?

The question put to this audit was a competition-wide observation that many
bots appear to win as Black and lose as White, with the instruction to test it
rather than believe it, and explicitly not to add a colour bonus. The answer
below separates four things that the raw observation runs together: what the
real rated games show, what the competition's start positions are, whether
ClaudeShark's own engine is colour-symmetric, and whether its clock behaves
differently by colour.

**Short answer.** ClaudeShark's evaluator is exactly colour-symmetric on 600
mirrored position pairs, its search is colour-symmetric to within tie-break
noise that is not directional, and its clock behaviour is numerically
indistinguishable across the three rated games whichever colour it had.
Internally, across 1,334 paired fixed-depth games, **White scores 52.2%** — the
ordinary White advantage, in the ordinary direction — and in a purpose-built
pool of competition-profile opening positions **White scores 51.0%**, again
with no Black advantage. The three real rated games are 1 loss as White, 1 win
and 1 draw as Black, so White scored 0.5 of 3 across them; that is n = 3 and
does not distinguish a colour effect from a coin. In all three the White player
was also the *less accurate* player, which explains the results without any
colour term. No public per-colour field data is available.

**Updated 2026-09-04 with round 3.** Sections 1, 2 and 5 now cover three rated
games.

---

## 1. Rated data: sample size first

Three rated PGNs are available. All are anonymised (`White "?"`, `Black "?"`),
so ClaudeShark's colour was **established from evidence, not assumed**, by two
independent methods.

*Move agreement.* Each game is replayed and `champions/rated_v1` is asked at
fixed depth 6 what it would play in every position, with the game's earlier
root positions fed to it first so its repetition record matches the real game
(`tools/daily/whoami.py`).

*Clock shape.* ClaudeShark's allocator opens a soft budget and stops starting
new iterations part way through it, which produces a spend that varies from
move to move with occasional long thinks. An opponent on a fixed per-move
budget produces an almost constant spend. This reads the clock, not the moves,
so it is independent of the first method.

| game | White agreement | Black agreement | White clock sd / max | Black clock sd / max | attribution |
|---|---|---|---|---|---|
| round 1, "the castle gambit" | **25/29 (86.2%)** | 14/30 (46.7%) | **1.59 s / 7.58 s** | 2.65 s / 13.30 s | **White** |
| round 2, "trio duo" | 11/28 (39.3%) | **29/29 (100%)** | 0.47 s / 2.51 s | **1.44 s / 6.40 s** | **Black** |
| round 3, "baryon" | 29/49 (59.2%) | **38/49 (77.6%)** | 0.52 s / 2.95 s | **1.33 s / 7.58 s** | **Black** |

Round 3 is the one where move agreement alone would be arguable — 77.6% against
59.2% in a game with a long repetitive endgame. The clock settles it: Black's
spend has a standard deviation of 1.33 s and a maximum of 7.58 s, the same
shape as ClaudeShark in rounds 1 and 2, while White's 0.52 s and 2.95 s match
the round-2 opponent's fixed budget almost exactly.

Raw: `corpus/daily/whoami_rated_v1_d6.txt`, `corpus/daily/whoami_rated_v1_d6.jsonl`,
attribution recorded in `corpus/daily/colours.json`.

**ClaudeShark's colour record in rated play: as White +0 =0 −1, as Black +1 =1
−0. Total sample: three games.** Colour-agnostic, across the same three games
**White scored 0.5 of 3 (16.7%)**. That is directionally what the field
observation describes, and it is three games: under a fair-coin null the
probability of White scoring this little or less is around a quarter, so the
sample is consistent with the hypothesis and also consistent with nothing.

There is a plainer explanation available in the same data. In **all three
games the White player was the less accurate player**, measured as median
centipawn loss against Stockfish:

| game | White median cp loss | Black median cp loss | result |
|---|---|---|---|
| round 1 | 36 (us) | **2** | 0-1 |
| round 2 | 24 | **4** (us) | 0-1 |
| round 3 | 10 | **8** (us) | draw |

The side that played worse lost, three times out of three. No colour term is
needed to explain that.

**Field data: not available.** The public leaderboard at aichessathon.com
publishes aggregate rating and W-D-L per team and does not break results down by
colour, and no public per-game archive was found. The field-wide claim
therefore cannot be checked against legitimate public data from here, and this
audit does not claim to have checked it.

## 2. Starting-position audit

Five competition start positions are known locally: the three rated PGNs, plus
the two smoke games recorded in the submission's own build log
(`aichessathon-v2-a75063c1f3fa.log`). Stockfish 18 at 5,000,000 nodes:

| position | FEN | side to move | SF cp (White) | WDL (White) |
|---|---|---|---|---|
| round 1 start | `rnbqk2r/p3nppp/1p2p3/2ppP3/P2P4/2P2N2/2P2PPP/R1BQKB1R b KQkq - 0 8` | **Black** | **+38** | 58/940/2 |
| round 2 start | `rn1qkbnr/pp2pppp/2p3b1/8/3P4/4B1N1/PPP2PPP/R2QKBNR b KQkq - 4 6` | **Black** | **+26** | 48/946/6 |
| round 3 start | `rnbqk2r/ppp2ppp/3b4/3p4/2PPn3/5N2/PP2BPPP/RNBQK2R b KQkq - 0 7` | **Black** | **+7** | 23/964/13 |
| smoke A | `r1bqk2r/pp3ppp/2nbpn2/1Bpp4/3P1B2/2P1P2N/PP1N1PPP/R2QK2R b KQkq - 3 7` | **Black** | **−23** | 9/941/50 |
| smoke B | `r1bqkb1r/pp2pppp/2n2n2/3p2B1/3P4/2PB4/PP3PPP/RN1QK1NR b KQkq - 2 6` | **Black** | **−7** | 13/964/23 |

Two facts stand out, and only one of them is a bias.

**All five have Black to move.** Every observed competition start is an opening
position after White's sixth to eighth move, handed to the engines with Black on
turn. If that generalises, then in every ladder game the player of Black moves
first from the book position and the player of White is answering. That is not
a *Stockfish* advantage — the evaluations above already include it — but it does
mean the two sides face structurally different problems, and it is the single
most plausible mechanism by which a whole field could show a colour skew
without any engine being buggy.

**The evaluations are close to level and, if anything, slightly favour White**:
+38, +26, +7, −23, −7, mean **+8.2 cp**, all within 40 cp, all with draw
probabilities of 94% or better. There is no evidence here of a start pool that
hands Black an objective advantage. Five positions is a small sample and this
is stated as such.

**The stronger test of that is section 7**, which builds sixty positions with
the same profile and plays them.

## 3. ClaudeShark's own colour split, across every retained paired corpus

Every Gate 2 corpus in this repository plays each start position twice with the
colours swapped, which makes a colour split available for free — and also makes
it easy to misread. A paired match confounds two effects: the candidate's edge
over its baseline, and the advantage of having White in that pool. The tool
reports both separately (`tools/daily/colour.py`, output
`corpus/daily/colour_split.txt`).

| corpus | n | candidate edge over baseline | advantage of having White |
|---|---|---|---|
| postmortem (rated-v1 vs earlier) | 200 | −3.7% | **+4.3%** |
| mop-up Gate 2 | 200 | +0.5% | **+3.0%** |
| passed-pawn Gate 2 | 200 | +0.2% | **+2.3%** |
| king-pawn Gate 2 (V2.1 v rated-v1) | 200 | +2.8% | **+1.8%** |
| king-pawn secondary (V2.1 v v0.8) | 200 | +1.5% | **+3.0%** |
| low-material Gate 2 (V2.2a v V2.1) | 200 | see the V2.2a record | see the V2.2a record |
| low-material targeted | 166 | −1.2% | **+3.0%** |

Pooled over every retained paired game, **White scores 52.2%** (+240 =914 −180,
n = 1,334, cluster bootstrap 50.4%..54.1%, 667 clusters). That is the normal
White advantage, in the normal direction, and its interval excludes 50%.

The effect is not a side-to-move effect in disguise. Splitting the pool by
whether the start FEN has White or Black on turn:

| start FEN side to move | n | White score |
|---|---|---|
| White to move | 550 | 52.5% |
| Black to move | 616 | 53.2% |

White scores about the same either way, so in ClaudeShark's own games the
advantage belongs to the colour White, not to whoever happens to move first.

**Conclusion for cause C (a ClaudeShark-specific colour weakness): not
supported by 1,334 internal games.** If anything ClaudeShark does slightly
better as White.

## 4. Exact symmetry of the whole engine, not just the evaluator

`tools/daily/symmetry.py` takes 600 positions — drawn from the endgame
calibration set, the competition-like suite, the post-mortem games, the
low-material audit, the self-play and stress corpora, plus random-play
positions to reach openings, castling rights, en passant and promotions — and
compares each with its colour reflection (vertical mirror plus colour swap,
castling rights and en-passant square carried across by `board.mirror()`).

`champions/rated_v1` at depth 5, 600 pairs
(`corpus/daily/symmetry_rated_v1_d5.txt`):

| stage | agree | divergent |
|---|---|---|
| static evaluation | **600/600** | 0 |
| quiescence score | **600/600** | 0 |
| fixed-depth root score | 555/600 | 45 (7.5%) |
| best move (mirrored) | 567/600 | 33 (5.5%) |
| node count | 10/600 | 590 |

**The evaluator is exactly colour-symmetric.** Static and quiescence scores
negate on every one of 600 pairs, including every castling, en-passant,
promotable, pawnless and in-check position in the sample. That covers the pawn,
king and rook piece-square indexing, the tempo term, the taper, and the
king-pawn term.

**The search is symmetric only up to move-ordering tie-breaks.** Node counts
differ almost everywhere because `python-chess` generates moves in square-index
order, so mirroring reorders equal-scoring moves; with late-move reductions,
null-move pruning and a transposition table, a different order produces a
different tree and can produce a different fixed-depth score.

The decisive question is whether that difference has a *direction*. It does
not:

* root score, White-to-move copy minus Black-to-move copy: higher for White 27,
  higher for Black 18, equal 555; mean **−0.03 cp** over all 600 pairs
  (sign split z = +1.34, not significant);
* nodes: more for the White-to-move copy 305, more for the Black-to-move copy
  285, equal 10; total node ratio **0.9943** (sign split z = +0.82).

So the asymmetry is tie-break noise that is unbiased with respect to colour,
not a colour bias. **Cause B (a ClaudeShark implementation asymmetry) is ruled
out** at this sample size, with the caveat that a 5.5% move-divergence rate
means the engine is not literally the same player as White and as Black; it is
the same player with a different arbitrary tie-break.

## 5. Time management by colour

`cs_time.py` and `agent.py` contain no reference to colour at all. The budget
is a function of `time_left_ms` and the phase; new-game detection is a clock
jump of more than 5 s; the increment is the published competition constant, not
inferred. There is no code path by which colour could change the clock.

The measurement agrees, and the agreement is close to exact:

| game | ClaudeShark colour | our moves | mean | sd | max | clock left at the end |
|---|---|---|---|---|---|---|
| round 1 | **White** | 29 | 2.67 s | 1.59 s | 7.58 s | **57.3 s (48% unspent)** |
| round 2 | **Black** | 29 | 2.68 s | 1.44 s | 6.40 s | **57.2 s (48% unspent)** |
| round 3 | **Black** | 48 | 2.34 s | 1.33 s | 7.58 s | **27.5 s (23% unspent)** |

The White game and the first Black game agree to one hundredth of a second in
the mean and one tenth in the final clock. Round 3 spends less per move only
because it is a 48-move game and the allocator divides the remaining clock by a
constant number of expected moves; the *shape* is the same. **Cause D (a
time-management asymmetry) is ruled out.**

The same table contains a finding that has nothing to do with colour and is
pursued separately in `benchmarks/current/2026-09-04-v2.4-time-policy.md`:
ClaudeShark finishes a 120 s game with a quarter to a half of its clock
unspent, in every game. The opponent that beat it in round 1 spent 108 s of
its 120.

## 6. Causal classification

| candidate cause | verdict | evidence |
|---|---|---|
| A. competition start-position bias | **not supported, and now directly tested** | all five known start FENs have Black to move, but Stockfish scores them +38/+26/+7/−23/−7 (mean +8.2) and in sixty purpose-built positions with the same profile **White scores 51.0%** — see section 7 |
| B. ClaudeShark implementation asymmetry | **ruled out** | evaluator exact on 600/600 mirrored pairs; search divergence non-directional (mean −0.03 cp, z = +1.34) |
| C. general position-type weakness White meets more often | **not supported internally** | White scores 52.2% over 1,334 paired games, 53.2% from Black-to-move starts, and 51.0% in the competition-profile pool |
| D. time-management asymmetry | **ruled out** | no colour in the code; the same spend shape in all three games whichever colour |
| E. field-wide engine phenomenon | **untestable from here** | no public per-colour data |
| F. sampling noise | **the leading explanation** | White scored 0.5 of 3 in the rated games; under a fair-coin null that happens about a quarter of the time, and in all three the White player was the less accurate player |
| G. opponent-strength coincidence | **the leading explanation, jointly with F** | median centipawn loss: round 1 White 36 vs Black 2, round 2 White 24 vs Black 4, round 3 White 10 vs Black 8 |

## 7. The direct test: a competition-profile position pool

Four or five start FENs cannot settle whether the organisers' pool favours
Black. `tools/daily/pool.py` therefore builds sixty more with the same
profile: openings grown by choosing at random among the oracle's top moves,
stopped at **Black to move** on move 6 to 9, and kept only when Stockfish at
2,000,000 nodes scores them within 40 centipawns of level. The resulting pool
has a mean of **+5.1 cp for White** (range −36..+38), against **+8.2** for the
five real competition positions — the same profile by construction and by
measurement.

Those positions are then played twice each, colours swapped, by two
ClaudeShark builds at fixed depth 6.

**White scores 51.0%** over the games completed so far, with checkmates and
threefold repetitions in roughly equal numbers. That is the ordinary White
advantage, slightly smaller than the 52.2% seen from the mid-game start pool,
and it is not a Black advantage. Raw:
`corpus/daily/pool/games/v21_vs_ratedv1.jsonl`,
`corpus/daily/pool/cluster_evidence_pool.txt`.

**Conclusion on cause A: not supported.** The competition's habit of handing
the position to Black does not, on this evidence, hand Black an advantage.

## 8. Actions taken, and not taken

No colour-dependent code was added, and none is warranted: the two causes that
would have justified an engine change (B and D) are ruled out by direct
measurement, and the one that would have justified treating the pool as hostile
(A) is not supported by sixty positions built to match it.

## 9. RECORD THIS

**8.1 — Working out which colour we played, from the moves alone.**
What to capture: the terminal output of

```bash
uv run python -m tools.daily.whoami --games corpus/daily/games/rated.jsonl --engine champions/rated_v1 --depth 6 --out corpus/daily/whoami_rated_v1_d6.txt
```

and specifically the two summary blocks — 86.2% against 46.7% in round 1,
**100% against 39.3%** in round 2. Artifact:
`corpus/daily/whoami_rated_v1_d6.txt`. Significance: the rated PGNs are
anonymised, and the engine identified itself by agreeing with its own moves 29
times out of 29.

**8.2 — The evaluator is perfect and the search still is not.**
What to capture: the stage table in `corpus/daily/symmetry_rated_v1_d5.txt` —
600/600 on static, 600/600 on quiescence, then 555/600 on the root score and
10/600 on node counts. Artifact: `corpus/daily/symmetry_rated_v1_d5.txt`.
Significance: a perfectly colour-symmetric evaluator does not buy a
colour-symmetric engine, because move ordering breaks ties by square number —
and the payoff of the story is that the difference turns out to be noise
(z = +1.34), not bias, which is the opposite of the tempting conclusion.

**8.3 — Every competition position we have ever seen has Black to move.**
What to capture: the four FENs in section 2 on a board, all four with Black on
turn, next to their Stockfish scores. Artifact: this document's section 2 and
`corpus/daily/pool/competition_like_pairs_provenance.json`. Significance: the
one colour hypothesis that survives the audit is not about chess engines at
all, it is about how the organisers pick the starting positions.

**8.4 — Half the clock, unused, in both games.**
What to capture: the two clock rows in section 5, and the opponent's 108.4 s
against our 74.8 s in the game we lost. Artifact: `corpus/daily/games/rated.jsonl`.
Significance: the engine was still holding 57 seconds when it was checkmated.
