# Top public games for ClaudeShark research

Snapshot: 2026-09-04T10:27:59+00:00. Ranking is a diagnostic prioritisation, not Elo evidence.

## 1. LSE4-E5 vs Good Morning (1-0)

- Game: [fda76239-1392-4e4a-aa3f-148b16d6c137](https://aichessathon.com/game/fda76239-1392-4e4a-aa3f-148b16d6c137)
- Round/opening: Rated 2 · Pirc Defence
- Starting FEN: `rnbq1rk1/ppp1ppbp/3p1np1/8/3PP3/2N2N2/PPP1BPPP/R1BQ1RK1 b - - 5 6`
- Research-priority score: 31.476 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 230-ply low-piece ending; the winner was at least 730 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 2. Daddy_Long_Legs vs Negamaximus (1-0)

- Game: [dafa0b07-1c29-418e-ba66-654a877fb742](https://aichessathon.com/game/dafa0b07-1c29-418e-ba66-654a877fb742)
- Round/opening: Rated 1 · Petroff Defence
- Starting FEN: `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6`
- Research-priority score: 30.646 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 4 collected games; it contains a 25-ply low-piece ending; it contains 1 promotion(s).
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 3. Daddy_Long_Legs vs checkers (0-1)

- Game: [c596a081-18c4-4a0f-b8bf-e2d091612316](https://aichessathon.com/game/c596a081-18c4-4a0f-b8bf-e2d091612316)
- Round/opening: Rated 3 · English Symmetrical
- Starting FEN: `r1bq1rk1/pp1pppbp/2n2np1/2p5/2PP4/2N1PNP1/PP3PBP/R1BQK2R b KQ - 0 7`
- Research-priority score: 26.552 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 46-ply low-piece ending; it contains 1 promotion(s).
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 4. Knight you will remember vs make_no_mistakes (0-1)

- Game: [75ed5090-6f22-4d2b-9d3c-40f68a0d3b5f](https://aichessathon.com/game/75ed5090-6f22-4d2b-9d3c-40f68a0d3b5f)
- Round/opening: Rated 2 · Petroff Defence
- Starting FEN: `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6`
- Research-priority score: 25.73 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 4 collected games; the winner was at least 1000 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; tactical foresight or compensation handling may explain the reversal.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; label the reversal window with an offline oracle and compare depth ladders before changing evaluation.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 5. Le StockFish vs Fuzzydafool (0-1)

- Game: [2daf2008-756a-4f6e-8aae-38aa3bae94b1](https://aichessathon.com/game/2daf2008-756a-4f6e-8aae-38aa3bae94b1)
- Round/opening: Rated 3 · Ruy Lopez, Closed
- Starting FEN: `r1bq1rk1/2p1bppp/p2p1n2/np2p3/4P3/1BNP1N1P/PPP2PP1/R1BQR1K1 b - - 0 10`
- Research-priority score: 25.32 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 2 collected games; it contains a 89-ply low-piece ending; it contains 1 promotion(s).
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 6. Magnus Claudeson vs Le StockFish (½-½)

- Game: [7ad68871-bc0d-44dc-9bcf-15713212b43d](https://aichessathon.com/game/7ad68871-bc0d-44dc-9bcf-15713212b43d)
- Round/opening: Rated 4 · English Symmetrical
- Starting FEN: `r1bq1rk1/pp1pppbp/2n2np1/2p5/2PP4/2N1PNP1/PP3PBP/R1BQK2R b KQ - 0 7`
- Research-priority score: 24.881 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 131-ply low-piece ending; the game lasts 213 plies.
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 7. Bartholomew vs blundered my queen 💔 (0-1)

- Game: [88ab3a9a-45ec-4b7c-881d-d6102b18daaa](https://aichessathon.com/game/88ab3a9a-45ec-4b7c-881d-d6102b18daaa)
- Round/opening: Rated 3 · Sicilian Closed
- Starting FEN: `1rbqk2r/pp2ppbp/2np1np1/2p5/P3P3/2NP1NP1/1PP2PBP/R1BQ1RK1 b k - 0 8`
- Research-priority score: 23.452 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 21-ply low-piece ending; it contains 1 promotion(s).
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 8. Fuzzydafool vs OptiFish-V1 (1-0)

- Game: [c108926e-5b0f-47af-a471-7b2827a8b261](https://aichessathon.com/game/c108926e-5b0f-47af-a471-7b2827a8b261)
- Round/opening: Rated 2 · Nimzo-Indian Defence
- Starting FEN: `rnbq1rk1/pp3ppp/4pn2/b1p5/2BP4/P1N1P2P/1P3PP1/R1BQK1NR w KQ - 1 9`
- Research-priority score: 22.871 (within this snapshot only)
- **OBSERVATION:** It contains a 29-ply low-piece ending; it contains 4 promotion(s); the winner was at least 440 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Endgame geometry or conversion gradients may separate the engines; passed-pawn and pawn-race handling may be decisive.
- **EXPERIMENT:** Add the position and pre-ending checkpoints to the conversion/blind-win diagnostics; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 9. Good Morning vs NaJ (1-0)

- Game: [f4bf197f-829e-48bd-83f9-e872432f05d6](https://aichessathon.com/game/f4bf197f-829e-48bd-83f9-e872432f05d6)
- Round/opening: Rated 1 · Petroff Defence
- Starting FEN: `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6`
- Research-priority score: 22.468 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 4 collected games; the winner was at least 600 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; tactical foresight or compensation handling may explain the reversal.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; label the reversal window with an offline oracle and compare depth ladders before changing evaluation.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 10. Obligatory En Passant vs Daddy_Long_Legs (0-1)

- Game: [054e0a15-5c97-4474-9e14-52f0bda568de](https://aichessathon.com/game/054e0a15-5c97-4474-9e14-52f0bda568de)
- Round/opening: Rated 2 · Petroff Defence
- Starting FEN: `rnbqkb1r/ppp2ppp/8/3p4/3Pn3/5N2/PPP1BPPP/RNBQK2R b KQkq - 1 6`
- Research-priority score: 22.329 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 4 collected games; the winner was at least 330 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; tactical foresight or compensation handling may explain the reversal.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; label the reversal window with an offline oracle and compare depth ladders before changing evaluation.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 11. SaucyBeans vs Only Blunders (1-0)

- Game: [4ab96e2e-ee32-4524-9233-69c64be6a826](https://aichessathon.com/game/4ab96e2e-ee32-4524-9233-69c64be6a826)
- Round/opening: Rated 2 · Scotch Game
- Starting FEN: `r1bqk2r/pppp1ppp/2n2n2/1B6/1b1NP3/2P5/PP3PPP/RNBQK2R b KQkq - 0 6`
- Research-priority score: 21.811 (within this snapshot only)
- **OBSERVATION:** It contains a 78-ply low-piece ending; it contains 1 promotion(s); the winner was at least 1000 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Endgame geometry or conversion gradients may separate the engines; passed-pawn and pawn-race handling may be decisive.
- **EXPERIMENT:** Add the position and pre-ending checkpoints to the conversion/blind-win diagnostics; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 12. Samson vs KingofImperial (0-1)

- Game: [9269bc52-0658-4de8-a981-8dbe5a663e4b](https://aichessathon.com/game/9269bc52-0658-4de8-a981-8dbe5a663e4b)
- Round/opening: Rated 2 · Caro-Kann Exchange
- Starting FEN: `r2qkb1r/pp2pppp/2n2n2/3p4/3P1Bb1/1QPB4/PP3PPP/RN2K1NR b KQkq - 4 7`
- Research-priority score: 21.8 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 2 collected games; it contains a 39-ply low-piece ending; it contains 2 promotion(s).
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 13. AI Fellow vs Sirloin v2 (1-0)

- Game: [6f4a2bd0-4a3b-4718-be0b-cadf0d18d13f](https://aichessathon.com/game/6f4a2bd0-4a3b-4718-be0b-cadf0d18d13f)
- Round/opening: Rated 4 · Ruy Lopez, Closed
- Starting FEN: `r1bq1rk1/2p1bppp/p2p1n2/np2p3/4P3/1BNP1N1P/PPP2PP1/R1BQR1K1 b - - 0 10`
- Research-priority score: 21.545 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 2 collected games; it contains 2 promotion(s); the winner was at least 810 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 14. R3 vs hyperfish (1-0)

- Game: [fdbdb960-8b53-41fb-a4a9-d3f4d865ad53](https://aichessathon.com/game/fdbdb960-8b53-41fb-a4a9-d3f4d865ad53)
- Round/opening: Rated 3 · French Winawer
- Starting FEN: `rnbqk2r/pp2nppp/4p3/2ppP3/3P4/P1P5/2P2PPP/1RBQKBNR b Kkq - 2 7`
- Research-priority score: 20.585 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 3 collected games; it contains 1 promotion(s); the winner was at least 310 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 15. Check Republic vs The Rookie (0-1)

- Game: [00b0efea-d366-4bfe-9de0-f18eb73dbceb](https://aichessathon.com/game/00b0efea-d366-4bfe-9de0-f18eb73dbceb)
- Round/opening: Rated 2 · Sicilian Classical
- Starting FEN: `r1bqkb1r/pp2pppp/2np1n2/1B6/3NP3/2N5/PPP2PPP/R1BQK2R b KQkq - 4 6`
- Research-priority score: 20.493 (within this snapshot only)
- **OBSERVATION:** It contains a 63-ply low-piece ending; it contains 1 promotion(s); the winner was at least 1090 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Endgame geometry or conversion gradients may separate the engines; passed-pawn and pawn-race handling may be decisive.
- **EXPERIMENT:** Add the position and pre-ending checkpoints to the conversion/blind-win diagnostics; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 16. Capablanca vs Only Blunders (1-0)

- Game: [ed05c218-390e-429c-8c75-770fd601ecf0](https://aichessathon.com/game/ed05c218-390e-429c-8c75-770fd601ecf0)
- Round/opening: Rated 4 · Reti Opening
- Starting FEN: `rnbq1rk1/pp2bppp/4pn2/2pp4/2PP4/N4NP1/PP2PPBP/R1BQ1RK1 b - - 1 7`
- Research-priority score: 20.349 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 2 collected games; it contains 1 promotion(s); the winner was at least 990 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 17. Tobias Carlsen vs R3 (0-1)

- Game: [69e42a25-8236-4a49-b1e1-6cf44b7e2ebd](https://aichessathon.com/game/69e42a25-8236-4a49-b1e1-6cf44b7e2ebd)
- Round/opening: Rated 4 · Pirc Defence
- Starting FEN: `rnbq1rk1/ppp1ppbp/3p1np1/8/3PP3/2N2N2/PPP1BPPP/R1BQ1RK1 b - - 5 6`
- Research-priority score: 20.209 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 3 collected games; it contains 1 promotion(s); the winner was at least 400 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; passed-pawn and pawn-race handling may be decisive.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 18. Friday vs Tobias Carlsen (0-1)

- Game: [4b8d5dfd-ae0a-4b99-8661-f53046175147](https://aichessathon.com/game/4b8d5dfd-ae0a-4b99-8661-f53046175147)
- Round/opening: Rated 2 · French Classical
- Starting FEN: `rnbqkb1r/pp1n1ppp/4p3/2ppP3/3P1P2/8/PPP1N1PP/R1BQKBNR b KQkq - 1 6`
- Research-priority score: 20.054 (within this snapshot only)
- **OBSERVATION:** It contains 3 promotion(s); the winner was at least 720 cp behind by simple material count earlier; the game lasts 151 plies.
- **HYPOTHESIS (medium/low confidence):** Passed-pawn and pawn-race handling may be decisive; tactical foresight or compensation handling may explain the reversal.
- **EXPERIMENT:** Test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints; label the reversal window with an offline oracle and compare depth ladders before changing evaluation.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 19. team vs Yumo (0-1)

- Game: [df2c2dab-3e8b-437b-8f1c-2ce579043eaa](https://aichessathon.com/game/df2c2dab-3e8b-437b-8f1c-2ce579043eaa)
- Round/opening: Rated 4 · Pirc Defence
- Starting FEN: `rnbq1rk1/ppp1ppbp/3p1np1/8/3PP3/2N2N2/PPP1BPPP/R1BQ1RK1 b - - 5 6`
- Research-priority score: 19.898 (within this snapshot only)
- **OBSERVATION:** The exact starting fen appears in 3 collected games; it contains a 24-ply low-piece ending; it contains 1 promotion(s).
- **HYPOTHESIS (medium/low confidence):** Move choice and outcome differences may isolate search/evaluation quality from position selection; endgame geometry or conversion gradients may separate the engines.
- **EXPERIMENT:** Replay the exact fen against frozen claudeshark variants with both colours and fixed depth; add the position and pre-ending checkpoints to the conversion/blind-win diagnostics.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.

## 20. Analphabet vs Chess (1-0)

- Game: [e9e2fabf-1850-4620-8172-3d44cdec0520](https://aichessathon.com/game/e9e2fabf-1850-4620-8172-3d44cdec0520)
- Round/opening: Rated 2 · Catalan Opening
- Starting FEN: `rnbq1rk1/pp2bppp/2p1pn2/3p4/2PP4/5NP1/PP2PPBP/RNBQ1RK1 w - - 0 7`
- Research-priority score: 18.711 (within this snapshot only)
- **OBSERVATION:** It contains a 32-ply low-piece ending; it contains 2 promotion(s); the winner was at least 900 cp behind by simple material count earlier.
- **HYPOTHESIS (medium/low confidence):** Endgame geometry or conversion gradients may separate the engines; passed-pawn and pawn-race handling may be decisive.
- **EXPERIMENT:** Add the position and pre-ending checkpoints to the conversion/blind-win diagnostics; test square-rule, king-distance, and blocked-passer terms separately on extracted checkpoints.
- **WHAT NOT TO INFER:** Do not infer the opponent's implementation from moves alone, or treat one game/current snapshot rating as causal Elo evidence.
