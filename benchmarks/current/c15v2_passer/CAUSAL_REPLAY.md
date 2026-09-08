# C15-v2 causal replay

11 serious errors repaired, 2 worsened.

## Repaired

### `3q4/1p1P1pk1/p6p/6pP/8/3Q4/8/3K4 b - - 17 72`

* game AlphaFish ply 134, 11 pieces, 1 enemy passer(s), most advanced 6 ranks
* oracle wanted `g7f6`; the game played `g7f8`
* RC-I `b7b6` losing 141 cp
* C15-v2 `g7g8` losing 0 cp
* baseline with more depth: +2 still failed, +5 repaired

### `r2q2k1/p4p2/1pb2bp1/2ppr3/8/1QNP2P1/PP2PPB1/R4K1R w - - 0 17`

* game AlphaFish ply 21, 24 pieces, 0 enemy passer(s), most advanced 0 ranks
* oracle wanted `a1d1`; the game played `f2f4`
* RC-I `e2e4` losing 112 cp
* C15-v2 `a1d1` losing 2 cp
* baseline with more depth: +2 repaired, +5 repaired

### `2rq2k1/p4p2/3r1bp1/1p6/2p1QPP1/2N5/PP2P3/R4K1R w - - 0 24`

* game AlphaFish ply 35, 20 pieces, 0 enemy passer(s), most advanced 0 ranks
* oracle wanted `a2a3`; the game played `a2a3`
* RC-I `c3b5` losing 187 cp
* C15-v2 `g4g5` losing 61 cp
* baseline with more depth: +2 still failed, +5 repaired

### `4r1k1/p5b1/6p1/1p4P1/2p1N2R/P2qPQ2/1P3K2/8 b - - 2 37`

* game AlphaFish ply 62, 16 pieces, 1 enemy passer(s), most advanced 2 ranks
* oracle wanted `d3c2`; the game played `d3c2`
* RC-I `g7b2` losing 132 cp
* C15-v2 `d3c2` losing 16 cp
* baseline with more depth: +2 still failed, +5 still failed

### `2Q5/8/6p1/5q2/6k1/K1p5/1p6/8 w - - 8 77`

* game AlphaFish ply 141, 7 pieces, 3 enemy passer(s), most advanced 6 ranks
* oracle wanted `c8a6`; the game played `c8c4`
* RC-I `c8f5` losing 22934 cp
* C15-v2 `c8c4` losing 0 cp
* baseline with more depth: +2 repaired, +5 still failed

### `4n1k1/5pp1/8/K1N4p/1p6/1P3P1P/1P5r/3R4 b - - 0 34`

* game PSL God Matt Bomer ply 52, 14 pieces, 0 enemy passer(s), most advanced 0 ranks
* oracle wanted `h2h3`; the game played `h2h3`
* RC-I `h2b2` losing 139 cp
* C15-v2 `h2h3` losing 4 cp
* baseline with more depth: +2 repaired, +5 repaired

### `3Rn3/4kpp1/8/2K5/4NPrp/1P6/1P6/8 w - - 5 41`

* game PSL God Matt Bomer ply 65, 12 pieces, 1 enemy passer(s), most advanced 4 ranks
* oracle wanted `d8d1`; the game played `d8d1`
* RC-I `d8b8` losing 116 cp
* C15-v2 `d8a8` losing 89 cp
* baseline with more depth: +2 repaired, +5 repaired

### `4r2k/8/p2n2pP/3Pq3/2p4R/2N3P1/2Q2PK1/8 b - - 1 41`

* game Capablanca ply 72, 15 pieces, 2 enemy passer(s), most advanced 5 ranks
* oracle wanted `h8h7`; the game played `h8h7`
* RC-I `e8g8` losing 155 cp
* C15-v2 `h8h7` losing 0 cp
* baseline with more depth: +2 repaired, +5 repaired

### `8/7k/p2n2pP/3P2q1/Q1p4R/2N3P1/5PK1/4r3 b - - 9 45`

* game Capablanca ply 80, 15 pieces, 2 enemy passer(s), most advanced 5 ranks
* oracle wanted `d6f5`; the game played `d6f5`
* RC-I `d6b5` losing 393 cp
* C15-v2 `d6f5` losing 0 cp
* baseline with more depth: +2 repaired, +5 repaired

### `2N2k2/1p2R1pp/1p6/pP6/3r4/2n3P1/5PKP/8 w - - 8 36`

* game Capablanca ply 55, 15 pieces, 1 enemy passer(s), most advanced 3 ranks
* oracle wanted `e7c7`; the game played `e7c7`
* RC-I `e7b7` losing 188 cp
* C15-v2 `e7c7` losing 2 cp
* baseline with more depth: +2 repaired, +5 repaired

### `3r2k1/p4pp1/2p1p3/4P1Pp/P1n1NP1P/b1Pr4/8/1KB3RR w - - 1 27`

* game Capablanca ply 41, 22 pieces, 0 enemy passer(s), most advanced 0 ranks
* oracle wanted `c1a3`; the game played `c1a3`
* RC-I `g1g3` losing 168 cp
* C15-v2 `c1a3` losing 0 cp
* baseline with more depth: +2 repaired, +5 repaired

## Worsened

### `4r1k1/8/1R6/pp3R1P/6p1/P1P2b1r/1P6/5K2 b - - 5 54`

* game Capablanca ply 96, 14 pieces, 1 enemy passer(s), most advanced 4 ranks
* oracle wanted `e8e7`; the game played `e8e7`
* RC-I `a5a4` losing 56 cp
* C15-v2 `h3h2` losing 108 cp
* baseline with more depth: +2 still failed, +5 repaired

### `8/8/8/1p4R1/p1k2K2/2r5/1r6/8 w - - 6 75`

* game Capablanca ply 137, 7 pieces, 2 enemy passer(s), most advanced 4 ranks
* oracle wanted `f4f5`; the game played `g5e5`
* RC-I `g5g1` losing 2 cp
* C15-v2 `g5e5` losing 147 cp
* baseline with more depth: +2 repaired, +5 repaired

## Repairs that extra depth does not buy

2 of the 11 repaired positions are still wrong when the baseline searches five plies deeper:

* `4r1k1/p5b1/6p1/1p4P1/2p1N2R/P2qPQ2/1P3K2/8 b - - 2 37` -- RC-I `g7b2` (132 cp), C15-v2 `d3c2` (16 cp)
* `2Q5/8/6p1/5q2/6k1/K1p5/1p6/8 w - - 8 77` -- RC-I `c8f5` (22934 cp), C15-v2 `c8c4` (0 cp)
