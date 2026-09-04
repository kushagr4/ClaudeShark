# These splits are frozen

Created 2026-09-04 by `tools/daily/splits.py` with seed **20260904** from
`analysis/top50_games.jsonl` (sha256 `37f821f4dfadf3ff...`). Membership is by
**exact starting FEN family**: every game beginning from the same position is on
the same side of the split, because two games from one position are not
independent evidence about a candidate.

| split | families | games | share | repeated families | FEN-list sha256 |
|---|---|---|---|---|---|
| `competition_diagnostic` | 51 | 71 | 50.4% | 14 | `dba94b1223900e8a5d325847b950485bdfd1295f03b690f104ad6cae35013041` |
| `competition_validation` | 29 | 35 | 24.8% | 6 | `ef2189f5447b41bcab8db4b0eb58555c95254f85b4768de53df54ee2f125e4f4` |
| `competition_holdout` | 33 | 35 | 24.8% | 2 | `a1806d7b05a6fbfa49b30f570c627ae9d7a719a9f94a302501e88a9c8f29d4af` |

Families appearing in more than one split: **0** (asserted by the tool, which
fails rather than writing an overlapping split). ClaudeShark's own three rated
starting positions are excluded from all three and remain external deployment
evidence.

## Rules

**Membership does not change.** It is not reshuffled after seeing how a feature
performs, and the seed is not retried.

* **`competition_diagnostic`** — hypotheses may be formed here, coefficients
  chosen here, per-position error mining and mechanism clustering done here.
* **`competition_validation`** — read **once**, after a feature and its
  parameters are frozen.
* **`competition_holdout`** — **not inspected during feature design.** No
  mechanism clustering, no feature attribution, no coefficient selection, no
  per-position error mining. Read only as final promotion evidence.

## One prior exposure, recorded rather than hidden

The 226-game `champions/v2_1_kingpawn` against `champions/rated_v1` match
(`corpus/daily/pool/games/v21_vs_ratedv1_actual.jsonl`) runs over all 113
families, including the holdout ones. That is acceptable for V2.1 specifically,
because V2.1 was designed and frozen long before these positions were seen, so
nothing about it was selected using them.

The consequence is recorded and honoured: **that population is exploratory
distribution evidence, not a pristine holdout.** For the headline V2.1
distribution verdict all 113 families are aggregated as planned. For designing
the *next* feature, detailed per-FEN and mechanism inspection is restricted to
the diagnostic split.
