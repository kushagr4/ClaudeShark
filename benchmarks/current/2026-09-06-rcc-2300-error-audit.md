# Large-error audit — rcc_vs_sf2300_dev_100.annotated.jsonl

engine champions\rc_c; 100 games; 4023 of our moves audited (positions already beyond +/-800 cp excluded)

| bin | moves | share |
|---|---|---|
| <50 | 3283 | 81.6% |
| 50-99 | 380 | 9.4% |
| 100-299 | 304 | 7.6% |
| >=300 | 56 | 1.4% |

**>=100 cp self-inflicted error rate: 8.95% of moves** (360 errors); >=300 cp: 1.39% (56); average cp loss 79.7
games with at least one >=100 cp error: 87 of 100; result-flipping errors: 135; errors per loss: 4.50 over 22 losses

## Every >=100 cp error (sorted by cp loss)

| game | ply | col | played | oracle | loss | before→after | flip | spent s | replay depth/score | static | qsearch | deep(10 s) move/loss | min repair depth | mechanism |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| g013 | 47 | b | exf4 | f7f6 | 10408 | +408→-10000 | Y | - | 6/1279 | 1243 | 1447 | f7f6/0 | 7 | UNCLASSIFIED |
| g095 | 31 | b | Bc4 | f6f5 | 10000 | +0→-10000 | Y | - | 6/241 (replay differs) | 159 | 159 | e8c8/442 | 6 | UNCLASSIFIED |
| g097 | 37 | b | dxc4 | g6d3 | 9782 | -218→-10000 |  | - | 5/280 | 295 | 295 | g6d3/100 | None | UNCLASSIFIED |
| g017 | 87 | b | e2 | a2d2 | 9557 | -443→-10000 |  | - | 7/-99 | 2 | 12 | a2d2/0 | 6 | UNCLASSIFIED |
| g076 | 24 | w | Nxc5 | a4d7 | 9537 | -463→-10000 |  | - | 7/439 | 117 | 488 | b3c5/9537 | None | UNCLASSIFIED |
| g048 | 50 | w | gxf4 | e2e3 | 9508 | -492→-10000 |  | - | 6/-274 | -187 | 77 | g3f4/9508 | 8 | UNCLASSIFIED |
| g063 | 29 | b | f5 | h8g8 | 9418 | -582→-10000 |  | - | 8/-60 | 170 | 170 | f7f5/9418 | None | UNCLASSIFIED |
| g094 | 42 | w | Ra6 | e1e2 | 9407 | -593→-10000 |  | - | 7/286 (replay differs) | 361 | 361 | a1a6/9407 | None | UNCLASSIFIED |
| g022 | 40 | w | b5 | c3e5 | 9371 | -629→-10000 |  | - | 6/-3 (replay differs) | 68 | 68 | d1c1/9371 | None | UNCLASSIFIED |
| g054 | 42 | w | Kf1 | f2f3 | 9365 | -635→-10000 |  | - | 7/17 | 160 | 160 | f2f3/36 | 8 | UNCLASSIFIED |
| g075 | 63 | b | Bc4 | c7c6 | 9297 | -703→-10000 |  | - | 7/-537 | -429 | -429 | a7a5/9297 | None | UNCLASSIFIED |
| g072 | 81 | w | Bc4 | h1g2 | 9291 | -709→-10000 |  | - | 7/-524 (replay differs) | -42 | -42 | h1g2/11 | 7 | UNCLASSIFIED |
| g041 | 43 | b | Qc7 | c8c5 | 9283 | -717→-10000 |  | - | 6/-225 | -18 | -18 | b8f4/9283 | None | UNCLASSIFIED |
| g052 | 124 | w | Ke3 | g4g2 | 9280 | -720→-10000 |  | - | 9/-200 | 188 | 163 | g4g2/0 | None | UNCLASSIFIED |
| g060 | 62 | w | h6 | h5h6 | 9262 | -738→-10000 |  | - | 7/108 | 120 | 120 | h5h6/9262 | None | UNCLASSIFIED |
| g060 | 64 | w | Qd5 | b7b8 | 9256 | -744→-10000 |  | - | 6/120 | 148 | 236 | b7d5/9256 | None | UNCLASSIFIED |
| g049 | 63 | b | Nxd5 | b4d3 | 9250 | -750→-10000 |  | - | 6/-204 | 136 | 200 | c7e7/9250 | None | UNCLASSIFIED |
| g015 | 45 | b | Qxe7 | f6f4 | 9229 | -771→-10000 |  | - | 7/-1082 | -1045 | -714 | f6e6/9229 | None | UNCLASSIFIED |
| g011 | 100 | b | Bxe3 | c7b8 | 9226 | -774→-10000 |  | - | 8/-909 (replay differs) | -761 | -761 | c7b7/17 | 6 | UNCLASSIFIED |
| g081 | 33 | b | Qd7 | d8f6 | 9207 | -793→-10000 |  | - | 6/-29 | 132 | 132 | d8d7/9207 | 8 | UNCLASSIFIED |
| g070 | 29 | w | Qxb3 | d1d2 | 9201 | -799→-10000 |  | - | 9/-662 | 135 | 135 | b2b3/9201 | None | UNCLASSIFIED |
| g063 | 19 | b | Kxg7 | f8d8 | 701 | -367→-1068 |  | - | 7/-31 | 9 | 109 | f5g7/53 | 8 | UNCLASSIFIED |
| g065 | 53 | b | Bf7 | d8d5 | 675 | +148→-527 | Y | - | 6/214 | 329 | 329 | a2f7/675 | 7 | UNCLASSIFIED |
| g005 | 47 | b | g6 | a2e2 | 575 | +246→-329 | Y | - | 7/157 | 312 | 381 | g7g6/575 | None | UNCLASSIFIED |
| g008 | 111 | w | Ra8 | f2f4 | 486 | +486→+0 | Y | - | 8/363 | 377 | 462 | a5a8/486 | None | UNCLASSIFIED |
| g081 | 31 | b | Re8 | e6d5 | 482 | -301→-783 |  | - | 6/81 | 137 | 137 | e6d5/0 | 7 | UNCLASSIFIED |
| g019 | 79 | b | Bg2 | f7f5 | 447 | -672→-1119 |  | - | 8/-503 (replay differs) | -309 | -309 | e1e8/158 | None | UNCLASSIFIED |
| g098 | 111 | w | Rd7 | e1d1 | 436 | -670→-1106 |  | - | 8/-260 (replay differs) | -160 | -160 | f6f7/262 | None | UNCLASSIFIED |
| g093 | 29 | b | O-O | d6e5 | 431 | +94→-337 | Y | - | 6/156 | 184 | 217 | e8g8/431 | None | UNCLASSIFIED |
| g076 | 20 | w | Nb3 | g4g5 | 424 | -307→-731 |  | - | 6/112 | 186 | 186 | d2b3/424 | None | UNCLASSIFIED |
| g094 | 36 | w | Bc2 | f3f4 | 407 | +99→-308 | Y | - | 6/326 (replay differs) | 334 | 334 | b3c2/407 | None | UNCLASSIFIED |
| g023 | 25 | b | Ne4 | d2d1 | 402 | -21→-423 | Y | - | 7/15 | 26 | 197 | f6e4/402 | 6 | UNCLASSIFIED |
| g043 | 39 | b | Ba4 | h5g4 | 400 | -332→-732 |  | - | 5/-29 (replay differs) | -39 | 65 | d7a4/400 | None | UNCLASSIFIED |
| g065 | 51 | b | Bxa2 | d8d5 | 397 | +29→-368 | Y | - | 6/204 | 291 | 297 | f7a2/397 | 7 | UNCLASSIFIED |
| g029 | 99 | b | Rb1 | c1c4 | 391 | -52→-443 | Y | - | 6/9 (replay differs) | 67 | 67 | c1b1/391 | 6 | UNCLASSIFIED |
| g052 | 94 | w | h3 | g8c4 | 389 | +0→-389 | Y | - | 7/236 | 363 | 363 | h2h3/389 | None | UNCLASSIFIED |
| g057 | 52 | b | Rxb3 | d7c7 | 388 | +243→-145 | Y | - | 8/74 (replay differs) | 75 | 167 | d7c7/0 | 8 | UNCLASSIFIED |
| g060 | 58 | w | Qxb7 | f3d5 | 368 | -478→-846 |  | - | 8/65 | 73 | 73 | f3d5/0 | None | UNCLASSIFIED |
| g096 | 108 | w | Re6+ | e1d1 | 363 | +0→-363 | Y | - | 8/212 (replay differs) | 238 | 1200 | b6e6/363 | 6 | UNCLASSIFIED |
| g044 | 28 | w | Qe2 | h5f3 | 357 | -232→-589 |  | - | 8/389 | 442 | 442 | h5e2/357 | None | UNCLASSIFIED |
| g001 | 41 | b | Rc2 | f4f3 | 350 | +0→-350 | Y | - | 7/42 (replay differs) | 209 | 209 | e6e5/431 | 6 | UNCLASSIFIED |
| g072 | 37 | w | Qe2 | e5d3 | 347 | +101→-246 | Y | - | 6/84 | 97 | 97 | e5d3/3 | 7 | UNCLASSIFIED |
| g024 | 48 | w | Rd1 | d6a6 | 342 | -28→-370 | Y | - | 7/-8 (replay differs) | 116 | 116 | e1d1/342 | None | UNCLASSIFIED |
| g087 | 143 | b | Ng5 | g6f6 | 341 | -558→-899 |  | - | 12/-194 | -209 | -209 | f7d8/67 | None | UNCLASSIFIED |
| g077 | 49 | b | Qxb2 | d2d5 | 336 | -166→-502 |  | - | 6/57 | -17 | 22 | d2b2/336 | 8 | UNCLASSIFIED |
| g075 | 29 | b | Ba4 | a6b5 | 330 | +164→-166 | Y | - | 6/29 | 200 | 200 | b3a4/330 | 8 | UNCLASSIFIED |
| g088 | 18 | w | Nxb7 | a1b1 | 328 | -38→-366 | Y | - | 6/90 | 115 | 115 | a1b1/3 | 7 | UNCLASSIFIED |
| g087 | 117 | b | Nd4 | e2c3 | 322 | -387→-709 |  | - | 11/-164 (replay differs) | -159 | -159 | e2c3/8 | 7 | UNCLASSIFIED |
| g058 | 32 | w | Bxe6 | e1e6 | 316 | +436→+120 | Y | - | 5/151 (replay differs) | 99 | 99 | a2a3/321 | None | UNCLASSIFIED |
| g009 | 56 | b | Rd8 | a8e8 | 314 | -12→-326 | Y | - | 7/178 | 257 | 257 | a8d8/314 | None | UNCLASSIFIED |
| g029 | 19 | b | Qxb2 | a7a5 | 314 | -112→-426 | Y | - | 6/142 | 158 | 192 | b6b2/314 | 8 | UNCLASSIFIED |
| g075 | 43 | b | e2 | d8d4 | 313 | -197→-510 |  | - | 6/24 | 282 | 282 | e3e2/313 | None | UNCLASSIFIED |
| g063 | 39 | b | Rf8 | c6d4 | 308 | -523→-831 |  | - | 7/-30 (replay differs) | 12 | 12 | f7f8/308 | 8 | UNCLASSIFIED |
| g058 | 30 | w | Bf5 | e1e6 | 306 | +415→+109 | Y | - | 6/88 | 88 | 88 | d3f5/306 | None | UNCLASSIFIED |
| g068 | 28 | w | Kc1 | d2c3 | 305 | -393→-698 |  | - | 7/133 | 295 | 332 | f1d3/40 | None | UNCLASSIFIED |
| g011 | 26 | b | Bg4 | a8d8 | 302 | -127→-429 | Y | - | 4/92 (replay differs) | 168 | 168 | e6g4/302 | 7 | UNCLASSIFIED |
| g001 | 69 | b | Rg2 | g7g6 | 299 | -279→-578 |  | - | 8/0 (replay differs) | 54 | 54 | g7g6/20 | 8 | UNCLASSIFIED |
| g008 | 113 | w | Ra2 | g6f5 | 299 | +639→+340 |  | - | 9/377 | 401 | 401 | a8a1/12 | None | UNCLASSIFIED |
| g019 | 73 | b | Bxf3 | g2f3 | 291 | -749→-1040 |  | - | 10/-731 | -414 | -327 | g2f3/291 | None | UNCLASSIFIED |
| g077 | 21 | b | Nc5 | d7b6 | 290 | -86→-376 | Y | - | 6/-52 (replay differs) | 18 | 53 | g7g6/140 | None | UNCLASSIFIED |
| g097 | 33 | b | hxg4 | f5e7 | 288 | +83→-205 | Y | - | 7/161 | 299 | 310 | h5g4/288 | None | UNCLASSIFIED |
| g014 | 64 | w | Be4 | b7e7 | 284 | +284→+0 | Y | - | 7/283 | 288 | 288 | b7c7/247 | None | UNCLASSIFIED |
| g079 | 45 | b | Qxf1 | h7h5 | 283 | +283→+0 | Y | - | 6/1142 | 818 | 1342 | b5f1/283 | 8 | UNCLASSIFIED |
| g008 | 123 | w | Ra2 | f2f3 | 278 | +278→+0 | Y | - | 9/335 | 373 | 373 | d2a2/278 | None | UNCLASSIFIED |
| g070 | 19 | w | a3 | c1d2 | 278 | -272→-550 |  | - | 6/134 | 35 | 77 | a2a3/278 | None | UNCLASSIFIED |
| g006 | 38 | w | Qg4 | d4f2 | 275 | +763→+488 |  | - | 6/882 | 876 | 876 | d4f2/9 | 7 | UNCLASSIFIED |
| g012 | 28 | w | Rc3 | c7e6 | 275 | +18→-257 | Y | - | 5/8 | 31 | 31 | c4c3/275 | None | UNCLASSIFIED |
| g049 | 59 | b | Ke8 | e5f5 | 273 | -275→-548 |  | - | 7/135 (replay differs) | 98 | 183 | e5f5/0 | 6 | UNCLASSIFIED |
| g052 | 120 | w | Qb1 | f1d1 | 268 | -111→-379 | Y | - | 6/180 | 216 | 216 | b2b4/265 | None | UNCLASSIFIED |
| g015 | 31 | b | Ra1 | g8g7 | 267 | -332→-599 |  | - | 6/-87 (replay differs) | 269 | 269 | d4c3/251 | None | UNCLASSIFIED |
| g023 | 59 | b | Ke6 | f7g6 | 267 | -324→-591 |  | - | 9/0 | 166 | 44 | f7e6/267 | 6 | UNCLASSIFIED |
| g044 | 32 | w | Bxh3 | e2f1 | 266 | -386→-652 |  | - | 8/635 | 395 | 701 | g2h3/266 | None | UNCLASSIFIED |
| g020 | 76 | w | Ne4 | c5c6 | 265 | +16→-249 | Y | - | 8/210 | 272 | 272 | g5e4/265 | None | UNCLASSIFIED |
| g047 | 113 | b | Bg3 | g2g3 | 265 | +273→+8 | Y | - | 8/229 | 267 | 267 | g2g3/4 | None | UNCLASSIFIED |
| g035 | 33 | b | fxg6 | f8d6 | 263 | -523→-786 |  | - | 6/25 | -52 | 219 | f7g6/263 | None | UNCLASSIFIED |
| g076 | 16 | w | hxg4 | c6a4 | 262 | -39→-301 | Y | - | 7/140 | 303 | 303 | h3g4/262 | None | UNCLASSIFIED |
| g063 | 9 | b | Qxa3 | a5c7 | 261 | -106→-367 | Y | - | 7/16 | 2 | 41 | a5a3/261 | None | UNCLASSIFIED |
| g090 | 34 | w | cxb6 | h5g3 | 258 | -3→-261 | Y | - | 8/132 | 169 | 169 | f1e1/0 | None | UNCLASSIFIED |
| g013 | 45 | b | Qxa2 | b1e4 | 255 | +715→+460 |  | - | 6/1426 | 1643 | 1643 | b1a2/255 | 8 | UNCLASSIFIED |
| g023 | 55 | b | b6 | a7d4 | 254 | -234→-488 |  | - | 8/31 | 171 | 171 | b7b6/254 | None | UNCLASSIFIED |
| g061 | 155 | b | Ke6 | f7c4 | 253 | +46→-207 | Y | - | 8/24 | 167 | 167 | f7g8/250 | None | UNCLASSIFIED |
| g070 | 21 | w | Kc2 | c1b1 | 253 | -551→-804 |  | - | 7/145 (replay differs) | 121 | 122 | c1c2/253 | 6 | UNCLASSIFIED |
| g060 | 22 | w | Rc1 | g2g4 | 248 | +51→-197 | Y | - | 6/101 (replay differs) | 107 | 107 | a1c1/248 | None | UNCLASSIFIED |
| g050 | 28 | w | Nf4 | b2b4 | 245 | -155→-400 |  | - | 6/161 | 244 | 470 | a4a5/82 | 7 | UNCLASSIFIED |
| g070 | 17 | w | c3 | f5d4 | 243 | -233→-476 |  | - | 6/-27 | 9 | 9 | c2c3/243 | None | UNCLASSIFIED |
| g049 | 43 | b | Qxa5 | e5d4 | 242 | -83→-325 | Y | - | 6/87 | 25 | 72 | c7a5/242 | None | UNCLASSIFIED |
| g090 | 130 | w | f7 | h4h3 | 240 | +0→-240 | Y | - | 10/-10 | -64 | -64 | c3c4/24 | None | UNCLASSIFIED |
| g066 | 44 | w | Kf2 | d5a5 | 239 | +259→+20 | Y | - | 7/182 | 211 | 211 | d5d3/216 | None | UNCLASSIFIED |
| g021 | 81 | b | Qg2 | h2h3 | 238 | -37→-275 | Y | - | 8/-21 | 55 | 55 | h2h3/0 | None | UNCLASSIFIED |
| g028 | 22 | w | Qxe4 | d3e2 | 237 | -46→-283 | Y | - | 6/113 | 124 | 124 | e3e4/237 | 8 | UNCLASSIFIED |
| g024 | 74 | w | Kf2 | f5f6 | 233 | -535→-768 |  | - | 9/-427 | -334 | -334 | g1f2/233 | 6 | UNCLASSIFIED |
| g044 | 30 | w | Bg2 | e2f3 | 233 | -225→-458 |  | - | 7/369 (replay differs) | 426 | 426 | d2f3/243 | None | UNCLASSIFIED |
| g022 | 34 | w | Ng2 | f1g2 | 229 | -352→-581 |  | - | 8/28 | 209 | 117 | h4g2/229 | None | UNCLASSIFIED |
| g068 | 26 | w | Qxe4 | a4d4 | 227 | -200→-427 |  | - | 6/308 | 207 | 309 | a4e4/227 | 8 | UNCLASSIFIED |
| g054 | 46 | w | b5 | f1e2 | 226 | -678→-904 |  | - | 8/-287 (replay differs) | -106 | -106 | f7c4/9322 | None | UNCLASSIFIED |
| g089 | 47 | b | Kg8 | h7g7 | 226 | +226→+0 | Y | - | 8/230 | 368 | 278 | h7g8/226 | None | UNCLASSIFIED |
| g072 | 75 | w | Bxc5 | d4e3 | 225 | -462→-687 |  | - | 6/-114 | 27 | 27 | d4c5/225 | None | UNCLASSIFIED |
| g041 | 17 | b | b5 | f4h6 | 224 | -36→-260 | Y | - | 6/63 | 99 | 99 | b7b5/224 | None | UNCLASSIFIED |
| g093 | 125 | b | Re6+ | c6d6 | 221 | -10→-231 | Y | - | 8/17 | 47 | 47 | f7e6/68 | None | UNCLASSIFIED |
| g017 | 53 | b | Bd4 | e3c5 | 220 | -206→-426 |  | - | 6/-20 | 79 | 79 | b6a5/96 | 7 | UNCLASSIFIED |
| g052 | 86 | w | Qf7+ | g8h7 | 220 | +385→+165 |  | - | 7/692 | 365 | 365 | g2f1/214 | None | UNCLASSIFIED |
| g011 | 84 | b | Rd2 | b2d2 | 217 | -717→-934 |  | - | 7/-719 | -582 | -582 | b2d2/217 | None | UNCLASSIFIED |
| g047 | 101 | b | Rg6 | d4d5 | 217 | +237→+20 | Y | - | 7/153 | 159 | 159 | g3g6/217 | 6 | UNCLASSIFIED |
| g060 | 34 | w | Ng5+ | f3h2 | 216 | -84→-300 | Y | - | 6/138 | 180 | 180 | f3h2/14 | 7 | UNCLASSIFIED |
| g096 | 104 | w | Rh6 | h8h7 | 215 | +0→-215 | Y | - | 7/125 (replay differs) | 250 | 250 | h8h7/0 | 6 | UNCLASSIFIED |
| g098 | 117 | w | f7 | f6f7 | 212 | -591→-803 |  | - | 9/-358 | -244 | -244 | f6f7/212 | None | UNCLASSIFIED |
| g028 | 122 | w | Kg2 | h5h6 | 210 | -14→-224 | Y | - | 9/70 | 116 | 116 | f3g2/210 | None | UNCLASSIFIED |
| g048 | 30 | w | c3 | d1d2 | 210 | -22→-232 | Y | - | 6/98 | 127 | 127 | f1f2/219 | None | UNCLASSIFIED |
| g035 | 71 | b | Be8 | e6e8 | 209 | -664→-873 |  | - | 10/-422 | -248 | -248 | c6e8/209 | None | UNCLASSIFIED |
| g065 | 9 | b | Nc6 | d6e5 | 208 | +5→-203 | Y | - | 6/43 | -10 | -10 | b8c6/208 | None | UNCLASSIFIED |
| g094 | 34 | w | f3 | e3f5 | 208 | +300→+92 | Y | - | 6/370 | 368 | 368 | f2f3/208 | 8 | UNCLASSIFIED |
| g065 | 37 | b | Ree8 | e6g6 | 206 | +201→-5 | Y | - | 6/241 (replay differs) | 271 | 271 | e6g6/7 | 7 | UNCLASSIFIED |
| g096 | 106 | w | Rb6 | h6h8 | 205 | +0→-205 | Y | - | 6/125 (replay differs) | 206 | 206 | h6h8/0 | 6 | UNCLASSIFIED |
| g043 | 31 | b | g4 | d8d6 | 204 | -183→-387 |  | - | 6/62 | 179 | 179 | g8f8/113 | None | UNCLASSIFIED |
| g063 | 17 | b | Ncxd4 | g7g6 | 204 | -163→-367 |  | - | 6/84 | 51 | 109 | f5h6/303 | None | UNCLASSIFIED |
| g068 | 24 | w | Qa4+ | d2c2 | 204 | +1→-203 | Y | - | 6/281 | 191 | 288 | d1a4/204 | None | UNCLASSIFIED |
| g081 | 27 | b | Bd7 | f5g6 | 204 | -197→-401 |  | - | 7/51 | 170 | 170 | f5g6/0 | None | UNCLASSIFIED |
| g022 | 38 | w | Bc3 | d4e5 | 198 | -586→-784 |  | - | 6/-2 (replay differs) | 87 | 87 | b4b5/225 | 8 | UNCLASSIFIED |
| g049 | 41 | b | Be5 | f6d4 | 198 | -39→-237 | Y | - | 6/33 (replay differs) | 49 | 49 | f6d4/0 | 6 | UNCLASSIFIED |
| g005 | 43 | b | Rxa3 | b3b1 | 197 | -63→-260 | Y | - | 7/216 | 261 | 305 | g7g6/234 | 6 | UNCLASSIFIED |
| g098 | 57 | w | Nc5 | b3b4 | 197 | -74→-271 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g008 | 75 | w | g3 | d1d6 | 196 | +420→+224 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g018 | 40 | w | Qf6 | e6e7 | 196 | +766→+570 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g093 | 15 | b | Qa5 | e7e6 | 196 | +22→-174 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g054 | 40 | w | b4 | g2g3 | 195 | -465→-660 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g070 | 5 | w | Ndf3 | e2f3 | 195 | -5→-200 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g084 | 2 | w | Rf1 | d3h7 | 195 | +141→-54 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g019 | 77 | b | Re1 | g7g5 | 194 | -711→-905 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g093 | 25 | b | e6 | f7f6 | 192 | +126→-66 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g073 | 48 | b | Ra5 | f6e7 | 190 | -447→-637 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g033 | 30 | b | Ne6 | f4d3 | 188 | +379→+191 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g065 | 15 | b | dxe5 | g7h6 | 187 | -200→-387 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g049 | 49 | b | gxf5 | e8e5 | 186 | -120→-306 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g061 | 55 | b | Rc3 | f7f6 | 186 | -61→-247 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g064 | 28 | w | dxe6 | g3f4 | 186 | +172→-14 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g056 | 19 | w | Be5 | d1c1 | 184 | -94→-278 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g087 | 145 | b | Kxg5 | g6g5 | 184 | -738→-922 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g038 | 58 | w | Rb1 | h4h5 | 183 | +0→-183 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g015 | 13 | b | Na5 | g8g7 | 182 | +65→-117 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g015 | 37 | b | Ra3 | f6h5 | 182 | -555→-737 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g079 | 41 | b | Nxf1+ | d2e4 | 182 | +512→+330 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 93 | b | Bxg4+ | e8e4 | 181 | -270→-451 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g055 | 7 | b | Bf5 | f7f5 | 181 | +156→-25 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g052 | 90 | w | Qg8 | f7c4 | 180 | +180→+0 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g017 | 55 | b | Kg8 | d4c5 | 177 | -258→-435 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g096 | 50 | w | Qf2 | d6b5 | 177 | +200→+23 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 91 | b | Bf3 | c1h1 | 176 | -110→-286 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g054 | 30 | w | Rd1 | f2f3 | 176 | -190→-366 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g072 | 35 | w | Bf2 | e5c4 | 176 | -15→-191 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g038 | 122 | w | Bc5 | d8d7 | 174 | +646→+472 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g047 | 23 | b | Nxg5 | h7h6 | 173 | -67→-240 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g096 | 114 | w | bxa3 | d6h6 | 172 | -362→-534 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g041 | 37 | b | Bb8 | f4h2 | 170 | -446→-616 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g093 | 145 | b | Rf7+ | g7f7 | 170 | -28→-198 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g017 | 33 | b | hxg6 | e3f2 | 168 | -76→-244 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g034 | 46 | w | Rd2 | e2a6 | 168 | -543→-711 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g078 | 96 | w | Kf4 | e3d5 | 168 | -231→-399 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g093 | 13 | b | Bb7 | d8d4 | 168 | +26→-142 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g008 | 81 | w | Rc2 | c4b4 | 167 | +326→+159 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g011 | 30 | b | Bf3 | e7e5 | 166 | -370→-536 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g043 | 17 | b | Bc6 | f6g4 | 166 | -47→-213 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g003 | 65 | b | c5 | d7e7 | 165 | +520→+355 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g003 | 27 | b | Nf5 | g3e4 | 164 | +115→-49 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g047 | 15 | b | b6 | c8e6 | 164 | +32→-132 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g096 | 84 | w | Rc6 | g3e1 | 164 | +295→+131 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g028 | 20 | w | Nxe4 | d3e4 | 163 | +117→-46 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g054 | 38 | w | Rc1 | d4d5 | 163 | -338→-501 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 55 | b | Qa3 | b4c4 | 162 | -242→-404 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g020 | 30 | w | Ng5 | f3d4 | 161 | +165→+4 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g049 | 51 | b | b5 | e8e5 | 161 | -322→-483 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 85 | b | Bf5 | c1c6 | 160 | -88→-248 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g036 | 32 | w | Rd1 | a7a6 | 160 | +136→-24 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g082 | 36 | w | Nf3 | g1h2 | 160 | +61→-99 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g092 | 38 | w | Qd5+ | e1c3 | 160 | +231→+71 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g020 | 102 | w | Rd2 | g1g2 | 159 | -255→-414 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g035 | 29 | b | g6 | a8d8 | 159 | -342→-501 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g060 | 26 | w | Bh4 | h3h4 | 159 | -192→-351 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g075 | 47 | b | Rd1+ | a6f6 | 158 | -572→-730 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g001 | 67 | b | Rf7 | g8h8 | 156 | -130→-286 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g020 | 94 | w | Rc8 | g1g2 | 156 | -243→-399 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g070 | 13 | w | Nh4 | e2d2 | 156 | -70→-226 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g008 | 89 | w | g4 | a2e2 | 155 | +155→+0 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g088 | 14 | w | e4 | d2d4 | 155 | +118→-37 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g005 | 27 | b | Rfe8 | f8f5 | 153 | -27→-180 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g056 | 31 | w | Rd2 | e2b5 | 153 | -273→-426 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g060 | 54 | w | Bh2 | h5h6 | 153 | -454→-607 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g050 | 22 | w | c4 | h2h3 | 152 | -8→-160 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g077 | 17 | b | Nxf3+ | d4b5 | 152 | +132→-20 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g078 | 88 | w | Ne3 | f1d2 | 152 | -238→-390 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g023 | 61 | b | g6 | b6b5 | 151 | -273→-424 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g003 | 25 | b | Ng3 | b8d7 | 150 | +269→+119 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g026 | 30 | w | Rfb1 | e4f6 | 150 | +643→+493 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g075 | 73 | b | Bc4 | e6b3 | 150 | -653→-803 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 65 | b | Be6 | e8e5 | 149 | -352→-501 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g038 | 20 | w | b3 | d3c4 | 149 | -87→-236 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g051 | 45 | b | Rc8 | d8d2 | 149 | +417→+268 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g041 | 11 | b | Bd7 | d5c3 | 148 | +87→-61 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g096 | 86 | w | Rxh6 | e5f6 | 148 | +148→+0 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g070 | 23 | w | bxc3 | e2d3 | 147 | -776→-923 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g096 | 80 | w | Qg3 | f2e3 | 147 | +231→+84 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g001 | 63 | b | Rf7 | g8h8 | 146 | -126→-272 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g015 | 25 | b | Rxa4 | b6d4 | 146 | -212→-358 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 35 | b | d3 | f7f6 | 146 | -175→-321 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g081 | 23 | b | Be6 | c5c4 | 146 | -119→-265 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g017 | 7 | b | Nbxd5 | e6d5 | 145 | -28→-173 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g052 | 8 | w | Ne5 | f1e1 | 145 | +125→-20 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g021 | 73 | b | Qh2 | g6g5 | 144 | +0→-144 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g091 | 29 | b | Qxa3 | g8h7 | 144 | +250→+106 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g019 | 71 | b | Re2+ | g2f3 | 143 | -657→-800 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g009 | 8 | b | Bxc3+ | g6g5 | 142 | +137→-5 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g030 | 64 | w | Be2 | f2f4 | 142 | +180→+38 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g052 | 38 | w | Be3 | d5d6 | 142 | +18→-124 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g080 | 50 | w | a4 | c3a5 | 142 | +243→+101 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g096 | 126 | w | Bf6+ | d1d2 | 141 | -649→-790 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g006 | 18 | w | Rae1 | a4a5 | 140 | -131→-271 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g019 | 35 | b | Rc4 | h6h5 | 140 | -225→-365 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 97 | b | Ree1 | f3e4 | 139 | -27→-166 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g087 | 83 | b | Rc8 | g8f7 | 139 | -307→-446 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g036 | 4 | w | Nxd4 | c3d5 | 138 | -149→-287 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g052 | 70 | w | Bh6 | g4h3 | 138 | -152→-290 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g077 | 47 | b | Qd2 | f2c5 | 138 | -91→-229 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g014 | 12 | w | e6 | e5d6 | 137 | +234→+97 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g021 | 99 | b | Qxf2 | b6c7 | 137 | -338→-475 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g061 | 91 | b | Bxg4 | g5h4 | 137 | -33→-170 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g064 | 22 | w | Bg3 | e5d3 | 137 | +63→-74 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g086 | 48 | w | Qc3 | a4c3 | 137 | +46→-91 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g018 | 4 | w | Qc4 | f5h6 | 136 | -57→-193 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g021 | 145 | b | Qd6 | b6d6 | 136 | -786→-922 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 71 | b | Qxc1 | d6f5 | 136 | -310→-446 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g085 | 31 | b | Qb8 | a8c6 | 136 | -62→-198 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g090 | 136 | w | Rc7 | f7h7 | 136 | -284→-420 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g006 | 4 | w | Bxe6 | c1e3 | 135 | +30→-105 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g006 | 16 | w | h3 | a4a5 | 135 | -40→-175 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g019 | 37 | b | h5 | d5d4 | 135 | -301→-436 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g043 | 43 | b | hxg4 | e8f8 | 135 | -644→-779 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g030 | 42 | w | Qg5 | f2f4 | 134 | +258→+124 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g034 | 20 | w | Qc2 | f3d4 | 134 | -85→-219 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g066 | 8 | w | b4 | e1g1 | 133 | -42→-175 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g085 | 35 | b | Be7 | c8c7 | 133 | -131→-264 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g008 | 95 | w | Rg3 | d3d1 | 132 | -110→-242 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g048 | 32 | w | d4 | g3g4 | 132 | -191→-323 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g072 | 59 | w | Rc1 | b4b5 | 132 | -200→-332 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g080 | 10 | w | f5 | d1d2 | 132 | +141→+9 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g014 | 70 | w | Kh3 | h2g2 | 130 | +377→+247 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g034 | 38 | w | Rf1 | c3a1 | 130 | -339→-469 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g064 | 62 | w | Rg7 | g2g5 | 130 | -11→-141 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g065 | 25 | b | Qb6 | d8f6 | 130 | -189→-319 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g074 | 14 | w | Rae1 | b5c6 | 130 | -40→-170 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g078 | 62 | w | c4 | b2c2 | 130 | -139→-269 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g083 | 51 | b | Rd3 | b8f4 | 130 | -25→-155 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g021 | 101 | b | Qh2+ | f2g3 | 129 | -330→-459 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g036 | 2 | w | d4 | c1d2 | 129 | -19→-148 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g058 | 28 | w | Qc2 | e1c1 | 129 | +172→+43 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g074 | 18 | w | e5 | b2b4 | 129 | +32→-97 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g028 | 158 | w | Kf2 | g3f3 | 128 | -35→-163 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g053 | 43 | b | Bxb2 | f7f5 | 128 | +759→+631 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g068 | 34 | w | Qxf5+ | h8f7 | 128 | -692→-820 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 45 | b | Qe2 | c6c4 | 127 | -342→-469 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g061 | 141 | b | Kg6 | h4f2 | 127 | -239→-366 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g073 | 40 | b | f5 | a2a1 | 127 | -240→-367 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g054 | 28 | w | hxg5 | c4b3 | 126 | -61→-187 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g057 | 24 | b | Rfe8 | b8a8 | 126 | +203→+77 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g082 | 116 | w | Rb7 | c3f6 | 126 | -451→-577 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g087 | 129 | b | Kg6 | c4a5 | 125 | -339→-464 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g045 | 57 | b | Rd4 | c4c2 | 124 | +399→+275 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g060 | 56 | w | Rg1 | e1g1 | 124 | -559→-683 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g099 | 38 | b | d5 | c7d8 | 124 | -325→-449 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g080 | 32 | w | Qc3 | d4c3 | 123 | +303→+180 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g000 | 28 | w | e4 | c2c3 | 122 | -40→-162 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g001 | 33 | b | Qxc4 | c7b7 | 122 | +111→-11 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g020 | 8 | w | d5 | c4e6 | 122 | +151→+29 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g067 | 45 | b | b6 | f7f5 | 122 | +210→+88 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g019 | 17 | b | a4 | f8d8 | 121 | +95→-26 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g034 | 62 | w | N1d2 | c1c2 | 121 | -767→-888 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g036 | 34 | w | Rxd8+ | a7d7 | 121 | +54→-67 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g034 | 12 | w | f5 | f3d4 | 120 | -54→-174 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g046 | 58 | w | Nxf7 | e5c6 | 120 | +528→+408 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g090 | 54 | w | Re3 | c1e1 | 120 | -232→-352 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g082 | 44 | w | Rxe4 | c3c4 | 119 | -345→-464 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g003 | 37 | b | Qh3 | e7d5 | 118 | +415→+297 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g021 | 87 | b | Kg8 | f7f6 | 118 | -254→-372 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g034 | 60 | w | Nf1 | b3b4 | 118 | -760→-878 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g043 | 27 | b | Nf6 | e6e5 | 118 | -135→-253 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g054 | 44 | w | Bxf4 | f2f3 | 118 | -573→-691 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g087 | 81 | b | f6 | f4g6 | 118 | -303→-421 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g008 | 1 | w | Nd5 | e1g1 | 117 | -12→-129 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 7 | b | Nh6 | g8f6 | 117 | -3→-120 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g030 | 24 | w | Rfe1 | c3a2 | 117 | +70→-47 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g051 | 49 | b | c4 | e5e4 | 117 | +366→+249 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g075 | 53 | b | Bxb3 | a4b3 | 117 | -704→-821 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g081 | 17 | b | gxf5 | d4c3 | 117 | +30→-87 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g099 | 50 | b | Qxa7 | d5d8 | 117 | -417→-534 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g023 | 19 | b | Rxe2 | b8a6 | 116 | -25→-141 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g028 | 150 | w | Kh3 | f3d1 | 116 | -22→-138 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g046 | 56 | w | Ne5 | c4d2 | 116 | +515→+399 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g078 | 38 | w | Bd3 | f3h4 | 116 | -63→-179 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g082 | 42 | w | Re3 | d1a1 | 116 | -209→-325 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g096 | 48 | w | Nfd6 | e4d6 | 116 | +207→+91 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g005 | 25 | b | fxe6 | d7e6 | 115 | +70→-45 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g020 | 40 | w | Nc5 | a3b4 | 115 | +139→+24 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g061 | 165 | b | Bb1 | d6c5 | 115 | +637→+522 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g006 | 14 | w | Qe2 | c3a2 | 114 | -127→-241 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g054 | 50 | w | Kf2 | d4d5 | 114 | -718→-832 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g073 | 78 | b | Rxc3 | c8e8 | 114 | -479→-593 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g099 | 30 | b | Rd7 | e7f8 | 114 | -139→-253 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g008 | 79 | w | Kf3 | d1b1 | 113 | +278→+165 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g021 | 25 | b | axb5 | f3g2 | 113 | +147→+34 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g075 | 35 | b | cxd5 | b5c4 | 113 | -246→-359 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g008 | 93 | w | Kh5 | a2e2 | 112 | +0→-112 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g044 | 110 | w | Kc4 | d1d6 | 112 | -634→-746 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g012 | 36 | w | a4 | c7d5 | 111 | -333→-444 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g073 | 56 | b | Be6 | g4d7 | 111 | -613→-724 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g080 | 16 | w | Nxc6+ | h3h4 | 111 | +377→+266 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g089 | 17 | b | a6 | f6g4 | 111 | +92→-19 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g058 | 34 | w | Rxe6 | f4h6 | 110 | +117→+7 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g024 | 70 | w | f4 | g1g2 | 109 | -524→-633 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g065 | 23 | b | c6 | e6d5 | 109 | -75→-184 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g065 | 47 | b | b5 | d8d4 | 109 | +151→+42 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g093 | 17 | b | a6 | a8c8 | 109 | -192→-301 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g093 | 59 | b | h5 | d7b7 | 109 | -353→-462 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g085 | 19 | b | Qa8 | d8b8 | 108 | -90→-198 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g047 | 45 | b | Rh8 | a8h8 | 107 | -346→-453 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g050 | 32 | w | hxg4 | f4g6 | 107 | -94→-201 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g054 | 32 | w | a5 | d1e1 | 107 | -347→-454 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g074 | 12 | w | Nc4 | b5c6 | 107 | -37→-144 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g098 | 73 | w | g3 | f5g6 | 107 | -138→-245 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g013 | 41 | b | cxb1=Q | c2b1q | 106 | +446→+340 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g034 | 34 | w | Rfe1 | f3d4 | 106 | -228→-334 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g044 | 8 | w | Rad1 | f3h2 | 106 | +27→-79 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g060 | 46 | w | Kh2 | g1f1 | 106 | -230→-336 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g080 | 28 | w | Qc3 | d2a5 | 106 | +296→+190 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g085 | 65 | b | Rxb2 | c2c8 | 106 | -626→-732 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g094 | 40 | w | Qd1 | d2f1 | 106 | -428→-534 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g043 | 33 | b | Kg7 | e6e5 | 105 | -393→-498 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g065 | 7 | b | Be6 | h7h6 | 105 | +32→-73 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g082 | 16 | w | Qc2 | c3c4 | 105 | +213→+108 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g094 | 16 | w | hxg4 | h4e7 | 105 | +370→+265 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g000 | 90 | w | Qc2 | f2f4 | 104 | +117→+13 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g008 | 107 | w | a5 | a4a5 | 104 | +578→+474 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g030 | 100 | w | Be2 | c4e2 | 104 | +395→+291 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g040 | 38 | w | Bc2 | e2b2 | 104 | +16→-88 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g050 | 38 | w | gxh5 | f3g5 | 104 | -152→-256 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g086 | 44 | w | Na4 | f1a1 | 104 | +104→+0 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g093 | 105 | b | Re8 | g6g5 | 104 | -118→-222 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g023 | 43 | b | h6 | e6d7 | 103 | -191→-294 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g029 | 29 | b | Rhe8 | d6e4 | 103 | -163→-266 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g042 | 34 | w | Rd1 | d4c6 | 103 | -52→-155 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g057 | 28 | b | Red8 | b8a8 | 103 | +259→+156 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g008 | 37 | w | Rc1 | d4c2 | 102 | +94→-8 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g022 | 22 | w | Nxe4 | d4e5 | 102 | -88→-190 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g025 | 31 | b | Rd2 | e5e4 | 102 | +248→+146 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g027 | 63 | b | Nf4 | a8d8 | 102 | +590→+488 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g060 | 18 | w | Bxh6 | d1d2 | 102 | +150→+48 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g014 | 6 | w | d4 | e1e2 | 101 | +35→-66 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g044 | 16 | w | Bf1 | g2g3 | 101 | -125→-226 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g093 | 89 | b | Rd3 | g8h8 | 101 | -64→-165 | Y | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g017 | 67 | b | e4 | c5a3 | 100 | -455→-555 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g052 | 118 | w | Kg3 | f1f2 | 100 | +0→-100 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g083 | 27 | b | Nxd5 | c5d4 | 100 | +84→-16 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |
| g095 | 23 | b | Qa2 | h7h6 | 100 | +100→+0 |  | - | -/- | - | - | -/- | - | UNCLASSIFIED |

