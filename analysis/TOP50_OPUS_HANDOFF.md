# AI Chessathon public top-50 data handoff

Scrape timestamp: **2026-09-04T10:27:59+00:00**

## 1. Public sources and boundary

- `GET https://aichessathon.com/leaderboard` — server-rendered complete ladder; no auth; no pagination.
- `GET https://aichessathon.com/team/{team_uuid}` — server-rendered complete public game list; no auth; no pagination.
- `GET https://aichessathon.com/game/{game_uuid}` — public game metadata, Stockfish review, and a data-URI PGN with FEN, moves, termination, and `%clk` comments.
- `GET https://aichessathon.com/api/platform/broadcast` — transient live rail JSON (`games`, `total`, `serverNow`); not a historical archive.
- The public frontend subscribes to Supabase Realtime channel `live`, event `game_finished`, then refreshes the broadcast route. This collector does not connect to Supabase or use a publishable key.
- No direct public Supabase REST table/view/RPC call was observed for leaderboard, team history, or completed-game data. Those views arrive in Next.js server-rendered HTML, so no table names are guessed.
- Required headers: none beyond an ordinary `User-Agent`. No cookies or authorization are sent. No advertised rate limit was found; the collector retries HTTP 429/5xx conservatively.

## 2. Snapshot summary

- Round state: {"ratings_after": "Round 3", "current_round": "Round 4 , in play 30 of 87 games finished", "teams": 167}
- Collection window: 2026-09-04T10:27:59+00:00 to 2026-09-04T10:29:18+00:00
- Top-50 teams: 50
- Unique completed public games: 143
- Live game pages without a final downloadable PGN at collection time: 0
- White/draw/Black: 67/13/63
- White score: 51.4%; Black score: 48.6%
- Black share of decisive games: 48.46% (95% Wilson 40.04-56.97%)
- Two-sided exact binomial p-value: 0.792583; statistically credible at 0.05: **no**
- This is a top-50-involvement sample, not a field-wide random sample. Selection by current rank can itself bias colour outcomes.

## 3. Top 50

