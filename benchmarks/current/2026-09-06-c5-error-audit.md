# Large-error audit — c5_vs_sf2300_dev_60_strict.annotated.jsonl

engine champions\c5_rfp; 60 games; 2337 of our moves audited (positions already beyond +/-800 cp excluded)

| bin | moves | share |
|---|---|---|
| <50 | 1938 | 82.9% |
| 50-99 | 205 | 8.8% |
| 100-299 | 144 | 6.2% |
| >=300 | 50 | 2.1% |

**>=100 cp self-inflicted error rate: 8.30% of moves** (194 errors); >=300 cp: 2.14% (50); average cp loss 128.2
games with at least one >=100 cp error: 49 of 60; result-flipping errors: 67; errors per loss: 5.50 over 22 losses

## Every >=100 cp error (sorted by cp loss)

| game | ply | col | played | oracle | loss | before→after | flip | spent s | replay depth/score | static | qsearch | deep(10 s) move/loss | min repair depth | mechanism |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| g010 | 59 | w | Rxb4 | b1c1 | 10007 | +7→-10000 | Y | 1.206 | 7/106 | 71 | 153 | b1c1/2 | None | UNCLASSIFIED |
| g046 | 36 | w | Nb6 | g2h3 | 9962 | -38→-10000 | Y | 1.558 | 6/818 | 679 | 855 | g2h3/22 | 8 | UNCLASSIFIED |
| g022 | 30 | w | Qxa7 | b7c7 | 9731 | -269→-10000 |  | 4.827 | 7/327 | 470 | 470 | b7a7/9731 | None | UNCLASSIFIED |
| g052 | 112 | w | Qg4 | b4b2 | 9621 | -379→-10000 |  | 0.731 | 5/-96 | -52 | -52 | d1e2/183 | None | UNCLASSIFIED |
| g043 | 37 | b | Ka8 | b8c8 | 9536 | -464→-10000 |  | 1.573 | 6/40 | 152 | 152 | d6c5/114 | None | UNCLASSIFIED |
| g000 | 158 | w | Kh7 | h6g7 | 9478 | -522→-10000 |  | 0.809 | 10/-517 (replay differs) | -308 | -426 | h6g7/199 | None | UNCLASSIFIED |
| g005 | 47 | b | Bc8 | h8h7 | 9435 | -565→-10000 |  | 1.803 | 6/132 (replay differs) | 202 | 202 | h8g8/410 | None | UNCLASSIFIED |
| g027 | 57 | b | e4 | c8c1 | 9411 | -589→-10000 |  | 2.641 | 8/-472 | 94 | 94 | g4e6/9411 | None | UNCLASSIFIED |
| g025 | 53 | b | cxd3 | e8e6 | 9401 | -599→-10000 |  | 1.722 | 6/285 | 383 | 405 | e8e5/9401 | None | UNCLASSIFIED |
| g000 | 172 | w | Kg8 | g7g8 | 9385 | -615→-10000 |  | 0.637 | 10/-341 | -309 | -339 | g7g8/9385 | None | UNCLASSIFIED |
| g027 | 51 | b | Qd7 | c8g4 | 9350 | -650→-10000 |  | 1.486 | 8/-406 | 88 | 88 | c8g4/0 | None | UNCLASSIFIED |
| g032 | 45 | w | Rg1 | e3d2 | 9347 | -653→-10000 |  | 2.768 | 6/-402 (replay differs) | -259 | -259 | f1g1/9347 | 6 | UNCLASSIFIED |
| g000 | 156 | w | Kh6 | g7h6 | 9345 | -655→-10000 |  | 0.615 | 8/-517 (replay differs) | -297 | -423 | g7h6/9345 | None | UNCLASSIFIED |
| g033 | 86 | b | Rh2 | a2a1 | 9282 | -718→-10000 |  | 1.256 | 9/-537 (replay differs) | -15 | -15 | f8g7/69 | 6 | UNCLASSIFIED |
| g052 | 118 | w | Qh4 | b4b2 | 9281 | -719→-10000 |  | 0.749 | 5/-151 | -80 | -80 | b4b2/28 | 8 | UNCLASSIFIED |
| g011 | 86 | b | b6 | c7d6 | 9259 | -741→-10000 |  | 1.318 | 7/-849 (replay differs) | -500 | -500 | b7b6/9259 | None | UNCLASSIFIED |
| g000 | 216 | w | Kg6 | h5g6 | 9251 | -749→-10000 |  | 0.523 | 10/-408 | -400 | -400 | h5g6/9251 | None | UNCLASSIFIED |
| g044 | 28 | w | Rfe1 | e2d3 | 9250 | -750→-10000 |  | 2.38 | 7/104 | 172 | 172 | f1e1/9250 | None | UNCLASSIFIED |
| g000 | 220 | w | Kg4 | h5g4 | 9248 | -752→-10000 |  | 0.44 | 9/-537 | -395 | -395 | h5g4/9248 | None | UNCLASSIFIED |
| g009 | 72 | b | c4 | h6g7 | 9236 | -764→-10000 |  | 1.317 | 8/-951 | -878 | -878 | h6g7/9 | None | UNCLASSIFIED |
| g048 | 172 | w | Kb3 | c4b4 | 9233 | -767→-10000 |  | 0.693 | 11/-1238 (replay differs) | -349 | -349 | c4b4/9233 | None | UNCLASSIFIED |
| g049 | 31 | b | Bf8 | c8e6 | 9217 | -783→-10000 |  | 10.336 | 8/-507 (replay differs) | 273 | 273 | g7h8/9217 | None | UNCLASSIFIED |
| g010 | 61 | w | Kg2 | g1h2 | 9203 | -797→-10000 |  | 1.859 | 9/-61 | 166 | 149 | g1g2/9203 | None | UNCLASSIFIED |
| g000 | 176 | w | Qxf6+ | h8f6 | 7447 | -668→-8115 |  | 0.001 | 0/0 | 385 | -293 | h8f6/7447 | None | UNCLASSIFIED |
| g000 | 196 | w | Kg8 | f8e8 | 7344 | -771→-8115 |  | 0.454 | 10/-389 (replay differs) | -296 | -296 | f8g7/1401 | None | UNCLASSIFIED |
| g007 | 87 | b | Qe2+ | e1e8 | 703 | -532→-1235 |  | 0.921 | 6/-167 | -24 | -24 | e1e8/0 | None | UNCLASSIFIED |
| g036 | 84 | w | Re1 | c5c6 | 664 | -355→-1019 |  | 1.336 | 6/64 (replay differs) | 77 | 77 | c1b2/207 | None | UNCLASSIFIED |
| g042 | 246 | w | c6 | b5b4 | 625 | +625→+0 | Y | 0.45 | 8/458 | 406 | 406 | c4e5/86 | None | UNCLASSIFIED |
| g022 | 32 | w | Rfe1 | a7c7 | 533 | -283→-816 |  | 1.654 | 7/237 | 531 | 531 | f1e1/533 | None | UNCLASSIFIED |
| g058 | 176 | w | Bc3 | a5a6 | 493 | +493→+0 | Y | 0.816 | 8/356 (replay differs) | 360 | 360 | d4f2/471 | None | UNCLASSIFIED |
| g050 | 118 | w | Bh5 | e2f3 | 487 | +0→-487 | Y | 0.994 | 9/27 | 159 | 159 | e2h5/487 | 6 | UNCLASSIFIED |
| g027 | 37 | b | gxh3 | g4g3 | 470 | -144→-614 | Y | 2.37 | 6/228 | 371 | 371 | e2b2/268 | None | UNCLASSIFIED |
| g007 | 91 | b | Qf2+ | e1e8 | 463 | -404→-867 |  | 1.786 | 7/-185 (replay differs) | -24 | -24 | e1e8/143 | None | UNCLASSIFIED |
| g042 | 196 | w | Kg6 | f5e6 | 462 | +473→+11 | Y | 0.785 | 7/182 (replay differs) | 276 | 276 | f5f6/451 | None | UNCLASSIFIED |
| g046 | 32 | w | Nxc6 | b6c8 | 453 | +231→-222 | Y | 2.666 | 7/666 | 436 | 567 | d4c6/453 | None | UNCLASSIFIED |
| g005 | 43 | b | Bf8 | g5g4 | 448 | -359→-807 |  | 1.492 | 6/175 | 324 | 324 | e7f8/448 | None | UNCLASSIFIED |
| g055 | 21 | b | bxc6 | f4g2 | 443 | +373→-70 | Y | 3.324 | 8/36 | -303 | 105 | f4g2/24 | None | UNCLASSIFIED |
| g046 | 34 | w | Nxa8 | b6c8 | 439 | +221→-218 | Y | 2.384 | 6/661 | 518 | 749 | b6a8/439 | None | UNCLASSIFIED |
| g049 | 29 | b | Nxa1 | e5e4 | 414 | -409→-823 |  | 2.203 | 6/66 | 69 | 160 | c2a1/414 | None | UNCLASSIFIED |
| g057 | 42 | b | Kh8 | g4f6 | 379 | -502→-881 |  | 1.697 | 9/-240 | -115 | 0 | g4f6/33 | None | UNCLASSIFIED |
| g025 | 51 | b | bxc4 | e8e6 | 371 | -203→-574 |  | 5.162 | 7/206 | 302 | 302 | b5c4/371 | None | UNCLASSIFIED |
| g050 | 58 | w | Rd1 | g3g4 | 360 | +279→-81 | Y | 1.527 | 6/-53 (replay differs) | -43 | -43 | g3g4/0 | 6 | UNCLASSIFIED |
| g020 | 74 | w | g5 | h4h5 | 357 | +357→+0 | Y | 1.125 | 9/244 | 209 | 209 | a2a3/357 | 6 | UNCLASSIFIED |
| g051 | 17 | b | Nxa6 | f5e6 | 340 | +51→-289 | Y | 5.326 | 7/-31 | 196 | 196 | b4a6/340 | 8 | UNCLASSIFIED |
| g055 | 37 | b | Qh6 | h4g3 | 320 | +401→+81 | Y | 2.209 | 6/240 | 212 | 242 | f6h6/320 | None | UNCLASSIFIED |
| g000 | 198 | w | Kg7 | g8f7 | 318 | -714→-1032 |  | 0.533 | 9/-404 | -305 | -305 | g8f7/302 | None | UNCLASSIFIED |
| g011 | 40 | b | Rf8 | g4g3 | 317 | +42→-275 | Y | 3.63 | 6/324 (replay differs) | 350 | 350 | c6e7/42 | 6 | UNCLASSIFIED |
| g031 | 43 | b | Bb8 | c7b6 | 315 | -62→-377 | Y | 1.98 | 9/-20 | 82 | 82 | c7d8/170 | None | UNCLASSIFIED |
| g022 | 22 | w | h5 | c2d2 | 309 | +107→-202 | Y | 7.328 | 6/377 | 454 | 454 | h4h5/309 | None | UNCLASSIFIED |
| g057 | 34 | b | Rxd2+ | c2c1 | 306 | -56→-362 | Y | 1.897 | 9/72 | 4 | 96 | c2d2/306 | 6 | UNCLASSIFIED |
| g035 | 103 | b | Rh2 | f3d4 | 298 | +313→+15 | Y | 1.536 | 7/187 | 211 | 211 | d2h2/298 | 8 | UNCLASSIFIED |
| g044 | 26 | w | f3 | c4c5 | 296 | -400→-696 |  | 2.724 | 7/132 | 204 | 204 | f2f3/296 | None | UNCLASSIFIED |
| g058 | 12 | w | Bc4 | e5f7 | 291 | +302→+11 | Y | 5.697 | 8/4 (replay differs) | 40 | 40 | c2c3/321 | None | UNCLASSIFIED |
| g020 | 38 | w | e7 | d1d7 | 289 | +314→+25 | Y | 2.959 | 8/247 | 185 | 185 | e6e7/289 | None | UNCLASSIFIED |
| g015 | 39 | b | Qd7 | d4f3 | 288 | +482→+194 |  | 1.587 | 5/192 | 271 | 271 | h3d7/288 | None | UNCLASSIFIED |
| g021 | 151 | b | Kd7 | e7d7 | 283 | -745→-1028 |  | 0.682 | 10/-411 | -273 | -273 | e7f7/7370 | None | UNCLASSIFIED |
| g039 | 33 | b | Rc2 | c3c1 | 280 | +173→-107 | Y | 2.547 | 7/178 | 214 | 214 | c3c2/280 | None | UNCLASSIFIED |
| g036 | 54 | w | Kg1 | f2g1 | 279 | -511→-790 |  | 1.528 | 8/-108 (replay differs) | 62 | -9 | f2e1/37 | 8 | UNCLASSIFIED |
| g000 | 174 | w | h8=Q | h7h8b | 276 | -729→-1005 |  | 0.524 | 13/-331 | -298 | 386 | h7h8q/276 | None | UNCLASSIFIED |
| g039 | 69 | b | Bd4 | f3e4 | 271 | +271→+0 | Y | 1.269 | 7/264 | 204 | 204 | c3d4/271 | None | UNCLASSIFIED |
| g022 | 28 | w | Bg2 | g1g2 | 269 | +10→-259 | Y | 3.281 | 8/401 | 471 | 471 | f3g2/269 | None | UNCLASSIFIED |
| g009 | 52 | b | Rxd3 | g8g7 | 262 | -411→-673 |  | 2.114 | 8/-319 (replay differs) | 244 | 244 | g8g7/0 | 7 | UNCLASSIFIED |
| g034 | 38 | w | Bf2 | b2b4 | 256 | -457→-713 |  | 2.8 | 7/112 | 185 | 185 | e3f2/256 | None | UNCLASSIFIED |
| g027 | 27 | b | Rxe2 | d8a5 | 251 | -6→-257 | Y | 3.392 | 7/336 | 416 | 429 | c2e2/251 | None | UNCLASSIFIED |
| g021 | 99 | b | gxh5 | c6d7 | 249 | -167→-416 |  | 1.249 | 9/70 | -6 | 79 | g6h5/249 | None | UNCLASSIFIED |
| g045 | 49 | b | Bd4 | e7f7 | 243 | +110→-133 |  | 1.871 | 6/135 | 222 | 222 | g7d4/243 | None | UNCLASSIFIED |
| g048 | 60 | w | bxc3 | d2e2 | 235 | -306→-541 |  | 3.001 | 8/19 | 149 | 152 | d2d3/33 | None | UNCLASSIFIED |
| g009 | 44 | b | Rxa2 | f7e6 | 234 | -116→-350 | Y | 2.459 | 6/61 | 90 | 178 | a8a2/234 | None | UNCLASSIFIED |
| g007 | 79 | b | Qa3 | c3f6 | 231 | -370→-601 |  | 0.942 | 7/-215 (replay differs) | -69 | -69 | c3e3/15 | 6 | UNCLASSIFIED |
| g008 | 11 | w | Bh4 | e7c8 | 229 | +0→-229 | Y | 3.236 | 5/140 | 164 | 164 | g5h4/229 | None | UNCLASSIFIED |
| g008 | 25 | w | Ke3 | h3g4 | 228 | -308→-536 |  | 6.474 | 8/-37 | 216 | 313 | f3e3/228 | 6 | UNCLASSIFIED |
| g011 | 64 | b | Rxb3 | d3d1 | 227 | -474→-701 |  | 1.732 | 9/43 | -380 | 39 | d3b3/227 | None | UNCLASSIFIED |
| g034 | 30 | w | Qd2 | d1d3 | 225 | -238→-463 |  | 1.688 | 6/84 | 139 | 139 | e2f2/249 | None | UNCLASSIFIED |
| g030 | 8 | w | O-O-O | f3e5 | 222 | +52→-170 | Y | 3.147 | 6/88 | 69 | 69 | e1c1/222 | None | UNCLASSIFIED |
| g044 | 22 | w | Nd2 | f3e5 | 222 | -220→-442 |  | 6.071 | 9/146 | 221 | 221 | f3d2/222 | None | UNCLASSIFIED |
| g009 | 46 | b | Rd2 | c5c4 | 220 | -133→-353 | Y | 2.85 | 6/115 | 187 | 222 | a2d2/220 | 8 | UNCLASSIFIED |
| g042 | 136 | w | Rxe6 | e2f2 | 215 | -81→-296 | Y | 1.004 | 8/-43 | -36 | -36 | e2e6/215 | None | UNCLASSIFIED |
| g047 | 63 | b | Rxb8 | d6b8 | 207 | -97→-304 | Y | 1.3 | 7/56 | -346 | 172 | h8b8/207 | None | UNCLASSIFIED |
| g059 | 13 | b | Qh6 | d2f4 | 207 | +211→+4 | Y | 3.309 | 6/222 | 379 | 379 | f6h6/207 | None | UNCLASSIFIED |
| g027 | 31 | b | Bxf6 | d8f6 | 206 | -130→-336 | Y | 1.674 | 7/180 | 275 | 549 | g7f6/206 | None | UNCLASSIFIED |
| g042 | 110 | w | Rd1 | g2e2 | 205 | +0→-205 | Y | 0.868 | 6/107 | 112 | 112 | a1e1/13 | 8 | UNCLASSIFIED |
| g021 | 141 | b | Kd7 | e6d6 | 203 | -668→-871 |  | 0.687 | 10/-349 (replay differs) | -180 | -180 | e6f7/94 | None | UNCLASSIFIED |
| g009 | 54 | b | Kg7 | g8h7 | 202 | -400→-602 |  | 1.801 | 10/-201 | 550 | 27 | g8g7/202 | 8 | UNCLASSIFIED |
| g042 | 112 | w | Rb2 | g2d2 | 202 | -9→-211 | Y | 1.396 | 7/116 (replay differs) | 155 | 155 | g2d2/1 | 8 | UNCLASSIFIED |
| g052 | 104 | w | Rxc4 | e1e2 | 202 | -203→-405 |  | 1.363 | 6/77 (replay differs) | 95 | 163 | c1c4/202 | 6 | UNCLASSIFIED |
| g038 | 20 | w | Nd6 | c2c4 | 199 | +117→-82 |  | 2.258 | 7/142 | 164 | 164 | e4d6/199 | 6 | UNCLASSIFIED |
| g028 | 36 | w | Rg4 | d2c4 | 196 | -64→-260 | Y | 1.622 | 7/0 | -21 | -1 | e4g4/196 | 6 | UNCLASSIFIED |
| g011 | 72 | b | Kg6 | h6g6 | 191 | -768→-959 |  | 0.0 | 0/0 | -380 | -426 | h6g6/191 | None | UNCLASSIFIED |
| g052 | 108 | w | Rb4 | c4c2 | 190 | -427→-617 |  | 1.195 | 7/-99 | 187 | 187 | c4c1/43 | 6 | UNCLASSIFIED |
| g021 | 97 | b | Bg7 | h5g4 | 189 | -4→-193 | Y | 2.211 | 9/66 (replay differs) | 117 | 117 | d4e5/23 | 6 | UNCLASSIFIED |
| g025 | 57 | b | d2 | d3d2 | 189 | -745→-934 |  | 1.633 | 5/281 (replay differs) | 540 | 540 | d3d2/189 | None | UNCLASSIFIED |
| g036 | 38 | w | Rf3 | c2e2 | 189 | -213→-402 |  | 2.404 | 6/-28 | -13 | -13 | e3f3/189 | None | UNCLASSIFIED |
| g011 | 34 | b | fxg4 | c7f4 | 188 | +296→+108 | Y | 1.986 | 7/219 | 119 | 206 | f5g4/188 | None | UNCLASSIFIED |
| g028 | 68 | w | Bb2 | e1f1 | 187 | -508→-695 |  | 1.676 | 10/-145 | -112 | -112 | c1b2/187 | None | UNCLASSIFIED |
| g049 | 21 | b | Rb8 | d4e2 | 186 | -246→-432 |  | 3.604 | 8/-31 (replay differs) | 53 | 78 | a8b8/186 | 6 | UNCLASSIFIED |
| g024 | 44 | w | Bxc8 | d3c4 | 184 | +184→+0 | Y | 3.355 | 7/364 | 267 | 382 | b7c8/184 | None | UNCLASSIFIED |
| g001 | 21 | b | Rad8 | e7e5 | 179 | +258→+79 | Y | 3.034 | 7/163 | 213 | 213 | a8d8/179 | None | UNCLASSIFIED |
| g021 | 75 | b | Bd4 | g7f6 | 179 | +199→+20 | Y | 3.281 | 9/138 | 228 | 228 | a7a6/192 | 6 | UNCLASSIFIED |
| g035 | 47 | b | Re8 | d5c4 | 179 | -3→-182 | Y | 2.152 | 6/7 (replay differs) | 10 | 10 | c5e4/121 | None | UNCLASSIFIED |
| g036 | 40 | w | Rxf7 | f3e3 | 178 | -237→-415 |  | 1.63 | 7/-49 | -3 | 66 | f3f7/178 | None | UNCLASSIFIED |
| g002 | 24 | w | Nd6 | e4g3 | 175 | +96→-79 |  | 4.046 | 8/91 | 174 | 174 | e4f6/105 | None | UNCLASSIFIED |
| g000 | 28 | w | Nh6+ | g4e5 | 174 | -95→-269 | Y | 5.333 | 8/-69 | 5 | 5 | g4h6/174 | None | UNCLASSIFIED |
| g011 | 62 | b | Rxb3 | d3d8 | 171 | -342→-513 |  | 1.437 | 6/45 | 33 | 39 | c3b3/171 | None | UNCLASSIFIED |
| g045 | 43 | b | fxe3 | d7a4 | 170 | +233→+63 | Y | 1.353 | 6/69 | 100 | 223 | f4e3/170 | None | UNCLASSIFIED |
| g006 | 8 | w | Bxe6 | e1g1 | 168 | -6→-174 | Y | 3.87 | 7/-26 | -86 | -58 | c4e6/168 | None | UNCLASSIFIED |
| g028 | 64 | w | Nxb3 | e1d2 | 168 | -332→-500 |  | 1.216 | 7/-137 (replay differs) | -88 | 7 | c5b3/168 | 6 | UNCLASSIFIED |
| g027 | 47 | b | Qd7 | d8f6 | 165 | -677→-842 |  | 7.441 | 9/-189 (replay differs) | 101 | 101 | d8c8/12 | 8 | UNCLASSIFIED |
| g057 | 30 | b | Rc2 | b2c4 | 163 | +0→-163 | Y | 2.308 | 8/69 (replay differs) | 135 | 135 | b2c4/0 | 6 | UNCLASSIFIED |
| g059 | 21 | b | Bd7 | d2c4 | 162 | +246→+84 | Y | 2.055 | 6/321 | 310 | 310 | c8d7/162 | None | UNCLASSIFIED |
| g000 | 16 | w | Rc1 | d4c5 | 159 | -18→-177 | Y | 3.998 | 7/18 | 37 | 37 | a1c1/159 | None | UNCLASSIFIED |
| g005 | 45 | b | Bxc5 | g5g4 | 159 | -496→-655 |  | 1.652 | 8/132 | 219 | 219 | f8c5/159 | None | UNCLASSIFIED |
| g022 | 24 | w | Qb3 | c2c1 | 159 | +159→+0 | Y | 2.723 | 6/396 | 444 | 444 | c2b3/159 | 8 | UNCLASSIFIED |
| g002 | 38 | w | Qxe6+ | f2f4 | 156 | +474→+318 |  | 1.99 | 6/259 | 216 | 290 | h3e6/156 | None | UNCLASSIFIED |
| g021 | 73 | b | Kg7 | c3c2 | 155 | +170→+15 | Y | 2.488 | 8/168 | 186 | 186 | g8g7/155 | None | UNCLASSIFIED |
| g043 | 3 | b | O-O-O | e8g8 | 155 | -15→-170 | Y | 2.763 | 6/6 | -38 | -37 | e8g8/0 | 8 | UNCLASSIFIED |
| g004 | 52 | w | Rxa5 | d1g4 | 153 | +352→+199 |  | 1.593 | 6/171 | 158 | 210 | c5a5/153 | None | UNCLASSIFIED |
| g046 | 10 | w | c3 | d3d4 | 153 | +66→-87 |  | 2.326 | 6/78 (replay differs) | 90 | 90 | c2c3/153 | 6 | UNCLASSIFIED |
| g056 | 59 | w | Rf4 | d4g4 | 148 | +148→+0 |  | 1.965 | 8/181 | 290 | 290 | d4g4/12 | None | UNCLASSIFIED |
| g020 | 58 | w | g4 | d6c7 | 147 | +153→+6 | Y | 2.974 | 9/203 | 242 | 242 | g2g3/138 | None | UNCLASSIFIED |
| g034 | 12 | w | O-O-O | e1g1 | 147 | +22→-125 |  | 3.332 | 6/62 (replay differs) | 22 | 22 | e1c1/147 | 6 | UNCLASSIFIED |
| g038 | 12 | w | Bxc6 | c3e4 | 146 | +162→+16 | Y | 2.789 | 6/130 | 133 | 133 | g2c6/146 | None | UNCLASSIFIED |
| g036 | 82 | w | Re2 | c5c6 | 144 | -444→-588 |  | 2.72 | 8/-67 | 65 | 65 | c2e2/144 | None | UNCLASSIFIED |
| g036 | 62 | w | c5 | f2e1 | 142 | -394→-536 |  | 1.812 | 7/30 (replay differs) | 37 | 37 | c4c5/142 | None | UNCLASSIFIED |
| g034 | 20 | w | Be3 | g3h5 | 141 | +54→-87 |  | 3.581 | 7/96 | 130 | 130 | d2e3/141 | None | UNCLASSIFIED |
| g004 | 72 | w | Ra5+ | a7a6 | 140 | +367→+227 |  | 1.423 | 8/217 (replay differs) | 254 | 254 | a7a5/140 | None | UNCLASSIFIED |
| g030 | 18 | w | bxc6 | f3e5 | 139 | -168→-307 |  | 2.554 | 6/165 | 201 | 201 | b5c6/139 | None | UNCLASSIFIED |
| g047 | 125 | b | Bd2 | g7h6 | 139 | -578→-717 |  | 1.04 | 7/-213 (replay differs) | -152 | -152 | e3a7/79 | 6 | UNCLASSIFIED |
| g052 | 98 | w | Qe1 | d4d5 | 139 | -45→-184 | Y | 1.121 | 6/71 | 89 | 89 | f2e1/139 | None | UNCLASSIFIED |
| g032 | 31 | w | Bg4 | g1h2 | 138 | -287→-425 |  | 2.128 | 8/80 | 139 | 139 | h3g4/138 | None | UNCLASSIFIED |
| g025 | 45 | b | Kg8 | e8e6 | 137 | -6→-143 |  | 1.592 | 6/148 | 259 | 259 | h8g8/137 | None | UNCLASSIFIED |
| g048 | 20 | w | c3 | d5e3 | 136 | +69→-67 |  | 2.889 | 7/80 | 110 | 110 | c2c3/136 | None | UNCLASSIFIED |
| g011 | 48 | b | g5 | c7b6 | 135 | -350→-485 |  | 2.071 | 7/-94 | 11 | 88 | c7e5/135 | None | UNCLASSIFIED |
| g033 | 72 | b | Rb8 | e8d7 | 135 | -275→-410 |  | 3.528 | 9/1 | 9 | 9 | e8d7/0 | None | UNCLASSIFIED |
| g045 | 73 | b | Qc7 | d4b2 | 135 | +456→+321 |  | 2.061 | 5/334 (replay differs) | 399 | 399 | g3c7/135 | None | UNCLASSIFIED |
| g009 | 32 | b | Nxd5 | g8h7 | 134 | -40→-174 | Y | 1.791 | 6/54 | 86 | 94 | g6g5/58 | 7 | UNCLASSIFIED |
| g027 | 43 | b | Kg8 | f8g8 | 134 | -601→-735 |  | 1.857 | 9/-195 | 273 | 71 | f8g8/134 | None | UNCLASSIFIED |
| g002 | 44 | w | cxb6 | e5d5 | 133 | +446→+313 |  | 2.377 | 7/269 | 264 | 264 | e5d5/0 | None | UNCLASSIFIED |
| g019 | 59 | b | Kf5 | f6g6 | 133 | +342→+209 |  | 2.363 | 7/222 (replay differs) | 254 | 254 | f3e4/141 | 8 | UNCLASSIFIED |
| g025 | 47 | b | b5 | e8e6 | 133 | -51→-184 | Y | 1.948 | 6/184 | 275 | 275 | a6a5/152 | None | UNCLASSIFIED |
| g031 | 35 | b | Qc5 | e8d8 | 132 | -247→-379 |  | 4.255 | 8/-2 | 41 | 41 | e7c5/132 | None | UNCLASSIFIED |
| g033 | 84 | b | Ra2+ | a3d3 | 132 | -629→-761 |  | 1.009 | 8/-247 | -44 | -44 | a3a2/132 | None | UNCLASSIFIED |
| g055 | 23 | b | Qg5 | e6f5 | 132 | +0→-132 |  | 1.836 | 6/36 | 101 | 101 | f6g5/132 | None | UNCLASSIFIED |
| g036 | 46 | w | Bd8 | c1e1 | 130 | -436→-566 |  | 2.348 | 8/-122 | 23 | 23 | h4d8/130 | None | UNCLASSIFIED |
| g008 | 5 | w | h3 | e7c8 | 129 | -228→-357 |  | 2.857 | 6/-71 | -34 | 49 | h2h3/129 | None | UNCLASSIFIED |
| g049 | 17 | b | Bg5 | d4e2 | 128 | -212→-340 |  | 4.243 | 8/-25 | 49 | 75 | a7a5/183 | None | UNCLASSIFIED |
| g011 | 44 | b | Ne5 | f8f4 | 127 | -305→-432 |  | 2.701 | 8/-199 | 431 | 431 | c6e5/127 | None | UNCLASSIFIED |
| g030 | 16 | w | Rhe1 | c1d2 | 127 | -127→-254 | Y | 2.041 | 6/120 | 142 | 142 | h1e1/127 | None | UNCLASSIFIED |
| g047 | 67 | b | Qb3 | g7h8 | 127 | +3→-124 |  | 1.371 | 6/186 (replay differs) | 234 | 234 | g7h8/3 | 7 | UNCLASSIFIED |
| g033 | 68 | b | Rd7 | e8d7 | 126 | -248→-374 |  | 2.889 | 9/1 (replay differs) | 3 | 3 | d8b8/12 | 6 | UNCLASSIFIED |
| g019 | 53 | b | a5 | f7f5 | 125 | +395→+270 |  | 3.08 | 8/220 (replay differs) | 225 | 225 | g7f6/116 | 8 | UNCLASSIFIED |
| g044 | 24 | w | Qc2 | b2b4 | 125 | -353→-478 |  | 2.295 | 7/151 | 188 | 188 | c3b3/127 | None | UNCLASSIFIED |
| g035 | 63 | b | Bd5 | c6b5 | 124 | -3→-127 |  | 1.527 | 6/-5 | -9 | -9 | c6d5/124 | None | UNCLASSIFIED |
| g047 | 53 | b | Bd6 | f6f5 | 123 | -10→-133 |  | 6.077 | 7/97 | 188 | 188 | e7d6/123 | 6 | UNCLASSIFIED |
| g057 | 38 | b | Nxg4 | h6f7 | 123 | -365→-488 |  | 12.961 | 10/-182 | -193 | 72 | f8f2/230 | None | UNCLASSIFIED |
| g000 | 46 | w | exd5 | e4e5 | 122 | -287→-409 |  | 1.575 | 6/-94 | -112 | -30 | e4d5/122 | None | UNCLASSIFIED |
| g017 | 19 | b | Be6 | c6e7 | 119 | +212→+93 | Y | 2.623 | 6/211 | 193 | 193 | a8b8/194 | None | UNCLASSIFIED |
| g033 | 14 | b | Rfd8 | c5c4 | 119 | +116→-3 |  | 4.486 | 7/59 (replay differs) | 71 | 110 | f8d8/119 | 6 | UNCLASSIFIED |
| g033 | 82 | b | Ra3 | f7f5 | 119 | -531→-650 |  | 1.327 | 7/-132 (replay differs) | 12 | 12 | g3b3/128 | 8 | UNCLASSIFIED |
| g043 | 21 | b | Qb6 | e6e5 | 118 | -316→-434 |  | 2.429 | 7/104 | 129 | 129 | c7d6/80 | 8 | UNCLASSIFIED |
| g008 | 1 | w | Nd5 | e1g1 | 117 | -12→-129 |  | 2.971 | 6/46 | 43 | 43 | c3d5/117 | None | UNCLASSIFIED |
| g025 | 31 | b | Qb6 | e5e4 | 117 | +95→-22 |  | 4.725 | 7/194 (replay differs) | 253 | 253 | b4b6/117 | None | UNCLASSIFIED |
| g033 | 66 | b | Be8 | g5g4 | 117 | -225→-342 |  | 2.2 | 8/-38 (replay differs) | 2 | 2 | d7e8/117 | 7 | UNCLASSIFIED |
| g035 | 55 | b | dxc4 | d8f8 | 115 | -198→-313 |  | 1.35 | 6/-51 | -9 | -9 | d8b8/16 | 8 | UNCLASSIFIED |
| g047 | 71 | b | Rxg1 | b1b2 | 115 | -108→-223 | Y | 1.169 | 7/170 (replay differs) | 231 | 231 | b1b2/0 | 6 | UNCLASSIFIED |
| g011 | 22 | b | Bg6 | d8g5 | 114 | +164→+50 | Y | 2.182 | 6/129 | 149 | 149 | h5g6/114 | None | UNCLASSIFIED |
| g036 | 64 | w | Qd2 | c5c6 | 114 | -545→-659 |  | 2.288 | 8/23 | 59 | 59 | c2d2/114 | None | UNCLASSIFIED |
| g030 | 12 | w | axb5 | f3e5 | 112 | -133→-245 | Y | 2.617 | 6/97 (replay differs) | 55 | 140 | f3e5/0 | 6 | UNCLASSIFIED |
| g041 | 41 | b | Qd5 | g7g6 | 112 | +306→+194 |  | 2.199 | 6/249 | 250 | 250 | c3e5/36 | 8 | UNCLASSIFIED |
| g050 | 28 | w | cxb5 | b2b4 | 112 | -62→-174 | Y | 3.85 | 7/102 | 148 | 160 | c4b5/112 | None | UNCLASSIFIED |
| g007 | 71 | b | a5 | e4f3 | 111 | -356→-467 |  | 1.683 | 7/-258 (replay differs) | -209 | -97 | e4f3/6 | 6 | UNCLASSIFIED |
| g009 | 12 | b | c5 | c7c6 | 111 | +88→-23 |  | 2.402 | 6/69 (replay differs) | 99 | 99 | a8d8/36 | 6 | UNCLASSIFIED |
| g009 | 42 | b | Ra8 | d8f8 | 111 | -131→-242 | Y | 2.467 | 6/72 | 144 | 144 | d8a8/111 | None | UNCLASSIFIED |
| g015 | 33 | b | Qh3 | f6d5 | 111 | +236→+125 | Y | 2.859 | 6/233 | 217 | 217 | g4h3/111 | None | UNCLASSIFIED |
| g032 | 35 | w | cxd4 | g4f5 | 111 | -430→-541 |  | 2.41 | 8/138 | 123 | 123 | c3d4/111 | None | UNCLASSIFIED |
| g042 | 138 | w | Nb3 | d2b3 | 109 | -227→-336 |  | 1.571 | 9/-38 | -47 | -47 | d2b3/109 | None | UNCLASSIFIED |
| g013 | 87 | b | Kf6 | h2e2 | 108 | +0→-108 |  | 1.494 | 6/24 (replay differs) | 271 | 271 | c6c5/91 | 6 | UNCLASSIFIED |
| g048 | 16 | w | Ng4 | d5e7 | 108 | +5→-103 |  | 1.908 | 7/33 | 197 | 197 | c2c4/36 | 6 | UNCLASSIFIED |
| g036 | 24 | w | exd5 | c3c4 | 106 | -117→-223 | Y | 3.547 | 6/36 (replay differs) | 101 | 101 | c3c4/4 | 6 | UNCLASSIFIED |
| g041 | 21 | b | Rad8 | b7c6 | 106 | +43→-63 |  | 2.795 | 6/105 | 89 | 89 | a8d8/106 | None | UNCLASSIFIED |
| g007 | 35 | b | Rf7 | d6d5 | 105 | -292→-397 |  | 1.577 | 6/-195 | -140 | -140 | f8f7/105 | None | UNCLASSIFIED |
| g016 | 38 | w | Rb1 | b3c4 | 105 | +109→+4 |  | 2.676 | 6/49 | 90 | 92 | d1b1/105 | 8 | UNCLASSIFIED |
| g020 | 46 | w | Bh4 | d8e8 | 105 | +119→+14 |  | 1.709 | 8/244 (replay differs) | 260 | 284 | g5h4/105 | 6 | UNCLASSIFIED |
| g049 | 19 | b | Bf6 | d4e2 | 105 | -314→-419 |  | 3.925 | 9/-51 | 44 | 44 | g5f6/105 | None | UNCLASSIFIED |
| g019 | 55 | b | Kf6 | e5e2 | 104 | +318→+214 |  | 2.386 | 7/215 | 246 | 246 | f3d5/108 | None | UNCLASSIFIED |
| g027 | 29 | b | d5 | d8a5 | 104 | +0→-104 |  | 2.717 | 6/336 | 647 | 647 | d8a5/1 | 8 | UNCLASSIFIED |
| g015 | 47 | b | Ng4 | g5h4 | 103 | +401→+298 |  | 3.108 | 8/336 | 316 | 316 | f6g4/103 | None | UNCLASSIFIED |
| g006 | 14 | w | Bb6 | c4b6 | 102 | -205→-307 |  | 2.125 | 7/-56 | -51 | -51 | e3b6/102 | None | UNCLASSIFIED |
| g033 | 76 | b | Rb2 | b3g3 | 101 | -395→-496 |  | 1.509 | 7/-55 (replay differs) | 22 | 22 | b3b1/92 | None | UNCLASSIFIED |
| g035 | 43 | b | Nd7 | e7c7 | 101 | -72→-173 | Y | 2.624 | 8/12 | -5 | -5 | b6d7/101 | None | UNCLASSIFIED |
| g047 | 129 | b | Kf8 | g8h7 | 101 | -583→-684 |  | 0.754 | 8/-277 | -187 | -187 | g7h7/195 | None | UNCLASSIFIED |
| g048 | 50 | w | a5 | a4b5 | 101 | -164→-265 |  | 2.931 | 7/116 | 178 | 178 | a4a5/101 | 6 | UNCLASSIFIED |
| g016 | 34 | w | Rfe1 | e3e4 | 100 | +74→-26 |  | 3.169 | 6/65 | 84 | 84 | d2c1/108 | None | UNCLASSIFIED |
| g036 | 22 | w | g3 | c3c4 | 100 | -27→-127 |  | 2.051 | 6/63 | 125 | 125 | c1d1/15 | 7 | UNCLASSIFIED |
| g047 | 69 | b | Rb1+ | b2c2 | 100 | -117→-217 | Y | 1.998 | 7/131 | 241 | 323 | b2b1/100 | None | UNCLASSIFIED |
