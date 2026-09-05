# AI Chessathon public top-50 data handoff

Scrape timestamp: **2026-09-05T00:12:23+00:00**

## 1. Public sources and boundary

- `GET https://aichessathon.com/leaderboard` — server-rendered complete ladder; no auth; no pagination.
- `GET https://aichessathon.com/team/{team_uuid}` — server-rendered complete public game list; no auth; no pagination.
- `GET https://aichessathon.com/game/{game_uuid}` — public game metadata, Stockfish review, and a data-URI PGN with FEN, moves, termination, and `%clk` comments.
- `GET https://aichessathon.com/api/platform/broadcast` — transient live rail JSON (`games`, `total`, `serverNow`); not a historical archive.
- The public frontend subscribes to Supabase Realtime channel `live`, event `game_finished`, then refreshes the broadcast route. This collector does not connect to Supabase or use a publishable key.
- No direct public Supabase REST table/view/RPC call was observed for leaderboard, team history, or completed-game data. Those views arrive in Next.js server-rendered HTML, so no table names are guessed.
- Required headers: none beyond an ordinary `User-Agent`. No cookies or authorization are sent. No advertised rate limit was found; the collector retries HTTP 429/5xx conservatively.

## 2. Snapshot summary

- Round state: {"ratings_after": "Round 15", "current_round": null, "teams": 243}
- Collection window: 2026-09-05T00:12:23+00:00 to 2026-09-05T00:13:14+00:00
- Top-50 teams: 50
- Unique completed public games: 447
- Live game pages without a final downloadable PGN at collection time: 0
- White/draw/Black: 196/70/181
- White score: 51.68%; Black score: 48.32%
- Black share of decisive games: 48.01% (95% Wilson 43.01-53.05%)
- Two-sided exact binomial p-value: 0.470934; statistically credible at 0.05: **no**
- This is a top-50-involvement sample, not a field-wide random sample. Selection by current rank can itself bias colour outcomes.

## 3. Top 50

| Rank | Bot | Team label | Rating | W-D-L | Team ID |
|---:|---|---|---:|---:|---|
| 1 | SoberJackson | Sobriety | 2164 | 12-1-2 | `258a9828-7442-4bea-97cb-eed1845ad2cc` |
| 2 | ms |  | 2132 | 11-2-2 | `c3e1bc09-3d21-4279-ace0-16bb3742f5da` |
| 3 | Mate in One | Mate in One | 2125 | 10-4-1 | `3be637a8-e78d-4da4-8016-d13e00170433` |
| 4 | Patzer 1.2 | Gijs Smit | 2080 | 11-1-3 | `3f0e0e44-cdce-485f-b5b6-3691e34f9f44` |
| 5 | checkers |  | 2026 | 9-3-3 | `9e5e613a-ca80-4fd9-aa68-76f184ef7bac` |
| 6 | Anchoa | Lubina | 2026 | 9-3-3 | `34fd9228-11bf-4e7a-ba8f-b452d96ad8c9` |
| 7 | Capablanca | THE ROOOOOKKK!!!! | 1957 | 11-0-4 | `c7fad433-1020-4b2a-a0e3-8e86720d23de` |
| 8 | Blank Shooter | No More Ammo | 1947 | 8-3-4 | `b49586d0-218d-4491-a460-90d0d9cf321c` |
| 9 | test2 | Team1 | 1943 | 8-5-2 | `9efa4b9d-296d-4ee0-b2e4-319dace8d318` |
| 10 | test_bot | pheanup | 1937 | 5-3-3 | `0a121c61-60a7-4926-a0e7-024dffa6b185` |
| 11 | AI Fellow | AI Fellows | 1932 | 8-3-4 | `b574c0ea-e994-4a16-9918-7fbc989c4234` |
| 12 | Loss Preventer | Lightning Tree | 1919 | 11-1-3 | `c90df064-e8e8-4144-b1fd-2dd6096dd21a` |
| 13 | make_no_mistakes | Make_no_mistakes | 1890 | 8-3-4 | `ba636320-7bda-41ab-835d-3799a11613d8` |
| 14 | stockfih | what even is en passant | 1890 | 4-3-0 | `b9cbed87-8a3a-437d-9333-1447f68200d1` |
| 15 | lyra | slopfish | 1886 | 5-4-4 | `1d137be0-3a3e-4cda-a7ba-b22d8d178e66` |
| 16 | Vengeance | Waterside Research | 1885 | 7-3-5 | `f1289d23-f983-4de4-8d7e-283fe2656c41` |
| 17 | stockfish.py | Asher Falcon | 1884 | 9-1-5 | `39c268bf-a894-4fb1-9d76-6b5343700832` |
| 18 | bot1 | pgn | 1873 | 7-3-5 | `8b738da9-e5bb-4122-89ce-0caf6466ba80` |
| 19 | Fuzzydafool | FuzzyBot | 1872 | 7-3-5 | `3241cef5-6b1c-41f2-b275-f0e50fc52ed5` |
| 20 | AlphaFish | Emile Andrieu | 1867 | 5-1-1 | `659a3020-8af7-4934-b753-3b7c5fd11184` |
| 21 | Dark Sister | Abhi's chess demon | 1860 | 9-2-4 | `7af404ee-389f-427c-9433-40ebe5902fc6` |
| 22 | DolphinBot | LeetBeaters | 1850 | 7-3-2 | `683eb648-7443-471d-a54e-daa6f51d042c` |
| 23 | My Gambit My Legacy | Alien Gambit | 1847 | 7-2-6 | `0e8ca369-000d-44d4-a7c8-d505bf0a3a30` |
| 24 | 50CentRaise |  | 1843 | 5-0-3 | `4857862c-3ea2-4ae9-8792-335918e2ef58` |
| 25 | 228 | Neural Gambit | 1826 | 6-3-2 | `2d7385e9-dffa-4216-aeca-dd844e18c7db` |
| 26 | TheROOK |  | 1818 | 8-4-3 | `13367195-d3ed-4c05-bba6-25ee8f416520` |
| 27 | KingofImperial | omega3 fish | 1813 | 7-2-6 | `1daad2c3-adda-4ae6-945c-e82c4015ee72` |
| 28 | keep_kann_and_caro_on | keep kann and caro on | 1810 | 7-3-5 | `9f1cfbea-48c3-4345-8741-021152dbe77c` |
| 29 | The Piece Sweeper | Binvengers | 1804 | 6-6-3 | `e0a34e4b-17e8-4e9d-a8bf-d145164b4bb1` |
| 30 | Good Morning | JSP | 1801 | 9-1-5 | `dab1e77e-ebb1-49f5-92d4-2a013e3288c4` |
| 31 | APEX | APEX | 1799 | 6-6-3 | `dbe5877f-f1ea-410f-8fea-c759d58fe09a` |
| 32 | Imperial Larper |  | 1792 | 2-0-0 | `cdc9d2a6-9470-450c-9642-31345007b69d` |
| 33 | Blunderbuss | Blunder Buss | 1790 | 7-2-6 | `5e10f7ae-b545-4ce9-bb7a-d2ec55f9387c` |
| 34 | rogo | rogo | 1786 | 3-0-1 | `638634c0-b93d-4eac-8ea3-cec357fde36f` |
| 35 | Danya's Disciple |  | 1784 | 8-2-5 | `a4b26c08-0fa5-48ae-b15e-69a622ee81bb` |
| 36 | Blundermaster | fuzz | 1782 | 7-4-4 | `0f755e93-36d5-40fe-9654-2fd874a5822e` |
| 37 | Cornelius | Cornelius | 1770 | 4-1-2 | `acecd823-279a-4bf9-8321-0ee6ed68deda` |
| 38 | zak |  | 1760 | 4-2-3 | `0cebedbb-0376-4058-b6f4-0e11ef9dbeed` |
| 39 | LSE4-E5 | jlu | 1759 | 9-0-6 | `d935d7bf-978d-4483-8995-8bac436da1d1` |
| 40 | SirBlunderiusThird | BitsEntangled | 1752 | 7-4-4 | `b227e85c-08e6-489b-ae9a-77e6e856ace0` |
| 41 | spring_week_converter | spring_week_converter | 1749 | 11-0-4 | `37b76f55-fe49-4bf9-9328-0a1eab74088c` |
| 42 | ChessML |  | 1746 | 5-7-3 | `e152b64e-0c6d-4341-b02b-09c09b098f8c` |
| 43 | ChittyChittyBangBang | ChessNotCheckers | 1739 | 10-1-4 | `074b8493-99e7-42f1-976a-e1e48fc4add5` |
| 44 | Pwn | Pwn | 1739 | 2-2-0 | `39630436-64b8-4445-aa23-e545dde7a28f` |
| 45 | Chimera | chimera | 1726 | 7-1-6 | `f7e8b14e-458d-489f-a2d5-0934c2b7d877` |
| 46 | MateX | CheckmateGPT | 1725 | 4-0-2 | `75c703fc-cfc9-40a6-b414-f6ec4cc93d83` |
| 47 | dog | mangodogo | 1725 | 10-1-4 | `1eabeb57-6e3c-46bd-902b-e3b7b5aacc73` |
| 48 | slopabot v2 | archierayteam | 1721 | 5-2-3 | `e41de29d-1869-4a7e-9cf0-0159e71e3d2c` |
| 49 | meowfish | adashima | 1717 | 2-2-0 | `e356ff20-37e4-4fc4-bfef-00cf5957a82c` |
| 50 | RMFE |  | 1716 | 9-2-4 | `8b991dda-4b49-46cc-900d-96c853154292` |

