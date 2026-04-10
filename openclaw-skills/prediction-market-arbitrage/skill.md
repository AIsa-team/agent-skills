---
name: Prediction Market Arbitrage
description: "Find and analyze arbitrage opportunities across prediction markets like Polymarket and Kalshi."
homepage: https://openclaw.ai
metadata: {"openclaw":{"emoji":"⚖️","requires":{"bins":["curl","python3"],"env":["AISA_API_KEY"]},"primaryEnv":"AISA_API_KEY"}}
---

# Cross-Platform Prediction Market Arbitrage ⚖️

**Find arbitrage opportunities across prediction markets for autonomous agents. Powered by AIsa.**

One API key. Match events across Polymarket and Kalshi to detect price discrepancies and potential risk-free profit opportunities.

## What Can You Do?

### Detect Price Discrepancies
```text
"Find the current price difference for the US election market between Polymarket and Kalshi."
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

Most endpoints require an ID from the `/markets` or `/matching-markets` responses. Always query markets first, then pass the relevant ID to downstream endpoints.

1. **Polymarket `token_id`**: Query `/polymarket/markets`, find `side_a.id` or `side_b.id` in the response, then use that value in the market price and orderbook endpoints.
2. **Kalshi `market_ticker`**: Query `/kalshi/markets`, find `market_ticker` in the response, then use that value in the market price and orderbook endpoints.

## Core Capabilities

### 1. Find Matching Markets

The first step in arbitrage is finding the same event on multiple platforms.

#### Match by Event Ticker or Slug

```bash
# Find equivalent markets across platforms using a Polymarket slug
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports?polymarket_market_slug={polymarket_market_slug}" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Or find equivalent markets using a Kalshi event ticker
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports?kalshi_event_ticker={kalshi_event_ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Match Sports by Date

```bash
# Find all matching sports markets across platforms for a specific date
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports/{sport}?date={date}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### 2. Compare Prices

Once matching markets are found, fetch the current prices on both platforms to calculate the spread.

#### Get Polymarket Price

```bash
# token_id comes from side_a.id or side_b.id in /polymarket/markets response
curl -X GET "https://api.aisa.one/apis/v1/polymarket/market-price/{token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Get Kalshi Price

```bash
# market_ticker comes from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/market-price/{market_ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### 3. Verify Liquidity

A price discrepancy is only actionable if there is enough liquidity to execute the trades.

#### Polymarket Orderbook

```bash
# token_id comes from side_a.id or side_b.id in /polymarket/markets response
curl -X GET "https://api.aisa.one/apis/v1/polymarket/orderbooks?token_id={token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Kalshi Orderbook

```bash
# ticker is the same value as market_ticker from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/orderbooks?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

## API Endpoints Reference

### Cross-Platform Endpoints

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/matching-markets/sports` | Find matching sports markets | `polymarket_market_slug` or `kalshi_event_ticker` |
| `/matching-markets/sports/<sport>` | Find sports markets by date | `sport`, `date` |

### Price and Liquidity Endpoints

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/polymarket/market-price/<token_id>` | Get Polymarket price | `token_id`, `at_time` |
| `/kalshi/market-price/<market_ticker>` | Get Kalshi price | `market_ticker`, `at_time` |
| `/polymarket/orderbooks` | Get Polymarket orderbook | `token_id`, `start_time`, `end_time` |
| `/kalshi/orderbooks` | Get Kalshi orderbook | `ticker`, `start_time`, `end_time` |

## Important Note About cURL Placeholders

The `{...}` values in the cURL examples are product-level placeholders and must be replaced before execution.

Execution constraint:
- Before running `curl`, the agent or runner must verify that every `{...}` placeholder has been replaced with a concrete value.
- If any placeholder such as `{token_id}`, `{market_ticker}`, `{sport}`, or `{date}` is still present in the final command, do not execute the command. Fail fast and surface a missing-parameter error instead.

This constraint is required because a literal brace placeholder may be interpreted by `curl` as URL globbing syntax rather than as plain text.

## Understanding Arbitrage and Odds

- **Prices as probabilities**: Prices are usually shown as decimals, for example `0.65` means a 65% implied probability.
- **Arbitrage opportunity**: An opportunity exists when the combined price of all mutually exclusive outcomes across different platforms is less than `1.0`. For example, if "Yes" is trading at `0.40` on Polymarket and "No" is trading at `0.55` on Kalshi, buying both guarantees a payout of `1.00` for a total cost of `0.95`, before fees and slippage.
- **Liquidity check**: Always check the `/orderbooks` endpoints. A price difference might exist, but if the orderbook lacks depth, executing the trade may eliminate the profit.

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