## Mechanism classification (the 120 largest errors, all 56 >= 300 cp included) — 2026-09-06 01:40 UK

Method: every error replayed with `champions/rc_c` at 2.5 s (the game's mean
think; the timed replay reproduced the error move in 89 of 120), at 8 s, and
at fixed depths 6/7/8; the deeper move was oracle-scored (1M nodes) so
"repaired" means the deeper move loses under 100 cp. Static and quiescence
scores were taken from the shipped evaluator. Classes are assigned by rule
from that evidence, not by eye; rows that no rule separates are UNKNOWN.

| mechanism (rule) | n | n >= 300 | cp lost (capped 1000) | games | result-flipping | from not-yet-lost positions |
|---|---|---|---|---|---|---|
| TACTICAL HORIZON — repaired by depth 7–8 or by 8 s | 41 | 22 | 16,838 | 30 | 19 | 22 |
| EVALUATION / WRONG WORLD MODEL — not repaired, static >= 200 cp above the oracle | 39 | 20 | 19,174 | 22 | 7 | 7 |
| UNKNOWN / MIXED — not repaired, static near the oracle | 17 | 5 | 5,539 | 16 | 16 | 16 |
| SEARCH INSTABILITY / TT-CONTEXT — a fixed depth-6 search avoids the move the depth-6/7 timed search played | 16 | 7 | 6,564 | 12 | 10 | 10 |
| ENDGAME — not repaired, eval near truth | 4 | 1 | 1,022 | 4 | 3 | 3 |
| CONVERSION — winning endgame, not repaired | 3 | 1 | 984 | 2 | 2 | 3 |

