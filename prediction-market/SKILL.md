---
name: prediction-market
description: Prediction markets data - Polymarket, Kalshi markets, prices, positions, and trades
---

# Prediction Market Data

Get current odds, prices, and market data from prediction markets like Polymarket and Kalshi. Access historical orderbook data, candlestick charts, trade history, wallet positions, and more.

## When to Use

- User asks about prediction market odds
- User wants to know probability of an event
- User asks "what are the odds of [event]?"
- Research on market sentiment
- Election or event probability checks
- Trading analysis on historical prices and orderbooks
- Portfolio tracking and P&L monitoring
- Arbitrage detection across platforms

## How It Works

Uses the Dome API at `https://api.aisa.one/apis/v1/dome` to aggregate prediction market data from Polymarket and Kalshi.

## Polymarket

### Markets

Find markets on Polymarket using various filters including the ability to search.

Parameters:
- `market_slug` (string[]) - Filter markets by market slug(s). Can provide multiple values.
- `event_slug` (string[]) - Filter markets by event slug(s). Can provide multiple values.
- `condition_id` (string[]) - Filter markets by condition ID(s). Can provide multiple values.
- `tags` (string[]) - Filter markets by tag(s). Can provide multiple values.
- `search` (string) - Search markets by keywords in title and description. Must be URL encoded (e.g., `bitcoin%20price` for `bitcoin price`).
- `status` (enum\<string\>) - Filter markets by status (whether they're open or closed)
- `min_volume` (number) - Filter markets with total trading volume greater than or equal to this amount (USD)
- `limit` (integer) - Number of markets to return (1-100). Default: 10 for search, 10 for regular queries.
- `offset` (integer) - Number of markets to skip for pagination
- `start_time` (integer) - Filter markets from this Unix timestamp in seconds (inclusive)
- `end_time` (integer) - Filter markets until this Unix timestamp in seconds (inclusive)

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/polymarket/markets?search=election&status=open" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Market Price

Fetches the current market price for a market by token_id. Allows historical lookups via the `at_time` query parameter.

Parameters:
- `at_time` (integer) - Optional Unix timestamp (in seconds) to fetch a historical market price. If not provided, returns the most real-time price available.

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/polymarket/market-price/{token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Activity

Fetches activity data for a specific user with optional filtering by market, condition, and time range. Returns trading activity including MERGES, SPLITS, and REDEEMS.

Parameters:
- `user`* (string) - User wallet address to fetch activity for
- `start_time` (integer) - Filter activity from this Unix timestamp in seconds (inclusive)
- `end_time` (integer) - Filter activity until this Unix timestamp in seconds (inclusive)
- `market_slug` (string) - Filter activity by market slug
- `condition_id` (string) - Filter activity by condition ID
- `limit` (integer) - Number of activities to return (1-1000)
- `offset` (integer) - Number of activities to skip for pagination

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/polymarket/activity?user={wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Trade History

Fetches historical trade data with optional filtering by market, condition, token, time range, and user's wallet address.

Parameters:
- `market_slug` (string) - Filter orders by market slug
- `condition_id` (string) - Filter orders by condition ID
- `token_id` (string) - Filter orders by token ID
- `start_time` (integer) - Filter orders from this Unix timestamp in seconds (inclusive)
- `end_time` (integer) - Filter orders until this Unix timestamp in seconds (inclusive)
- `limit` (integer) - Number of orders to return (1-1000)
- `offset` (integer) - Number of orders to skip for pagination
- `user` (string) - Filter orders by user (wallet address)

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/polymarket/orders?market={market_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Orderbook History

Fetches historical orderbook snapshots for a specific asset (token ID) over a specified time range. If no `start_time` and `end_time` are provided, returns the latest orderbook snapshot for the market.

Parameters:
- `token_id`* (string) - The token id (asset) for the Polymarket market
- `start_time` (integer) - Start time in Unix timestamp (milliseconds). Optional - if not provided along with `end_time`, returns the latest orderbook snapshot.
- `end_time` (integer) - End time in Unix timestamp (milliseconds). Optional - if not provided along with `start_time`, returns the latest orderbook snapshot.
- `limit` (integer) - Maximum number of snapshots to return (default: 100, max: 200). Ignored when fetching the latest orderbook without `start_time` and `end_time`.
- `pagination_key` (string) - Pagination key to get the next chunk of data. Ignored when fetching the latest orderbook without `start_time` and `end_time`.

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/polymarket/orderbooks?token_id={token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Candlesticks

Fetches historical candlestick data for a market identified by condition_id, over a specified interval.

Parameters:
- `start_time`* (integer) - Unix timestamp (in seconds) for start of time range
- `end_time`* (integer) - Unix timestamp (in seconds) for end of time range
- `interval` (enum\<integer\>) - Interval length: `1` = 1m, `60` = 1h, `1440` = 1d. Defaults to 1m. Note: There are range limits for interval — specifically: `1` (1m): max range 1 week, `60` (1h): max range 1 month, `1440` (1d): max range 1 year

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/polymarket/candlesticks/{condition_id}?interval=60" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Positions

Fetches all Polymarket positions for a proxy wallet address. Returns positions with balance >= 10,000 shares (0.01 normalized) with market info.

Parameters:
- `limit` (integer) - Maximum number of positions to return per page. Defaults to 100, maximum 100.
- `pagination_key` (string) - Pagination key returned from previous request to fetch next page of results

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/polymarket/positions/wallet/{wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Wallet

Fetches wallet information by providing either an EOA (Externally Owned Account) address or a proxy wallet address. Returns the associated EOA, proxy, and wallet type. Optionally returns trading metrics including total volume, number of trades, and unique markets traded when `with_metrics=true`.

Parameters:
- `eoa` (string) - EOA (Externally Owned Account) wallet address. Either `eoa` or `proxy` must be provided, but not both.
- `proxy` (string) - Proxy wallet address. Either `eoa` or `proxy` must be provided, but not both.
- `with_metrics` (enum\<string\>) - Whether to include wallet trading metrics (total volume, trades, and markets). Pass `true` to include metrics. Metrics are computed only when explicitly requested for performance reasons.
- `start_time` (integer) - Optional start date for metrics calculation (Unix timestamp in seconds). Only used when `with_metrics=true`.
- `end_time` (integer) - Optional end date for metrics calculation (Unix timestamp in seconds). Only used when `with_metrics=true`.

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/polymarket/wallet?eoa={wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Wallet Profit-and-Loss

Fetches the realized profit and loss (PnL) for a specific wallet address over a specified time range and granularity. Note: This will differ to what you see on Polymarket's dashboard since Polymarket showcases historical unrealized PnL.

Parameters:
- `granularity`* (enum\<string\>) - Example: `"day"`
- `start_time` (integer) - Defaults to first day of first trade if not provided.
- `end_time` (integer) - Defaults to the current date if not provided.

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/polymarket/wallet/pnl/{wallet_address}?granularity=day" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Kalshi

### Markets

Find markets on Kalshi using various filters including market ticker, event ticker, status, and volume.

Parameters:
- `market_ticker` (string[]) - Filter markets by market ticker(s). Can provide multiple values.
- `event_ticker` (string[]) - Filter markets by event ticker(s). Can provide multiple values.
- `search` (string) - Search markets by keywords in title and description. Must be URL encoded (e.g., `bitcoin%20price` for `bitcoin price`).
- `status` (enum\<string\>) - Filter markets by status (whether they're open or closed)
- `min_volume` (number) - Filter markets with total trading volume greater than or equal to this amount (in dollars)
- `limit` (integer) - Number of markets to return (1-100). Default: 10.
- `offset` (integer) - Number of markets to skip for pagination

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/kalshi/markets?search=fed%20rate" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Market Price

Fetches the current market price for a Kalshi market by market_ticker. Returns prices for both yes and no sides. Allows historical lookups via the `at_time` query parameter.

Parameters:
- `at_time` (integer) - Optional Unix timestamp (in seconds) to fetch a historical market price. If not provided, returns the most real-time price available.

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/kalshi/market-price/{market_ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Trade History

Fetches historical trade data for Kalshi markets with optional filtering by ticker and time range. Returns executed trades with pricing, volume, and taker side information. All timestamps are in seconds.

Parameters:
- `ticker` (string) - The Kalshi market ticker to filter trades
- `start_time` (integer) - Start time in Unix timestamp (seconds)
- `end_time` (integer) - End time in Unix timestamp (seconds)
- `limit` (integer) - Maximum number of trades to return (default: 100)
- `offset` (integer) - Number of trades to skip for pagination

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/kalshi/trades?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Orderbook History

Fetches historical orderbook snapshots for a specific Kalshi market (ticker) over a specified time range. If no `start_time` and `end_time` are provided, returns the latest orderbook snapshot for the market.

Parameters:
- `ticker`* (string) - The Kalshi market ticker
- `start_time` (integer) - Start time in Unix timestamp (milliseconds). Optional - if not provided along with `end_time`, returns the latest orderbook snapshot.
- `end_time` (integer) - End time in Unix timestamp (milliseconds). Optional - if not provided along with `start_time`, returns the latest orderbook snapshot.
- `limit` (integer) - Maximum number of snapshots to return (default: 100, max: 200). Ignored when fetching the latest orderbook without `start_time` and `end_time`.

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/kalshi/orderbooks?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Cross-Platform

### Sports Markets

Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events using a Polymarket market slug or a Kalshi event ticker.

Parameters:
- `polymarket_market_slug` (string[]) - The Polymarket market slug(s) to find matching markets for. To get multiple markets at once, provide the query param multiple times with different slugs. Cannot be combined with `kalshi_event_ticker`.
- `kalshi_event_ticker` (string[]) - The Kalshi event ticker(s) to find matching markets for. To get multiple markets at once, provide the query param multiple times with different tickers. Cannot be combined with `polymarket_market_slug`.

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/matching-markets/sports" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Sports Markets by Date

Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events by sport and date.

Supported sports: `nba`, `nfl`, `mlb`, `nhl`, `soccer`, `tennis`

Parameters:
- `date`* (string) - The date to find matching markets for in YYYY-MM-DD format

```bash
curl -X GET "https://api.aisa.one/apis/v1/dome/matching-markets/sports/nba?date=2024-03-01" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Response Schemas

### Markets Response (`/polymarket/markets`, `/kalshi/markets`)

Returns `markets` array:
- `title` (string) - Market question (e.g., "Will Trump nationalize elections?")
- `market_slug` (string) - URL-friendly identifier
- `condition_id` (string) - Blockchain condition ID
- `start_time` / `end_time` (integer) - Unix timestamps
- `completed_time` (integer|null) - Null if still open
- `tags` (array) - Category tags (e.g., `["politics", "us election"]`)
- `volume_1_week` / `volume_1_month` / `volume_1_year` / `volume_total` (number) - Trading volume in USD
- `side_a` / `side_b` (object) - id and label (typically "Yes"/"No")
- `winning_side` (object|null) - Null if unresolved
- `image` (string) - Market thumbnail URL

### Activity Response (`/polymarket/activity`)

Returns `activities` array:
- `title` (string) - Market title
- `market_slug` (string) - Market identifier
- `side` (string) - Trade side: `BUY`, `SELL`, or `MERGE`
- `shares` (integer) - Raw share amount
- `shares_normalized` (number) - Human-readable share amount
- `price` (number) - Trade price (0-1, represents probability)
- `timestamp` (integer) - Unix timestamp of the trade
- `user` (string) - Wallet address of the trader
- `tx_hash` (string) - Blockchain transaction hash

---

## Understanding Odds

- Prices are shown as decimals (0.65 = 65% probability)
- "Yes" price = probability market thinks event will happen
- Higher volume = more confidence/liquidity
- Prices change based on trading activity

## Use Cases

- **Market Research**: Track prediction market sentiment
- **Trading Analysis**: Analyze historical prices and orderbooks
- **Portfolio Tracking**: Monitor positions and P&L
- **Arbitrage**: Find price differences across platforms
- **Forecasting**: Use market prices as probability estimates

## Error Handling

- `400` - `search` requires `status` parameter (`open` or `closed`) — always include both
- `401` - Invalid API key
- `429` - Rate limit — wait and retry
- Empty `markets` array means no markets match the search term
- Activity endpoint returns recent trades globally — no filters required

## Tips

- Check multiple markets for the same event
- Volume indicates market confidence
- Recent activity shows sentiment shifts
- Polymarket focuses on politics/world events, Kalshi on finance/weather