| Rank | Bot | Team label | Rating | W-D-L | Team ID |
|---:|---|---|---:|---:|---|
| 1 | My Gambit My Legacy | Alien Gambit | 1898 | 3-0-0 | `0e8ca369-000d-44d4-a7c8-d505bf0a3a30` |
| 2 | KingofImperial | omega3 fish | 1898 | 3-0-0 | `1daad2c3-adda-4ae6-945c-e82c4015ee72` |
| 3 | SoberJackson | Sobriety | 1898 | 3-0-0 | `258a9828-7442-4bea-97cb-eed1845ad2cc` |
| 4 | Fuzzydafool | FuzzyBot | 1898 | 3-0-0 | `3241cef5-6b1c-41f2-b275-f0e50fc52ed5` |
| 5 | Patzer 1.0 | Gijs Smit | 1898 | 3-0-0 | `3f0e0e44-cdce-485f-b5b6-3691e34f9f44` |
| 6 | Blunderbuss | Blunder Buss | 1898 | 3-0-0 | `5e10f7ae-b545-4ce9-bb7a-d2ec55f9387c` |
| 7 | checkers |  | 1898 | 3-0-0 | `9e5e613a-ca80-4fd9-aa68-76f184ef7bac` |
| 8 | make_no_mistakes | Make_no_mistakes | 1898 | 3-0-0 | `ba636320-7bda-41ab-835d-3799a11613d8` |
| 9 | ms | ms | 1898 | 3-0-0 | `c3e1bc09-3d21-4279-ace0-16bb3742f5da` |
| 10 | kingsgambit | IM_master | 1898 | 3-0-0 | `ea00da98-023a-42bf-8560-495e84d8df1c` |
| 11 | The Rookie | Waterside Research | 1898 | 3-0-0 | `f1289d23-f983-4de4-8d7e-283fe2656c41` |
| 12 | Chimera | chimera | 1872 | 3-0-0 | `f7e8b14e-458d-489f-a2d5-0934c2b7d877` |
| 13 | Anchoa | Lubina | 1792 | 2-1-0 | `34fd9228-11bf-4e7a-ba8f-b452d96ad8c9` |
| 14 | Mate in One | Mate in One | 1792 | 2-1-0 | `3be637a8-e78d-4da4-8016-d13e00170433` |
| 15 | Dark Sister | Abhi's chess demon | 1792 | 2-1-0 | `7af404ee-389f-427c-9433-40ebe5902fc6` |
| 16 | bot1 | pgn | 1792 | 2-1-0 | `8b738da9-e5bb-4122-89ce-0caf6466ba80` |
| 17 | Blank Shooter | No More Ammo | 1768 | 2-1-0 | `b49586d0-218d-4491-a460-90d0d9cf321c` |
| 18 | AI Fellow | AI Fellows | 1768 | 2-1-0 | `b574c0ea-e994-4a16-9918-7fbc989c4234` |
| 19 | The Piece Sweeper | Binvengers | 1768 | 2-1-0 | `e0a34e4b-17e8-4e9d-a8bf-d145164b4bb1` |
| 20 | Sirloin v2 | Elbow Grease | 1766 | 2-1-0 | `5413ad8a-a0f1-4379-90c1-281f5c365fb7` |
| 21 | Tobias Carlsen |  | 1735 | 2-1-0 | `903d9bc9-e89a-4c0d-bd2f-61ed92481fad` |
| 22 | R3 | Team1 | 1735 | 2-1-0 | `9efa4b9d-296d-4ee0-b2e4-319dace8d318` |
| 23 | keep_kann_and_caro_on | keep kann and caro on | 1735 | 2-1-0 | `9f1cfbea-48c3-4345-8741-021152dbe77c` |
| 24 | GoodKnight | tristanize_chess | 1733 | 2-1-0 | `b1d4ae25-42a4-474a-b5bb-8e42066abda4` |
| 25 | lefischer |  | 1686 | 2-0-1 | `0900c279-5ede-4155-a850-436c28af6ea9` |
| 26 | CHINA MACHINE | Sillycats | 1686 | 2-0-1 | `17719f6d-f1dc-4078-8606-2fe63a632ea0` |
| 27 | Magnus Claudeson | AlphaBeta | 1686 | 2-0-1 | `1f234cf3-2829-4107-8a5f-2d0e15e978da` |
| 28 | Le StockFish | French Carlsen | 1686 | 2-0-1 | `2dc678cd-2e7c-4894-aeb5-ef273c023c01` |
| 29 | Analphabet | YouU-AreR | 1686 | 2-0-1 | `4c0e2889-26cd-41bb-b6e0-2471a3963ef1` |
| 30 | SaucyBeans |  | 1686 | 2-0-1 | `6fbef6df-7fc0-4b3c-ab73-240d8600df0d` |
| 31 | Daddy_Long_Legs | Johnny's Sins | 1686 | 2-0-1 | `925cb1e5-1634-46c4-b6a6-ca87b4b1a520` |
| 32 | Danya's Disciple |  | 1686 | 2-0-1 | `a4b26c08-0fa5-48ae-b15e-69a622ee81bb` |
| 33 | LSE4-E5 | jlu | 1686 | 2-0-1 | `d935d7bf-978d-4483-8995-8bac436da1d1` |
| 34 | APEX | APEX | 1686 | 2-0-1 | `dbe5877f-f1ea-410f-8fea-c759d58fe09a` |
| 35 | Fight Club |  | 1686 | 2-0-1 | `edc3ae56-ebc8-4a39-9e46-11db2179faf8` |
| 36 | lyra | slopfish | 1662 | 1-0-0 | `1d137be0-3a3e-4cda-a7ba-b22d8d178e66` |
| 37 | team |  | 1662 | 1-0-0 | `55b6ba0f-26a3-4ffa-929d-8615bdc10153` |
| 38 | Yumo |  | 1662 | 1-2-0 | `5aa0e1ef-c640-45f9-b4b4-1389de2a609b` |
| 39 | KD | Dominated Horses | 1662 | 1-2-0 | `74427349-a24e-498e-8508-a8a80d225133` |
| 40 | ChessML |  | 1654 | 1-2-0 | `e152b64e-0c6d-4341-b02b-09c09b098f8c` |
| 41 | TheROOK |  | 1638 | 2-0-1 | `13367195-d3ed-4c05-bba6-25ee8f416520` |
| 42 | Samson | Finlay Phillips | 1638 | 2-0-1 | `1a7f24af-0e65-4f49-b084-a7fd513ddb14` |
| 43 | Loki 3.0 |  | 1638 | 2-0-1 | `239fb36b-5e2f-4bb7-9a8a-5832363a0c25` |
| 44 | Minimaxnus | Stonkfish | 1638 | 2-0-1 | `385a6db2-1c05-46db-ae91-7218700f83b3` |
| 45 | stockfish.py | Asher Falcon | 1638 | 2-0-1 | `39c268bf-a894-4fb1-9d76-6b5343700832` |
| 46 | The Castle Gambit | The Castle Gambit | 1638 | 2-0-1 | `6a43144c-53b1-40d0-b620-8833a255f82f` |
| 47 | Only Blunders | OnlyBlunder | 1638 | 2-0-1 | `72e19bc4-a390-4dbd-9df8-04c55e39bf7b` |
| 48 | Capablanca | THE ROOOOOKKK!!!! | 1638 | 2-0-1 | `c7fad433-1020-4b2a-a0e3-8e86720d23de` |
| 49 | Good Morning | JSP | 1638 | 2-0-1 | `dab1e77e-ebb1-49f5-92d4-2a013e3288c4` |
| 50 | blundered my queen 💔 |  | 1638 | 2-0-1 | `ea0db44a-0888-4b54-b7ff-ec805c7befb6` |