The 240 smaller errors (100–299 cp) were not replayed: 32,819 cp, 78 flips,
155 from not-yet-lost positions.

### What the numbers say

1. **Systematic optimism.** In the 120 positions the shipped static
   evaluation sits a median **+269 cp above the oracle** (74 of 120 at
   least +200, only 4 at least −200) and the root score inherits it (median
   +218). 77 of the 120 errors were made with a material lead of a pawn or
   more; in the optimistic errors 39 of 63 had two or more enemy pieces
   bearing on our king zone (19 of 57 in the rest). This is the
   "material-up but under attack" blindness of the earlier rated-game
   postmortem, now measured on 120 positions.
2. **But optimism mostly deepens lost positions.** The EVALUATION class
   flips only 7 results and only 7 of its 39 errors come from positions that
   were not already lost; the class that decides games is search depth:
   TACTICAL HORIZON + SEARCH INSTABILITY account for **29 of the 52
   result-flipping errors from live positions**, and 46 of the 120 errors are
   repaired by one or two more plies (min repair depth 6: 16, 7: 14, 8: 16).
3. **Depth at the error.** At 2.5 s the replay reached depth 6 in 50 cases,
   7 in 31, 8 in 21; the game budget is one to two plies short of the
   repair in the horizon class.
4. **Instability is a live signal.** The 16 SEARCH-INSTABILITY errors are
   positions where the fixed depth-6 search chooses a sound move but the
   timed search (which reached depth 6–7 with aspiration windows and a warm
   table) played the error: the root was flip-flopping. `cs_time.py` records
   that a stability-based extension was once removed "for want of
   evidence"; this is the evidence, and it is now a pre-registered
   candidate (`spec.md` §7, C4).
5. The king-safety v1 term in `cs_king.py` (off, coin-flip at Gate 1,
   uniform penalty) is **not** resurrected by this: the optimism class it
   would address is the one that flips fewest results.

### Ranking (expected large-error reduction per development minute)

| rank | mechanism | share of live flips (120) | fix | generality | speed cost | time to test |
|---|---|---|---|---|---|---|
| 1 | horizon + instability | 29 / 52 | **C4: instability-triggered time extension** (one extra iteration when the root move or score moved in the last iteration, inside the hard budget) | high (every phase) | none per node; clock cost measured | Gate 1 probe 10 min; screens 60–100 games |
| 2 | horizon | same | more identity-preserving speed | high | negative | profile-driven, hours |
| 3 | evaluation optimism under attack | 7 / 52 | selective compensation/king-pressure discount (v2 design, not v1 retune) | medium | per-node | days; needs matched negatives |
| 4 | conversion | 2 / 52 | narrow endgame repair | low | per-node | later |