## 4. Colour by current-rank bucket

- 1-10: 51/19/49 W/D/B across 119 unique games touching the bucket; Black score 49.16%.
- 11-25: 81/27/65 W/D/B across 173 unique games touching the bucket; Black score 45.38%.
- 26-50: 120/44/99 W/D/B across 263 unique games touching the bucket; Black score 46.01%.

### Starting side and opening-family checks

- Black to move in the supplied FEN: 359 games, W/D/B 155/57/147, Black score 48.89%.
- White to move in the supplied FEN: 88 games, W/D/B 41/13/34, Black score 46.02%.
- Sicilian Closed: 52 games, W/D/B 26/9/17, Black score 41.35%.
- English Symmetrical: 36 games, W/D/B 15/10/11, Black score 44.44%.
- Reti Opening: 35 games, W/D/B 24/4/7, Black score 25.71%.
- Ruy Lopez, Closed: 29 games, W/D/B 13/4/12, Black score 48.28%.
- Petroff Defence: 22 games, W/D/B 7/2/13, Black score 63.64%.
- London System: 19 games, W/D/B 7/3/9, Black score 55.26%.
- Sicilian Sveshnikov: 17 games, W/D/B 9/1/7, Black score 44.12%.
- King's Indian Classical: 16 games, W/D/B 6/0/10, Black score 62.5%.
- Nimzo-Indian Defence: 15 games, W/D/B 8/1/6, Black score 43.33%.
- Sicilian Dragon: 15 games, W/D/B 5/3/7, Black score 56.67%.

## 5. Repeated exact starting FENs

