# The oracle that gave two answers

## What was wrong

`compare.py`, the harness that produced C15's chess evidence and the first
C15-v2 run, opened one Stockfish process per worker and analysed position after
position through it:

```python
eng = chess.engine.SimpleEngine.popen_uci(SF)
eng.configure({"Threads": 1, "Hash": 128})
...
i2 = eng.analyse(b, chess.engine.Limit(nodes=NODES))
```

A fixed-node search is deterministic only from a fixed starting state, and the
transposition table is part of that state. Nothing here clears it. The two
builds being compared visit the same positions in the same order, but they play
*different moves*, so from the first divergence onwards each build's Stockfish
holds a different table, and every later analysis is scored from a different
starting point. The measurement of build B depends on the moves build B chose
earlier — which is exactly the thing the measurement is supposed to be
independent of.

## How large the effect was

The symptom is unmistakable, because it produces an impossible row: both builds
play the identical move and the oracle reports a different loss for it.

| run | positions | same move, different score |
|---|---|---|
| C15 vs C12 (the run that produced the C15 verdict) | 144 | **55** |
| RC-I vs C15-v2 (first attempt, same harness) | 144 | **57** |

Only 18 of the 144 positions had genuinely different moves in the C15 run. So
126 positions could not possibly show a real difference, and 55 of them did.

The contamination reached the headline. Of C15's **17 reported repairs, 5 are
positions where both builds played the same move**:

| move both builds played | reported as | position |
|---|---|---|
| `g8f8` | 22,776 -> 0 | `6k1/8/5K1p/7P/8/8/5B2/8 b - - 8 74` |
| `c8c4` | 23,916 -> 0 | `2Q5/8/6p1/5q2/6k1/K1p5/1p6/8 w - - 8 77` |
| `h4g3` | 6,128 -> 0 | `8/P7/8/1K6/7Q/8/q7/6k1 w - - 1 70` |
| `e4f6` | 108 -> 85 | `4r1k1/p5b1/6p1/1p4P1/2p1N2R/P3PQK1/1q6/8 w - - 0 39` |
| `g5h6` | 112 -> 87 | `3r2k1/p3bpp1/2p1p2p/4P1P1/2n1NP1P/2pr4/PP6/1KB3RR w - - 0 25` |

Three of those five are swings of more than 6,000 centipawns attributed to a
move that was never in question. **Both** of C15's two reported regressions are
the same artefact.

## The fix

python-chess sends `ucinewgame` whenever the `game` argument of `analyse`
changes, and Stockfish clears its table on `ucinewgame`. Declaring a new game
per analysis makes each one a pure function of the position:

```python
def oracle(board, tag):
    return eng.analyse(board, chess.engine.Limit(nodes=NODES), game=tag)
```

`compare2.py` also measures each position's own score independently in both
passes and reports two invariants that must both be zero: the number of
positions whose own score differed between passes, and the number of positions
where the same move received a different loss. If either is non-zero the run is
not trustworthy and says so on its own output.

## What it means for the earlier verdicts

C15 was rejected on **cost**, and that verdict is unaffected — the timing
measurement never touched Stockfish. What is affected is the claim that C15
"repaired 17 of 144 serious errors against 2 worsened", which appears in
`benchmarks/current/2026-09-08-rc-i-combined.md` and in the RC-I session
report. That figure was measured on this harness and should not be quoted
again. The corrected numbers for the same mechanism are in
`benchmarks/current/c15v2_passer/`.

**RECORD THIS.** A rejected candidate whose chess case was half measurement
error is a good, honest segment, and it is easy to show on screen:

```bash
cd C:\Users\epick\AppData\Local\Temp\claude\C--Users-epick-Documents-ClaudeShark\e3813b42-0a37-4aea-86be-348b96190e38\scratchpad\c15v2
uv run python -c "import json;r=json.load(open('benchmarks/current/c15v2_passer/compare_shared_hash_FLAWED.json'));print(sum(1 for x in r if x['base_move']==x['cand_move'] and x['base_loss']!=x['cand_loss']),'of',len(r),'positions: same move, different score')"
```

The shot is the table above — one move, `g8f8`, scored 22,776 by one run and 0
by the other, with the board `6k1/8/5K1p/7P/8/8/5B2/8 b` on screen: a bare king
and a pawn against king and bishop, a position with nothing to argue about.
