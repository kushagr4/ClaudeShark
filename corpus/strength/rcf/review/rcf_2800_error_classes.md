errors: 111; result-flipping: 41; reproduced at game budget: 66

extra-depth repair rate (errors reproduced at the game budget, ladder available):
  +1: 18/73 = 25%
  +2: 20/56 = 36%
  +3: 17/38 = 45%

mechanism classes (count, result flips):
   45  flips  16  EVALUATION (no depth repairs)
   45  flips  20  ROOT INSTABILITY / TIME NOISE
    6  flips   2  TACTICAL HORIZON (+2)
    5  flips   1  SEARCH SHAPE (LMR/ORDERING: deep 10 s repairs, +3 does not)
    4  flips   1  ENDGAME (knowledge)
    2  flips   0  CONVERSION
    2  flips   0  TIME (moved fast)
    1  flips   0  TACTICAL HORIZON (+1)
    1  flips   1  TACTICAL HORIZON (+3)

| game | ply | col | played | oracle | loss | replay depth | repaired at +k | deep repairs | pieces | class |
|---|---|---|---|---|---|---|---|---|---|---|
| g036 | 65 | w | Rxh3 | e6e7 | 9359 | 12 | None | False | 19 | EVALUATION (no depth repairs) |
| g016 | 76 | w | Kd2 | e5e6 | 9334 | 13 | None | False | 13 | ROOT INSTABILITY / TIME NOISE |
| g035 | 48 | b | Qxg7 | e7e8 | 9334 | 14 | None | False | 19 | EVALUATION (no depth repairs) |
| g022 | 72 | w | Kd3 | d4e3 | 9241 | 15 | None | False | 13 | EVALUATION (no depth repairs) |
| g009 | 48 | b | Rc7 | d6d5 | 9232 | 11 | 3 | True | 18 | ROOT INSTABILITY / TIME NOISE |
| g016 | 84 | w | Kd2 | d1c2 | 9212 | 15 | None | False | 13 | EVALUATION (no depth repairs) |
| g003 | 45 | b | Kd6 | c5d5 | 9203 | 29 | None | True | 11 | ROOT INSTABILITY / TIME NOISE |
| g030 | 70 | w | a5 | d4e4 | 7289 | 17 | None | False | 10 | EVALUATION (no depth repairs) |
| g026 | 98 | w | Bd4 | e5d5 | 684 | 16 | None | True | 5 | ROOT INSTABILITY / TIME NOISE |
| g050 | 235 | w | Ke5 | a4e4 | 569 | 64 | None | False | 4 | ROOT INSTABILITY / TIME NOISE |
| g048 | 20 | w | Qe8 | h3g4 | 565 | 12 | 2 | True | 19 | TACTICAL HORIZON (+2) |
| g059 | 92 | b | Rb6 | g8h8 | 504 | 17 | None | False | 7 | ROOT INSTABILITY / TIME NOISE |
| g003 | 41 | b | Bxg5 | c4d5 | 483 | 18 | None | False | 13 | ROOT INSTABILITY / TIME NOISE |
| g059 | 96 | b | Rb6 | b5b8 | 431 | 16 | None | False | 7 | ENDGAME (knowledge) |
| g011 | 58 | b | Qg2 | g1e3 | 408 | 14 | None | False | 18 | EVALUATION (no depth repairs) |
| g054 | 94 | w | Rxg5+ | a6a8 | 352 | 12 | 1 | True | 10 | ROOT INSTABILITY / TIME NOISE |
| g007 | 9 | b | Nc6 | e7c5 | 346 | 10 | None | False | 28 | EVALUATION (no depth repairs) |
| g019 | 11 | b | Nd1 | e3f1 | 341 | 12 | None | False | 15 | ROOT INSTABILITY / TIME NOISE |
| g003 | 43 | b | Kc5 | c4d5 | 307 | 25 | None | True | 11 | ROOT INSTABILITY / TIME NOISE |
| g033 | 79 | b | d3 | e3f2 | 297 | 14 | None | False | 14 | EVALUATION (no depth repairs) |
| g059 | 34 | b | f4 | a6a5 | 291 | 11 | 1 | True | 16 | ROOT INSTABILITY / TIME NOISE |
| g006 | 128 | w | Ke3 | f3g3 | 284 | 16 | None | False | 13 | ROOT INSTABILITY / TIME NOISE |
| g026 | 86 | w | g7 | g1e3 | 283 | 20 | None | False | 7 | ENDGAME (knowledge) |
| g038 | 47 | w | Rc7+ | e4d6 | 278 | 10 | 2 | True | 17 | TACTICAL HORIZON (+2) |
| g004 | 14 | w | d4 | f1f2 | 277 | 10 | 2 | True | 19 | TACTICAL HORIZON (+2) |
| g041 | 11 | b | Qxd4 | a2a1 | 248 | 12 | None | False | 18 | EVALUATION (no depth repairs) |
| g040 | 38 | w | Kg6 | e6g6 | 247 | 14 | None | False | 11 | EVALUATION (no depth repairs) |
| g034 | 75 | w | Rxb5 | d3e3 | 241 | 11 | None | False | 13 | EVALUATION (no depth repairs) |
| g054 | 76 | w | b7 | g1h2 | 239 | 12 | None | True | 12 | SEARCH SHAPE (LMR/ORDERING: deep 10 s repairs, +3 does not) |
| g048 | 30 | w | Qd8+ | f6f5 | 234 | 16 | None | False | 18 | ROOT INSTABILITY / TIME NOISE |
| g032 | 58 | w | Qxc6 | g2g4 | 230 | 13 | None | False | 22 | EVALUATION (no depth repairs) |
| g009 | 12 | b | h5 | g7g6 | 219 | 13 | None | False | 27 | EVALUATION (no depth repairs) |
| g022 | 50 | w | Kf2 | f1e2 | 217 | 13 | None | True | 17 | SEARCH SHAPE (LMR/ORDERING: deep 10 s repairs, +3 does not) |
| g036 | 63 | w | fxe5 | f1f2 | 215 | 10 | 1 | True | 20 | ROOT INSTABILITY / TIME NOISE |
| g031 | 61 | b | Rxe4 | c5d7 | 214 | 14 | None | False | 16 | ROOT INSTABILITY / TIME NOISE |
| g031 | 77 | b | Kf6 | e7d6 | 214 | 15 | None | True | 13 | ROOT INSTABILITY / TIME NOISE |
| g034 | 15 | w | Rad1 | a1e1 | 214 | 9 | None | False | 24 | EVALUATION (no depth repairs) |
| g015 | 61 | b | Rxg5 | h6g5 | 204 | 14 | None | False | 17 | EVALUATION (no depth repairs) |
| g030 | 22 | w | f4 | a3a4 | 204 | 9 | 3 | False | 24 | ROOT INSTABILITY / TIME NOISE |
| g004 | 6 | w | Rxf2 | d1b3 | 195 | 15 | None | False | 24 | EVALUATION (no depth repairs) |