- `rnbq1rk1/pp2bppp/4pn2/2ppN3/2P5/3P2P1/PP2PPBP/RNBQ1RK1 b - - 0 7` — 6 games, W/D/B 4/0/2, first moves Bd6, Nc6, Qc7; strongest observed winner AI Fellow vs Bonjour Oui Oui Baguette (1-0); Outcomes vary by engine/pairing.
- `1rbqk1nr/pp2ppbp/2np2p1/2p5/P3P3/2NP2P1/1PP1NPBP/R1BQK2R b KQk - 0 7` — 5 games, W/D/B 3/1/1, first moves Bd7, Nf6, h5; strongest observed winner Anchoa vs AI Fellow (1-0); Outcomes vary by engine/pairing.
- `r1bqk2r/pp1pppbp/2n2np1/2p5/2P5/2N2NPP/PP1PPPB1/R1BQK2R b KQkq - 0 6` — 5 games, W/D/B 3/1/1, first moves O-O, d5; strongest observed winner Anchoa vs bot1 (1-0); Outcomes vary by engine/pairing.
- `r1bqk2r/pp2ppbp/2np1np1/2p5/4P3/2NP1NP1/PPP2PBP/R1BQ1RK1 b kq - 3 7` — 5 games, W/D/B 3/1/1, first moves O-O, e5; strongest observed winner KingofImperial vs make_no_mistakes (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/pppp1ppp/2n2n2/1Bb5/3NP3/2P5/PP3PPP/RNBQ1RK1 b kq - 2 7` — 5 games, W/D/B 2/1/2, first moves Nxd4, O-O; strongest observed winner SirBlunderiusThird vs TheROOK (0-1); Outcomes vary by engine/pairing.
- `r2qkb1r/pp2pppp/2n2n2/3p4/3P1Bb1/1QPB4/PP3PPP/RN2K1NR b KQkq - 4 7` — 5 games, W/D/B 3/0/2, first moves Na5, Qb6, Qd7; strongest observed winner Capablanca vs DolphinBot (1-0); Outcomes vary by engine/pairing.
- `rn1qkbnr/pp3ppp/2p1p3/3pPb2/3P4/5N2/PPPN1PPP/R1BQKB1R b KQkq - 1 5` — 5 games, W/D/B 4/0/1, first moves Bb4, Nd7; strongest observed winner The Castle Gambit vs stockfish.py (0-1); biggest snapshot-rating upset Zagreus 5.0 vs spring_week_converter (1-0); White dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `rnbq1rk1/ppp2pbp/5np1/4p3/2P1P3/2N1BN2/PP2BPPP/R2QK2R b KQ - 1 8` — 5 games, W/D/B 2/0/3, first moves Nc6, a5, b6; strongest observed winner Knight you will remember vs Capablanca (0-1); biggest snapshot-rating upset test2 vs stockfish.py (0-1); Outcomes vary by engine/pairing.
- `r1bq1rk1/ppp2pbp/2np1np1/P2Pp3/4P3/2N2N2/1PP1BPPP/R1BQK2R b KQ - 0 8` — 4 games, W/D/B 1/0/3, first moves Nb4, Ne7; strongest observed winner Good Morning vs APEX (1-0); biggest snapshot-rating upset Good Morning vs Magnus Claudeson (0-1); Black dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `r1bqk1nr/pp3pbp/2np2p1/2p1p3/4P3/2NP2PP/PPP1NPB1/R1BQK2R b KQkq - 1 7` — 4 games, W/D/B 1/2/1, first moves Nf6, Nge7; strongest observed winner citytrek vs AlphaFish (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/pp1pppbp/2n2np1/2p5/Q1P5/2N2NP1/PP1PPPBP/R1B1K2R b KQkq - 5 6` — 4 games, W/D/B 2/2/0, first moves O-O, d6; strongest observed winner make_no_mistakes vs TheROOK (1-0); White dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `r1bqk2r/pp2npbp/2npp1p1/2p5/4P3/2NPB1P1/PPP1NPBP/R2QK2R w KQkq - 2 8` — 4 games, W/D/B 1/0/3, first moves O-O, d4; strongest observed winner SoberJackson vs Blank Shooter (1-0); Black dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `r1bqkb1r/1p3ppp/p1np1n2/4p3/4P3/N1N2P2/PPP3PP/R1BQKB1R b KQkq - 1 8` — 4 games, W/D/B 1/1/2, first moves Be6, Be7, d5; strongest observed winner we arent calling it that vs bot1 (0-1); Outcomes vary by engine/pairing.
- `rnbq1rk1/pp2bppp/4pn2/2pp4/2PP4/N4NP1/PP2PPBP/R1BQK2R w KQ - 0 7` — 4 games, W/D/B 3/1/0, first moves O-O, dxc5; strongest observed winner Patzer 1.2 vs Fuzzydafool (1-0); White dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `rnbq1rk1/ppp2ppp/4pn2/3p4/1bPP4/2NBPN2/PP3PPP/R1BQK2R b KQ - 1 6` — 4 games, W/D/B 3/1/0, first moves Bxc3+, Nc6, c5; strongest observed winner Loss Preventer vs limlamlom (1-0); White dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `rnbqk2r/ppp1bppp/4pn2/3p4/2P5/3P1NP1/PP2PPBP/RNBQK2R b KQkq - 0 5` — 4 games, W/D/B 3/0/1, first moves Nc6, c5, dxc4; strongest observed winner test_bot vs ms (0-1); White dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `rnbqk2r/ppp2ppp/3b4/3p4/3Pn3/2P2N1P/PP2BPP1/RNBQK2R b KQkq - 2 8` — 4 games, W/D/B 1/0/3, first moves Nc6, O-O; strongest observed winner Loki 3.0 vs SoberJackson (0-1); Black dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `r1bq1rk1/1pp2ppp/p1np1n2/2b1p3/2B1P3/2PP1N1P/PP1N1PP1/R1BQ1RK1 b - - 0 8` — 3 games, W/D/B 3/0/0, first moves Ba7, b5, d5; strongest observed winner Blank Shooter vs stockfish.py (1-0); White dominates this exact FEN in the observed sample.
- `r1bq1rk1/2p1bppp/p2p1n2/np2p3/4P3/1B1P1N1P/PPP2PP1/RNBQR1K1 w - - 1 10` — 3 games, W/D/B 2/1/0, first moves Nc3; strongest observed winner Blundermaster vs Shallow Blue 2.0 (1-0); biggest snapshot-rating upset SirBlunderiusThird vs Cornelius (1-0); White dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `r1bq1rk1/2p1bppp/p2p1n2/np2p3/4P3/1BNP1N2/PPP2PPP/R1BQR1K1 w - - 3 10` — 3 games, W/D/B 2/0/1, first moves Bd2, d4, h3; strongest observed winner Capablanca vs no1 (1-0); Outcomes vary by engine/pairing.
- `r1bq1rk1/pp1pppbp/2n2np1/2p5/2PP4/2N1PNP1/PP3PBP/R1BQK2R b KQ - 0 7` — 3 games, W/D/B 1/1/1, first moves cxd4, d5; strongest observed winner Daddy_Long_Legs vs checkers (0-1); Outcomes vary by engine/pairing.
- `r1bq1rk1/pp1pppbp/2n2np1/2p5/2PP4/2N2NP1/PP2PPBP/R1BQ1RK1 b - - 0 7` — 3 games, W/D/B 0/1/2, first moves cxd4; strongest observed winner The Castle Gambit vs Dark Sister (0-1); Black dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `r1bq1rk1/pp2ppbp/2np1np1/2p5/2P4P/2NP1NP1/PP2PPB1/R1BQK2R w KQ - 0 8` — 3 games, W/D/B 0/1/2, first moves Be3, e4, h5; strongest observed winner GoodKnight vs Loss Preventer (0-1); Black dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `r1bq1rk1/pp2ppbp/2np1np1/2p5/4P2P/2NP2P1/PPP1NPB1/R1BQK2R w KQ - 3 8` — 3 games, W/D/B 0/1/2, first moves Be3, O-O; strongest observed winner PAWXN vs Imperial Larper (0-1); Black dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `r1bq1rk1/pppp1ppp/2n2n2/1Bb5/3NP3/2P5/PP3PPP/RNBQ1RK1 w - - 3 8` — 3 games, W/D/B 1/1/1, first moves Be3, Re1; strongest observed winner Anchoa vs checkers (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/2p1bppp/p1np1n2/1p2p3/4P3/1B3N2/PPPPQPPP/RNB1R1K1 b kq - 1 8` — 3 games, W/D/B 1/1/1, first moves O-O; strongest observed winner AI Fellow vs My Gambit My Legacy (1-0); biggest snapshot-rating upset keep_kann_and_caro_on vs Blundermaster (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/pp1pppbp/2n2np1/2p5/2P5/2N1PNP1/PP1P1PBP/R1BQK2R b KQkq - 0 6` — 3 games, W/D/B 3/0/0, first moves O-O, d5, e6; strongest observed winner Blank Shooter vs The Piece Sweeper (1-0); White dominates this exact FEN in the observed sample.
- `r1bqk2r/pp2npbp/2np2p1/2p1p3/4P3/2NP2PP/PPP1NPB1/R1BQ1RK1 b kq - 3 8` — 3 games, W/D/B 3/0/0, first moves O-O; strongest observed winner Loss Preventer vs noob (1-0); White dominates this exact FEN in the observed sample.
- `r1bqk2r/pp2ppbp/2n3p1/2pn4/8/2N1PNP1/PP1P1PBP/R1BQ1RK1 b kq - 1 8` — 3 games, W/D/B 1/1/1, first moves O-O; strongest observed winner The_crow vs test2 (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/ppp2ppp/2np1n2/2b1p3/P1B1P3/2PP1N2/1P3PPP/RNBQK2R b KQkq - 0 6` — 3 games, W/D/B 1/0/2, first moves a5; strongest observed winner Blundermaster vs TheROOK (0-1); biggest snapshot-rating upset APEX vs Blunderbuss (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/pppnppbp/6p1/8/Q2PP3/2P2N2/P4PPP/R1B1KB1R b KQkq - 4 8` — 3 games, W/D/B 0/0/3, first moves O-O; strongest observed winner Chimera vs make_no_mistakes (0-1); Black dominates this exact FEN in the observed sample.
- `r1bqkb1r/pp1n1ppp/2n1p3/2ppP3/3P1P2/2NB4/PPP3PP/R1BQK1NR w KQkq - 2 7` — 3 games, W/D/B 2/0/1, first moves Nf3, dxc5; strongest observed winner checkers vs SoberJackson (0-1); Outcomes vary by engine/pairing.
- `r1bqkb1r/pp2pppp/2np1n2/8/4P3/1NN5/PPP2PPP/R1BQKB1R b KQkq - 4 6` — 3 games, W/D/B 1/1/1, first moves e5, g6; strongest observed winner Magnus Claudeson vs AlphaFish (0-1); biggest snapshot-rating upset Mesh Potato vs test2 (1-0); Outcomes vary by engine/pairing.
- `r1bqkb1r/pp3ppp/2n1pn2/2pp4/3P1B2/P1P1P3/1P1N1PPP/R2QKBNR b KQkq - 0 6` — 3 games, W/D/B 1/0/2, first moves Bd6; strongest observed winner test_bot vs Hallucinated Gambits (1-0); biggest snapshot-rating upset MateX vs The Castle Gambit (0-1); Outcomes vary by engine/pairing.
- `r2qk2r/2p1bppp/p1np1n2/1p2p3/4P3/1BN2Q1P/PPPP1PP1/R1B1R1K1 b kq - 0 10` — 3 games, W/D/B 1/0/2, first moves Nd4; strongest observed winner Fight Club vs Vengeance (0-1); Outcomes vary by engine/pairing.
- `rn1qkb1r/pp1bpp1p/3p1np1/8/3NP3/2N5/PPP1BPPP/R1BQK2R b KQkq - 3 7` — 3 games, W/D/B 1/0/2, first moves Bg7; strongest observed winner AI Fellow vs Ultron (1-0); Outcomes vary by engine/pairing.
- `rn1qkb1r/pp2nppp/2p1p3/3pP3/2PPb3/5N1P/PP1N1PP1/R1BQKB1R b KQkq - 2 7` — 3 games, W/D/B 1/0/2, first moves Nf5, Ng6; strongest observed winner Zagreus 5.0 vs Loss Preventer (0-1); Outcomes vary by engine/pairing.
- `rn1qkbnr/pp2ppp1/2p3bp/8/3P3P/5NN1/PPP2PP1/R1BQKB1R b KQkq - 1 7` — 3 games, W/D/B 1/2/0, first moves Nd7, e6; strongest observed winner AlphaFish vs dog (1-0); Outcomes vary by engine/pairing.
- `rn1qkbnr/pp2pppp/2p3b1/8/3P1B2/6N1/PPP2PPP/R2QKBNR b KQkq - 4 6` — 3 games, W/D/B 0/0/3, first moves Nf6, e6; strongest observed winner Analphabet vs Patzer 1.2 (0-1); Black dominates this exact FEN in the observed sample.
- `rn1qkbnr/pp2pppp/2p3b1/8/3P4/4B1N1/PPP2PPP/R2QKBNR b KQkq - 4 6` — 3 games, W/D/B 2/0/1, first moves Nf6, e6; strongest observed winner Dark Sister vs slopabot v2 (1-0); Outcomes vary by engine/pairing.
- `rnbq1rk1/1pp1bppp/4pn2/p2p4/2PP4/5NP1/PP2PPBP/RNBQ1RK1 w - - 0 7` — 3 games, W/D/B 1/1/1, first moves cxd5; strongest observed winner Knightmare vs spring_week_converter (0-1); Outcomes vary by engine/pairing.
- `rnbq1rk1/p1p2ppp/1p3n2/3p4/1b1P4/2NBPN2/PP3PPP/R1BQ1RK1 b - - 1 8` — 3 games, W/D/B 2/0/1, first moves Nc6, c5; strongest observed winner checkers vs Vengeance (1-0); Outcomes vary by engine/pairing.
- `rnbq1rk1/p3bppp/1pp1pn2/3p4/2PP4/1P3NP1/P3PPBP/RNBQ1RK1 w - - 0 8` — 3 games, W/D/B 0/0/3, first moves Bg5, Nbd2, Ne5; strongest observed winner Fuzzydafool vs Vengeance (0-1); Black dominates this exact FEN in the observed sample.
- `rnbq1rk1/pp2bppp/4pn2/2pp4/2PP4/N4NP1/PP2PPBP/R1BQ1RK1 b - - 1 7` — 3 games, W/D/B 3/0/0, first moves Nc6; strongest observed winner Capablanca vs Generational Comeback (1-0); White dominates this exact FEN in the observed sample.
- `rnbq1rk1/pp2ppbp/3p1np1/8/3NP3/2N1B2P/PPPQ1PP1/R3KB1R b KQ - 4 8` — 3 games, W/D/B 2/1/0, first moves Nbd7, Nc6; strongest observed winner zak vs Horrendous (1-0); White dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `rnbq1rk1/ppp2pbp/3p1np1/4p3/2PPP3/2N2N2/PP2BPPP/1RBQK2R b K - 1 7` — 3 games, W/D/B 0/0/3, first moves exd4; strongest observed winner spring_week_converter vs slopabot v2 (0-1); biggest snapshot-rating upset RMFE vs CHINA MACHINE (0-1); Black dominates this exact FEN in the observed sample.
- `rnbqk2r/p3nppp/1p2p3/2ppP3/P2P4/2P2N2/2P2PPP/R1BQKB1R b KQkq - 0 8` — 3 games, W/D/B 2/0/1, first moves Ba6, O-O, h6; strongest observed winner My Gambit My Legacy vs Blank Shooter (0-1); Outcomes vary by engine/pairing.
- `rnbqk2r/ppp1bppp/4pn2/3p4/2P5/1P3NP1/P2PPPBP/RNBQK2R b KQkq - 0 5` — 3 games, W/D/B 1/1/1, first moves c5, d4; strongest observed winner Danya's Disciple vs stockfih (0-1); biggest snapshot-rating upset Oyinda vs AlphaFish (1-0); Outcomes vary by engine/pairing.
- `rnbqk2r/ppp1bppp/4pn2/3pN3/2P5/6P1/PP1PPPBP/RNBQK2R b KQkq - 4 5` — 3 games, W/D/B 2/1/0, first moves Nbd7, d4; strongest observed winner Loss Preventer vs Rustic Alpha 3 (1-0); White dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `rnbqk2r/ppp2ppp/3b4/3p4/3Pn3/2P2N1P/PP3PP1/RNBQKB1R w KQkq - 1 8` — 3 games, W/D/B 0/0/3, first moves Bd3, Be2; strongest observed winner test_bot vs SoberJackson (0-1); Black dominates this exact FEN in the observed sample.
- `rnbqk2r/ppp3pp/4pn2/3p1p2/1b1P4/1PP2NP1/P3PPBP/RNBQK2R b KQkq - 0 6` — 3 games, W/D/B 2/1/0, first moves Bd6, Be7; strongest observed winner Dark Sister vs Blunderbuss (1-0); biggest snapshot-rating upset Shallow Blue 2.0 vs dog (1-0); White dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `rnbqkb1r/1p3ppp/p3pn2/2p5/2BP4/4PN1P/PP3PP1/RNBQ1RK1 b kq - 1 7` — 3 games, W/D/B 0/2/1, first moves Nc6, b5; strongest observed winner Yumo vs ChessML (0-1); Outcomes vary by engine/pairing.
- `rnbqkb1r/pp2pp1p/3p1np1/8/3NP3/2N5/PPP1BPPP/R1BQK2R b KQkq - 1 6` — 3 games, W/D/B 0/1/2, first moves Bg7, Nc6; strongest observed winner SirBlunderiusThird vs Blank Shooter (0-1); Black dominates this exact FEN in the observed sample; Outcomes vary by engine/pairing.
- `rnbqkbnr/pp3ppp/8/2pp4/3P4/7P/PPPN1PP1/R1BQKBNR b KQkq - 0 5` — 3 games, W/D/B 2/0/1, first moves Nc6, Nf6; strongest observed winner Anchoa vs SoberJackson (0-1); biggest snapshot-rating upset Patzer 1.2 vs ms (1-0); Outcomes vary by engine/pairing.
- `1rbqk2r/pp2ppbp/2np1np1/2p5/P3P3/2NP1NP1/1PP2PBP/R1BQ1RK1 b k - 0 8` — 2 games, W/D/B 1/0/1, first moves O-O; strongest observed winner Ticktocker vs 50CentRaise (0-1); Outcomes vary by engine/pairing.
- `1rbqk2r/pp2ppbp/2np1np1/2p5/P3P3/2NP2P1/1PP1NPBP/R1BQ1RK1 b k - 2 8` — 2 games, W/D/B 2/0/0, first moves O-O, h5; strongest observed winner Blank Shooter vs Dark Sister (1-0); White dominates this exact FEN in the observed sample.
- `1rbqkb1r/1p3ppp/p1np1n2/4p1B1/4P3/N1N5/PPP2PPP/R2QKB1R b KQk - 3 9` — 2 games, W/D/B 2/0/0, first moves Be7, Bg4; strongest observed winner 228 vs MARK-2 (1-0); White dominates this exact FEN in the observed sample.
- `r1b1k2r/pp3ppp/2nqpn2/2pp4/3P4/2P1PN2/PP1NBPPP/R2QK2R b KQkq - 1 8` — 2 games, W/D/B 1/0/1, first moves Kd7, O-O; strongest observed winner stonkfish vs Anchoa (0-1); Outcomes vary by engine/pairing.
- `r1b1kbnr/pp3ppp/4p3/3pP3/1n1P4/1P3N2/1P3PPP/RNB1KB1R w KQkq - 1 9` — 2 games, W/D/B 0/1/1, first moves Kd1, Na3; strongest observed winner stonkfish vs Chimera (0-1); Outcomes vary by engine/pairing.
- `r1b1qrk1/ppp2pbp/n2p2p1/4p1B1/2PPP1n1/2NQ1N2/PP2BPPP/R3K2R w KQ - 6 10` — 2 games, W/D/B 0/0/2, first moves d5; strongest observed winner The_crow vs ms (0-1); Black dominates this exact FEN in the observed sample.
- `r1b2rk1/pp3ppp/2nqpn2/2pp4/3P4/2P1PN2/PP1NBPPP/R2QK2R w KQ - 2 9` — 2 games, W/D/B 1/0/1, first moves O-O; strongest observed winner checkers vs lyra (1-0); Outcomes vary by engine/pairing.
- `r1bq1rk1/1p2ppbp/p1np1np1/2p5/2P4P/2NP1NP1/PP2PPB1/1RBQK2R w K - 0 9` — 2 games, W/D/B 0/0/2, first moves Be3, Qb3; strongest observed winner Bishop vs test2 (0-1); Black dominates this exact FEN in the observed sample.
- `r1bq1rk1/2p1bppp/p2p1n2/np2p3/4P3/1BNP1N1P/PPP2PP1/R1BQR1K1 b - - 0 10` — 2 games, W/D/B 1/0/1, first moves Nxb3; strongest observed winner AI Fellow vs Sirloin v2.5 (1-0); Outcomes vary by engine/pairing.
- `r1bq1rk1/pp1nbpp1/2p1pn1p/3p4/2PP4/5NP1/PPQ1PPBP/RNBR2K1 w - - 2 9` — 2 games, W/D/B 2/0/0, first moves b3, h3; strongest observed winner AI Fellow vs ILuvFortnite (1-0); White dominates this exact FEN in the observed sample.
- `r1bq1rk1/pp2npbp/2np2p1/2p1p3/4P3/P1NP2PP/1PP1NPB1/R1BQK2R w KQ - 3 9` — 2 games, W/D/B 1/1/0, first moves O-O; strongest observed winner Danya's Disciple vs we arent calling it that (1-0); Outcomes vary by engine/pairing.
- `r1bq1rk1/pp2ppbp/2np1np1/2p5/2P4P/2NP1NP1/PP2PPB1/1RBQK2R b K - 1 8` — 2 games, W/D/B 2/0/0, first moves Nh5, Qb6; strongest observed winner ms vs Thorp (1-0); White dominates this exact FEN in the observed sample.
- `r1bqk1nr/pp1p1ppp/1bn1p3/8/4P3/PNN5/1PP2PPP/R1BQKB1R b KQkq - 4 7` — 2 games, W/D/B 1/1/0, first moves Nf6, Nge7; strongest observed winner 228 vs ChittyChittyBangBang (1-0); Outcomes vary by engine/pairing.
- `r1bqk1nr/pp1p1ppp/2n1p3/2b5/4P3/PN6/1PP2PPP/RNBQKB1R b KQkq - 2 6` — 2 games, W/D/B 1/0/1, first moves Bb6; strongest observed winner test2 vs zak (1-0); Outcomes vary by engine/pairing.
- `r1bqk2r/1p2ppbp/p1np1np1/2pN4/P3P3/3PB1P1/1PP2PBP/R2QK1NR b KQkq - 1 8` — 2 games, W/D/B 2/0/0, first moves Ng4, Nxd5; strongest observed winner Anchoa vs PlayOps (1-0); White dominates this exact FEN in the observed sample.
- `r1bqk2r/1p2ppbp/p1np2p1/2pN4/P3P1n1/3PB1P1/1PP2PBP/R2QK1NR w KQkq - 2 9` — 2 games, W/D/B 2/0/0, first moves Bc1, c3; strongest observed winner lyra vs stockfish.py (1-0); White dominates this exact FEN in the observed sample.
- `r1bqk2r/2p1bppp/p1np1n2/1p2p3/4P3/1B1P1N2/PPP2PPP/RNBQR1K1 b kq - 0 8` — 2 games, W/D/B 1/0/1, first moves Na5, O-O; strongest observed winner Mate in One vs lyra (1-0); Outcomes vary by engine/pairing.
- `r1bqk2r/2p1bppp/p2p1n2/np2p3/4P3/1B1P1N2/PPP2PPP/RNBQR1K1 w kq - 1 9` — 2 games, W/D/B 2/0/0, first moves Bd2, h3; strongest observed winner Good Morning vs Traveling Salespawn (1-0); White dominates this exact FEN in the observed sample.
- `r1bqk2r/pp1n1ppp/2n1p3/2bpP3/5P2/2NB1N2/PPP3PP/R1BQK2R b KQkq - 1 8` — 2 games, W/D/B 1/1/0, first moves a6, f6; strongest observed winner Anchoa vs Dark Sister (1-0); Outcomes vary by engine/pairing.
- `r1bqk2r/pp1n1ppp/2n1p3/2bpP3/5P2/2NB4/PPP3PP/R1BQK1NR w KQkq - 0 8` — 2 games, W/D/B 2/0/0, first moves Nf3; strongest observed winner SoberJackson vs ms (1-0); White dominates this exact FEN in the observed sample.
- `r1bqk2r/pp1nbppp/2n1p3/2ppP3/3P1P2/2P2N2/PP2N1PP/R1BQKB1R b KQkq - 2 8` — 2 games, W/D/B 0/2/0, first moves O-O, Qc7; no decisive game; no dominance flag.
- `r1bqk2r/pp1pppbp/2n2np1/2p5/2P5/2NP1NP1/PP2PPBP/R1BQK2R b KQkq - 0 6` — 2 games, W/D/B 1/0/1, first moves O-O; strongest observed winner stockfish.py vs Vengeance (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/pp2npbp/2np2p1/2p1p3/4P3/P1NP2PP/1PP2PB1/R1BQK1NR w KQkq - 1 8` — 2 games, W/D/B 0/1/1, first moves Nge2; strongest observed winner My Gambit My Legacy vs test2 (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/pp2ppbp/2np1np1/2p5/4P2P/2NP2P1/PPP1NPB1/R1BQK2R b KQkq - 2 7` — 2 games, W/D/B 1/0/1, first moves Bg4, a6; strongest observed winner Prototype1 vs checkers (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/pp3ppp/2nbpn2/1Bpp4/3P1B2/2P1P2N/PP1N1PPP/R2QK2R b KQkq - 3 7` — 2 games, W/D/B 1/1/0, first moves O-O, cxd4; strongest observed winner LSE4-E5 vs KD (1-0); Outcomes vary by engine/pairing.
- `r1bqk2r/pp3ppp/2nbpn2/2pp4/3P4/P1P1P1B1/1P1N1PPP/R2QKBNR b KQkq - 2 7` — 2 games, W/D/B 1/0/1, first moves e5; strongest observed winner ms vs LSE4-E5 (1-0); Outcomes vary by engine/pairing.
- `r1bqk2r/ppp1bppp/2np1n2/4p3/P1B1P3/3P1N2/1PPN1PPP/R1BQK2R b KQkq - 0 6` — 2 games, W/D/B 1/0/1, first moves O-O; strongest observed winner Dio vs lyra (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/ppp2pp1/2np1n1p/2b1p3/4P3/1BPP1N2/PP3PPP/RNBQ1RK1 b kq - 1 7` — 2 games, W/D/B 0/0/2, first moves O-O; strongest observed winner TK-Bravo vs ChittyChittyBangBang (0-1); Black dominates this exact FEN in the observed sample.
- `r1bqk2r/ppp2ppp/2np1n2/2b1p3/2B1P3/2PP1N2/PP1N1PPP/R1BQK2R b KQkq - 1 6` — 2 games, W/D/B 1/0/1, first moves O-O, a6; strongest observed winner Mate in One vs Vengeance (1-0); Outcomes vary by engine/pairing.
- `r1bqk2r/ppp2ppp/2p2n2/4p3/4P3/P1P2N2/2PP1PPP/R1BQK2R b KQkq - 0 7` — 2 games, W/D/B 1/0/1, first moves Nxe4; strongest observed winner ms vs lyra (1-0); biggest snapshot-rating upset SoberJackson vs Fuzzydafool (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/pppp1ppp/1bn2n2/8/4P3/1NN2P2/PPP3PP/R1BQKB1R b KQkq - 4 7` — 2 games, W/D/B 1/0/1, first moves O-O, a5; strongest observed winner AI Fellow vs checkers (0-1); Outcomes vary by engine/pairing.
- `r1bqkb1r/pp1n1ppp/2p1pn2/3p4/2PP4/2N1PN1P/PP3PP1/R1BQKB1R b KQkq - 0 6` — 2 games, W/D/B 0/0/2, first moves Bd6; strongest observed winner Pawn Star 1 vs Cornelius (0-1); Black dominates this exact FEN in the observed sample.
- `r1bqkb1r/pp2pppp/2np1n2/1B6/3NP3/2N5/PPP2PPP/R1BQK2R b KQkq - 4 6` — 2 games, W/D/B 0/0/2, first moves Bd7; strongest observed winner KingofImperial vs Capablanca (0-1); Black dominates this exact FEN in the observed sample.
- `r1bqkb1r/pp3ppp/2n1pn2/2pp4/3P1B2/2P1P2P/PP1N1PP1/R2QKBNR b KQkq - 0 6` — 2 games, W/D/B 1/1/0, first moves Bd6, cxd4; strongest observed winner Blunderbuss vs SaucyBeans (1-0); Outcomes vary by engine/pairing.
- `r1bqkb1r/pp3ppp/2n1pn2/2pp4/3P1B2/2P1P3/PP1NBPPP/R2QK1NR b KQkq - 1 6` — 2 games, W/D/B 1/0/1, first moves Bd6, Qb6; strongest observed winner ms vs AI Fellow (1-0); biggest snapshot-rating upset make_no_mistakes vs Blunderbuss (0-1); Outcomes vary by engine/pairing.
- `r1bqkb1r/pp3ppp/2n1pn2/2pp4/3P4/2P1P1B1/PP1N1PPP/R2QKBNR b KQkq - 1 6` — 2 games, W/D/B 0/0/2, first moves Be7, Qb6; strongest observed winner WunderBar vs slopabot v2 (0-1); biggest snapshot-rating upset ChittyChittyBangBang vs Steinitz (0-1); Black dominates this exact FEN in the observed sample.
- `r1bqkb1r/pp3ppp/2np1n2/4p3/4P3/1NN2P2/PPP3PP/R1BQKB1R b KQkq - 1 7` — 2 games, W/D/B 2/0/0, first moves Be6, Qb6; strongest observed winner 50CentRaise vs The Piece Sweeper (1-0); White dominates this exact FEN in the observed sample.
- `r1bqkb1r/pp3ppp/2np1n2/4p3/4P3/N1N5/PPP2PPP/R1BQKB1R b KQkq - 1 7` — 2 games, W/D/B 1/0/1, first moves Be6, Be7; strongest observed winner stockfish.py vs KingofImperial (1-0); Outcomes vary by engine/pairing.
- `r1bqkb1r/pp3ppp/2np4/1N1Pp3/8/8/PPP2PPP/R1BQKB1R b KQkq - 0 8` — 2 games, W/D/B 2/0/0, first moves Ne7, a6; strongest observed winner LSE4-E5 vs Daddy_Long_Legs (1-0); White dominates this exact FEN in the observed sample.
- `r1bqkb1r/ppp2ppp/2n2n2/3p4/3NP3/5P2/PPP3PP/RNBQKB1R w KQkq - 0 6` — 2 games, W/D/B 0/0/2, first moves Bb5, Nxc6; strongest observed winner make_no_mistakes vs keep_kann_and_caro_on (0-1); biggest snapshot-rating upset make_no_mistakes vs keep_kann_and_caro_on (0-1); Black dominates this exact FEN in the observed sample.
- `r1bqkbnr/pp1p1ppp/2n1p3/8/3NP3/6P1/PPP2P1P/RNBQKB1R b KQkq - 0 5` — 2 games, W/D/B 0/0/2, first moves Qa5+, e5; strongest observed winner Mesh Potato vs zak (0-1); Black dominates this exact FEN in the observed sample.
- `r1bqkbnr/pp3ppp/2n5/2pp4/3P4/P4N2/1PPN1PPP/R1BQKB1R b KQkq - 2 6` — 2 games, W/D/B 1/1/0, first moves Nf6, cxd4; strongest observed winner bot1 vs Danya's Disciple (1-0); Outcomes vary by engine/pairing.
- `r1bqkbnr/pp3ppp/2npp3/1N6/2P1P3/8/PP3PPP/RNBQKB1R b KQkq - 0 6` — 2 games, W/D/B 0/1/1, first moves Nf6; strongest observed winner Keresight vs stockfish.py (0-1); Outcomes vary by engine/pairing.
- `r2q1rk1/2pbbppp/p1np1n2/1p2p3/P2PP3/1BP2N2/1P3PPP/RNBQR1K1 b - - 0 10` — 2 games, W/D/B 1/0/1, first moves b4, h6; strongest observed winner lyra vs AI Fellow (0-1); Outcomes vary by engine/pairing.
- `r2q1rk1/pppnppbp/3p1npB/8/3PP1b1/2N2N2/PPPQBPPP/R3K2R b KQ - 9 8` — 2 games, W/D/B 1/0/1, first moves Bxf3, c6; strongest observed winner Vengeance vs ms (0-1); Outcomes vary by engine/pairing.
- `r2qkb1r/1p3ppp/p1npbn2/4p3/4P3/N1N2P2/PPP3PP/R1BQKB1R w KQkq - 2 9` — 2 games, W/D/B 1/0/1, first moves Nc4; strongest observed winner KingofImperial vs SoberJackson (0-1); Outcomes vary by engine/pairing.
- `r2qkb1r/pp1n1ppp/2p1pn2/5b2/P1NP4/2N1P3/1P3PPP/R1BQKB1R b KQkq - 0 8` — 2 games, W/D/B 1/0/1, first moves Bb4, Qc7; strongest observed winner Le StockFish vs Capablanca (0-1); Outcomes vary by engine/pairing.
- `rn1q1rk1/pbp1bppp/1p1ppn2/8/2PP4/PP3NP1/4PPBP/RNBQ1RK1 b - - 0 8` — 2 games, W/D/B 0/0/2, first moves c5; strongest observed winner DolphinBot vs AI Fellow (0-1); Black dominates this exact FEN in the observed sample.
- `rn1qk2r/pbppbppp/1p2pn2/8/2PP4/5NP1/PP2PPBP/RNBQ1RK1 b kq - 4 6` — 2 games, W/D/B 0/0/2, first moves O-O, c6; strongest observed winner Vengeance vs bot1 (0-1); biggest snapshot-rating upset Vengeance vs bot1 (0-1); Black dominates this exact FEN in the observed sample.
- `rn1qkb1r/1p3ppp/p2pbn2/4p3/4P3/1NN1B3/PPPQ1PPP/R3KB1R b KQkq - 3 8` — 2 games, W/D/B 1/1/0, first moves Be7, Nc6; strongest observed winner SoberJackson vs Patzer 1.2 (1-0); Outcomes vary by engine/pairing.
- `rn1qkb1r/pp3ppp/2p1p3/3n1b2/P1BP1B2/2N1PN2/1P3PPP/R2QK2R b KQkq - 0 8` — 2 games, W/D/B 2/0/0, first moves Nxf4; strongest observed winner keep_kann_and_caro_on vs Boon (1-0); White dominates this exact FEN in the observed sample.
- `rn2kb1r/pp1q1ppp/5n2/2pp4/3P4/7P/PPPN1PP1/R1BQK1NR w KQkq - 0 8` — 2 games, W/D/B 2/0/0, first moves Ngf3, Qe2+; strongest observed winner Patzer 1.2 vs Keresight (1-0); White dominates this exact FEN in the observed sample.
- `rnbq1rk1/ppp1bppp/4pn2/3p4/2PP4/N4NP1/PP2PPBP/R1BQK2R b KQ - 0 6` — 2 games, W/D/B 1/0/1, first moves Bxa3, c5; strongest observed winner Patzer 1.2 vs Anchoa (0-1); biggest snapshot-rating upset Patzer 1.2 vs Anchoa (0-1); Outcomes vary by engine/pairing.
- `rnbq1rk1/ppp1bppp/4pn2/3pN3/2P5/6P1/PP1PPPBP/RNBQ1RK1 b - - 6 6` — 2 games, W/D/B 1/0/1, first moves Nbd7, c5; strongest observed winner Alpha-01 vs Blundermaster (0-1); Outcomes vary by engine/pairing.
- `rnbq1rk1/ppp1ppbp/3p1np1/6B1/3PP3/2N2N2/PPP1BPPP/R2QK2R b KQ - 5 6` — 2 games, W/D/B 2/0/0, first moves Bg4, h6; strongest observed winner ms vs Capablanca (1-0); White dominates this exact FEN in the observed sample.
- `rnbq1rk1/ppp1ppbp/3p1np1/8/3PP3/2N2N2/PPP1BPPP/R1BQ1RK1 b - - 5 6` — 2 games, W/D/B 1/0/1, first moves Nc6, e5; strongest observed winner Tobias Carlsen vs test2 (0-1); biggest snapshot-rating upset LSE4-E5 vs Good Morning (1-0); Outcomes vary by engine/pairing.
- `rnbq1rk1/ppp2ppp/4pn2/3p4/1bPP4/2NBP3/PP1B1PPP/R2QK1NR b KQ - 1 6` — 2 games, W/D/B 0/0/2, first moves c5, dxc4; strongest observed winner My Gambit My Legacy vs Patzer 1.2 (0-1); Black dominates this exact FEN in the observed sample.
- `rnbqk1nr/pp3ppp/8/2bp4/8/1N6/PPP2PPP/R1BQKBNR b KQkq - 1 6` — 2 games, W/D/B 1/1/0, first moves Bb6; strongest observed winner SoberJackson vs SirBlunderiusThird (1-0); Outcomes vary by engine/pairing.
- `rnbqk2r/1p2bppp/p2ppn2/8/4PPP1/1NN5/PPP4P/R1BQKB1R b KQkq - 0 8` — 2 games, W/D/B 2/0/0, first moves d5; strongest observed winner APEX vs Pawnzi Scheme (1-0); White dominates this exact FEN in the observed sample.
- `rnbqk2r/pp2nppp/4p3/2ppP3/3P4/P1P5/2P2PPP/1RBQKBNR b Kkq - 2 7` — 2 games, W/D/B 2/0/0, first moves Nbc6, cxd4; strongest observed winner Mate in One vs e=π=2 (1-0); White dominates this exact FEN in the observed sample.
- `rnbqk2r/pp2ppbp/3p1np1/8/3NP3/2N1B2P/PPP2PP1/R2QKB1R b KQkq - 2 7` — 2 games, W/D/B 1/0/1, first moves O-O; strongest observed winner Stinkfish vs The Piece Sweeper (0-1); Outcomes vary by engine/pairing.
- `rnbqk2r/pp2ppbp/3p1np1/8/3NP3/2N1B3/PPP1BPPP/R2QK2R b KQkq - 3 7` — 2 games, W/D/B 0/1/1, first moves O-O; strongest observed winner SoberJackson vs keep_kann_and_caro_on (0-1); biggest snapshot-rating upset SoberJackson vs keep_kann_and_caro_on (0-1); Outcomes vary by engine/pairing.
- `rnbqk2r/ppp1bppp/4pn2/8/2Pp4/5NP1/PPQPPPBP/RNB1K2R w KQkq - 0 6` — 2 games, W/D/B 1/0/1, first moves O-O, b4; strongest observed winner Chimera vs Cornelius (0-1); Outcomes vary by engine/pairing.
- `rnbqk2r/ppp1ppbp/6p1/8/3PP3/2P1B3/P4PPP/R2QKBNR b KQkq - 2 7` — 2 games, W/D/B 0/1/1, first moves c5; strongest observed winner Blunderbuss vs 50CentRaise (0-1); Outcomes vary by engine/pairing.
- `rnbqk2r/ppp1ppbp/6p1/8/3PP3/2P2N2/P4PPP/R1BQKB1R b KQkq - 2 7` — 2 games, W/D/B 1/0/1, first moves O-O, c5; strongest observed winner Danya's Disciple vs make_no_mistakes (0-1); Outcomes vary by engine/pairing.
- `rnbqk2r/ppp2ppp/3b4/3p4/3Pn3/2PB1N1P/PP3PP1/RNBQK2R b KQkq - 2 8` — 2 games, W/D/B 1/1/0, first moves O-O; strongest observed winner spring_week_converter vs Brrrrrr (1-0); Outcomes vary by engine/pairing.
- `rnbqk2r/ppp2ppp/8/3p4/1b1Pn3/2P2N1P/PP3PP1/RNBQKB1R b KQkq - 0 7` — 2 games, W/D/B 2/0/0, first moves Bd6; strongest observed winner checkers vs make_no_mistakes (1-0); White dominates this exact FEN in the observed sample.
- `rnbqk2r/ppp3pp/3bpn2/3p1p2/2PP4/5NP1/PP2PPBP/RNBQ1RK1 b kq - 0 6` — 2 games, W/D/B 1/1/0, first moves O-O, c6; strongest observed winner test_bot vs 228 (1-0); Outcomes vary by engine/pairing.
- `rnbqkb1r/1p3ppp/p3pn2/2p5/2BP4/2N1PN2/PP3PPP/R1BQ1RK1 b kq - 1 7` — 2 games, W/D/B 1/0/1, first moves b5; strongest observed winner The Piece Sweeper vs Sirloin v2.5 (1-0); biggest snapshot-rating upset spring_week_converter vs stonkfish (0-1); Outcomes vary by engine/pairing.
- `rnbqkb1r/pp1n1ppp/4p3/3pP3/3Q1P2/2N1B3/PPP3PP/R3KBNR b KQkq - 0 7` — 2 games, W/D/B 1/1/0, first moves Nc6; strongest observed winner APEX vs SaucyBeans (1-0); Outcomes vary by engine/pairing.
- `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/4BN2/PPP2PPP/RN1QKB1R b KQkq - 1 6` — 2 games, W/D/B 0/0/2, first moves Bd6, Nc6; strongest observed winner Gayukh vs ChittyChittyBangBang (0-1); Black dominates this exact FEN in the observed sample.
- `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6` — 2 games, W/D/B 1/0/1, first moves Be7, Nc6; strongest observed winner Knight you will remember vs make_no_mistakes (0-1); Outcomes vary by engine/pairing.
- `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/P4N2/1PP2PPP/RNBQKB1R b KQkq - 0 6` — 2 games, W/D/B 0/1/1, first moves Bd6, Nc6; strongest observed winner 50CentRaise vs Blank Shooter (0-1); Outcomes vary by engine/pairing.
- `rnbqkb1r/ppp3pp/4pn2/3p1p2/3P3P/5NP1/PPP1PPB1/RNBQK2R b KQkq - 0 5` — 2 games, W/D/B 0/1/1, first moves Bd6; strongest observed winner Anchoa vs test_bot (0-1); biggest snapshot-rating upset Anchoa vs test_bot (0-1); Outcomes vary by engine/pairing.

## 6. Highest-value research games

### 1. Zagreus 5.0-spring_week_converter 1-0

Game [56990337-e687-404f-a7dd-6817679445c5](https://aichessathon.com/game/56990337-e687-404f-a7dd-6817679445c5); FEN `rn1qkbnr/pp3ppp/2p1p3/3pPb2/3P4/5N2/PPPN1PPP/R1BQKB1R b KQkq - 1 5`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 90-ply low-piece ending; it contains 2 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 2. Capablanca-DolphinBot 1-0

Game [6eae3d36-c44e-4af1-b5ad-ad834a670e95](https://aichessathon.com/game/6eae3d36-c44e-4af1-b5ad-ad834a670e95); FEN `r2qkb1r/pp2pppp/2n2n2/3p4/3P1Bb1/1QPB4/PP3PPP/RN2K1NR b KQkq - 4 7`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 42-ply low-piece ending; it contains 2 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 3. Mate in One-Chimera 1-0

Game [10435e74-bbee-4fe5-a597-e3c50175e30a](https://aichessathon.com/game/10435e74-bbee-4fe5-a597-e3c50175e30a); FEN `rnbqk2r/ppp1bppp/4pn2/3p4/2P5/3P1NP1/PP2PPBP/RNBQK2R b KQkq - 0 5`.

**OBSERVATION:** The exact starting fen appears in 4 collected games; it contains a 119-ply low-piece ending; it contains 3 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 4. spring_week_converter-SaucyBeans 1-0

Game [1f575fc3-1f9a-4404-ab12-85569c6761cf](https://aichessathon.com/game/1f575fc3-1f9a-4404-ab12-85569c6761cf); FEN `r1bqk1nr/pp3pbp/2np2p1/2p1p3/4P3/2NP2PP/PPP1NPB1/R1BQK2R b KQkq - 1 7`.

**OBSERVATION:** The exact starting fen appears in 4 collected games; it contains a 60-ply low-piece ending; it contains 4 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 5. Anchoa-AI Fellow 1-0

Game [28162785-c377-4666-9d5c-9563ec2eb0c5](https://aichessathon.com/game/28162785-c377-4666-9d5c-9563ec2eb0c5); FEN `1rbqk1nr/pp2ppbp/2np2p1/2p5/P3P3/2NP2P1/1PP1NPBP/R1BQK2R b KQk - 0 7`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 226-ply low-piece ending; the winner was at least 500 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 6. test_bot-ms 0-1

Game [d2fbe9ce-8aa1-4510-b46b-ed6188cee5ee](https://aichessathon.com/game/d2fbe9ce-8aa1-4510-b46b-ed6188cee5ee); FEN `rnbqk2r/ppp1bppp/4pn2/3p4/2P5/3P1NP1/PP2PPBP/RNBQK2R b KQkq - 0 5`.

**OBSERVATION:** The exact starting fen appears in 4 collected games; it contains a 61-ply low-piece ending; it contains 3 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 7. Chimera-SaucyBeans 1-0

Game [b6e7ede4-2845-4c95-a71d-e5086f376396](https://aichessathon.com/game/b6e7ede4-2845-4c95-a71d-e5086f376396); FEN `rnbq1rk1/pp2bppp/4pn2/2ppN3/2P5/3P2P1/PP2PPBP/RNBQ1RK1 b - - 0 7`.

**OBSERVATION:** The exact starting fen appears in 6 collected games; it contains 2 promotion(s); the winner was at least 300 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 8. DolphinBot-Blundermaster 1-0

Game [2013074a-a8b5-4a93-9396-5e3f48d0af44](https://aichessathon.com/game/2013074a-a8b5-4a93-9396-5e3f48d0af44); FEN `r1bqk2r/pp1pppbp/2n2np1/2p5/2P5/2N2NPP/PP1PPPB1/R1BQK2R b KQkq - 0 6`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 45-ply low-piece ending; it contains 1 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 9. SirBlunderiusThird-TheROOK 0-1

Game [2edfb285-18a8-4990-8f1b-ce49bcad013e](https://aichessathon.com/game/2edfb285-18a8-4990-8f1b-ce49bcad013e); FEN `r1bqk2r/pppp1ppp/2n2n2/1Bb5/3NP3/2P5/PP3PPP/RNBQ1RK1 b kq - 2 7`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 22-ply low-piece ending; it contains 2 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 10. Zagreus 5.0-dog 0-1

Game [ff2cc3fe-12dc-44a9-b762-4a1cc82157a8](https://aichessathon.com/game/ff2cc3fe-12dc-44a9-b762-4a1cc82157a8); FEN `rnbq1rk1/ppp2pbp/5np1/4p3/2P1P3/2N1BN2/PP2BPPP/R2QK2R b KQ - 1 8`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 55-ply low-piece ending; it contains 2 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 11. MateX-murmp-bot 1-0

Game [028595d8-0ad5-43d2-841f-04cb8839e17c](https://aichessathon.com/game/028595d8-0ad5-43d2-841f-04cb8839e17c); FEN `rnbq1rk1/pp2bppp/4pn2/2ppN3/2P5/3P2P1/PP2PPBP/RNBQ1RK1 b - - 0 7`.

**OBSERVATION:** The exact starting fen appears in 6 collected games; it contains a 62-ply low-piece ending; the winner was at least 370 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 12. KingofImperial-make_no_mistakes 0-1

Game [e9818481-77a0-49b7-b2d7-6af617c32c5e](https://aichessathon.com/game/e9818481-77a0-49b7-b2d7-6af617c32c5e); FEN `r1bqk2r/pp2ppbp/2np1np1/2p5/4P3/2NP1NP1/PPP2PBP/R1BQ1RK1 b kq - 3 7`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 46-ply low-piece ending; it contains 1 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 13. Samson-KingofImperial 0-1

Game [9269bc52-0658-4de8-a981-8dbe5a663e4b](https://aichessathon.com/game/9269bc52-0658-4de8-a981-8dbe5a663e4b); FEN `r2qkb1r/pp2pppp/2n2n2/3p4/3P1Bb1/1QPB4/PP3PPP/RN2K1NR b KQkq - 4 7`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 39-ply low-piece ending; it contains 2 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 14. test2-stockfish.py 0-1

Game [5852b2e9-e611-4364-9930-fef0ca4e60df](https://aichessathon.com/game/5852b2e9-e611-4364-9930-fef0ca4e60df); FEN `rnbq1rk1/ppp2pbp/5np1/4p3/2P1P3/2N1BN2/PP2BPPP/R2QK2R b KQ - 1 8`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 52-ply low-piece ending; the winner was at least 700 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 15. Anchoa-bot1 1-0

Game [b4d7c9bd-f1ad-450b-8166-dccbd6971b51](https://aichessathon.com/game/b4d7c9bd-f1ad-450b-8166-dccbd6971b51); FEN `r1bqk2r/pp1pppbp/2n2np1/2p5/2P5/2N2NPP/PP1PPPB1/R1BQK2R b KQkq - 0 6`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 39-ply low-piece ending; it contains 2 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 16. Patzer 1.2-Fuzzydafool 1-0

Game [ca646a07-3791-4e83-8220-1c6f11b4467d](https://aichessathon.com/game/ca646a07-3791-4e83-8220-1c6f11b4467d); FEN `rnbq1rk1/pp2bppp/4pn2/2pp4/2PP4/N4NP1/PP2PPBP/R1BQK2R w KQ - 0 7`.

**OBSERVATION:** The exact starting fen appears in 4 collected games; it contains a 63-ply low-piece ending; it contains 2 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 17. TheROOK-Mesh Potato 1-0

Game [e6cba770-cb67-4f9f-9806-4f1703914e52](https://aichessathon.com/game/e6cba770-cb67-4f9f-9806-4f1703914e52); FEN `r2qk2r/2p1bppp/p1np1n2/1p2p3/4P3/1BN2Q1P/PPPP1PP1/R1B1R1K1 b kq - 0 10`.

**OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 52-ply low-piece ending; it contains 4 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 18. AI Fellow-Bonjour Oui Oui Baguette 1-0

Game [3c50f46d-14cf-46a7-8523-9955bcdb16db](https://aichessathon.com/game/3c50f46d-14cf-46a7-8523-9955bcdb16db); FEN `rnbq1rk1/pp2bppp/4pn2/2ppN3/2P5/3P2P1/PP2PPBP/RNBQ1RK1 b - - 0 7`.

**OBSERVATION:** The exact starting fen appears in 6 collected games; the winner was at least 600 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; tactical foresight or compensation handling may explain the reversal.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; label the reversal window with an offline oracle and compare depth ladders before changing evaluation.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 19. bitterbot-spring_week_converter 1-0

Game [ace00c45-8355-4287-9d6e-c7b9babd8a5a](https://aichessathon.com/game/ace00c45-8355-4287-9d6e-c7b9babd8a5a); FEN `rnbq1rk1/ppp2pbp/5np1/4p3/2P1P3/2N1BN2/PP2BPPP/R2QK2R b KQ - 1 8`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains 1 promotion(s); the winner was at least 520 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 20. My Gambit My Legacy-Vengeance ½-½

Game [bbd702b1-4fb0-4415-a256-21a40fb01dd1](https://aichessathon.com/game/bbd702b1-4fb0-4415-a256-21a40fb01dd1); FEN `1rbqk1nr/pp2ppbp/2np2p1/2p5/P3P3/2NP2P1/1PP1NPBP/R1BQK2R b KQk - 0 7`.

**OBSERVATION:** The exact starting fen appears in 5 collected games; it contains a 76-ply low-piece ending; it contains 1 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 7. Recurring behaviours and ClaudeShark hypotheses

These are hypotheses generated from public move records, not claims about competitors' implementations:

- **Endgame conversion (medium):** long low-piece tails and promotion races are candidates for king/pawn geometry tests. Compare V2.1 king-pawn and passed-pawn variants on extracted checkpoints.
- **Compensation/tactical reversals (low):** games where the winner was materially behind deserve oracle-labelled depth ladders before any evaluation change.
- **Repetition/time management (low):** long games under low clock should be replayed with repetition and allocator instrumentation; do not infer causality from final clocks alone.
- **Quiet move quality (low):** use the public Stockfish review only to locate candidate first errors, then reproduce them with the repository's fixed-depth tools.

What ClaudeShark 'lacks' is not proven by this dataset. The defensible next step is to turn the shortlisted positions into diagnostic fixtures and test one mechanism at a time under the existing gates.

## 8. Caveats

- The ladder changed during the live event; all ranks/ratings are snapshot values, not historical pre-game ratings.
- The live site cannot be scraped atomically: the top-50 set is fixed at the first timestamp, while team/game pages are fetched during the recorded collection window.
- Completed-game pages expose no game timestamp. `timestamp` is therefore `null`; the scrape timestamp and rated round are retained.
- Team pages expose completed games only. A game still in progress may appear in the live broadcast route but is intentionally excluded until its public game page has a PGN.
- This scrape recorded 0 such live page(s) in `analysis/top50_collection_log.json`; rerunning later can collect them after finalisation.
- Rank-bucket samples overlap when a game has top-50 participants from different buckets; each game is counted once within each touched bucket.
- The exact binomial test conditions on decisive games and assumes independent fair-colour outcomes. Reused curated FENs and rank-selection can violate that assumption, so the FEN breakdown is essential.
- Public Stockfish labels are observational aids, not a licence to copy an engine or infer another bot's architecture.

## 9. Reproduction

```powershell
uv run python -m tools.aichessathon_public all --top 50 --output-dir analysis
uv run python -m tools.aichessathon_public analyse --output-dir analysis --shortlist 20
```

Raw artifacts: `analysis/top50_leaderboard.json`, `analysis/top50_leaderboard.csv`, `analysis/top50_games.jsonl`, and `analysis/top50_pgn/`.