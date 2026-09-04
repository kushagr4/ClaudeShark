# Search ablation: no selective mechanism is responsible, and depth is worth a great deal

**Date:** 2026-09-04. **Branch:** `v2.2-development`. **Engine:**
`champions/v2_1_kingpawn`. **Audit only — no engine file was changed.**
Raw: `corpus/daily/search_audit_v21.txt`, `.jsonl`.

## 1. Why this was run rather than another evaluation term

Two independent pieces of evidence pointed at the search rather than the
evaluator.

The V2 root-cause map's largest single blind-win mechanism is
"tactical/horizon" with about 35 trajectories. And the feature attribution in
`corpus/daily/attribution_endgame_calibrated.txt` — which removes the engine's
uniform compression of decisive scores by calibrating an expected root per
50 cp oracle band — found that the biggest remaining departures belong to
positions with an advanced passed pawn, where the **root** score departs
sharply (own best passer on the sixth rank +41, on the seventh +61; enemy best
passer on the seventh −67) while the **static** score in the same buckets does
not (−18, +15, −11). A bucket whose root moves and whose static does not is a
horizon effect, and an evaluation term aimed at it would be fighting the
search.

Section 15 of the standing brief lists a search audit as the right response,
and section 16 requires attribution before any extension: classify first, do
not add an extension because it sounds right.

## 2. Method

Eighty positions in which the mover lost at least 200 centipawns, sampled at
random from every ply of four annotated 200-game corpora and restricted to
positions the oracle scored within 800 of level, so that the sample is about
mistakes rather than about already-decided games. Each position is searched by
the same frozen engine under nine configurations: the baseline at depth 6, the
same engine at depths 7 and 8, and each selective mechanism disabled one at a
time through its declared environment flag.

Every chosen move is then scored by Stockfish at 1,000,000 nodes on the
position it produces. **Configurations are compared on the quality of the move
they produce, not on whether they agree with Stockfish's first choice**, so a
mechanism that changes many moves without improving them is visible as such.

## 3. Result

| configuration | mean oracle value after its move | vs baseline | agrees with the oracle | moves changed | mean nodes |
|---|---|---|---|---|---|
| baseline, depth 6 | −1222 | — | 8/80 | — | 33,354 |
| **depth 7** | **−575** | **+647** | 17/80 | 30 | 62,935 |
| **depth 8** | **−323** | **+899** | 24/80 | 45 | 138,422 |
| no null move | −1224 | −2 | 8/80 | 3 | 35,650 |
| no late-move reductions | −855 | +367 | 9/80 | 13 | 61,923 |
| no aspiration window | −1203 | +19 | 9/80 | 9 | 33,586 |
| no quiescence SEE pruning | −1221 | +1 | 8/80 | 3 | 36,494 |
| no PVS | −1114 | +108 | 10/80 | 6 | 49,499 |
| no transposition cutoff on PV nodes | −1214 | +8 | 10/80 | 2 | 33,647 |
| *the move actually played in the game* | −1175 | +47 | | | |
| *the oracle's own first choice* | **−45** | +1177 | | | (the ceiling) |

## 4. What it says

**No selective mechanism is the cause.** Null move, the aspiration window,
quiescence SEE pruning and the transposition cutoff on PV nodes are worth −2,
+19, +1 and +8 centipawns respectively — indistinguishable from nothing on a
sample whose ceiling is +1177 away. Whatever is producing these errors, it is
not one of them, and there is nothing here to justify disabling or tuning any
of them.

**Late-move reductions cost real move quality, and still pay for themselves.**
Turning LMR off gains +367 cp and costs 1.9 times the nodes. But depth 7 gains
+647 cp for almost exactly the same nodes (62,935 against 61,923). **At an
equal node budget, spending the extra nodes on another ply of reduced search
beats spending them on an unreduced search of the same depth by 280
centipawns.** LMR is not the problem; it is the reason the extra ply is
affordable.

**Depth is the lever, by a factor of two over anything else.** One extra ply is
worth +647 centipawns of move quality on this sample and takes the oracle
agreement from 8 to 17 of 80; two plies are worth +899 and take it to 24. The
sample is selected — these are positions where somebody blundered, which is
exactly where depth helps most — so the number does not transfer to a whole
game. The ordering does.

## 5. The consequence, which is not a search change

The engine already has a large, unused reserve of exactly the resource this
table says it needs. In all three rated games it finished with a large part of
its clock unspent:

| game | our moves | mean spend | clock left at the end |
|---|---|---|---|
| round 1 | 29 | 2.67 s | **57.3 s of 120 s** |
| round 2 | 29 | 2.68 s | **57.2 s of 120 s** |
| round 3 | 48 | see the rated-game record | |

The allocator computes a soft budget of about 4.98 s on a full clock and then
declines to start a new iteration once 45% of it has elapsed
(`START_FRACTION = 0.45`), so the money is budgeted and not spent.

This is the one place where the search audit produces a testable candidate, and
it is a time-policy change rather than a search change: **convert unused clock
into depth**. It must be measured at the competition's own time control, not at
a scaled-down one — `BENCHMARKS.md` already records an experiment invalidated
by exactly that mistake, and the earlier `START_FRACTION = 0.60` test that came
out inconclusive at +9 Elo was run at about 0.9 s per move, roughly a third of
the competition's operating point.

## 6. What was explicitly not done

No extension was added. No pruning parameter was changed. The engine is
byte-identical to what it was before this audit, and the depth-6 fingerprint is
still 1,712,405 nodes.
