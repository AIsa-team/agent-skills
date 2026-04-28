---
name: prediction-market-data
description: 'Prediction markets data - Polymarket, Kalshi markets, prices, positions, and trades. Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows.'
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 📈
    requires:
      bins:
      - curl
      - python
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# Cross-Platform Prediction Market Data 📈

**Prediction markets data access for autonomous agents. Powered by AIsa.**

One API key. Full Polymarket and Kalshi intelligence.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness, including:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**
- and any other harness that implements the [Agent Skills
  specification](https://agentskills.io/specification)

Requires Python 3, a POSIX shell, and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## What Can You Do?

### Probability Checks
```text
"What are the odds of [event] happening?"
```

### Market Sentiment
```text
"Research the current market sentiment on the upcoming election."
```

### Trading Analysis
```text
"Analyze historical prices and orderbooks for this market."
```

### Portfolio Tracking
```text
"Track portfolio positions and P&L for wallet address X."
```

### Arbitrage Detection
```text
"Find arbitrage opportunities across Polymarket and Kalshi."
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## How to Look Up IDs

Most endpoints require an ID that comes from the `/markets` response. Always query markets first, then pass the relevant ID to downstream endpoints.

1. **Polymarket `token_id`**: Query `/polymarket/markets`, find `side_a.id` or `side_b.id` in the response, then pass it to `/polymarket/market-price/{token_id}`.
2. **Polymarket `condition_id`**: Query `/polymarket/markets`, find `condition_id` in the response, then pass it to `/polymarket/candlesticks/{condition_id}`.
3. **Kalshi `market_ticker`**: Query `/kalshi/markets`, find `market_ticker` in the response, then pass it to `/kalshi/market-price/{market_ticker}`.

## End-to-End Examples

### Get the current price of a Polymarket market

Prices require a `token_id`, which comes from the `/markets` response. Always query markets first.

**Step 1: Find a market and extract the token_id:**

```bash
# Search for open election markets and grab a token_id
python scripts/prediction_market_client.py polymarket markets --search "election" --status open --limit 5
```

The response includes a `side_a.id` and `side_b.id` for each market; these are the token IDs for the Yes and No sides respectively:

```json
{
  "markets": [
    {
      "title": "Will Trump nationalize elections?",
      "market_slug": "will-trump-nationalize-elections",
      "condition_id": "0xe6522d64f35a6843ebdbccab2e3d4a1385350be6d40a3de766330e207b71a8ba",
      "side_a": {
        "id": "44482086252598348208660011972852804909957485351743405768768577675743702971026",
        "label": "Yes"
      },
      "side_b": {
        "id": "68987475491741167427045844503509447338405188188495224371188027929166363674438",
        "label": "No"
      }
    }
  ]
}
```

**Step 2: Fetch the current price using the token_id:**

```bash
# Use side_a.id (Yes) or side_b.id (No) from Step 1
python scripts/prediction_market_client.py polymarket price 44482086252598348208660011972852804909957485351743405768768577675743702971026
```

The price is a decimal between 0 and 1 representing the probability (e.g. `0.20` = 20% chance of Yes).

---

### Get the current price of a Kalshi market

**Step 1: Find a market and extract the market_ticker:**

```bash
python scripts/prediction_market_client.py kalshi markets --search "fed rate" --status open --limit 5
```

```json
{
  "markets": [
    {
      "title": "Will the federal funds rate be above 3.75% after the Mar 2026 meeting?",
      "market_ticker": "KXFED-26MAR-T3.75",
      "last_price": 6
    }
  ]
}
```

**Step 2: Fetch the price using the market_ticker:**

```bash
python scripts/prediction_market_client.py kalshi price KXFED-26MAR-T3.75
```

---

## Core Capabilities

### Polymarket

#### Markets

```bash
# Find markets on Polymarket
curl -X GET "https://api.aisa.one/apis/v1/polymarket/markets?search=election&status=open" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Market Price

```bash
# Step 1: query /polymarket/markets to get a token_id from side_a.id or side_b.id
# Step 2: pass that token_id here to get the current price
curl -X GET "https://api.aisa.one/apis/v1/polymarket/market-price/{token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Activity

```bash
# Fetch activity data for a specific user
curl -X GET "https://api.aisa.one/apis/v1/polymarket/activity?user={wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Trade History

```bash
# Fetch historical trade data
curl -X GET "https://api.aisa.one/apis/v1/polymarket/orders?market_slug={market_slug}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Orderbook History

```bash
# Fetch historical orderbook snapshots for a specific asset
# token_id comes from side_a.id or side_b.id in /polymarket/markets response
curl -X GET "https://api.aisa.one/apis/v1/polymarket/orderbooks?token_id={token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Candlesticks

```bash
# Fetch historical candlestick data for a market
# condition_id comes from /polymarket/markets response
curl -X GET "https://api.aisa.one/apis/v1/polymarket/candlesticks/{condition_id}?interval=60" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Positions

```bash
# Fetch all Polymarket positions for a proxy wallet address
curl -X GET "https://api.aisa.one/apis/v1/polymarket/positions/wallet/{wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Wallet

```bash
# Fetch wallet information
curl -X GET "https://api.aisa.one/apis/v1/polymarket/wallet?eoa={wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Wallet Profit-and-Loss

```bash
# Fetch realized profit and loss (PnL) for a specific wallet address
curl -X GET "https://api.aisa.one/apis/v1/polymarket/wallet/pnl/{wallet_address}?granularity=day" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Kalshi

#### Markets

```bash
# Find markets on Kalshi
curl -X GET "https://api.aisa.one/apis/v1/kalshi/markets?search=fed%20rate" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Market Price

```bash
# Fetch the current market price for a Kalshi market
# market_ticker comes from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/market-price/{market_ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Trade History

```bash
# Fetch historical trade data for Kalshi markets
# ticker (market_ticker) comes from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/trades?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Orderbook History

```bash
# Fetch historical orderbook snapshots for a specific Kalshi market
# ticker (market_ticker) comes from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/orderbooks?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Cross-Platform

#### Sports Markets

```bash
# Find equivalent markets across platforms for sports events
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Sports Markets by Date

```bash
# Find equivalent markets across platforms for a sport on a given date
# sport options: nfl, mlb, cfb, nba, nhl, cbb, pga, tennis
# date format: YYYY-MM-DD
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports/nba?date=2025-08-16" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Sport abbreviations:

| Abbreviation | Sport |
|---|---|
| `nfl` | Football |
| `mlb` | Baseball |
| `cfb` | College Football |
| `nba` | Basketball |
| `nhl` | Hockey |
| `cbb` | College Basketball |
| `pga` | Golf |
| `tennis` | Tennis |

## API Endpoints Reference

### Polymarket Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/polymarket/markets` | Find markets | `search`, `status`, `market_slug`, `limit` |
| `/polymarket/market-price/{token_id}` | Get market price | `token_id`, `at_time` |
| `/polymarket/activity` | Get user activity | `user`, `start_time`, `end_time` |
| `/polymarket/orders` | Get trade history | `market_slug`, `token_id`, `user` |
| `/polymarket/orderbooks` | Get orderbook history | `token_id`, `start_time`, `end_time` |
| `/polymarket/candlesticks/{condition_id}` | Get candlestick data | `condition_id`, `start_time`, `end_time`, `interval` |
| `/polymarket/positions/wallet/{wallet_address}` | Get wallet positions | `wallet_address`, `limit` |
| `/polymarket/wallet` | Get wallet info | `eoa` or `proxy`, `with_metrics` |
| `/polymarket/wallet/pnl/{wallet_address}` | Get wallet PnL | `wallet_address`, `granularity` |

### Kalshi Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/kalshi/markets` | Find markets | `search`, `status`, `market_ticker` |
| `/kalshi/market-price/{market_ticker}` | Get market price | `market_ticker`, `at_time` |
| `/kalshi/trades` | Get trade history | `ticker`, `start_time`, `end_time` |
| `/kalshi/orderbooks` | Get orderbook history | `ticker`, `start_time`, `end_time` |

### Cross-Platform Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/matching-markets/sports` | Find matching sports markets | `polymarket_market_slug` or `kalshi_event_ticker` |
| `/matching-markets/sports/{sport}` | Find sports markets by date | `sport` (nfl\|mlb\|cfb\|nba\|nhl\|cbb\|pga\|tennis), `date` (YYYY-MM-DD) |

## Response Schemas

### Markets Response
Returns markets array:
- `title` (string) - Market question (e.g., "Will Trump nationalize elections?")
- `market_slug` (string) - URL-friendly identifier
- `condition_id` (string) - Blockchain condition ID
- `start_time` / `end_time` (integer) - Unix timestamps
- `completed_time` (integer|null) - Null if still open
- `tags` (array) - Category tags (e.g., ["politics", "us election"])
- `volume_1_week` / `volume_1_month` / `volume_1_year` / `volume_total` (number) - Trading volume in USD
- `side_a` / `side_b` (object) - id and label (typically "Yes"/"No")
- `winning_side` (object|null) - Null if unresolved
- `image` (string) - Market thumbnail URL

### Activity Response
Returns activities array:
- `title` (string) - Market title
- `market_slug` (string) - Market identifier
- `side` (string) - Trade side: BUY, SELL, or MERGE
- `shares` (integer) - Raw share amount
- `shares_normalized` (number) - Human-readable share amount
- `price` (number) - Trade price (0-1, represents probability)
- `timestamp` (integer) - Unix timestamp of the trade
- `user` (string) - Wallet address of the trader
- `tx_hash` (string) - Blockchain transaction hash

## Understanding Odds
- Prices are shown as decimals (0.65 = 65% probability)
- "Yes" price = probability market thinks event will happen
- Higher volume = more confidence/liquidity
- Prices change based on trading activity

## Pricing

| API | Cost |
|-----|------|
| Prediction market read query | $0.01 |

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key
3. Add credits (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See [API Reference](https://aisa.one/docs/api-reference/) for complete endpoint documentation.
