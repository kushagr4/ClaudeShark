# Diagnostic: widened bounds, K refitted at every width

Fable's fit placed four of ten parameters on the 1.5x ceiling. With K refitted per width the calibration gradient is removed, so a fit that still climbs with the ceiling is absorbing units rather than chess.

| bounds | lambda | max|delta| | on bound | val ES-MSE | K | effective scale | MG P/N/B/R/Q |
|---|---|---|---|---|---|---|---|
| [0.6, 1.5] | 0 | 468 | 3/10 | 0.04234 | 120 | 1.14x | 72/341/354/459/723 |
| [0.5, 2.0] | 0 | 936 | 1/10 | 0.04200 | 130 | 1.30x | 66/318/332/427/546 |
| [0.4, 2.5] | 0 | 1132 | 1/10 | 0.04188 | 130 | 1.32x | 65/311/325/416/410 |
| [0.3, 3.0] | 0 | 1154 | 0/10 | 0.04188 | 130 | 1.32x | 65/310/323/415/388 |
| [0.25, 4.0] | 0 | 1154 | 0/10 | 0.04188 | 130 | 1.32x | 65/310/323/415/388 |

Two things fall out of this table, and neither favours the ten-parameter model.

First, the lambda sweep selects **zero regularisation at every width**. A fit whose validation loss always prefers the most movement available is not finding structure; it is spending degrees of freedom.

Second, and decisively: once the ceiling is lifted the middlegame queen **collapses back toward the diagnosed artefact**. Production is 1025; the fit goes to 723, then 546, then 388, and settles there. The previous session identified the large negative queen correction as an artefact of the fitting setup rather than a chess fact, and this shows the artefact was never removed -- it was only held back by the 0.6-1.5x band. Inside that band the fit still leans the same way: it scales pawn and knight to the 1.5x ceiling but holds the queen to 1.18x, which is the same preference wearing a bound.

That is the mechanism behind the ten-parameter candidate's extra deterministic margin over the one-parameter scale: the two differ almost only in the middlegame queen. The margin therefore rides on a component already known to be an artefact, which is why the one-parameter scale is the candidate that goes to the arena.