## 4. Colour by current-rank bucket

- 1-10: 16/0/19 W/D/B across 35 unique games touching the bucket; Black score 54.29%.
- 11-25: 22/9/18 W/D/B across 49 unique games touching the bucket; Black score 45.92%.
- 26-50: 35/7/37 W/D/B across 79 unique games touching the bucket; Black score 51.27%.

### Starting side and opening-family checks

- Black to move in the supplied FEN: 122 games, W/D/B 56/11/55, Black score 49.59%.
- White to move in the supplied FEN: 21 games, W/D/B 11/2/8, Black score 42.86%.
- Sicilian Closed: 14 games, W/D/B 6/3/5, Black score 46.43%.
- Ruy Lopez, Closed: 13 games, W/D/B 6/1/6, Black score 50.0%.
- Petroff Defence: 10 games, W/D/B 4/2/4, Black score 50.0%.
- English Symmetrical: 9 games, W/D/B 4/1/4, Black score 50.0%.
- King's Indian Classical: 9 games, W/D/B 5/1/3, Black score 38.89%.
- Reti Opening: 9 games, W/D/B 8/1/0, Black score 5.56%.
- French Winawer: 6 games, W/D/B 4/0/2, Black score 33.33%.
- Nimzo-Indian Defence: 6 games, W/D/B 3/0/3, Black score 50.0%.
- Catalan Opening: 5 games, W/D/B 3/0/2, Black score 40.0%.
- French Classical: 5 games, W/D/B 2/1/2, Black score 50.0%.

## 5. Repeated exact starting FENs

