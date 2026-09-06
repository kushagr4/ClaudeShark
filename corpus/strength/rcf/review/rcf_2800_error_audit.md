# Large-error audit — rcf_vs_sf2800_dev2400_60_strict.annotated.jsonl

engine champions\rc_f; 60 games; 3332 of our moves audited (positions already beyond +/-800 cp excluded)

| bin | moves | share |
|---|---|---|
| <50 | 3127 | 93.8% |
| 50-99 | 94 | 2.8% |
| 100-299 | 92 | 2.8% |
| >=300 | 19 | 0.6% |

**>=100 cp self-inflicted error rate: 3.33% of moves** (111 errors); >=300 cp: 0.57% (19); average cp loss 34.7
games with at least one >=100 cp error: 40 of 60; result-flipping errors: 41; errors per loss: 3.64 over 14 losses

## Every >=100 cp error (sorted by cp loss)

| game | ply | col | played | oracle | loss | before→after | flip | spent s | replay depth/score | static | qsearch | deep(10 s) move/loss | min repair depth | mechanism |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| g036 | 65 | w | Rxh3 | e6e7 | 9359 | -641→-10000 |  | 1.331 | 12/-326 | -75 | None | f3h3/9359 | None | UNCLASSIFIED |
| g016 | 76 | w | Kd2 | e5e6 | 9334 | -666→-10000 |  | 1.799 | 13/-731 (replay differs) | -116 | None | a2a3/138 | 12 | UNCLASSIFIED |
| g035 | 48 | b | Qxg7 | e7e8 | 9334 | -666→-10000 |  | 1.68 | 14/-688 | -263 | None | f7g7/9334 | 9 | UNCLASSIFIED |
| g022 | 72 | w | Kd3 | d4e3 | 9241 | -759→-10000 |  | 2.284 | 15/-1191 | -278 | None | d4d3/9241 | None | UNCLASSIFIED |
| g009 | 48 | b | Rc7 | d6d5 | 9232 | -768→-10000 |  | 1.632 | 11/-891 (replay differs) | -416 | None | d7d8/0 | 9 | UNCLASSIFIED |
| g016 | 84 | w | Kd2 | d1c2 | 9212 | -788→-10000 |  | 2.17 | 15/-874 | -145 | None | d1d2/9212 | None | UNCLASSIFIED |
| g003 | 45 | b | Kd6 | c5d5 | 9203 | -797→-10000 |  | 9.901 | 29/-92 (replay differs) | 107 | None | c5d5/0 | 9 | UNCLASSIFIED |
| g030 | 70 | w | a5 | d4e4 | 7289 | -654→-7943 |  | 1.828 | 17/-388 | -64 | None | a4a5/7289 | 10 | UNCLASSIFIED |
| g026 | 98 | w | Bd4 | e5d5 | 684 | +761→+77 | Y | 1.179 | 16/497 (replay differs) | 340 | None | e5d5/0 | 10 | UNCLASSIFIED |
| g050 | 235 | w | Ke5 | a4e4 | 569 | +0→-569 | Y | 0.002 | 64/0 (replay differs) | 19 | None | f5f6/488 | None | UNCLASSIFIED |
| g048 | 20 | w | Qe8 | h3g4 | 565 | +55→-510 | Y | 2.049 | 12/109 | 75 | None | h3g4/0 | 14 | UNCLASSIFIED |
| g059 | 92 | b | Rb6 | g8h8 | 504 | -784→-1288 |  | 2.177 | 17/-1140 (replay differs) | -381 | None | d6b6/504 | 9 | UNCLASSIFIED |
| g003 | 41 | b | Bxg5 | c4d5 | 483 | -264→-747 |  | 3.122 | 18/0 (replay differs) | 140 | None | h4g5/483 | None | UNCLASSIFIED |
| g059 | 96 | b | Rb6 | b5b8 | 431 | -761→-1192 |  | 2.319 | 16/-1325 | -377 | None | b5b6/431 | None | UNCLASSIFIED |
| g011 | 58 | b | Qg2 | g1e3 | 408 | -492→-900 |  | 1.923 | 14/-74 | 45 | None | g1g2/408 | 9 | UNCLASSIFIED |
| g054 | 94 | w | Rxg5+ | a6a8 | 352 | +355→+3 | Y | 1.506 | 12/127 (replay differs) | 139 | None | a6a8/12 | 12 | UNCLASSIFIED |
| g007 | 9 | b | Nc6 | e7c5 | 346 | -32→-378 | Y | 4.887 | 10/-23 | 17 | None | a5c6/346 | 14 | UNCLASSIFIED |
| g019 | 11 | b | Nd1 | e3f1 | 341 | -137→-478 | Y | 3.127 | 12/12 (replay differs) | 66 | None | e3d1/341 | None | UNCLASSIFIED |
| g003 | 43 | b | Kc5 | c4d5 | 307 | -607→-914 |  | 6.039 | 25/-67 (replay differs) | 117 | None | c4d5/0 | 9 | UNCLASSIFIED |
| g033 | 79 | b | d3 | e3f2 | 297 | -219→-516 |  | 1.583 | 14/0 | 69 | None | d4d3/297 | None | UNCLASSIFIED |
| g059 | 34 | b | f4 | a6a5 | 291 | -21→-312 | Y | 1.579 | 11/79 (replay differs) | 119 | None | a6a5/7 | 9 | UNCLASSIFIED |
| g006 | 128 | w | Ke3 | f3g3 | 284 | +284→+0 | Y | 0.713 | 16/181 (replay differs) | 224 | None | f3e3/284 | None | UNCLASSIFIED |
| g026 | 86 | w | g7 | g1e3 | 283 | +376→+93 | Y | 1.66 | 20/383 | 187 | None | g6g7/283 | None | UNCLASSIFIED |
| g038 | 47 | w | Rc7+ | e4d6 | 278 | -528→-806 |  | 1.269 | 10/-236 | 94 | None | e4d6/56 | 12 | UNCLASSIFIED |
| g004 | 14 | w | d4 | f1f2 | 277 | -408→-685 |  | 1.919 | 10/-257 | -104 | None | f1f2/26 | 9 | UNCLASSIFIED |
| g041 | 11 | b | Qxd4 | a2a1 | 248 | +248→+0 | Y | 2.522 | 12/169 | 114 | None | e4d4/248 | None | UNCLASSIFIED |
| g040 | 38 | w | Kg6 | e6g6 | 247 | +247→+0 | Y | 2.775 | 14/462 | 172 | None | h5g6/247 | None | UNCLASSIFIED |
| g034 | 75 | w | Rxb5 | d3e3 | 241 | -38→-279 | Y | 1.553 | 11/88 | 108 | None | e5b5/241 | None | UNCLASSIFIED |
| g054 | 76 | w | b7 | g1h2 | 239 | +239→+0 | Y | 1.566 | 12/378 | 238 | None | g1h2/6 | None | UNCLASSIFIED |
| g048 | 30 | w | Qd8+ | f6f5 | 234 | -716→-950 |  | 11.372 | 16/-29984 (replay differs) | 157 | None | h3g4/9284 | None | UNCLASSIFIED |
| g032 | 58 | w | Qxc6 | g2g4 | 230 | -155→-385 |  | 3.816 | 13/49 | 49 | None | a4c6/230 | None | UNCLASSIFIED |
| g009 | 12 | b | h5 | g7g6 | 219 | +33→-186 | Y | 3.688 | 13/133 | 97 | None | h7h5/219 | None | UNCLASSIFIED |
| g022 | 50 | w | Kf2 | f1e2 | 217 | -377→-594 |  | 1.409 | 13/-330 | 162 | None | f1e2/0 | 11 | UNCLASSIFIED |
| g036 | 63 | w | fxe5 | f1f2 | 215 | -514→-729 |  | 1.167 | 10/-345 (replay differs) | -163 | None | f1f2/16 | 9 | UNCLASSIFIED |
| g031 | 61 | b | Rxe4 | c5d7 | 214 | -133→-347 | Y | 2.792 | 14/12 (replay differs) | 39 | None | d4e4/214 | None | UNCLASSIFIED |
| g031 | 77 | b | Kf6 | e7d6 | 214 | +0→-214 | Y | 1.295 | 15/70 (replay differs) | 114 | None | e7d6/0 | 12 | UNCLASSIFIED |
| g034 | 15 | w | Rad1 | a1e1 | 214 | +102→-112 |  | 2.235 | 9/151 | 117 | None | a1d1/214 | None | UNCLASSIFIED |
| g015 | 61 | b | Rxg5 | h6g5 | 204 | -7→-211 | Y | 1.118 | 14/-8 | -352 | None | g7g5/204 | 9 | UNCLASSIFIED |
| g030 | 22 | w | f4 | a3a4 | 204 | -29→-233 | Y | 1.836 | 9/64 (replay differs) | 119 | None | f2f4/204 | 9 | UNCLASSIFIED |
| g004 | 6 | w | Rxf2 | d1b3 | 195 | -198→-393 |  | 14.408 | 15/63 | -1 | None | f1f2/195 | None | UNCLASSIFIED |
| g000 | 35 | w | Rdd5 | a5d2 | 194 | -26→-220 | Y | 2.131 | 11/-71 | 36 | None | d6d5/194 | None | UNCLASSIFIED |
| g009 | 32 | b | b6 | d8e8 | 191 | -507→-698 |  | 2.435 | 13/0 | 111 | None | b7b6/191 | 14 | UNCLASSIFIED |
| g002 | 46 | w | Bxe4+ | h4h5 | 186 | -1→-187 | Y | 2.148 | 13/46 (replay differs) | 54 | None | b7d7/0 | 9 | UNCLASSIFIED |
| g033 | 75 | b | d4 | e3f4 | 186 | +0→-186 | Y | 3.583 | 15/38 | 134 | None | d5d4/186 | 9 | UNCLASSIFIED |
| g033 | 83 | b | d2 | e3g3 | 186 | -734→-920 |  | 1.032 | 14/-32 | 71 | None | g7g8/0 | None | UNCLASSIFIED |
| g008 | 5 | w | O-O-O | g4g5 | 184 | -53→-237 | Y | 3.28 | 11/22 | -12 | None | e1c1/184 | None | UNCLASSIFIED |
| g024 | 20 | w | Rcd1 | b5c3 | 180 | -221→-401 |  | 2.845 | 10/-25 | 18 | None | c1d1/180 | None | UNCLASSIFIED |
| g008 | 27 | w | Be2 | b2a2 | 176 | -279→-455 |  | 1.674 | 11/-54 (replay differs) | -5 | None | h3h4/191 | None | UNCLASSIFIED |
| g019 | 9 | b | Ne3+ | e1e4 | 176 | +0→-176 | Y | 2.1 | 11/0 (replay differs) | 23 | None | e1e4/0 | 9 | UNCLASSIFIED |
| g035 | 30 | b | Nxc2 | e3g4 | 176 | -218→-394 |  | 1.827 | 10/152 | 155 | None | e3c2/176 | None | UNCLASSIFIED |
| g014 | 30 | w | Nxf2 | c2c4 | 173 | -143→-316 | Y | 2.861 | 11/68 | 76 | None | e4f2/173 | 14 | UNCLASSIFIED |
| g034 | 77 | w | Kc2 | c3e2 | 170 | -57→-227 | Y | 1.416 | 13/88 | 135 | None | d3c2/170 | None | UNCLASSIFIED |
| g006 | 140 | w | Be5 | f3g2 | 166 | -9→-175 | Y | 0.5 | 13/81 (replay differs) | 195 | None | d6e5/166 | 9 | UNCLASSIFIED |
| g030 | 24 | w | Nd3 | e5f3 | 166 | -87→-253 | Y | 2.536 | 10/0 (replay differs) | 112 | None | e5f3/0 | 9 | UNCLASSIFIED |
| g016 | 38 | w | Bf1 | e4e5 | 163 | +0→-163 | Y | 1.818 | 10/-21 (replay differs) | -11 | None | c4f1/163 | None | UNCLASSIFIED |
| g038 | 1 | w | Na4 | g3f3 | 157 | -14→-171 | Y | 3.931 | 12/0 | 37 | None | c1e3/82 | 9 | UNCLASSIFIED |
| g015 | 55 | b | Bd8 | f6g5 | 155 | -7→-162 | Y | 3.308 | 16/-23 (replay differs) | -24 | None | f6d8/155 | 10 | UNCLASSIFIED |
| g036 | 57 | w | f4 | h3f1 | 155 | -564→-719 |  | 1.338 | 12/-236 (replay differs) | -33 | None | f3f4/155 | 10 | UNCLASSIFIED |
| g042 | 20 | w | Bxa1 | g7b7 | 155 | +192→+37 | Y | 2.129 | 13/166 | -20 | None | d5e5/161 | None | UNCLASSIFIED |
| g038 | 39 | w | fxe3 | f2f3 | 153 | -280→-433 |  | 3.866 | 14/-32 | 6 | None | f2e3/153 | None | UNCLASSIFIED |
| g015 | 81 | b | Rb6 | g5g4 | 148 | -254→-402 |  | 1.058 | 15/-41 (replay differs) | 64 | None | h7g6/0 | 10 | UNCLASSIFIED |
| g003 | 25 | b | b3 | c6c5 | 147 | -29→-176 | Y | 2.9 | 14/38 (replay differs) | 138 | None | c6c5/1 | 9 | UNCLASSIFIED |
| g054 | 30 | w | d5 | h2h3 | 145 | +144→-1 |  | 3.617 | 11/138 (replay differs) | 190 | None | a4b5/58 | 9 | UNCLASSIFIED |
| g030 | 56 | w | Rxh7+ | h8e8 | 144 | -401→-545 |  | 2.108 | 17/-188 | -91 | None | h8h7/144 | None | UNCLASSIFIED |
| g046 | 85 | w | Re7 | c1e2 | 139 | +389→+250 |  | 2.125 | 13/437 | 434 | None | e6e7/139 | None | UNCLASSIFIED |
| g022 | 42 | w | Nf5 | b6b3 | 138 | -6→-144 |  | 5.349 | 12/14 | 85 | None | g3f5/138 | 9 | UNCLASSIFIED |
| g011 | 48 | b | Qg1+ | g2g5 | 134 | -204→-338 |  | 1.171 | 13/0 | 53 | None | g2g1/134 | None | UNCLASSIFIED |
| g027 | 59 | b | Rh7 | d4e5 | 132 | +483→+351 |  | 1.995 | 11/270 (replay differs) | 260 | None | b7h7/132 | None | UNCLASSIFIED |
| g038 | 25 | w | Ba5 | e2f4 | 132 | -57→-189 | Y | 2.942 | 12/53 | 40 | None | d2a5/132 | None | UNCLASSIFIED |
| g035 | 28 | b | Ne3 | a5c6 | 129 | -208→-337 |  | 1.702 | 11/156 | 100 | None | g4e3/129 | None | UNCLASSIFIED |
| g040 | 36 | w | Kh5 | g4f5 | 129 | +367→+238 |  | 2.435 | 12/291 (replay differs) | 251 | None | g4h5/129 | 12 | UNCLASSIFIED |
| g034 | 109 | w | Bd4 | c6f6 | 127 | -195→-322 |  | 1.17 | 11/-68 | 33 | None | c3d4/127 | None | UNCLASSIFIED |
| g004 | 4 | w | cxd3 | d1d3 | 126 | -122→-248 | Y | 2.223 | 12/124 | -261 | None | c2d3/126 | None | UNCLASSIFIED |
| g024 | 34 | w | Kf1 | f2f1 | 126 | -389→-515 |  | 3.235 | 14/0 | 105 | None | f2f1/126 | None | UNCLASSIFIED |
| g008 | 31 | w | Qc3 | e1c1 | 125 | -487→-612 |  | 3.526 | 11/-132 (replay differs) | -3 | None | e1c1/11 | 10 | UNCLASSIFIED |
| g002 | 72 | w | Rb2 | d2c2 | 123 | -326→-449 |  | 1.191 | 13/-85 (replay differs) | -60 | None | d2b2/123 | None | UNCLASSIFIED |
| g035 | 18 | b | Bxe5 | f6e4 | 123 | -79→-202 | Y | 2.838 | 10/100 (replay differs) | 176 | None | d6c7/140 | None | UNCLASSIFIED |
| g036 | 13 | w | Rh2 | d1e1 | 123 | -252→-375 |  | 3.052 | 11/28 (replay differs) | 126 | None | d1f1/50 | 12 | UNCLASSIFIED |
| g016 | 66 | w | Qc4 | c2b2 | 122 | -491→-613 |  | 1.523 | 11/-224 (replay differs) | -107 | None | b5d3/0 | 9 | UNCLASSIFIED |
| g000 | 57 | w | Kf2 | f3f2 | 120 | -293→-413 |  | 3.892 | 14/-177 | -39 | None | f3f2/120 | None | UNCLASSIFIED |
| g016 | 68 | w | Bd3 | c4c5 | 120 | -458→-578 |  | 1.122 | 10/-252 | -103 | None | f1d3/120 | None | UNCLASSIFIED |
| g024 | 16 | w | exf4 | h5f3 | 120 | -121→-241 | Y | 3.754 | 11/-19 | 21 | None | e3f4/120 | None | UNCLASSIFIED |
| g030 | 26 | w | Ne5 | b4b5 | 119 | -215→-334 |  | 1.801 | 10/-10 | 81 | None | d3e5/119 | None | UNCLASSIFIED |
| g004 | 2 | w | Nc3 | a2a4 | 118 | +10→-108 |  | 3.427 | 11/81 | 109 | None | e2c3/118 | None | UNCLASSIFIED |
| g005 | 37 | b | Qd1 | c4c3 | 118 | -492→-610 |  | 2.022 | 12/-172 | 42 | None | c2d1/118 | 10 | UNCLASSIFIED |
| g013 | 15 | b | h4 | a1a3 | 117 | +0→-117 |  | 2.421 | 12/73 (replay differs) | 22 | None | b4b3/4 | 9 | UNCLASSIFIED |
| g002 | 76 | w | Rd2 | c2c4 | 116 | -324→-440 |  | 1.372 | 14/-83 | -59 | None | c2d2/116 | None | UNCLASSIFIED |
| g015 | 77 | b | Rxa5 | c5a5 | 115 | -172→-287 |  | 2.315 | 16/-39 | 68 | None | c5c8/231 | None | UNCLASSIFIED |
| g025 | 37 | b | b6 | c6c1 | 115 | -56→-171 | Y | 4.761 | 11/89 (replay differs) | 105 | None | c6c4/53 | 9 | UNCLASSIFIED |
| g059 | 106 | b | Kg8 | f8g8 | 115 | -629→-744 |  | 0.206 | 13/-575 | -372 | None | f8g8/115 | None | UNCLASSIFIED |
| g016 | 50 | w | Kd1 | a7d7 | 114 | -332→-446 |  | 1.97 | 12/-84 | -114 | None | a7d7/5 | 14 | UNCLASSIFIED |
| g054 | 24 | w | Rbc1 | h2h3 | 114 | +8→-106 |  | 2.682 | 11/91 (replay differs) | 143 | None | e2f3/8 | 10 | UNCLASSIFIED |
| g035 | 32 | b | Kf8 | f5f4 | 113 | -265→-378 |  | 1.86 | 11/144 (replay differs) | 162 | None | g8f8/113 | None | UNCLASSIFIED |
| g024 | 36 | w | Kf2 | f1f2 | 112 | -399→-511 |  | 0.001 | 0/0 | 89 | None | f1f2/112 | None | UNCLASSIFIED |
| g000 | 27 | w | Ba5 | d2d5 | 111 | -25→-136 |  | 3.659 | 13/-45 (replay differs) | -23 | None | b4a5/111 | 9 | UNCLASSIFIED |
| g003 | 23 | b | Rc8 | b4a3 | 111 | +0→-111 |  | 2.941 | 14/10 | 147 | None | b4a3/17 | None | UNCLASSIFIED |
| g010 | 85 | w | e7+ | e6e7 | 111 | +709→+598 |  | 1.854 | 17/648 | 335 | None | e6e7/9 | 9 | UNCLASSIFIED |
| g035 | 40 | b | Re7 | g7h6 | 110 | -548→-658 |  | 1.492 | 10/-242 | 108 | None | g7h6/23 | 9 | UNCLASSIFIED |
| g016 | 74 | w | Qa2 | c4a2 | 108 | -578→-686 |  | 3.236 | 14/-275 (replay differs) | -74 | None | e2f1/49 | 9 | UNCLASSIFIED |
| g034 | 115 | w | Bb6 | f2g4 | 108 | -355→-463 |  | 1.256 | 11/-84 | 104 | None | c7c8/105 | None | UNCLASSIFIED |
| g024 | 32 | w | Kf2 | f1f2 | 106 | -442→-548 |  | 0.0 | 0/0 | 89 | None | f1f2/106 | None | UNCLASSIFIED |
| g009 | 26 | b | Nxe6 | c7a6 | 105 | -391→-496 |  | 2.892 | 12/9 | 26 | None | c7e6/105 | None | UNCLASSIFIED |
| g039 | 22 | b | Bd7 | c8d7 | 105 | -98→-203 | Y | 3.619 | 11/140 (replay differs) | 180 | None | c7c6/0 | 12 | UNCLASSIFIED |
| g039 | 30 | b | Rd6 | c8d7 | 105 | -123→-228 | Y | 2.211 | 10/158 | 198 | None | d8d6/105 | None | UNCLASSIFIED |
| g024 | 18 | w | Kg3 | b5c3 | 104 | -147→-251 | Y | 2.566 | 10/-23 (replay differs) | 5 | None | c1d1/46 | 9 | UNCLASSIFIED |
| g003 | 5 | b | fxg4 | g6h7 | 103 | -49→-152 | Y | 3.312 | 12/60 | 116 | None | f5g4/103 | 9 | UNCLASSIFIED |
| g015 | 105 | b | Rc3 | f3f8 | 103 | -528→-631 |  | 0.874 | 12/-175 (replay differs) | 1 | None | f3e3/85 | 9 | UNCLASSIFIED |
| g008 | 29 | w | Nd2 | b2a1 | 102 | -424→-526 |  | 2.554 | 13/-93 | 31 | None | f3d2/102 | None | UNCLASSIFIED |
| g029 | 60 | b | d3 | g7g6 | 102 | +125→+23 |  | 3.271 | 14/150 | 142 | None | g7g6/4 | 9 | UNCLASSIFIED |
| g017 | 21 | b | Rxe3 | c5b3 | 101 | +119→+18 |  | 1.796 | 13/282 | 56 | None | c3e3/101 | 9 | UNCLASSIFIED |
| g033 | 3 | b | Re8 | b7b6 | 101 | +8→-93 |  | 4.139 | 13/56 (replay differs) | 43 | None | b7b6/0 | 9 | UNCLASSIFIED |
