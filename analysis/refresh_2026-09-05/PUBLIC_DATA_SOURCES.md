# AI Chessathon public data sources

Verified from a signed-out browser and unauthenticated HTTP requests on 2026-09-04.

## Completed-game collection routes

### `GET https://aichessathon.com/leaderboard`

- Authentication/headers: no authentication and no required custom header. The collector sends only a descriptive `User-Agent`.
- Query parameters: none required. Team links contain optional `from=lb` navigation context; it does not change the record.
- Response: server-rendered HTML. Each ladder row has `data-href=/team/{team_uuid}?from=lb` and cells for rank, bot/team display, university, rating, games, and W-D-L.
- Pagination: none; the complete current ladder is in one response.

### `GET https://aichessathon.com/team/{team_uuid}`

- Authentication/headers: no authentication and no required custom header.
- Query parameters: none required. `from=...` is optional backlink context.
- Response: server-rendered HTML. Game rows expose game UUID, rated round, colour, opponent UUID/name, result, and opening, newest first.
- Pagination: none observed; all public rows are returned in one page.

### `GET https://aichessathon.com/game/{game_uuid}`

- Authentication/headers: no authentication and no required custom header.
- Query parameters: none required. `from=...` is optional backlink context.
- Completed response: server-rendered HTML with both team UUIDs/names, result, round, termination, opening, Stockfish review summary, and a `data:application/x-chess-pgn` download URI. The decoded PGN contains starting FEN, SAN movetext, result/termination, and `%clk` comments.
- Live response: public partial movetext/clocks are embedded in the Next.js payload, but there is no final downloadable PGN or result. The completed-game dataset records and excludes such pages until finalisation.
- Timestamps/rating context: completed pages do not expose a game timestamp or historical pre-game ratings. The dataset uses `timestamp: null` and labels current ladder ratings as snapshot context.
- Pagination: not applicable.

## Live display route

### `GET https://aichessathon.com/api/platform/broadcast`

- Authentication/headers/query: no authentication, custom header, or query parameter required.
- Response headers observed: HTTP 200, `Content-Type: application/json`, `Cache-Control: no-store`.
- Top-level schema: `games` array, `total` integer, `serverNow` Unix epoch milliseconds.
- Game schema observed: `matchId`, `roundId`, `finishedAt`, `offsetsMs`, `clocksMs`, `control` (`base_ms`, `inc_ms`), `startFen`, SAN `moves`, `whiteFirst`, `firstMoveNo`, `white` and `black` objects (`teamId`, `name`, `botName`, avatar metadata), and `result`.
- Purpose/retention: transient live rail, polled by the frontend every 60 seconds and after finish notifications; it is not a historical archive and exposes no pagination.

## Supabase / Next.js findings

- The public client uses the documented Supabase project host for Realtime channel `live`, broadcast event `game_finished`; the event payload contains `match_id`, after which the client refreshes `/api/platform/broadcast` after about 900 ms.
- The collector does not open that WebSocket and does not use or store the site's public publishable key because neither is needed for completed data.
- No browser-side Supabase REST table, view, or RPC request was observed for the ladder, team history, or completed game. Those arrive server-rendered. No private table names were guessed or probed.
- Next.js navigation may request RSC payloads with framework-generated headers/state. Those are deployment-specific and unnecessary; the stable public HTML pages above are used.

## Rate limits and retry policy

No rate-limit documentation or rate-limit headers were observed. This is not proof that no limit exists. The collector uses modest configurable concurrency, a 45-second timeout, and backoff on HTTP 429 and transient 5xx/network failures.