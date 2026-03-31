---
name: Prediction Market Arbitrage
description: "Find and analyze arbitrage opportunities across prediction markets like Polymarket and Kalshi."
homepage: https://openclaw.ai
metadata: {"openclaw":{"emoji":"⚖️","requires":{"bins":["curl","python3"],"env":["AISA_API_KEY"]},"primaryEnv":"AISA_API_KEY"}}
---

# Cross-Platform Prediction Market Arbitrage ⚖️

**Find arbitrage opportunities across prediction markets for autonomous agents. Powered by AIsa.**

One API key. Instantly match events across Polymarket and Kalshi to detect price discrepancies and risk-free profit opportunities.

## What Can You Do?

### Detect Price Discrepancies
```text
"Find the current price difference for the 2024 US Election between Polymarket and Kalshi."
```

### Match Cross-Platform Markets
```text
"Find the Kalshi equivalent for this Polymarket sports event."
```

### Track Arbitrage Spreads
```text
"Monitor the price spread for the upcoming NBA game across all supported prediction markets."
```

### Analyze Orderbook Depth
```text
"Check the orderbook depth on both platforms to see if the arbitrage opportunity is actionable."
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## How to Look Up IDs

Most endpoints require an ID that comes from the `/markets` or `/matching-markets` responses. Always query markets first, then pass the relevant ID to downstream endpoints.

1. **Polymarket `token_id`** — Query `/polymarket/markets`, find `side_a.id` or `side_b.id` in the response, then pass it to `/polymarket/market-price/{token_id}`.
2. **Kalshi `market_ticker`** — Query `/kalshi/markets`, find `market_ticker` in the response, then pass it to `/kalshi/market-price/{market_ticker}`.

## Core Capabilities

### 1. Find Matching Markets (Cross-Platform)

The first step in arbitrage is finding the exact same event on multiple platforms.

#### Match by Event Ticker / Slug

```bash
# Find equivalent markets across platforms using a Polymarket slug
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports?polymarket_market_slug=nba-lakers-vs-celtics" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Or find equivalent markets using a Kalshi ticker
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports?kalshi_event_ticker=KXNBA-24" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Match Sports by Date

```bash
# Find all matching sports markets across platforms for a specific date
# sport options: nfl, mlb, cfb, nba, nhl, cbb, pga, tennis
# date format: YYYY-MM-DD
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports/nba?date=2025-08-16" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### 2. Compare Prices

Once matching markets are found, fetch the real-time prices on both platforms to calculate the spread.

#### Get Polymarket Price

```bash
# Step 1: query /polymarket/markets to get a token_id from side_a.id or side_b.id
# Step 2: pass that token_id here to get the current price
curl -X GET "https://api.aisa.one/apis/v1/polymarket/market-price/{token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Get Kalshi Price

```bash
# Fetch the current market price for a Kalshi market
# market_ticker comes from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/market-price/{market_ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### 3. Verify Liquidity (Orderbooks)

A price discrepancy is only actionable if there is enough liquidity to execute the trades.

#### Polymarket Orderbook

```bash
# Fetch the latest orderbook snapshot for a Polymarket asset
# token_id comes from side_a.id or side_b.id in /polymarket/markets response
curl -X GET "https://api.aisa.one/apis/v1/polymarket/orderbooks?token_id={token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Kalshi Orderbook

```bash
# Fetch the latest orderbook snapshot for a Kalshi market
# ticker (market_ticker) comes from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/orderbooks?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

## API Endpoints Reference

### Cross-Platform Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/matching-markets/sports` | Find matching sports markets | `polymarket_market_slug` or `kalshi_event_ticker` |
| `/matching-markets/sports/{sport}` | Find sports markets by date | `sport` (nfl\|mlb\|cfb\|nba\|nhl\|cbb\|pga\|tennis), `date` (YYYY-MM-DD) |

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

### Price & Liquidity Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/polymarket/market-price/{token_id}` | Get Polymarket price | `token_id`, `at_time` |
| `/kalshi/market-price/{market_ticker}` | Get Kalshi price | `market_ticker`, `at_time` |
| `/polymarket/orderbooks` | Get Polymarket orderbook | `token_id`, `start_time`, `end_time` |
| `/kalshi/orderbooks` | Get Kalshi orderbook | `ticker`, `start_time`, `end_time` |

## Understanding Arbitrage & Odds

- **Prices as Probabilities**: Prices are shown as decimals (e.g., 0.65 = 65% implied probability).
- **Arbitrage Opportunity**: An opportunity exists when the combined price of all mutually exclusive outcomes across different platforms is less than 1.0 (or 100 cents). For example, if "Yes" is trading at 0.40 on Polymarket and "No" is trading at 0.55 on Kalshi, buying both guarantees a payout of 1.00 for a total cost of 0.95 (a 0.05 risk-free profit minus fees).
- **Liquidity Check**: Always check the `/orderbooks` endpoints. A price difference might exist, but if the orderbook lacks depth, executing the trade will cause slippage, eliminating the profit.

## Pricing

| API | Cost |
|-----|------|
| Prediction market read query | $0.01 |

Every response includes `usage.cost` and `usage.credits_remaining`.

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key
3. Add credits (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See [API Reference](https://docs.aisa.one/reference/) for complete endpoint documentation.