- `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6` — 4 games, W/D/B 2/0/2, first moves Bb4+, Bd6, Be7, Nc6; strongest observed winner Knight you will remember vs make_no_mistakes (0-1); Outcomes vary by engine/pairing.
- `1rbqk2r/pp2ppbp/2np1np1/2p5/P3P3/2NP1NP1/1PP2PBP/R1BQ1RK1 b k - 0 8` — 3 games, W/D/B 1/1/1, first moves Be6, O-O; strongest observed winner APEX vs LSE4-E5 (1-0); Outcomes vary by engine/pairing.
- `r1bq1rk1/pp1pppbp/2n2np1/2p5/2PP4/2N1PNP1/PP3PBP/R1BQK2R b KQ - 0 7` — 3 games, W/D/B 1/1/1, first moves cxd4, d5; strongest observed winner Daddy_Long_Legs vs checkers (0-1); Outcomes vary by engine/pairing.
- `rnbq1rk1/ppp1ppbp/3p1np1/8/3PP3/2N2N2/PPP1BPPP/R1BQ1RK1 b - - 5 6` — 3 games, W/D/B 1/0/2, first moves Nbd7, Nc6, e5; strongest observed winner Tobias Carlsen vs R3 (0-1); Outcomes vary by engine/pairing.
- `rnbqk2r/pp2nppp/4p3/2ppP3/3P4/P1P5/2P2PPP/1RBQKBNR b Kkq - 2 7` — 3 games, W/D/B 2/0/1, first moves Nbc6, cxd4; strongest observed winner Mate in One vs First Bot (1-0); Outcomes vary by engine/pairing.
- `r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/PB1P1N2/1PP2PPP/RNBQR1K1 b - - 0 9` — 2 games, W/D/B 1/0/1, first moves Na5, h6; strongest observed winner lefischer vs My Gambit My Legacy (0-1); Outcomes vary by engine/pairing.
- `r1bq1rk1/2p1bppp/p2p1n2/np2p3/4P3/1BNP1N1P/PPP2PP1/R1BQR1K1 b - - 0 10` — 2 games, W/D/B 1/0/1, first moves Nxb3; strongest observed winner Le StockFish vs Fuzzydafool (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/2p1bppp/p1np1n2/1p2p3/4P3/1B3N1P/PPPP1PP1/RNBQR1K1 b kq - 0 8` — 2 games, W/D/B 1/0/1, first moves O-O; strongest observed winner Analphabet vs SaucyBeans (0-1); biggest snapshot-rating upset ChessML vs KD (1-0); Outcomes vary by engine/pairing.
- `r1bqk2r/pp1n1ppp/2n1p3/2bpP3/5P2/2NB1N2/PPP3PP/R1BQK2R b KQkq - 1 8` — 2 games, W/D/B 1/0/1, first moves a6; strongest observed winner DegreeGambit vs kingsgambit (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/ppp1bppp/2np1n2/4p3/2B1P3/2PP1N2/PP3PPP/RNBQ1RK1 b kq - 0 6` — 2 games, W/D/B 0/1/1, first moves Kf8, O-O; strongest observed winner Loki vs The Piece Sweeper (0-1); Outcomes vary by engine/pairing.
- `r1bqk2r/ppp2pp1/2np1n1p/2b1p3/4P3/1BPP1N2/PP3PPP/RNBQ1RK1 b kq - 1 7` — 2 games, W/D/B 0/0/2, first moves Bg4, O-O; strongest observed winner Muggsy_Bogues vs Chimera (0-1); Black dominates this exact FEN in the observed sample.
- `r1bqk2r/pppp1ppp/2n2n2/1Bb5/3NP3/2P5/PP3PPP/RNBQ1RK1 b kq - 2 7` — 2 games, W/D/B 2/0/0, first moves Nxd4, O-O; strongest observed winner LSE4-E5 vs Greedy Material (1-0); White dominates this exact FEN in the observed sample.
- `r1bqkb1r/1p3ppp/p1np1n2/4p3/4P3/N1N2P2/PPP3PP/R1BQKB1R b KQkq - 1 8` — 2 games, W/D/B 0/0/2, first moves Be6, Be7; strongest observed winner femboy number 1 vs bot1 (0-1); Black dominates this exact FEN in the observed sample.
- `r2qk2r/2p1bppp/p1np1n2/1p2p3/4P3/1BN2Q1P/PPPP1PP1/R1B1R1K1 b kq - 0 10` — 2 games, W/D/B 0/0/2, first moves Nd4; strongest observed winner CHINA MACHINE vs KingofImperial (0-1); Black dominates this exact FEN in the observed sample.
- `r2qkb1r/pp2pppp/2n2n2/3p4/3P1Bb1/1QPB4/PP3PPP/RN2K1NR b KQkq - 4 7` — 2 games, W/D/B 1/0/1, first moves Na5, Qb6; strongest observed winner Samson vs KingofImperial (0-1); Outcomes vary by engine/pairing.
- `rnbq1rk1/1pp2pbp/3p1np1/p2Pp3/2P1P3/2N2N1P/PP2BPP1/R1BQK2R b KQ - 0 8` — 2 games, W/D/B 1/1/0, first moves Na6, a4; strongest observed winner Patzer 1.0 vs Blunderbuss (1-0); Outcomes vary by engine/pairing.
- `rnbq1rk1/pp2bppp/4pn2/2pp4/2PP4/N4NP1/PP2PPBP/R1BQ1RK1 b - - 1 7` — 2 games, W/D/B 2/0/0, first moves Nc6; strongest observed winner keep_kann_and_caro_on vs GoodKnight (1-0); White dominates this exact FEN in the observed sample.
- `rnbq1rk1/pp2bppp/4pn2/2ppN3/2P5/3P2P1/PP2PPBP/RNBQ1RK1 b - - 0 7` — 2 games, W/D/B 2/0/0, first moves Nc6, Qc7; strongest observed winner Chimera vs kilobyte (1-0); White dominates this exact FEN in the observed sample.
- `rnbq1rk1/ppp1ppbp/3p1np1/6B1/3PP3/2N2N2/PPP1BPPP/R2QK2R b KQ - 5 6` — 2 games, W/D/B 1/0/1, first moves Bg4, d5; strongest observed winner ms vs Capablanca (1-0); Outcomes vary by engine/pairing.
- `rnbq1rk1/ppp2pbp/5np1/4p3/2P1P3/2N1BN2/PP2BPPP/R2QK2R b KQ - 1 8` — 2 games, W/D/B 1/0/1, first moves Ng4, b6; strongest observed winner Only Blunders vs HaveFaith (1-0); Outcomes vary by engine/pairing.
- `rnbq1rk1/ppp2ppp/5n2/3p4/1b1P4/2NBP3/PP2NPPP/R1BQK2R b KQ - 1 7` — 2 games, W/D/B 1/0/1, first moves Nc6, Re8; strongest observed winner Samson vs Blunderbus (1-0); Outcomes vary by engine/pairing.
- `rnbqk2r/p3nppp/1p2p3/2ppP3/P2P4/2P2N2/2P2PPP/R1BQKB1R b KQkq - 0 8` — 2 games, W/D/B 1/0/1, first moves Nd7, h6; strongest observed winner bot1 vs RMFE (1-0); Outcomes vary by engine/pairing.
- `rnbqk2r/ppp2ppp/3b4/3p4/3Pn3/2P2N1P/PP2BPP1/RNBQK2R b KQkq - 2 8` — 2 games, W/D/B 0/0/2, first moves O-O; strongest observed winner Loki 3.0 vs SoberJackson (0-1); Black dominates this exact FEN in the observed sample.

## 6. Highest-value research games

### 1. LSE4-E5-Good Morning 1-0

Game [fda76239-1392-4e4a-aa3f-148b16d6c137](https://aichessathon.com/game/fda76239-1392-4e4a-aa3f-148b16d6c137); FEN `rnbq1rk1/ppp1ppbp/3p1np1/8/3PP3/2N2N2/PPP1BPPP/R1BQ1RK1 b - - 5 6`.

**OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 230-ply low-piece ending; the winner was at least 730 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 2. Daddy_Long_Legs-Negamaximus 1-0

Game [dafa0b07-1c29-418e-ba66-654a877fb742](https://aichessathon.com/game/dafa0b07-1c29-418e-ba66-654a877fb742); FEN `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6`.

**OBSERVATION:** The exact starting fen appears in 4 collected games; it contains a 25-ply low-piece ending; it contains 1 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 3. Daddy_Long_Legs-checkers 0-1

Game [c596a081-18c4-4a0f-b8bf-e2d091612316](https://aichessathon.com/game/c596a081-18c4-4a0f-b8bf-e2d091612316); FEN `r1bq1rk1/pp1pppbp/2n2np1/2p5/2PP4/2N1PNP1/PP3PBP/R1BQK2R b KQ - 0 7`.

**OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 46-ply low-piece ending; it contains 1 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 4. Knight you will remember-make_no_mistakes 0-1

Game [75ed5090-6f22-4d2b-9d3c-40f68a0d3b5f](https://aichessathon.com/game/75ed5090-6f22-4d2b-9d3c-40f68a0d3b5f); FEN `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6`.

**OBSERVATION:** The exact starting fen appears in 4 collected games; the winner was at least 1000 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; tactical foresight or compensation handling may explain the reversal.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; label the reversal window with an offline oracle and compare depth ladders before changing evaluation.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 5. Le StockFish-Fuzzydafool 0-1

Game [2daf2008-756a-4f6e-8aae-38aa3bae94b1](https://aichessathon.com/game/2daf2008-756a-4f6e-8aae-38aa3bae94b1); FEN `r1bq1rk1/2p1bppp/p2p1n2/np2p3/4P3/1BNP1N1P/PPP2PP1/R1BQR1K1 b - - 0 10`.

**OBSERVATION:** The exact starting fen appears in 2 collected games; it contains a 89-ply low-piece ending; it contains 1 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 6. Magnus Claudeson-Le StockFish ½-½

Game [7ad68871-bc0d-44dc-9bcf-15713212b43d](https://aichessathon.com/game/7ad68871-bc0d-44dc-9bcf-15713212b43d); FEN `r1bq1rk1/pp1pppbp/2n2np1/2p5/2PP4/2N1PNP1/PP3PBP/R1BQK2R b KQ - 0 7`.

**OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 131-ply low-piece ending; the game lasts 213 plies.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 7. Bartholomew-blundered my queen 💔 0-1

Game [88ab3a9a-45ec-4b7c-881d-d6102b18daaa](https://aichessathon.com/game/88ab3a9a-45ec-4b7c-881d-d6102b18daaa); FEN `1rbqk2r/pp2ppbp/2np1np1/2p5/P3P3/2NP1NP1/1PP2PBP/R1BQ1RK1 b k - 0 8`.

**OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 21-ply low-piece ending; it contains 1 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 8. Fuzzydafool-OptiFish-V1 1-0

Game [c108926e-5b0f-47af-a471-7b2827a8b261](https://aichessathon.com/game/c108926e-5b0f-47af-a471-7b2827a8b261); FEN `rnbq1rk1/pp3ppp/4pn2/b1p5/2BP4/P1N1P2P/1P3PP1/R1BQK1NR w KQ - 1 9`.

**OBSERVATION:** It contains a 29-ply low-piece ending; it contains 4 promotion(s); the winner was at least 440 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Endgame geometry or conversion gradients may separate the engines; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Add the position and pre-ending checkpoints to the conversion/blind-win diagnostics; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 9. Good Morning-NaJ 1-0

Game [f4bf197f-829e-48bd-83f9-e872432f05d6](https://aichessathon.com/game/f4bf197f-829e-48bd-83f9-e872432f05d6); FEN `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6`.

**OBSERVATION:** The exact starting fen appears in 4 collected games; the winner was at least 600 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; tactical foresight or compensation handling may explain the reversal.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; label the reversal window with an offline oracle and compare depth ladders before changing evaluation.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 10. Obligatory En Passant-Daddy_Long_Legs 0-1

Game [054e0a15-5c97-4474-9e14-52f0bda568de](https://aichessathon.com/game/054e0a15-5c97-4474-9e14-52f0bda568de); FEN `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6`.

**OBSERVATION:** The exact starting fen appears in 4 collected games; the winner was at least 330 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; tactical foresight or compensation handling may explain the reversal.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; label the reversal window with an offline oracle and compare depth ladders before changing evaluation.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 11. SaucyBeans-Only Blunders 1-0

Game [4ab96e2e-ee32-4524-9233-69c64be6a826](https://aichessathon.com/game/4ab96e2e-ee32-4524-9233-69c64be6a826); FEN `r1bqk2r/pppp1ppp/2n2n2/1B6/1b1NP3/2P5/PP3PPP/RNBQK2R b KQkq - 0 6`.

**OBSERVATION:** It contains a 78-ply low-piece ending; it contains 1 promotion(s); the winner was at least 1000 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Endgame geometry or conversion gradients may separate the engines; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Add the position and pre-ending checkpoints to the conversion/blind-win diagnostics; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 12. Samson-KingofImperial 0-1

Game [9269bc52-0658-4de8-a981-8dbe5a663e4b](https://aichessathon.com/game/9269bc52-0658-4de8-a981-8dbe5a663e4b); FEN `r2qkb1r/pp2pppp/2n2n2/3p4/3P1Bb1/1QPB4/PP3PPP/RN2K1NR b KQkq - 4 7`.

**OBSERVATION:** The exact starting fen appears in 2 collected games; it contains a 39-ply low-piece ending; it contains 2 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 13. AI Fellow-Sirloin v2 1-0

Game [6f4a2bd0-4a3b-4718-be0b-cadf0d18d13f](https://aichessathon.com/game/6f4a2bd0-4a3b-4718-be0b-cadf0d18d13f); FEN `r1bq1rk1/2p1bppp/p2p1n2/np2p3/4P3/1BNP1N1P/PPP2PP1/R1BQR1K1 b - - 0 10`.

**OBSERVATION:** The exact starting fen appears in 2 collected games; it contains 2 promotion(s); the winner was at least 810 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 14. R3-hyperfish 1-0

Game [fdbdb960-8b53-41fb-a4a9-d3f4d865ad53](https://aichessathon.com/game/fdbdb960-8b53-41fb-a4a9-d3f4d865ad53); FEN `rnbqk2r/pp2nppp/4p3/2ppP3/3P4/P1P5/2P2PPP/1RBQKBNR b Kkq - 2 7`.

**OBSERVATION:** The exact starting fen appears in 3 collected games; it contains 1 promotion(s); the winner was at least 310 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 15. Check Republic-The Rookie 0-1

Game [00b0efea-d366-4bfe-9de0-f18eb73dbceb](https://aichessathon.com/game/00b0efea-d366-4bfe-9de0-f18eb73dbceb); FEN `r1bqkb1r/pp2pppp/2np1n2/1B6/3NP3/2N5/PPP2PPP/R1BQK2R b KQkq - 4 6`.

**OBSERVATION:** It contains a 63-ply low-piece ending; it contains 1 promotion(s); the winner was at least 1090 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Endgame geometry or conversion gradients may separate the engines; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Add the position and pre-ending checkpoints to the conversion/blind-win diagnostics; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 16. Capablanca-Only Blunders 1-0

Game [ed05c218-390e-429c-8c75-770fd601ecf0](https://aichessathon.com/game/ed05c218-390e-429c-8c75-770fd601ecf0); FEN `rnbq1rk1/pp2bppp/4pn2/2pp4/2PP4/N4NP1/PP2PPBP/R1BQ1RK1 b - - 1 7`.

**OBSERVATION:** The exact starting fen appears in 2 collected games; it contains 1 promotion(s); the winner was at least 990 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 17. Tobias Carlsen-R3 0-1

Game [69e42a25-8236-4a49-b1e1-6cf44b7e2ebd](https://aichessathon.com/game/69e42a25-8236-4a49-b1e1-6cf44b7e2ebd); FEN `rnbq1rk1/ppp1ppbp/3p1np1/8/3PP3/2N2N2/PPP1BPPP/R1BQ1RK1 b - - 5 6`.

**OBSERVATION:** The exact starting fen appears in 3 collected games; it contains 1 promotion(s); the winner was at least 400 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 18. Friday-Tobias Carlsen 0-1

Game [4b8d5dfd-ae0a-4b99-8661-f53046175147](https://aichessathon.com/game/4b8d5dfd-ae0a-4b99-8661-f53046175147); FEN `rnbqkb1r/pp1n1ppp/4p3/2ppP3/3P1P2/8/PPP1N1PP/R1BQKBNR b KQkq - 1 6`.

**OBSERVATION:** It contains 3 promotion(s); the winner was at least 720 cp behind by simple material count earlier; the game lasts 151 plies.

**HYPOTHESIS (medium/low confidence):** Passed-pawn and pawn-race handling may be decisive; tactical foresight or compensation handling may explain the reversal.

**EXPERIMENT:** Test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints; label the reversal window with an offline oracle and compare depth ladders before changing evaluation.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 19. team-Yumo 0-1

Game [df2c2dab-3e8b-437b-8f1c-2ce579043eaa](https://aichessathon.com/game/df2c2dab-3e8b-437b-8f1c-2ce579043eaa); FEN `rnbq1rk1/ppp1ppbp/3p1np1/8/3PP3/2N2N2/PPP1BPPP/R1BQ1RK1 b - - 5 6`.

**OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 24-ply low-piece ending; it contains 1 promotion(s).

**HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.

**EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.

**LIMIT:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

### 20. Analphabet-Chess 1-0

Game [e9e2fabf-1850-4620-8172-3d44cdec0520](https://aichessathon.com/game/e9e2fabf-1850-4620-8172-3d44cdec0520); FEN `rnbq1rk1/pp2bppp/2p1pn2/3p4/2PP4/5NP1/PP2PPBP/RNBQ1RK1 w - - 0 7`.

**OBSERVATION:** It contains a 32-ply low-piece ending; it contains 2 promotion(s); the winner was at least 900 cp behind by simple material count earlier.

**HYPOTHESIS (medium/low confidence):** Endgame geometry or conversion gradients may separate the engines; passed-pawn and pawn-race handling may be decisive.

**EXPERIMENT:** Add the position and pre-ending checkpoints to the conversion/blind-win diagnostics; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.

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